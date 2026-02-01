"""
Test OAuth URL generation to see what URL is being opened
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

def test_oauth_url_generation():
    """Test the OAuth URL that gets generated"""
    print("=" * 70)
    print("Testing Fyers OAuth URL Generation")
    print("=" * 70)
    
    # Test credentials (dummy)
    test_api_key = "TESTKEY123-100"
    test_api_secret = "TEST_SECRET_KEY"
    
    print(f"\nTest API Key: {test_api_key}")
    print(f"Test API Secret: {test_api_secret[:10]}...")
    
    # Test URL generation from OAuth service
    print("\n" + "-" * 70)
    print("1. Testing OAuth Service URL Generation")
    print("-" * 70)
    
    try:
        from src.services.fyers_oauth_service import FyersOAuthService, FYERS_AUTH_URL, REDIRECT_URI
        
        print(f"\nBase Auth URL: {FYERS_AUTH_URL}")
        print(f"Redirect URI: {REDIRECT_URI}")
        
        oauth = FyersOAuthService(test_api_key, test_api_secret)
        auth_url = oauth.generate_auth_url()
        
        print(f"\nGenerated OAuth URL:")
        print(auth_url)
        
        # Check URL components
        print("\n" + "-" * 70)
        print("URL Components Check:")
        print("-" * 70)
        
        checks = [
            ("Contains client_id", f"client_id={test_api_key}" in auth_url),
            ("Contains redirect_uri", "redirect_uri=" in auth_url),
            ("Contains response_type=code", "response_type=code" in auth_url),
            ("Contains state", "state=" in auth_url),
            ("Starts with correct base URL", auth_url.startswith(FYERS_AUTH_URL))
        ]
        
        for check_name, result in checks:
            status = "✓" if result else "✗"
            print(f"{status} {check_name}")
        
        all_passed = all(result for _, result in checks)
        
        if all_passed:
            print("\n✓ All URL checks passed!")
        else:
            print("\n✗ Some URL checks failed!")
        
        return all_passed
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_broker_service_url():
    """Test URL generation from broker service"""
    print("\n" + "-" * 70)
    print("2. Testing Broker Service URL Generation")
    print("-" * 70)
    
    try:
        from src.services.broker_service import BrokerService, FYERS_AUTH_URL
        from src.services.encryption_service import EncryptionService
        from src.repositories.credential_repository import CredentialRepository
        from src.database.connection import init_db, get_session
        
        print(f"\nBroker Service Auth URL: {FYERS_AUTH_URL}")
        
        # Initialize services
        init_db()
        session = get_session()
        encryption_service = EncryptionService(b'test_key_32_bytes_long_enough!!')
        cred_repo = CredentialRepository(session)
        broker_service = BrokerService(cred_repo, encryption_service)
        
        # Generate URL
        test_api_key = "TESTKEY123-100"
        result = broker_service.generate_oauth_url(test_api_key)
        
        if result.is_ok():
            url = result.value
            print(f"\nGenerated URL:")
            print(url)
            
            print("\n✓ Broker service URL generation successful!")
            return True
        else:
            print(f"\n✗ Error: {result.error}")
            return False
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_actual_fyers_url():
    """Test if we can reach the Fyers auth endpoint"""
    print("\n" + "-" * 70)
    print("3. Testing Actual Fyers Endpoint Reachability")
    print("-" * 70)
    
    try:
        import httpx
        from src.services.fyers_oauth_service import FYERS_AUTH_URL
        
        # Try to make a simple GET request to see if endpoint exists
        test_url = FYERS_AUTH_URL + "?client_id=TEST"
        
        print(f"\nTesting URL: {test_url}")
        print("Making HTTP request...")
        
        with httpx.Client(timeout=10) as client:
            response = client.get(test_url, follow_redirects=True)
            
            print(f"\nResponse Status: {response.status_code}")
            print(f"Response URL: {response.url}")
            
            if response.status_code == 200:
                print("✓ Endpoint is reachable!")
                return True
            elif response.status_code == 400:
                print("✓ Endpoint exists (400 = bad request, expected with test data)")
                return True
            else:
                print(f"⚠ Unexpected status code: {response.status_code}")
                print(f"Response text: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"\n✗ Error reaching endpoint: {e}")
        return False

def main():
    print("\n")
    print("=" * 70)
    print("FYERS OAUTH URL DIAGNOSTIC TEST")
    print("=" * 70)
    
    results = []
    
    results.append(("OAuth Service URL", test_oauth_url_generation()))
    results.append(("Broker Service URL", test_broker_service_url()))
    results.append(("Fyers Endpoint", test_actual_fyers_url()))
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - OAuth should work!")
    else:
        print("✗ SOME TESTS FAILED - Check errors above")
    print("=" * 70)
    print()

if __name__ == "__main__":
    main()
