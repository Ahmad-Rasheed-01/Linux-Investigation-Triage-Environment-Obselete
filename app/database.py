#!/usr/bin/env python3
"""
Database configuration and initialization for LITE application
"""

import os
import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, create_engine
from sqlalchemy.exc import SQLAlchemyError

# Initialize SQLAlchemy instance
db = SQLAlchemy()

def init_db():
    """Initialize the database with required tables and functions"""
    try:
        # Create all tables defined in models
        db.create_all()
        
        # Load and execute the database schema SQL file
        schema_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database_schema.sql')
        
        if os.path.exists(schema_file):
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # Split the SQL file into individual statements
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    try:
                        db.session.execute(text(statement))
                    except SQLAlchemyError as e:
                        # Log the error but continue with other statements
                        logging.warning(f"Error executing SQL statement: {e}")
                        continue
            
            db.session.commit()
            logging.info("Database schema initialized successfully")
        else:
            logging.warning("Database schema file not found")
            
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        db.session.rollback()
        raise

def create_case_schema(case_name):
    """Create a new schema for a forensic case"""
    try:
        # Sanitize case name for use as schema name
        schema_name = f"case_{case_name.lower().replace(' ', '_').replace('-', '_')}"
        
        # Call the PostgreSQL function to create case schema
        result = db.session.execute(
            text("SELECT create_case_schema(:schema_name)"),
            {'schema_name': schema_name}
        )
        
        db.session.commit()
        
        success = result.scalar()
        if success:
            logging.info(f"Created schema for case: {case_name} (schema: {schema_name})")
            return schema_name
        else:
            logging.error(f"Failed to create schema for case: {case_name}")
            return None
            
    except Exception as e:
        logging.error(f"Error creating case schema: {e}")
        db.session.rollback()
        return None

def drop_case_schema(schema_name):
    """Drop a case schema and all its data"""
    try:
        # Call the PostgreSQL function to drop case schema
        result = db.session.execute(
            text("SELECT drop_case_schema(:schema_name)"),
            {'schema_name': schema_name}
        )
        
        db.session.commit()
        
        success = result.scalar()
        if success:
            logging.info(f"Dropped schema: {schema_name}")
            return True
        else:
            logging.error(f"Failed to drop schema: {schema_name}")
            return False
            
    except Exception as e:
        logging.error(f"Error dropping case schema: {e}")
        db.session.rollback()
        return False

def get_case_tables(schema_name):
    """Get list of tables in a case schema"""
    try:
        result = db.session.execute(
            text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :schema_name 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """),
            {'schema_name': schema_name}
        )
        
        tables = [row[0] for row in result.fetchall()]
        return tables
        
    except Exception as e:
        logging.error(f"Error getting case tables: {e}")
        return []

def get_table_row_count(schema_name, table_name):
    """Get row count for a specific table in a case schema"""
    try:
        result = db.session.execute(
            text(f"SELECT COUNT(*) FROM {schema_name}.{table_name}")
        )
        
        count = result.scalar()
        return count if count is not None else 0
        
    except Exception as e:
        logging.error(f"Error getting row count for {schema_name}.{table_name}: {e}")
        return 0

def execute_case_query(schema_name, query, params=None):
    """Execute a query within a specific case schema"""
    try:
        if params:
            result = db.session.execute(text(query), params)
        else:
            result = db.session.execute(text(query))
        
        return result
        
    except Exception as e:
        logging.error(f"Error executing query in schema {schema_name}: {e}")
        raise

def check_db_connection():
    """Check if database connection is working"""
    try:
        # Simple query to test connection
        result = db.session.execute(text("SELECT 1"))
        result.scalar()
        return True
    except Exception as e:
        logging.error(f"Database connection check failed: {e}")
        return False