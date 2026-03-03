#!/usr/bin/env python3
"""
Refresh Gmail MCP Server Token.

Run this script to get a fresh OAuth token for the Gmail MCP server.
It will open your browser for Google OAuth authentication.

Usage:
    cd ai_employee_scripts
    uv run python refresh_gmail_mcp_token.py
"""

import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes required by Gmail MCP Server
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
]

def main():
    script_dir = Path(__file__).parent
    credentials_path = script_dir / 'credentials.json'
    token_path = script_dir / 'token_gmail.json'

    # Check for credentials.json
    if not credentials_path.exists():
        print("ERROR: credentials.json not found!")
        print(f"Looking at: {credentials_path}")
        print("\nPlease download from Google Cloud Console and place in ai_employee_scripts/")
        return 1

    print("=" * 60)
    print("GMAIL MCP SERVER - TOKEN REFRESH")
    print("=" * 60)
    print(f"\nToken file: {token_path}")
    print(f"Credentials: {credentials_path}")

    # Delete old expired token if exists
    if token_path.exists():
        print(f"\nRemoving old expired token: {token_path}")
        token_path.unlink()

    # Create OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path), SCOPES
    )
    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

    # Generate auth URL
    auth_url, _ = flow.authorization_url(
        prompt='consent',
        access_type='offline'  # Important: gets us a refresh token
    )

    print("\n" + "=" * 60)
    print("STEP 1: Authorize the Application")
    print("=" * 60)
    print("\n1. Copy this URL and open it in your browser:\n")
    print(f"   {auth_url}\n")
    print("2. Click 'Allow' to grant permissions")
    print("3. Copy the authorization code shown")
    print("\n" + "=" * 60)

    # Get authorization code from user
    code = input("\nPaste authorization code here: ").strip()

    if not code:
        print("\nERROR: No code entered. Exiting.")
        return 1

    try:
        # Exchange code for credentials
        print("\nExchanging code for token...")
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Save token to file
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes,
            'expiry': creds.expiry.isoformat() if creds.expiry else None
        }

        with open(token_path, 'w') as f:
            json.dump(token_data, f, indent=2)

        print("\n" + "=" * 60)
        print("SUCCESS! Token Saved")
        print("=" * 60)
        print(f"\nToken file: {token_path}")
        print(f"Expires: {creds.expiry}")
        print(f"Has refresh token: {bool(creds.refresh_token)}")
        print("\nYour Gmail MCP server should now work!")
        print("Restart Claude Code to apply changes.")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nTroubleshooting:")
        print("- Make sure you copied the entire authorization code")
        print("- The code expires after a few minutes - get a new one if needed")
        print("- Check that credentials.json is valid")
        return 1

if __name__ == "__main__":
    exit(main())
