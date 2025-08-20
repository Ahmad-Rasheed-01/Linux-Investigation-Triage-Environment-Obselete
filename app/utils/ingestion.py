#!/usr/bin/env python3
"""
Ingestion task management utilities for LITE application

Handles background processing of uploaded JSON files.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Tuple
from app.database import db
from app.models import Case, IngestionLog
from app.ingestion import process_uploaded_file

logger = logging.getLogger(__name__)

def start_ingestion_task(case_id: int, file_path: str, filename: str, file_size: float) -> bool:
    """
    Start ingestion task for an uploaded file.
    
    Args:
        case_id: ID of the case
        file_path: Path to the uploaded file
        filename: Original filename
        file_size: File size in bytes
        
    Returns:
        bool: True if task started successfully
    """
    try:
        # Get case information
        case = Case.query.get(case_id)
        if not case:
            logger.error(f"Case {case_id} not found")
            return False
        
        # Create ingestion log entry
        log_entry = IngestionLog(
            case_id=case_id,
            filename=filename,
            file_size=file_size / (1024 * 1024),  # Convert to MB
            artifact_type='pending',  # Will be determined during processing
            status='pending',
            records_processed=0,
            started_at=datetime.utcnow()
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        # Process file immediately (synchronous for now)
        # In a production environment, this would be queued for background processing
        success, message, stats = process_uploaded_file(
            file_path, case.case_uuid, filename
        )
        
        # Update log entry with results
        log_entry.status = 'success' if success else 'failed'
        log_entry.artifact_type = stats.get('artifact_type', 'unknown')
        log_entry.records_processed = stats.get('inserted_records', 0)
        log_entry.completed_at = datetime.utcnow()
        log_entry.processing_time = (log_entry.completed_at - log_entry.started_at).total_seconds()
        
        if not success:
            log_entry.error_message = message
        
        db.session.commit()
        
        # Update case statistics
        update_case_statistics(case_id)
        
        logger.info(f"Ingestion task completed for {filename}: {message}")
        return True
        
    except Exception as e:
        logger.error(f"Error starting ingestion task for {filename}: {e}")
        
        # Update log entry with error if it exists
        try:
            if 'log_entry' in locals():
                log_entry.status = 'failed'
                log_entry.error_message = str(e)
                log_entry.completed_at = datetime.utcnow()
                db.session.commit()
        except:
            pass
        
        return False

def update_case_statistics(case_id: int) -> None:
    """
    Update case statistics after ingestion.
    
    Args:
        case_id: ID of the case to update
    """
    try:
        case = Case.query.get(case_id)
        if not case:
            return
        
        # Get ingestion statistics
        ingestion_logs = IngestionLog.query.filter_by(case_id=case_id).all()
        
        total_artifacts = len([log for log in ingestion_logs if log.status == 'success'])
        total_file_size = sum([log.file_size for log in ingestion_logs if log.status == 'success'])
        
        # Update case
        case.total_artifacts = total_artifacts
        case.total_file_size = total_file_size
        case.updated_at = datetime.utcnow()
        
        # Update ingestion status
        failed_count = len([log for log in ingestion_logs if log.status == 'failed'])
        pending_count = len([log for log in ingestion_logs if log.status in ['pending', 'processing']])
        
        if pending_count > 0:
            case.ingestion_status = 'processing'
        elif failed_count > 0 and total_artifacts == 0:
            case.ingestion_status = 'failed'
        elif failed_count > 0:
            case.ingestion_status = 'partial'
        elif total_artifacts > 0:
            case.ingestion_status = 'completed'
        else:
            case.ingestion_status = 'pending'
        
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Error updating case statistics for case {case_id}: {e}")
        db.session.rollback()

def get_ingestion_status(case_id: int = None) -> Dict[str, Any]:
    """
    Get ingestion status for a specific case or all cases.
    
    Args:
        case_id: Optional case ID to filter by
        
    Returns:
        Dict containing ingestion statistics
    """
    try:
        query = IngestionLog.query
        
        if case_id:
            query = query.filter_by(case_id=case_id)
        
        logs = query.all()
        
        stats = {
            'total': len(logs),
            'success': len([log for log in logs if log.status == 'success']),
            'failed': len([log for log in logs if log.status == 'failed']),
            'pending': len([log for log in logs if log.status in ['pending', 'processing']]),
            'total_records': sum([log.records_processed for log in logs if log.status == 'success']),
            'total_size_mb': sum([log.file_size for log in logs if log.status == 'success'])
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting ingestion status: {e}")
        return {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'pending': 0,
            'total_records': 0,
            'total_size_mb': 0
        }

def retry_failed_ingestion(log_id: int) -> Tuple[bool, str]:
    """
    Retry a failed ingestion task.
    
    Args:
        log_id: ID of the ingestion log to retry
        
    Returns:
        Tuple of (success, message)
    """
    try:
        log_entry = IngestionLog.query.get(log_id)
        if not log_entry:
            return False, "Ingestion log not found"
        
        if log_entry.status != 'failed':
            return False, "Can only retry failed ingestions"
        
        case = Case.query.get(log_entry.case_id)
        if not case:
            return False, "Associated case not found"
        
        # Construct file path (assuming it still exists)
        file_path = os.path.join(
            'uploads', 
            str(log_entry.case_id), 
            log_entry.filename
        )
        
        if not os.path.exists(file_path):
            return False, "Original file no longer exists"
        
        # Reset log entry
        log_entry.status = 'processing'
        log_entry.error_message = None
        log_entry.started_at = datetime.utcnow()
        log_entry.completed_at = None
        log_entry.processing_time = None
        
        db.session.commit()
        
        # Process file
        success, message, stats = process_uploaded_file(
            file_path, case.case_uuid, log_entry.filename
        )
        
        # Update log entry
        log_entry.status = 'success' if success else 'failed'
        log_entry.artifact_type = stats.get('artifact_type', log_entry.artifact_type)
        log_entry.records_processed = stats.get('inserted_records', 0)
        log_entry.completed_at = datetime.utcnow()
        log_entry.processing_time = (log_entry.completed_at - log_entry.started_at).total_seconds()
        
        if not success:
            log_entry.error_message = message
        
        db.session.commit()
        
        # Update case statistics
        update_case_statistics(log_entry.case_id)
        
        return success, message
        
    except Exception as e:
        logger.error(f"Error retrying ingestion {log_id}: {e}")
        return False, f"Error retrying ingestion: {str(e)}"

def cleanup_old_ingestion_logs(days: int = 30) -> int:
    """
    Clean up old ingestion logs.
    
    Args:
        days: Number of days to keep logs
        
    Returns:
        Number of logs deleted
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_logs = IngestionLog.query.filter(
            IngestionLog.started_at < cutoff_date,
            IngestionLog.status.in_(['completed', 'failed'])
        ).all()
        
        count = len(old_logs)
        
        for log in old_logs:
            db.session.delete(log)
        
        db.session.commit()
        
        logger.info(f"Cleaned up {count} old ingestion logs")
        return count
        
    except Exception as e:
        logger.error(f"Error cleaning up ingestion logs: {e}")
        db.session.rollback()
        return 0