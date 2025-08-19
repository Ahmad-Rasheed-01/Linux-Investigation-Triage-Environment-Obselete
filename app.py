#!/usr/bin/env python3
"""
LITE - Linux Investigation & Triage Environment
Main Flask Application Entry Point

A digital forensics web application for processing and visualizing
JSON artifacts collected from Linux systems.
"""

import os
import sys
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import Config
    from app.database import db, init_db, check_db_connection
    from app.models import Case, IngestionLog, SystemSettings
    from app.routes import main_bp, cases_bp, analysis_bp, api_bp
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {e}")
    print("Please ensure all dependencies are installed:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

logger = logging.getLogger(__name__)

def setup_environment():
    """Setup environment variables and configuration."""
    # Set default environment variables if not already set
    os.environ.setdefault('FLASK_APP', 'app.py')
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', '1')
    
    # Create uploads directory if it doesn't exist
    upload_dir = os.environ.get('UPLOAD_FOLDER', 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        logger.info(f"Created uploads directory: {upload_dir}")

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Test PostgreSQL connection on startup
    with app.app_context():
        if not check_db_connection():
            print("ERROR: PostgreSQL database is not accessible!")
            print("Please ensure PostgreSQL is running and connection details are correct.")
            print("Check your DATABASE_URL configuration in config.py")
            sys.exit(1)
        
        # Initialize database
        init_db()
        
        # Create tables if they don't exist
        db.create_all()
        
        # Initialize system settings if needed
        if not SystemSettings.query.first():
            logger.info("Initializing system settings...")
            settings = SystemSettings(
                setting_key='app_initialized',
                setting_value=str(datetime.utcnow()),
                description='Application initialization timestamp'
            )
            db.session.add(settings)
            
            version_setting = SystemSettings(
                setting_key='app_version',
                setting_value='1.0.0',
                description='LITE application version'
            )
            db.session.add(version_setting)
            
            try:
                db.session.commit()
                logger.info("System settings initialized")
            except Exception as e:
                db.session.rollback()
                logger.warning(f"Could not initialize system settings: {e}")
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(cases_bp, url_prefix='/cases')
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/lite.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('LITE startup')
    
    return app

def main():
    """Main entry point for the LITE application."""
    print("="*60)
    print("LITE - Linux Investigation & Triage Environment")
    print("Digital Forensics Web Application")
    print("="*60)
    print()
    
    # Setup environment
    setup_environment()
    
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"ERROR: Python 3.8+ required, found {sys.version}")
        sys.exit(1)
    
    try:
        # Initialize application
        app = create_app()
        
        # Get configuration
        host = os.environ.get('FLASK_HOST', '127.0.0.1')
        port = int(os.environ.get('FLASK_PORT', 5000))
        debug = os.environ.get('FLASK_DEBUG', '1').lower() in ('1', 'true', 'yes')
        
        print(f"Starting LITE server...")
        print(f"Server will be available at:")
        print(f"  - http://{host}:{port}")
        print(f"  - http://localhost:{port}")
        print()
        print("Press Ctrl+C to stop the server")
        print("="*60)
        print()
        
        # Start the Flask development server
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=debug
        )
        
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        logger.info("LITE server stopped by user")
    except Exception as e:
        print(f"\nERROR: Failed to start server: {e}")
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
    finally:
        print("\nThank you for using LITE!")
        print("="*60)

if __name__ == '__main__':
    main()