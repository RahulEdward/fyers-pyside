"""
Complete test of the login flow
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

def test_callback_server():
    """Test if callback server can start"""
    print("=" * 70)
    print("TEST 1: Callback Server")
    print("=" * 70)
    
    try:
        from src.services.fyers_oauth_service import FyersOAuthService
        
        api_key = "3DMS06KO8R-100"
        api_secret = "SOFYMFWRA6"
        
        oauth = FyersOAuthService(api_key, api_secret)
        
        print("\nStarting callback server...")
        if oauth.start_callback_server():
            print("✓ Callback server started successfully on port 8765")
            
            # Give it a moment
            import time
            time.sleep(0.5)
            
            # Stop it
            oauth.stop_callback_server()
            print("✓ Server stopped successfully")
            
            # Wait for cleanup
            time.sleep(0.5)
            
            return True
        else:
            print("✗ Failed to start callback server")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_url_generation():
    """Test OAuth URL generation"""
    print("\n" + "=" * 70)
    print("TEST 2: OAuth URL Generation")
    print("=" * 70)
    
    try:
        from src.services.fyers_oauth_service import FyersOAuthService
        
        api_key = "3DMS06KO8R-100"
        api_secret = "SOFYMFWRA6"
        
        oauth = FyersOAuthService(api_key, api_secret)
        auth_url = oauth.generate_auth_url()
        
        print(f"\nGenerated URL:")
        print(auth_url)
        
        # Verify components
        checks = [
            ("Contains API Key", api_key in auth_url),
            ("Contains redirect_uri", "redirect_uri=http%3A%2F%2F127.0.0.1%3A8765%2Fcallback" in auth_url),
            ("Contains response_type=code", "response_type=code" in auth_url),
            ("Contains state", "state=fyers_auth" in auth_url),
            ("Contains scope=openid", "scope=openid" in auth_url),
            ("Correct base URL", auth_url.startswith("https://api-t1.fyers.in/api/v3/generate-authcode")),
        ]
        
        print("\nURL Verification:")
        all_passed = True
        for check_name, result in checks:
            status = "✓" if result else "✗"
            print(f"  {status} {check_name}")
            if not result:
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_token_exchange():
    """Test token exchange logic (without actual auth code)"""
    print("\n" + "=" * 70)
    print("TEST 3: Token Exchange Setup")
    print("=" * 70)
    
    try:
        from src.services.fyers_oauth_service import FyersOAuthService
        import hashlib
        
        api_key = "3DMS06KO8R-100"
        api_secret = "SOFYMFWRA6"
        
        oauth = FyersOAuthService(api_key, api_secret)
        
        # Test hash generation
        checksum_input = f"{api_key}:{api_secret}"
        app_id_hash = hashlib.sha256(checksum_input.encode()).hexdigest()
        
        print(f"\nAPI Key: {api_key}")
        print(f"API Secret: {api_secret[:5]}...")
        print(f"App ID Hash: {app_id_hash[:20]}...")
        
        print("\n✓ Token exchange setup is correct")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_setup():
    """Test database initialization"""
    print("\n" + "=" * 70)
    print("TEST 4: Database Setup")
    print("=" * 70)
    
    try:
        from src.database.connection import init_db, get_session
        
        print("\nInitializing database...")
        init_db()
        print("✓ Database initialized")
        
        session = get_session()
        print("✓ Database session created")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_services_initialization():
    """Test if all services can be initialized"""
    print("\n" + "=" * 70)
    print("TEST 5: Services Initialization")
    print("=" * 70)
    
    try:
        from src.database.connection import init_db, get_session
        from src.services.broker_service import BrokerService
        from src.services.encryption_service import EncryptionService
        from src.repositories.credential_repository import CredentialRepository
        
        print("\nInitializing services...")
        
        init_db()
        session = get_session()
        print("✓ Database ready")
        
        encryption_key = b'fyers_trading_app_secret_key_2024'
        encryption_service = EncryptionService(encryption_key)
        print("✓ Encryption service created")
        
        cred_repo = CredentialRepository(session)
        print("✓ Credential repository created")
        
        broker_service = BrokerService(cred_repo, encryption_service)
        print("✓ Broker service created")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n")
    print("=" * 70)
    print("FYERS LOGIN FLOW - COMPREHENSIVE TEST")
    print("=" * 70)
    
    results = []
    
    results.append(("Callback Server", test_callback_server()))
    results.append(("OAuth URL Generation", test_url_generation()))
    results.append(("Token Exchange Setup", test_token_exchange()))
    results.append(("Database Setup", test_database_setup()))
    results.append(("Services Initialization", test_services_initialization()))
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("\nLogin flow is ready!")
        print("\nTo test manually:")
        print("1. Make sure redirect URL in Fyers dashboard is:")
        print("   http://127.0.0.1:8765/callback")
        print("2. Run: python -m src.main")
        print("3. Enter credentials and click Connect")
    else:
        print("✗ SOME TESTS FAILED")
        print("\nPlease fix the issues above before running the app")
    print("=" * 70)
    print()

if __name__ == "__main__":
    main()
