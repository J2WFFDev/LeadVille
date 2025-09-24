#!/usr/bin/env python3
"""
Authentication System Test
Tests JWT authentication, user management, and role-based access control
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.impact_bridge.auth import AuthService, Role
from src.impact_bridge.database import init_database, get_database_session
from src.impact_bridge.config import DatabaseConfig


def test_authentication_system():
    """Test the complete authentication system"""
    print("🔐 Testing LeadVille Authentication System")
    print("=" * 50)
    
    # Initialize database
    db_config = DatabaseConfig(dir="./db", file="bridge.db")
    db_session = init_database(db_config)
    
    auth_service = AuthService(db_session.get_session())
    
    print("1. 🏗️  Setting up default users...")
    result = auth_service.setup_default_users()
    
    admin_password = None
    if result["success"]:
        print("   ✅ Default users created successfully")
        for account in result["accounts"]:
            print(f"   📝 {account['username']} ({account['role']}) - Password: {account['password']}")
            if account['username'] == 'admin':
                admin_password = account['password']
    else:
        print(f"   ⚠️  {result['error']}")
        # If users already exist, use default admin password
        admin_password = "admin123"  # Would need to be set in real deployment
    
    print("\n2. 🔑 Testing admin login...")
    login_result = auth_service.authenticate_user(
        username="admin",
        password=admin_password,
        ip_address="127.0.0.1",
        user_agent="Test Client"
    )
    
    if login_result["success"]:
        print("   ✅ Admin login successful")
        print(f"   🎫 Access token generated: {login_result['access_token'][:50]}...")
        print(f"   👤 User: {login_result['user']['username']} ({login_result['user']['role']})")
        access_token = login_result["access_token"]
    else:
        print(f"   ❌ Login failed: {login_result['error']}")
        return
    
    print("\n3. 🔍 Testing token verification...")
    from src.impact_bridge.auth.utils import verify_token
    payload = verify_token(access_token)
    
    if payload:
        print("   ✅ Token verification successful")
        print(f"   📋 User ID: {payload['user_id']}, Role: {payload['role']}")
    else:
        print("   ❌ Token verification failed")
    
    print("\n4. 👥 Testing user creation...")
    create_result = auth_service.create_user(
        username="test_ro",
        password="ro123",
        full_name="Test Range Officer",
        role=Role.RO,
        created_by_id=payload['user_id'] if payload else None
    )
    
    if create_result["success"]:
        print("   ✅ Range Officer user created successfully")
        print(f"   👤 Username: {create_result['user']['username']}")
        print(f"   🎭 Role: {create_result['user']['role']}")
    else:
        print(f"   ❌ User creation failed: {create_result['error']}")
    
    print("\n5. 🔒 Testing role-based permissions...")
    
    # Test admin user permissions
    admin_user = auth_service.get_user_from_token(access_token)
    if admin_user:
        print(f"   👑 Admin has admin permissions: {admin_user.has_permission(Role.ADMIN)}")
        print(f"   🎯 Admin has RO permissions: {admin_user.has_permission(Role.RO)}")
        print(f"   👀 Admin has viewer permissions: {admin_user.has_permission(Role.VIEWER)}")
    
    # Test RO user login and permissions
    ro_login = auth_service.authenticate_user("test_ro", "ro123")
    if ro_login["success"]:
        ro_user = auth_service.get_user_from_token(ro_login["access_token"])
        print(f"   🎯 RO has admin permissions: {ro_user.has_permission(Role.ADMIN)}")
        print(f"   🎯 RO has RO permissions: {ro_user.has_permission(Role.RO)}")
        print(f"   👀 RO has viewer permissions: {ro_user.has_permission(Role.VIEWER)}")
    
    print("\n6. 🚪 Testing session revocation...")
    session_jti = payload["session_jti"] if payload else None
    if session_jti:
        revoke_success = auth_service.revoke_session(session_jti)
        print(f"   {'✅' if revoke_success else '❌'} Session revocation: {revoke_success}")
        
        # Try to use revoked token
        revoked_user = auth_service.get_user_from_token(access_token)
        print(f"   {'✅' if not revoked_user else '❌'} Revoked token rejected: {revoked_user is None}")
    
    print("\n7. 📊 Testing database stats...")
    db = db_session.get_session()
    from src.impact_bridge.database.models import User, UserSession
    
    user_count = db.query(User).count()
    session_count = db.query(UserSession).count()
    active_sessions = db.query(UserSession).filter(UserSession.revoked_at == None).count()
    
    print(f"   👥 Total users: {user_count}")
    print(f"   🎫 Total sessions: {session_count}")
    print(f"   ✅ Active sessions: {active_sessions}")
    
    print("\n🎉 Authentication system test completed!")
    
    # Show available roles
    print("\n📋 Available roles:")
    for role in Role:
        print(f"   🎭 {role.value}: {role.name}")
    
    return True


if __name__ == "__main__":
    try:
        test_authentication_system()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)