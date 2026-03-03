# LinkedIn API MCP Server Documentation

## Overview

The LinkedIn API MCP Server provides LinkedIn posting functionality via the official LinkedIn Share API (UGC Posts v2). It uses OAuth 2.0 access token authentication to post content to LinkedIn and retrieve profile information.

**Location:** `ai_employee_scripts/mcp_servers/linkedin_api_mcp.py`

**MCP Name:** `linkedin-api`

---

## Features

### Available Tools

| Tool | Description | Async |
|------|-------------|-------|
| `post_to_linkedin` | Post text content to LinkedIn using Share API | Yes |
| `get_linkedin_profile` | Fetch authenticated user's LinkedIn profile | Yes |

### Tool Parameters

#### `post_to_linkedin`

```python
mcp__linkedin_api__post_to_linkedin(
    text: str,        # Post content (max 3000 characters)
    title: str = ""   # Optional title/headline for the post
)
```

**Returns:** Success message with post URN or error details

**Content Limits:**
- Max 3000 characters for LinkedIn articles
- Automatically truncates if exceeded

#### `get_linkedin_profile`

```python
mcp__linkedin_api__get_linkedin_profile()
```

**Returns:** User profile information including name, email, person URN

---

## Setup Guide

### Prerequisites

1. **LinkedIn Account** with access to LinkedIn Developer Tools
2. **Python 3.13+** with UV package manager
3. **LinkedIn Developer Application**

### Step 1: Create LinkedIn Developer Application

1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/tools)
2. Click **"Create App"**
3. Fill in:
   - **App name:** e.g., "digital-FTE"
   - **LinkedIn Page:** Create a free company page if you don't have one
   - **Logo:** Any image works
4. Agree to terms and click **Create**

### Step 2: Request API Product Access

1. In your app, go to the **Products** tab
2. Click **"Request access"** on:
   - ✅ **Share on LinkedIn** — for posting (usually instant approval)
   - ✅ **Sign In with LinkedIn using OpenID Connect** — for reading profile info
3. Wait for approval

### Step 3: Configure Redirect URL

1. Go to the **Auth** tab in your app
2. Add this **Redirect URL:** `http://localhost:8000/callback`
3. Copy your **Client ID** and **Client Secret**

### Step 4: Add Client Credentials to .env (FIRST)

Add to `ai_employee_scripts/.env`:

```bash
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
```

**Why first?** The `get_token.py` script reads these from `.env` to exchange the authorization code for an access token. This keeps credentials out of the codebase.

### Step 5: Generate Access Token

**Step 5a: Start the callback server**

```bash
# From project root
python get_token.py
```

Output: `Waiting for LinkedIn... Open the URL in your browser now.`

**Step 5b: Open authorization URL in browser**

```
https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8000/callback&scope=w_member_social%20openid%20profile%20email&prompt=consent
```

**Replace:** `YOUR_CLIENT_ID` with your actual Client ID

**Step 5c: Authorize**

1. Log in to LinkedIn
2. Click **"Allow"** to grant permissions
3. Your terminal will print: `✅ ACCESS TOKEN: <your_token_here>`

### Step 6: Add Access Token to .env

Add the access token to `ai_employee_scripts/.env`:

```bash
LINKEDIN_ACCESS_TOKEN=your_access_token_here
```

⚠️ **Token expires in 60 days** — Repeat Step 5-6 to refresh

### Step 3: Add Credentials to .env

Add to `ai_employee_scripts/.env`:

```bash
LINKEDIN_ACCESS_TOKEN=your_access_token_here
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
```

### Step 5: Install Dependencies

```bash
cd ai_employee_scripts
uv sync
```

Required packages:
- `mcp>=0.1.0`
- `httpx>=0.28.1`
- `fastmcp` (included with mcp)

---

## Configuration

### MCP Server Configuration

The LinkedIn API MCP is configured in `AI_Employee_Vault/.mcp.json`:

```json
{
  "mcpServers": {
    "linkedin-api": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/ai-employee/ai_employee_scripts",
        "run",
        "mcp_servers/linkedin_api_mcp.py"
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

| Variable | Description | Required For |
|----------|-------------|--------------|
| `LINKEDIN_CLIENT_ID` | LinkedIn application client ID | **get_token.py** (add BEFORE running) |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn application client secret | **get_token.py** (add BEFORE running) |
| `LINKEDIN_ACCESS_TOKEN` | OAuth 2.0 access token | MCP server (add AFTER get_token.py) |

**Setup Order:**
1. Add `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET` first
2. Run `get_token.py` to get access token
3. Add `LINKEDIN_ACCESS_TOKEN` to complete setup

---

## Authentication Workflow

### Diagram

```
┌─────────────────────────────────────┐
│  Create LinkedIn Developer App      │
│  Request: Share on LinkedIn + OpenID│
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Add Redirect URL:                  │
│  http://localhost:8000/callback     │
│  Copy Client ID & Client Secret     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Add to ai_employee_scripts/.env:   │
│  LINKEDIN_CLIENT_ID=xxx             │
│  LINKEDIN_CLIENT_SECRET=xxx         │
│                                     │
│  ✅ Credentials not in code!        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Run: python get_token.py           │
│  (Reads credentials from .env)      │
│  Server starts on localhost:8000    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Open authorization URL in browser  │
│  (with YOUR_CLIENT_ID)              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Log in to LinkedIn                 │
│  Click "Allow" to authorize         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Callback with authorization code   │
│  Script exchanges code for token    │
│  (Using client_id/secret from .env) │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  ✅ ACCESS TOKEN printed to terminal│
│  Copy the token                     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Add to .env:                       │
│  LINKEDIN_ACCESS_TOKEN=xxx          │
│                                     │
│  Now all 3 credentials in .env      │
└─────────────────────────────────────┘
```

### Token Lifecycle

| Token Type | Duration | Refresh |
|------------|----------|---------|
| Access Token | ~60 days | No refresh - requires re-authentication |
| Authorization Code | 10 minutes | Single use |

**Important:** LinkedIn access tokens expire and cannot be refreshed. You must re-authenticate when expired.

---

## Usage Examples

### In Agent Skills

#### Posting LinkedIn Content (execute-approved skill)

```python
# Post to LinkedIn
result = mcp__linkedin_api__post_to_linkedin(
    text="Here are 3 automation mistakes costing you sales:\n\n1. Manual data entry\n2. No follow-up sequences\n3. Ignoring analytics\n\nWhich one are you guilty of?",
    title="Automation Mistakes"
)
```

#### Getting Profile Information

```python
# Get LinkedIn profile
profile = mcp__linkedin_api__get_linkedin_profile()
# Returns: Name, Email, Person URN
```

---

## API Endpoints Used

| Endpoint | Purpose | Method |
|----------|---------|--------|
| `https://api.linkedin.com/v2/userinfo` | Get user profile (OpenID Connect) | GET |
| `https://api.linkedin.com/v2/ugcPosts` | Create UGC post | POST |

### Headers Used

```http
Authorization: Bearer {access_token}
Content-Type: application/json
X-Restli-Protocol-Version: 2.0.0
LinkedIn-Version: 202501
```

---

## Files and Paths

| File | Location | Purpose |
|------|----------|---------|
| Token Script | `get_token.py` (project root) | **Primary: Creates OAuth token** |
| MCP Server | `ai_employee_scripts/mcp_servers/linkedin_api_mcp.py` | Main MCP server code |
| Credentials | `ai_employee_scripts/.env` | Stores access token, client ID, client secret |
| MCP Config | `AI_Employee_Vault/.mcp.json` | MCP server configuration |

---

## Troubleshooting

### Issue: "LINKEDIN_ACCESS_TOKEN not found in environment"

**Error Message:**
```
❌ LINKEDIN_ACCESS_TOKEN not found in environment!
```

**Solution:**
1. Run `get_token.py` to get access token
2. Add to `ai_employee_scripts/.env`:
   ```bash
   LINKEDIN_ACCESS_TOKEN=your_token_here
   ```

---

### Issue: 401 Unauthorized

**Error Message:**
```
Error: Failed to post to LinkedIn. Status: 401
```

**Solution:**
1. Access token has expired (~60 days)
2. Re-run `get_token.py` to get fresh token
3. Update `.env` file with new token

---

### Issue: 403 Forbidden

**Error Message:**
```
Error: Failed to post to LinkedIn. Status: 403
```

**Solution:**
1. Check OAuth scopes include `w_member_social`
2. Verify application is approved in LinkedIn Developer Portal
3. Some scopes require LinkedIn's approval

---

### Issue: "No person URN found"

**Error Message:**
```
Error: No person ID found in profile response
```

**Solution:**
1. Access token may lack `openid` or `profile` scopes
2. Re-authenticate with correct scopes
3. Check LinkedIn application permissions

---

### Issue: Post Content Truncated

**Message:**
```
⚠️ Post content truncated to 3000 characters
```

**Cause:** LinkedIn has character limits

**Solution:**
- Keep posts under 3000 characters
- Content is auto-truncated with `...` suffix

---

### Issue: "Request timed out"

**Error Message:**
```
Request timed out. LinkedIn API is taking too long to respond.
```

**Solution:**
1. Check internet connection
2. LinkedIn API may be slow - retry
3. Timeout is set to 30 seconds

---

## Token Refresh Guide

### LinkedIn Token Limitations

**Important:** LinkedIn access tokens **cannot be refreshed**. When they expire (~60 days), you must:

1. Re-run `get_token.py`
2. Get new authorization code
3. Exchange for new access token
4. Update `.env` file

```bash
# From project root
python get_token.py
```

---

## Skills Using LinkedIn API MCP

| Skill | Usage | Description |
|-------|-------|-------------|
| `execute-approved` | `post_to_linkedin` | Posts approved LinkedIn content |
| `linkedin-posting` | Content generation | Creates LinkedIn posts (uses execute-approved to post) |

---

## Dependencies

```
mcp>=0.1.0
httpx>=0.28.1
fastmcp
```

Install via:
```bash
cd ai_employee_scripts
uv sync
```

---

## API Reference

### UGC Post Structure

```json
{
  "author": "urn:li:person:{person_urn}",
  "lifecycleState": "PUBLISHED",
  "specificContent": {
    "com.linkedin.ugc.ShareContent": {
      "shareCommentary": {
        "text": "Post content here..."
      },
      "shareMediaCategory": "NONE"
    }
  },
  "visibility": {
    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
  }
}
```

### Profile Response (OpenID Connect)

```json
{
  "sub": "123456789",
  "given_name": "John",
  "family_name": "Doe",
  "email": "john.doe@example.com"
}
```

---

## Security Notes

1. **Never commit** `.env` file with access token to git
2. **Never share** your access token or client secret
3. **Revoke access** in LinkedIn settings if credentials are compromised
4. **Token expires** after ~60 days - re-authentication required
5. **Store securely** - `.env` is git-ignored

---

## Related Documentation

- [LinkedIn UGC Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/ugc-posts)
- [LinkedIn OAuth 2.0](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow)
- [Execute Approved Skill](../../.claude/skills/execute-approved/SKILL.md)
- [LinkedIn Posting Skill](../../.claude/skills/linkedin-posting/SKILL.md)

---

*Generated: 2026-02-28*
*AI Employee Project - Gold Tier Documentation*
