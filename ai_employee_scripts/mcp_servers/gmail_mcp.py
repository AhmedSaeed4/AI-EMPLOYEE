#!/usr/bin/env python3
"""
Gmail MCP Server - Send and manage emails via Gmail API

This is an MCP (Model Context Protocol) server that exposes Gmail
functionality as tools that Claude Code can call directly.

Date: 2026-02-15
"""

import asyncio
import base64
import os
import logging
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path
from typing import Optional

from mcp.server import FastMCP
from mcp.server.stdio import stdio_server

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ====== CONFIGURATION ======

SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',    # Required for sending emails
    'https://www.googleapis.com/auth/gmail.modify',  # Required for drafts/labels
]

# Global variables (initialized on startup)
_gmail_service = None
_creds = None

# ====== LOGGING SETUP ======

def setup_logger():
    """Set up logging for the MCP server."""
    logger = logging.getLogger('gmail-mcp')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger()

# ====== AUTHENTICATION ======

def authenticate():
    """
    Authenticate with Gmail API using OAuth 2.0.

    This handles:
    1. Loading existing credentials from token file
    2. Refreshing tokens if expired
    3. Running OAuth flow if no valid credentials (uses run_console for WSL)

    Returns:
        Gmail service object ready for API calls

    Raises:
        FileNotFoundError if credentials.json not found
    """
    global _gmail_service, _creds

    # Find credentials.json
    script_dir = Path(__file__).parent.parent
    possible_creds_paths = [
        script_dir / 'credentials.json',
        script_dir.parent / 'credentials.json',
    ]

    credentials_path = None
    for path in possible_creds_paths:
        if path.exists():
            credentials_path = path
            break

    if credentials_path is None:
        logger.error("credentials.json not found. Please download from Google Cloud Console.")
        raise FileNotFoundError("credentials.json not found")

    # Token storage path
    token_path = credentials_path.parent / 'token_gmail.json'

    # Load existing credentials if available
    _creds = None
    if token_path.exists():
        try:
            _creds = Credentials.from_authorized_user_file(
                str(token_path), SCOPES
            )
        except Exception as e:
            logger.warning(f"Failed to load token: {e}. Will re-authenticate.")

    # Refresh or get new credentials
    if not _creds or not _creds.valid:
        if _creds and _creds.expired and _creds.refresh_token:
            try:
                _creds.refresh(Request())
                logger.info("Refreshed expired credentials")
            except Exception as e:
                logger.warning(f"Refresh failed: {e}. Will run full OAuth flow.")
                _creds = None  # Force re-auth

        if not _creds or not _creds.valid:
            logger.info("Running OAuth flow...")
            logger.info("=" * 60)
            logger.info("AUTHENTICATION REQUIRED")
            logger.info("=" * 60)

            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )

            # Manual OAuth flow for WSL compatibility
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

            auth_url, _ = flow.authorization_url(prompt='consent')
            logger.info("")
            logger.info("Visit this URL to authorize the application:")
            logger.info("")
            logger.info(auth_url)
            logger.info("")
            logger.info("After authorizing, paste the authorization code here and press Enter:")

            code = input("Enter authorization code: ")

            # Exchange code for credentials
            flow.fetch_token(code=code)
            _creds = flow.credentials

            logger.info("=" * 60)
            logger.info("Authentication successful!")

            # Save credentials for next run (overwrites old token)
            import json
            with open(token_path, 'w') as token:
                json.dump({
                    'token': _creds.token,
                    'refresh_token': _creds.refresh_token,
                    'token_uri': _creds.token_uri,
                    'client_id': _creds.client_id,
                    'client_secret': _creds.client_secret,
                    'scopes': _creds.scopes,
                    'expiry': _creds.expiry.isoformat() if _creds.expiry else None
                }, token)
            logger.info(f"Token saved to: {token_path}")
            logger.info("=" * 60)

    # Build and return service
    _gmail_service = build('gmail', 'v1', credentials=_creds)
    return _gmail_service

def get_gmail_service():
    """Get or initialize Gmail service."""
    global _gmail_service
    if _gmail_service is None:
        _gmail_service = authenticate()
    return _gmail_service

# ====== MCP SERVER SETUP ======

# Create FastMCP instance
mcp = FastMCP(
    "gmail-mcp",
    instructions="""
    Gmail integration for sending and managing emails.

    Available tools:
    - send_email: Send an email to specified recipient
    - draft_email: Create a draft email (doesn't send)
    - search_emails: Search for emails matching query
    - get_thread: Get all messages in a thread

    All email actions are logged to the vault's Logs folder.
    """
)

# ====== MCP TOOLS ======

@mcp.tool()
async def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None
) -> str:
    """
    Send an email via Gmail API.

    Args:
        to: Recipient email address(es)
        subject: Email subject line
        body: Email body content (plain text)
        cc: Optional CC recipients
        bcc: Optional BCC recipients

    Returns:
        Confirmation message with message ID, or error message
    """
    service = get_gmail_service()

    try:
        # Create email message
        message = EmailMessage()
        message['To'] = to
        message['Subject'] = subject
        message.set_content(body)

        if cc:
            message['Cc'] = cc
        if bcc:
            message['Bcc'] = bcc

        # Convert to Gmail format
        raw = base64.urlsafe_b64encode(message.as_string().encode()).decode()

        # Send via Gmail API
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()

        logger.info(f"Email sent to {to}. ID: {result['id']}")

        return f"Email sent successfully to {to}\nMessage ID: {result['id']}"

    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
async def draft_email(
    to: str,
    subject: str,
    body: str
) -> str:
    """
    Create a draft email via Gmail API (doesn't send).

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content

    Returns:
        Draft ID and confirmation, or error message
    """
    service = get_gmail_service()

    try:
        # Create email message
        message = EmailMessage()
        message['To'] = to
        message['Subject'] = subject
        message.set_content(body)

        # Convert to Gmail format
        raw = base64.urlsafe_b64encode(message.as_string().encode()).decode()

        # Create draft
        result = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw}}
        ).execute()

        logger.info(f"Draft created. ID: {result['id']}")

        return f"Draft created successfully\nDraft ID: {result['id']}\nRecipient: {to}"

    except Exception as e:
        error_msg = f"Error creating draft: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
async def search_emails(
    query: str,
    max_results: int = 10
) -> str:
    """
    Search Gmail for emails matching a query.

    Args:
        query: Gmail search query (same syntax as Gmail search box)
        max_results: Maximum number of results to return

    Returns:
        Formatted list of matching emails
    """
    service = get_gmail_service()

    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])

        output = []
        for msg in messages:
            msg_detail = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata'
            ).execute()

            # Extract headers
            headers = {}
            for h in msg_detail['payload'].get('headers', []):
                name = h.get('name')
                if name in ['From', 'Subject', 'Date']:
                    headers[name] = h.get('value')

            output.append({
                'id': msg['id'],
                'from': headers.get('From', 'Unknown'),
                'subject': headers.get('Subject', 'No Subject')
            })

        logger.info(f"Search '{query}' found {len(output)} results")

        return f"Search results for '{query}':\n" + "\n".join(
            f"- {m['subject']} (from: {m['from']})" for m in output
        )

    except Exception as e:
        error_msg = f"Error searching emails: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
async def get_thread(thread_id: str) -> str:
    """
    Get all messages in a Gmail thread.

    Args:
        thread_id: Gmail thread ID

    Returns:
        Thread messages with subjects and senders
    """
    service = get_gmail_service()

    try:
        results = service.users().threads().get(
            userId='me',
            id=thread_id
        ).execute()

        messages = results.get('messages', [])

        output = []
        for msg in messages:
            msg_detail = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata'
            ).execute()

            headers = {}
            for h in msg_detail['payload'].get('headers', []):
                name = h.get('name')
                if name in ['From', 'Subject', 'Date']:
                    headers[name] = h.get('value')

            output.append({
                'id': msg['id'],
                'from': headers.get('From', 'Unknown'),
                'subject': headers.get('Subject', 'No Subject')
            })

        return f"Thread {thread_id}:\n" + "\n".join(
            f"- {m['subject']} (from: {m['from']})" for m in output
        )

    except Exception as e:
        error_msg = f"Error getting thread: {str(e)}"
        logger.error(error_msg)
        return error_msg

# ====== MAIN ENTRY POINT ======

async def main():
    """
    Run the Gmail MCP server.

    Authentication happens on startup before MCP server starts.
    """
    logger.info("Starting Gmail MCP Server...")

    # Authenticate FIRST (before MCP server starts)
    # This ensures we have valid credentials before accepting any tool calls
    logger.info("Authenticating with Gmail...")
    authenticate()
    logger.info("Authentication complete. Gmail MCP server is ready.")
    logger.info("Waiting for Claude Code to connect via stdio...")

    # Now run the MCP server (must be awaited)
    await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())
