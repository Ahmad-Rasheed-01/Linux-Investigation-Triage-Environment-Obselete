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
            
            # Split the SQL file into individual statements, handling PostgreSQL functions
            statements = []
            current_statement = ""
            in_function = False
            
            for line in schema_sql.split('\n'):
                line = line.strip()
                if not line or line.startswith('--'):
                    continue
                    
                current_statement += line + '\n'
                
                # Check if we're entering a function definition
                if 'CREATE OR REPLACE FUNCTION' in line.upper():
                    in_function = True
                
                # Check if we're ending a function definition
                if in_function and line.endswith('$$ LANGUAGE plpgsql;'):
                    in_function = False
                    statements.append(current_statement.strip())
                    current_statement = ""
                elif not in_function and line.endswith(';'):
                    statements.append(current_statement.strip())
                    current_statement = ""
            
            # Add any remaining statement
            if current_statement.strip():
                statements.append(current_statement.strip())
            
            for statement in statements:
                if statement:
                    try:
                        logging.info(f"Executing SQL statement: {statement[:100]}...")
                        db.session.execute(text(statement))
                        logging.info("Statement executed successfully")
                    except SQLAlchemyError as e:
                        # Log the error but continue with other statements
                        logging.error(f"Error executing SQL statement: {e}")
                        logging.error(f"Failed statement: {statement}")
                        continue
            
            db.session.commit()
            logging.info("Database schema initialized successfully")
        else:
            logging.warning("Database schema file not found")
            
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        db.session.rollback()
        raise

def create_case_schema(schema_name):
    """Create a new schema for a forensic case"""
    try:
        # Call the PostgreSQL function to create case schema
        result = db.session.execute(
            text("SELECT create_case_schema(:schema_name)"),
            {'schema_name': schema_name}
        )
        
        db.session.commit()
        
        success = result.scalar()
        if success:
            logging.info(f"Created schema: {schema_name}")
            return True
        else:
            logging.error(f"Failed to create schema: {schema_name}")
            return False
            
    except Exception as e:
        logging.error(f"Error creating case schema: {e}")
        db.session.rollback()
        return False

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
    """Check if PostgreSQL database connection is working"""
    try:
        # Test PostgreSQL connection with version check
        result = db.session.execute(text("SELECT version()"))
        version_info = result.scalar()
        
        # Verify it's PostgreSQL
        if not version_info or 'PostgreSQL' not in version_info:
            logging.error(f"Expected PostgreSQL but got: {version_info}")
            return False
            
        logging.info(f"PostgreSQL connection successful: {version_info}")
        return True
        
    except Exception as e:
        logging.error(f"PostgreSQL connection check failed: {e}")
        logging.error("Please ensure:")
        logging.error("1. PostgreSQL service is running")
        logging.error("2. Database credentials are correct")
        logging.error("3. Database 'lite_forensics' exists")
        logging.error("4. User has proper permissions")
        return False