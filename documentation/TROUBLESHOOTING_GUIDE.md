# Troubleshooting Guide

This guide covers common issues and their solutions for the AI Employee.

---

## Quick Diagnostics

### Check System Status

```bash
# Check if orchestrator is running
ps aux | grep orchestrator | grep -v grep

# Check if watchers are running
ps aux | grep watcher | grep -v grep

# Check PM2 status
pm2 status

# Check recent logs
tail -50 AI_Employee_Vault/Logs/$(date +%Y-%m-%d)_orchestrator.log
```

### Check Logs

```bash
# Orchestrator logs
tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d)_orchestrator.log

# PM2 logs
pm2 logs ai-employee-local --lines 100

# Cron logs
tail -f AI_Employee_Vault/Logs/cron.log

# Vault sync logs
tail -f AI_Employee_Vault/Logs/vault_sync.log
```

---

## Common Issues

### 1. Watcher Not Starting

**Symptoms:**
- `ps aux | grep watcher` shows no process
- PM2 shows `errored` status

**Diagnosis:**
```bash
# Check Python path
which python3

# Check UV installation
uv --version

# Try running watcher directly
cd ai_employee_scripts
uv run python watchers/filesystem_watcher.py
```

**Solutions:**
1. **Missing dependencies:**
   ```bash
   cd ai_employee_scripts
   uv sync
   ```

2. **Invalid Python path in PM2 config:**
   - Update `interpreter` path in `ecosystem.local.config.js`

3. **Permission errors:**
   ```bash
   chmod +x ai_employee_scripts/watchers/*.py
   ```

---

### 2. MCP Server Not Responding

**Symptoms:**
- "MCP server not found" error
- Tool calls timeout
- "Connection refused" error

**Diagnosis:**
```bash
# Test MCP server directly
cd ai_employee_scripts
uv run python mcp_servers/gmail_mcp.py
```

**Solutions:**
1. **Check MCP configuration:**
   - Verify paths in `AI_Employee_Vault/.mcp.json`
   - Ensure `PYTHONPATH` is set correctly

2. **Check dependencies:**
   ```bash
   uv sync
   ```

3. **Restart Claude Code:**
   - Exit and restart Claude Code CLI

---

### 3. Gmail Authentication Failed

**Symptoms:**
- "credentials.json not found"
- "Token refresh failed"
- 401 Unauthorized error

**Diagnosis:**
```bash
# Check credentials file
ls -la ai_employee_scripts/credentials.json

# Check token file
ls -la ai_employee_scripts/token_gmail.json
```

**Solutions:**
1. **Missing credentials:**
   - Download `credentials.json` from Google Cloud Console
   - Place in `ai_employee_scripts/`

2. **Expired token:**
   ```bash
   cd ai_employee_scripts
   uv run python refresh_gmail_mcp_token.py
   ```

3. **Revoked access:**
   - Go to Google Account settings → Security → Third-party apps
   - Remove access and re-authorize

---

### 4. LinkedIn API Not Working

**Symptoms:**
- "Invalid access token"
- 403 Forbidden error

**Solutions:**
1. **Expired token:**
   - Generate new token from LinkedIn Developer Portal
   - Update `LINKEDIN_ACCESS_TOKEN` in `.env`

2. **Insufficient permissions:**
   - Request required scopes: `w_member_social`, `r_liteprofile`
   - Wait for LinkedIn approval

3. **API limits exceeded:**
   - Check usage in LinkedIn Developer Portal

---

### 5. Twitter Posting Failed (402 Payment Required)

**Symptoms:**
- `402 Payment Required` error when posting

**Cause:**
- X API requires paid credits for posting

**Solution:**
- Add credits at https://developer.x.com
- This is a Twitter/X policy, not a code issue

---

### 6. Odoo Connection Failed

**Symptoms:**
- "Connection refused"
- "Invalid database"
- 401 Unauthorized

**Diagnosis:**
```bash
# Test Odoo connection
curl http://localhost:8069/web/database/list
```

**Solutions:**
1. **Odoo not running:**
   ```bash
   # Start Odoo (Docker)
   docker start odoo

   # Or start manually
   ./odoo-bin -c odoo.conf
   ```

2. **Wrong credentials:**
   - Check `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD` in `.env`

3. **Database doesn't exist:**
   - Create database in Odoo manager

---

### 7. PM2 Keeps Restarting

**Symptoms:**
- `pm2 status` shows high restart count
- Process status: `errored` or `stopped`

**Diagnosis:**
```bash
# Check error logs
pm2 logs ai-employee-local --err --lines 50
```

**Solutions:**
1. **Code error:**
   - Fix the error in logs
   - Restart: `pm2 restart ai-employee-local`

2. **Memory limit:**
   - Increase `max_memory_restart` in config

3. **Missing environment:**
   - Check `.env` file exists
   - Check PYTHONPATH is correct

---

### 8. Vault Sync Failing

**Symptoms:**
- "Not a git repository"
- "Push rejected"
- "Authentication failed"

**Diagnosis:**
```bash
# Test sync
cd ai_employee_scripts
uv run python vault_sync.py --dry-run
```

**Solutions:**
1. **Not a git repo:**
   ```bash
   git init
   git remote add origin <your-repo-url>
   ```

2. **Authentication:**
   ```bash
   # Set up SSH key
   ssh-keygen -t ed25519
   cat ~/.ssh/id_ed25519.pub  # Add to GitHub
   ```

3. **Merge conflicts:**
   ```bash
   git status  # See conflicts
   # Resolve and commit
   ```

---

### 9. Duplicate Email Processing

**Symptoms:**
- Same email processed multiple times
- Duplicate action files created

**Cause:**
- Vault sync not running
- Processed IDs file not shared

**Solution:**
1. **Enable vault sync:**
   ```bash
   # Set up cron
   */5 * * * * cd /path/to/ai_employee_scripts && uv run python vault_sync.py
   ```

2. **Check shared state:**
   - Verify `Logs/gmail_processed_ids.json` exists
   - Ensure git is syncing this file

---

### 10. Ralph Wiggum Hook Blocking Exit

**Symptoms:**
- Claude won't exit
- "Pending tasks remain" message

**Cause:**
- Files in `Needs_Action/` folder

**Solutions:**
1. **Process pending tasks:**
   ```bash
   claude code -p "/check-tasks"
   claude code -p "/process-file"
   ```

2. **Emergency bypass:**
   ```bash
   touch AI_Employee_Vault/stop_ralph
   ```

---

## Error Reference

### HTTP Errors

| Code | Description | Solution |
|------|-------------|----------|
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Refresh credentials/token |
| 402 | Payment Required | Add API credits (Twitter) |
| 403 | Forbidden | Check permissions/scopes |
| 404 | Not Found | Check resource ID |
| 429 | Rate Limited | Wait and retry |
| 500 | Server Error | Retry later |
| 503 | Service Unavailable | Check service status |

### Python Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Missing dependency | Run `uv sync` |
| `PermissionError` | File permissions | Check file permissions |
| `FileNotFoundError` | Missing file | Check path or create file |
| `ConnectionError` | Network issue | Check network/firewall |
| `TimeoutError` | Request timeout | Increase timeout or retry |

---

## Debug Mode

### Enable Debug Logging

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Run with debug
cd ai_employee_scripts
LOG_LEVEL=DEBUG uv run python orchestrator.py
```

### Test Individual Components

```bash
# Test Gmail MCP
uv run python mcp_servers/gmail_mcp.py

# Test Gmail Watcher
uv run python watchers/gmail_watcher.py

# Test Cloud Agent
uv run python cloud/test_cloud_agent.py
```

---

## Recovery Procedures

### Reset Orchestrator State

```bash
# Stop orchestrator
pm2 stop ai-employee-local

# Clear state
rm AI_Employee_Vault/Logs/orchestrator_state.json

# Restart
pm2 restart ai-employee-local
```

### Reset Gmail Processed IDs

```bash
# WARNING: This will re-process all emails
rm AI_Employee_Vault/Logs/gmail_processed_ids.json
```

### Clean Up Failed Queue

```bash
# Move all failed items back to Needs_Action
mv AI_Employee_Vault/Failed_Queue/* AI_Employee_Vault/Needs_Action/
```

---

## Getting Help

1. **Check logs first:**
   - `AI_Employee_Vault/Logs/`
   - `pm2 logs`

2. **Search documentation:**
   - [Getting Started](GETTING_STARTED.md)
   - [Configuration Reference](CONFIGURATION_REFERENCE.md)

3. **Create an issue:**
   - Include logs
   - Include error messages
   - Include steps to reproduce

---

## Related Documentation

- [Getting Started Guide](GETTING_STARTED.md)
- [Configuration Reference](CONFIGURATION_REFERENCE.md)
- [Security & Credentials Guide](SECURITY_CREDENTIALS_GUIDE.md)

---

*Generated: 2026-03-14*
*AI Employee Project - Platinum Tier Documentation*