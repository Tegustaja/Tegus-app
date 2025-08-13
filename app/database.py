"""
Database configuration and session management
"""
from database.config import get_db, get_session_local
from database.models import Base

# Re-export for backward compatibility
__all__ = ['get_db', 'get_session_local', 'Base']
