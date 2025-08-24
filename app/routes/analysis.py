#!/usr/bin/env python3
"""
Analysis routes for LITE application

Handles artifact analysis, filtering, and exploration functionality.
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from sqlalchemy import text, func
from app.database import db, execute_case_query, get_case_tables, get_table_row_count
from app.models import Case
from datetime import datetime, timedelta
import logging
import json
from uuid import UUID

analysis_bp = Blueprint('analysis', __name__)

# Define artifact categories and their corresponding tables
ARTIFACT_CATEGORIES = {
    'overview': {
        'name': 'Overview',
        'icon': 'fas fa-chart-pie',
        'tables': ['collection_metadata']
    },
    'users': {
        'name': 'User Accounts',
        'icon': 'fas fa-users',
        'tables': ['user_accounts'],
        'subcategories': {
            'accounts': 'User Accounts',
            'activity': 'User Activity'
        }
    },
    'processes': {
        'name': 'Processes',
        'icon': 'fas fa-cogs',
        'tables': ['processes'],
        'subcategories': {
            'running': 'Running Processes',
            'analysis': 'Process Analysis'
        }
    },
    'network': {
        'name': 'Network',
        'icon': 'fas fa-network-wired',
        'tables': ['network_connections', 'firewall_rules'],
        'subcategories': {
            'connections': 'Network Connections',
            'firewall': 'Firewall Rules'
        }
    },
    'system': {
        'name': 'System',
        'icon': 'fas fa-server',
        'tables': ['systemd_services', 'installed_packages', 'cron_jobs'],
        'subcategories': {
            'services': 'System Services',
            'packages': 'Installed Packages',
            'scheduled': 'Scheduled Tasks'
        }
    },
    'logs': {
        'name': 'Logs',
        'icon': 'fas fa-file-alt',
        'tables': ['auth_logs', 'system_logs', 'kernel_logs'],
        'subcategories': {
            'auth': 'Authentication Logs',
            'system': 'System Logs',
            'kernel': 'Kernel Logs'
        }
    },
    'files': {
        'name': 'Files & Directories',
        'icon': 'fas fa-folder',
        'tables': ['file_system', 'recent_files'],
        'subcategories': {
            'filesystem': 'File System',
            'recent': 'Recent Files'
        }
    },
    'browser': {
        'name': 'Browser Data',
        'icon': 'fas fa-globe',
        'tables': ['browsing_history', 'browser_downloads'],
        'subcategories': {
            'history': 'Browsing History',
            'downloads': 'Downloads'
        }
    }
}

@analysis_bp.route('/<case_id>')
def analysis_home(case_id):
    """Analysis home page with navigation"""
    try:
        case_uuid = UUID(case_id)
        case = Case.query.get_or_404(case_uuid)
        
        # Get available tables for this case
        available_tables = get_case_tables(case.schema_name)
        
        # Calculate table statistics
        total_records = 0
        for table in available_tables:
            try:
                count = get_table_row_count(case.schema_name, table)
                total_records += count
            except Exception:
                pass  # Skip tables that can't be counted
        
        table_stats = {
            'total_tables': len(available_tables),
            'total_records': total_records
        }
        
        # Filter categories based on available tables
        available_categories = {}
        for cat_key, cat_info in ARTIFACT_CATEGORIES.items():
            # Check if any of the category's tables exist
            if any(table in available_tables for table in cat_info['tables']):
                available_categories[cat_key] = cat_info
        
        return render_template('analysis/home.html', 
                             case=case, 
                             categories=available_categories,
                             table_stats=table_stats)
        
    except Exception as e:
        current_app.logger.error(f"Error loading analysis page for case {case_id}: {e}")
        return render_template('errors/500.html'), 500

@analysis_bp.route('/<case_id>/<category>')
@analysis_bp.route('/<case_id>/<category>/<subcategory>')
def view_category(case_id, category, subcategory=None):
    """View specific artifact category or subcategory"""
    try:
        case_uuid = UUID(case_id)
        case = Case.query.get_or_404(case_uuid)
        
        if category not in ARTIFACT_CATEGORIES:
            return render_template('errors/404.html'), 404
        
        cat_info = ARTIFACT_CATEGORIES[category]
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Get filtering parameters
        filters = {}
        for key, value in request.args.items():
            if key not in ['page', 'per_page'] and value:
                filters[key] = value
        
        # Determine which table to query
        table_name = cat_info['tables'][0]  # Default to first table
        if subcategory and 'subcategories' in cat_info:
            # Map subcategory to specific table if needed
            subcategory_mapping = {
                'connections': 'network_connections',
                'firewall': 'firewall_rules',
                'services': 'systemd_services',
                'packages': 'installed_packages',
                'scheduled': 'cron_jobs',
                'auth': 'auth_logs',
                'system': 'system_logs',
                'kernel': 'kernel_logs',
                'filesystem': 'file_system',
                'recent': 'recent_files',
                'history': 'browsing_history',
                'downloads': 'browser_downloads'
            }
            table_name = subcategory_mapping.get(subcategory, table_name)
        
        # Build query based on category
        data, total_count, columns = get_category_data(
            case.schema_name, table_name, page, per_page, filters
        )
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return render_template('analysis/category.html',
                             case=case,
                             category=category,
                             subcategory=subcategory,
                             cat_info=cat_info,
                             data=data,
                             columns=columns,
                             pagination={
                                 'page': page,
                                 'per_page': per_page,
                                 'total': total_count,
                                 'total_pages': total_pages,
                                 'has_prev': has_prev,
                                 'has_next': has_next
                             },
                             filters=filters)
        
    except Exception as e:
        current_app.logger.error(f"Error viewing category {category} for case {case_id}: {e}")
        return render_template('errors/500.html'), 500

@analysis_bp.route('/api/<case_id>/<category>/data')
def get_category_data_api(case_id, category):
    """API endpoint for category data (for AJAX/DataTables)"""
    try:
        case_uuid = UUID(case_id)
        case = Case.query.get_or_404(case_uuid)
        
        if category not in ARTIFACT_CATEGORIES:
            return jsonify({'error': 'Invalid category'}), 400
        
        # Get DataTables parameters
        draw = request.args.get('draw', type=int)
        start = request.args.get('start', 0, type=int)
        length = request.args.get('length', 50, type=int)
        search_value = request.args.get('search[value]', '')
        
        # Calculate page from start and length
        page = (start // length) + 1
        
        cat_info = ARTIFACT_CATEGORIES[category]
        table_name = cat_info['tables'][0]
        
        # Build filters from search
        filters = {}
        if search_value:
            filters['search'] = search_value
        
        data, total_count, columns = get_category_data(
            case.schema_name, table_name, page, length, filters
        )
        
        # Format for DataTables
        response = {
            'draw': draw,
            'recordsTotal': total_count,
            'recordsFiltered': total_count,  # TODO: Implement proper filtering
            'data': data
        }
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error getting category data API: {e}")
        return jsonify({'error': 'Failed to load data'}), 500

@analysis_bp.route('/api/<case_id>/search')
def search_artifacts(case_id):
    """Global search across all artifact types"""
    try:
        case_uuid = UUID(case_id)
        case = Case.query.get_or_404(case_uuid)
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'results': []})
        
        results = []
        available_tables = get_case_tables(case.schema_name)
        
        # Search across different tables
        search_tables = {
            'user_accounts': ['username', 'home_directory'],
            'processes': ['name', 'command', 'user'],
            'network_connections': ['local_address', 'remote_address'],
            'auth_logs': ['username', 'message', 'source_ip'],
            'browsing_history': ['url', 'title']
        }
        
        for table_name, search_columns in search_tables.items():
            if table_name in available_tables:
                table_results = search_in_table(
                    case.schema_name, table_name, search_columns, query
                )
                results.extend(table_results)
        
        return jsonify({'results': results[:50]})  # Limit to 50 results
        
    except Exception as e:
        current_app.logger.error(f"Error searching artifacts: {e}")
        return jsonify({'error': 'Search failed'}), 500

def get_category_data(schema_name, table_name, page, per_page, filters):
    """Get data for a specific category with pagination and filtering"""
    try:
        # Get total count
        count_query = f"SELECT COUNT(*) FROM {schema_name}.{table_name}"
        result = execute_case_query(schema_name, count_query)
        total_count = result.scalar()
        
        # Get column names
        columns_query = f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{schema_name}' 
            AND table_name = '{table_name}'
            ORDER BY ordinal_position
        """
        result = execute_case_query(schema_name, columns_query)
        columns = [row[0] for row in result.fetchall()]
        
        # Build data query with pagination
        offset = (page - 1) * per_page
        data_query = f"""
            SELECT * FROM {schema_name}.{table_name}
            ORDER BY id DESC
            LIMIT {per_page} OFFSET {offset}
        """
        
        result = execute_case_query(schema_name, data_query)
        rows = result.fetchall()
        
        # Convert to list of dictionaries
        data = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                # Handle datetime objects
                if isinstance(value, datetime):
                    value = value.isoformat()
                row_dict[column] = value
            data.append(row_dict)
        
        return data, total_count, columns
        
    except Exception as e:
        current_app.logger.error(f"Error getting category data: {e}")
        return [], 0, []

def search_in_table(schema_name, table_name, search_columns, query):
    """Search for a query in specific columns of a table"""
    try:
        # Build search conditions
        conditions = []
        for column in search_columns:
            conditions.append(f"{column}::text ILIKE '%{query}%'")
        
        search_query = f"""
            SELECT *, '{table_name}' as source_table
            FROM {schema_name}.{table_name}
            WHERE {' OR '.join(conditions)}
            LIMIT 10
        """
        
        result = execute_case_query(schema_name, search_query)
        rows = result.fetchall()
        
        # Get column names
        columns_query = f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{schema_name}' 
            AND table_name = '{table_name}'
            ORDER BY ordinal_position
        """
        result = execute_case_query(schema_name, columns_query)
        columns = [row[0] for row in result.fetchall()]
        columns.append('source_table')
        
        # Convert to dictionaries
        results = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i] if i < len(row) else None
                if isinstance(value, datetime):
                    value = value.isoformat()
                row_dict[column] = value
            results.append(row_dict)
        
        return results
        
    except Exception as e:
        current_app.logger.error(f"Error searching in table {table_name}: {e}")
        return []