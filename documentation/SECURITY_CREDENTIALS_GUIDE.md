# Security & Credentials Guide

This guide covers credential management, security best practices, and sensitive data handling for the AI Employee.

---

## Overview

The AI Employee handles sensitive credentials for:
- Email (Gmail)
- Social Media (LinkedIn, Facebook, Instagram, Twitter)
- Accounting (Odoo)
- AI Services (OpenAI)

**Critical Rule:** Never commit credentials to git.

---

## Credential Storage

### Local vs Cloud

| Component | Local | Cloud |
|-----------|-------|-------|
| Gmail Watcher | `credentials.json` file | `GOOGLE_CREDENTIALS` env var |
| Gmail MCP | `token_gmail.json` file | `token_gmail.json` file |
| LinkedIn/Meta/Twitter | `.env` file | `.env` file |
| Odoo | `.env` file | `.env` file |

### File Locations

| Credential | Location | Git Ignored |
|------------|----------|-------------|
| `credentials.json` | `ai_employee_scripts/` | ✅ Yes |
| `token_*.json` | `ai_employee_scripts/` | ✅ Yes |
| `.env` | `ai_employee_scripts/` | ✅ Yes |
| LinkedIn session | `sessions/linkedin_mcp/` | ✅ Yes |

---

## .gitignore Configuration

**File:** `.gitignore`

```gitignore
# ========================================
# CREDENTIALS - NEVER COMMIT THESE
# ========================================

# Google OAuth
ai_employee_scripts/credentials.json
ai_employee_scripts/token_*.json

# Environment variables
ai_employee_scripts/.env
ai_employee_scripts/.env.*
ai_employee_scripts/.env.cloud

# Session files
sessions/
*.session

# ========================================
# SENSITIVE DATA
# ========================================

# Private keys
*.pem
*.key

# API keys (if stored in files)
*api_key*
*secret*

# ========================================
# LOGS (may contain sensitive data)
# ========================================

# Uncomment to ignore logs
# AI_Employee_Vault/Logs/

# ========================================
# DEVELOPMENT
# ========================================

# Python
__pycache__/
*.pyc
.venv/
*.egg-info/

# IDE
.idea/
.vscode/

# OS
.DS_Store
Thumbs.db
```

---

## Gmail Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)

### Step 2: Download Credentials

1. Go to **APIs & Services** → **Credentials**
2. Download OAuth client JSON
3. Save as `ai_employee_scripts/credentials.json`

### Step 3: Configure OAuth Consent Screen

1. Go to **OAuth consent screen**
2. Add scopes:
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.modify`
3. Add test users (your email)

### Step 4: Generate Token

```bash
cd ai_employee_scripts
uv run python refresh_gmail_mcp_token.py
```

**What happens:**
1. Script reads `credentials.json`
2. Generates OAuth URL
3. You authorize in browser
4. Token saved to `token_gmail.json`

---

## LinkedIn Setup

### API Access (for posting)

1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Create an app
3. Request **Marketing API** access
4. Generate access token

**Required Scopes:**
- `w_member_social` - Post as member
- `r_liteprofile` - Read profile

**Add to `.env`:**
```bash
LINKEDIN_ACCESS_TOKEN=your-token
LINKEDIN_CLIENT_ID=your-client-id
LINKEDIN_CLIENT_SECRET=your-client-secret
```

### Session-Based (for messaging)

Uses Playwright browser automation.

**Setup:**
```bash
cd ai_employee_scripts
uv run python setup_linkedin.py
```

**Session location:** `sessions/linkedin_mcp/`

---

## Meta (Facebook & Instagram) Setup

### Step 1: Create Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create app (Business type)
3. Add **Facebook Login** and **Instagram Graph API**

### Step 2: Get Page Access Token

1. Go to **Graph API Explorer**
2. Select your app
3. Get User Access Token with:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
4. Exchange for Long-Lived Token:
   ```
   GET https://graph.facebook.com/v18.0/oauth/access_token?
     grant_type=fb_exchange_token&
     client_id={app-id}&
     client_secret={app-secret}&
     fb_exchange_token={short-lived-token}
   ```

### Step 3: Get Page ID

```bash
# Using Graph API
curl "https://graph.facebook.com/v18.0/me/accounts?access_token={token}"
```

**Add to `.env`:**
```bash
META_ACCESS_TOKEN=your-long-lived-token
META_PAGE_ID=your-page-id
```

---

## Twitter/X Setup

### Step 1: Create Twitter App

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create project and app
3. Set up OAuth 1.0a

### Step 2: Generate Keys

1. Go to **Keys and Tokens**
2. Generate:
   - API Key
   - API Secret
   - Access Token
   - Access Token Secret

**Add to `.env`:**
```bash
X_API_KEY=your-api-key
X_API_SECRET=your-api-secret
X_ACCESS_TOKEN=your-access-token
X_ACCESS_TOKEN_SECRET=your-access-token-secret
```

**Important:** Twitter API requires paid credits for posting (402 Payment Required).

---

## Odoo Setup

### Option 1: Docker (Local)

```bash
# Start Odoo
docker run -d -p 8069:8069 --name odoo odoo:16

# Create database via web UI
# http://localhost:8069
```

### Option 2: Existing Instance

Connect to existing Odoo instance.

**Add to `.env`:**
```bash
ODOO_URL=http://localhost:8069
ODOO_DB=your-database-name
ODOO_USER=your-email@example.com
ODOO_PASSWORD=your-api-password
```

**Security Note:** Use a dedicated API user with limited permissions.

---

## OpenAI Setup (Cloud Agents)

### Step 1: Get API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create API key

**Add to `.env`:**
```bash
OPENAI_API_KEY=sk-...
```

### Step 2: Configure Agents

```python
# cloud/config/settings.py
DEFAULT_MODEL = "gpt-4o"
MAX_TOKENS = 4096
```

---

## Cloud Deployment Security

### Environment Variables

For cloud VM, use `.env` file or cloud provider's secret management:

```bash
# Create .env on cloud VM
ssh ubuntu@your-vm
cd ai-employee/ai_employee_scripts
nano .env
# Paste your credentials
```

### Google Credentials for Cloud

For Gmail cloud watcher, use service account or environment variable:

```bash
# Option 1: Service account JSON file
# Upload service-account.json to VM

# Option 2: Environment variable (single line)
GOOGLE_CREDENTIALS={"type":"service_account","project_id":"..."}
```

---

## Security Best Practices

### 1. Never Commit Secrets

```bash
# Before committing
git status
# Ensure no .env, credentials.json, token_*.json

# If accidentally committed
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch ai_employee_scripts/.env' \
  --prune-empty --tag-name-filter cat -- --all
```

### 2. Use Long-Lived Tokens

- Gmail: Refresh tokens are long-lived
- LinkedIn: Access tokens expire in 60 days, refresh before
- Meta: Long-lived tokens last 60 days, refresh before
- Twitter: Access tokens don't expire unless revoked

### 3. Rotate Credentials Regularly

- Review and rotate every 90 days
- Immediately rotate if compromised

### 4. Limit API Permissions

Only request minimum required scopes:
- Gmail: `gmail.send`, `gmail.modify`
- LinkedIn: `w_member_social`, `r_liteprofile`
- Meta: `pages_manage_posts`

### 5. Use Dedicated API Users

- Create dedicated user for API access
- Don't use personal accounts
- Set up IP restrictions if possible

### 6. Monitor API Usage

- Check API call logs
- Set up billing alerts
- Review token usage

---

## Credential Recovery

### Gmail

```bash
# Re-authorize
cd ai_employee_scripts
uv run python refresh_gmail_mcp_token.py
```

### LinkedIn

```bash
# Generate new token from Developer Portal
# Update .env
```

### Meta

```bash
# Generate new long-lived token
# Update .env
```

### Twitter

```bash
# Regenerate keys in Developer Portal
# Update .env
```

---

## Emergency Procedures

### Credential Compromised

1. **Immediately revoke:**
   - Gmail: Google Account → Security → Third-party apps → Remove
   - LinkedIn: Developer Portal → Apps → Revoke token
   - Meta: App Settings → Remove
   - Twitter: Developer Portal → Regenerate keys

2. **Generate new credentials**

3. **Update `.env` and redeploy**

4. **Review logs for unauthorized access**

### .env Committed to Git

1. **Remove from history:**
   ```bash
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch ai_employee_scripts/.env' \
     --prune-empty --tag-name-filter cat -- --all
   ```

2. **Force push (if already pushed):**
   ```bash
   git push origin --force --all
   ```

3. **Rotate ALL credentials**

---

## Related Documentation

- [Getting Started Guide](GETTING_STARTED.md)
- [Configuration Reference](CONFIGURATION_REFERENCE.md)
- [Cloud Deployment Guide](CLOUD_DEPLOYMENT_GUIDE.md)

---

*Generated: 2026-03-14*
*AI Employee Project - Platinum Tier Documentation*