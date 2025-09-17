"""
Authentication service and decorators
JWT-based authentication with role-based access control
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from functools import wraps

from flask import request, jsonify, g, current_app
from sqlalchemy.orm import Session

from ..database.models import User, UserSession, Role
from .utils import (
    verify_token, generate_token, generate_session_jti,
    hash_password, verify_password, create_default_admin
)
from ..database import get_database_session


class AuthService:
    """Authentication service for LeadVille Impact Bridge"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Authenticate user and create session"""
        
        # Find user
        user = self.db.query(User).filter(
            User.username == username,
            User.is_active == True
        ).first()
        
        if not user:
            return {"success": False, "error": "Invalid credentials"}
        
        # Check if account is locked
        if user.is_locked():
            return {
                "success": False,
                "error": "Account locked due to too many failed attempts",
                "locked_until": user.locked_until.isoformat() if user.locked_until else None
            }
        
        # Verify password
        if not user.verify_password(password):
            user.increment_failed_attempts()
            self.db.commit()
            return {"success": False, "error": "Invalid credentials"}
        
        # Clear failed attempts on successful authentication
        user.clear_failed_attempts()
        
        # Create new session
        session_jti = generate_session_jti()
        expires_at = datetime.utcnow() + timedelta(minutes=30)  # 30 minute sessions
        
        user_session = UserSession(
            user_id=user.id,
            token_jti=session_jti,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        # Generate refresh token
        refresh_token = user_session.generate_refresh_token()
        
        self.db.add(user_session)
        self.db.commit()
        
        # Generate JWT tokens
        access_token = generate_token(
            user_id=user.id,
            username=user.username,
            role=user.role.value,
            session_jti=session_jti,
            token_type="access"
        )
        
        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 1800,  # 30 minutes
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value
            }
        }
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        
        # Find session by refresh token
        sessions = self.db.query(UserSession).join(User).filter(
            User.is_active == True
        ).all()
        
        user_session = None
        for session in sessions:
            if session.verify_refresh_token(refresh_token) and session.is_active():
                user_session = session
                break
        
        if not user_session:
            return {"success": False, "error": "Invalid refresh token"}
        
        user = user_session.user
        
        # Generate new access token
        access_token = generate_token(
            user_id=user.id,
            username=user.username,
            role=user.role.value,
            session_jti=user_session.token_jti,
            token_type="access"
        )
        
        # Update session activity
        user_session.update_activity()
        self.db.commit()
        
        return {
            "success": True,
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 1800
        }
    
    def revoke_session(self, session_jti: str) -> bool:
        """Revoke user session"""
        session = self.db.query(UserSession).filter(
            UserSession.token_jti == session_jti
        ).first()
        
        if session:
            session.revoke()
            self.db.commit()
            return True
        
        return False
    
    def get_user_from_token(self, token: str) -> Optional[User]:
        """Get user from JWT access token"""
        payload = verify_token(token, "access")
        if not payload:
            return None
        
        # Verify session is still active
        session = self.db.query(UserSession).filter(
            UserSession.token_jti == payload["session_jti"]
        ).first()
        
        if not session or not session.is_active():
            return None
        
        # Update activity and return user
        session.update_activity()
        self.db.commit()
        
        return session.user
    
    def create_user(
        self,
        username: str,
        password: str,
        full_name: str,
        role: Role,
        created_by_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create new user account"""
        
        # Check if username already exists
        existing = self.db.query(User).filter(User.username == username).first()
        if existing:
            return {"success": False, "error": "Username already exists"}
        
        # Create user
        user = User(
            username=username,
            full_name=full_name,
            role=role,
            created_by=created_by_id
        )
        user.set_password(password)
        
        self.db.add(user)
        self.db.commit()
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value
            }
        }
    
    def setup_default_users(self) -> Dict[str, Any]:
        """Create default users on first boot"""
        
        # Check if any users exist
        existing_users = self.db.query(User).count()
        if existing_users > 0:
            return {"success": False, "error": "Users already exist"}
        
        # Create default admin
        admin_creds = create_default_admin()
        
        admin_user = User(
            username=admin_creds["username"],
            full_name=admin_creds["full_name"],
            role=Role.ADMIN,
            is_default=True
        )
        admin_user.set_password(admin_creds["password"])
        
        # Create default viewer account
        viewer_user = User(
            username="viewer",
            full_name="Default Viewer",
            role=Role.VIEWER,
            is_default=True
        )
        viewer_user.set_password("viewer123")
        
        self.db.add(admin_user)
        self.db.add(viewer_user)
        self.db.commit()
        
        return {
            "success": True,
            "message": "Default users created",
            "accounts": [
                {
                    "username": admin_creds["username"],
                    "password": admin_creds["password"],
                    "role": "admin",
                    "note": "CHANGE PASSWORD IMMEDIATELY"
                },
                {
                    "username": "viewer",
                    "password": "viewer123",
                    "role": "viewer",
                    "note": "Default read-only account"
                }
            ]
        }


def get_auth_service() -> AuthService:
    """Get authentication service instance"""
        from ..config import DatabaseConfig
        db_config = DatabaseConfig()
        with get_database_session(db_config) as session:
            return AuthService(session)


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
        
        try:
            token_type, token = auth_header.split(' ', 1)
            if token_type.lower() != 'bearer':
                return jsonify({"error": "Invalid token type"}), 401
        except ValueError:
            return jsonify({"error": "Invalid authorization header"}), 401
        
            from ..config import DatabaseConfig
            db_config = DatabaseConfig()
            with get_database_session(db_config) as session:
                auth_service = AuthService(session)
                user = auth_service.get_user_from_token(token)
        
        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Store user in Flask's g object for use in route handlers
        g.current_user = user
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_role(required_role: Union[Role, str]):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user = g.current_user
            
            # Convert string to Role enum if needed
            if isinstance(required_role, str):
                try:
                    role_enum = Role(required_role)
                except ValueError:
                    return jsonify({"error": "Invalid role"}), 500
            else:
                role_enum = required_role
            
            if not user.has_permission(role_enum):
                return jsonify({
                    "error": "Insufficient permissions",
                    "required_role": role_enum.value,
                    "user_role": user.role.value
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator