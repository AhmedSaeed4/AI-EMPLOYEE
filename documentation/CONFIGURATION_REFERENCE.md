# Configuration Reference

This guide covers all configuration files and environment variables for the AI Employee.

---

## Configuration Files Overview

| File | Purpose | Location |
|------|---------|----------|
| `.claude/settings.local.json` | Claude Code settings | Project root |
| `AI_Employee_Vault/.mcp.json` | MCP server configuration | Vault |
| `ai_employee_scripts/pyproject.toml` | Python dependencies | Scripts |
| `ai_employee_scripts/.env` | Environment variables | Scripts |
| `ecosystem.local.config.js` | PM2 config (local) | Scripts |
| `ecosystem.cloud.config.js` | PM2 config (cloud) | Scripts |
| `.gitignore` | Git ignore patterns | Project root |

---

## Claude Code Settings

**File:** `.claude/settings.local.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "ExitPlanMode",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/ralph_wiggum.py"
          }
        ]
      }
    ]
  }
}
```

### Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `ralph_wiggum.py` | Exit attempt | Block exit if tasks pending in Needs_Action |

---

## MCP Server Configuration

**File:** `AI_Employee_Vault/.mcp.json`

```json
{
  "mcpServers": {
    "gmail": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/ai_employee_scripts",
        "run",
        "mcp_servers/gmail_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/ai_employee_scripts"
      }
    },
    "linkedin_api": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/ai_employee_scripts",
        "run",
        "mcp_servers/linkedin_api_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/ai_employee_scripts"
      }
    },
    "linkedin": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/ai_employee_scripts",
        "run",
        "mcp_servers/linkedin_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/ai_employee_scripts",
        "LINKEDIN_MCP_SESSION": "/path/to/sessions/linkedin_mcp"
      }
    },
    "meta-api": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/ai_employee_scripts",
        "run",
        "mcp_servers/meta_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/ai_employee_scripts"
      }
    },
    "twitter-api": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/ai_employee_scripts",
        "run",
        "mcp_servers/twitter_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/ai_employee_scripts"
      }
    },
    "odoo": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/ai_employee_scripts",
        "run",
        "mcp_servers/odoo_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/ai_employee_scripts"
      }
    }
  }
}
```

### MCP Servers

| Server | Purpose | Tools |
|--------|---------|-------|
| `gmail` | Email operations | `send_email`, `draft_email`, `search_emails`, `get_thread` |
| `linkedin_api` | LinkedIn posting | `post_to_linkedin`, `get_linkedin_profile` |
| `linkedin` | LinkedIn messaging | `reply_to_message`, `get_messages`, `validate_session` |
| `meta-api` | Facebook/Instagram | `post_to_facebook`, `post_to_instagram`, `post_to_both` |
| `twitter-api` | Twitter posting | `post_tweet`, `post_business_update`, `get_twitter_profile` |
| `odoo` | Accounting | `get_revenue`, `get_expenses`, `create_draft_invoice`, `post_invoice` |

---

## Environment Variables

**File:** `ai_employee_scripts/.env`

### Gmail

```bash
# OAuth credentials (alternative to credentials.json file)
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret
```

### LinkedIn

```bash
# LinkedIn API (for posting)
LINKEDIN_ACCESS_TOKEN=your-access-token
LINKEDIN_CLIENT_ID=your-client-id
LINKEDIN_CLIENT_SECRET=your-client-secret

# LinkedIn Session (for messaging via Playwright)
LINKEDIN_MCP_SESSION=/path/to/sessions/linkedin_mcp
```

### Meta (Facebook & Instagram)

```bash
# Page Access Token (long-lived)
META_ACCESS_TOKEN=your-page-access-token

# Facebook Page ID
META_PAGE_ID=your-page-id

# Instagram Business Account ID (optional, auto-detected)
INSTAGRAM_BUSINESS_ID=your-instagram-business-id
```

### Twitter/X

```bash
# OAuth 1.0a credentials
X_API_KEY=your-api-key
X_API_SECRET=your-api-secret
X_ACCESS_TOKEN=your-access-token
X_ACCESS_TOKEN_SECRET=your-access-token-secret
```

### Odoo

```bash
# Odoo instance
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=your-email@example.com
ODOO_PASSWORD=your-api-password
```

### OpenAI (Cloud Agents)

```bash
# For cloud agents (optional, for tracing)
OPENAI_API_KEY=your-openai-api-key
```

### Cloud Watchers

```bash
# Gmail credentials as JSON (for cloud watchers)
GOOGLE_CREDENTIALS={"type":"service_account","project_id":"...","private_key":"..."}
```

---

## Python Project Configuration

**File:** `ai_employee_scripts/pyproject.toml`

```toml
[project]
name = "ai_employee_scripts"
version = "0.1.0"
description = "AI Employee automation scripts"
requires-python = ">=3.13"

dependencies = [
    "google-api-python-client>=2.189.0",
    "google-auth-oauthlib>=1.2.4",
    "playwright>=1.58.0",
    "playwright-stealth>=2.0.2",
    "watchdog>=6.0.0",
    "mcp>=0.1.0",
    "httpx>=0.27.0",
    "fastmcp>=0.1.0",
    "odoorpc>=0.10.0",
    "tweepy>=4.16.0",
    "openai-agents>=0.1.0",
]
```

---

## PM2 Configuration

### Local Configuration

**File:** `ai_employee_scripts/ecosystem.local.config.js`

```javascript
module.exports = {
  apps: [{
    name: 'ai-employee-local',
    script: 'watchdog.py',
    interpreter: '/path/to/.venv/bin/python',
    cwd: '/path/to/ai_employee_scripts',
    watch: false,
    autorestart: true,
    max_restarts: 10,
    min_uptime: '10s',
    error_file: './logs/local-err.log',
    out_file: './logs/local-out.log',
    time: true,
    instances: 1,
    exec_mode: 'fork',
    max_memory_restart: '1G',
    kill_timeout: 5000,
    wait_ready: true,
  }]
};
```

### Cloud Configuration

**File:** `ai_employee_scripts/ecosystem.cloud.config.js`

```javascript
module.exports = {
  apps: [{
    name: 'ai-employee-cloud',
    script: 'cloud/cloud_orchestrator.py',
    interpreter: '/path/to/.venv/bin/python',
    cwd: '/path/to/ai_employee_scripts',
    // ... same options as local
  }]
};
```

---

## Git Configuration

**File:** `.gitignore`

```gitignore
# Credentials - NEVER COMMIT
ai_employee_scripts/credentials.json
ai_employee_scripts/token_*.json
ai_employee_scripts/.env
ai_employee_scripts/.env.*

# Session files
sessions/

# Logs (optional - you may want to sync)
# AI_Employee_Vault/Logs/

# OS
.DS_Store
Thumbs.db

# IDE
.idea/
.vscode/

# Python
__pycache__/
*.pyc
.venv/
*.egg-info/

# Node
node_modules/
```

---

## Cron Configuration

```bash
# Current crontab
crontab -l

# Edit crontab
crontab -e
```

### Scheduled Jobs

| Schedule | Job | Script |
|----------|-----|--------|
| 2:00 AM daily | LinkedIn post | `linkedin_cron_trigger.py` |
| 3:00 AM daily | Meta post | `meta_cron_trigger.py` |
| 4:00 AM daily | Twitter post | `twitter_cron_trigger.py` |
| 6:00 AM Monday | CEO Briefing | `weekly_audit_cron_trigger.py` |
| Every 5 min | Vault sync | `vault_sync.py` |

### Crontab Format

```bash
PATH=/home/adev/.local/bin:/usr/local/bin:/usr/bin:/bin

# Social Posts (Daily)
0 2 * * * cd "/path/to/ai_employee_scripts" && uv run python scripts/linkedin_cron_trigger.py >> /path/to/Logs/cron.log 2>&1
0 3 * * * cd "/path/to/ai_employee_scripts" && uv run python scripts/meta_cron_trigger.py >> /path/to/Logs/cron.log 2>&1
0 4 * * * cd "/path/to/ai_employee_scripts" && uv run python scripts/twitter_cron_trigger.py >> /path/to/Logs/cron.log 2>&1

# CEO Briefing (Monday mornings)
0 6 * * 1 cd "/path/to/ai_employee_scripts" && uv run python scripts/weekly_audit_cron_trigger.py >> /path/to/Logs/cron.log 2>&1

# Vault Sync (every 5 minutes)
*/5 * * * * cd "/path/to/ai_employee_scripts" && uv run python vault_sync.py >> /path/to/Logs/vault_sync.log 2>&1
```

---

## Vault Configuration

### Company_Handbook.md

**Purpose:** AI behavior rules and constraints

**Key sections:**
- Financial rules
- Communication rules
- Social media rules
- WhatsApp rules
- General constraints

### Business_Goals.md

**Purpose:** Business context for content generation

**Key sections:**
- Industries
- Services
- Target audience
- Unique selling points
- Posting topics

---

## Cloud Configuration

### cloud/config/settings.py

```python
# Agent settings
DEFAULT_MODEL = "gpt-4o"
MAX_TOKENS = 4096
TEMPERATURE = 0.7

# MCP settings
ODOO_MCP_PATH = "cloud/mcp_servers/odoo_server.py"

# Guardrail settings
MAX_INPUT_LENGTH = 10000
MAX_OUTPUT_LENGTH = 5000
```

---

## Path Reference

| Component | Default Path |
|-----------|--------------|
| Project Root | `~/ai-employee/` |
| Scripts | `~/ai-employee/ai_employee_scripts/` |
| Vault | `~/ai-employee/AI_Employee_Vault/` |
| Skills | `~/ai-employee/.claude/skills/` |
| Hooks | `~/ai-employee/.claude/hooks/` |
| Cron Scripts | `~/ai-employee/ai_employee_scripts/scripts/` |
| Cron Log | `~/ai-employee/AI_Employee_Vault/Logs/cron.log` |
| MCP Servers (Local) | `~/ai-employee/ai_employee_scripts/mcp_servers/` |
| Cloud Agents | `~/ai-employee/ai_employee_scripts/cloud/` |
| Cloud MCP | `~/ai-employee/ai_employee_scripts/cloud/mcp_servers/` |

---

## Related Documentation

- [Getting Started Guide](GETTING_STARTED.md)
- [PM2 Setup Guide](PM2_SETUP_GUIDE.md)
- [Security & Credentials Guide](SECURITY_CREDENTIALS_GUIDE.md)

---

*Generated: 2026-03-14*
*AI Employee Project - Platinum Tier Documentation*