# Getting Started Guide

## Prerequisites

Before setting up the AI Employee, ensure you have:

- **Python 3.13+** installed
- **UV package manager** ([install guide](https://docs.astral.sh/uv/))
- **Node.js 18+** and **npm** (for PM2)
- **Git** for version control and vault sync
- **Obsidian** (optional, for viewing the vault)
- **Claude Code CLI** ([install guide](https://docs.anthropic.com/en/docs/claude-code))

---

## Quick Start (5 Minutes)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ai-employee.git
cd ai-employee
```

### 2. Install Python Dependencies

```bash
cd ai_employee_scripts
uv sync
```

This installs all required packages defined in `pyproject.toml`.

### 3. Set Up Environment Variables

Create a `.env` file in `ai_employee_scripts/`:

```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
nano .env
```

**Required variables for basic operation:**
```bash
# Gmail (for email operations)
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret

# LinkedIn API (for posting)
LINKEDIN_ACCESS_TOKEN=your-access-token
LINKEDIN_CLIENT_ID=your-client-id
LINKEDIN_CLIENT_SECRET=your-client-secret

# Meta (Facebook/Instagram)
META_ACCESS_TOKEN=your-access-token
META_PAGE_ID=your-page-id

# Twitter/X
X_API_KEY=your-api-key
X_API_SECRET=your-api-secret
X_ACCESS_TOKEN=your-access-token
X_ACCESS_TOKEN_SECRET=your-access-token-secret

# Odoo Accounting
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=your-email@example.com
ODOO_PASSWORD=your-password

# OpenAI (optional, for cloud agents)
OPENAI_API_KEY=your-openai-api-key
```

### 4. Set Up Gmail OAuth

```bash
# Run the token refresh script
cd ai_employee_scripts
uv run python refresh_gmail_mcp_token.py
```

Follow the prompts to authenticate with Google.

### 5. Run the Orchestrator

```bash
cd ai_employee_scripts
uv run python orchestrator.py
```

This starts the main orchestrator and all watchers.

---

## Full Installation Guide

### Step 1: System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.13 | 3.13+ |
| RAM | 2GB | 4GB+ |
| Disk Space | 500MB | 1GB+ |
| OS | Linux/WSL/macOS | Ubuntu 22.04 / WSL2 |

### Step 2: Install UV Package Manager

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

### Step 3: Install Node.js and PM2 (for 24/7 operation)

```bash
# Install Node.js (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 globally
npm install -g pm2
```

### Step 4: Project Structure Setup

```bash
# Navigate to project
cd ai-employee

# Install Python dependencies
cd ai_employee_scripts
uv sync

# Create required directories
mkdir -p logs
```

### Step 5: Configure MCP Servers

The MCP servers are configured in `.claude/settings.local.json`. This file is already set up with all 6 MCP servers.

**No additional configuration needed** - UV handles the Python environment automatically.

### Step 6: Set Up API Credentials

#### Gmail Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `credentials.json` to `ai_employee_scripts/`
6. Run: `uv run python refresh_gmail_mcp_token.py`

#### LinkedIn Setup

1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Create an app
3. Request Marketing API access
4. Generate access token
5. Add to `.env`: `LINKEDIN_ACCESS_TOKEN`

#### Meta (Facebook/Instagram) Setup

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a Facebook App
3. Add Facebook Login and Instagram Graph API
4. Generate a long-lived Page access token
5. Add to `.env`: `META_ACCESS_TOKEN` and `META_PAGE_ID`

#### Twitter/X Setup

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a project and app
3. Generate API keys and access tokens
4. Add to `.env`: `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`
5. **Note:** You need API credits (402 Payment Required) to post

#### Odoo Setup

1. Install Odoo or use an existing instance
2. Create a user with API access
3. Add to `.env`: `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD`

---

## Verify Installation

### Check Python Environment

```bash
cd ai_employee_scripts
uv run python -c "import google; import playwright; print('All dependencies installed')"
```

### Check MCP Servers

```bash
# Test Gmail MCP
uv run python mcp_servers/gmail_mcp.py

# You should see: "Gmail MCP Server starting..."
```

### Check Watchers

```bash
# Start File System Watcher (Ctrl+C to stop)
uv run python watchers/filesystem_watcher.py
```

### Check Vault Structure

```bash
ls -la AI_Employee_Vault/
```

Expected folders:
- `Inbox/`
- `Needs_Action/`
- `Pending_Approval/`
- `Approved/`
- `Rejected/`
- `Done/`
- `Logs/`
- `Content_To_Post/`

---

## Running the System

### Development Mode

Run individual components for testing:

```bash
# Run specific watcher
uv run python watchers/gmail_watcher.py

# Run orchestrator (manages all watchers)
uv run python orchestrator.py

# Run cloud orchestrator
uv run python cloud/cloud_orchestrator.py
```

### Production Mode (PM2)

```bash
# Start with PM2
pm2 start ecosystem.local.config.js

# Save PM2 configuration
pm2 save

# Enable startup on boot
pm2 startup
```

---

## Using Agent Skills

Agent skills are invoked through Claude Code CLI:

```bash
# Check pending tasks
claude code -p "/check-tasks"

# Process a file
claude code -p "/process-file"

# Generate social media posts
claude code -p "/linkedin-posting"
claude code -p "/meta-posting"
claude code -p "/twitter-posting"

# Check accounting
claude code -p "/check-accounting"

# Generate weekly briefing
claude code -p "/weekly-audit"
```

---

## Next Steps

- Read [Project Architecture](PROJECT_ARCHITECTURE.md) for system overview
- Read [Agent Skills Reference](AGENT_SKILLS_REFERENCE.md) for all available skills
- Read [Configuration Reference](CONFIGURATION_REFERENCE.md) for detailed settings
- Read [PM2 Setup Guide](PM2_SETUP_GUIDE.md) for 24/7 operation

---

## Troubleshooting

### "uv: command not found"

Install UV:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "credentials.json not found"

Download OAuth credentials from Google Cloud Console and place in `ai_employee_scripts/`.

### "Token refresh failed"

Run the token refresh script:
```bash
uv run python refresh_gmail_mcp_token.py
```

### "Permission denied" errors

Make scripts executable:
```bash
chmod +x ai_employee_scripts/*.py
```

---

## Getting Help

- Check [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)
- Review logs in `AI_Employee_Vault/Logs/`
- Check PM2 logs: `pm2 logs ai-employee-local`

---

*Generated: 2026-03-14*
*AI Employee Project - Platinum Tier Documentation*