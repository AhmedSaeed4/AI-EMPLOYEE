# Gmail MCP Server Documentation

## Overview

The Gmail MCP Server provides email functionality to the AI Employee via the Gmail API. It enables sending emails, creating drafts, searching emails, and retrieving message threads through the Model Context Protocol (MCP).

**Location:** `ai_employee_scripts/mcp_servers/gmail_mcp.py`

**MCP Name:** `gmail`

---

## Features

### Available Tools

| Tool | Description | Async |
|------|-------------|-------|
| `send_email` | Send an email to specified recipient(s) | Yes |
| `draft_email` | Create a draft email (doesn't send) | Yes |
| `search_emails` | Search Gmail for emails matching a query | Yes |
| `get_thread` | Get all messages in a Gmail thread | Yes |

### Tool Parameters

#### `send_email`
```python
mcp__gmail__send_email(
    to: str,           # Recipient email address(es)
    subject: str,      # Email subject line
    body: str,         # Email body content (plain text)
    cc: str = None,    # Optional CC recipients
    bcc: str = None    # Optional BCC recipients
)
```

**Returns:** Confirmation message with Message ID

#### `draft_email`
```python
mcp__gmail__draft_email(
    to: str,           # Recipient email address
    subject: str,      # Email subject line
    body: str          # Email body content
)
```

**Returns:** Draft ID and confirmation

#### `search_emails`
```python
mcp__gmail__search_emails(
    query: str,                # Gmail search query (same syntax as Gmail search box)
    max_results: int = 10      # Maximum number of results to return
)
```

**Returns:** Formatted list of matching emails with sender and subject

#### `get_thread`
```python
mcp__gmail__get_thread(
    thread_id: str     # Gmail thread ID
)
```

**Returns:** Thread messages with subjects and senders

---

## Setup Guide

### Prerequisites

1. **Google Account:** A Google Account with Gmail enabled
2. **Python 3.13+** with UV package manager
3. **Google Cloud Project** with Gmail API enabled

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API:
   - Navigate to **APIs & Services** → **Library**
   - Search for "Gmail API"
   - Click **Enable**

### Step 2: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. Configure OAuth consent screen if prompted:
   - Choose **External** user type
   - Add app name, user support email
   - Add **Scopes**:
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/gmail.modify`
   - Add test users (your email address)
4. Create OAuth client ID:
   - Application type: **Desktop app**
   - Name: `Gmail MCP Server`
5. Download the credentials JSON file
6. Rename it to `credentials.json`
7. Place it in: `ai_employee_scripts/credentials.json`

### Step 3: Install Dependencies

```bash
cd ai_employee_scripts
uv sync
```

The required packages are:
- `google-api-python-client>=2.189.0`
- `google-auth-oauthlib>=1.2.4`

### Step 4: Create OAuth Token

**Use the refresh script (Recommended method):**

```bash
cd ai_employee_scripts
uv run python refresh_gmail_mcp_token.py
```

**Authentication Flow:**

1. Script checks for `credentials.json`
2. Generates OAuth authorization URL
3. Copy the URL and open it in your browser
4. Click **Allow** to grant permissions
5. Copy the authorization code from the browser
6. Paste the code into the terminal when prompted
7. Token is saved to `token_gmail.json`

**Why use the refresh script?**
- Dedicated tool for token creation/refresh
- Clear step-by-step terminal output
- Automatically removes old expired tokens
- Uses `access_type=offline` to get refresh token

**Alternative: Run the MCP server directly**

```bash
cd ai_employee_scripts
uv run python mcp_servers/gmail_mcp.py
```

The MCP server will also trigger OAuth flow if no valid token exists.

---

## Configuration

### MCP Server Configuration

The Gmail MCP is configured in `AI_Employee_Vault/.mcp.json`:

```json
{
  "mcpServers": {
    "gmail": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/ai-employee/ai_employee_scripts",
        "run",
        "mcp_servers/gmail_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/ai-employee/ai_employee_scripts"
      }
    }
  }
}
```

**Replace:** `/path/to/ai-employee` with your actual project path

### Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `PYTHONPATH` | Path to `ai_employee_scripts` | Python module import path |

**Note:** The `credentials.json` and `token_gmail.json` are loaded from the same directory as the MCP script (`ai_employee_scripts/`).

### Token Storage

After successful authentication, tokens are stored at:
- **Location:** `ai_employee_scripts/token_gmail.json`
- **Format:** JSON with access token, refresh token, expiry

**Token structure:**
```json
{
  "token": "ya29.a0AfB6...[truncated]",
  "refresh_token": "1//0g...[truncated]",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "779023793111-xxxxx.apps.googleusercontent.com",
  "client_secret": "GOCSPX-xxxxx",
  "scopes": [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify"
  ],
  "expiry": "2026-02-22T02:44:23"
}
```

**Token Auto-Refresh:** The server automatically refreshes expired tokens using the refresh token.

---

## Authentication Workflow

### Diagram

```
┌─────────────────────────────────────┐
│  Step 1: Run Refresh Script         │
│  refresh_gmail_mcp_token.py         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Reads: credentials.json             │
│ Location: ai_employee_scripts/      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Deletes old token if exists         │
│ token_gmail.json                    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Generates OAuth Authorization URL   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ User opens URL in browser           │
│ Clicks "Allow" to grant permissions │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ User copies authorization code      │
│ Pastes into terminal                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Script exchanges code for token     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Token saved to:                     │
│ ai_employee_scripts/token_gmail.json│
│                                     │
│ Contains:                           │
│ - access_token (1 hour expiry)      │
│ - refresh_token (long-lived)        │
│ - client_id, client_secret          │
│ - scopes, expiry                    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Step 2: Start Claude Code           │
│ Gmail MCP Server reads token        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Token auto-refreshed when expired   │
│ Using refresh_token                 │
└─────────────────────────────────────┘
```

### Scopes Required

| Scope | Purpose |
|-------|---------|
| `https://www.googleapis.com/auth/gmail.send` | Send emails |
| `https://www.googleapis.com/auth/gmail.modify` | Create drafts, manage labels |

---

## Usage Examples

### In Agent Skills

#### Sending Email (execute-approved skill)

```python
# Send an email reply
result = mcp__gmail__send_email(
    to="client@example.com",
    subject="Re: Project Update",
    body="Thank you for your email. I'll review and get back to you shortly."
)
```

#### Sending CEO Briefing (weekly-audit skill)

```python
# Email the weekly briefing
mcp__gmail__send_email(
    to="your-email@example.com",
    subject="CEO Briefing - Week of 2026-02-23",
    body=briefing_content
)
```

#### Creating Draft

```python
# Create a draft email
mcp__gmail__draft_email(
    to="prospect@example.com",
    subject="AI Employee Services",
    body="Hi, I'd like to discuss how our AI Employee can help your business..."
)
```

#### Searching Emails

```python
# Search for emails from a specific sender
results = mcp__gmail__search_emails(
    query="from:john@example.com",
    max_results=10
)

# Search for unread emails
results = mcp__gmail__search_emails(
    query="is:unread",
    max_results=20
)
```

---

## Files and Paths

| File | Location | Purpose |
|------|----------|---------|
| Refresh Script | `ai_employee_scripts/refresh_gmail_mcp_token.py` | **Primary: Creates/refreshes token** |
| MCP Server | `ai_employee_scripts/mcp_servers/gmail_mcp.py` | Main MCP server code |
| Credentials | `ai_employee_scripts/credentials.json` | OAuth client credentials |
| Token | `ai_employee_scripts/token_gmail.json` | OAuth access/refresh token |
| MCP Config | `AI_Employee_Vault/.mcp.json` | MCP server configuration |

**Workflow:** Refresh Script → Creates Token → MCP Server Reads Token

---

## Troubleshooting

### Issue: "credentials.json not found"

**Error Message:**
```
ERROR: credentials.json not found. Please download from Google Cloud Console.
```

**Solution:**
1. Download credentials from Google Cloud Console (see Setup Guide)
2. Place file at `ai_employee_scripts/credentials.json`

---

### Issue: "Refresh failed"

**Error Message:**
```
WARNING: Refresh failed: ... Will run full OAuth flow.
```

**Solution:**
1. Run the refresh script:
   ```bash
   cd ai_employee_scripts
   uv run python refresh_gmail_mcp_token.py
   ```
2. Follow the OAuth flow in the terminal
3. Old token will be replaced with fresh one

---

### Issue: "Invalid authorization code"

**Error Message:**
```
ERROR: Invalid authorization code
```

**Solution:**
1. The authorization code expires after a few minutes
2. Get a fresh code from the authorization URL
3. Copy the **entire** code (it's quite long)
4. Paste it into the terminal

---

### Issue: Token expires frequently

**Cause:** OAuth access tokens expire after 1 hour (by design)

**Solution:**
- The MCP server auto-refreshes using the refresh token
- Ensure `refresh_token` is present in `token_gmail.json`
- If refresh token is missing, run the refresh script again with `access_type=offline`

---

### Issue: 401 Unauthorized

**Error Message:**
```
Error sending email: <HttpError 401 ...>
```

**Solution:**
1. Token has expired or been revoked
2. Run refresh script to get new token
3. Check that Gmail API is enabled in Google Cloud Console

---

### Issue: 403 Forbidden

**Error Message:**
```
Error sending email: <HttpError 403 ...>
```

**Solution:**
1. Check that correct scopes are authorized
2. Verify OAuth consent screen has the required scopes
3. Re-run OAuth flow if scopes were added later

---

### Issue: WSL Browser Not Opening

**Symptom:** OAuth flow prints URL but browser doesn't open

**Solution:**
- The MCP server uses **console mode** (`urn:ietf:wg:oauth:2.0:oob`)
- Manually copy the URL and open in browser on Windows host
- Paste the authorization code back into WSL terminal

---

## Token Creation and Refresh

### Creating Token (First Time)

Use the refresh script - same script for both creation and refresh:

```bash
cd ai_employee_scripts
uv run python refresh_gmail_mcp_token.py
```

**What the script does:**
1. Checks for `credentials.json`
2. Deletes old `token_gmail.json` if exists
3. Generates OAuth URL
4. Exchanges authorization code for token
5. Saves new token with `access_type=offline` (gets refresh token)

### Refreshing Token

**Automatic:** The MCP server auto-refreshes using `refresh_token` when `access_token` expires (1 hour).

**Manual refresh** (if needed):
```bash
cd ai_employee_scripts
uv run python refresh_gmail_mcp_token.py
```

### When to Manually Refresh

- Token was revoked in Google Account settings
- Authentication errors occur repeatedly
- You want to ensure a fresh `refresh_token`

**Refresh Script Output:**
```
============================================================
GMAIL MCP SERVER - TOKEN REFRESH
============================================================

Token file: /path/to/token_gmail.json
Credentials: /path/to/credentials.json

Removing old expired token: /path/to/token_gmail.json

============================================================
STEP 1: Authorize the Application
============================================================

1. Copy this URL and open it in your browser:

   https://accounts.google.com/o/oauth2/v2/auth?...

2. Click 'Allow' to grant permissions
3. Copy the authorization code shown

============================================================

Paste authorization code here: [paste code here]

Exchanging code for token...

============================================================
SUCCESS! Token Saved
============================================================

Token file: /path/to/token_gmail.json
Expires: 2026-04-30 12:34:56
Has refresh token: True

Your Gmail MCP server should now work!
Restart Claude Code to apply changes.
============================================================
```

---

## Skills Using Gmail MCP

| Skill | Usage | Description |
|-------|-------|-------------|
| `execute-approved` | `send_email` | Sends approved email replies |
| `weekly-audit` | `send_email` | Emails CEO briefing to user |

---

## Dependencies

```
google-api-python-client>=2.189.0
google-auth-oauthlib>=1.2.4
mcp>=0.1.0
```

Install via:
```bash
cd ai_employee_scripts
uv sync
```

---

## Security Notes

1. **Never commit** `credentials.json` or `token_gmail.json` to git
2. **Never share** your authorization codes or refresh tokens
3. **Revoke access** in Google Account settings if credentials are compromised
4. **Token storage:** Files are stored locally and never transmitted except to Google APIs

---

## Related Documentation

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [Weekly Audit Skill](../../.claude/skills/weekly-audit/SKILL.md)
- [Execute Approved Skill](../../.claude/skills/execute-approved/SKILL.md)

---

*Generated: 2026-02-28*
*AI Employee Project - Gold Tier Documentation*
