# Gmail Watcher Documentation

## Overview

The Gmail Watcher monitors Gmail for recent emails (last 24 hours) and creates task files in `Needs_Action/`. It stores full email content in `Inbox/` and creates reference tasks with previews in `Needs_Action/`.

**Location:** `ai_employee_scripts/watchers/gmail_watcher.py`

**Inheritance:** Inherits from `BaseWatcher`

---

## Features

### What It Does

| Action | Description |
|--------|-------------|
| Monitors | Polls Gmail every 2 minutes for new emails |
| Stores | Full email in `Inbox/EMAIL_[message_id].md` |
| Creates | Task in `Needs_Action/` with preview |
| Detects | Priority based on sender/subject keywords |
| Tracks | Processed message IDs to avoid duplicates |

### Email Priority Detection

| Priority | Keywords (Subject) | Description |
|----------|-------------------|-------------|
| **high** | urgent, asap, emergency, important, deadline | Immediate attention |
| **medium** | invoice, payment, meeting, proposal | Business-critical |
| **low** | Everything else | Standard processing |

---

## Architecture

### Polling Flow

```
┌─────────────────────────────────────┐
│  1. Authenticate with Gmail API     │
│  - Load or create OAuth token       │
│  - Build Gmail service              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. Query Recent Emails             │
│  - Last 24 hours                    │
│  - Exclude sent emails              │
│  - Max 20 results                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. Filter New Messages             │
│  - Check against processed_ids set  │
│  - Return only unseen messages      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  4. Process Each New Email          │
│  - Get full message details         │
│  - Extract headers and body         │
│  - Store in Inbox/                  │
│  - Create task in Needs_Action/     │
│  - Mark as processed                │
└─────────────────────────────────────┘
```

---

## Setup Guide

### Prerequisites

1. **Python 3.13+** with UV package manager
2. **Google Cloud Project** with Gmail API enabled
3. **OAuth 2.0 Credentials** (credentials.json)

### Step 1: Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Navigate to **APIs & Services** → **Library**
4. Search for **Gmail API** and click **Enable**

### Step 2: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: `Gmail Watcher` (or any name)
5. Click **Create**

### Step 3: Download credentials.json

1. After creating OAuth client, click **Download JSON**
2. Save as `credentials.json` in `ai_employee_scripts/`

**File Location:**
```
ai_employee_scripts/credentials.json
```

### Step 4: Install Dependencies

```bash
cd ai_employee_scripts
uv sync
```

Required packages:
- `google-api-python-client`
- `google-auth-oauthlib`
- `google-auth`

### Step 5: Run the Watcher (First Run)

```bash
cd ai_employee_scripts
python watchers/gmail_watcher.py
```

**First Run Flow:**

1. Watcher checks for `token_gmail_watcher.json`
2. If not found, browser opens for OAuth consent
3. Click **Allow** to grant Gmail access
4. Token saved automatically
5. Watcher starts polling

**Expected Output:**
```
Gmail Watcher starting... Press Ctrl+C to stop.
2026-02-28 12:34:56 - GmailWatcher - INFO - Starting GmailWatcher...
2026-02-28 12:34:56 - GmailWatcher - INFO - Vault path: /path/to/AI_Employee_Vault
2026-02-28 12:34:56 - GmailWatcher - INFO - Check interval: 120s
2026-02-28 12:34:57 - GmailWatcher - INFO - Gmail authentication successful
```

---

## Configuration

### Environment Variables

No environment variables required. Watcher uses file-based credentials:

| File | Purpose | Location |
|------|---------|----------|
| `credentials.json` | OAuth client credentials | `ai_employee_scripts/` |
| `token_gmail_watcher.json` | OAuth access token (auto-created) | `ai_employee_scripts/` |

### Check Interval

Default: 120 seconds (2 minutes)

To change, edit `gmail_watcher.py`:

```python
def main():
    watcher = GmailWatcher(
        vault_path=str(vault_path),
        check_interval=60  # Change to 1 minute
    )
```

### Gmail API Scopes

```python
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]
```

---

## Authentication

### OAuth 2.0 Flow

```
┌─────────────────────────────────────┐
│  1. First Run - No Token Found      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. Open Browser for OAuth          │
│  - localhost:8080 callback          │
│  - Show Google consent screen       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. User Clicks "Allow"             │
│  - Grant Gmail API permissions      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  4. Token Saved to File             │
│  - token_gmail_watcher.json         │
│  - Includes refresh_token           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  5. Subsequent Runs                 │
│  - Load token from file             │
│  - Auto-refresh if expired          │
│  - No manual login needed           │
└─────────────────────────────────────┘
```

### Token Files

| Token File | Purpose | Used By |
|------------|---------|---------|
| `token_gmail_watcher.json` | Watcher token | Gmail Watcher only |
| `token_gmail.json` | MCP token | Gmail MCP only |

**Important:** The watcher uses its OWN token file (`token_gmail_watcher.json`) to avoid conflicts with the Gmail MCP.

**Important:** The watcher uses its OWN token file (`token_gmail_watcher.json`) to avoid conflicts with the Gmail MCP.

---

## File Processing

### Inbox File Format

`Inbox/EMAIL_[message_id].md`

```markdown
---
type: email
source: gmail
message_id: 1234567890abcdef
from: Sender Name <sender@example.com>
to: recipient@example.com
cc: cc@example.com
subject: Email Subject
received: Fri, 28 Feb 2026 12:34:56 +0000
---

# Email Subject

**From:** Sender Name <sender@example.com>
**To:** recipient@example.com
**Cc:** cc@example.com
**Date:** Fri, 28 Feb 2026 12:34:56 +0000
**Message ID:** 1234567890abcdef

---

## Email Body

[Full email body text or HTML]
```

### Task File Format

`Needs_Action/EMAIL_[subject]_[timestamp].md`

```markdown
---
type: email
source: gmail
message_id: 1234567890abcdef
from: Sender Name <sender@example.com>
subject: Email Subject
received: Fri, 28 Feb 2026 12:34:56 +0000
priority: high
status: pending
inbox_ref: EMAIL_1234567890abcdef.md
created: 2026-02-28T12:34:56
---

# Email from Sender Name <sender@example.com>

## Subject
Email Subject

## Details
- **From:** Sender Name <sender@example.com>
- **Received:** Fri, 28 Feb 2026 12:34:56 +0000
- **Priority:** high
- **Full Email:** `../Inbox/EMAIL_1234567890abcdef.md`

## Preview
[First 500 characters of email body]...

## Suggested Actions
- [ ] Read full email in `Inbox/EMAIL_1234567890abcdef.md`
- [ ] Determine if action needed
- [ ] Respond or archive

## Quick Reply Ideas
- [ ] "Thank you for reaching out..."
- [ ] "I'll review and get back to you..."
- [ ] Forward to relevant person
```

---

## Usage Examples

### Basic Usage

```python
from pathlib import Path
from watchers.gmail_watcher import GmailWatcher

vault_path = Path(__file__).parent / 'AI_Employee_Vault'

watcher = GmailWatcher(
    vault_path=str(vault_path),
    check_interval=120  # 2 minutes
)

watcher.run()
```

### Mark as Read

```python
# Mark an email as read in Gmail
watcher.mark_as_read(message_id='1234567890abcdef')
```

### State Persistence

**Important:** The `processed_ids` set is stored **in memory only** and resets on watcher restart. This means:
- After restart, the same emails won't be reprocessed (Gmail query filters them out)
- But if an email arrives during downtime, it will be detected on next run
- The 24-hour window (`newer_than:1d`) prevents duplicates across restarts

---

## Files and Paths

| File/Folder | Location | Purpose |
|-------------|----------|---------|
| Watcher Script | `ai_employee_scripts/watchers/gmail_watcher.py` | Main watcher code |
| Credentials | `ai_employee_scripts/credentials.json` | OAuth client credentials |
| Token | `ai_employee_scripts/token_gmail_watcher.json` | OAuth access token (auto-created) |
| Inbox | `AI_Employee_Vault/Inbox/` | Full email storage |
| Tasks | `AI_Employee_Vault/Needs_Action/` | Email task files |
| State | In-memory (`processed_ids` set) | Processed message IDs (reset on restart) |

**Credentials Search Paths:** The watcher searches these locations for `credentials.json`:
1. `ai_employee_scripts/credentials.json`
2. Project root `credentials.json` (parent of ai_employee_scripts)

---

## Troubleshooting

### Issue: "credentials.json not found"

**Error Message:**
```
FileNotFoundError: credentials.json not found
```

**Solution:**
1. Download OAuth credentials from Google Cloud Console
2. Save as `ai_employee_scripts/credentials.json`

---

### Issue: Token Expired

**Error Message:**
```
google.auth.exceptions.RefreshError: Watcher token expired. Re-authenticating...
```

**Solution:**
1. Delete `token_gmail_watcher.json`
2. Restart watcher
3. Re-authenticate in browser

---

### Issue: "Quota exceeded"

**Error Message:**
```
googleapiclient.errors.HttpError: 429 Quota exceeded
```

**Solution:**
- Gmail API has usage quotas
- Wait before retrying
- Consider increasing `check_interval`

---

### Issue: No New Emails Detected

**Possible Causes:**
1. Query filters out emails (`newer_than:1d -in:sent`)
2. Emails already processed (in `processed_ids` set)
3. No new emails in last 24 hours

**Solution:**
- Check watcher logs for activity
- Verify Gmail inbox has recent emails

---

## Running as Background Service

### Using nohup

```bash
cd ai_employee_scripts
nohup python watchers/gmail_watcher.py > /dev/null 2>&1 &
```

### Checking Status

```bash
ps aux | grep gmail_watcher | grep -v grep
```

### Stopping

```bash
pkill -f gmail_watcher
```

---

## Skills Using Gmail Watcher

| Skill | Usage | Description |
|-------|-------|-------------|
| `check-watchers` | Check status | Shows if Gmail Watcher is running |
| `process-file` | Process emails | Handles email tasks from Needs_Action |
| `stop-watcher` | Stop watcher | Stops Gmail Watcher |

---

## Dependencies

```
google-api-python-client>=2.0.0
google-auth-oauthlib>=1.0.0
google-auth>=2.0.0
```

Install via:
```bash
cd ai_employee_scripts
uv sync
```

---

## Security Notes

1. **Never commit** `credentials.json` or `token_gmail_watcher.json` to git
2. **Credentials** are stored locally only
3. **OAuth tokens** include refresh_token for automatic renewal
4. **Scopes** are limited to Gmail operations

---

## Related Documentation

- [Base Watcher](base-watcher.md) - Abstract base class
- [Gmail MCP](../mcp/gmail-mcp.md) - Gmail API for sending/replying
- [File System Watcher](filesystem-watcher.md) - File monitoring

---

## API Reference

### Gmail Query Syntax

Watcher uses this query:
```python
q='newer_than:1d -in:sent'
```

| Query Part | Meaning |
|------------|---------|
| `newer_than:1d` | Last 24 hours |
| `-in:sent` | Exclude sent emails |

Other useful operators:
- `from:sender@example.com` - From specific sender
- `subject:invoice` - Subject contains "invoice"
- `is:unread` - Only unread emails
- `has:attachment` - Emails with attachments

---

*Generated: 2026-02-28*
*AI Employee Project - Gold Tier Documentation*
