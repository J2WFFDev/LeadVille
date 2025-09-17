"""
Authentication utility functions
Password hashing, JWT token generation and verification
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
import bcrypt


# JWT Configuration
JWT_SECRET_KEY = None  # Will be initialized on first use
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7


def get_jwt_secret() -> str:
    """Get or generate JWT secret key"""
    global JWT_SECRET_KEY
    if JWT_SECRET_KEY is None:
        # In production, this should come from environment or config file
        JWT_SECRET_KEY = secrets.token_urlsafe(32)
    return JWT_SECRET_KEY


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    password_bytes = password.encode('utf-8')
    hash_bytes = bcrypt.hashpw(password_bytes, salt)
    return hash_bytes.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against bcrypt hash"""
    try:
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


def generate_token(
    user_id: int,
    username: str,
    role: str,
    session_jti: str,
    token_type: str = "access"
) -> str:
    """Generate JWT access or refresh token"""
    now = datetime.utcnow()
    
    if token_type == "access":
        expires_delta = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    else:  # refresh token
        expires_delta = timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    expires_at = now + expires_delta
    
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "session_jti": session_jti,
        "token_type": token_type,
        "iat": now,
        "exp": expires_at,
        "jti": str(uuid.uuid4())  # Unique token ID
    }
    
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        
        # Verify token type
        if payload.get("token_type") != token_type:
            return None
            
        return payload
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_session_jti() -> str:
    """Generate unique session JTI (JWT ID)"""
    return str(uuid.uuid4())


def create_default_admin() -> Dict[str, str]:
    """Create default admin credentials for first boot"""
    # Generate secure random password
    password = secrets.token_urlsafe(12)
    
    return {
        "username": "admin",
        "password": password,
        "full_name": "Default Administrator",
        "role": "admin"
    }