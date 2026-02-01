"""
Test if browser can actually load the Fyers OAuth page
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

def test_url_in_browser():
    """Test the actual URL that will be opened in browser"""
    print("=" * 70)
    print("TESTING BROWSER URL LOADING")
    print("=" * 70)
    
    api_key = "3DMS06KO8R-100"
    
    from urllib.parse import urlencode
    
    # Test different URL variations
    urls_to_test = []
    
    # Current URL with all parameters
    params1 = {
        'client_id': api_key,
        'redirect_uri': 'http://127.0.0.1:8765/callback',
        'response_type': 'code',
        'state': 'fyers_auth',
        'scope': 'openid'
    }
    urls_to_test.append(("Current (with scope)", f"https://api-t1.fyers.in/api/v3/generate-authcode?{urlencode(params1)}"))
    
    # Without scope
    params2 = {
        'client_id': api_key,
        'redirect_uri': 'http://127.0.0.1:8765/callback',
        'response_type': 'code',
        'state': 'fyers_auth'
    }
    urls_to_test.append(("Without scope", f"https://api-t1.fyers.in/api/v3/generate-authcode?{urlencode(params2)}"))
    
    # Minimal parameters
    params3 = {
        'client_id': api_key,
        'redirect_uri': 'http://127.0.0.1:8765/callback',
        'response_type': 'code'
    }
    urls_to_test.append(("Minimal", f"https://api-t1.fyers.in/api/v3/generate-authcode?{urlencode(params3)}"))
    
    try:
        import httpx
        
        for name, url in urls_to_test:
            print(f"\n{'-' * 70}")
            print(f"Testing: {name}")
            print(f"{'-' * 70}")
            print(f"URL: {url}")
            
            try:
                with httpx.Client(timeout=10, follow_redirects=True) as client:
                    response = client.get(url)
                    
                    print(f"\nStatus: {response.status_code}")
                    print(f"Final URL: {response.url}")
                    
                    # Check if it's an error page
                    if "error" in str(response.url).lower():
                        print("❌ Redirected to error page")
                        # Try to extract error message
                        if "error_msg=" in str(response.url):
                            from urllib.parse import parse_qs, urlparse
                            parsed = urlparse(str(response.url))
                            params = parse_qs(parsed.query)
                            if 'error_msg' in params:
                                print(f"Error: {params['error_msg'][0]}")
                    elif response.status_code == 200:
                        print("✅ Page loaded successfully")
                        # Check if it's a login page
                        if "login" in response.text.lower() or "fyers" in response.text.lower():
                            print("✅ Looks like a login page")
                    else:
                        print(f"⚠️  Unexpected status: {response.status_code}")
                        
            except Exception as e:
                print(f"❌ Request failed: {e}")
        
        print("\n" + "=" * 70)
        print("RECOMMENDATION")
        print("=" * 70)
        
        print("\nIf all URLs fail, check:")
        print("1. Is your API Key correct? (3DMS06KO8R-100)")
        print("2. Is the app active in Fyers dashboard?")
        print("3. Is redirect URL set in Fyers: http://127.0.0.1:8765/callback")
        print("4. Try accessing Fyers dashboard: https://myapi.fyers.in/dashboard")
        
    except ImportError:
        print("\n❌ httpx not installed. Install with: pip install httpx")

def test_alternative_approach():
    """Test if we should use a different approach"""
    print("\n" + "=" * 70)
    print("CHECKING FYERS API DOCUMENTATION")
    print("=" * 70)
    
    print("\nAccording to Fyers API v3 documentation:")
    print("- Auth URL: https://api-t1.fyers.in/api/v3/generate-authcode")
    print("- Required params: client_id, redirect_uri, response_type")
    print("- Optional params: state, scope")
    
    print("\nLet me check if there's an alternative endpoint...")
    
    try:
        import httpx
        
        # Try the base API URL
        base_urls = [
            "https://api-t1.fyers.in/api/v3/",
            "https://api.fyers.in/api/v3/",
            "https://trade.fyers.in/",
        ]
        
        for base_url in base_urls:
            try:
                print(f"\nTrying: {base_url}")
                with httpx.Client(timeout=5) as client:
                    response = client.get(base_url)
                    print(f"  Status: {response.status_code}")
                    if response.status_code == 200:
                        print(f"  ✅ Reachable")
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                
    except ImportError:
        pass

def main():
    test_url_in_browser()
    test_alternative_approach()
    
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("\n1. Copy one of the URLs above")
    print("2. Paste it directly in your browser")
    print("3. Tell me what you see:")
    print("   - Does it load?")
    print("   - Is there an error message?")
    print("   - Does it show a login page?")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
