"""backend/budget_sync/config/settings.py"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables from the .env file(s)
load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('budget_app.log')
    ]
)


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL'
    )
    DEBUG = os.getenv('FLASK_DEBUG')  # 1 = Development, 0 = Production
    SESSION_TYPE = os.getenv("SESSION_TYPE", "filesystem")  # Default to filesystem
    SESSION_PERMANENT = False

class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DEV_DATABASE_URL',
    )
    SQLALCHEMY_RECORD_QUERIES = True
    SESSION_TYPE = "filesystem"  # Use filesystem for dev environment
    DEBUG_TB_PANELS = [
        'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
        'flask_debugtoolbar.panels.logger.LoggingPanel',
        'flask_debugtoolbar.panels.route_list.RouteListDebugPanel',
        'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel',
    ]
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing


class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_DATABASE_URL',
    )
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing

class ProductionConfig(Config):
    """Production-specific configuration."""
    # Handle Heroku's postgres:// URL format
    database_url = os.getenv('DATABASE_URL', '')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url
    SESSION_TYPE = "redis"  # Use Redis in production
    SESSION_REDIS = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Connection pooling settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,  # Maximum number of permanent connections
        'pool_timeout': 30,  # Seconds to wait before timing out
        'pool_recycle': 1800,  # Recycle connections after 30 minutes
        'max_overflow': 10,  # Allow up to 10 connections beyond pool_size
    }
    
    # Additional production settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    PROPAGATE_EXCEPTIONS = True  # Ensure we see production errors
