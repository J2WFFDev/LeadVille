"""Authentication dependencies for FastAPI route protection."""

from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import User, UserRole, TokenData
from .service import AuthService


# Security scheme for JWT tokens
security = HTTPBearer()


def get_auth_service() -> AuthService:
    """Get authentication service instance."""
    # In production, this would be injected via dependency injection
    # For now, we'll create a singleton instance
    if not hasattr(get_auth_service, "_instance"):
        import os
        secret_key = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
        get_auth_service._instance = AuthService(secret_key=secret_key)
    return get_auth_service._instance


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user from JWT token."""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = auth_service.verify_token(credentials.credentials, token_type="access")
        if token_data is None or token_data.username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    user = auth_service.get_user(token_data.username)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (ensure user is not disabled)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    return current_user


def require_role(allowed_roles: List[UserRole]):
    """Create dependency to require specific user roles."""
    
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {[role.value for role in allowed_roles]}"
            )
        return current_user
    
    return role_checker


# Common role dependencies
require_admin = require_role([UserRole.ADMIN])
require_admin_or_ro = require_role([UserRole.ADMIN, UserRole.RO])
require_scorekeeper_or_higher = require_role([UserRole.ADMIN, UserRole.RO, UserRole.SCOREKEEPER])
require_any_authenticated = Depends(get_current_active_user)


async def verify_csrf_token(
    request: Request,
    x_csrf_token: Optional[str] = Header(None),
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verify CSRF token for unsafe HTTP methods."""
    
    # Only check CSRF for unsafe methods
    if request.method not in ["POST", "PUT", "DELETE", "PATCH"]:
        return
    
    if not x_csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token required for this request"
        )
    
    if not auth_service.verify_csrf_token(current_user.username, x_csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired CSRF token"
        )


class RoleBasedAccess:
    """Class for creating role-based access dependencies."""
    
    @staticmethod
    def admin_only():
        """Require admin role."""
        return require_role([UserRole.ADMIN])
    
    @staticmethod  
    def ro_or_admin():
        """Require RO or admin role."""
        return require_role([UserRole.ADMIN, UserRole.RO])
    
    @staticmethod
    def scorekeeper_or_higher():
        """Require scorekeeper, RO, or admin role."""
        return require_role([UserRole.ADMIN, UserRole.RO, UserRole.SCOREKEEPER])
    
    @staticmethod
    def any_authenticated():
        """Require any authenticated user."""
        return get_current_active_user


# Optional user dependency (for endpoints that work with or without auth)
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    
    if not credentials:
        return None
    
    try:
        token_data = auth_service.verify_token(credentials.credentials, token_type="access")
        if token_data is None or token_data.username is None:
            return None
        
        user = auth_service.get_user(token_data.username)
        return user if user and user.is_active else None
        
    except Exception:
        return None