"""
LITE - Linux Investigation & Triage Environment
Database Utilities

This module contains utility functions for database operations,
including PostgreSQL connection testing and case schema management.
"""

import logging
import psycopg2
from psycopg2 import sql
from sqlalchemy import text, inspect
from flask import current_app
from app.database import db

logger = logging.getLogger(__name__)

def test_postgresql_connection():
    """
    Test PostgreSQL database connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        # Get database URI from config
        database_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        
        # Parse connection parameters
        if database_uri.startswith('postgresql://'):
            # Extract connection details from URI
            import urllib.parse
            parsed = urllib.parse.urlparse(database_uri)
            
            conn_params = {
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'database': parsed.path[1:],  # Remove leading slash
                'user': parsed.username,
                'password': parsed.password
            }
            
            # Test connection
            conn = psycopg2.connect(**conn_params)
            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            logger.info(f"PostgreSQL connection successful: {version[0]}")
            return True
            
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return False

def create_case_schema(case_uuid):
    """
    Create a dedicated schema for a forensic case.
    
    Args:
        case_uuid (str): Unique identifier for the case
        
    Returns:
        bool: True if schema created successfully, False otherwise
    """
    try:
        schema_name = f"case_{case_uuid.replace('-', '_')}"
        
        # Create schema
        db.session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        
        # Read and execute schema creation SQL
        schema_file = current_app.config.get('DATABASE_SCHEMA_FILE', 'database_schema.sql')
        
        try:
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            # Replace placeholder with actual schema name
            schema_sql = schema_sql.replace('{{SCHEMA_NAME}}', schema_name)
            
            # Execute schema creation
            db.session.execute(text(schema_sql))
            db.session.commit()
            
            logger.info(f"Created schema '{schema_name}' for case {case_uuid}")
            return True
            
        except FileNotFoundError:
            logger.warning(f"Schema file {schema_file} not found, creating basic schema")
            
            # Create basic tables if schema file not found
            basic_tables = [
                f'CREATE TABLE IF NOT EXISTS "{schema_name}".collection_metadata (id SERIAL PRIMARY KEY, data JSONB, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)',
                f'CREATE TABLE IF NOT EXISTS "{schema_name}".user_accounts (id SERIAL PRIMARY KEY, data JSONB, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)',
                f'CREATE TABLE IF NOT EXISTS "{schema_name}".processes (id SERIAL PRIMARY KEY, data JSONB, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)',
                f'CREATE TABLE IF NOT EXISTS "{schema_name}".network_connections (id SERIAL PRIMARY KEY, data JSONB, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)',
                f'CREATE TABLE IF NOT EXISTS "{schema_name}".system_logs (id SERIAL PRIMARY KEY, data JSONB, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'
            ]
            
            for table_sql in basic_tables:
                db.session.execute(text(table_sql))
            
            db.session.commit()
            logger.info(f"Created basic schema '{schema_name}' for case {case_uuid}")
            return True
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create schema for case {case_uuid}: {e}")
        return False

def drop_case_schema(case_uuid):
    """
    Drop a case schema and all its data.
    
    Args:
        case_uuid (str): Unique identifier for the case
        
    Returns:
        bool: True if schema dropped successfully, False otherwise
    """
    try:
        schema_name = f"case_{case_uuid.replace('-', '_')}"
        
        # Drop schema with CASCADE to remove all objects
        db.session.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        db.session.commit()
        
        logger.info(f"Dropped schema '{schema_name}' for case {case_uuid}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to drop schema for case {case_uuid}: {e}")
        return False

def get_case_tables(case_uuid):
    """
    Get list of tables in a case schema.
    
    Args:
        case_uuid (str): Unique identifier for the case
        
    Returns:
        list: List of table names in the case schema
    """
    try:
        schema_name = f"case_{case_uuid.replace('-', '_')}"
        
        # Query information_schema to get table names
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = :schema_name 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        result = db.session.execute(query, {'schema_name': schema_name})
        tables = [row[0] for row in result.fetchall()]
        
        return tables
        
    except Exception as e:
        logger.error(f"Failed to get tables for case {case_uuid}: {e}")
        return []

def get_table_info(case_uuid, table_name):
    """
    Get information about a specific table in a case schema.
    
    Args:
        case_uuid (str): Unique identifier for the case
        table_name (str): Name of the table
        
    Returns:
        dict: Table information including row count and columns
    """
    try:
        schema_name = f"case_{case_uuid.replace('-', '_')}"
        full_table_name = f'"{schema_name}"."{table_name}"'
        
        # Get row count
        count_query = text(f'SELECT COUNT(*) FROM {full_table_name}')
        row_count = db.session.execute(count_query).scalar()
        
        # Get column information
        columns_query = text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = :schema_name AND table_name = :table_name
            ORDER BY ordinal_position
        """)
        
        result = db.session.execute(columns_query, {
            'schema_name': schema_name,
            'table_name': table_name
        })
        
        columns = []
        for row in result.fetchall():
            columns.append({
                'name': row[0],
                'type': row[1],
                'nullable': row[2] == 'YES'
            })
        
        return {
            'table_name': table_name,
            'schema_name': schema_name,
            'row_count': row_count,
            'columns': columns
        }
        
    except Exception as e:
        logger.error(f"Failed to get table info for {table_name} in case {case_uuid}: {e}")
        return None

def execute_case_query(case_uuid, query, params=None):
    """
    Execute a query within a case schema context.
    
    Args:
        case_uuid (str): Unique identifier for the case
        query (str): SQL query to execute
        params (dict): Query parameters
        
    Returns:
        list: Query results
    """
    try:
        schema_name = f"case_{case_uuid.replace('-', '_')}"
        
        # Set search path to case schema
        db.session.execute(text(f'SET search_path TO "{schema_name}", public'))
        
        # Execute query
        result = db.session.execute(text(query), params or {})
        
        # Reset search path
        db.session.execute(text('SET search_path TO public'))
        
        return result.fetchall()
        
    except Exception as e:
        # Reset search path on error
        try:
            db.session.execute(text('SET search_path TO public'))
        except:
            pass
        
        logger.error(f"Failed to execute query in case {case_uuid}: {e}")
        raise

def get_case_statistics(case_uuid):
    """
    Get comprehensive statistics for a case.
    
    Args:
        case_uuid (str): Unique identifier for the case
        
    Returns:
        dict: Case statistics including table counts and data size
    """
    try:
        schema_name = f"case_{case_uuid.replace('-', '_')}"
        
        # Get all tables in the schema
        tables = get_case_tables(case_uuid)
        
        statistics = {
            'total_tables': len(tables),
            'total_records': 0,
            'tables': {}
        }
        
        # Get statistics for each table
        for table_name in tables:
            try:
                table_info = get_table_info(case_uuid, table_name)
                if table_info:
                    statistics['tables'][table_name] = {
                        'row_count': table_info['row_count'],
                        'columns': len(table_info['columns'])
                    }
                    statistics['total_records'] += table_info['row_count']
            except Exception as e:
                logger.warning(f"Could not get statistics for table {table_name}: {e}")
                continue
        
        return statistics
        
    except Exception as e:
        logger.error(f"Failed to get statistics for case {case_uuid}: {e}")
        return {
            'total_tables': 0,
            'total_records': 0,
            'tables': {}
        }

def check_schema_exists(case_uuid):
    """
    Check if a case schema exists.
    
    Args:
        case_uuid (str): Unique identifier for the case
        
    Returns:
        bool: True if schema exists, False otherwise
    """
    try:
        schema_name = f"case_{case_uuid.replace('-', '_')}"
        
        query = text("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.schemata 
                WHERE schema_name = :schema_name
            )
        """)
        
        result = db.session.execute(query, {'schema_name': schema_name})
        return result.scalar()
        
    except Exception as e:
        logger.error(f"Failed to check schema existence for case {case_uuid}: {e}")
        return False