#!/usr/bin/env python3
"""
Case management routes for LITE application

Handles all case-related operations including creation, management,
and case-specific dashboards.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from sqlalchemy import text
from app.database import db, create_case_schema, drop_case_schema, get_case_tables, get_table_row_count
from app.models import Case, IngestionLog
from app.utils.file_utils import allowed_filename, get_file_size
from app.utils.ingestion import start_ingestion_task
from datetime import datetime
import os
import uuid
import logging

cases_bp = Blueprint('cases', __name__)

@cases_bp.route('/')
def list_cases():
    """List all cases with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config.get('CASES_PER_PAGE', 20)
        status_filter = request.args.get('status', 'all')
        search_query = request.args.get('search', '')
        
        # Build query
        query = Case.query
        
        if status_filter != 'all':
            query = query.filter_by(status=status_filter)
        
        if search_query:
            query = query.filter(
                Case.case_name.ilike(f'%{search_query}%') |
                Case.case_number.ilike(f'%{search_query}%') |
                Case.investigator.ilike(f'%{search_query}%')
            )
        
        # Order by most recent first
        query = query.order_by(Case.updated_at.desc())
        
        # Paginate
        cases = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('cases/list.html', cases=cases, 
                             status_filter=status_filter, search_query=search_query)
        
    except Exception as e:
        current_app.logger.error(f"Error listing cases: {e}")
        flash('Error loading cases', 'error')
        return redirect(url_for('main.index'))

@cases_bp.route('/create', methods=['GET', 'POST'])
def create_case():
    """Create a new forensic case"""
    if request.method == 'GET':
        return render_template('cases/create.html')
    
    # Check if this is an AJAX request (look for X-Requested-With header or Accept header)
    is_ajax = (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('Accept', '') or
        request.is_json
    )
    
    try:
        # Get form data (AJAX requests can still send FormData with files)
        case_name = request.form.get('case_name', '').strip()
        case_number = request.form.get('case_number', '').strip()
        description = request.form.get('description', '').strip()
        investigator = request.form.get('investigator', '').strip()
        evidence_source = request.form.get('evidence_source', '').strip()
        case_priority = request.form.get('case_priority', 'medium')
        collection_date_str = request.form.get('collection_date', '')
        
        # Get uploaded files
        uploaded_files = request.files.getlist('artifact_files')
        
        # Validate required fields
        if not case_name or not investigator:
            error_msg = 'Case name and investigator are required'
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('cases/create.html')
        
        # Check if case name already exists
        if Case.query.filter_by(case_name=case_name).first():
            error_msg = 'A case with this name already exists'
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('cases/create.html')
        
        # Parse collection date
        collection_date = None
        if collection_date_str:
            try:
                collection_date = datetime.strptime(collection_date_str, '%Y-%m-%d')
            except ValueError:
                error_msg = 'Invalid collection date format'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('cases/create.html')
        
        # Create case schema first
        schema_name = create_case_schema(case_name)
        if not schema_name:
            error_msg = 'Failed to create database schema for case'
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 500
            flash(error_msg, 'error')
            return render_template('cases/create.html')
        
        # Create case record
        case = Case(
            case_name=case_name,
            case_number=case_number if case_number else None,
            description=description if description else None,
            investigator=investigator,
            evidence_source=evidence_source if evidence_source else None,
            collection_date=collection_date,
            case_priority=case_priority,
            schema_name=schema_name,
            status='active'
        )
        
        db.session.add(case)
        db.session.commit()
        
        current_app.logger.info(f"Created new case: {case_name} (ID: {case.id})")
        
        # Handle file uploads if any
        uploaded_count = 0
        if uploaded_files:
            try:
                # Create upload directory for this case
                case_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(case.id))
                os.makedirs(case_upload_dir, exist_ok=True)
                
                for file in uploaded_files:
                    if file.filename and allowed_filename(file.filename, {'json'}):
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(case_upload_dir, filename)
                        file.save(file_path)
                        
                        # Get file size
                        file_size = get_file_size(file_path)
                        
                        # Start ingestion process
                        start_ingestion_task(case.id, file_path, filename, file_size)
                        uploaded_count += 1
                        
            except Exception as e:
                current_app.logger.error(f"Error processing uploaded files: {e}")
                # Don't fail case creation if file upload fails
        
        # Prepare success message
        if uploaded_count > 0:
            success_msg = f'Case "{case_name}" created successfully with {uploaded_count} files uploaded. Ingestion started.'
        else:
            success_msg = f'Case "{case_name}" created successfully'
        
        if is_ajax:
            return jsonify({
                'success': True, 
                'message': success_msg,
                'case_id': case.id,
                'uploaded_files': uploaded_count,
                'redirect_url': url_for('cases.view_case', case_id=case.id)
            })
        
        flash(success_msg, 'success')
        return redirect(url_for('cases.view_case', case_id=case.id))
        
    except Exception as e:
        current_app.logger.error(f"Error creating case: {e}")
        db.session.rollback()
        error_msg = 'Error creating case'
        
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg}), 500
        
        flash(error_msg, 'error')
        return render_template('cases/create.html')

@cases_bp.route('/<int:case_id>')
def view_case(case_id):
    """View case details and dashboard"""
    try:
        case = Case.query.get_or_404(case_id)
        
        # Get case tables and their row counts
        tables = get_case_tables(case.schema_name)
        table_stats = {}
        
        for table in tables:
            row_count = get_table_row_count(case.schema_name, table)
            table_stats[table] = row_count
        
        # Get recent ingestion logs for this case
        recent_logs = IngestionLog.query.filter_by(case_id=case_id).order_by(
            IngestionLog.started_at.desc()
        ).limit(10).all()
        
        # Calculate case statistics
        total_records = sum(table_stats.values())
        
        case_data = {
            'case': case.to_dict(),
            'table_stats': table_stats,
            'total_records': total_records,
            'recent_logs': [log.to_dict() for log in recent_logs]
        }
        
        return render_template('cases/view.html', data=case_data)
        
    except Exception as e:
        current_app.logger.error(f"Error viewing case {case_id}: {e}")
        flash('Error loading case details', 'error')
        return redirect(url_for('cases.list_cases'))

@cases_bp.route('/<int:case_id>/edit', methods=['GET', 'POST'])
def edit_case(case_id):
    """Edit case details"""
    case = Case.query.get_or_404(case_id)
    
    if request.method == 'GET':
        return render_template('cases/edit.html', case=case)
    
    try:
        # Update case fields
        case.case_number = request.form.get('case_number', '').strip() or None
        case.description = request.form.get('description', '').strip() or None
        case.investigator = request.form.get('investigator', '').strip()
        case.evidence_source = request.form.get('evidence_source', '').strip() or None
        case.case_priority = request.form.get('case_priority', 'medium')
        
        collection_date_str = request.form.get('collection_date', '')
        if collection_date_str:
            try:
                case.collection_date = datetime.strptime(collection_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid collection date format', 'error')
                return render_template('cases/edit.html', case=case)
        else:
            case.collection_date = None
        
        case.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        current_app.logger.info(f"Updated case: {case.case_name} (ID: {case.id})")
        flash('Case updated successfully', 'success')
        
        return redirect(url_for('cases.view_case', case_id=case.id))
        
    except Exception as e:
        current_app.logger.error(f"Error updating case {case_id}: {e}")
        db.session.rollback()
        flash('Error updating case', 'error')
        return render_template('cases/edit.html', case=case)

@cases_bp.route('/<int:case_id>/status', methods=['POST'])
def update_case_status(case_id):
    """Update case status (activate/deactivate/close)"""
    try:
        case = Case.query.get_or_404(case_id)
        new_status = request.json.get('status')
        
        if new_status not in ['active', 'inactive', 'closed']:
            return jsonify({'error': 'Invalid status'}), 400
        
        case.status = new_status
        case.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        current_app.logger.info(f"Updated case status: {case.case_name} -> {new_status}")
        
        return jsonify({
            'success': True,
            'message': f'Case status updated to {new_status}',
            'case': case.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating case status: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update case status'}), 500

@cases_bp.route('/<int:case_id>/delete', methods=['POST'])
def delete_case(case_id):
    """Delete a case and its schema"""
    try:
        case = Case.query.get_or_404(case_id)
        schema_name = case.schema_name
        case_name = case.case_name
        
        # Delete ingestion logs first (foreign key constraint)
        IngestionLog.query.filter_by(case_id=case_id).delete()
        
        # Delete case record
        db.session.delete(case)
        db.session.commit()
        
        # Drop the case schema
        if drop_case_schema(schema_name):
            current_app.logger.info(f"Deleted case and schema: {case_name}")
            flash(f'Case "{case_name}" deleted successfully', 'success')
        else:
            current_app.logger.warning(f"Case deleted but schema cleanup failed: {schema_name}")
            flash(f'Case deleted but database cleanup may be incomplete', 'warning')
        
        return redirect(url_for('cases.list_cases'))
        
    except Exception as e:
        current_app.logger.error(f"Error deleting case {case_id}: {e}")
        db.session.rollback()
        flash('Error deleting case', 'error')
        return redirect(url_for('cases.view_case', case_id=case_id))

@cases_bp.route('/<int:case_id>/upload', methods=['GET', 'POST'])
def upload_artifacts(case_id):
    """Upload JSON artifact files to a case"""
    case = Case.query.get_or_404(case_id)
    
    if request.method == 'GET':
        return render_template('cases/upload.html', case=case)
    
    try:
        if 'files' not in request.files:
            flash('No files selected', 'error')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        uploaded_files = []
        
        for file in files:
            if file.filename == '':
                continue
            
            if file and allowed_filename(file.filename, {'json'}):
                filename = secure_filename(file.filename)
                
                # Create upload directory for this case
                case_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(case_id))
                os.makedirs(case_upload_dir, exist_ok=True)
                
                # Save file
                file_path = os.path.join(case_upload_dir, filename)
                file.save(file_path)
                
                # Get file size
                file_size = get_file_size(file_path)
                
                uploaded_files.append({
                    'filename': filename,
                    'path': file_path,
                    'size': file_size
                })
        
        if not uploaded_files:
            flash('No valid JSON files uploaded', 'error')
            return redirect(request.url)
        
        # Start ingestion process for uploaded files
        for file_info in uploaded_files:
            start_ingestion_task(case_id, file_info['path'], file_info['filename'], file_info['size'])
        
        flash(f'Successfully uploaded {len(uploaded_files)} files. Ingestion started.', 'success')
        return redirect(url_for('cases.view_case', case_id=case_id))
        
    except Exception as e:
        current_app.logger.error(f"Error uploading artifacts for case {case_id}: {e}")
        flash('Error uploading files', 'error')
        return redirect(url_for('cases.upload_artifacts', case_id=case_id))