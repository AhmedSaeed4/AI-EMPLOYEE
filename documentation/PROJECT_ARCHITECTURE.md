# AI Employee - Project Architecture Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Component Breakdown](#component-breakdown)
4. [Data Flow](#data-flow)
5. [File Structure](#file-structure)
6. [Configuration Files](#configuration-files)
7. [Skills Reference](#skills-reference)

---

## Overview

**AI Employee** is an autonomous Digital FTE (Full-Time Equivalent) built with Claude Code, Obsidian, and Python. It monitors external inputs (Gmail, LinkedIn, files), processes them using Claude AI, and executes actions (send emails, post to social media, manage accounting).

### Core Philosophy: Perception → Reasoning → Action

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  PERCEPTION     │───▶│  REASONING      │───▶│  ACTION         │
│  (Watchers)     │    │  (Claude Code)  │    │  (MCP Servers)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

| Stage | Component | Purpose |
|-------|-----------|---------|
| **Perception** | Watchers | Monitor external inputs continuously |
| **Reasoning** | Claude Code + Skills | Process tasks, make decisions |
| **Action** | MCP Servers | Execute external actions |

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AI EMPLOYEE SYSTEM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        ORCHESTRATOR (24/7)                            │  │
│  │  - Starts/Stops watchers                                              │  │
│  │  - Monitors Needs_Action/, Approved/, Rejected/                       │  │
│  │  - Triggers Claude Code skills                                        │  │
│  │  - Health checks and auto-restart                                     │  │
│  └─────────────┬─────────────────────────────────────────────────────────┘  │
│                │                                                            │
│                ▼                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        WATCHERS (Perception)                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐    │  │
│  │  │  File System │  │    Gmail     │  │       LinkedIn           │    │  │
│  │  │    Watcher   │  │    Watcher   │  │       Watcher            │    │  │
│  │  │              │  │              │  │                          │    │  │
│  │  │ Poll every   │  │ Poll every   │  │  Poll every             │    │  │
│  │  │  2 seconds   │  │  2 minutes   │  │  5 minutes               │    │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────────────────┘    │  │
│  └─────────┼──────────────────┼───────────────────┼──────────────────────┘  │
│            │                  │                   │                          │
│            ▼                  ▼                   ▼                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     AI_EMPLOYEE_VAULT (Data Store)                    │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐    │  │
│  │  │  Inbox/      │  │Needs_Action/ │  │   Approved/              │    │  │
│  │  │              │  │              │  │   Rejected/              │    │  │
│  │  │ Full content │  │ Task files   │  │   Pending_Approval/      │    │  │
│  │  │ storage      │  │ for Claude   │  │   Done/                  │    │  │
│  │  └──────────────┘  └──────┬───────┘  └──────────────────────────┘    │  │
│  └───────────────────────────────────┼─────────────────────────────────────┘  │
│                                      │                                        │
│                                      ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    CLAUDE CODE (Reasoning)                             │  │
│  │  - Reads task files from Needs_Action/                                 │  │
│  │  - Processes content (emails, messages, files)                         │  │
│  │  - Creates action files in Pending_Approval/ (for sensitive actions)   │  │
│  │  - Moves completed tasks to Done/                                      │  │
│  │  - Updates Dashboard.md                                                │  │
│  └─────────────┬─────────────────────────────────────────────────────────┘  │
│                │                                                            │
│                ▼                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     MCP SERVERS (Action)                               │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │  │
│  │  │   Gmail  │ │LinkedIn  │ │LinkedIn  │ │   Odoo   │ │  Twitter │   │  │
│  │  │   MCP    │ │   MCP    │ │  API MCP │ │   MCP    │ │   MCP    │   │  │
│  │  │          │ │          │ │          │ │          │ │          │   │  │
│  │  │Send/Reply│ │Messages  │ │  Posts   │ │Accounting│ │  Tweets  │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │  │
│  │                                                                      │  │
│  │  ┌──────────┐                                                      │  │
│  │  │  Meta    │                                                      │  │
│  │  │   MCP    │                                                      │  │
│  │  │          │                                                      │  │
│  │  │FB/Insta  │                                                      │  │
│  │  └──────────┘                                                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Orchestrator

**File:** `ai_employee_scripts/orchestrator.py`

**Purpose:** 24/7 master process that manages all system components.

**Responsibilities:**

| Function | Description |
|----------|-------------|
| Start Watchers | Launches File System, Gmail, LinkedIn watchers as subprocesses |
| Monitor Needs_Action | Triggers `/process-file` skill when new tasks appear |
| Monitor Approved | Triggers `/execute-approved` skill when actions approved |
| Monitor Rejected | Logs rejected actions to file |
| Health Check | Restarts crashed watchers automatically |
| Graceful Shutdown | Handles SIGINT/SIGTERM, cleans up processes |

**Monitoring Intervals:**

| Folder | Check Interval | Action Triggered |
|--------|---------------|------------------|
| `Needs_Action/` | 30 seconds | `/process-file` |
| `Approved/` | 60 seconds | `/execute-approved` |
| `Rejected/` | 60 seconds | Log to file |
| Watcher Health | 60 seconds | Auto-restart |

**State Persistence:**
- State file: `Logs/orchestrator_state.json`
- Tracks: `seen_files` (to avoid reprocessing)

---

### 2. Watchers (Perception Layer)

**Location:** `ai_employee_scripts/watchers/`

| Watcher | File | Poll Interval | Monitors | Creates |
|---------|------|--------------|----------|---------|
| File System | `filesystem_watcher.py` | 2 seconds | `Drop_Zone/` folder | Task in `Needs_Action/` |
| Gmail | `gmail_watcher.py` | 2 minutes | Gmail (last 24h) | Task in `Needs_Action/` |
| LinkedIn | `linkedin_watcher.py` | 5 minutes | LinkedIn messages | Task in `Needs_Action/` |

**Base Watcher Class:** `base_watcher.py`

All API-based watchers inherit from `BaseWatcher` which provides:
- Polling loop with `run()` method
- Logging to file and console
- Error handling with consecutive error tracking
- Failed_Queue file creation for retries

**Note:** FileSystemWatcher is standalone (doesn't inherit from BaseWatcher).

---

### 3. AI Employee Vault (Data Store)

**Location:** `AI_Employee_Vault/`

**Purpose:** Central data store for all tasks, content, and state.

| Folder | Purpose | Managed By |
|--------|---------|------------|
| `Inbox/` | Full content storage (emails, messages, files) | Watchers |
| `Needs_Action/` | Tasks awaiting Claude processing | Watchers → Claude |
| `Pending_Approval/` | Actions requiring human approval | Claude (sensitive actions) |
| `Approved/` | Approved actions ready to execute | Human (moves from Pending) |
| `Rejected/` | Rejected actions (logged) | Human (moves from Pending) |
| `Done/` | Completed tasks | Claude (after processing) |
| `Logs/` | Activity logs, state files, errors | System |
| `Briefings/` | Weekly CEO briefings | `weekly-audit` skill |
| `Content_To_Post/` | Social media content queue | Content skills |

---

### 4. Claude Code (Reasoning Layer)

**Interface:** `.claude/skills/` - Agent Skills (slash commands)

**Skills:** 20+ skills for different operations

| Skill Category | Skills |
|----------------|--------|
| **Task Management** | `check-tasks`, `process-file`, `create-plan` |
| **Watcher Control** | `start-watcher`, `stop-watcher`, `check-watchers`, `watcher-status` |
| **Accounting** | `check-accounting`, `create-invoice` |
| **Social Media** | `linkedin-posting`, `meta-posting`, `twitter-posting`, `post-linkedin` |
| **Approvals** | `approve-action`, `execute-approved` |
| **Reporting** | `daily-summary`, `weekly-audit` |
| **Configuration** | `update-handbook` |

**Ralph Wiggum Hook:** `.claude/hooks/ralph_wiggum.py`

- Blocks Claude from stopping if `Needs_Action/` has pending files
- Emergency bypass: Create `stop_ralph` file in vault

---

### 5. MCP Servers (Action Layer)

**Location:** `ai_employee_scripts/mcp_servers/`

| MCP Server | Purpose | External Service | Configuration |
|------------|---------|------------------|---------------|
| `gmail_mcp.py` | Send/reply emails | Gmail API | OAuth 2.0 |
| `linkedin_mcp.py` | Send messages | LinkedIn (browser) | Playwright session |
| `linkedin_api_mcp.py` | Create posts | LinkedIn API | OAuth 2.0 |
| `twitter_mcp.py` | Post tweets | Twitter/X API | OAuth 1.0a |
| `meta_mcp.py` | Post to FB/Insta | Meta Graph API | OAuth 2.0 |
| `odoo_mcp.py` | Accounting operations | Odoo JSON-RPC | Docker + credentials |

**MCP Configuration:** `AI_Employee_Vault/.mcp.json`

Registers all MCP servers with Claude Code using `uv run` for execution.

---

## Data Flow

### 1. New Input Arrives

```
┌─────────────────────────────────────────────────────────────────────┐
│ INPUT SOURCE                                                        │
├─────────────────────────────────────────────────────────────────────┤
│ • File dropped in Drop_Zone/                                       │
│ • New email arrives in Gmail                                       │
│ • New LinkedIn message received                                    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ WATCHER DETECTS INPUT                                               │
├─────────────────────────────────────────────────────────────────────┤
│ • FileSystemWatcher: Polling every 2 seconds                       │
│ • GmailWatcher: Polling every 2 minutes                            │
│ • LinkedInWatcher: Polling every 5 minutes                         │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ CREATE FILES                                                        │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Copy full content to Inbox/                                      │
│    - Inbox/EMAIL_[id].md                                           │
│    - Inbox/LINKEDIN_MESSAGE_[timestamp].md                         │
│    - Inbox/[filename] (copied from Drop_Zone)                      │
│                                                                      │
│ 2. Create task in Needs_Action/                                     │
│    - EMAIL_[subject]_[timestamp].md                                 │
│    - LINKEDIN_MESSAGE_[timestamp].md                               │
│    - FILE_[name]_[timestamp].md                                    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR DETECTS NEW TASK                                       │
├─────────────────────────────────────────────────────────────────────┤
│ • Monitors Needs_Action/ every 30 seconds                          │
│ • Calls: /process-file skill                                       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ CLAUDE CODE PROCESSES TASK                                          │
├─────────────────────────────────────────────────────────────────────┤
│ • Reads task file from Needs_Action/                               │
│ • Reads full content from Inbox/                                   │
│ • Determines required action based on:                             │
│   - Task type (email, message, file)                               │
│   - Content analysis                                               │
│   - Company_Handbook.md rules                                      │
│                                                                      │
│ Possible Outcomes:                                                  │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ A. Direct Action (Safe)                                       │  │
│ │    • Reply to email via Gmail MCP                            │  │
│ │    • Send LinkedIn message via LinkedIn MCP                  │  │
│ │    • Move to Done/                                           │  │
│ ├───────────────────────────────────────────────────────────────┤  │
│ │ B. Requires Approval (Sensitive)                              │  │
│ │    • Create file in Pending_Approval/                         │  │
│ │    • Wait for human to move to Approved/ or Rejected/         │  │
│ ├───────────────────────────────────────────────────────────────┤  │
│ │ C. Information Only                                            │  │
│ │    • Extract key information                                  │  │
│ │    • Update Dashboard.md                                     │  │
│ │    • Move to Done/                                            │  │
│ └───────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ APPROVAL WORKFLOW (for sensitive actions)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Pending_Approval/              Human Decision                      │
│  ┌─────────────────┐            ┌─────────────────┐               │
│  │ ACTION_...md    │───────────▶│ Review          │               │
│  │                 │            │ Decide          │               │
│  └─────────────────┘            └────────┬────────┘               │
│                                          │                         │
│               ┌─────────────────────────┼─────────────────────────┐│
│               │                         │                         ││
│               ▼                         ▼                         ││
│        Approved/                  Rejected/                      ││
│  ┌─────────────────┐          ┌─────────────────┐                ││
│  │ ACTION_...md    │          │ ACTION_...md    │                ││
│  └─────────────────┘          └─────────────────┘                ││
│         │                                                         ││
└─────────┼───────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR DETECTS APPROVED ACTION                                 │
├─────────────────────────────────────────────────────────────────────┤
│ • Monitors Approved/ every 60 seconds                               │
│ • Calls: /execute-approved skill                                   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ EXECUTE ACTION VIA MCP SERVER                                       │
├─────────────────────────────────────────────────────────────────────┤
│ • Send email → Gmail MCP                                            │
│ • Send LinkedIn message → LinkedIn MCP                              │
│ • Post to social media → LinkedIn/Twitter/Meta MCP                  │
│ • Create invoice → Odoo MCP                                         │
│                                                                      │
│ • Move to Done/                                                     │
│ • Update Dashboard.md                                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

### Project Root

```
ai-employee/
├── AI_Employee_Vault/          # Central data store
├── ai_employee_scripts/        # Python scripts
├── Drop_Zone/                  # File drop location
├── documentation/              # Project documentation
│   ├── mcp/                    # MCP server docs
│   └── watchers/               # Watcher docs
├── .claude/                    # Claude Code config
│   ├── skills/                 # Agent skills
│   ├── hooks/                  # Hooks (Ralph Wiggum)
│   └── settings.local.json     # Claude settings
└── .mcp.json                   # MCP config (legacy)
```

### ai_employee_scripts/

```
ai_employee_scripts/
├── watchers/                   # Perception layer
│   ├── base_watcher.py         # Abstract base class
│   ├── filesystem_watcher.py   # File monitoring
│   ├── gmail_watcher.py        # Gmail monitoring
│   ├── linkedin_watcher.py     # LinkedIn monitoring
│   └── save_linkedin_session.py # Helper (not actively used)
│
├── mcp_servers/                # Action layer
│   ├── gmail_mcp.py            # Email operations
│   ├── linkedin_mcp.py         # LinkedIn messaging
│   ├── linkedin_api_mcp.py     # LinkedIn posting
│   ├── twitter_mcp.py          # Twitter posting
│   ├── meta_mcp.py             # Facebook/Instagram posting
│   └── odoo_mcp.py             # Accounting operations
│
├── shared/                     # Shared utilities
│   ├── error_handler.py        # Error handling
│   └── retry_handler.py        # Retry logic
│
├── scripts/                    # Cron triggers
│   ├── linkedin_cron_trigger.py
│   ├── meta_cron_trigger.py
│   ├── twitter_cron_trigger.py
│   └── weekly_audit_cron_trigger.py
│
├── orchestrator.py             # Master controller (24/7 process)
├── refresh_gmail_mcp_token.py  # Token refresh utility
├── setup_linkedin.py           # LinkedIn setup helper
├── main.py                     # Entry point
├── watchdog.py                 # Watchdog process
├── pyproject.toml              # UV project config
├── credentials.json            # OAuth credentials (git-ignored)
├── token_gmail.json            # Gmail MCP token (git-ignored)
└── token_gmail_watcher.json    # Gmail Watcher token (git-ignored)
```

### AI_Employee_Vault/

```
AI_Employee_Vault/
├── Inbox/                      # Full content storage
│   ├── EMAIL_[id].md
│   ├── LINKEDIN_MESSAGE_[ts].md
│   └── [copied files]
│
├── Needs_Action/               # Tasks awaiting processing
│   ├── EMAIL_[subject]_[ts].md
│   ├── LINKEDIN_MESSAGE_[ts].md
│   └── FILE_[name]_[ts].md
│
├── Pending_Approval/           # Awaiting human approval
│   └── ACTION_[type]_[target]_[date].md
│
├── Approved/                   # Approved actions (execute)
│   └── ACTION_[type]_[target]_[date].md
│
├── Rejected/                   # Rejected actions (log only)
│   └── ACTION_[type]_[target]_[date].md
│
├── Done/                       # Completed tasks
│   ├── COMPLETED_[type]_[ts].md
│   └── [processed files]
│
├── Logs/                       # System logs
│   ├── YYYY-MM-DD_orchestrator.log
│   ├── orchestrator_state.json
│   ├── linkedin_state.json
│   ├── rejected_actions.log
│   └── [watcher logs]
│
├── Briefings/                  # CEO briefings
│   └── YYYY-MM-DD_Weekly_Briefing.md
│
├── Content_To_Post/            # Social media queue
│   ├── queued/
│   └── posted/
│
├── Dashboard.md                # Central status hub
├── Company_Handbook.md         # AI behavior rules
├── Business_Goals.md           # Business objectives
├── .mcp.json                   # MCP server config
└── .obsidian/                  # Obsidian settings
```

---

## Configuration Files

### 1. MCP Configuration

**File:** `AI_Employee_Vault/.mcp.json`

**Purpose:** Registers MCP servers with Claude Code.

**Format:**
```json
{
  "mcpServers": {
    "gmail": {
      "type": "stdio",
      "command": "uv",
      "args": ["--directory", "/path/to/ai_employee_scripts", "run", "mcp_servers/gmail_mcp.py"],
      "env": {"PYTHONPATH": "/path/to/ai_employee_scripts"}
    },
    ...
  }
}
```

**Servers Registered:**
- `gmail` - Email operations
- `linkedin` - LinkedIn messaging
- `linkedin-api` - LinkedIn posting
- `twitter-api` - Twitter posting
- `meta-api` - Facebook/Instagram posting
- `odoo` - Accounting operations

### 2. Claude Code Settings

**File:** `.claude/settings.local.json`

**Purpose:** Claude Code IDE settings.

### 3. UV Project Configuration

**File:** `ai_employee_scripts/pyproject.toml`

**Purpose:** Python dependency management.

**Dependencies Include:**
- `google-api-python-client` - Gmail API
- `playwright` - Browser automation
- `fastmcp` - MCP server framework
- `odoo-api` - Odoo integration

### 4. Environment Variables

**Required Environment Variables (via .env):**

| Variable | Purpose | Used By |
|----------|---------|---------|
| `LINKEDIN_CLIENT_ID` | LinkedIn OAuth | LinkedIn API MCP |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn OAuth | LinkedIn API MCP |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn OAuth | LinkedIn API MCP |
| `X_API_KEY` | Twitter OAuth | Twitter MCP |
| `X_API_SECRET` | Twitter OAuth | Twitter MCP |
| `X_ACCESS_TOKEN` | Twitter OAuth | Twitter MCP |
| `X_ACCESS_TOKEN_SECRET` | Twitter OAuth | Twitter MCP |
| `META_PAGE_ID` | Facebook Page | Meta MCP |
| `META_ACCESS_TOKEN` | Long-lived token | Meta MCP |
| `INSTAGRAM_BUSINESS_ID` | Instagram account | Meta MCP |
| `ODOO_URL` | Odoo instance | Odoo MCP |
| `ODOO_DB` | Database name | Odoo MCP |
| `ODOO_USER` | API user | Odoo MCP |
| `ODOO_PASSWORD` | API password | Odoo MCP |
| `LINKEDIN_MCP_SESSION` | Session path | LinkedIn MCP |

---

## Skills Reference

### Task Management Skills

| Skill | Trigger | Action |
|-------|---------|--------|
| `check-tasks` | Manual | List all pending tasks in Needs_Action/ |
| `process-file` | Orchestrator | Process tasks from Needs_Action/ |
| `create-plan` | Manual | Create Plan.md for complex tasks |

### Watcher Control Skills

| Skill | Trigger | Action |
|-------|---------|--------|
| `start-watcher` | Manual | Start specific watcher or all |
| `stop-watcher` | Manual | Stop specific watcher or all |
| `check-watchers` | Manual | Check status of all watchers |
| `watcher-status` | Manual | Show File System Watcher status |

### Accounting Skills

| Skill | Trigger | Action |
|-------|---------|--------|
| `check-accounting` | Manual | Get revenue, expenses, invoices from Odoo |
| `create-invoice` | Manual | Create draft invoice in Odoo |

### Social Media Skills

| Skill | Trigger | Action |
|-------|---------|--------|
| `linkedin-posting` | Manual | Generate LinkedIn post idea |
| `meta-posting` | Manual | Generate Facebook/Instagram post |
| `twitter-posting` | Manual | Generate Twitter post |
| `post-linkedin` | Manual | Add post to Content_To_Post/queued/ |

### Approval Skills

| Skill | Trigger | Action |
|-------|---------|--------|
| `approve-action` | Manual | Move file from Pending_Approval to Approved |
| `execute-approved` | Orchestrator | Execute approved actions via MCP servers |

### Reporting Skills

| Skill | Trigger | Action |
|-------|---------|--------|
| `daily-summary` | Manual/Cron | Generate daily summary, update Dashboard |
| `weekly-audit` | Manual/Cron | Generate CEO briefing, email via Gmail |

### Configuration Skills

| Skill | Trigger | Action |
|-------|---------|--------|
| `update-handbook` | Manual | Add/update rules in Company_Handbook.md |

---

## Key Design Decisions

### 1. Polling vs Events

**Decision:** Use polling for watchers instead of event-driven architecture.

**Reason:** WSL compatibility - `inotify` doesn't work reliably on WSL with Windows-mounted drives.

**Trade-off:** Slight delay (2-5 minutes) vs 100% reliability across platforms.

### 2. Separate Tokens for Watcher and MCP

**Decision:** Gmail Watcher uses `token_gmail_watcher.json`, Gmail MCP uses `token_gmail.json`.

**Reason:** Avoid conflicts when both are running simultaneously.

**Benefit:** Independent operation, no token clobbering.

### 3. Obsidian as Data Store

**Decision:** Use Obsidian vault (Markdown files) instead of database.

**Reason:**
- Human-readable and editable
- Works with Obsidian's graph view
- Easy to backup and sync
- No vendor lock-in

### 4. Approval Workflow

**Decision:** Sensitive actions require human approval (Pending_Approval → Approved).

**Reason:** Safety for financial, social media, and external communications.

**Company_Handbook Rules:**
- Payments >$100 require approval
- New payment recipients require approval
- Social media posts require approval
- WhatsApp replies NEVER auto-sent

### 5. Orchestrator as Master Process

**Decision:** Single 24/7 process manages all watchers and triggers.

**Benefits:**
- Centralized health checking
- Auto-restart crashed watchers
- Unified logging
- Graceful shutdown

---

## Running the System

### Start Full System

```bash
cd ai_employee_scripts
python orchestrator.py
```

**This starts:**
1. Orchestrator process
2. File System Watcher (PID tracked)
3. Gmail Watcher (PID tracked)
4. LinkedIn Watcher (PID tracked)
5. Monitor threads for Needs_Action/, Approved/, Rejected/

### Start Individual Watcher

```bash
cd ai_employee_scripts
python watchers/filesystem_watcher.py
python watchers/gmail_watcher.py
python watchers/linkedin_watcher.py
```

### Check Running Status

```bash
ps aux | grep -E "(orchestrator|filesystem_watcher|gmail_watcher|linkedin_watcher)" | grep -v grep
```

### Stop System

```bash
# Press Ctrl+C in orchestrator terminal
# Or kill orchestrator PID (watchers will stop automatically)
```

---

## Documentation References

| Topic | Document |
|-------|----------|
| Gmail MCP | [documentation/mcp/gmail-mcp.md](mcp/gmail-mcp.md) |
| LinkedIn API MCP | [documentation/mcp/linkedin-api-mcp.md](mcp/linkedin-api-mcp.md) |
| LinkedIn MCP | [documentation/mcp/linkedin-mcp.md](mcp/linkedin-mcp.md) |
| Meta API MCP | [documentation/mcp/meta-api-mcp.md](mcp/meta-api-mcp.md) |
| Twitter API MCP | [documentation/mcp/twitter-api-mcp.md](mcp/twitter-api-mcp.md) |
| Odoo MCP | [documentation/mcp/odoo-mcp.md](mcp/odoo-mcp.md) |
| Base Watcher | [documentation/watchers/base-watcher.md](watchers/base-watcher.md) |
| File System Watcher | [documentation/watchers/filesystem-watcher.md](watchers/filesystem-watcher.md) |
| Gmail Watcher | [documentation/watchers/gmail-watcher.md](watchers/gmail-watcher.md) |
| LinkedIn Watcher | [documentation/watchers/linkedin-watcher.md](watchers/linkedin-watcher.md) |

---

*Generated: 2026-02-28*
*AI Employee Project - Complete Architecture Documentation*
