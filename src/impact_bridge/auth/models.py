"""
Authentication models for LeadVille Impact Bridge
User accounts, sessions, and role management
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey, 
    CheckConstraint, Index, func, Enum as SqlEnum
)
from sqlalchemy.orm import relationship

from ..database.models import Base


class Role(str, Enum):
    """User roles with hierarchical permissions"""
    ADMIN = "admin"          # Full system access
    RO = "ro"               # Range Officer - stage management  
    SCOREKEEPER = "scorekeeper"  # Results management
    VIEWER = "viewer"       # Read-only access
    COACH = "coach"         # Coach notes and observations


class User(Base):
    """User account with role-based access control"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=True)
    role = Column(SqlEnum(Role), nullable=False, default=Role.VIEWER)
    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)  # Default accounts created on first boot
    
    # Security fields
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=False, default=func.now())
    last_login_at = Column(DateTime, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    created_users = relationship("User", remote_side=[id])
    
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_role', 'role'),
        Index('idx_user_active', 'is_active'),
        CheckConstraint('failed_login_attempts >= 0', name='check_failed_attempts_positive'),
    )
    
    def set_password(self, password: str) -> None:
        """Set user password with secure hashing"""
        from .utils import hash_password
        self.password_hash = hash_password(password)
        self.password_changed_at = datetime.utcnow()
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        from .utils import verify_password
        return verify_password(password, self.password_hash)
    
    def is_locked(self) -> bool:
        """Check if account is locked due to failed attempts"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def increment_failed_attempts(self) -> None:
        """Increment failed login attempts and lock if needed"""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 15 minutes
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)
    
    def clear_failed_attempts(self) -> None:
        """Clear failed attempts on successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.utcnow()
    
    def has_permission(self, required_role: Role) -> bool:
        """Check if user has required role permissions (hierarchical)"""
        if not self.is_active or self.is_locked():
            return False
            
        role_hierarchy = {
            Role.ADMIN: 5,
            Role.RO: 4,
            Role.SCOREKEEPER: 3, 
            Role.COACH: 2,
            Role.VIEWER: 1
        }
        
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level


class UserSession(Base):
    """User session management for JWT tokens"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token_jti = Column(String(36), nullable=False, unique=True)  # JWT ID
    refresh_token_hash = Column(String(255), nullable=True)
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    login_method = Column(String(20), nullable=False, default='password')
    
    # Session lifecycle
    created_at = Column(DateTime, nullable=False, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, nullable=False, default=func.now())
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index('idx_session_token', 'token_jti'),
        Index('idx_session_user', 'user_id'),
        Index('idx_session_expires', 'expires_at'),
        Index('idx_session_revoked', 'revoked_at'),
    )
    
    def is_active(self) -> bool:
        """Check if session is still active"""
        now = datetime.utcnow()
        return (
            self.revoked_at is None and
            self.expires_at > now
        )
    
    def revoke(self) -> None:
        """Revoke the session"""
        self.revoked_at = datetime.utcnow()
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity_at = datetime.utcnow()
    
    def generate_refresh_token(self) -> str:
        """Generate and store refresh token"""
        refresh_token = secrets.token_urlsafe(32)
        from .utils import hash_password
        self.refresh_token_hash = hash_password(refresh_token)
        return refresh_token
    
    def verify_refresh_token(self, token: str) -> bool:
        """Verify refresh token"""
        if self.refresh_token_hash is None:
            return False
        from .utils import verify_password
        return verify_password(token, self.refresh_token_hash)