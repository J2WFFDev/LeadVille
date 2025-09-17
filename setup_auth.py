#!/usr/bin/env python3
"""
Simple Authentication Setup
Creates default admin user with known password for testing
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.impact_bridge.database import init_database, get_database_session
from src.impact_bridge.database.models import User, Role, UserSession
from src.impact_bridge.config import DatabaseConfig


def setup_auth():
    """Setup authentication with known password"""
    print("🔐 LeadVille Authentication Setup")
    print("=" * 40)
    
    # Initialize database
    db_config = DatabaseConfig(dir="./db", file="bridge.db")
    db_session = init_database(db_config)
    db = db_session.get_session()
    
    print("📊 Current users in database:")
    users = db.query(User).all()
    for user in users:
        print(f"   👤 {user.username} ({user.role.value}) - Active: {user.is_active}")
    
    # Check if admin exists
    admin = db.query(User).filter(User.username == "admin").first()
    
    if admin:
        print(f"\n✅ Admin user exists: {admin.username}")
        print("🔑 Setting known password for testing...")
        admin.set_password("admin123")
        db.commit()
        print("   ✅ Password set to: admin123")
    else:
        print("\n🏗️  Creating admin user...")
        admin = User(
            username="admin",
            full_name="Administrator",
            role=Role.ADMIN,
            is_default=True
        )
        admin.set_password("admin123")
        db.add(admin)
        db.commit()
        print("   ✅ Admin user created with password: admin123")
    
    # Test login
    print("\n🔑 Testing login...")
    from src.impact_bridge.auth import AuthService
    auth_service = AuthService(db)
    
    result = auth_service.authenticate_user(
        username="admin",
        password="admin123",
        ip_address="127.0.0.1"
    )
    
    if result["success"]:
        print("   ✅ Login successful!")
        print(f"   🎫 Token: {result['access_token'][:50]}...")
        print(f"   👤 User: {result['user']['full_name']} ({result['user']['role']})")
        
        # Test token verification
        user = auth_service.get_user_from_token(result["access_token"])
        if user:
            print(f"   ✅ Token verification successful: {user.username}")
        else:
            print("   ❌ Token verification failed")
            
    else:
        print(f"   ❌ Login failed: {result['error']}")
    
    # Show sessions
    sessions = db.query(UserSession).all()
    print(f"\n📊 Active sessions: {len(sessions)}")
    for session in sessions:
        status = "active" if session.is_active() else "expired/revoked"
        print(f"   🎫 {session.user.username}: {status}")
    
    print("\n🎉 Authentication setup completed!")
    print("📝 Use admin/admin123 for testing")


if __name__ == "__main__":
    try:
        setup_auth()
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)