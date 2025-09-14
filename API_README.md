# LeadVille Impact Bridge - FastAPI Backend

## Overview

The LeadVille Impact Bridge FastAPI backend provides a production-ready REST API foundation for the BLE-based impact sensor system. This API serves as the central hub for managing device connections, processing sensor data, and providing real-time monitoring capabilities.

## Features

### ✅ Implemented (Foundation)

- **🚀 FastAPI Application** - Modern async web framework with automatic API documentation
- **❤️ Health Check Endpoints** - Basic and detailed component health monitoring
- **📊 System Metrics** - Real-time performance and resource utilization
- **🔒 Security Middleware** - CORS, rate limiting, security headers, request validation
- **🔐 JWT Authentication** - Complete authentication system with refresh tokens and RBAC
- **👥 Role-Based Access Control** - 5 user roles (admin, ro, scorekeeper, viewer, coach)
- **🛡️ CSRF Protection** - Token-based protection for unsafe HTTP methods
- **📝 Structured Logging** - NDJSON format with request tracking and systemd integration
- **⚡ Error Handling** - Comprehensive exception management with standardized responses
- **📚 API Documentation** - Automatic OpenAPI/Swagger documentation generation
- **🔧 Configuration Management** - Environment-based settings with validation

### 🚧 Ready for Integration

- **🗄️ SQLAlchemy Database** - Configured for connection but pending schema implementation
- **📡 MQTT Message Bus** - Configuration ready for broker integration
- **📱 BLE Services** - Health checks prepared for device service integration

## Quick Start

### 1. Install Dependencies

```bash
# Install the package with API dependencies
pip install -e .

# Or install specific dependencies
pip install fastapi uvicorn pydantic-settings slowapi psutil
```

### 2. Start the API Server

```bash
# Using the convenience script
python start_api.py

# Or directly
python -m src.impact_bridge.api.main

# With custom configuration
python start_api.py --host 127.0.0.1 --port 8080 --debug
```

### 3. Access the API

- **API Root**: http://localhost:8000/
- **Interactive Documentation**: http://localhost:8000/v1/docs  
- **Health Check**: http://localhost:8000/v1/health
- **Detailed Health**: http://localhost:8000/v1/health/detailed
- **System Metrics**: http://localhost:8000/v1/metrics
- **OpenAPI Schema**: http://localhost:8000/v1/openapi.json

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API information and version |
| `GET` | `/v1` | API version details |

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/v1/auth/login` | User login with credentials | ❌ |
| `POST` | `/v1/auth/refresh` | Refresh access token | ❌ |
| `POST` | `/v1/auth/logout` | User logout | ✅ |
| `GET` | `/v1/auth/me` | Get current user info | ✅ |
| `GET` | `/v1/auth/csrf-token` | Get CSRF protection token | ✅ |
| `POST` | `/v1/auth/verify` | Verify token validity | ✅ |
| `GET` | `/v1/auth/roles` | List available user roles | ❌ |

### Health & Monitoring

| Method | Endpoint | Description | Response | Auth Required |
|--------|----------|-------------|----------|---------------|
| `GET` | `/v1/health` | Basic health status | `HealthStatus` | ❌ |
| `GET` | `/v1/health/detailed` | Component health details | `DetailedHealthStatus` | ❌ |
| `GET` | `/v1/metrics` | System performance metrics | `MetricsResponse` | ❌ |

### Device Management (Admin)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/v1/admin/devices/list` | List all devices | Any authenticated |
| `GET` | `/v1/admin/devices/health` | All device health status | Any authenticated |
| `POST` | `/v1/admin/devices/discover` | Start BLE device discovery | Admin only |
| `POST` | `/v1/admin/devices/pair` | Pair with BLE device | Admin only |
| `POST` | `/v1/admin/devices/assign` | Assign device to target | Admin only |
| `DELETE` | `/v1/admin/devices/{address}` | Remove device | Admin only |

### Example Health Response

```json
{
  "status": "healthy",
  "timestamp": "2025-09-13T18:27:00.298708",
  "version": "v1", 
  "uptime_seconds": 20.45
}
```

### Example Detailed Health Response

```json
{
  "status": "healthy",
  "timestamp": "2025-09-13T18:27:05.492889",
  "version": "v1",
  "uptime_seconds": 25.64,
  "components": [
    {
      "name": "database",
      "status": "healthy", 
      "message": "Database connection successful",
      "last_check": "2025-09-13T18:27:05.492819",
      "response_time_ms": 1.23,
      "metadata": {
        "type": "sqlite",
        "url": "sqlite:///./db/bridge.db"
      }
    }
  ]
}
```

## Configuration

### Environment Variables

Copy `config/api_config.env.example` to `.env` and customize:

```bash
# Server settings
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# Security settings
RATE_LIMIT_REQUESTS=100
CORS_ORIGINS=["*"]

# Integration settings
DATABASE_URL=sqlite:///./db/bridge.db
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883

# Logging settings
LOG_LEVEL=INFO
ENABLE_REQUEST_LOGGING=true
```

### Configuration Classes

The API uses Pydantic settings for type-safe configuration:

- `APIConfig` - Main application settings
- Environment variable integration
- Validation and type checking
- Default value management

## Security Features

### Implemented Security

- **🔒 CORS Protection** - Configurable origin restrictions
- **⚡ Rate Limiting** - Per-client request throttling  
- **🛡️ Security Headers** - XSS, content type, frame protection
- **🔐 JWT Authentication** - Access tokens + refresh tokens with role-based access
- **🔑 Password Security** - bcrypt hashing with salt rounds
- **🛡️ CSRF Protection** - Token-based protection for unsafe HTTP methods
- **🔍 Request Validation** - Automatic Pydantic model validation
- **📝 Request Tracking** - Unique request IDs for audit trails

### Security Headers Added

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY  
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; ...
```

## Logging & Monitoring

### Structured Logging

- **📄 NDJSON Format** - Machine-readable log output
- **🔗 Request Correlation** - Unique request ID tracking
- **⏱️ Performance Metrics** - Response time measurement  
- **🎯 Component Tracing** - Detailed service interaction logs

### Log Categories

- `request_start` - HTTP request initiation
- `request_complete` - Successful request completion
- `error` - Error conditions and exceptions
- `status` - Application lifecycle events

### Example Log Entry

```json
{
  "seq": 15,
  "type": "request_complete", 
  "ts_ms": 1234.567,
  "msg": "GET /v1/health -> 200",
  "hms": "18:27:05.493",
  "data": {
    "request_id": "d3ea03c2-c889-44c6-b4ae-7495a366d580",
    "status_code": 200,
    "duration_ms": 12.34
  }
}
```

## Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run API tests
pytest tests/api/ -v

# Run specific test
pytest tests/api/test_main.py::test_health_check_basic -v
```

### Test Coverage

- ✅ Health check endpoints
- ✅ Metrics collection
- ✅ Security middleware
- ✅ Error handling
- ✅ API documentation
- ✅ Request validation

## Integration with LeadVille Bridge

### Current Integration Points

1. **Logging Infrastructure** - Reuses existing `NdjsonLogger` from `impact_bridge.logs`
2. **Configuration System** - Extends existing config management patterns  
3. **Component Architecture** - Follows established modular design
4. **Health Monitoring** - Prepared for BLE device, database, and MQTT integration

### Future Integration (Planned)

- **BLE Device Management** - AMG timer and BT50 sensor control endpoints
- **Shot Detection API** - Real-time impact detection event streaming
- **Database Integration** - SQLAlchemy models for data persistence
- **MQTT Message Bus** - Event publishing and subscription management
- **WebSocket Support** - Real-time data streaming for web clients

## Development

### Adding New Endpoints

1. Create router in `src/impact_bridge/api/`
2. Define Pydantic models in `models.py`
3. Add router to `main.py`
4. Create tests in `tests/api/`

### Example Router

```python
from fastapi import APIRouter, Depends
from .models import CustomResponse
from .config import api_config

router = APIRouter()

@router.get("/custom", response_model=CustomResponse)
async def custom_endpoint() -> CustomResponse:
    return CustomResponse(message="Hello World")
```

### Code Quality

- **Type Hints** - Full type annotation coverage
- **Async/Await** - Proper asynchronous programming patterns
- **Error Handling** - Comprehensive exception management
- **Documentation** - Inline docstrings and API docs
- **Testing** - Unit and integration test coverage

## Deployment

### Development

```bash
# Start with auto-reload
python start_api.py --debug

# Custom configuration
API_DEBUG=true LOG_LEVEL=DEBUG python -m src.impact_bridge.api.main
```

### Production

```bash
# Production server
uvicorn src.impact_bridge.api.main:create_app --host 0.0.0.0 --port 8000

# With gunicorn (recommended)
gunicorn src.impact_bridge.api.main:create_app -w 4 -k uvicorn.workers.UvicornWorker
```

### Systemd Service

Ready for integration with existing Pi deployment via `setup_pi.sh`.

## Performance

### Metrics Available

- **Memory Usage** - Current RAM consumption
- **CPU Usage** - Processor utilization percentage  
- **Request Count** - Total processed requests
- **Active Connections** - Current WebSocket/HTTP connections
- **Uptime** - Application runtime duration

### Monitoring Integration

- **Prometheus Ready** - Metrics endpoint compatible
- **Health Check Standards** - Industry-standard health endpoints
- **Structured Logging** - Compatible with log aggregation systems

## Support

### Troubleshooting

1. **Port Already in Use**: Change port with `--port 8080`
2. **Import Errors**: Ensure `pip install -e .` was run
3. **Permission Denied**: Check file permissions on log directories
4. **Database Errors**: Verify database directory exists and is writable

### Contributing

Follow existing LeadVille development patterns:

- Maintain minimal, surgical changes
- Preserve existing functionality  
- Add comprehensive tests
- Update documentation
- Follow async/await patterns

---

**Next Steps**: This foundation is ready for integration with database schemas, MQTT message bus, and BLE device management as outlined in the project roadmap.