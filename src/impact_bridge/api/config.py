"""FastAPI configuration management for LeadVille Impact Bridge."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class APIConfig(BaseSettings):
    """FastAPI application configuration."""

    # Server settings
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="API_DEBUG")
    
    # CORS settings
    cors_origins: list[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    # Security settings
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, env="RATE_LIMIT_PERIOD")
    
    # JWT Authentication settings
    jwt_secret_key: str = Field(default="dev-secret-key-change-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Database settings
    database_url: str = Field(default="sqlite:///./db/bridge.db", env="DATABASE_URL")
    
    # MQTT settings
    mqtt_broker_host: str = Field(default="localhost", env="MQTT_BROKER_HOST")
    mqtt_broker_port: int = Field(default=1883, env="MQTT_BROKER_PORT")
    mqtt_topic_prefix: str = Field(default="leadville", env="MQTT_TOPIC_PREFIX")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    enable_request_logging: bool = Field(default=True, env="ENABLE_REQUEST_LOGGING")
    
    # API versioning
    api_version: str = Field(default="v1", env="API_VERSION")
    api_title: str = Field(default="LeadVille Impact Bridge API", env="API_TITLE")
    
    # Health check settings
    health_check_timeout: float = Field(default=5.0, env="HEALTH_CHECK_TIMEOUT")

    class Config:
        """Pydantic configuration."""
        env_file = ".env"


def get_api_config() -> APIConfig:
    """Get API configuration instance."""
    return APIConfig()


# Global config instance
api_config = get_api_config()