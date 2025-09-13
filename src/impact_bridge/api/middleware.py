"""FastAPI middleware for security, logging, and monitoring."""

import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from ..logs import NdjsonLogger
from .config import api_config


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    def __init__(self, app: FastAPI, logger: NdjsonLogger):
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        self.logger.log(
            "request_start",
            f"{request.method} {request.url.path}",
            data={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": get_remote_address(request),
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log successful response
            duration = time.time() - start_time
            self.logger.log(
                "request_complete",
                f"{request.method} {request.url.path} -> {response.status_code}",
                data={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as exc:
            # Log error response
            duration = time.time() - start_time
            self.logger.error(
                f"Request failed: {request.method} {request.url.path}",
                data={
                    "request_id": request_id,
                    "error": str(exc),
                    "duration_ms": round(duration * 1000, 2),
                }
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        
        return response


def setup_middleware(app: FastAPI, logger: NdjsonLogger) -> None:
    """Configure all middleware for the FastAPI application."""
    
    # Rate limiting
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_config.cors_origins,
        allow_credentials=api_config.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Request logging (add last so it captures everything)
    if api_config.enable_request_logging:
        app.add_middleware(RequestLoggingMiddleware, logger=logger)