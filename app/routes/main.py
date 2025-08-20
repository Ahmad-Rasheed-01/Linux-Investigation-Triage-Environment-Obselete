#!/usr/bin/env python3
"""
Main routes for LITE application

Handles the main dashboard and home page routes.
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from sqlalchemy import func, text
from app.database import db
from app.models import Case, IngestionLog
from datetime import datetime, timedelta
import logging

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main dashboard - consolidated overview of all cases"""
    try:
        # Get case statistics
        total_cases = Case.query.count()
        active_cases = Case.query.filter_by(status='active').count()
        inactive_cases = Case.query.filter_by(status='inactive').count()
        closed_cases = Case.query.filter_by(status='closed').count()
        
        # Get recent cases (last 10)
        recent_cases = Case.query.order_by(Case.updated_at.desc()).limit(10).all()
        
        # Get ingestion statistics
        total_ingestions = IngestionLog.query.count()
        successful_ingestions = IngestionLog.query.filter_by(status='success').count()
        failed_ingestions = IngestionLog.query.filter_by(status='failed').count()
        
        # Get recent ingestion activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_ingestions = IngestionLog.query.filter(
            IngestionLog.started_at >= yesterday
        ).order_by(IngestionLog.started_at.desc()).limit(20).all()
        
        # Calculate total data processed
        total_data_size = db.session.query(func.sum(Case.total_file_size)).scalar() or 0
        
        # Get case priority distribution
        priority_stats = db.session.query(
            Case.case_priority,
            func.count(Case.id)
        ).group_by(Case.case_priority).all()
        
        # Get monthly case creation trend (last 6 months)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        
        # PostgreSQL-compatible date grouping
        monthly_cases = db.session.query(
            func.to_char(Case.created_at, 'YYYY-MM').label('month'),
            func.count(Case.id).label('count')
        ).filter(
            Case.created_at >= six_months_ago
        ).group_by(
            func.to_char(Case.created_at, 'YYYY-MM')
        ).order_by('month').all()
        
        # Prepare data for template
        stats = {
            'total_cases': total_cases,
            'active_cases': active_cases,
            'inactive_cases': inactive_cases,
            'closed_cases': closed_cases,
            'total_ingestions': total_ingestions,
            'successful_ingestions': successful_ingestions,
            'failed_ingestions': failed_ingestions,
            'total_data_gb': round(total_data_size / 1024, 2),
            'case_status_distribution': {
                'active': active_cases,
                'inactive': inactive_cases,
                'closed': closed_cases
            },
            'priority_distribution': dict(priority_stats),
            'monthly_trends': [
                {
                    'month': month if month else '',
                    'count': count
                } for month, count in monthly_cases
            ]
        }
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             recent_cases=recent_cases, 
                             recent_ingestions=recent_ingestions)
        
    except Exception as e:
        current_app.logger.error(f"Error loading main dashboard: {e}")
        return render_template('errors/500.html'), 500

@main_bp.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'disconnected',
            'error': str(e)
        }), 500

@main_bp.route('/about')
def about():
    """About page with application information"""
    return render_template('main/about.html')

@main_bp.route('/help')
def help_page():
    """Help and documentation page"""
    return render_template('main/help.html')

@main_bp.route('/api/dashboard/stats')
def dashboard_stats_api():
    """API endpoint for dashboard statistics (for AJAX updates)"""
    try:
        # Get case statistics
        total_cases = Case.query.count()
        active_cases = Case.query.filter_by(status='active').count()
        inactive_cases = Case.query.filter_by(status='inactive').count()
        closed_cases = Case.query.filter_by(status='closed').count()
        
        # Get ingestion statistics
        total_ingestions = IngestionLog.query.count()
        successful_ingestions = IngestionLog.query.filter_by(status='success').count()
        failed_ingestions = IngestionLog.query.filter_by(status='failed').count()
        
        # Calculate total data processed
        total_data_size = db.session.query(func.sum(Case.total_file_size)).scalar() or 0
        
        # Get case priority distribution
        priority_stats = db.session.query(
            Case.case_priority,
            func.count(Case.id)
        ).group_by(Case.case_priority).all()
        
        # Get monthly case creation trend (last 6 months)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        
        # PostgreSQL-compatible date grouping
        monthly_cases = db.session.query(
            func.to_char(Case.created_at, 'YYYY-MM').label('month'),
            func.count(Case.id).label('count')
        ).filter(
            Case.created_at >= six_months_ago
        ).group_by(
            func.to_char(Case.created_at, 'YYYY-MM')
        ).order_by('month').all()
        
        stats = {
            'total_cases': total_cases,
            'active_cases': active_cases,
            'inactive_cases': inactive_cases,
            'closed_cases': closed_cases,
            'total_ingestions': total_ingestions,
            'successful_ingestions': successful_ingestions,
            'failed_ingestions': failed_ingestions,
            'total_data_gb': round(total_data_size / 1024, 2),
            'case_status_distribution': {
                'active': active_cases,
                'inactive': inactive_cases,
                'closed': closed_cases
            },
            'priority_distribution': dict(priority_stats),
            'monthly_trends': [
                {
                    'month': month if month else '',
                    'count': count
                } for month, count in monthly_cases
            ],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        current_app.logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500