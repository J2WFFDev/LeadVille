"""Exception handling for the FastAPI application."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Union

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..logs import NdjsonLogger
from .models import ErrorResponse


class APIException(HTTPException):
    """Base API exception with enhanced error details."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code or "GENERAL_ERROR"
        self.extra_data = extra_data or {}


class ComponentUnavailableError(APIException):
    """Exception raised when a required component is unavailable."""
    
    def __init__(self, component: str, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail or f"Component {component} is currently unavailable",
            error_code="COMPONENT_UNAVAILABLE",
            extra_data={"component": component}
        )


class ConfigurationError(APIException):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, detail: str, config_key: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="CONFIGURATION_ERROR",
            extra_data={"config_key": config_key} if config_key else {}
        )


def create_error_response(
    error_code: str,
    message: str,
    detail: Optional[str] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """Create a standardized error response."""
    return ErrorResponse(
        error=error_code,
        message=message,
        detail=detail,
        request_id=request_id,
        timestamp=datetime.utcnow()
    )


def setup_exception_handlers(app: FastAPI, logger: NdjsonLogger) -> None:
    """Set up exception handlers for the FastAPI application."""
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle HTTP exceptions."""
        request_id = getattr(request.state, "request_id", None)
        
        # Log the error
        logger.error(
            f"HTTP {exc.status_code}: {exc.detail}",
            data={
                "request_id": request_id,
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method,
            }
        )
        
        error_response = create_error_response(
            error_code="HTTP_ERROR",
            message=exc.detail,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(mode='json')
        )
    
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
        """Handle custom API exceptions."""
        request_id = getattr(request.state, "request_id", None)
        
        # Log the error
        logger.error(
            f"API Error {exc.status_code}: {exc.detail}",
            data={
                "request_id": request_id,
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method,
                "extra_data": exc.extra_data,
            }
        )
        
        error_response = create_error_response(
            error_code=exc.error_code,
            message=exc.detail,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(mode="json")
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle request validation errors."""
        request_id = getattr(request.state, "request_id", None)
        
        # Format validation errors
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        # Log the validation error
        logger.error(
            f"Validation error: {len(errors)} field(s) invalid",
            data={
                "request_id": request_id,
                "validation_errors": errors,
                "path": request.url.path,
                "method": request.method,
            }
        )
        
        error_response = create_error_response(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            detail=f"Invalid fields: {', '.join([e['field'] for e in errors])}",
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump(mode="json")
        )
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        """Handle rate limit exceeded errors."""
        request_id = getattr(request.state, "request_id", None)
        
        # Log the rate limit violation
        logger.error(
            f"Rate limit exceeded: {exc.detail}",
            data={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown",
            }
        )
        
        error_response = create_error_response(
            error_code="RATE_LIMIT_EXCEEDED",
            message="Too many requests",
            detail=exc.detail,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=error_response.model_dump(mode="json"),
            headers={"Retry-After": "60"}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        request_id = getattr(request.state, "request_id", None)
        
        # Log the unexpected error
        logger.error(
            f"Unexpected error: {str(exc)}",
            data={
                "request_id": request_id,
                "exception_type": type(exc).__name__,
                "path": request.url.path,
                "method": request.method,
            }
        )
        
        error_response = create_error_response(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            detail="Please contact support if this problem persists" if not app.debug else str(exc),
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(mode="json")
        )