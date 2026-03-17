# Cloud Deployment Guide

This guide covers deploying the AI Employee to a cloud VM for 24/7 operation (Platinum Tier).

---

## Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLOUD VM (24/7)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PM2 → cloud_orchestrator.py → cloud_watchers                  │
│                                      │                          │
│                                      ▼                          │
│                          AI_Employee_Vault                     │
│                                      │                          │
│                                      ▼                          │
│                          vault_sync.py (cron)                  │
│                                      │                          │
│                                      ▼                          │
│                              Git Sync                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Git Push/Pull
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        LOCAL MACHINE                           │
│                                                                 │
│  PM2 → watchdog.py → orchestrator.py → watchers               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Purpose | Location |
|-----------|---------|----------|
| `cloud_orchestrator.py` | Main orchestrator for cloud | `cloud/` |
| `cloud_watchers/` | Cloud-specific watchers | `cloud_watchers/` |
| `odoo_server.py` | Cloud MCP server (read-only) | `cloud/mcp_servers/` |
| `vault_sync.py` | Git-based vault sync | `ai_employee_scripts/` |
| `ecosystem.cloud.config.js` | PM2 config for cloud | `ai_employee_scripts/` |

---

## Prerequisites

### Cloud Provider

Recommended providers:
- **Oracle Cloud** (Free Tier: 4 ARM CPUs, 24GB RAM)
- **AWS EC2** (t3.micro free tier)
- **Google Cloud** (e2-micro free tier)
- **DigitalOcean** ($4-6/month)

### Requirements

- Ubuntu 22.04 or similar
- Python 3.13+
- Git
- Node.js 18+ (for PM2)
- At least 1GB RAM

---

## Step 1: Provision Cloud VM

### Oracle Cloud (Free Tier)

1. Create Oracle Cloud account
2. Create Compute Instance:
   - Shape: VM.Standard.E2.1.Micro (Free Tier)
   - OS: Ubuntu 22.04
   - SSH key: Upload your public key
3. Note the public IP

### AWS EC2 (Free Tier)

1. Launch EC2 instance:
   - AMI: Ubuntu 22.04 LTS
   - Instance type: t3.micro
   - Key pair: Create or select existing
2. Configure security group:
   - SSH (22) from your IP
3. Launch and note the public IP

---

## Step 2: Connect to VM

```bash
# SSH into your VM
ssh ubuntu@<your-vm-ip>

# Update system
sudo apt update && sudo apt upgrade -y
```

---

## Step 3: Install Dependencies

```bash
# Install Python 3.13
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install python3.13 python3.13-venv python3.13-dev -y

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Install Git
sudo apt install git -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install PM2
sudo npm install -g pm2
```

---

## Step 4: Clone Repository

```bash
# Clone your repository
git clone https://github.com/your-username/ai-employee.git
cd ai-employee
```

---

## Step 5: Configure Environment

### Create .env File

```bash
cd ai_employee_scripts

# Create .env from template
cat > .env << 'EOF'
# Gmail (for cloud watchers)
GOOGLE_CREDENTIALS={"type":"service_account",...}

# LinkedIn
LINKEDIN_ACCESS_TOKEN=your-token
LINKEDIN_CLIENT_ID=your-client-id
LINKEDIN_CLIENT_SECRET=your-client-secret

# Meta
META_ACCESS_TOKEN=your-token
META_PAGE_ID=your-page-id

# Twitter
X_API_KEY=your-key
X_API_SECRET=your-secret
X_ACCESS_TOKEN=your-token
X_ACCESS_TOKEN_SECRET=your-secret

# Odoo
ODOO_URL=http://your-odoo-instance:8069
ODOO_DB=odoo
ODOO_USER=your-email@example.com
ODOO_PASSWORD=your-password

# OpenAI (for cloud agents)
OPENAI_API_KEY=your-openai-key
EOF
```

**Important:** For Gmail cloud watcher, use `GOOGLE_CREDENTIALS` environment variable with the JSON credentials.

### Install Python Dependencies

```bash
cd ai_employee_scripts
uv sync
```

---

## Step 6: Configure PM2

### Update Paths in Config

```bash
# Edit the cloud config file
nano ecosystem.cloud.config.js
```

Update paths to match your VM:

```javascript
module.exports = {
  apps: [{
    name: 'ai-employee-cloud',
    script: 'cloud/cloud_orchestrator.py',
    interpreter: '/home/ubuntu/ai-employee/ai_employee_scripts/.venv/bin/python',
    cwd: '/home/ubuntu/ai-employee/ai_employee_scripts',
    // ... rest of config
  }]
};
```

### Create Logs Directory

```bash
mkdir -p logs
```

---

## Step 7: Start Cloud Orchestrator

```bash
cd ai_employee_scripts

# Start with PM2
pm2 start ecosystem.cloud.config.js

# Save configuration
pm2 save

# Enable startup on boot
pm2 startup
```

---

## Step 8: Set Up Vault Sync

```bash
# Set up cron for vault sync
crontab -e

# Add this line (every 5 minutes)
*/5 * * * * cd /home/ubuntu/ai-employee/ai_employee_scripts && /home/ubuntu/.local/bin/uv run python vault_sync.py >> /home/ubuntu/ai-employee/AI_Employee_Vault/Logs/vault_sync.log 2>&1
```

---

## Step 9: Verify Deployment

### Check PM2 Status

```bash
pm2 status
```

Expected output:
```
┌─────┬──────────────────────┬─────────────┬─────────┬─────────┐
│ id  │ name                 │ mode        │ status  │ cpu     │
├─────┼──────────────────────┼─────────────┼─────────┼─────────┤
│ 0   │ ai-employee-cloud    │ fork        │ online  │ 0%      │
└─────┴──────────────────────┴─────────────┴─────────┴─────────┘
```

### Check Logs

```bash
pm2 logs ai-employee-cloud --lines 50
```

### Check Vault Sync

```bash
# Run once to test
cd ai_employee_scripts
uv run python vault_sync.py --dry-run
```

---

## Cloud Agents (Optional)

The cloud deployment includes OpenAI Agents SDK-based agents for autonomous task processing.

### Agent Architecture

| Agent | Purpose | MCP Integration |
|-------|---------|-----------------|
| TriageAgent | Routes tasks to specialists | Attaches MCP to specialists |
| EmailAgent | Email processing | None |
| SocialAgent | Social media management | None |
| FinanceAgent | Accounting/invoicing | Odoo MCP (read-only) |

### Testing Cloud Agents

```bash
cd ai_employee_scripts
uv run python cloud/test_cloud_agent.py
```

---

## Monitoring

### PM2 Monitoring

```bash
# Real-time dashboard
pm2 monit

# Process details
pm2 show ai-employee-cloud
```

### Log Monitoring

```bash
# Follow logs
pm2 logs ai-employee-cloud

# Check orchestrator logs
tail -f AI_Employee_Vault/Logs/YYYY-MM-DD_orchestrator.log
```

### Health Checks

```bash
# Check if orchestrator is running
ps aux | grep cloud_orchestrator

# Check if watchers are running
ps aux | grep watcher
```

---

## Troubleshooting

### VM Not Accessible

1. Check security group/firewall rules
2. Verify SSH key permissions: `chmod 600 ~/.ssh/key.pem`
3. Check VM status in cloud console

### PM2 Not Starting

1. Check logs: `pm2 logs ai-employee-cloud --err`
2. Verify Python path: `which python3.13`
3. Check dependencies: `uv sync`

### Git Sync Failing

1. Check credentials: `git config --list`
2. Set up SSH key for GitHub:
   ```bash
   ssh-keygen -t ed25519 -C "your-email@example.com"
   cat ~/.ssh/id_ed25519.pub  # Add to GitHub
   ```
3. Update remote URL: `git remote set-url origin git@github.com:username/ai-employee.git`

### Gmail Cloud Watcher Not Working

1. Verify `GOOGLE_CREDENTIALS` in `.env`
2. Check JSON format (must be single-line or properly escaped)
3. Test credentials:
   ```bash
   uv run python cloud_watchers/gmail_watcher.py
   ```

---

## Cost Optimization

### Free Tier Limits

| Provider | Free Tier | Limits |
|----------|-----------|--------|
| Oracle Cloud | Always Free | 4 ARM CPUs, 24GB RAM |
| AWS EC2 | 12 months | 750 hours/month t3.micro |
| Google Cloud | Always Free | e2-micro (US regions) |

### Tips

1. **Use Oracle Free Tier** - Most generous free tier
2. **Schedule non-critical tasks** - Reduce compute during off-hours
3. **Monitor usage** - Set up billing alerts
4. **Clean up logs** - Delete old logs to save disk space

---

## Security

### Firewall Rules

```bash
# Only allow SSH from your IP
sudo ufw allow from YOUR_IP to any port 22
sudo ufw enable
```

### SSH Hardening

Edit `/etc/ssh/sshd_config`:
```
PermitRootLogin no
PasswordAuthentication no
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

### Regular Updates

```bash
# Update system weekly
sudo apt update && sudo apt upgrade -y
```

---

## Related Documentation

- [PM2 Setup Guide](PM2_SETUP_GUIDE.md)
- [Vault Sync Setup Guide](VAULT_SYNC_SETUP_GUIDE.md)
- [Cloud Agents Guide](CLOUD_AGENTS_GUIDE.md)
- [Security & Credentials Guide](SECURITY_CREDENTIALS_GUIDE.md)

---

*Generated: 2026-03-14*
*AI Employee Project - Platinum Tier Documentation*