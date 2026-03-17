# PM2 Setup Guide

PM2 (Process Manager 2) keeps your watcher scripts running 24/7. It's a production-grade process manager that acts as a watchdog for your AI Employee.

---

## Why PM2?

| Problem | Without PM2 | With PM2 |
|---------|-------------|----------|
| Session closes | Script dies | ✅ Auto-restarts |
| Unhandled exception | Script exits | ✅ Auto-restarts |
| System reboot | Manual restart | ✅ Auto-starts on boot |
| Logging | Lost output | ✅ Captures logs |
| Monitoring | Manual checks | ✅ `pm2 status` |

---

## Installation

```bash
# Install Node.js (if not installed)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 globally
npm install -g pm2

# Verify installation
pm2 --version
```

---

## Configuration Files

### Local Configuration

**File:** `ai_employee_scripts/ecosystem.local.config.js`

```javascript
module.exports = {
  apps: [{
    name: 'ai-employee-local',

    // Script to run (watchdog monitors orchestrator)
    script: 'watchdog.py',

    // Use UV virtual environment Python
    interpreter: '/path/to/ai-employee/ai_employee_scripts/.venv/bin/python',

    // Working directory
    cwd: '/path/to/ai-employee/ai_employee_scripts',

    // Auto-restart configuration
    watch: false,
    autorestart: true,
    max_restarts: 10,
    min_uptime: '10s',

    // Logging
    error_file: './logs/local-err.log',
    out_file: './logs/local-out.log',
    log_file: './logs/local-combined.log',
    time: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',

    // Process management
    instances: 1,
    exec_mode: 'fork',

    // Memory and CPU limits
    max_memory_restart: '1G',
    kill_timeout: 5000,
    wait_ready: true,
  }]
};
```

### Cloud Configuration

**File:** `ai_employee_scripts/ecosystem.cloud.config.js`

Used for cloud deployment (Oracle VM, etc.). Same structure but runs `cloud/cloud_orchestrator.py`.

---

## Architecture

### Local Architecture

```
PM2 → watchdog.py → orchestrator.py → watchers (gmail, linkedin, etc)
```

**Flow:**
1. PM2 starts `watchdog.py`
2. Watchdog starts `orchestrator.py` as subprocess
3. Orchestrator starts all watchers
4. PM2 monitors watchdog and restarts if it crashes
5. Watchdog monitors orchestrator and restarts if it crashes

### Cloud Architecture

```
PM2 → cloud_orchestrator.py → cloud_watchers (built-in)
```

**Flow:**
1. PM2 starts `cloud_orchestrator.py`
2. Cloud orchestrator starts cloud watchers as subprocesses
3. Built-in health checks and auto-restart

---

## Quick Start

### Step 1: Update Paths

Edit `ecosystem.local.config.js` and update paths:

```javascript
// Update these paths to match your setup
interpreter: '/your/path/to/ai-employee/ai_employee_scripts/.venv/bin/python',
cwd: '/your/path/to/ai-employee/ai_employee_scripts',
```

### Step 2: Create Logs Directory

```bash
cd ai_employee_scripts
mkdir -p logs
```

### Step 3: Start PM2

```bash
cd ai_employee_scripts
pm2 start ecosystem.local.config.js
```

### Step 4: Save Configuration

```bash
# Save current PM2 configuration
pm2 save

# Enable startup on boot
pm2 startup
```

**Copy and run the command PM2 outputs** to enable auto-start on system boot.

---

## PM2 Commands

### Basic Commands

```bash
# Check status
pm2 status

# View logs
pm2 logs ai-employee-local

# Follow logs (live)
pm2 logs ai-employee-local --lines 100

# Restart
pm2 restart ai-employee-local

# Stop
pm2 stop ai-employee-local

# Delete from PM2
pm2 delete ai-employee-local
```

### Monitoring

```bash
# Real-time monitoring dashboard
pm2 monit

# Process details
pm2 show ai-employee-local

# CPU/Memory usage
pm2 list
```

### Log Management

```bash
# View error logs
pm2 logs ai-employee-local --err

# View output logs
pm2 logs ai-employee-local --out

# Flush all logs
pm2 flush

# Reload logs
pm2 reloadLogs
```

---

## Log Locations

| Log Type | Location |
|----------|----------|
| PM2 output | `ai_employee_scripts/logs/local-out.log` |
| PM2 error | `ai_employee_scripts/logs/local-err.log` |
| PM2 combined | `ai_employee_scripts/logs/local-combined.log` |
| Orchestrator | `AI_Employee_Vault/Logs/YYYY-MM-DD_orchestrator.log` |
| Watchers | `AI_Employee_Vault/Logs/<WatcherName>.log` |

---

## Startup Script

PM2 can auto-start your processes on system boot:

```bash
# Generate startup script
pm2 startup

# Output example:
# sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u username --hp /home/username
```

Run the command it outputs, then:

```bash
pm2 save
```

---

## Testing PM2

### Verify Installation

```bash
pm2 status
```

Expected output:
```
┌─────┬──────────────────────┬─────────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┬──────────┐
│ id  │ name                 │ mode        │ ↺       │ status  │ cpu      │ mem    │ user │ watching  │ pid      │
├─────┼──────────────────────┼─────────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┼──────────┤
│ 0   │ ai-employee-local    │ fork        │ 0       │ online  │ 0%       │ 45.2mb │ user │ disabled  │ 12345    │
└─────┴──────────────────────┴─────────────┴─────────┴─────────┴──────────┴────────┴──────┴───────────┴──────────┘
```

### Test Auto-Restart

```bash
# Kill the process manually
pkill -f watchdog

# Wait 10 seconds
sleep 10

# Check if PM2 restarted it
pm2 status
```

The status should still show `online` with `↺` (restarts) count increased.

### Test Processing

1. Drop a file in `Drop_Zone/`
2. Check PM2 logs: `pm2 logs ai-employee-local`
3. Verify file processed and moved to `Done/`

---

## Troubleshooting

### Process keeps restarting

**Check logs:**
```bash
pm2 logs ai-employee-local --err --lines 50
```

**Common causes:**
- Missing dependencies: Run `uv sync`
- Invalid path in config: Update `interpreter` and `cwd`
- Permission errors: Check file permissions

### Python not found

Update the `interpreter` path in config:
```bash
# Find your Python path
which python3

# Or use UV's venv
ls ai_employee_scripts/.venv/bin/python
```

### Logs not appearing

```bash
# Create logs directory
mkdir -p ai_employee_scripts/logs

# Restart PM2
pm2 restart ai-employee-local
```

### Port already in use

PM2 uses ports for its API. Check if already running:
```bash
pm2 list
pm2 kill  # Stop all PM2 processes
pm2 start ecosystem.local.config.js
```

---

## Advanced Configuration

### Environment Variables

Add to `ecosystem.local.config.js`:

```javascript
env: {
  NODE_ENV: 'production',
  MY_CUSTOM_VAR: 'value',
}
```

### Resource Limits

```javascript
// Memory limit (restart if exceeded)
max_memory_restart: '1G',

// CPU limit (not hard limit, but monitored)
cpu_max: 80,  // 80% CPU

// Graceful shutdown timeout
kill_timeout: 5000,  // 5 seconds

// Minimum uptime before considering stable
min_uptime: '10s',
```

### Restart Policy

```javascript
// Maximum restarts within min_uptime
max_restarts: 10,

// Restart delay
restart_delay: 1000,  // 1 second

// Auto-restart on file changes (not recommended for production)
watch: false,
```

---

## Monitoring with PM2 Plus (Optional)

PM2 offers a cloud monitoring dashboard:

```bash
# Link to PM2 Plus
pm2 link <secret_key> <public_key>
```

Visit [pm2.io](https://pm2.io/) for more details.

---

## Uninstalling PM2

```bash
# Stop and delete all processes
pm2 delete all

# Disable startup
pm2 unstartup

# Remove PM2
npm remove -g pm2
```

---

## Related Documentation

- [Vault Sync Setup Guide](VAULT_SYNC_SETUP_GUIDE.md)
- [Cloud Deployment Guide](CLOUD_DEPLOYMENT_GUIDE.md)
- [Getting Started Guide](GETTING_STARTED.md)

---

*Generated: 2026-03-14*
*AI Employee Project - Platinum Tier Documentation*