#!/usr/bin/env python3
"""
API routes for LITE application

Provides REST API endpoints for external integrations and AJAX calls.
"""

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import text, func
from app.database import db, execute_case_query, get_case_tables, get_table_row_count
from app.models import Case, IngestionLog
from datetime import datetime, timedelta
import logging
from uuid import UUID

api_bp = Blueprint('api', __name__)

@api_bp.route('/cases', methods=['GET'])
def get_cases():
    """Get list of all cases"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        query = Case.query
        
        if status:
            query = query.filter_by(status=status)
        
        cases = query.order_by(Case.updated_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'cases': [case.to_dict() for case in cases.items],
            'pagination': {
                'page': cases.page,
                'pages': cases.pages,
                'per_page': cases.per_page,
                'total': cases.total,
                'has_next': cases.has_next,
                'has_prev': cases.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting cases via API: {e}")
        return jsonify({'error': 'Failed to retrieve cases'}), 500

@api_bp.route('/cases/<case_id>', methods=['GET'])
def get_case(case_id):
    """Get specific case details"""
    try:
        case_uuid = UUID(case_id)
        case = Case.query.get_or_404(case_uuid)
        
        # Get table statistics
        tables = get_case_tables(case.schema_name)
        table_stats = {}
        
        for table in tables:
            row_count = get_table_row_count(case.schema_name, table)
            table_stats[table] = row_count
        
        case_data = case.to_dict()
        case_data['table_statistics'] = table_stats
        case_data['total_records'] = sum(table_stats.values())
        
        return jsonify(case_data)
        
    except Exception as e:
        current_app.logger.error(f"Error getting case {case_id} via API: {e}")
        return jsonify({'error': 'Failed to retrieve case'}), 500

@api_bp.route('/cases/<case_id>/artifacts/<table_name>', methods=['GET'])
def get_case_artifacts(case_id, table_name):
    """Get artifacts from a specific table in a case"""
    try:
        case_uuid = UUID(case_id)
        case = Case.query.get_or_404(case_uuid)
        
        # Validate table exists
        available_tables = get_case_tables(case.schema_name)
        if table_name not in available_tables:
            return jsonify({'error': 'Table not found'}), 404
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM {case.schema_name}.{table_name}"
        result = execute_case_query(case.schema_name, count_query)
        total_count = result.scalar()
        
        # Get data with pagination
        offset = (page - 1) * per_page
        data_query = f"""
            SELECT * FROM {case.schema_name}.{table_name}
            ORDER BY id DESC
            LIMIT {per_page} OFFSET {offset}
        """
        
        result = execute_case_query(case.schema_name, data_query)
        rows = result.fetchall()
        
        # Get column names
        columns_query = f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{case.schema_name}' 
            AND table_name = '{table_name}'
            ORDER BY ordinal_position
        """
        result = execute_case_query(case.schema_name, columns_query)
        columns = [row[0] for row in result.fetchall()]
        
        # Convert to list of dictionaries
        data = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                if isinstance(value, datetime):
                    value = value.isoformat()
                row_dict[column] = value
            data.append(row_dict)
        
        return jsonify({
            'artifacts': data,
            'table_name': table_name,
            'columns': columns,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'total_pages': (total_count + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting artifacts for case {case_id}, table {table_name}: {e}")
        return jsonify({'error': 'Failed to retrieve artifacts'}), 500

@api_bp.route('/cases/<case_id>/query', methods=['POST'])
def execute_custom_query(case_id):
    """Execute a custom SQL query on a case schema"""
    try:
        case_uuid = UUID(case_id)
        case = Case.query.get_or_404(case_uuid)
        
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query'].strip()
        
        # Basic security check - only allow SELECT statements
        if not query.upper().startswith('SELECT'):
            return jsonify({'error': 'Only SELECT queries are allowed'}), 400
        
        # Prevent dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return jsonify({'error': f'Keyword {keyword} is not allowed'}), 400
        
        # Execute query with timeout
        result = execute_case_query(case.schema_name, query)
        rows = result.fetchall()
        
        # Get column names from result
        columns = list(result.keys()) if hasattr(result, 'keys') else []
        
        # Convert to list of dictionaries
        data = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i] if i < len(row) else None
                if isinstance(value, datetime):
                    value = value.isoformat()
                row_dict[column] = value
            data.append(row_dict)
        
        return jsonify({
            'results': data,
            'columns': columns,
            'row_count': len(data)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error executing custom query for case {case_id}: {e}")
        return jsonify({'error': f'Query execution failed: {str(e)}'}), 500

@api_bp.route('/ingestion/status', methods=['GET'])
def get_ingestion_status():
    """Get current ingestion status across all cases"""
    try:
        # Get ingestion statistics
        stats = db.session.query(
            IngestionLog.status,
            func.count(IngestionLog.id).label('count')
        ).group_by(IngestionLog.status).all()
        
        status_counts = dict(stats)
        
        # Get recent ingestion logs
        recent_logs = IngestionLog.query.order_by(
            IngestionLog.started_at.desc()
        ).limit(20).all()
        
        # Get active ingestions
        active_ingestions = IngestionLog.query.filter(
            IngestionLog.status.in_(['pending', 'processing'])
        ).all()
        
        return jsonify({
            'status_counts': status_counts,
            'recent_logs': [log.to_dict() for log in recent_logs],
            'active_ingestions': [log.to_dict() for log in active_ingestions]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting ingestion status: {e}")
        return jsonify({'error': 'Failed to get ingestion status'}), 500

@api_bp.route('/ingestion/<int:log_id>/status', methods=['GET'])
def get_ingestion_log_status(log_id):
    """Get status of a specific ingestion log"""
    try:
        log = IngestionLog.query.get_or_404(log_id)
        return jsonify(log.to_dict())
        
    except Exception as e:
        current_app.logger.error(f"Error getting ingestion log {log_id}: {e}")
        return jsonify({'error': 'Failed to get ingestion log'}), 500

@api_bp.route('/statistics/dashboard', methods=['GET'])
def get_dashboard_statistics():
    """Get comprehensive dashboard statistics"""
    try:
        # Case statistics
        case_stats = db.session.query(
            Case.status,
            func.count(Case.id).label('count')
        ).group_by(Case.status).all()
        
        # Priority distribution
        priority_stats = db.session.query(
            Case.case_priority,
            func.count(Case.id).label('count')
        ).group_by(Case.case_priority).all()
        
        # Ingestion statistics
        ingestion_stats = db.session.query(
            IngestionLog.status,
            func.count(IngestionLog.id).label('count'),
            func.sum(IngestionLog.file_size).label('total_size')
        ).group_by(IngestionLog.status).all()
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_activity = db.session.query(
            func.date(Case.created_at).label('date'),
            func.count(Case.id).label('cases_created')
        ).filter(
            Case.created_at >= week_ago
        ).group_by(
            func.date(Case.created_at)
        ).order_by('date').all()
        
        # Total data processed
        total_data = db.session.query(
            func.sum(Case.total_file_size)
        ).scalar() or 0
        
        return jsonify({
            'case_statistics': dict(case_stats),
            'priority_distribution': dict(priority_stats),
            'ingestion_statistics': {
                row.status: {
                    'count': row.count,
                    'total_size_mb': float(row.total_size or 0)
                } for row in ingestion_stats
            },
            'recent_activity': [
                {
                    'date': activity.date.isoformat(),
                    'cases_created': activity.cases_created
                } for activity in recent_activity
            ],
            'total_data_processed_mb': float(total_data),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting dashboard statistics: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500

@api_bp.route('/export/case/<case_id>', methods=['GET'])
def export_case_data(case_id):
    """Export case data in JSON format"""
    try:
        case_uuid = UUID(case_id)
        case = Case.query.get_or_404(case_uuid)
        
        # Get all tables and their data
        tables = get_case_tables(case.schema_name)
        export_data = {
            'case_info': case.to_dict(),
            'export_timestamp': datetime.utcnow().isoformat(),
            'tables': {}
        }
        
        for table_name in tables:
            # Get table data
            query = f"SELECT * FROM {case.schema_name}.{table_name}"
            result = execute_case_query(case.schema_name, query)
            rows = result.fetchall()
            
            # Get column names
            columns_query = f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = '{case.schema_name}' 
                AND table_name = '{table_name}'
                ORDER BY ordinal_position
            """
            result = execute_case_query(case.schema_name, columns_query)
            columns = [row[0] for row in result.fetchall()]
            
            # Convert to list of dictionaries
            table_data = []
            for row in rows:
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    row_dict[column] = value
                table_data.append(row_dict)
            
            export_data['tables'][table_name] = {
                'columns': columns,
                'data': table_data,
                'row_count': len(table_data)
            }
        
        return jsonify(export_data)
        
    except Exception as e:
        current_app.logger.error(f"Error exporting case {case_id}: {e}")
        return jsonify({'error': 'Failed to export case data'}), 500

# Error handlers for API blueprint
@api_bp.errorhandler(404)
def api_not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@api_bp.errorhandler(400)
def api_bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@api_bp.errorhandler(500)
def api_internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500