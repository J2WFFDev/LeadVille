"""
Authentication API endpoints for LeadVille Impact Bridge
JWT-based authentication with role-based access control
"""

import os
from datetime import datetime
from typing import Optional

from flask import Flask, request, jsonify, g
from flask_cors import CORS

from ..auth import AuthService, require_auth, require_role, Role
from ..database import get_database_session
from ..config import DatabaseConfig


def create_auth_routes(app: Flask) -> None:
    """Add authentication routes to Flask app"""
    
    # Enable CORS for auth endpoints
    CORS(app, resources={r"/api/auth/*": {"origins": "*"}})
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """User login endpoint"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "JSON data required"}), 400
            
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({"error": "Username and password required"}), 400
            
            # Get client info
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent')
            
            # Authenticate user
            db_config = DatabaseConfig()
            with get_database_session(db_config) as session:
                auth_service = AuthService(session)
                result = auth_service.authenticate_user(
                    username=username,
                    password=password,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            if result["success"]:
                return jsonify(result), 200
            else:
                return jsonify({"error": result["error"]}), 401
                
        except Exception as e:
            return jsonify({"error": f"Login failed: {str(e)}"}), 500
    
    @app.route('/api/auth/refresh', methods=['POST'])
    def refresh_token():
        """Refresh access token using refresh token"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "JSON data required"}), 400
            
            refresh_token = data.get('refresh_token')
            if not refresh_token:
                return jsonify({"error": "Refresh token required"}), 400
            
            db_config = DatabaseConfig()
            with get_database_session(db_config) as session:
                auth_service = AuthService(session)
                result = auth_service.refresh_token(refresh_token)
            
            if result["success"]:
                return jsonify(result), 200
            else:
                return jsonify({"error": result["error"]}), 401
                
        except Exception as e:
            return jsonify({"error": f"Token refresh failed: {str(e)}"}), 500
    
    @app.route('/api/auth/logout', methods=['POST'])
    @require_auth
    def logout():
        """User logout - revoke session"""
        try:
            # Get session JTI from token
            auth_header = request.headers.get('Authorization')
            token = auth_header.split(' ', 1)[1]
            
            from ..auth.utils import verify_token
            payload = verify_token(token)
            if not payload:
                return jsonify({"error": "Invalid token"}), 401
            
            session_jti = payload["session_jti"]
            
            db_config = DatabaseConfig()
            with get_database_session(db_config) as session:
                auth_service = AuthService(session)
                success = auth_service.revoke_session(session_jti)
            
            if success:
                return jsonify({"message": "Logged out successfully"}), 200
            else:
                return jsonify({"error": "Session not found"}), 404
                
        except Exception as e:
            return jsonify({"error": f"Logout failed: {str(e)}"}), 500
    
    @app.route('/api/auth/me', methods=['GET'])
    @require_auth
    def get_current_user():
        """Get current user information"""
        try:
            user = g.current_user
            return jsonify({
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role.value,
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                    "created_at": user.created_at.isoformat()
                }
            }), 200
            
        except Exception as e:
            return jsonify({"error": f"Failed to get user info: {str(e)}"}), 500
    
    @app.route('/api/auth/setup', methods=['POST'])
    def setup_default_users():
        """Setup default users on first boot (no auth required)"""
        try:
            db_config = DatabaseConfig()
            with get_database_session(db_config) as session:
                auth_service = AuthService(session)
                result = auth_service.setup_default_users()
            
            if result["success"]:
                return jsonify(result), 200
            else:
                return jsonify({"error": result["error"]}), 400
                
        except Exception as e:
            return jsonify({"error": f"Setup failed: {str(e)}"}), 500
    
    @app.route('/api/auth/users', methods=['GET'])
    @require_role(Role.ADMIN)
    def list_users():
        """List all users (admin only)"""
        try:
            from ..database.models import User
            
            db_config = DatabaseConfig()
            with get_database_session(db_config) as db:
                users = db.query(User).all()
                
                return jsonify({
                    "users": [
                        {
                            "id": user.id,
                            "username": user.username,
                            "full_name": user.full_name,
                            "role": user.role.value,
                            "is_active": user.is_active,
                            "is_default": user.is_default,
                            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                            "created_at": user.created_at.isoformat()
                        }
                        for user in users
                    ]
                }), 200
            
        except Exception as e:
            return jsonify({"error": f"Failed to list users: {str(e)}"}), 500
    
    @app.route('/api/auth/users', methods=['POST'])
    @require_role(Role.ADMIN)
    def create_user():
        """Create new user (admin only)"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "JSON data required"}), 400
            
            username = data.get('username')
            password = data.get('password')
            full_name = data.get('full_name')
            role = data.get('role', 'viewer')
            
            if not username or not password:
                return jsonify({"error": "Username and password required"}), 400
            
            try:
                role_enum = Role(role)
            except ValueError:
                return jsonify({"error": f"Invalid role: {role}"}), 400
            
            db_config = DatabaseConfig()
            with get_database_session(db_config) as session:
                auth_service = AuthService(session)
                result = auth_service.create_user(
                    username=username,
                    password=password,
                    full_name=full_name,
                    role=role_enum,
                    created_by_id=g.current_user.id
                )
            
            if result["success"]:
                return jsonify(result), 201
            else:
                return jsonify({"error": result["error"]}), 400
                
        except Exception as e:
            return jsonify({"error": f"User creation failed: {str(e)}"}), 500
    
    @app.route('/api/auth/health', methods=['GET'])
    def auth_health():
        """Authentication system health check"""
        try:
            from ..database.models import User
            
            db_config = DatabaseConfig()
            with get_database_session(db_config) as db:
                user_count = db.query(User).count()
                active_users = db.query(User).filter(User.is_active == True).count()
                
                return jsonify({
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "users": {
                        "total": user_count,
                        "active": active_users
                    },
                    "features": {
                        "jwt_auth": True,
                        "role_based_access": True,
                        "session_management": True,
                        "password_hashing": True
                    }
                }), 200
            
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 500