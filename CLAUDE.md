# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Personal AI Employee Hackathon 0** — Building an autonomous Digital FTE (Full-Time Equivalent) using Claude Code, Obsidian, and Python.

The architecture separates **data** (Obsidian vault) from **code** (Python scripts):

```
ai-employee/
├── AI_Employee_Vault/     # Obsidian vault (data, task state)
├── .claude/skills/          # Claude Agent Skills
└── ai_employee_scripts/      # UV Python project (watchers, MCP servers)
```

---

## Essential Commands

### Python Environment (UV)

```bash
# Install dependencies
cd ai_employee_scripts && uv sync

# Run a watcher script
cd ai_employee_scripts && uv run python watchers/<script>.py

# Add new dependencies
cd ai_employee_scripts && uv add <package>
```

### File System Watcher

```bash
# Start the watcher (monitors Drop_Zone/)
cd ai_employee_scripts && uv run python watchers/filesystem_watcher.py

# Stop the watcher
pkill -f filesystem_watcher

# Check if running
ps aux | grep filesystem_watcher | grep -v grep
```

---

## Architecture

### Perception → Reasoning → Action

1. **Perception (Watchers)** — Scripts that monitor external inputs
   - `base_watcher.py` — Abstract base class with polling loop pattern
   - `filesystem_watcher.py` — Polling-based file monitor (WSL-compatible)
   - `gmail_watcher.py` — Gmail email monitoring
   - `linkedin_watcher.py` — LinkedIn message monitoring

2. **Reasoning (Claude)** — Processes tasks via Agent Skills (`.claude/skills/`)

3. **Action (MCP Servers)** — Execute external actions via 6 MCP servers (Gmail, LinkedIn, LinkedIn API, Twitter, Meta, Odoo)

### Watcher Pattern

All watchers follow the `BaseWatcher` pattern:
- `check_for_updates()` — Return list of new items
- `create_action_file(item)` — Create `.md` task in `Needs_Action/`
- `run()` — Main polling loop with `check_interval`

**Note:** Uses **polling** (not `inotify`) for WSL compatibility. Watcher checks folder every N seconds rather than using file system events.

---

## Agent Skills

Located in `.claude/skills/`. These are slash-commands for Claude:

**Task Management:** `check-tasks`, `process-file`, `create-plan`, `daily-summary`
**Business:** `check-accounting`, `create-invoice`, `weekly-audit`
**Social Media:** `linkedin-posting`, `meta-posting`, `twitter-posting`, `post-linkedin`
**Approvals:** `approve-action`, `execute-approved`
**Watchers:** `start-watcher`, `stop-watcher`, `watcher-status`, `check-watchers`
**Config:** `update-handbook`

---

## Vault Folder Structure

`AI_Employee_Vault/` is the central data store:

| Folder | Purpose |
|---------|-----------|
| `Inbox/` | Raw input copied from watchers |
| `Needs_Action/` | Tasks awaiting Claude processing |
| `Done/` | Completed tasks |
| `Pending_Approval/` | Actions requiring human approval |
| `Approved/` | Approved actions (triggers execution) |
| `Rejected/` | Rejected actions |
| `Logs/` | Activity logs and error records |
| `Briefings/` | Weekly CEO Briefing reports |
| `Content_To_Post/` | Social media content queue |
| `Dashboard.md` | Central status hub |
| `Company_Handbook.md` | AI behavior rules and constraints |

---

## Company_Handbook Rules (CRITICAL)

**Always reference `AI_Employee_Vault/Company_Handbook.md` before taking actions.**

Key constraints:
- **Financial:** Payments >$100 or new recipients ALWAYS require approval
- **WhatsApp:** Never auto-reply; keywords `urgent`, `asap`, `invoice`, `payment`, `help` trigger flags
- **Social Media:** Drafts only; posting/replies require approval
- **NEVER without permission:** Send money, commit to deadlines, share contacts, delete files outside vault

---

## Hackathon Tier Progress

| Tier | Status |
|-------|--------|
| **Bronze** | ✅ Complete — Vault, File System Watcher, Agent Skills |
| **Silver** | ✅ Complete — Gmail/LinkedIn watchers, MCP servers, orchestrator |
| **Gold** | ✅ Complete — Odoo integration, Ralph Wiggum loop, CEO Briefing |
| **Platinum** | ⏳ Not started — Cloud deployment, vault sync |

---

## Important Implementation Notes

### WSL Compatibility
The File System Watcher uses **polling** instead of `watchdog.Observer` because `inotify` doesn't work reliably on WSL with Windows-mounted drives (`/mnt/d/`).

### Approval Workflow
For sensitive actions, create files in `Pending_Approval/` with format:
```
ACTION_[type]_[target]_[date].md
```
Human approval = moving file to `Approved/` (triggers execution via orchestrator).

### Error Handling
- Log errors to `Logs/YYYY-MM-DD.json`
- Create notification file in `Needs_Action/`
- Never auto-retry financial/sensitive actions without approval

---

## Adding New Components

### New Watcher
1. Create `ai_employee_scripts/watchers/<name>_watcher.py`
2. Inherit from `BaseWatcher`
3. Implement `check_for_updates()` and `create_action_file()`
4. Add dependencies via `uv add <package>`

### Available Skills

Located in `.claude/skills/<skill-name>/SKILL.md`. Each skill is self-contained with its own frontmatter and logic.

**Current Skills (18 total):**

| Skill | Purpose |
|--------|---------|
| `check-tasks` | List pending tasks in `Needs_Action/` |
| `process-file` | Process a file from `Inbox/` |
| `daily-summary` | Generate daily summary and update `Dashboard.md` |
| `watcher-status` | Check if File System Watcher is running |
| `update-handbook` | Add/update rules in `Company_Handbook.md` |
| `check-accounting` | Check accounting status from Odoo |
| `create-invoice` | Create draft invoice in Odoo |
| `weekly-audit` | Generate weekly CEO Briefing |
| `linkedin-posting` | Generate LinkedIn posts |
| `meta-posting` | Generate Facebook/Instagram posts |
| `twitter-posting` | Generate Twitter posts |
| `post-linkedin` | Queue LinkedIn posts |
| `approve-action` | Move action to Approved folder |
| `execute-approved` | Execute approved actions via MCP |
| `start-watcher` | Start a watcher script |
| `stop-watcher` | Stop watcher(s) |
| `check-watchers` | Check status of all watchers |
| `create-plan` | Create Plan.md for complex tasks |

---

### Adding New Skills

**Pattern**: Each skill lives in its own folder with a `SKILL.md` file.

```
.claude/skills/
├── check-tasks/
│   └── SKILL.md
├── process-file/
│   └── SKILL.md
├── daily-summary/
│   └── SKILL.md
├── watcher-status/
│   └── SKILL.md
└── update-handbook/
    └── SKILL.md
```

To add a new skill:
1. Create folder: `.claude/skills/<skill-name>/`
2. Create file: `.claude/skills/<skill-name>/SKILL.md`
3. Add frontmatter with description and usage
### Adding MCP Servers
6 MCP servers available: `gmail_mcp.py`, `linkedin_mcp.py`, `linkedin_api_mcp.py`, `twitter_mcp.py`, `meta_mcp.py`, `odoo_mcp.py`
1. Create `ai_employee_scripts/mcp_servers/<name>.py`
2. Implement MCP protocol (stdio JSON-RPC)
3. Register in Claude Code MCP config

---

## Security

- **Never commit** `.env` files, API tokens, or credentials
- Use environment variables for all secrets
- `Drop_Zone/` files are copied to `Inbox/` (safekeeping)
- Human-in-the-Loop required for financial/social actions
