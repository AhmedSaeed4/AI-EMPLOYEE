# AI Employee Scripts

> **Personal AI Employee Hackathon 0** — Building Autonomous FTEs with Claude Code

This is the codebase for the AI Employee — a collection of Python scripts that act as the "senses" and "hands" for your personal AI assistant.

---

## Project Structure

```
save-1/
├── AI_Employee_Vault/          # Obsidian vault (data only)
│   ├── Inbox/                  # Raw input from watchers
│   ├── Needs_Action/           # Tasks requiring processing
│   ├── Done/                   # Completed tasks
│   ├── Pending_Approval/       # Awaiting human approval
│   ├── Approved/               # Approved actions
│   ├── Rejected/              # Rejected actions
│   ├── Logs/                  # Activity & error logs
│   ├── Dashboard.md            # Central hub
│   └── Company_Handbook.md    # Rules of engagement
│
├── Drop_Zone/                  # Drop files here to test File System Watcher
│
└── ai_employee_scripts/        # This folder (UV Python project)
    ├── watchers/               # Monitoring scripts
    ├── mcp_servers/            # MCP servers (Silver+)
    ├── orchestrator.py         # Master scheduler (Silver+)
    └── .venv/                  # Virtual environment
```

---

## Quick Start

### Prerequisites

- Python 3.13+
- UV package manager
- Claude Code (Pro or free tier with Gemini API)
- Obsidian (for the vault)

### Installation

```bash
# Dependencies are managed by UV
uv sync
```

### Running the File System Watcher

```bash
# Start the watcher
uv run watchers/filesystem_watcher.py
```

Then drop any file into `Drop_Zone/` — the watcher will:
1. Copy the file to `AI_Employee_Vault/Inbox/`
2. Create a task file in `AI_Employee_Vault/Needs_Action/`
3. Notify Claude Code to process it

---

## Components

### Watchers (`watchers/`)

Lightweight scripts that monitor external inputs and trigger the AI.

| Watcher | Status | Purpose |
|---------|--------|---------|
| `base_watcher.py` | ✅ Complete | Abstract base class for all watchers |
| `filesystem_watcher.py` | ✅ Complete | Monitors Drop_Zone for new files |
| `gmail_watcher.py` | ✅ Complete | Monitors Gmail for new emails |
| `linkedin_watcher.py` | ✅ Complete | Monitors LinkedIn messages |
| `whatsapp_watcher.py` | ⏳ Planned | Monitors WhatsApp for messages |

### MCP Servers (`mcp_servers/`)

Model Context Protocol servers that let Claude Code take actions.

| Server | Status | Purpose |
|--------|--------|---------|
| `gmail_mcp.py` | ✅ Complete | Send/reply emails via Gmail API |
| `linkedin_mcp.py` | ✅ Complete | Send LinkedIn messages (browser) |
| `linkedin_api_mcp.py` | ✅ Complete | Post to LinkedIn (API) |
| `twitter_mcp.py` | ✅ Complete | Post to Twitter/X |
| `meta_mcp.py` | ✅ Complete | Post to Facebook/Instagram |
| `odoo_mcp.py` | ✅ Complete | Accounting operations |

---

## Tier Progress

| Tier | Requirements | Status |
|------|-------------|--------|
| **Bronze** | Vault structure, one watcher, Claude read/write | ✅ Complete |
| **Silver** | Multiple watchers, MCP servers, orchestrator | ✅ Complete |
| **Gold** | Odoo integration, Ralph Wiggum loop, CEO Briefing | ✅ Complete |
| **Platinum** | Cloud deployment, vault sync, work-zone specialization | ⏳ Not Started |

---

## Development

### Adding a New Watcher

1. Create a new file in `watchers/`
2. Inherit from `BaseWatcher`
3. Implement `check_for_updates()` and `create_action_file()`
4. Add dependencies to `pyproject.toml` if needed

```bash
uv add <package-name>
```

### Running Scripts

```bash
# With UV (recommended)
uv run watchers/<script_name>.py

# Or activate the virtual environment first
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
python watchers/<script_name>.py
```

---

## Configuration

### Environment Variables

Create a `.env` file in `ai_employee_scripts/` (add to `.gitignore`):

```bash
# Gmail API (Silver tier)
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret

# Banking APIs (Gold tier)
BANK_API_TOKEN=your_token

# WhatsApp session (Silver tier)
WHATSAPP_SESSION_PATH=/path/to/session
```

---

## Security Notes

- **Never commit** `.env` files or API credentials
- Use environment variables for all secrets
- Implement Human-in-the-Loop for sensitive actions
- All financial actions require approval

---

## Resources

- [Hackathon Requirements](../hackathon-requirments/)
- [Claude Code Docs](https://claude.com/product/claude-code)
- [MCP Specification](https://modelcontextprotocol.io)
- [UV Package Manager](https://astral.sh/uv)

---

## License

MIT

---

*Created for Personal AI Employee Hackathon 0 — 2026*
