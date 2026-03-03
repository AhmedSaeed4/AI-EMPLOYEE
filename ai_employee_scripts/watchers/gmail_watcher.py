"""
Gmail Watcher - Monitors Gmail for recent emails (last 24 hours)
Creates action files in Needs_Action folder for all new emails.
"""
import os
import time
import logging
from pathlib import Path
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from base_watcher import BaseWatcher


# Gmail API Scopes - use broader scopes to work with existing token
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]


class GmailWatcher(BaseWatcher):
    """Watches Gmail for recent emails (last 24 hours)."""

    def __init__(self, vault_path: str, credentials_path: str = None, check_interval: int = 120):
        """
        Initialize Gmail Watcher.

        Args:
            vault_path: Path to AI_Employee_Vault
            credentials_path: Path to credentials.json file
            check_interval: Seconds between checks (default: 120)
        """
        super().__init__(vault_path, check_interval)
        self.credentials_path = Path(credentials_path) if credentials_path else None
        self.service = None
        self.processed_ids = set()
        # Inbox folder for storing full emails
        self.inbox = Path(vault_path) / 'Inbox'
        self.inbox.mkdir(parents=True, exist_ok=True)
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth."""
        # Look for credentials in script directory or parent directory
        if self.credentials_path is None:
            # Try default locations
            script_dir = Path(__file__).parent.parent
            possible_paths = [
                script_dir / 'credentials.json',
                script_dir.parent / 'credentials.json',
            ]
            for path in possible_paths:
                if path.exists():
                    self.credentials_path = path
                    break

        if self.credentials_path is None or not self.credentials_path.exists():
            self.logger.error(f'credentials.json not found at {self.credentials_path}')
            self.logger.error('Please download from Google Cloud Console and place in ai_employee_scripts/')
            raise FileNotFoundError('credentials.json not found')

        # Look for token file - USE WATCHER-SPECIFIC TOKEN ONLY
        # NEVER touch the MCP's token_gmail.json
        token_path = self.credentials_path.parent / 'token_gmail_watcher.json'

        creds = None
        if token_path.exists():
            # Load watcher's own token
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Save refreshed watcher credentials
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                except RefreshError:
                    # Watcher token refresh failed - re-auth
                    self.logger.warning('Watcher token expired. Re-authenticating...')
                    creds = None

            if not creds or not creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=8080)
                # Save to watcher-specific token file (NEVER touches MCP token)
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)
        self.logger.info('Gmail authentication successful')

    def check_for_updates(self) -> list:
        """
        Check for new recent emails (last 24 hours).

        Returns:
            List of new email messages
        """
        try:
            # Query for recent emails (last 24 hours), exclude sent emails
            results = self.service.users().messages().list(
                userId='me',
                q='newer_than:1d -in:sent',
                maxResults=20
            ).execute()

            messages = results.get('messages', [])

            # Filter out already processed messages
            new_messages = [
                m for m in messages
                if m['id'] not in self.processed_ids
            ]

            return new_messages

        except Exception as e:
            self.logger.error(f'Error checking Gmail: {e}')
            return []

    def create_action_file(self, message) -> Path:
        """
        Create action file for an email.
        Stores full email in Inbox/ and creates a reference in Needs_Action/.

        Args:
            message: Gmail message object

        Returns:
            Path to created action file
        """
        try:
            # Get FULL message details (including body)
            msg = self.service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()

            # Extract headers
            headers = {}
            for h in msg['payload'].get('headers', []):
                name = h['name']
                if name in ['From', 'Subject', 'Date', 'To', 'Cc']:
                    headers[name] = h['value']

            sender = headers.get('From', 'Unknown')
            subject = headers.get('Subject', 'No Subject')
            date_str = headers.get('Date', datetime.now().isoformat())
            to = headers.get('To', '')
            cc = headers.get('Cc', '')

            # Extract email body
            body_text, body_html = self._extract_body(msg['payload'])

            # Determine priority based on sender/subject
            priority = self._determine_priority(sender, subject)

            # 1. Store full email in Inbox/
            inbox_filename = f'EMAIL_{message["id"]}.md'
            inbox_filepath = self.inbox / inbox_filename

            inbox_content = f'''---
type: email
source: gmail
message_id: {message['id']}
from: {sender}
to: {to}
cc: {cc}
subject: {subject}
received: {date_str}
---

# {subject}

**From:** {sender}
**To:** {to}
**Cc:** {cc}
**Date:** {date_str}
**Message ID:** {message['id']}

---

## Email Body

{body_text if body_text else body_html}
'''

            inbox_filepath.write_text(inbox_content, encoding='utf-8')
            self.logger.info(f'Stored full email in Inbox: {inbox_filename}')

            # 2. Create task file in Needs_Action/ (with reference)
            safe_subject = subject[:50].replace('/', '-').replace('\\', '-')
            safe_subject = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in safe_subject)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            task_filename = f'EMAIL_{safe_subject}_{timestamp}.md'

            task_content = f'''---
type: email
source: gmail
message_id: {message['id']}
from: {sender}
subject: {subject}
received: {date_str}
priority: {priority}
status: pending
inbox_ref: {inbox_filename}
created: {datetime.now().isoformat()}
---

# Email from {sender}

## Subject
{subject}

## Details
- **From:** {sender}
- **Received:** {date_str}
- **Priority:** {priority}
- **Full Email:** `../Inbox/{inbox_filename}`

## Preview
{body_text[:500] if body_text and len(body_text) > 500 else (body_text or body_html[:500] if body_html else '')}
{'...' if (body_text and len(body_text) > 500) or (body_html and len(body_html) > 500) else ''}

## Suggested Actions
- [ ] Read full email in `Inbox/{inbox_filename}`
- [ ] Determine if action needed
- [ ] Respond or archive

## Quick Reply Ideas
- [ ] "Thank you for reaching out..."
- [ ] "I'll review and get back to you..."
- [ ] Forward to relevant person
'''

            # Write to Needs_Action
            task_filepath = self.needs_action / task_filename
            task_filepath.write_text(task_content, encoding='utf-8')

            # Mark as processed
            self.processed_ids.add(message['id'])

            return task_filepath

        except Exception as e:
            self.logger.error(f'Error creating action file: {e}')
            raise

    def _extract_body(self, payload: dict) -> tuple:
        """
        Extract email body from Gmail payload.

        Args:
            payload: Gmail message payload

        Returns:
            Tuple of (text_body, html_body) - one may be empty
        """
        import base64
        from email import message_from_string

        text_body = ''
        html_body = ''

        def decode_data(data: str) -> str:
            """Decode base64 URL encoded data."""
            if not data:
                return ''
            # Add padding if needed
            missing_padding = len(data) % 4
            if missing_padding:
                data += '=' * (4 - missing_padding)
            try:
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            except Exception:
                return data

        def extract_from_part(part: dict) -> tuple:
            """Recursively extract body from a message part."""
            text = ''
            html = ''

            # Check if this part has a body
            if 'body' in part and 'data' in part['body']:
                data = decode_data(part['body']['data'])
                mime_type = part.get('mimeType', '')

                if mime_type == 'text/plain':
                    text = data
                elif mime_type == 'text/html':
                    html = data

            # Recursively check nested parts
            if 'parts' in part:
                for subpart in part['parts']:
                    sub_text, sub_html = extract_from_part(subpart)
                    if sub_text and not text:
                        text = sub_text
                    if sub_html and not html:
                        html = sub_html

            return text, html

        text_body, html_body = extract_from_part(payload)

        # If HTML only, strip tags for text preview
        if not text_body and html_body:
            import re
            text_body = re.sub(r'<[^>]+>', ' ', html_body)
            text_body = ' '.join(text_body.split())

        return text_body, html_body

    def _determine_priority(self, sender: str, subject: str) -> str:
        """
        Determine email priority based on sender and subject.

        Args:
            sender: Email sender address
            subject: Email subject line

        Returns:
            Priority level: high, medium, or low
        """
        sender_lower = sender.lower()
        subject_lower = subject.lower()

        # High priority keywords
        high_keywords = ['urgent', 'asap', 'emergency', 'important', 'deadline']
        if any(kw in subject_lower for kw in high_keywords):
            return 'high'

        # High priority senders (customize based on your contacts)
        # Add important clients, boss, etc.
        # if any(contact in sender_lower for contact in self.high_priority_contacts):
        #     return 'high'

        # Medium priority
        medium_keywords = ['invoice', 'payment', 'meeting', 'proposal']
        if any(kw in subject_lower for kw in medium_keywords):
            return 'medium'

        return 'low'

    def mark_as_read(self, message_id: str):
        """
        Mark a message as read in Gmail.

        Args:
            message_id: Gmail message ID
        """
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            self.logger.info(f'Marked {message_id} as read')
        except Exception as e:
            self.logger.error(f'Error marking as read: {e}')


def main():
    """Run the Gmail Watcher."""
    # Determine vault path
    vault_path = Path(__file__).parent.parent.parent / 'AI_Employee_Vault'

    watcher = GmailWatcher(
        vault_path=str(vault_path),
        check_interval=120  # Check every 2 minutes
    )

    print("Gmail Watcher starting... Press Ctrl+C to stop.")
    watcher.run()


if __name__ == '__main__':
    main()
