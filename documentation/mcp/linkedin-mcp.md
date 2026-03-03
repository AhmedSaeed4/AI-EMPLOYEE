# LinkedIn MCP Server Documentation

## Overview

The LinkedIn MCP Server provides LinkedIn messaging functionality via browser automation using Playwright. It enables replying to LinkedIn messages, posting content, and fetching messages through the Model Context Protocol (MCP).

**Location:** `ai_employee_scripts/mcp_servers/linkedin_mcp.py`

**MCP Name:** `linkedin`

**Note:** This is separate from `linkedin-api` MCP which uses the official LinkedIn API for posting.

---

## Features

### Available Tools

| Tool | Description | Async |
|------|-------------|-------|
| `post_content` | Post content to LinkedIn feed | Yes |
| `reply_to_message` | Reply to a LinkedIn message conversation | Yes |
| `get_messages` | Fetch LinkedIn messages/conversations | Yes |
| `validate_session` | Verify LinkedIn connection status | Yes |

### Tool Parameters

#### `post_content`

```python
mcp__linkedin__post_content(
    content: str,              # Post content (supports line breaks, hashtags, mentions)
    visibility: str = "PUBLIC"  # 'PUBLIC' or 'CONNECTIONS'
)
```

**Returns:** Confirmation message with post details and timestamp

**Note:** This tool uses browser automation and may be slower than the API-based posting.

#### `reply_to_message`

```python
mcp__linkedin__reply_to_message(
    conversation_url: str,     # Full conversation URL OR sender name
    message: str,              # Reply message content
    wait_before_send: int = 2  # Seconds to wait before sending
)
```

**URL Example:** `https://www.linkedin.com/messaging/thread/ABC123/`

**Name Search:** Can use sender name (e.g., "John Smith") and it will search and click the conversation.

**Returns:** Confirmation message with conversation details

#### `get_messages`

```python
mcp__linkedin__get_messages(
    filter: str = "all",           # 'all', 'unread', or 'pinned'
    limit: int = 10,                # Maximum messages to return
    include_content: bool = False  # Fetch full message content (slower)
)
```

**Returns:** JSON string with messages array including sender, preview, conversation URL, and unread status

#### `validate_session`

```python
mcp__linkedin__validate_session()
```

**Returns:** JSON with status (`connected`/`disconnected`), session path, and verification time

---

## Setup Guide

### Prerequisites

1. **LinkedIn Account** with messaging access
2. **Python 3.13+** with UV package manager
3. **X Server** (for WSL: WSLg, X410, or similar)
4. **Playwright Browsers** installed

### Step 1: Install Dependencies

```bash
cd ai_employee_scripts
uv sync
```

Required packages:
- `playwright>=1.58.0`
- `playwright-stealth>=2.0.2`
- `mcp>=0.1.0`

### Step 2: Install Playwright Browsers

```bash
cd ai_employee_scripts
uv run playwright install chromium
```

**Or for all browsers:**
```bash
uv run playwright install
```

### Step 3: First Run - Browser Login

The MCP server uses **session persistence** - you only need to log in once.

```bash
cd ai_employee_scripts
uv run python mcp_servers/linkedin_mcp.py
```

**First Run Flow:**

1. Server checks for existing session at `sessions/linkedin_mcp/`
2. If no session found, **Chromium browser opens**
3. Log in to LinkedIn manually
4. Session is automatically saved
5. Browser closes
6. MCP server starts

**Subsequent Runs:**
- Session is loaded automatically
- No manual login required
- Server starts immediately

### Step 4: Verify Session

Once the server is running, check session status:

```python
# In Claude Code or via MCP
mcp__linkedin__validate_session()
```

Expected response:
```json
{
  "status": "connected",
  "session_path": "/path/to/sessions/linkedin_mcp",
  "first_run": false,
  "verified_at": "2026-02-28T12:34:56"
}
```

---

## Configuration

### MCP Server Configuration

The LinkedIn MCP is configured in `AI_Employee_Vault/.mcp.json`:

```json
{
  "mcpServers": {
    "linkedin": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/ai-employee/ai_employee_scripts",
        "run",
        "mcp_servers/linkedin_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/ai-employee/ai_employee_scripts",
        "DISPLAY": ":0"
      }
    }
  }
}
```

**Replace:** `/path/to/ai-employee` with your actual project path

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LINKEDIN_MCP_SESSION` | Custom session path (optional) | No |
| `DISPLAY` | X server display for browser (WSL) | No (uses `:0` by default) |

### Session Storage

**Location:** `ai_employee_scripts/sessions/linkedin_mcp/`

**Structure:**
```
sessions/linkedin_mcp/
└── Default/
    ├── Cookies          # Session cookies
    ├── Preferences      # Browser preferences
    └── ...             # Other session data
```

**Isolation:** Separate from `linkedin_watcher` session for independent operation.

---

## Authentication

### Session-Based Authentication

The LinkedIn MCP uses **browser session persistence** (not OAuth tokens):

```
┌─────────────────────────────────────┐
│  First Run: No Session Found        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Chromium Browser Opens            │
│  (Non-headless for manual login)    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  User Logs In to LinkedIn           │
│  (Email/Password or SSO)            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Login Detected                     │
│  Checks for profile icon, feed, etc │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Session Saved Automatically        │
│  sessions/linkedin_mcp/Default/     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Browser Closes                     │
│  MCP Server Starts                  │
└─────────────────────────────────────┘
```

**Session Reuse:**
- Session persists across server restarts
- Only requires re-login if session expires
- Separate from linkedin_watcher session

---

## Usage Examples

### In Agent Skills

#### Replying to Messages (execute-approved skill)

```python
# Reply to a LinkedIn message
result = mcp__linkedin__reply_to_message(
    conversation_url="https://www.linkedin.com/messaging/thread/ABC123/",
    message="Thanks for reaching out! I'll review your proposal and get back to you by end of day.",
    wait_before_send=2
)
```

**Or using sender name:**
```python
result = mcp__linkedin__reply_to_message(
    conversation_url="John Smith",  # Will search and click conversation
    message="Thanks for your message! Let's schedule a call."
)
```

#### Getting Messages

```python
# Get all messages
import json
result = mcp__linkedin__get_messages(
    filter="all",
    limit=10,
    include_content=False
)
messages = json.loads(result)

# Get only unread messages
unread = mcp__linkedin__get_messages(
    filter="unread",
    limit=20
)
```

#### Posting Content

```python
# Post to LinkedIn feed
result = mcp__linkedin__post_content(
    content="Just shipped a new feature! 🚀 #automation #AI",
    visibility="PUBLIC"
)
```

---

## Files and Paths

| File | Location | Purpose |
|------|----------|---------|
| MCP Server | `ai_employee_scripts/mcp_servers/linkedin_mcp.py` | Main MCP server code |
| Session Storage | `ai_employee_scripts/sessions/linkedin_mcp/` | Persistent browser session |
| Debug Screenshots | `AI_Employee_Vault/Logs/linkedin_*.png` | Screenshots for debugging |
| MCP Config | `AI_Employee_Vault/.mcp.json` | MCP server configuration |

---

## Troubleshooting

### Issue: "Browser not initialized"

**Error Message:**
```
Error: Browser not initialized. Please check the MCP server logs.
```

**Solution:**
1. Check session exists: `ls ai_employee_scripts/sessions/linkedin_mcp/`
2. If session missing, run first-run setup again
3. Ensure DISPLAY variable is set (WSL)

---

### Issue: "Not logged in to LinkedIn"

**Error Message:**
```
Error: Not logged in to LinkedIn. Please run manual login first.
```

**Solution:**
1. Stop the MCP server
2. Delete session folder: `rm -rf sessions/linkedin_mcp/`
3. Restart server - it will open browser for login
4. Log in and wait for "Login detected" message

---

### Issue: "Could not find 'Start a post' button"

**Error Message:**
```
Error: Could not find 'Start a post' button. You might not be logged in.
```

**Solution:**
1. Verify session is valid using `validate_session`
2. LinkedIn UI may have changed - check screenshots in `Logs/` folder
3. Re-login if session expired

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
⚠️ Session expired or invalid. Need to re-login.
```

**Solution:**
1. Delete expired session: `rm -rf sessions/linkedin_mcp/`
2. Restart MCP server
3. Log in again when browser opens

---

## Browser Automation Details

### Human-Like Typing

The server types content with random delays (10-30ms per character) to mimic human behavior and avoid LinkedIn's bot detection.

### Screenshot Debugging

Screenshots are saved to `AI_Employee_Vault/Logs/` for debugging:
- `linkedin_feed_HHMMSS.png` - Feed page screenshot
- `linkedin_modal_HHMMSS.png` - Post composer screenshot

### Multiple Selectors

The tool tries multiple CSS selectors to handle LinkedIn's dynamic class names:
- Fallback selector patterns
- Text-based searching
- ARIA label matching

---

## Skills Using LinkedIn MCP

| Skill | Tool Used | Description |
|-------|-----------|-------------|
| `execute-approved` | `reply_to_message` | Replies to approved LinkedIn messages |
| `process-file` | `reply_to_message` | Auto-replies to LinkedIn messages |

---

## Dependencies

```
playwright>=1.58.0
playwright-stealth>=2.0.2
mcp>=0.1.0
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
3. **Session Isolation:** MCP uses separate session from linkedin_watcher
4. **Manual Login:** First login requires manual authentication in browser
5. **Screenshot Logs:** Debug screenshots may contain sensitive content

---

## Related Documentation

- [Playwright Documentation](https://playwright.dev/python/)
- [Execute Approved Skill](../../.claude/skills/execute-approved/SKILL.md)
- [Process File Skill](../../.claude/skills/process-file/SKILL.md)
- [LinkedIn API MCP](linkedin-api-mcp.md) - Official API for posting

---

## Comparison: linkedin vs linkedin-api MCP

| Feature | `linkedin` | `linkedin-api` |
|---------|-----------|----------------|
| **Method** | Browser automation | Official API |
| **Authentication** | Session-based | OAuth token |
| **Posting** | ✅ Yes | ✅ Yes |
| **Messaging** | ✅ Yes | ❌ No |
| **Reliability** | Medium (UI changes) | High (API) |
| **Speed** | Slow (browser) | Fast (API) |
| **Use Case** | Message replies | Feed posting |

---

*Generated: 2026-02-28*
*AI Employee Project - Gold Tier Documentation*
