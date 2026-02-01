"""
Quick diagnostic script to test login components
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from PySide6.QtWidgets import QApplication
        print("✓ PySide6 imported")
    except ImportError as e:
        print(f"✗ PySide6 import failed: {e}")
        return False
    
    try:
        from src.database.connection import init_db, get_session
        print("✓ Database module imported")
    except ImportError as e:
        print(f"✗ Database import failed: {e}")
        return False
    
    try:
        from src.services.fyers_oauth_service import FyersOAuthService
        print("✓ OAuth service imported")
    except ImportError as e:
        print(f"✗ OAuth service import failed: {e}")
        return False
    
    try:
        from src.ui.windows.login_window import LoginWindow
        print("✓ Login window imported")
    except ImportError as e:
        print(f"✗ Login window import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database initialization"""
    print("\nTesting database...")
    
    try:
        from src.database.connection import init_db, get_session
        init_db()
        session = get_session()
        print("✓ Database initialized")
        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False

def test_oauth_server():
    """Test if OAuth callback server can start"""
    print("\nTesting OAuth callback server...")
    
    try:
        from src.services.fyers_oauth_service import FyersOAuthService
        
        # Try to start server with dummy credentials
        oauth = FyersOAuthService("TEST-KEY", "TEST-SECRET")
        if oauth.start_callback_server():
            print("✓ OAuth callback server can start on port 8765")
            oauth.stop_callback_server()
            return True
        else:
            print("✗ OAuth callback server failed to start")
            return False
    except Exception as e:
        print(f"✗ OAuth server test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Fyers Trading System - Login Diagnostic")
    print("=" * 60)
    
    all_ok = True
    
    all_ok = test_imports() and all_ok
    all_ok = test_database() and all_ok
    all_ok = test_oauth_server() and all_ok
    
    print("\n" + "=" * 60)
    if all_ok:
        print("✓ All tests passed - Login should work")
        print("\nTo run the app: python -m src.main")
    else:
        print("✗ Some tests failed - Please fix the issues above")
    print("=" * 60)

if __name__ == "__main__":
    main()
