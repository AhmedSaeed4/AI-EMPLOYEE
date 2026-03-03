# Personal AI Employee

> *Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.*

**Hackathon:** Personal AI Employee Hackathon 0 - Building Autonomous FTEs in 2026

**Current Tier:** Gold (100% Complete)

---

## Overview

The Personal AI Employee is an autonomous Digital FTE (Full-Time Equivalent) that proactively manages personal and business affairs 24/7. Built with Claude Code, Obsidian, and Python, it serves as a "Smart Consultant" that continuously monitors inputs, reasons about tasks, and executes actions with human oversight.

### Key Features

- **Multi-Platform Social Posting** - LinkedIn, Facebook, Instagram, Twitter/X
- **Email Management** - Gmail integration with drafting and sending
- **Accounting Integration** - Odoo JSON-RPC for invoices, payments, revenue tracking
- **CEO Briefing** - Weekly automated business audit emailed to your inbox
- **Human-in-the-Loop** - All sensitive actions require approval
- **Error Recovery** - Automatic retry, watchdog monitoring, failed action queue

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Automated Scheduling](#automated-scheduling)
- [MCP Servers](#mcp-servers)
- [Agent Skills](#agent-skills)
- [Human-in-the-Loop Workflow](#human-in-the-loop-workflow)
- [Error Recovery & Graceful Degradation](#error-recovery--graceful-degradation)
- [Platform-Specific Notes](#platform-specific-notes)
- [Known Issues](#known-issues)
- [Troubleshooting](#troubleshooting)
- [Dependencies](#dependencies)
- [Tier Progress](#tier-progress)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

### Architecture

```
                    ╔═════════════════════════════════════════════╗
                    ║            ENTRY POINTS                    ║
                    ╠═════════════════════════════════════════════╣
                    ║  1. Cron Jobs (Scheduled Automation)       ║
                    ║  2. Claude Code Skills (Interactive)       ║
                    ║  3. Watchdog.py (Production Monitoring)    ║
                    ╚═════════════════════════════════════════════╝
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
        ╔═══════════════════════╗         ╔═══════════════════════╗
        ║    Cron Triggers      ║         ║     Watchdog.py       ║
        ║  (linkedin/meta/      ║         ║  Monitors & Restarts  ║
        ║   twitter/weekly)     ║         ║   Orchestrator.py     ║
        ╚════════════╤═══════════╝         ╚════════════╤═════════╝
                     │                                 │
                     │    ┌────────────────────────────┘
                     │    │
                     ▼    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator.py                           │
│              (Master Controller - Monitors Folders)          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Needs_Action │  │   Approved   │  │   Rejected   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌─────────────────┐                   ┌─────────────────┐
│  Perception     │                   │   Reasoning     │
│   (Watchers)    │──────────────────▶│   (Claude)      │
│                 │                   │                 │
│ • File System   │    Creates        │ • Process Files │
│ • Gmail         │    Action Files   │ • Create Plans  │
│ • LinkedIn      │                   │ • Generate Posts│
└─────────────────┘                   └────────┬────────┘
                                               │
                                               ▼
                                        ┌──────────────┐
                                        │ Pending_     │
                                        │  Approval    │
                                        └──────┬───────┘
                                               │
                                    ┌──────────┴──────────┐
                                    ▼                     ▼
                              ┌──────────┐          ┌──────────┐
                              │ Human    │          │  Rejected│
                              │ Review   │          └──────────┘
                              └────┬─────┘
                                   │
                                   ▼
                            ┌──────────────┐
                            │   Approved   │
                            └──────┬───────┘
                                   │
                                   ▼
┌─────────────────┐     ┌─────────────────┐
│     Action      │     │    Execution    │
│     (MCPs)      │────▶│   (Orchestrator)│
│                 │     └─────────────────┘
│ • Gmail         │             │
│ • LinkedIn      │             ▼
│ • Meta          │     ┌──────────────┐
│ • Twitter       │     │     Done     │
│ • Odoo          │     └──────────────┘
└─────────────────┘

═══════════════════════════════════════════════════════════════
                    Scheduled Automation (Cron)
═══════════════════════════════════════════════════════════════
  2 AM → LinkedIn Post    3 AM → Meta Post     4 AM → Twitter
                                            │
                                            ▼
                                   6 AM Monday → CEO Briefing
```

---

## Quick Start

### Prerequisites

- **Python** 3.13 or higher
- **Claude Code** (Pro subscription or Free with Gemini API)
- **Obsidian** (for vault/dashboard)
- **UV** (Python package manager)

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd ai-employee

# 2. Install dependencies
cd ai_employee_scripts
uv sync

# 3. Install Playwright browsers
uv run playwright install chromium

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your API credentials

# 5. Configure Claude Code MCP servers
# Edit ~/.config/claude-code/mcp.json or project .claude/settings.local.json
```

### Configuration

Create your `.env` file in `ai_employee_scripts/`:

```bash
# Gmail
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret

# LinkedIn API
LINKEDIN_ACCESS_TOKEN=your_access_token
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret

# LinkedIn Session (for messaging)
LINKEDIN_MCP_SESSION=/path/to/sessions/linkedin_mcp

# Odoo Accounting
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=your-email@example.com
ODOO_PASSWORD=your-odoo-password

# Meta (Facebook & Instagram)
META_ACCESS_TOKEN=your_access_token
META_PAGE_ID=your_page_id

# Twitter (X)
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret
```

---

## Usage

### Generate Social Posts

```bash
# LinkedIn
claude code -p "/linkedin-posting"

# Facebook/Instagram
claude code -p "/meta-posting"

# Twitter/X
claude code -p "/twitter-posting"
```

### Business Operations

```bash
# Check accounting status
claude code -p "/check-accounting"

# Create invoice
claude code -p "/create-invoice"

# Weekly CEO Briefing
claude code -p "/weekly-audit"
```

### Task Management

```bash
# Check pending tasks
claude code -p "/check-tasks"

# Process a task file
claude code -p "/process-file TASK_example.md"

# Execute approved actions
claude code -p "/execute-approved"
```

### Watcher Management

```bash
# Start a watcher
claude code -p "/start-watcher filesystem"

# Check watcher status
claude code -p "/watcher-status"

# Stop watchers
claude code -p "/stop-watcher all"
```

---

## Project Structure

```
ai-employee/
├── .claude/
│   ├── skills/              # Claude Agent Skills (18 total)
│   │   ├── approve-action/
│   │   ├── check-accounting/
│   │   ├── check-tasks/
│   │   ├── check-watchers/
│   │   ├── create-invoice/
│   │   ├── create-plan/
│   │   ├── daily-summary/
│   │   ├── execute-approved/
│   │   ├── linkedin-posting/
│   │   ├── meta-posting/
│   │   ├── process-file/
│   │   ├── start-watcher/
│   │   ├── stop-watcher/
│   │   ├── twitter-posting/
│   │   ├── update-handbook/
│   │   ├── watcher-status/
│   │   ├── weekly-audit/
│   │   ├── post-linkedin/
│   │   └── check-watchers/
│   ├── hooks/
│   │   └── ralph_wiggum.py  # Stop hook - prevents exit with pending tasks
│   └── settings.local.json  # MCP server configuration
│
├── ai_employee_scripts/
│   ├── watchers/            # Perception Layer
│   │   ├── base_watcher.py
│   │   ├── filesystem_watcher.py
│   │   ├── gmail_watcher.py
│   │   └── linkedin_watcher.py
│   │
│   ├── mcp_servers/         # Action Layer (MCP Servers)
│   │   ├── gmail_mcp.py
│   │   ├── linkedin_api_mcp.py
│   │   ├── linkedin_mcp.py
│   │   ├── odoo_mcp.py
│   │   ├── meta_mcp.py
│   │   └── twitter_mcp.py
│   │
│   ├── shared/              # Error Recovery
│   │   ├── error_handler.py
│   │   └── retry_handler.py
│   │
│   ├── scripts/             # Cron Triggers
│   │   ├── linkedin_cron_trigger.py
│   │   ├── meta_cron_trigger.py
│   │   ├── twitter_cron_trigger.py
│   │   └── weekly_audit_cron_trigger.py
│   │
│   ├── orchestrator.py      # Master controller
│   ├── watchdog.py          # Process monitor
│   ├── pyproject.toml       # Python dependencies
│   └── .env                 # Environment variables (not in git)
│
├── AI_Employee_Vault/       # Obsidian Vault (Data)
│   ├── Dashboard.md         # Central status hub
│   ├── Company_Handbook.md  # AI behavior rules
│   ├── Business_Goals.md    # Business context
│   ├── Inbox/               # Raw data from watchers
│   ├── Needs_Action/        # Tasks awaiting processing
│   ├── Done/                # Completed tasks
│   ├── Pending_Approval/    # Actions requiring approval
│   ├── Approved/            # Approved actions
│   ├── Rejected/            # Rejected actions
│   ├── Failed_Queue/        # Failed actions (human review)
│   ├── Plans/               # Complex task plans
│   ├── Logs/                # Activity logs
│   ├── Briefings/           # CEO Briefing reports
│   └── Content_To_Post/     # Social media queue
│
├── README.md                # This file
├── PROJECT_STATUS.md        # Detailed project status
└── CLAUDE.md                # Claude Code instructions
```

---

## Automated Scheduling

The AI Employee includes 4 cron jobs for automated operation:

| Time | Day | Platform | Purpose |
|------|-----|----------|---------|
| 2:00 AM | Daily | LinkedIn | Generate post |
| 3:00 AM | Daily | Facebook/Instagram | Generate post |
| 4:00 AM | Daily | Twitter/X | Generate post |
| 6:00 AM | Monday | All | CEO Briefing |

### Setup Cron Jobs

```bash
# Edit crontab
crontab -e

# Add these lines:
PATH=/home/adev/.local/bin:/usr/local/bin:/usr/bin:/bin

# Social Posts (Daily)
0 2 * * * cd "/path/to/ai-employee/ai_employee_scripts" && uv run python scripts/linkedin_cron_trigger.py >> /path/to/AI_Employee_Vault/Logs/cron.log 2>&1
0 3 * * * cd "/path/to/ai-employee/ai_employee_scripts" && uv run python scripts/meta_cron_trigger.py >> /path/to/AI_Employee_Vault/Logs/cron.log 2>&1
0 4 * * * cd "/path/to/ai-employee/ai_employee_scripts" && uv run python scripts/twitter_cron_trigger.py >> /path/to/AI_Employee_Vault/Logs/cron.log 2>&1

# CEO Briefing (Monday mornings)
0 6 * * 1 cd "/path/to/ai-employee/ai_employee_scripts" && uv run python scripts/weekly_audit_cron_trigger.py >> /path/to/AI_Employee_Vault/Logs/cron.log 2>&1
```

---

## MCP Servers

The project uses 6 MCP servers for external actions:

| Server | Purpose | Tools |
|--------|---------|-------|
| `gmail` | Email operations | send_email, draft_email, search_emails, get_thread |
| `linkedin_api` | LinkedIn posting | post_to_linkedin, get_linkedin_profile |
| `linkedin` | LinkedIn messaging | get_messages, reply_to_message, validate_session |
| `odoo` | Accounting | create_draft_invoice, get_invoices, get_payments, get_revenue, get_expenses |
| `meta-api` | Facebook/Instagram | post_to_facebook, post_to_instagram, post_to_both, get_meta_profile |
| `twitter-api` | Twitter/X | post_tweet, post_business_update, get_twitter_profile |

### MCP Configuration

Add to `~/.config/claude-code/mcp.json` or `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "uv",
      "args": ["run", "python", "mcp_servers/gmail_mcp.py"],
      "cwd": "/path/to/ai-employee/ai_employee_scripts"
    },
    "linkedin_api": {
      "command": "uv",
      "args": ["run", "python", "mcp_servers/linkedin_api_mcp.py"],
      "cwd": "/path/to/ai-employee/ai_employee_scripts"
    },
    "linkedin": {
      "command": "uv",
      "args": ["run", "python", "mcp_servers/linkedin_mcp.py"],
      "cwd": "/path/to/ai-employee/ai_employee_scripts"
    },
    "odoo": {
      "command": "uv",
      "args": ["run", "python", "mcp_servers/odoo_mcp.py"],
      "cwd": "/path/to/ai-employee/ai_employee_scripts"
    },
    "meta-api": {
      "command": "uv",
      "args": ["run", "python", "mcp_servers/meta_mcp.py"],
      "cwd": "/path/to/ai-employee/ai_employee_scripts"
    },
    "twitter-api": {
      "command": "uv",
      "args": ["run", "python", "mcp_servers/twitter_mcp.py"],
      "cwd": "/path/to/ai-employee/ai_employee_scripts"
    }
  }
}
```

---

## Agent Skills

All AI functionality is implemented as Claude Agent Skills:

### Task Management
- `/check-tasks` - List pending tasks
- `/process-file` - Process task from Needs_Action
- `/create-plan` - Generate Plan.md for complex tasks
- `/daily-summary` - Update Dashboard with daily summary

### Business Operations
- `/check-accounting` - Odoo revenue/expenses summary
- `/create-invoice` - Create Odoo draft invoice
- `/weekly-audit` - Generate CEO Briefing with auto-email

### Social Media
- `/linkedin-posting` - Generate LinkedIn posts
- `/meta-posting` - Generate Facebook/Instagram posts
- `/twitter-posting` - Generate Twitter posts
- `/post-linkedin` - Queue LinkedIn posts

### Approval & Execution
- `/approve-action` - Move action to Approved folder
- `/execute-approved` - Execute approved actions via MCP

### Watcher Management
- `/start-watcher` - Start a watcher script
- `/stop-watcher` - Stop watcher(s)
- `/watcher-status` - Check watcher status
- `/check-watchers` - Status of all watchers

### Configuration
- `/update-handbook` - Update Company_Handbook.md

---

## Human-in-the-Loop Workflow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Watcher    │────▶│ Needs_Action │────▶│     AI       │
│  Detects     │     │  (Queue)     │     │  Processes   │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │    Claude    │
                                          │   Creates    │
                                          │    Plans     │
                                          └──────┬───────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │   Pending_   │
                                          │  Approval    │
                                          └──────┬───────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │    Human     │
                                          │   Reviews    │
                                          └──────┬───────┘
                                                 │
                            ┌────────────────────┴────────────────────┐
                            ▼                                         ▼
                     ┌──────────────┐                          ┌──────────────┐
                     │  Approved    │                          │  Rejected    │
                     │              │                          └──────────────┘
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    Orchestr- │
                     │    ator      │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  MCP Server  │
                     │  Executes    │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │     Done     │
                     └──────────────┘
```

---

## Error Recovery & Graceful Degradation

The AI Employee includes comprehensive error handling:

### Error Categories

| Category | Examples | Recovery |
|----------|----------|----------|
| Transient | Network timeout, API rate limit | Exponential backoff retry |
| Authentication | Expired token | Alert human, pause operations |
| Logic | Claude misinterprets | Human review queue |
| Data | Corrupted file | Quarantine + alert |
| System | Orchestrator crash | Watchdog auto-restart |

### Components

- **`error_handler.py`** - Error classification system
- **`retry_handler.py`** - Async/sync retry decorators with exponential backoff
- **`watchdog.py`** - Separate process that monitors and restarts orchestrator
- **`Failed_Queue/`** - Failed actions stored for human review

### Watchdog Process

```bash
# Start watchdog (monitors orchestrator)
cd ai_employee_scripts
uv run python watchdog.py
```

The watchdog will:
- Monitor orchestrator process health
- Auto-restart if crashed (max 5 restarts/hour)
- Alert human if restart limit exceeded

---

## Platform-Specific Notes

### Instagram Posting
- **Image required** - Must provide public image URL
- **Caption limit** - 2200 characters
- **Image size** - 1080x1080px recommended
- **Format** - JPEG or PNG

### Twitter/X Posting
- **Character limit** - 280 characters (strict)
- **API credits** - Required for posting
- **Note:** Implementation is complete; posting requires X API credits

### LinkedIn Posting
- **Character limit** - 3000 characters
- **Hashtags** - Recommended 3-5
- **API** - Official LinkedIn API

---

## Known Issues

| Issue | Workaround |
|-------|------------|
| Twitter API 402 error | Add credits at https://developer.x.com |
| Instagram image selection | Human provides image URL in approval file |
| WSL inotify issues | Watchers use polling instead of inotify |

---

## Troubleshooting

### Watcher not running
```bash
# Check if process exists
ps aux | grep watcher

# Check logs
tail -f AI_Employee_Vault/Logs/cron.log

# Restart watcher
claude code -p "/start-watcher filesystem"
```

### MCP server not connecting
```bash
# Verify MCP server runs manually
cd ai_employee_scripts
uv run python mcp_servers/gmail_mcp.py

# Check Claude Code logs
# View Claude Code settings to verify MCP configuration
```

### Orchestrator crashed
```bash
# Check if watchdog is running (should auto-restart)
ps aux | grep watchdog

# Manual restart
cd ai_employee_scripts
uv run python orchestrator.py
```

### Ralph Wiggum hook blocking exit
```bash
# Create bypass file in vault
touch AI_Employee_Vault/stop_ralph

# Or complete pending tasks
claude code -p "/check-tasks"
```

---

## Dependencies

```
google-api-python-client>=2.189.0
google-auth-httplib2>=0.3.0
google-auth-oauthlib>=1.2.4
playwright>=1.58.0
watchdog>=6.0.0
mcp>=0.1.0
playwright-stealth>=2.0.2
httpx>=0.28.1
odoorpc>=0.10.1
tweepy>=4.16.0
```

Install with:
```bash
cd ai_employee_scripts
uv sync
```

---

## Tier Progress

| Tier | Status | Progress |
|------|--------|----------|
| **Bronze** | ✅ Complete | 100% |
| **Silver** | ✅ Complete | 100% |
| **Gold** | ✅ Complete | 100% |
| **Platinum** | ⏳ Not Started | 0% |

### Gold Tier Checklist

| Requirement | Status |
|-------------|--------|
| Full cross-domain (Personal + Business) | ✅ |
| Odoo accounting integration | ✅ |
| Facebook/Instagram integration | ✅ |
| Twitter (X) integration | ✅ |
| Weekly CEO Briefing | ✅ |
| Error recovery / graceful degradation | ✅ |
| Ralph Wiggum loop | ✅ |
| Comprehensive audit logging | ✅ |
| Documentation | ✅ |

---

## Security

- **Credentials** stored in `.env` file (never committed to git)
- **Human-in-the-Loop** for all sensitive actions
- **Audit logging** for all actions in `Logs/` folder
- **Approval workflow** prevents unintended actions
- **Session isolation** for LinkedIn messaging

---

## Contributing

This is a hackathon project. Contributions welcome via pull requests.

---

## License

MIT License - See LICENSE file for details

---

## Acknowledgments

- **Hackathon:** Personal AI Employee Hackathon 0 - Building Autonomous FTEs in 2026
- **Inspired by:** Claude Code Agent Skills and Model Context Protocol (MCP)
- **Tools:** Claude Code, Obsidian, UV, Playwright, Odoo

---

*Last Updated: 2026-02-28*
*Version: 0.1.0*
