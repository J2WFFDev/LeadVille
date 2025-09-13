"""Main FastAPI application for LeadVille Impact Bridge."""

import logging
import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

from ..logs import NdjsonLogger
from .config import api_config
from .exceptions import setup_exception_handlers
from .health import router as health_router
from .metrics import router as metrics_router
from .devices import router as devices_router
from .middleware import setup_middleware
from .models import APIInfo


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Create FastAPI instance
    app = FastAPI(
        title=api_config.api_title,
        description="Production BLE-based impact sensor system for shooting sports with real-time shot detection and impact correlation.",
        version="2.0.0",
        docs_url=f"/{api_config.api_version}/docs",
        redoc_url=f"/{api_config.api_version}/redoc",
        openapi_url=f"/{api_config.api_version}/openapi.json",
        debug=api_config.debug,
    )
    
    # Setup logging
    if api_config.debug:
        log_dir = Path("/tmp/logs")
        log_dir.mkdir(exist_ok=True)
    else:
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
    
    logger = NdjsonLogger(str(log_dir), "api")
    
    # Setup middleware (must be done before adding routes)
    setup_middleware(app, logger)
    
    # Setup exception handlers
    setup_exception_handlers(app, logger)
    
    # Add API routes
    app.include_router(health_router, prefix=f"/{api_config.api_version}", tags=["Health"])
    app.include_router(metrics_router, prefix=f"/{api_config.api_version}", tags=["Metrics"])
    app.include_router(devices_router, prefix=f"/{api_config.api_version}/admin/devices", tags=["Device Management"])
    
    # Root endpoint with API information
    @app.get("/", response_model=APIInfo)
    async def root() -> APIInfo:
        """Get API information."""
        return APIInfo(
            title=api_config.api_title,
            version="2.0.0",
            description="LeadVille Impact Bridge FastAPI Backend Foundation",
            contact={
                "name": "LeadVille Team",
                "email": "team@leadville.example.com"
            },
            license={
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        )
    
    # API version endpoint
    @app.get(f"/{api_config.api_version}")
    async def api_version():
        """Get API version information."""
        return {
            "api_version": api_config.api_version,
            "service": "LeadVille Impact Bridge API",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "operational"
        }
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Application startup event."""
        logger.status("FastAPI application starting up", data={
            "version": "2.0.0",
            "api_version": api_config.api_version,
            "debug_mode": api_config.debug,
            "host": api_config.host,
            "port": api_config.port
        })
        
        # Log configuration (non-sensitive parts only)
        logger.status("Configuration loaded", data={
            "cors_origins": api_config.cors_origins,
            "rate_limit": f"{api_config.rate_limit_requests}/{api_config.rate_limit_period}s",
            "log_level": api_config.log_level,
            "enable_request_logging": api_config.enable_request_logging
        })
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown event."""
        logger.status("FastAPI application shutting down")
    
    return app


def main():
    """Main entry point for running the API server."""
    
    # Configure Python logging to integrate with our structured logging
    logging.basicConfig(
        level=getattr(logging, api_config.log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create the application
    app = create_app()
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host=api_config.host,
        port=api_config.port,
        log_level=api_config.log_level.lower(),
        access_log=api_config.enable_request_logging,
        reload=api_config.debug,
    )


if __name__ == "__main__":
    main()