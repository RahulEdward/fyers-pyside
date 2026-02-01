"""
Test real OAuth flow with actual credentials
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

def test_oauth_flow():
    """Test the complete OAuth flow"""
    print("=" * 70)
    print("TESTING FYERS OAUTH FLOW")
    print("=" * 70)
    
    # Your credentials
    api_key = "3DMS06KO8R-100"
    api_secret = "SOFYMFWRA6"
    
    print(f"\nAPI Key: {api_key}")
    print(f"API Secret: {api_secret[:5]}...")
    
    try:
        from src.services.fyers_oauth_service import FyersOAuthService
        
        print("\n" + "-" * 70)
        print("Step 1: Creating OAuth Service")
        print("-" * 70)
        
        oauth = FyersOAuthService(api_key, api_secret)
        print("✓ OAuth service created")
        
        print("\n" + "-" * 70)
        print("Step 2: Generating Auth URL")
        print("-" * 70)
        
        auth_url = oauth.generate_auth_url()
        print(f"\nGenerated URL:")
        print(auth_url)
        
        # Verify URL components
        print("\nURL Verification:")
        checks = [
            ("Contains API Key", api_key in auth_url),
            ("Contains redirect_uri", "redirect_uri=" in auth_url),
            ("Contains response_type=code", "response_type=code" in auth_url),
            ("Contains state", "state=" in auth_url),
            ("Contains scope=openid", "scope=openid" in auth_url),
        ]
        
        for check_name, result in checks:
            status = "✓" if result else "✗"
            print(f"  {status} {check_name}")
        
        all_passed = all(result for _, result in checks)
        
        if not all_passed:
            print("\n✗ URL verification failed!")
            return False
        
        print("\n" + "-" * 70)
        print("Step 3: Starting Callback Server")
        print("-" * 70)
        
        if oauth.start_callback_server():
            print("✓ Callback server started on port 8765")
        else:
            print("✗ Failed to start callback server")
            return False
        
        print("\n" + "-" * 70)
        print("Step 4: Testing URL in Browser")
        print("-" * 70)
        
        print("\nℹ️  To complete the test:")
        print("   1. Copy the URL above")
        print("   2. Open it in your browser")
        print("   3. Login with your Fyers credentials")
        print("   4. Check if it redirects to http://127.0.0.1:8765/callback")
        
        print("\n" + "=" * 70)
        print("✓ OAuth URL is correctly configured!")
        print("=" * 70)
        
        # Stop server
        oauth.stop_callback_server()
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_url_reachability():
    """Test if the generated URL is reachable"""
    print("\n" + "=" * 70)
    print("TESTING URL REACHABILITY")
    print("=" * 70)
    
    api_key = "3DMS06KO8R-100"
    
    try:
        import httpx
        from src.services.fyers_oauth_service import FYERS_AUTH_URL
        
        # Build the actual URL
        from urllib.parse import urlencode
        params = {
            'client_id': api_key,
            'redirect_uri': 'http://127.0.0.1:8765/callback',
            'response_type': 'code',
            'state': 'fyers_auth',
            'scope': 'openid'
        }
        
        test_url = f"{FYERS_AUTH_URL}?{urlencode(params)}"
        
        print(f"\nTesting URL:")
        print(test_url)
        
        print("\nMaking HTTP request...")
        
        with httpx.Client(timeout=10, follow_redirects=False) as client:
            response = client.get(test_url)
            
            print(f"\nResponse Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ URL is reachable and returns 200 OK")
                print("✓ Fyers login page should load in browser")
                return True
            elif response.status_code in [301, 302, 303, 307, 308]:
                print(f"✓ URL redirects (status {response.status_code})")
                print(f"  Redirect to: {response.headers.get('Location', 'N/A')}")
                return True
            else:
                print(f"⚠ Unexpected status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

def main():
    print("\n")
    
    result1 = test_oauth_flow()
    result2 = test_url_reachability()
    
    print("\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    
    if result1 and result2:
        print("✓ ALL TESTS PASSED")
        print("\nYou can now run the app with: python -m src.main")
        print("\nMake sure in Fyers dashboard:")
        print("  - Redirect URL is set to: http://127.0.0.1:8765/callback")
    else:
        print("✗ SOME TESTS FAILED")
    
    print("=" * 70)
    print()

if __name__ == "__main__":
    main()
