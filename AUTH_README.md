# LeadVille Impact Bridge - Authentication System

## Overview

The LeadVille Impact Bridge API implements a comprehensive JWT-based authentication system with refresh tokens and role-based access control (RBAC). This system provides secure access to the BLE device management and impact sensor functionality.

## Features

### ✅ Implemented Authentication Features

- **🔐 JWT Authentication** - Access tokens (30 min) + Refresh tokens (7 days)
- **🔑 Password Security** - bcrypt hashing with salt rounds
- **👥 Role-Based Access Control** - 5 distinct user roles with granular permissions
- **🛡️ CSRF Protection** - Token-based protection for unsafe HTTP methods  
- **🔒 Secure Session Management** - Token rotation and revocation support
- **📱 Token Refresh** - Seamless access token renewal without re-login
- **🚪 Login/Logout Flows** - Complete session lifecycle management

## User Roles

The system supports five distinct user roles with different permission levels:

| Role | Description | Permissions |
|------|-------------|-------------|
| `admin` | System Administrator | Full access to all endpoints |
| `ro` | Range Officer | Competition and match management |
| `scorekeeper` | Score Keeper | Score recording and match data |  
| `viewer` | Viewer | Read-only access to results |
| `coach` | Coach | Access to specific shooters' data |

## API Endpoints

### Authentication Endpoints

All authentication endpoints are under the `/v1/auth` prefix:

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/v1/auth/login` | User login | ❌ |
| `POST` | `/v1/auth/refresh` | Refresh access token | ❌ |
| `POST` | `/v1/auth/logout` | User logout | ✅ |
| `GET` | `/v1/auth/me` | Get current user info | ✅ |
| `GET` | `/v1/auth/csrf-token` | Get CSRF token | ✅ |
| `POST` | `/v1/auth/verify` | Verify token validity | ✅ |
| `GET` | `/v1/auth/roles` | List available roles | ❌ |

### Protected Endpoints

Device management endpoints require authentication and appropriate role permissions:

| Endpoint Pattern | Required Role | Description |
|------------------|---------------|-------------|
| `GET /v1/admin/devices/list` | Any authenticated | View device list |
| `GET /v1/admin/devices/health*` | Any authenticated | View device health |
| `POST /v1/admin/devices/discover` | `admin` | Start device discovery |
| `POST /v1/admin/devices/pair` | `admin` | Pair with device |
| `POST /v1/admin/devices/assign` | `admin` | Assign device to target |
| `POST /v1/admin/devices/unassign` | `admin` | Unassign device |
| `POST /v1/admin/devices/monitoring` | `admin` | Control health monitoring |
| `DELETE /v1/admin/devices/{address}` | `admin` | Remove device |

## Usage Examples

### 1. User Login

```bash
curl -X POST "http://localhost:8000/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "admin",
       "password": "admin123"
     }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "username": "admin",
    "role": "admin",
    "is_active": true,
    "created_at": "2025-09-13T23:18:20.442409Z",
    "last_login": "2025-09-13T23:18:21.616447Z"
  }
}
```

### 2. Accessing Protected Endpoints

```bash
curl -X GET "http://localhost:8000/v1/admin/devices/list" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Refreshing Access Token

```bash
curl -X POST "http://localhost:8000/v1/auth/refresh" \
     -H "Content-Type: application/json" \
     -d '{
       "refresh_token": "YOUR_REFRESH_TOKEN"
     }'
```

### 4. Getting CSRF Token

```bash
curl -X GET "http://localhost:8000/v1/auth/csrf-token" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "token": "2ajI39YcQvN3c4pYW9oHmS2OUUmn...",
  "expires_at": "2025-09-14T00:18:50.460716Z"
}
```

### 5. Using CSRF Token for Unsafe Methods

For POST, PUT, DELETE, PATCH requests, include the CSRF token:

```bash
curl -X POST "http://localhost:8000/v1/admin/devices/discover" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "X-CSRF-Token: YOUR_CSRF_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"duration": 10}'
```

## Default Users

The system includes default users for testing and initial setup:

| Username | Password | Role | Description |
|----------|----------|------|-------------|
| `admin` | `admin123` | `admin` | System administrator |
| `ro1` | `ro123456` | `ro` | Range officer example |
| `scorekeeper1` | `score123` | `scorekeeper` | Scorekeeper example |
| `viewer1` | `view123` | `viewer` | Viewer example |
| `coach1` | `coach123` | `coach` | Coach example |

**⚠️ Security Warning:** Change default passwords in production environments!

## Configuration

### Environment Variables

Configure authentication via environment variables:

```bash
# JWT Configuration
export JWT_SECRET_KEY="your-super-secret-key-here"
export JWT_ALGORITHM="HS256"
export JWT_ACCESS_TOKEN_EXPIRE_MINUTES="30"
export JWT_REFRESH_TOKEN_EXPIRE_DAYS="7"

# API Configuration  
export API_HOST="0.0.0.0"
export API_PORT="8000"
export API_DEBUG="false"
```

### Security Best Practices

1. **Secret Key**: Use a cryptographically secure secret key in production
2. **HTTPS**: Always use HTTPS in production environments
3. **Token Expiration**: Keep access token expiration short (15-30 minutes)
4. **Password Policy**: Enforce strong passwords for user accounts
5. **Rate Limiting**: Monitor and limit authentication attempts
6. **Audit Logging**: Log authentication events for security monitoring

## Error Responses

The authentication system returns consistent error responses:

```json
{
  "error": "HTTP_ERROR",
  "message": "Incorrect username or password",
  "detail": null,
  "request_id": "3c47777b-56b9-4d19-8ace-78352b461e19", 
  "timestamp": "2025-09-13T23:18:27.328854"
}
```

### Common HTTP Status Codes

- `200 OK` - Successful authentication/authorization
- `401 Unauthorized` - Invalid credentials or expired token
- `403 Forbidden` - Insufficient permissions for role
- `422 Unprocessable Entity` - Invalid request format
- `500 Internal Server Error` - Server-side authentication error

## Integration with Client Applications

### Web Applications

For browser-based applications:

1. Store access token in memory (not localStorage for security)
2. Store refresh token in httpOnly cookie
3. Implement automatic token refresh before expiration
4. Include CSRF tokens for state-changing operations
5. Handle 401/403 responses by redirecting to login

### Mobile Applications

For mobile applications:

1. Store tokens in secure keychain/keystore
2. Implement background token refresh
3. Use certificate pinning for API calls
4. Handle network interruptions gracefully

### API Clients

For server-to-server integration:

1. Use service account credentials
2. Implement proper token caching and refresh
3. Handle rate limiting and backoff
4. Monitor authentication failures

## Testing

The authentication system includes comprehensive test coverage:

- ✅ 12 authentication endpoint tests
- ✅ 12 role-based access control tests  
- ✅ Token validation and refresh testing
- ✅ CSRF protection validation
- ✅ Error handling verification

Run tests with:

```bash
# Authentication tests
pytest tests/api/test_auth.py -v

# Role-based access tests  
pytest tests/api/test_device_auth.py -v

# All API tests
pytest tests/api/ -v
```

## Troubleshooting

### Common Issues

**1. "Not authenticated" errors**
- Verify JWT token is included in Authorization header
- Check token format: `Bearer YOUR_TOKEN`  
- Ensure token hasn't expired

**2. "Insufficient permissions" errors**
- Verify user has required role for endpoint
- Check role assignments in user management
- Confirm endpoint role requirements

**3. "Invalid or expired refresh token"**
- Refresh token may have expired (7 day default)
- Token may have been revoked via logout
- Re-authenticate with login endpoint

**4. CSRF token errors**
- Include X-CSRF-Token header for unsafe methods
- Ensure CSRF token hasn't expired (1 hour default)
- Generate new CSRF token if needed

### Debug Mode

Enable debug logging for authentication issues:

```bash
export LOG_LEVEL="DEBUG"
export API_DEBUG="true"
```

## Migration and Deployment

### Production Deployment Checklist

- [ ] Change all default passwords
- [ ] Generate secure JWT secret key
- [ ] Enable HTTPS/TLS encryption
- [ ] Configure proper CORS origins
- [ ] Set up monitoring and alerting
- [ ] Implement backup authentication method
- [ ] Review and test all security headers
- [ ] Validate rate limiting configuration

### Database Integration

The authentication system is designed to integrate with persistent storage:

- User data is currently in-memory (for development)
- Production deployments should use database storage
- Support for SQLAlchemy integration is prepared
- Refresh token storage should be database-backed

---

**Next Steps**: This authentication foundation provides secure access control for all LeadVille Impact Bridge functionality and is ready for production deployment with proper configuration.