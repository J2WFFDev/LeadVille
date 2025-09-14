"""Authentication service for JWT and user management."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from .models import User, UserRole, TokenData, TokenResponse, CSRFToken


class AuthService:
    """Authentication service handling JWT tokens and user management."""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # In-memory user store (in production, this would be a database)
        self._users: Dict[str, User] = {}
        self._refresh_tokens: Dict[str, TokenData] = {}  # Store active refresh tokens
        self._csrf_tokens: Dict[str, CSRFToken] = {}     # Store CSRF tokens
        
        # Create default admin user
        self._create_default_users()
    
    def _create_default_users(self):
        """Create default users for development."""
        default_users = [
            {"username": "admin", "password": "admin123", "role": UserRole.ADMIN},
            {"username": "ro1", "password": "ro123456", "role": UserRole.RO},
            {"username": "scorekeeper1", "password": "score123", "role": UserRole.SCOREKEEPER},
            {"username": "viewer1", "password": "view123", "role": UserRole.VIEWER},
            {"username": "coach1", "password": "coach123", "role": UserRole.COACH},
        ]
        
        for user_data in default_users:
            user = User(
                username=user_data["username"],
                hashed_password=self.get_password_hash(user_data["password"]),
                role=user_data["role"],
                created_at=datetime.now(timezone.utc)
            )
            self._users[user.username] = user
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password for storage."""
        return self.pwd_context.hash(password)
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self._users.get(username)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = self.get_user(username)
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        return user
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token for user."""
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expire = datetime.now(timezone.utc) + expires_delta
        
        to_encode = {
            "sub": user.username,
            "role": user.role.value,
            "exp": expire,
            "token_type": "access",
            "iat": datetime.now(timezone.utc)
        }
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token for user."""
        expires_delta = timedelta(days=self.refresh_token_expire_days)
        expire = datetime.now(timezone.utc) + expires_delta
        
        # Generate unique token ID
        token_id = secrets.token_urlsafe(32)
        
        to_encode = {
            "sub": user.username,
            "role": user.role.value,
            "exp": expire,
            "token_type": "refresh",
            "jti": token_id,  # JWT ID for token revocation
            "iat": datetime.now(timezone.utc)
        }
        
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        # Store refresh token data
        token_data = TokenData(
            username=user.username,
            role=user.role,
            exp=expire,
            token_type="refresh"
        )
        self._refresh_tokens[token_id] = token_data
        
        return token
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[TokenData]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            username: str = payload.get("sub")
            role_str: str = payload.get("role")
            exp_timestamp = payload.get("exp")
            token_type_in_payload = payload.get("token_type", "access")
            
            if username is None or token_type_in_payload != token_type:
                return None
            
            # Check expiration
            if exp_timestamp:
                exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                if datetime.now(timezone.utc) >= exp_datetime:
                    return None
            
            # Verify refresh token is still active
            if token_type == "refresh":
                token_id = payload.get("jti")
                if not token_id or token_id not in self._refresh_tokens:
                    return None
            
            try:
                role = UserRole(role_str) if role_str else None
            except ValueError:
                return None
            
            return TokenData(
                username=username,
                role=role,
                exp=datetime.fromtimestamp(exp_timestamp, tz=timezone.utc) if exp_timestamp else None,
                token_type=token_type
            )
            
        except JWTError:
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Create new access token from valid refresh token."""
        token_data = self.verify_token(refresh_token, token_type="refresh")
        if not token_data or not token_data.username:
            return None
        
        user = self.get_user(token_data.username)
        if not user or not user.is_active:
            return None
        
        return self.create_access_token(user)
    
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """Revoke a refresh token."""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            token_id = payload.get("jti")
            
            if token_id and token_id in self._refresh_tokens:
                del self._refresh_tokens[token_id]
                return True
                
        except JWTError:
            pass
        
        return False
    
    def login_user(self, username: str, password: str) -> TokenResponse:
        """Login user and return token response."""
        user = self.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        access_token = self.create_access_token(user)
        refresh_token = self.create_refresh_token(user)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60,
            user=user.to_info()
        )
    
    def logout_user(self, refresh_token: str) -> bool:
        """Logout user by revoking refresh token."""
        return self.revoke_refresh_token(refresh_token)
    
    def create_csrf_token(self, username: str) -> CSRFToken:
        """Create CSRF token for form protection."""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        csrf_token = CSRFToken(token=token, expires_at=expires_at)
        self._csrf_tokens[f"{username}:{token}"] = csrf_token
        
        return csrf_token
    
    def verify_csrf_token(self, username: str, token: str) -> bool:
        """Verify CSRF token."""
        csrf_key = f"{username}:{token}"
        csrf_token = self._csrf_tokens.get(csrf_key)
        
        if not csrf_token:
            return False
        
        if datetime.now(timezone.utc) >= csrf_token.expires_at:
            # Clean up expired token
            del self._csrf_tokens[csrf_key]
            return False
        
        return True
    
    def cleanup_expired_tokens(self):
        """Clean up expired refresh and CSRF tokens."""
        now = datetime.now(timezone.utc)
        
        # Clean up expired refresh tokens
        expired_refresh = [
            token_id for token_id, token_data in self._refresh_tokens.items()
            if token_data.exp and now >= token_data.exp
        ]
        for token_id in expired_refresh:
            del self._refresh_tokens[token_id]
        
        # Clean up expired CSRF tokens
        expired_csrf = [
            key for key, csrf_token in self._csrf_tokens.items()
            if now >= csrf_token.expires_at
        ]
        for key in expired_csrf:
            del self._csrf_tokens[key]