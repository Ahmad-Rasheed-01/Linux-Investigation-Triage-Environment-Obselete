#!/usr/bin/env python3
"""
SQLAlchemy models for LITE application
"""

from datetime import datetime
from enum import Enum
from app.database import db
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
import uuid

class CaseStatus(Enum):
    """Enumeration for case status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"

class Case(db.Model):
    """Model for forensic investigation cases"""
    __tablename__ = 'cases'
    
    id = Column(Integer, primary_key=True)
    case_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    case_name = Column(String(255), unique=True, nullable=False)
    case_number = Column(String(100), unique=True, nullable=True)
    description = Column(Text, nullable=True)
    investigator = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    status = Column(String(20), default=CaseStatus.ACTIVE.value, nullable=False)
    schema_name = Column(String(255), unique=True, nullable=False)
    
    # Case metadata
    evidence_source = Column(String(500), nullable=True)
    collection_date = Column(DateTime, nullable=True)
    case_priority = Column(String(20), default='medium', nullable=False)  # low, medium, high, critical
    
    # Statistics (updated when artifacts are ingested)
    total_artifacts = Column(Integer, default=0, nullable=False)
    total_file_size = Column(Float, default=0.0, nullable=False)  # in MB
    ingestion_status = Column(String(50), default='pending', nullable=False)  # pending, in_progress, completed, failed
    
    # Additional metadata as JSON
    case_metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f'<Case {self.case_name}>'
    
    def to_dict(self):
        """Convert case to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'case_uuid': str(self.case_uuid),
            'case_name': self.case_name,
            'case_number': self.case_number,
            'description': self.description,
            'investigator': self.investigator,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status': self.status,
            'schema_name': self.schema_name,
            'evidence_source': self.evidence_source,
            'collection_date': self.collection_date.isoformat() if self.collection_date else None,
            'case_priority': self.case_priority,
            'total_artifacts': self.total_artifacts,
            'total_file_size': self.total_file_size,
            'ingestion_status': self.ingestion_status,
            'metadata': self.metadata
        }
    
    @classmethod
    def get_active_cases(cls):
        """Get all active cases"""
        return cls.query.filter_by(status=CaseStatus.ACTIVE.value).all()
    
    @classmethod
    def get_by_schema_name(cls, schema_name):
        """Get case by schema name"""
        return cls.query.filter_by(schema_name=schema_name).first()
    
    def activate(self):
        """Activate the case"""
        self.status = CaseStatus.ACTIVE.value
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate the case"""
        self.status = CaseStatus.INACTIVE.value
        self.updated_at = datetime.utcnow()
    
    def close(self):
        """Close the case"""
        self.status = CaseStatus.CLOSED.value
        self.updated_at = datetime.utcnow()

class IngestionLog(db.Model):
    """Model for tracking JSON file ingestion logs"""
    __tablename__ = 'ingestion_logs'
    
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, db.ForeignKey('cases.id'), nullable=False)
    filename = Column(String(500), nullable=False)
    file_size = Column(Float, nullable=False)  # in MB
    artifact_type = Column(String(100), nullable=False)
    records_processed = Column(Integer, default=0, nullable=False)
    status = Column(String(50), nullable=False)  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    processing_time = Column(Float, nullable=True)  # in seconds
    
    # Relationship
    case = db.relationship('Case', backref=db.backref('ingestion_logs', lazy=True))
    
    def __repr__(self):
        return f'<IngestionLog {self.filename} - {self.status}>'
    
    def to_dict(self):
        """Convert ingestion log to dictionary"""
        return {
            'id': self.id,
            'case_id': self.case_id,
            'filename': self.filename,
            'file_size': self.file_size,
            'artifact_type': self.artifact_type,
            'records_processed': self.records_processed,
            'status': self.status,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'processing_time': self.processing_time
        }

class SystemSettings(db.Model):
    """Model for application system settings"""
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(Text, nullable=True)
    setting_type = Column(String(50), default='string', nullable=False)  # string, integer, boolean, json
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<SystemSettings {self.setting_key}>'
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get a system setting value"""
        setting = cls.query.filter_by(setting_key=key).first()
        if setting:
            if setting.setting_type == 'boolean':
                return setting.setting_value.lower() in ('true', '1', 'yes')
            elif setting.setting_type == 'integer':
                return int(setting.setting_value)
            elif setting.setting_type == 'json':
                import json
                return json.loads(setting.setting_value)
            else:
                return setting.setting_value
        return default
    
    @classmethod
    def set_setting(cls, key, value, setting_type='string', description=None):
        """Set a system setting value"""
        setting = cls.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = str(value)
            setting.setting_type = setting_type
            setting.updated_at = datetime.utcnow()
            if description:
                setting.description = description
        else:
            setting = cls(
                setting_key=key,
                setting_value=str(value),
                setting_type=setting_type,
                description=description
            )
            db.session.add(setting)
        
        db.session.commit()
        return setting