# Vault Sync Setup Guide

The Vault Sync script (`vault_sync.py`) automatically syncs the `AI_Employee_Vault` between local and cloud via Git. This is essential for Platinum tier deployment where both local and cloud instances need to share state.

---

## Purpose

**Problem:** When running both local and cloud watchers, duplicate email processing can occur.

**Solution:** Git-based state sync ensures both instances see the same processed email IDs.

**How it works:**
```
1. Cloud watcher processes email → saves ID to gmail_processed_ids.json
2. Git push → local pulls
3. Local watcher loads same state file → skips already processed emails
4. No duplicates!
```

---

## Prerequisites

- Git installed and configured
- GitHub (or other Git hosting) repository
- SSH key or HTTPS credentials for push access

---

## Quick Start

### Step 1: Initialize Git (if not already)

```bash
cd /path/to/ai-employee
git init
git remote add origin https://github.com/your-username/ai-employee.git
```

### Step 2: Create .gitignore

Ensure sensitive files are not committed:

```bash
# Add to .gitignore
cat >> .gitignore << EOF
# Credentials
ai_employee_scripts/credentials.json
ai_employee_scripts/token_*.json
ai_employee_scripts/.env

# Logs (optional - you may want to sync these)
# AI_Employee_Vault/Logs/

# Python
__pycache__/
*.pyc
.venv/
EOF
```

### Step 3: Initial Commit

```bash
git add .
git commit -m "Initial commit"
git push -u origin main
```

### Step 4: Test Vault Sync

```bash
cd ai_employee_scripts

# Dry run (test without making changes)
uv run python vault_sync.py --dry-run
```

Expected output:
```
============================================================
DRY RUN MODE - No changes will be made
============================================================
[2026-03-14 10:00:00] Pulling changes...
[DRY RUN] Would execute: git fetch
[DRY RUN] Would execute: git rebase origin/main
[2026-03-14 10:00:01] Pull successful
[2026-03-14 10:00:01] No local changes to push
```

### Step 5: Run Once (for real)

```bash
uv run python vault_sync.py
```

---

## Cron Setup

### Local Machine

```bash
# Edit crontab
crontab -e

# Add this line (runs every 5 minutes)
*/5 * * * * cd "/path/to/ai-employee/ai_employee_scripts" && uv run python vault_sync.py >> /path/to/ai-employee/AI_Employee_Vault/Logs/vault_sync.log 2>&1
```

### Cloud VM

```bash
# Edit crontab
crontab -e

# Add this line (runs every 5 minutes)
*/5 * * * * cd "/home/user/ai-employee/ai_employee_scripts" && uv run python vault_sync.py >> /home/user/ai-employee/AI_Employee_Vault/Logs/vault_sync.log 2>&1
```

---

## Usage

### Command Line Options

```bash
# Run once (default for cron)
uv run python vault_sync.py

# Test without making changes
uv run python vault_sync.py --dry-run

# Run as continuous daemon
uv run python vault_sync.py --daemon

# Run once and exit (same as no args)
uv run python vault_sync.py --once
```

### Daemon Mode

Run continuously with a configurable interval:

```bash
uv run python vault_sync.py --daemon
```

Output:
```
[2026-03-14 10:00:00] Vault sync daemon starting...
[2026-03-14 10:00:00] Sync interval: 300s
[2026-03-14 10:00:00] Vault path: /path/to/AI_Employee_Vault
[2026-03-14 10:00:00] Press Ctrl+C to stop

[2026-03-14 10:00:00] Pulling changes...
[2026-03-14 10:00:01] Pull successful
[2026-03-14 10:00:01] No local changes to push
[2026-03-14 10:00:01] Waiting 300s until next sync...
```

---

## How It Works

### Sync Flow

```
┌─────────────────────────────────────┐
│  1. Pull Changes                    │
│  - git fetch                        │
│  - git rebase origin/main           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. Check Local Changes             │
│  - git status --porcelain           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. Push if Changes                 │
│  - git add -A                       │
│  - git commit -m "Auto-sync: ..."   │
│  - git push                         │
└─────────────────────────────────────┘
```

### Shared State File

**Location:** `AI_Employee_Vault/Logs/gmail_processed_ids.json`

**Format:**
```json
{
  "processed_ids": [
    "message_id_1",
    "message_id_2",
    ...
  ],
  "last_updated": "2026-03-14T10:00:00"
}
```

Both local and cloud watchers read/write to this same file, ensuring no duplicate processing.

---

## Configuration

### Environment Variables

None required - paths are auto-detected relative to script location.

### Customization

Edit `vault_sync.py` to customize:

```python
# Sync interval (default: 5 minutes)
SYNC_INTERVAL = 300  # seconds

# Commit message format
COMMIT_MESSAGE = "Auto-sync: Update vault {timestamp}"
```

---

## Troubleshooting

### "Not a git repository"

Initialize git first:
```bash
cd /path/to/ai-employee
git init
git remote add origin <your-repo-url>
```

### "Push rejected (non-fast-forward)"

Force sync:
```bash
# Pull with rebase
git pull --rebase origin main

# Or reset to remote (WARNING: loses local changes)
git fetch origin
git reset --hard origin/main
```

### "Authentication failed"

Set up SSH keys or use HTTPS with credentials:
```bash
# Option 1: SSH
git remote set-url origin git@github.com:username/ai-employee.git

# Option 2: HTTPS with credential cache
git config --global credential.helper cache
```

### "Merge conflicts"

The script aborts rebase on conflicts. Resolve manually:
```bash
cd /path/to/ai-employee
git status  # See conflicted files
# Edit files to resolve conflicts
git add .
git rebase --continue
```

### Rebase keeps failing

Switch to merge strategy:
```bash
# In vault_sync.py, change rebase to merge
# Replace: git_cmd(["git", "rebase", "origin/main"])
# With: git_cmd(["git", "merge", "origin/main"])
```

---

## Best Practices

### Commit Frequency

- **Recommended:** Every 5 minutes (default)
- **Minimum:** Every 1 minute (higher load)
- **Maximum:** Every 15 minutes (more staleness)

### Branch Strategy

- Use `main` branch for production
- Create feature branches for major changes
- The sync script always syncs with `origin/main`

### Monitoring

Check the log file periodically:
```bash
tail -f AI_Employee_Vault/Logs/vault_sync.log
```

---

## Security Considerations

### What Gets Synced

**Synced:**
- Processed email IDs
- Task files (Done, Needs_Action)
- Dashboard.md
- Briefings
- Content_To_Post

**NOT Synced (add to .gitignore):**
- `credentials.json`
- `token_*.json`
- `.env` files
- OAuth tokens

### Recommended .gitignore

```gitignore
# Credentials - NEVER COMMIT
ai_employee_scripts/credentials.json
ai_employee_scripts/token_*.json
ai_employee_scripts/.env
ai_employee_scripts/.env.*

# Session files
sessions/

# OS files
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
```

---

## Alternative: Syncthing

For real-time sync without Git, consider [Syncthing](https://syncthing.net/):

**Pros:**
- Real-time sync
- No Git overhead
- P2P (no cloud needed)

**Cons:**
- More complex setup
- Requires both machines online
- No version history

---

## Related Documentation

- [PM2 Setup Guide](PM2_SETUP_GUIDE.md)
- [Cloud Deployment Guide](CLOUD_DEPLOYMENT_GUIDE.md)
- [Getting Started Guide](GETTING_STARTED.md)

---

*Generated: 2026-03-14*
*AI Employee Project - Platinum Tier Documentation*