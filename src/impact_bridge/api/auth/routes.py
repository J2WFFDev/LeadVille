"""Authentication routes for login, logout, and token management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPAuthorizationCredentials

from .dependencies import get_auth_service, get_current_active_user
from .models import (
    UserCredentials, 
    TokenResponse, 
    RefreshTokenRequest,
    UserInfo,
    CSRFToken,
    User
)
from .service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserCredentials,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Login with username and password to get JWT tokens."""
    
    try:
        token_response = auth_service.login_user(
            username=credentials.username,
            password=credentials.password
        )
        
        return token_response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """Refresh access token using refresh token."""
    
    new_access_token = auth_service.refresh_access_token(refresh_request.refresh_token)
    
    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": auth_service.access_token_expire_minutes * 60
    }


@router.post("/logout")
async def logout(
    refresh_request: RefreshTokenRequest,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """Logout user by revoking refresh token."""
    
    success = auth_service.logout_user(refresh_request.refresh_token)
    
    return {
        "message": "Logged out successfully" if success else "Logout completed",
        "success": success
    }


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> UserInfo:
    """Get current user information."""
    return current_user.to_info()


@router.get("/csrf-token", response_model=CSRFToken)
async def get_csrf_token(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> CSRFToken:
    """Get CSRF token for form protection."""
    return auth_service.create_csrf_token(current_user.username)


@router.post("/verify")
async def verify_token(
    request: Request,
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """Verify current token is valid."""
    
    return {
        "valid": True,
        "user": current_user.to_info().dict(),
        "message": "Token is valid"
    }


@router.get("/roles")
async def get_available_roles() -> dict:
    """Get list of available user roles."""
    
    from .models import UserRole
    
    roles = {
        role.value: {
            "name": role.value,
            "description": _get_role_description(role)
        }
        for role in UserRole
    }
    
    return {"roles": roles}


def _get_role_description(role) -> str:
    """Get human-readable description for user role."""
    descriptions = {
        "admin": "Full system access and administration",
        "ro": "Range Officer - competition and match management", 
        "scorekeeper": "Score recording and match data management",
        "viewer": "Read-only access to results and data",
        "coach": "Access to specific shooters' training data"
    }
    return descriptions.get(role.value, "Unknown role")