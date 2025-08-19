"""
LITE - Linux Investigation & Triage Environment
File Utilities

This module contains utility functions for file operations,
including file validation, size calculations, and upload handling.
"""

import os
import json
import logging
from werkzeug.utils import secure_filename
from flask import current_app

logger = logging.getLogger(__name__)

def validate_file_upload(file):
    """
    Validate uploaded file for security and format requirements.
    
    Args:
        file: FileStorage object from Flask request
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "No file selected"
    
    # Check file extension
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'json'})
    if not allowed_filename(file.filename, allowed_extensions):
        return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
    
    # Check file size
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024)  # 500MB default
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    if file_size > max_size:
        return False, f"File too large. Maximum size: {format_file_size(max_size)}"
    
    if file_size == 0:
        return False, "File is empty"
    
    # Validate JSON format for JSON files
    if file.filename.lower().endswith('.json'):
        try:
            content = file.read()
            file.seek(0)  # Reset file pointer
            
            # Try to parse JSON
            json.loads(content.decode('utf-8'))
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {str(e)}"
        except UnicodeDecodeError:
            return False, "File encoding not supported. Please use UTF-8"
    
    return True, None

def allowed_filename(filename, allowed_extensions):
    """
    Check if filename has an allowed extension.
    
    Args:
        filename (str): Name of the file
        allowed_extensions (set): Set of allowed file extensions
        
    Returns:
        bool: True if filename is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_size(file_path):
    """
    Get file size in bytes.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        int: File size in bytes, or 0 if file doesn't exist
    """
    try:
        return os.path.getsize(file_path)
    except (OSError, IOError):
        return 0

def format_file_size(size_bytes):
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def save_uploaded_file(file, upload_folder, case_uuid=None):
    """
    Save uploaded file to the specified folder.
    
    Args:
        file: FileStorage object from Flask request
        upload_folder (str): Directory to save the file
        case_uuid (str, optional): Case UUID for organizing files
        
    Returns:
        tuple: (success, file_path_or_error_message)
    """
    try:
        # Validate file first
        is_valid, error_msg = validate_file_upload(file)
        if not is_valid:
            return False, error_msg
        
        # Create secure filename
        filename = secure_filename(file.filename)
        
        # Create case-specific subdirectory if case_uuid provided
        if case_uuid:
            case_folder = os.path.join(upload_folder, f"case_{case_uuid}")
            os.makedirs(case_folder, exist_ok=True)
            file_path = os.path.join(case_folder, filename)
        else:
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
        
        # Handle filename conflicts
        counter = 1
        original_path = file_path
        while os.path.exists(file_path):
            name, ext = os.path.splitext(original_path)
            file_path = f"{name}_{counter}{ext}"
            counter += 1
        
        # Save file
        file.save(file_path)
        
        logger.info(f"File saved successfully: {file_path}")
        return True, file_path
        
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        return False, f"Failed to save file: {str(e)}"

def delete_file(file_path):
    """
    Safely delete a file.
    
    Args:
        file_path (str): Path to the file to delete
        
    Returns:
        bool: True if file deleted successfully, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted: {file_path}")
            return True
        else:
            logger.warning(f"File not found for deletion: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Failed to delete file {file_path}: {e}")
        return False

def get_file_info(file_path):
    """
    Get comprehensive information about a file.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        dict: File information including size, timestamps, etc.
    """
    try:
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        
        return {
            'path': file_path,
            'filename': os.path.basename(file_path),
            'size': stat.st_size,
            'size_formatted': format_file_size(stat.st_size),
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'accessed': stat.st_atime,
            'is_file': os.path.isfile(file_path),
            'is_readable': os.access(file_path, os.R_OK),
            'is_writable': os.access(file_path, os.W_OK)
        }
        
    except Exception as e:
        logger.error(f"Failed to get file info for {file_path}: {e}")
        return None

def read_json_file(file_path):
    """
    Read and parse a JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        tuple: (success, data_or_error_message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return True, data
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON format: {str(e)}"
    except FileNotFoundError:
        return False, "File not found"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

def write_json_file(file_path, data):
    """
    Write data to a JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        data: Data to write (must be JSON serializable)
        
    Returns:
        tuple: (success, error_message_or_none)
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True, None
    except Exception as e:
        return False, f"Error writing file: {str(e)}"

def cleanup_old_files(directory, max_age_days=30):
    """
    Clean up old files in a directory.
    
    Args:
        directory (str): Directory to clean up
        max_age_days (int): Maximum age of files to keep in days
        
    Returns:
        tuple: (files_deleted, total_size_freed)
    """
    try:
        import time
        
        if not os.path.exists(directory):
            return 0, 0
        
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        files_deleted = 0
        size_freed = 0
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        files_deleted += 1
                        size_freed += file_size
                        logger.info(f"Deleted old file: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not delete file {file_path}: {e}")
                    continue
        
        return files_deleted, size_freed
        
    except Exception as e:
        logger.error(f"Error during cleanup of {directory}: {e}")
        return 0, 0