# LinkedIn Watcher Documentation

## Overview

The LinkedIn Watcher monitors LinkedIn for unread messages using browser automation (Playwright). It stores full message content in `Inbox/` and creates reference tasks in `Needs_Action/` with suggested response templates.

**Location:** `ai_employee_scripts/watchers/linkedin_watcher.py`

**Inheritance:** Inherits from `BaseWatcher`

---

## Features

### What It Does

| Action | Description |
|--------|-------------|
| Monitors | Polls LinkedIn messaging every 5 minutes |
| Detects | Unread messages only |
| Stores | Full message in `Inbox/` |
| Creates | Task in `Needs_Action/` with response templates |
| Persists | Session and state across restarts |

### Session Management

| Feature | Description |
|---------|-------------|
| First Run | Opens browser for manual login |
| Subsequent Runs | Uses saved session (headless) |
| Session Path | `ai_employee_scripts/sessions/linkedin/` |
| State File | `Logs/linkedin_state.json` |
| Login Check | Every 3 seconds for up to 2 minutes |
| Message Limit | 10 unread messages per check |

---

## Architecture

### Polling Flow

```
┌─────────────────────────────────────┐
│  1. Load Previous State             │
│  - Load seen message IDs            │
│  - Load seen request IDs            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. Check Session Status            │
│  - First run? (no session files)    │
│  - If first run: open visible       │
│  - If existing: use headless        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. Navigate to LinkedIn            │
│  - Go to messaging page             │
│  - First run: wait for login        │
│  - Check for security verification  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  4. Scan for Unread Messages        │
│  - Filter by unread                 │
│  - Extract sender and preview       │
│  - Generate message ID              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  5. Process New Messages            │
│  - Filter against seen_messages     │
│  - Store in Inbox/                  │
│  - Create task in Needs_Action/     │
│  - Save state                       │
└─────────────────────────────────────┘
```

---

## Setup Guide

### Prerequisites

1. **Python 3.13+** with UV package manager
2. **LinkedIn Account**
3. **Playwright** browsers installed
4. **X Server** (for WSL: WSLg, X410, or similar)

### Step 1: Install Dependencies

```bash
cd ai_employee_scripts
uv sync
```

Required packages:
- `playwright>=1.58.0`
- `playwright-stealth>=2.0.2`

### Step 2: Install Playwright Browsers

```bash
cd ai_employee_scripts
uv run playwright install chromium
```

**Or for all browsers:**
```bash
uv run playwright install
```

### Step 3: First Run - Manual Login

```bash
cd ai_employee_scripts
python watchers/linkedin_watcher.py
```

**First Run Flow:**

1. Watcher checks for existing session files
2. Chromium browser opens (visible, not headless)
3. Navigate to LinkedIn messaging page
4. **You must log in manually** in the browser window
5. Watcher checks URL **every 3 seconds** for up to **2 minutes**:
   - Checks for `'login'` in URL (not logged in)
   - Checks for `'messaging'` in URL (logged in)
   - Checks for `'checkpoint'` or `'challenge'` (security verification)
6. Once logged in detected, session saved
7. Browser closes
8. Watcher starts polling

**Expected Output:**
```
LinkedIn Watcher starting... Press Ctrl+C to stop.
2026-02-28 12:34:56 - LinkedInWatcher - INFO - Starting LinkedInWatcher...
2026-02-28 12:34:56 - LinkedInWatcher - INFO - Session path: /path/to/sessions/linkedin
2026-02-28 12:34:56 - LinkedInWatcher - INFO - First run: True
==================================================
FIRST RUN - MANUAL LOGIN REQUIRED
==================================================
1. A browser window has opened
2. Log in to LinkedIn in that window
3. Wait for this script to detect login (up to 2 minutes)
==================================================
```

### Step 4: Verify Session

Once logged in, subsequent runs will be headless:

```
2026-02-28 12:34:56 - LinkedInWatcher - INFO - First run: False
2026-02-28 12:34:56 - LinkedInWatcher - INFO - Creating browser context (headless=True)...
2026-02-28 12:34:58 - LinkedInWatcher - INFO - ✓ Login detected! Session saved.
```

---

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DISPLAY` | X server display (WSL) | No (uses `:0` by default) |

### Check Interval

Default: 300 seconds (5 minutes)

To change, edit `linkedin_watcher.py`:

```python
def main():
    watcher = LinkedInWatcher(
        vault_path=str(vault_path),
        check_interval=120  # Change to 2 minutes
    )
```

### Session Path

Default: `ai_employee_scripts/sessions/linkedin/`

Customizable via constructor:

```python
watcher = LinkedInWatcher(
    vault_path=str(vault_path),
    session_path='/custom/path/to/session',
    check_interval=300
)
```

---

## Authentication

### Session-Based Authentication

```
┌─────────────────────────────────────┐
│  1. First Run - No Session          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. Open Visible Browser            │
│  - headless=False                   │
│  - Navigate to LinkedIn             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. Manual Login Required           │
│  - User logs in                     │
│  - May face 2FA or checkpoint       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  4. Detect Login                    │
│  - Check URL for 'login' string     │
│  - Verify messaging page loaded     │
│  - Wait up to 2 minutes             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  5. Session Saved                   │
│  - Cookies saved                    │
│  - Browser closes                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  6. Subsequent Runs                 │
│  - Load session from disk           │
│  - Run headless                     │
│  - No manual login needed           │
└─────────────────────────────────────┘
```

### Session Storage

**Location:** `ai_employee_scripts/sessions/linkedin/`

**Structure:**
```
sessions/linkedin/
└── Default/
    ├── Cookies          # Session cookies
    ├── Preferences      # Browser preferences
    └── ...             # Other session data
```

**Isolation:** Separate from `linkedin_mcp` session for independent operation.

---

## File Processing

### Inbox File Format

`Inbox/LINKEDIN_MESSAGE_[timestamp].md`

**Timestamp Format:** Uses **microseconds** for unique filenames when processing multiple items:
```
LINKEDIN_MESSAGE_20260228_123456_123456.md  (YYYYMMDD_HHMMSS_microseconds)
```

```markdown
---
type: linkedin
source: linkedin
activity_type: message
from: John Doe
created: 2026-02-28T12:34:56
---

# LinkedIn Message from John Doe

## Activity Details
- **Type:** Message
- **From:** John Doe
- **Message ID:** 123456789

## Content/Message
Hi! I saw your profile and wanted to connect...

---
*This file was automatically generated by LinkedIn Watcher.*
```

### State Persistence Methods

| Method | Purpose |
|--------|---------|
| `_load_state()` | Loads previously seen message/request IDs from state file |
| `_save_state()` | Saves current seen items to state file (called after each batch) |
| `_get_item_id(item)` | Returns unique identifier: `{type}_{id}` |

### Message ID Generation

**Important:** LinkedIn Watcher uses **hash-based IDs** because LinkedIn doesn't expose stable message IDs in the UI:

```python
msg_id = str(hash(text))  # Hash of message preview text
```

**Note:** This means the same message content could generate the same ID. The watcher relies on `seen_messages` set to prevent duplicates.

### Task File Format

`Needs_Action/LINKEDIN_MESSAGE_[timestamp].md`

```markdown
---
type: linkedin
source: linkedin
activity_type: message
from: John Doe
priority: high
status: pending
inbox_ref: LINKEDIN_MESSAGE_20260228_123456.md
created: 2026-02-28T12:34:56
---

# LinkedIn Message from John Doe

## Activity Details
- **Type:** Message
- **From:** John Doe
- **Priority:** high

## Content/Message
Hi! I saw your profile and wanted to connect...

## Suggested Actions
- [ ] Review the message
- [ ] Respond if needed
- [ ] Update CRM or notes

## Quick Response Ideas
- [ ] "Thanks for reaching out! I'd be happy to..."
- [ ] "Let me check and get back to you by..."
```

### Response Templates by Type

| Type | Templates |
|------|-----------|
| **message** | "Thanks for reaching out!", "Let me check and get back to you..." |
| **connection_request** | "Thank you for connecting!", "Great to connect! How did you find..." |
| **comment** | "Thanks for commenting!", "Great point! I appreciate..." |

---

## Usage Examples

### Basic Usage

```python
from pathlib import Path
from watchers.linkedin_watcher import LinkedInWatcher

vault_path = Path(__file__).parent / 'AI_Employee_Vault'

watcher = LinkedInWatcher(
    vault_path=str(vault_path),
    check_interval=300  # 5 minutes
)

watcher.run()
```

### Custom Session Path

```python
watcher = LinkedInWatcher(
    vault_path=str(vault_path),
    session_path='/custom/path/sessions/linkedin',
    check_interval=300
)
```

---

## Files and Paths

| File/Folder | Location | Purpose |
|-------------|----------|---------|
| Watcher Script | `ai_employee_scripts/watchers/linkedin_watcher.py` | Main watcher code |
| Session Storage | `ai_employee_scripts/sessions/linkedin/` | Persistent browser session |
| State File | `AI_Employee_Vault/Logs/linkedin_state.json` | Seen message IDs (persisted across restarts) |
| Inbox | `AI_Employee_Vault/Inbox/` | Full message storage |
| Tasks | `AI_Employee_Vault/Needs_Action/` | Message task files |

**State File Structure:**
```json
{
  "messages": ["hash1", "hash2", ...],
  "requests": ["hash1", "hash2", ...],
  "last_updated": "2026-02-28T12:34:56"
}
```

---

## Troubleshooting

### Issue: "Login timeout"

**Error Message:**
```
2026-02-28 12:34:56 - LinkedInWatcher - WARNING - Login timeout - will try again on next run
```

**Cause:** Login didn't complete within 2 minutes

**Solution:**
1. Delete session folder: `rm -rf sessions/linkedin/`
2. Restart watcher
3. Complete login faster when browser opens

---

### Issue: "Security verification detected"

**Message:**
```
2026-02-28 12:34:56 - LinkedInWatcher - INFO - Security verification detected, waiting...
```

**Cause:** LinkedIn requires additional verification

**Solution:**
1. Complete verification in browser
2. Wait for watcher to detect login
3. Session will be saved after verification

---

### Issue: Playwright Browsers Not Installed

**Error Message:**
```
Executable doesn't exist at /path/to/chromium
```

**Solution:**
```bash
cd ai_employee_scripts
uv run playwright install chromium
```

---

### Issue: "No Display" (WSL)

**Error Message:**
```
WebDriver error: cannot find display
```

**Solution:**
1. Install WSLg or X410 for WSL
2. Or use Xvfb for headless display:
   ```bash
   sudo apt install xvfb
   Xvfb :99 -screen 0 1024x768x24 &
   export DISPLAY=:99
   ```

---

### Issue: Session Expired

**Message:**
```
2026-02-28 12:34:56 - LinkedInWatcher - WARNING - Session expired or invalid
```

**Solution:**
1. Delete expired session: `rm -rf sessions/linkedin/`
2. Restart watcher
3. Log in again when browser opens

---

## Running as Background Service

### Using nohup

```bash
cd ai_employee_scripts
nohup python watchers/linkedin_watcher.py > /dev/null 2>&1 &
```

### Checking Status

```bash
ps aux | grep linkedin_watcher | grep -v grep
```

### Stopping

```bash
pkill -f linkedin_watcher
```

---

## Skills Using LinkedIn Watcher

| Skill | Usage | Description |
|-------|-------|-------------|
| `check-watchers` | Check status | Shows if LinkedIn Watcher is running |
| `process-file` | Process messages | Handles LinkedIn message tasks |
| `stop-watcher` | Stop watcher | Stops LinkedIn Watcher |

---

## Dependencies

```
playwright>=1.58.0
playwright-stealth>=2.0.2
```

Install via:
```bash
cd ai_employee_scripts
uv sync
uv run playwright install chromium
```

---

## Security Notes

1. **Session Storage:** Sessions contain login cookies - keep `sessions/` folder secure
2. **Never commit** `sessions/` folder to git (already in .gitignore)
3. **Session Isolation:** Watcher uses separate session from linkedin_mcp
4. **Manual Login:** First login requires manual authentication in browser

---

## Related Documentation

- [Base Watcher](base-watcher.md) - Abstract base class
- [LinkedIn Session Saver](linkedin-session-saver.md) - Alternative session setup
- [LinkedIn MCP](../mcp/linkedin-mcp.md) - LinkedIn API for messaging
- [LinkedIn API MCP](../mcp/linkedin-api-mcp.md) - Official API for posting

---

*Generated: 2026-02-28*
*AI Employee Project - Gold Tier Documentation*
