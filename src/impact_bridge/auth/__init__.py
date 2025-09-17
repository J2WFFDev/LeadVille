"""
Authentication module for LeadVille Impact Bridge
Provides JWT-based authentication with role-based access control
"""

from ..database.models import User, UserSession, Role
from .auth import AuthService, require_auth, require_role
from .utils import hash_password, verify_password, generate_token, verify_token

__all__ = [
    'User', 'UserSession', 'Role', 'AuthService',
    'require_auth', 'require_role',
    'hash_password', 'verify_password', 'generate_token', 'verify_token'
]