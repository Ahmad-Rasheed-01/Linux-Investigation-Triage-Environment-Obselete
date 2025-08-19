"""
LITE - Linux Investigation & Triage Environment
Format Utilities

This module contains utility functions for formatting data,
timestamps, and other display-related operations.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

def format_timestamp(timestamp, format_type='datetime'):
    """
    Format timestamp for display.
    
    Args:
        timestamp: Unix timestamp, datetime object, or ISO string
        format_type (str): Type of formatting ('datetime', 'date', 'time', 'relative')
        
    Returns:
        str: Formatted timestamp string
    """
    try:
        # Handle different timestamp formats
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        elif isinstance(timestamp, str):
            # Try parsing ISO format
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            return str(timestamp)
        
        # Format based on type
        if format_type == 'datetime':
            return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        elif format_type == 'date':
            return dt.strftime('%Y-%m-%d')
        elif format_type == 'time':
            return dt.strftime('%H:%M:%S')
        elif format_type == 'relative':
            return format_relative_time(dt)
        else:
            return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            
    except Exception as e:
        logger.warning(f"Failed to format timestamp {timestamp}: {e}")
        return str(timestamp)

def format_relative_time(dt):
    """
    Format datetime as relative time (e.g., "2 hours ago").
    
    Args:
        dt (datetime): Datetime object
        
    Returns:
        str: Relative time string
    """
    try:
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        diff = now - dt
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 2592000:  # 30 days
            days = int(seconds // 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return dt.strftime('%Y-%m-%d')
            
    except Exception as e:
        logger.warning(f"Failed to format relative time: {e}")
        return str(dt)

def format_json(data, indent=2, max_length=None):
    """
    Format data as JSON string.
    
    Args:
        data: Data to format as JSON
        indent (int): JSON indentation
        max_length (int, optional): Maximum length before truncation
        
    Returns:
        str: Formatted JSON string
    """
    try:
        json_str = json.dumps(data, indent=indent, ensure_ascii=False, default=str)
        
        if max_length and len(json_str) > max_length:
            json_str = json_str[:max_length] + "..."
        
        return json_str
        
    except Exception as e:
        logger.warning(f"Failed to format JSON: {e}")
        return str(data)

def format_number(number, format_type='default'):
    """
    Format numbers for display.
    
    Args:
        number: Number to format
        format_type (str): Type of formatting ('default', 'bytes', 'percentage', 'currency')
        
    Returns:
        str: Formatted number string
    """
    try:
        if number is None:
            return "N/A"
        
        num = float(number)
        
        if format_type == 'bytes':
            return format_bytes(num)
        elif format_type == 'percentage':
            return f"{num:.1f}%"
        elif format_type == 'currency':
            return f"${num:,.2f}"
        else:
            # Default formatting with thousands separator
            if num == int(num):
                return f"{int(num):,}"
            else:
                return f"{num:,.2f}"
                
    except Exception as e:
        logger.warning(f"Failed to format number {number}: {e}")
        return str(number)

def format_bytes(bytes_value):
    """
    Format bytes in human-readable format.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        str: Formatted bytes string (e.g., "1.5 MB")
    """
    try:
        if bytes_value == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        size = float(bytes_value)
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        if i == 0:
            return f"{int(size)} {size_names[i]}"
        else:
            return f"{size:.1f} {size_names[i]}"
            
    except Exception as e:
        logger.warning(f"Failed to format bytes {bytes_value}: {e}")
        return str(bytes_value)

def format_duration(seconds):
    """
    Format duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    try:
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{int(minutes)}m {int(remaining_seconds)}s"
        else:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            return f"{int(hours)}h {int(remaining_minutes)}m"
            
    except Exception as e:
        logger.warning(f"Failed to format duration {seconds}: {e}")
        return str(seconds)

def truncate_text(text, max_length=100, suffix="..."):
    """
    Truncate text to specified length.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
        suffix (str): Suffix to add when truncated
        
    Returns:
        str: Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def format_list(items, separator=", ", max_items=None):
    """
    Format list of items for display.
    
    Args:
        items: List of items
        separator (str): Separator between items
        max_items (int, optional): Maximum number of items to show
        
    Returns:
        str: Formatted list string
    """
    try:
        if not items:
            return ""
        
        str_items = [str(item) for item in items]
        
        if max_items and len(str_items) > max_items:
            displayed_items = str_items[:max_items]
            remaining = len(str_items) - max_items
            return separator.join(displayed_items) + f" (+{remaining} more)"
        else:
            return separator.join(str_items)
            
    except Exception as e:
        logger.warning(f"Failed to format list: {e}")
        return str(items)

def format_dict_for_display(data, max_depth=3, current_depth=0):
    """
    Format dictionary for readable display.
    
    Args:
        data: Dictionary to format
        max_depth (int): Maximum nesting depth
        current_depth (int): Current nesting depth
        
    Returns:
        str: Formatted dictionary string
    """
    try:
        if current_depth >= max_depth:
            return "{...}"
        
        if not isinstance(data, dict):
            return str(data)
        
        items = []
        for key, value in data.items():
            if isinstance(value, dict):
                if current_depth < max_depth - 1:
                    formatted_value = format_dict_for_display(value, max_depth, current_depth + 1)
                else:
                    formatted_value = "{...}"
            elif isinstance(value, list):
                if len(value) > 3:
                    formatted_value = f"[{len(value)} items]"
                else:
                    formatted_value = str(value)
            else:
                formatted_value = str(value)
            
            items.append(f"{key}: {formatted_value}")
        
        return "{" + ", ".join(items) + "}"
        
    except Exception as e:
        logger.warning(f"Failed to format dict: {e}")
        return str(data)

def format_status_badge(status, status_type='default'):
    """
    Format status for badge display.
    
    Args:
        status (str): Status value
        status_type (str): Type of status ('case', 'priority', 'ingestion')
        
    Returns:
        dict: Badge formatting information
    """
    status_lower = str(status).lower()
    
    if status_type == 'case':
        status_map = {
            'active': {'class': 'badge-success', 'text': 'Active'},
            'closed': {'class': 'badge-secondary', 'text': 'Closed'},
            'archived': {'class': 'badge-warning', 'text': 'Archived'},
            'pending': {'class': 'badge-info', 'text': 'Pending'}
        }
    elif status_type == 'priority':
        status_map = {
            'high': {'class': 'badge-danger', 'text': 'High'},
            'medium': {'class': 'badge-warning', 'text': 'Medium'},
            'low': {'class': 'badge-success', 'text': 'Low'},
            'critical': {'class': 'badge-dark', 'text': 'Critical'}
        }
    elif status_type == 'ingestion':
        status_map = {
            'pending': {'class': 'badge-info', 'text': 'Pending'},
            'processing': {'class': 'badge-warning', 'text': 'Processing'},
            'completed': {'class': 'badge-success', 'text': 'Completed'},
            'failed': {'class': 'badge-danger', 'text': 'Failed'}
        }
    else:
        status_map = {}
    
    return status_map.get(status_lower, {
        'class': 'badge-secondary',
        'text': str(status).title()
    })

def format_table_data(data, column_type='text'):
    """
    Format data for table display based on column type.
    
    Args:
        data: Data to format
        column_type (str): Type of column ('text', 'timestamp', 'json', 'number', 'boolean')
        
    Returns:
        str: Formatted data for table display
    """
    try:
        if data is None:
            return ""
        
        if column_type == 'timestamp':
            return format_timestamp(data)
        elif column_type == 'json':
            if isinstance(data, (dict, list)):
                return format_json(data, indent=None, max_length=200)
            else:
                return str(data)
        elif column_type == 'number':
            return format_number(data)
        elif column_type == 'boolean':
            return "Yes" if data else "No"
        else:
            # Default text formatting
            text = str(data)
            return truncate_text(text, max_length=200)
            
    except Exception as e:
        logger.warning(f"Failed to format table data: {e}")
        return str(data)

def sanitize_filename(filename):
    """
    Sanitize filename for safe file system usage.
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    import re
    
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        filename = name[:max_name_length] + ('.' + ext if ext else '')
    
    return filename or 'unnamed_file'