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
from uuid import UUID

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
        # Log form data for debugging
        current_app.logger.info(f"Form data received: {dict(request.form)}")
        current_app.logger.info(f"Files received: {[f.filename for f in request.files.getlist('artifact_files')]}")
        
        # Get form data (AJAX requests can still send FormData with files)
        case_name = request.form.get('case_name', '').strip()
        case_number = request.form.get('case_number', '').strip()
        description = request.form.get('case_description', '').strip()  # Form uses 'case_description'
        investigator = request.form.get('investigator_name', '').strip()  # Form uses 'investigator_name'
        evidence_source = request.form.get('evidence_source', '').strip()
        case_priority = request.form.get('case_priority', 'medium')
        collection_date_str = request.form.get('collection_date', '')
        
        # Get uploaded files
        uploaded_files = request.files.getlist('artifact_files')
        
        current_app.logger.info(f"Parsed data - case_name: '{case_name}', investigator: '{investigator}'")
        
        # Validate required fields
        if not case_name or not investigator:
            error_msg = 'Case name and investigator are required'
            current_app.logger.warning(f"Validation failed: case_name='{case_name}', investigator='{investigator}'")
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('cases/create.html')
        
        # Check if case name already exists
        existing_case = Case.query.filter_by(case_name=case_name).first()
        if existing_case:
            error_msg = 'A case with this name already exists'
            current_app.logger.warning(f"Case name conflict: '{case_name}' already exists")
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('cases/create.html')
        
        current_app.logger.info(f"Validation passed, creating case record...")
        
        # Parse collection date
        collection_date = None
        if collection_date_str:
            current_app.logger.info(f"Parsing collection date: '{collection_date_str}'")
            try:
                # Try datetime-local format first (from HTML5 input)
                collection_date = datetime.strptime(collection_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                try:
                    # Fallback to date-only format
                    collection_date = datetime.strptime(collection_date_str, '%Y-%m-%d')
                except ValueError:
                    current_app.logger.error(f"Invalid date format: '{collection_date_str}'")
                    error_msg = 'Invalid collection date format'
                    if is_ajax:
                        return jsonify({'success': False, 'message': error_msg}), 400
                    flash(error_msg, 'error')
                    return render_template('cases/create.html')
            current_app.logger.info(f"Parsed collection date: {collection_date}")
        
        # Generate a temporary UUID for schema name
        import uuid
        temp_uuid = uuid.uuid4()
        temp_schema_name = f"case_{str(temp_uuid).replace('-', '_')}"
        
        # Create case record with schema name
        current_app.logger.info(f"Creating Case object...")
        case = Case(
            case_name=case_name,
            case_number=case_number if case_number else None,
            description=description if description else None,
            investigator=investigator,
            evidence_source=evidence_source if evidence_source else None,
            collection_date=collection_date,
            case_priority=case_priority,
            status='active',
            schema_name=temp_schema_name  # Set schema name immediately
        )
        
        current_app.logger.info(f"Case UUID: {case.case_uuid}, Schema name: {case.schema_name}")
        
        # Add case to session
        db.session.add(case)
        
        # Create case schema using the schema name
        current_app.logger.info(f"Creating case schema: {case.schema_name}")
        schema_success = create_case_schema(case.schema_name)
        if not schema_success:
            current_app.logger.error(f"Failed to create schema: {case.schema_name}")
            db.session.rollback()
            error_msg = 'Failed to create database schema for case'
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 500
            flash(error_msg, 'error')
            return render_template('cases/create.html')
        
        # Commit the transaction
        current_app.logger.info(f"Committing case creation...")
        db.session.commit()
        current_app.logger.info(f"Case created successfully with ID: {case.id}")
        
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

@cases_bp.route('/<case_id>')
def view_case(case_id):
    """View case details and dashboard"""
    try:
        # Convert string UUID to UUID object
        case_uuid = UUID(case_id)
        case = Case.query.get_or_404(case_uuid)
        
        # Get case tables and their row counts
        tables = get_case_tables(case.schema_name)
        table_stats = {}
        
        for table in tables:
            row_count = get_table_row_count(case.schema_name, table)
            table_stats[table] = row_count
        
        # Get recent ingestion logs
        recent_logs = IngestionLog.query.filter_by(case_id=case.id).order_by(
            IngestionLog.started_at.desc()
        ).limit(10).all()
        
        # Debug logging
        import sys
        print(f"DEBUG: Case ID: {case.id}, Case UUID: {case.case_uuid}")
        sys.stdout.flush()
        print(f"DEBUG: Recent logs count: {len(recent_logs)}")
        sys.stdout.flush()
        print(f"DEBUG: All logs query: IngestionLog.query.filter_by(case_id={case.id}).all()")
        all_logs_debug = IngestionLog.query.filter_by(case_id=case.id).all()
        print(f"DEBUG: All logs count: {len(all_logs_debug)}")
        sys.stdout.flush()
        for log in recent_logs:
            print(f"DEBUG: Log: {log.filename}, Status: {log.status}, Case ID: {log.case_id}")
            sys.stdout.flush()
        
        # Also check if there are any logs with different case_id format
        all_logs_in_db = IngestionLog.query.all()
        print(f"DEBUG: Total logs in database: {len(all_logs_in_db)}")
        sys.stdout.flush()
        for log in all_logs_in_db[:5]:  # Show first 5
            print(f"DEBUG: DB Log: {log.filename}, Case ID: {log.case_id}, Status: {log.status}")
            sys.stdout.flush()
        
        # Calculate case statistics
        total_records = sum(table_stats.values())
        
        # Calculate ingestion statistics
        all_logs = IngestionLog.query.filter_by(case_id=case.id).all()
        successful_ingestions = len([log for log in all_logs if log.status == 'completed'])
        failed_ingestions = len([log for log in all_logs if log.status == 'failed'])
        total_files = len(all_logs)
        
        # Calculate total data size (approximate based on records)
        total_data_size_mb = round(total_records * 0.001, 2)  # Rough estimate
        
        stats = {
            'total_files': total_files,
            'successful_ingestions': successful_ingestions,
            'failed_ingestions': failed_ingestions,
            'total_data_size_mb': total_data_size_mb
        }
        
        return render_template('cases/view.html', 
                             case=case,
                             table_stats=table_stats,
                             total_records=total_records,
                             ingestion_logs=recent_logs,
                             stats=stats)
        
    except Exception as e:
        current_app.logger.error(f"Error viewing case {case_id}: {e}")
        flash('Error loading case details', 'error')
        return redirect(url_for('cases.list_cases'))

@cases_bp.route('/<case_id>/edit', methods=['GET', 'POST'])
def edit_case(case_id):
    """Edit case details"""
    case_uuid = UUID(case_id)
    case = Case.query.get_or_404(case_uuid)
    
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

@cases_bp.route('/<case_id>/status', methods=['POST'])
def update_case_status(case_id):
    """Update case status (activate/deactivate/close)"""
    try:
        case_uuid = UUID(case_id)
        case = Case.query.get_or_404(case_uuid)
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

@cases_bp.route('/<case_id>/delete', methods=['POST'])
def delete_case(case_id):
    """Delete a case and its schema"""
    try:
        case_uuid = UUID(case_id)
        case = Case.query.get_or_404(case_uuid)
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

@cases_bp.route('/<case_id>/upload', methods=['GET', 'POST'])
def upload_artifacts(case_id):
    """Upload JSON artifact files to a case"""
    case_uuid = UUID(case_id)
    case = Case.query.filter_by(case_uuid=case_uuid).first_or_404()
    
    if request.method == 'GET':
        return render_template('cases/upload.html', case=case)
    
    # Check if this is an AJAX request (fetch API doesn't set X-Requested-With by default)
    # We'll detect AJAX by checking if the request expects JSON or has specific headers
    is_ajax = (request.headers.get('Accept', '').find('application/json') != -1 or 
               request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
               'fetch' in request.headers.get('User-Agent', '').lower())
    
    try:
        if 'files' not in request.files:
            error_msg = 'No files selected'
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'error')
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
            error_msg = 'No valid JSON files uploaded'
            if is_ajax:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(request.url)
        
        # Start ingestion process for uploaded files
        for file_info in uploaded_files:
            start_ingestion_task(case.id, file_info['path'], file_info['filename'], file_info['size'])
        
        success_msg = f'Successfully uploaded {len(uploaded_files)} files. Ingestion started.'
        
        if is_ajax:
            return jsonify({
                'success': True, 
                'message': success_msg,
                'uploaded_count': len(uploaded_files)
            })
        
        flash(success_msg, 'success')
        return redirect(url_for('cases.view_case', case_id=case_id))
        
    except Exception as e:
        current_app.logger.error(f"Error uploading artifacts for case {case_id}: {e}")
        error_msg = f'Error uploading files: {str(e)}'
        
        if is_ajax:
            return jsonify({'success': False, 'error': error_msg}), 500
        
        flash('Error uploading files', 'error')
        return redirect(url_for('cases.upload_artifacts', case_id=case_id))