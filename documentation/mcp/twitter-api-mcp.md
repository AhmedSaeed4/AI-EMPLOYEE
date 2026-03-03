# Twitter/X API MCP Server Documentation

## Overview

The Twitter/X API MCP Server provides Twitter posting functionality via the Twitter API v2 using Tweepy. It uses OAuth 1.0a authentication (4-key method) to post tweets and retrieve profile information.

**Location:** `ai_employee_scripts/mcp_servers/twitter_mcp.py`

**MCP Name:** `twitter-api`

---

## Features

### Available Tools

| Tool | Description | Async |
|------|-------------|-------|
| `post_tweet` | Post any text as a tweet (max 280 chars) | Yes |
| `get_twitter_profile` | Fetch authenticated user's Twitter/X profile | Yes |
| `post_business_update` | Post formatted business update tweet | Yes |

### Tool Parameters

#### `post_tweet`

```python
mcp__twitter-api__post_tweet(
    text: str    # Tweet content (max 280 characters)
)
```

**Returns:** Success message with Tweet ID and URL

**Content Limits:**
- Max 280 characters
- Auto-truncates if exceeded (adds `...` suffix)

#### `get_twitter_profile`

```python
mcp__twitter-api__get_twitter_profile()
```

**Returns:** Profile information including:
- Name and username
- User ID
- Bio
- Follower/following counts
- Tweet count
- Profile URL

#### `post_business_update`

```python
mcp__twitter-api__post_business_update(
    update_type: str,   # Type: 'invoice_sent', 'project_complete', 'new_service', 'milestone', 'general'
    details: str,       # Specific details of the update
    hashtags: str = ""  # Optional hashtags (e.g., "#freelance #videoediting")
)
```

**Returns:** Success message with Tweet ID and URL

**Update Types:**
| Type | Emoji | Template |
|------|-------|----------|
| `invoice_sent` | ✅ | "Another project invoiced and delivered! {details}" |
| `project_complete` | 🎉 | "Project complete! {details}" |
| `new_service` | 🚀 | "Excited to announce: {details}" |
| `milestone` | 🏆 | "Milestone reached: {details}" |
| `general` | - | Uses details directly as tweet |

---

## Setup Guide

### Prerequisites

1. **X (Twitter) Account** — Create one at [x.com](https://x.com)
2. **Python 3.13+** with UV package manager
3. **Twitter Developer Account** (free tier)

### Step 1: Create Twitter Developer Account

1. Go to [developer.x.com](https://developer.x.com) and click **Sign up** using your X account
2. When asked what you are building, enter this description:

   ```
   Personal automation tool that posts business updates, project completions,
   and service announcements to X. Built for a solo entrepreneur to schedule
   and publish content automatically as part of a local-first AI productivity system.
   ```

💡 **Free tier access is approved instantly** — 500 posts and 100 reads per month

### Step 2: Create Project and App

1. Go to [console.x.com](https://console.x.com) after your developer account is approved
2. Click **New Project** → Give it a name → Click **Next**
3. Inside the project, click **Add App** and give your app a name
4. Once the app is created, click **App Settings**

### Step 3: Configure User Authentication

⚠️ **You MUST complete this step BEFORE generating your Access Token.** If you skip it, your token will be **Read-only** and posting will fail.

1. Scroll to **User authentication settings** and click **Set up**
2. Configure the fields as follows:

   | Field | Value |
   |-------|-------|
   | App permissions | **Read and Write** |
   | Type of App | **Web App, Automated App or Bot** |
   | Callback URI | `http://127.0.0.1` |
   | Website URL | `http://127.0.0.1` |
   | Organization URL | *(leave blank)* |
   | Terms of Service | *(leave blank)* |
   | Privacy Policy | *(leave blank)* |

⚠️ **Troubleshooting:** If you see "Not a valid URL format" on the Callback URI field, make sure there are **no trailing spaces** after `http://127.0.0.1`. Type it fresh, then press **End** to check.

3. Click **Save** → Click **Yes** when prompted to confirm

### Step 4: Generate Your API Keys

⚠️ **X only shows your secrets ONCE.** Save them immediately in a safe place.

1. Go to your App's **Keys and Tokens** tab
2. Under **Consumer Keys**, click **Regenerate** → Save the **API Key** and **API Key Secret**
3. Under **Authentication Tokens**, click **Generate**
   - ✅ Verify you see **"Read and Write"** next to your token
   - If you see "Read only", go back to Step 3
4. Save all four values:

```bash
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_key_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

### Step 5: Add Keys to .env

Add all four to `ai_employee_scripts/.env`:

```bash
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_key_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

### Step 6: Install Dependencies

```bash
cd ai_employee_scripts
uv sync
```

Required packages:
- `tweepy>=4.16.0`
- `mcp>=0.1.0`

---

## Configuration

### MCP Server Configuration

The Twitter API MCP is configured in `AI_Employee_Vault/.mcp.json`:

```json
{
  "mcpServers": {
    "twitter-api": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/ai-employee/ai_employee_scripts",
        "run",
        "mcp_servers/twitter_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/ai-employee/ai_employee_scripts"
      }
    }
  }
}
```

**Replace:** `/path/to/ai-employee` with your actual project path

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `X_API_KEY` | Twitter/X API Key (Consumer Key) | Yes |
| `X_API_SECRET` | Twitter/X API Secret (Consumer Secret) | Yes |
| `X_ACCESS_TOKEN` | Twitter/X Access Token | Yes |
| `X_ACCESS_TOKEN_SECRET` | Twitter/X Access Token Secret | Yes |

---

## Authentication

### OAuth 1.0a (4-Key Method)

This MCP uses **OAuth 1.0a** (not OAuth 2.0), which requires 4 keys:

```
┌─────────────────────────────────────┐
│  Sign up at developer.x.com         │
│  Describe: "Personal automation     │
│  tool for business updates..."      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Create Project → Add App           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Configure User Authentication:     │
│  BEFORE generating tokens!          │
│                                     │
│  App permissions: Read and Write    │
│  Type: Web App, Bot, etc.           │
│  Callback URI: http://127.0.0.1     │
│  Website URL: http://127.0.0.1      │
│                                     │
│  ⚠️ No trailing spaces in URLs!     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Go to Keys and Tokens tab          │
│                                     │
│  1. Regenerate Consumer Keys:       │
│     - API Key                       │
│     - API Key Secret                │
│                                     │
│  2. Generate Authentication Token:  │
│     - Verify "Read and Write" shown │
│     - Access Token                  │
│     - Access Token Secret           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Copy all 4 keys immediately!       │
│  (X only shows secrets ONCE)        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Add to ai_employee_scripts/.env    │
│  X_API_KEY=xxx                      │
│  X_API_SECRET=xxx                   │
│  X_ACCESS_TOKEN=xxx                 │
│  X_ACCESS_TOKEN_SECRET=xxx          │
└─────────────────────────────────────┘
```

### Key Differences from OAuth 2.0

| OAuth 1.0a | OAuth 2.0 |
|------------|-----------|
| 4 keys required | 1-2 keys required |
| No refresh needed | Tokens expire, refresh required |
| Access tokens don't expire | Limited lifetime |
| Older, more stable | Newer, simpler |

---

## Usage Examples

### In Agent Skills

#### Posting Simple Tweet (execute-approved skill)

```python
# Post a tweet
result = mcp__twitter-api__post_tweet(
    text="Just shipped a new feature for our AI Employee! 🚀 #automation #AI"
)
```

#### Posting Business Update (execute-approved skill)

```python
# Post project completion
result = mcp__twitter-api__post_business_update(
    update_type="project_complete",
    details="Delivered custom automation workflow for client",
    hashtags="#freelance #automation"
)
```

#### Getting Profile Info

```python
# Get profile information
profile = mcp__twitter-api__get_twitter_profile()
```

---

## Files and Paths

| File | Location | Purpose |
|------|----------|---------|
| MCP Server | `ai_employee_scripts/mcp_servers/twitter_mcp.py` | Main MCP server code |
| Credentials | `ai_employee_scripts/.env` | All 4 API keys |
| MCP Config | `AI_Employee_Vault/.mcp.json` | MCP server configuration |

---

## Troubleshooting

### Issue: "Missing credentials"

**Error Message:**
```
❌ Missing credentials: X_API_KEY, X_API_SECRET, ...
```

**Solution:**
Add all 4 keys to `ai_employee_scripts/.env`:
```bash
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

---

### Issue: "Forbidden (403)" - Read Only Token

**Error Message:**
```
❌ Forbidden (403): Twitter rejected the request.
Most likely cause: Access Token is 'Read Only' — you need 'Read and Write'.
```

**Solution:**
1. Go to your App in [console.x.com](https://console.x.com)
2. **Keys and Tokens** tab → Check if it says "Read only" next to your token
3. Go back to **App Settings** → **User authentication settings**
4. Set **App permissions** to **"Read and Write"**
5. Click **Save** → Click **Yes** to confirm
6. Go back to **Keys and Tokens** → Under **Authentication Tokens**, click **Regenerate**
7. Verify you see **"Read and Write"** next to the new token
8. Update `X_ACCESS_TOKEN` and `X_ACCESS_TOKEN_SECRET` in `.env`

---

### Issue: "Unauthorized (401)"

**Error Message:**
```
❌ Unauthorized (401): Invalid credentials.
```

**Solution:**
1. Verify all 4 keys are correct in `.env`
2. No extra spaces or quotes
3. Keys haven't been revoked in X Developer Portal
4. Regenerate keys if needed

---

### Issue: "Rate limit exceeded (429)"

**Error Message:**
```
❌ Rate limit exceeded (429): Too many requests.
Free tier allows 500 posts per month.
```

**Solution:**
- Free tier: 500 posts/month
- Wait before trying again
- Consider upgrading tier for higher limits

---

### Issue: Tweet Truncated

**Message:**
```
⚠️ Tweet truncated to 280 characters
```

**Cause:** Twitter has 280 character limit

**Solution:**
- Keep tweets under 280 characters
- Content is auto-truncated with `...` suffix

---

## API Rate Limits (Free Tier)

| Action | Limit | Period |
|--------|-------|--------|
| Post Tweet | 500 | Month |
| Get Profile | 15 | 15 min |

**Note:** Rate limits are subject to change by X/Twitter.

---

## Skills Using Twitter API MCP

| Skill | Usage | Description |
|-------|-------|-------------|
| `execute-approved` | `post_tweet`, `post_business_update` | Posts approved Twitter content |
| `twitter-posting` | Content generation | Creates Twitter posts (uses execute-approved to post) |

---

## Dependencies

```
tweepy>=4.16.0
mcp>=0.1.0
```

Install via:
```bash
cd ai_employee_scripts
uv sync
```

---

## Security Notes

1. **Never commit** `.env` file with API keys to git
2. **Never share** your 4 API keys
3. **Revoke access** in X Developer Portal if credentials are compromised
4. **Tokens don't expire** - but can be revoked
5. **Store securely** - `.env` is git-ignored

---

## Related Documentation

- [X API Documentation](https://developer.x.com/en/docs/twitter-api)
- [Tweepy Documentation](https://docs.tweepy.org/)
- [Execute Approved Skill](../../.claude/skills/execute-approved/SKILL.md)
- [Twitter Posting Skill](../../.claude/skills/twitter-posting/SKILL.md)

---

*Generated: 2026-02-28*
*AI Employee Project - Gold Tier Documentation*
