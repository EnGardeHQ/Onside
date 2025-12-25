"""
Script to generate a Google OAuth2 refresh token for the Search Console API.
This only needs to be run once to get the initial refresh token.
"""
import os
import sys
import json
import webbrowser
from typing import Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

# OAuth 2.0 configuration
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
REDIRECT_URI = 'http://localhost:8080/callback'
AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
TOKEN_URI = 'https://oauth2.googleapis.com/token'

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP server to handle OAuth 2.0 callback."""
    auth_code = None
    
    def do_GET(self):
        """Handle GET request to the callback URL."""
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/callback':
            query = parse_qs(parsed_path.query)
            if 'code' in query:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'''
                    <html><body>
                    <h1>Authentication successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                    </body></html>
                ''')
                OAuthCallbackHandler.auth_code = query['code'][0]
                return
        
        self.send_error(404, 'Not Found')
    
    def log_message(self, format, *args):
        """Override to prevent logging to stderr."""
        return

def get_auth_url() -> str:
    """Generate the authorization URL."""
    client_id = os.getenv('PAGESPEED_CLIENT_ID')
    if not client_id:
        raise ValueError("PAGESPEED_CLIENT_ID environment variable not set")
    
    params = {
        'client_id': client_id,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',
    }
    
    query = '&'.join([f"{k}={v}" for k, v in params.items()])
    return f"{AUTH_URI}?{query}"

def exchange_code_for_token(auth_code: str) -> Dict[str, Any]:
    """Exchange authorization code for tokens."""
    flow = Flow.from_client_config(
        {
            'web': {
                'client_id': os.getenv('PAGESPEED_CLIENT_ID'),
                'client_secret': os.getenv('Google Web CLIENT_SECRET'),
                'auth_uri': AUTH_URI,
                'token_uri': TOKEN_URI,
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    flow.fetch_token(code=auth_code)
    return flow.credentials.to_json()

def main():
    """Run the OAuth 2.0 flow and print the refresh token."""
    try:
        # Check required environment variables
        required_vars = ['PAGESPEED_CLIENT_ID', 'Google Web CLIENT_SECRET']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print("Error: The following required environment variables are not set:")
            for var in missing_vars:
                print(f"- {var}")
            print("\nPlease set these variables in your .env file and try again.")
            sys.exit(1)
        
        # Start HTTP server to handle the OAuth 2.0 callback
        server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
        
        try:
            # Get the authorization URL and open it in the default web browser
            auth_url = get_auth_url()
            print("Opening authorization URL in your default web browser...")
            print(f"If the browser doesn't open, please visit this URL manually:\n{auth_url}\n")
            webbrowser.open(auth_url)
            
            # Wait for the OAuth 2.0 callback
            print("Waiting for authorization...")
            while OAuthCallbackHandler.auth_code is None:
                server.handle_request()
            
            # Exchange the authorization code for tokens
            print("\nAuthorization received! Exchanging code for tokens...")
            tokens = exchange_code_for_token(OAuthCallbackHandler.auth_code)
            tokens_data = json.loads(tokens)
            
            # Print the refresh token
            refresh_token = tokens_data.get('refresh_token')
            if not refresh_token:
                print("Error: No refresh token received. Make sure to grant offline access.")
                sys.exit(1)
            
            print("\n✅ Success! Add the following to your .env file:")
            print(f"GOOGLE_REFRESH_TOKEN={refresh_token}")
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(1)
        finally:
            # Shut down the server
            server.server_close()
            
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}", file=sys.stderr)
        if 'invalid_client' in str(e):
            print("\nMake sure your client ID and secret are correct and that the redirect URI")
            print(f"is properly configured in the Google Cloud Console: {REDIRECT_URI}")
        sys.exit(1)

if __name__ == '__main__':
    print("Google OAuth 2.0 Token Generator")
    print("===============================")
    print("This script will help you generate a refresh token for the Google Search Console API.")
    print("You'll need to authorize the application in your web browser.\n")
    
    main()
