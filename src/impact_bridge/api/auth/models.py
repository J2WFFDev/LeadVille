"""Authentication models and schemas for LeadVille Impact Bridge API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User roles for role-based access control."""
    
    ADMIN = "admin"          # Full system access
    RO = "ro"               # Range Officer - competition management
    SCOREKEEPER = "scorekeeper"  # Score recording and management
    VIEWER = "viewer"        # Read-only access to results
    COACH = "coach"         # Access to specific shooters' data


class UserCredentials(BaseModel):
    """User login credentials."""
    
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class TokenData(BaseModel):
    """JWT token payload data."""
    
    username: Optional[str] = None
    role: Optional[UserRole] = None
    exp: Optional[datetime] = None
    token_type: str = "access"  # "access" or "refresh"


class TokenResponse(BaseModel):
    """Authentication token response."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration in seconds")
    user: UserInfo


class UserInfo(BaseModel):
    """User information for responses."""
    
    username: str
    role: UserRole
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    
    refresh_token: str


class User(BaseModel):
    """Internal user model."""
    
    username: str
    hashed_password: str
    role: UserRole
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    
    def to_info(self) -> UserInfo:
        """Convert to user info for responses."""
        return UserInfo(
            username=self.username,
            role=self.role,
            is_active=self.is_active,
            created_at=self.created_at,
            last_login=self.last_login
        )


class CSRFToken(BaseModel):
    """CSRF token for form protection."""
    
    token: str
    expires_at: datetime


class LoginAttempt(BaseModel):
    """Track login attempts for security."""
    
    username: str
    ip_address: str
    timestamp: datetime
    success: bool
    user_agent: Optional[str] = None