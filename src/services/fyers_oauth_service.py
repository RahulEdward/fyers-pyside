"""
Fyers OAuth Service - Handles browser-based OAuth authentication
"""
import os
import hashlib
import webbrowser
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)

# Fyers OAuth Configuration
FYERS_AUTH_URL = "https://api-t1.fyers.in/api/v3/generate-authcode"
FYERS_TOKEN_URL = "https://api-t1.fyers.in/api/v3/validate-authcode"
REDIRECT_PORT = 8765
REDIRECT_URI = f"http://127.0.0.1:{REDIRECT_PORT}/callback"


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback"""
    
    auth_code = None
    error = None
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass
    
    def do_GET(self):
        """Handle GET request from OAuth callback"""
        parsed = urlparse(self.path)
        
        if parsed.path == '/callback':
            params = parse_qs(parsed.query)
            
            if 'auth_code' in params:
                OAuthCallbackHandler.auth_code = params['auth_code'][0]
                self._send_success_response()
            elif 'code' in params:
                OAuthCallbackHandler.auth_code = params['code'][0]
                self._send_success_response()
            else:
                OAuthCallbackHandler.error = params.get('error', ['Unknown error'])[0]
                self._send_error_response()
        else:
            self.send_response(404)
            self.end_headers()
    
    def _send_success_response(self):
        """Send success HTML response"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Fyers Authentication</title>
            <style>
                body {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background: linear-gradient(135deg, #131722 0%, #1E222D 100%);
                    color: #E0E0E0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    text-align: center;
                    padding: 40px;
                    background: #1E222D;
                    border-radius: 16px;
                    border: 1px solid #2A2E39;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                }
                .success-icon {
                    font-size: 64px;
                    margin-bottom: 20px;
                }
                h1 {
                    color: #00D09C;
                    margin-bottom: 10px;
                }
                p {
                    color: #9E9E9E;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✅</div>
                <h1>Authentication Successful!</h1>
                <p>You can close this window and return to the application.</p>
            </div>
            <script>setTimeout(function() { window.close(); }, 3000);</script>
        </body>
        </html>
        """
        self.wfile.write(html.encode())
    
    def _send_error_response(self):
        """Send error HTML response"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Fyers Authentication Failed</title>
            <style>
                body {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background: linear-gradient(135deg, #131722 0%, #1E222D 100%);
                    color: #E0E0E0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    text-align: center;
                    padding: 40px;
                    background: #1E222D;
                    border-radius: 16px;
                    border: 1px solid #2A2E39;
                }
                .error-icon { font-size: 64px; margin-bottom: 20px; }
                h1 { color: #FF5252; }
                p { color: #9E9E9E; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon">❌</div>
                <h1>Authentication Failed</h1>
                <p>Please try again or check your credentials.</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode())


class FyersOAuthService:
    """Service for Fyers OAuth authentication"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.server = None
        self.server_thread = None
    
    def generate_auth_url(self) -> str:
        """Generate Fyers OAuth authorization URL"""
        params = {
            'client_id': self.api_key,
            'redirect_uri': REDIRECT_URI,
            'response_type': 'code',
            'state': 'fyers_auth',
            'scope': 'openid'
        }
        return f"{FYERS_AUTH_URL}?{urlencode(params)}"
    
    def start_callback_server(self) -> bool:
        """Start local HTTP server for OAuth callback"""
        try:
            # Reset state
            OAuthCallbackHandler.auth_code = None
            OAuthCallbackHandler.error = None
            
            # Try to create server
            try:
                self.server = HTTPServer(('127.0.0.1', REDIRECT_PORT), OAuthCallbackHandler)
            except OSError as e:
                if "address already in use" in str(e).lower():
                    logger.error(f"Port {REDIRECT_PORT} is already in use. Please close other applications using this port.")
                    return False
                raise
            
            self.server.timeout = 120  # 2 minute timeout
            
            # Start server in background thread
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            logger.info(f"OAuth callback server started on http://127.0.0.1:{REDIRECT_PORT}/callback")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start callback server: {e}")
            return False
    
    def _run_server(self):
        """Run the HTTP server - handles multiple requests"""
        try:
            # Handle multiple requests in case of redirects
            while not OAuthCallbackHandler.auth_code and not OAuthCallbackHandler.error:
                self.server.handle_request()
                if OAuthCallbackHandler.auth_code or OAuthCallbackHandler.error:
                    break
        except Exception as e:
            logger.error(f"Server error: {e}")
    
    def stop_callback_server(self):
        """Stop the callback server"""
        if self.server:
            try:
                # Shutdown server properly
                self.server.server_close()
                self.server = None
                logger.info("OAuth callback server stopped")
            except Exception as e:
                logger.error(f"Error stopping server: {e}")
                self.server = None
    
    def authenticate(self, on_success: Callable[[str], None] = None, 
                    on_error: Callable[[str], None] = None) -> Optional[str]:
        """
        Start OAuth flow - opens browser and waits for callback
        
        Returns:
            Access token on success, None on failure
        """
        try:
            # Start callback server FIRST
            if not self.start_callback_server():
                if on_error:
                    on_error("Failed to start authentication server. Port 8765 may be in use.")
                return None
            
            # Wait a moment for server to be fully ready
            time.sleep(0.5)
            
            # Generate and open auth URL
            auth_url = self.generate_auth_url()
            logger.info(f"Opening browser for Fyers authentication...")
            logger.info(f"Auth URL: {auth_url}")
            
            webbrowser.open(auth_url)
            
            # Wait for callback (max 2 minutes)
            timeout = 120
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if OAuthCallbackHandler.auth_code:
                    # Got auth code, exchange for access token
                    logger.info(f"Received auth code: {OAuthCallbackHandler.auth_code[:20]}...")
                    access_token = self._exchange_code_for_token(OAuthCallbackHandler.auth_code)
                    
                    if access_token:
                        logger.info("Successfully obtained access token")
                        if on_success:
                            on_success(access_token)
                        return access_token
                    else:
                        if on_error:
                            on_error("Failed to exchange auth code for token")
                        return None
                
                if OAuthCallbackHandler.error:
                    if on_error:
                        on_error(OAuthCallbackHandler.error)
                    return None
                
                time.sleep(0.5)
            
            # Timeout
            if on_error:
                on_error("Authentication timed out - did not receive callback")
            return None
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            if on_error:
                on_error(str(e))
            return None
        finally:
            self.stop_callback_server()
    
    def _exchange_code_for_token(self, auth_code: str) -> Optional[str]:
        """Exchange authorization code for access token"""
        try:
            import httpx
            
            # Generate app ID hash
            checksum_input = f"{self.api_key}:{self.api_secret}"
            app_id_hash = hashlib.sha256(checksum_input.encode()).hexdigest()
            
            payload = {
                'grant_type': 'authorization_code',
                'appIdHash': app_id_hash,
                'code': auth_code
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Exchanging auth code for access token...")
            
            with httpx.Client() as client:
                response = client.post(FYERS_TOKEN_URL, json=payload, headers=headers, timeout=30)
                data = response.json()
                
                logger.info(f"Token response: {data}")
                
                if data.get('s') == 'ok' and 'access_token' in data:
                    access_token = data.get('access_token')
                    logger.info("Successfully obtained Fyers access token")
                    return access_token
                else:
                    error_msg = data.get('message', 'Unknown error')
                    logger.error(f"Token exchange failed: {error_msg}")
                    return None
                    
        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return None
