#!/usr/bin/env python3
"""
Configuration settings for LITE application
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings - SQLite for development, PostgreSQL for production
    POSTGRES_USER = os.environ.get('POSTGRES_USER') or 'postgres'
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD') or 'password'
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST') or 'localhost'
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT') or '5432'
    POSTGRES_DB = os.environ.get('POSTGRES_DB') or 'lite_forensics'
    
    # Use SQLite for development if PostgreSQL is not available
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(basedir, "lite_dev.db")}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300
    }
    
    # File upload settings
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    ALLOWED_EXTENSIONS = {'json'}
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Application settings
    CASES_PER_PAGE = 20
    MAX_CONCURRENT_INGESTIONS = 3
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
    @staticmethod
    def init_app(app):
        """Initialize application with this config"""
        # Create upload directory if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Override with production database if available
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or Config.SQLALCHEMY_DATABASE_URI
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}