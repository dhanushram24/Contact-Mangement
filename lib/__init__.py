"""
Contact Management Library
A reusable library for contact management system
"""

from .database import DatabaseConnection, DatabaseConfig, get_db
from .queries import MasterQueries, ContactQueries, DebugQueries
from .auth import TokenManager, AuthConfig, AuthenticationService, get_auth_service

__version__ = "1.0.0"

__all__ = [
    # Database
    "DatabaseConnection",
    "DatabaseConfig",
    "get_db",
    
    # Queries
    "MasterQueries",
    "ContactQueries",
    "DebugQueries",
    
    # Authentication
    "TokenManager",
    "AuthConfig",
    "AuthenticationService",
    "get_auth_service",
]