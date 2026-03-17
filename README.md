# Personal AI Employee

> *Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.*

**Hackathon:** Personal AI Employee Hackathon 0 - Building Autonomous FTEs in 2026

**Current Tier:** Platinum ⏳ 80% In Progress (Cloud deployment pending)

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
- **Cloud Agents** - OpenAI Agents SDK for autonomous cloud processing (Platinum)
- **24/7 Operation** - PM2 process management with auto-restart

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Cloud Deployment](#cloud-deployment)
- [Cloud Agents](#cloud-agents)
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

## Architecture

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AI EMPLOYEE SYSTEM                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ╔═════════════════════════════════════════════════════════════════════════╗   │
│  ║                         ENTRY POINTS                                      ║   │
│  ╠═════════════════════════════════════════════════════════════════════════╣   │
│  ║  1. Cron Jobs (Scheduled Automation)                                      ║   │
│  ║  2. Claude Code Skills (Interactive)                                      ║   │
│  ║  3. Watchdog.py (Production Monitoring)                                   ║   │
│  ║  4. Cloud Orchestrator (24/7 Cloud Operation)                             ║   │
│  ╚═════════════════════════════════════════════════════════════════════════╝   │
│                                      │                                          │
│                    ┌─────────────────┴─────────────────┐                       │
│                    ▼                                   ▼                        │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────────┐    │
│  │         LOCAL (Your PC)         │   │        CLOUD (VM 24/7)          │    │
│  │                                 │   │                                 │    │
│  │  PM2 → watchdog.py              │   │  PM2 → cloud_orchestrator.py    │    │
│  │         │                       │   │         │                       │    │
│  │         ▼                       │   │         ▼                       │    │
│  │  orchestrator.py                │   │  ┌─────────────────────────┐    │    │
│  │         │                       │   │  │   Cloud Agents (OpenAI) │    │    │
│  │         ▼                       │   │  │   ┌─────────────────┐   │    │    │
│  │  ┌─────────────────┐            │   │  │   │  TriageAgent    │   │    │    │
│  │  │ Local Watchers  │            │   │  │   │  (Router)       │   │    │    │
│  │  │ • filesystem    │            │   │  │   └────────┬────────┘   │    │    │
│  │  │ • gmail         │            │   │  │            │            │    │    │
│  │  │ • linkedin      │            │   │  │   ┌────────┼────────┐   │    │    │
│  │  └─────────────────┘            │   │  │   ▼        ▼        ▼   │    │    │
│  │                                 │   │  │ Email   Social  Finance │    │    │
│  └─────────────────────────────────┘   │  └─────────────────────────┘    │    │
│                                        │         │                       │    │
│                                        │         ▼                       │    │
│                                        │  ┌─────────────────┐            │    │
│                                        │  │ Cloud Watchers  │            │    │
│                                        │  │ • gmail         │            │    │
│                                        │  └─────────────────┘            │    │
│                                        └─────────────────────────────────┘    │
│                                                                                 │
│  ╔═════════════════════════════════════════════════════════════════════════╗   │
│  ║                    SHARED STATE (Git Sync)                               ║   │
│  ║                                                                          ║   │
│  ║   AI_Employee_Vault/  ←──── vault_sync.py (cron every 5 min) ────→      ║   │
│  ║                                                                          ║   │
│  ║   • Logs/gmail_processed_ids.json (prevents duplicate processing)       ║   │
│  ║   • Dashboard.md, Content_To_Post/, Pending_Approval/                   ║   │
│  ╚═════════════════════════════════════════════════════════════════════════╝   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Architecture Layers

| Layer | Components | Purpose |
|-------|------------|---------|
| **Perception** | Watchers (File, Gmail, LinkedIn) | Monitor external inputs |
| **Reasoning** | Claude Code + Cloud Agents | Process tasks, make decisions |
| **Action** | MCP Servers (6 total) | Execute external actions |
| **Orchestration** | orchestrator.py, cloud_orchestrator.py | Manage processes, health checks |
| **State** | Git Sync, Vault | Shared state, persistence |

### Processing Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  PERCEPTION     │───▶│  REASONING      │───▶│  ACTION         │
│  (Watchers)     │    │  (Claude/AI)    │    │  (MCP Servers)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘

Local:  Watcher → Needs_Action → Claude → Pending_Approval → Human → Approved → MCP
Cloud:  Watcher → Needs_Action → AI Agent → Pending_Approval → Human → Approved → MCP
```

---

## Quick Start

### Prerequisites

- **Python** 3.13 or higher
- **Claude Code** (Pro subscription or Free with Gemini API)
- **Obsidian** (for vault/dashboard)
- **UV** (Python package manager)
- **Node.js 18+** and **PM2** (for 24/7 operation)

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

# 5. Set up Gmail OAuth
uv run python refresh_gmail_mcp_token.py
```

### Start the System

```bash
# Development (single process)
cd ai_employee_scripts
uv run python orchestrator.py

# Production (PM2 24/7)
pm2 start ecosystem.local.config.js
pm2 save
pm2 startup
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
claude code -p "/process-file"

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
│   ├── hooks/
│   │   └── ralph_wiggum.py  # Stop hook
│   └── settings.local.json  # MCP configuration
│
├── ai_employee_scripts/
│   ├── watchers/            # Local Watchers
│   │   ├── base_watcher.py
│   │   ├── filesystem_watcher.py
│   │   ├── gmail_watcher.py
│   │   └── linkedin_watcher.py
│   │
│   ├── cloud_watchers/      # Cloud Watchers
│   │   ├── base_cloud_watcher.py
│   │   ├── gmail_watcher.py
│   │   └── linkedin_watcher.py
│   │
│   ├── cloud/               # Cloud Agents (Platinum)
│   │   ├── cloud_orchestrator.py
│   │   ├── agent_definitions/
│   │   │   ├── triage_agent.py
│   │   │   ├── email_agent.py
│   │   │   ├── social_agent.py
│   │   │   └── finance_agent.py
│   │   ├── mcp_servers/
│   │   │   └── odoo_server.py
│   │   └── guardrails/
│   │
│   ├── mcp_servers/         # MCP Servers (6 total)
│   │   ├── gmail_mcp.py
│   │   ├── linkedin_api_mcp.py
│   │   ├── linkedin_mcp.py
│   │   ├── odoo_mcp.py
│   │   ├── meta_mcp.py
│   │   └── twitter_mcp.py
│   │
│   ├── shared/              # Error Recovery
│   ├── scripts/             # Cron Triggers
│   ├── orchestrator.py      # Local orchestrator
│   ├── watchdog.py          # Process monitor
│   ├── vault_sync.py        # Git sync (Platinum)
│   ├── ecosystem.local.config.js   # PM2 local config
│   └── ecosystem.cloud.config.js   # PM2 cloud config
│
├── AI_Employee_Vault/       # Obsidian Vault (Data)
│   ├── Dashboard.md
│   ├── Company_Handbook.md
│   ├── Inbox/
│   ├── Needs_Action/
│   ├── Pending_Approval/
│   ├── Approved/
│   ├── Done/
│   ├── Logs/
│   │   └── gmail_processed_ids.json  # Shared state
│   └── Content_To_Post/
│
├── documentation/           # Full documentation
│   ├── GETTING_STARTED.md
│   ├── CLOUD_DEPLOYMENT_GUIDE.md
│   ├── CLOUD_AGENTS_GUIDE.md
│   ├── PM2_SETUP_GUIDE.md
│   └── ...
│
├── README.md
├── PROJECT_STATUS.md
└── CLAUDE.md
```

---

## Cloud Deployment

Deploy to a cloud VM for 24/7 autonomous operation.

### Quick Setup

```bash
# On cloud VM (Ubuntu)
git clone https://github.com/your-username/ai-employee.git
cd ai-employee/ai_employee_scripts

# Install dependencies
uv sync

# Configure environment
cp .env.cloud.example .env
# Edit .env with cloud credentials

# Start with PM2
pm2 start ecosystem.cloud.config.js
pm2 save
pm2 startup
```

### Shared State (Git Sync)

Prevents duplicate email processing between local and cloud:

```bash
# Set up cron (both local and cloud)
*/5 * * * * cd /path/to/ai_employee_scripts && uv run python vault_sync.py
```

**How it works:**
1. Cloud watcher processes email → saves ID to `gmail_processed_ids.json`
2. Git push → local pulls
3. Local watcher reads same file → skips already processed emails

### PM2 Configuration

| Config | Purpose | Runs |
|--------|---------|------|
| `ecosystem.local.config.js` | Local PC | watchdog.py → orchestrator.py |
| `ecosystem.cloud.config.js` | Cloud VM | cloud_orchestrator.py |

---

## Cloud Agents

Cloud Agents are autonomous AI agents built with **OpenAI Agents SDK** that run 24/7 on the cloud VM.

### Agent Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TriageAgent                          │
│  - Analyzes incoming tasks                              │
│  - Routes to appropriate specialist                     │
│  - Attaches MCP servers to specialists                  │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌────────────┐  ┌────────────┐  ┌────────────┐
│ EmailAgent │  │SocialAgent │  │FinanceAgent│
│            │  │            │  │            │
│ - Draft    │  │ - Posts    │  │ - Invoices │
│ - Reply    │  │ - Schedule │  │ - Reports  │
│ - Search   │  │ - Analyze  │  │ - Odoo MCP │
└────────────┘  └────────────┘  └────────────┘
```

### Agents

| Agent | Purpose | MCP Integration |
|-------|---------|-----------------|
| **TriageAgent** | Routes tasks to specialists | Attaches MCP to specialists |
| **EmailAgent** | Email processing | None |
| **SocialAgent** | Social media management | None |
| **FinanceAgent** | Accounting/invoicing | Odoo MCP (per-request) |

### MCP Integration Pattern

**Critical:** MCP servers use per-request lifecycle, not global caching:

```python
# ✅ CORRECT
async def handle_request():
    server = MCPServerStdio(...)
    agent.mcp_servers = [server]
    await server.connect()
    try:
        result = await Runner.run(agent, ...)
    finally:
        await server.cleanup()
```

### Security

Cloud MCP is **read-only + draft-only**:
- Can read customer data
- Can create draft invoices
- Cannot post/finalize invoices

---

## Automated Scheduling

4 cron jobs for automated operation:

| Time | Day | Platform | Purpose |
|------|-----|----------|---------|
| 2:00 AM | Daily | LinkedIn | Generate post |
| 3:00 AM | Daily | Facebook/Instagram | Generate post |
| 4:00 AM | Daily | Twitter/X | Generate post |
| 6:00 AM | Monday | All | CEO Briefing |

### Setup Cron Jobs

```bash
crontab -e

# Add:
PATH=/home/adev/.local/bin:/usr/local/bin:/usr/bin:/bin

0 2 * * * cd "/path/to/ai_employee_scripts" && uv run python scripts/linkedin_cron_trigger.py >> /path/to/Logs/cron.log 2>&1
0 3 * * * cd "/path/to/ai_employee_scripts" && uv run python scripts/meta_cron_trigger.py >> /path/to/Logs/cron.log 2>&1
0 4 * * * cd "/path/to/ai_employee_scripts" && uv run python scripts/twitter_cron_trigger.py >> /path/to/Logs/cron.log 2>&1
0 6 * * 1 cd "/path/to/ai_employee_scripts" && uv run python scripts/weekly_audit_cron_trigger.py >> /path/to/Logs/cron.log 2>&1
```

---

## MCP Servers

6 MCP servers for external actions:

| Server | Purpose | Tools |
|--------|---------|-------|
| `gmail` | Email operations | send_email, draft_email, search_emails, get_thread |
| `linkedin_api` | LinkedIn posting | post_to_linkedin, get_linkedin_profile |
| `linkedin` | LinkedIn messaging | get_messages, reply_to_message, validate_session |
| `odoo` | Accounting | create_draft_invoice, get_invoices, get_revenue, get_expenses |
| `meta-api` | Facebook/Instagram | post_to_facebook, post_to_instagram, post_to_both |
| `twitter-api` | Twitter/X | post_tweet, post_business_update, get_twitter_profile |

**Cloud MCP (7th):** `cloud/mcp_servers/odoo_server.py` - Read-only + draft-only

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
      "cwd": "/path/to/ai-employee/ai_employee_scripts",
      "env": {
        "LINKEDIN_MCP_SESSION": "/path/to/sessions/linkedin_mcp"
      }
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

**Note:** Replace `/path/to/ai-employee` with your actual project path. The `linkedin` MCP server requires the `LINKEDIN_MCP_SESSION` environment variable pointing to the Playwright session directory.

---

## Agent Skills

18 skills organized by category:

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
                     └──────┬───────┘                          └──────────────┘
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

### Error Categories

| Category | Examples | Recovery |
|----------|----------|----------|
| Transient | Network timeout, API rate limit | Exponential backoff retry |
| Authentication | Expired token | Alert human, pause operations |
| Logic | Claude misinterprets | Human review queue |
| Data | Corrupted file | Quarantine + alert |
| System | Orchestrator crash | Watchdog auto-restart |

### Components

- **`error_handler.py`** - Error classification
- **`retry_handler.py`** - Retry with exponential backoff
- **`watchdog.py`** - Monitors and restarts orchestrator
- **`Failed_Queue/`** - Failed actions for human review

---

## Platform-Specific Notes

### Instagram Posting
- **Image required** - Must provide public image URL
- **Caption limit** - 2200 characters
- **Image size** - 1080x1080px recommended

### Twitter/X Posting
- **Character limit** - 280 characters (strict)
- **API credits** - Required for posting (402 Payment Required)

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
ps aux | grep watcher
tail -f AI_Employee_Vault/Logs/cron.log
claude code -p "/start-watcher filesystem"
```

### MCP server not connecting
```bash
cd ai_employee_scripts
uv run python mcp_servers/gmail_mcp.py
```

### PM2 issues
```bash
pm2 status
pm2 logs ai-employee-local --lines 50
pm2 restart ai-employee-local
```

### Ralph Wiggum hook blocking exit
```bash
touch AI_Employee_Vault/stop_ralph
# Or process pending tasks
claude code -p "/check-tasks"
```

---

## Dependencies

```toml
[project]
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
    "openai-agents>=0.1.0",  # Cloud Agents
]
```

---

## Tier Progress

| Tier | Status | Progress |
|------|--------|----------|
| **Bronze** | ✅ Complete | 100% |
| **Silver** | ✅ Complete | 100% |
| **Gold** | ✅ Complete | 100% |
| **Platinum** | ⏳ In Progress | ~80% |

### Platinum Tier Checklist

| Requirement | Status |
|-------------|--------|
| Cloud agents (OpenAI Agents SDK) | ✅ |
| Cloud MCP integration | ✅ |
| Cloud watchers (Gmail) | ✅ |
| PM2 configs (local + cloud) | ✅ |
| Vault sync script | ✅ |
| Cloud VM deployment | ❌ Pending |
| Vault sync cron setup | ❌ Pending |

---

## Security

- **Credentials** stored in `.env` file (never committed to git)
- **Human-in-the-Loop** for all sensitive actions
- **Audit logging** for all actions in `Logs/` folder
- **Approval workflow** prevents unintended actions
- **Session isolation** for LinkedIn messaging
- **Cloud MCP** is read-only + draft-only

---

## Documentation

Full documentation available in `documentation/`:

| Document | Description |
|----------|-------------|
| [GETTING_STARTED.md](documentation/GETTING_STARTED.md) | Installation guide |
| [PROJECT_ARCHITECTURE.md](documentation/PROJECT_ARCHITECTURE.md) | System architecture |
| [CLOUD_DEPLOYMENT_GUIDE.md](documentation/CLOUD_DEPLOYMENT_GUIDE.md) | Cloud deployment |
| [CLOUD_AGENTS_GUIDE.md](documentation/CLOUD_AGENTS_GUIDE.md) | Cloud agents |
| [PM2_SETUP_GUIDE.md](documentation/PM2_SETUP_GUIDE.md) | PM2 setup |
| [TROUBLESHOOTING_GUIDE.md](documentation/TROUBLESHOOTING_GUIDE.md) | Troubleshooting |

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
- **Tools:** Claude Code, Obsidian, UV, Playwright, Odoo, OpenAI Agents SDK

---

*Last Updated: 2026-03-14*
*Version: 0.2.0*