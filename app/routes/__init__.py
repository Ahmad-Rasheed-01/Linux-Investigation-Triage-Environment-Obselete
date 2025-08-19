#!/usr/bin/env python3
"""
Routes package for LITE application

This package contains all the Flask blueprints and route handlers
for different sections of the application.
"""

from .main import main_bp
from .cases import cases_bp
from .analysis import analysis_bp
from .api import api_bp

__all__ = ['main_bp', 'cases_bp', 'analysis_bp', 'api_bp']