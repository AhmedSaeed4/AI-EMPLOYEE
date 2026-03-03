from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request, urllib.parse, json
import os
from pathlib import Path

# Load .env file
ENV_FILE = Path(__file__).parent / "ai_employee_scripts" / ".env"
if ENV_FILE.exists():
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        code = parse_qs(urlparse(self.path).query).get('code', [None])[0]
        if code:
            data = urllib.parse.urlencode({
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': os.getenv('LINKEDIN_CLIENT_ID'),
                'client_secret': os.getenv('LINKEDIN_CLIENT_SECRET'),
                'redirect_uri': 'http://localhost:8000/callback'
            }).encode()
            try:
                res = urllib.request.urlopen('https://www.linkedin.com/oauth/v2/accessToken', data)
                token_data = json.loads(res.read().decode())
                print("\n✅ ACCESS TOKEN:", token_data['access_token'])
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Got the token! Check your terminal.")
            except Exception as e:
                print("Error:", e)
    def log_message(self, *args): pass

print("Waiting for LinkedIn... Open the URL in your browser now.")
HTTPServer(('', 8000), Handler).handle_request()