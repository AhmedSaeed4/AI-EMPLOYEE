# Agent Skills Reference

Agent Skills are Claude Code slash commands that provide specialized functionality. Each skill lives in `.claude/skills/<skill-name>/SKILL.md`.

---

## Skills Overview (18 Total)

| Category | Skills |
|----------|--------|
| **Task Management** | `check-tasks`, `process-file`, `create-plan` |
| **Watcher Control** | `start-watcher`, `stop-watcher`, `check-watchers`, `watcher-status` |
| **Accounting** | `check-accounting`, `create-invoice` |
| **Social Media** | `linkedin-posting`, `meta-posting`, `twitter-posting`, `post-linkedin` |
| **Approvals** | `approve-action`, `execute-approved` |
| **Reporting** | `daily-summary`, `weekly-audit` |
| **Configuration** | `update-handbook` |

---

## Task Management Skills

### `/check-tasks`

**Purpose:** List all pending tasks in `Needs_Action/` folder.

**Usage:**
```bash
claude code -p "/check-tasks"
```

**Output:**
- Lists all `.md` files in `Needs_Action/`
- Shows task type, creation time, and priority
- Displays count of pending tasks

**Files:**
- Skill: `.claude/skills/check-tasks/SKILL.md`
- Monitors: `AI_Employee_Vault/Needs_Action/`

---

### `/process-file`

**Purpose:** Process a task file from `Needs_Action/` folder.

**Usage:**
```bash
claude code -p "/process-file"
```

**Workflow:**
1. Reads task file from `Needs_Action/`
2. Determines task type (email, LinkedIn message, file)
3. Reads `Company_Handbook.md` for rules
4. Processes content and determines action:
   - Safe action → Execute directly
   - Sensitive action → Create file in `Pending_Approval/`
   - Information only → Extract and log
5. Moves processed file to `Done/`
6. Updates `Dashboard.md`

**Files:**
- Skill: `.claude/skills/process-file/SKILL.md`
- Reads: `AI_Employee_Vault/Needs_Action/`
- Writes: `AI_Employee_Vault/Done/`, `Pending_Approval/`

---

### `/create-plan`

**Purpose:** Create a `Plan.md` file for complex multi-step tasks.

**Usage:**
```bash
claude code -p "/create-plan"
```

**Output:**
- Creates `Plan.md` in `Plans/` folder
- Breaks down task into steps
- Identifies dependencies
- Estimates effort

**Files:**
- Skill: `.claude/skills/create-plan/SKILL.md`
- Writes: `AI_Employee_Vault/Plans/`

---

## Watcher Control Skills

### `/start-watcher`

**Purpose:** Start one or more watcher scripts.

**Usage:**
```bash
claude code -p "/start-watcher filesystem"
claude code -p "/start-watcher gmail"
claude code -p "/start-watcher linkedin"
claude code -p "/start-watcher all"
```

**Watchers:**
| Watcher | Monitors | Poll Interval |
|---------|----------|---------------|
| `filesystem` | `Drop_Zone/` folder | 2 seconds |
| `gmail` | Gmail inbox (last 24h) | 2 minutes |
| `linkedin` | LinkedIn messages | 5 minutes |

**Files:**
- Skill: `.claude/skills/start-watcher/SKILL.md`
- Scripts: `ai_employee_scripts/watchers/<name>_watcher.py`

---

### `/stop-watcher`

**Purpose:** Stop one or more watcher scripts.

**Usage:**
```bash
claude code -p "/stop-watcher filesystem"
claude code -p "/stop-watcher gmail"
claude code -p "/stop-watcher all"
```

**Files:**
- Skill: `.claude/skills/stop-watcher/SKILL.md`

---

### `/check-watchers`

**Purpose:** Check status of all watcher scripts.

**Usage:**
```bash
claude code -p "/check-watchers"
```

**Output:**
- Shows running/stopped status for each watcher
- Displays PID if running
- Shows last check time

**Files:**
- Skill: `.claude/skills/check-watchers/SKILL.md`

---

### `/watcher-status`

**Purpose:** Check detailed status of File System Watcher.

**Usage:**
```bash
claude code -p "/watcher-status"
```

**Output:**
- Running status
- Files processed count
- Last activity
- Error count

**Files:**
- Skill: `.claude/skills/watcher-status/SKILL.md`

---

## Accounting Skills

### `/check-accounting`

**Purpose:** Get financial summary from Odoo.

**Usage:**
```bash
claude code -p "/check-accounting"
```

**Output:**
- Total revenue (last 30 days)
- Total expenses (last 30 days)
- Pending invoices
- Recent payments
- Profit calculation

**MCP Server:** `odoo`

**Files:**
- Skill: `.claude/skills/check-accounting/SKILL.md`
- MCP: `ai_employee_scripts/mcp_servers/odoo_mcp.py`

---

### `/create-invoice`

**Purpose:** Create a draft invoice in Odoo.

**Usage:**
```bash
claude code -p "/create-invoice"
```

**Workflow:**
1. Prompts for customer name
2. Prompts for amount and description
3. Creates draft invoice in Odoo
4. Creates approval file in `Pending_Approval/`
5. Human approval required to post invoice

**MCP Server:** `odoo`

**Files:**
- Skill: `.claude/skills/create-invoice/SKILL.md`
- MCP: `ai_employee_scripts/mcp_servers/odoo_mcp.py`

---

## Social Media Skills

### `/linkedin-posting`

**Purpose:** Generate a lead-generating LinkedIn post idea.

**Usage:**
```bash
claude code -p "/linkedin-posting"
```

**Workflow:**
1. Reads `Business_Goals.md` for context
2. Generates post idea based on topics
3. Creates file in `Content_To_Post/queued/`
4. Creates approval file in `Pending_Approval/`

**Output Files:**
- `Content_To_Post/queued/LINKEDIN_POST_<topic>_<timestamp>.md`
- `Pending_Approval/LINKEDIN_POST_<topic>_<timestamp>.md`

**MCP Server:** `linkedin_api`

**Files:**
- Skill: `.claude/skills/linkedin-posting/SKILL.md`

---

### `/meta-posting`

**Purpose:** Generate a Facebook/Instagram post.

**Usage:**
```bash
claude code -p "/meta-posting"
```

**Workflow:**
1. Reads `Business_Goals.md` for context
2. Generates post for both platforms
3. Creates file in `Content_To_Post/queued/`
4. Creates approval file in `Pending_Approval/`
5. Human selects platform(s) in approval

**Note:** Instagram requires an image URL (provided in approval).

**MCP Server:** `meta-api`

**Files:**
- Skill: `.claude/skills/meta-posting/SKILL.md`

---

### `/twitter-posting`

**Purpose:** Generate a Twitter (X) post.

**Usage:**
```bash
claude code -p "/twitter-posting"
```

**Workflow:**
1. Reads `Business_Goals.md` for context
2. Generates tweet (max 280 characters)
3. Creates file in `Content_To_Post/queued/`
4. Creates approval file in `Pending_Approval/`

**Note:** Twitter posting requires X API credits (402 Payment Required).

**MCP Server:** `twitter-api`

**Files:**
- Skill: `.claude/skills/twitter-posting/SKILL.md`

---

### `/post-linkedin`

**Purpose:** Create LinkedIn post content and add to queue.

**Usage:**
```bash
claude code -p "/post-linkedin"
```

**Files:**
- Skill: `.claude/skills/post-linkedin/SKILL.md`

---

## Approval Skills

### `/approve-action`

**Purpose:** Move action from `Pending_Approval` to `Approved` folder.

**Usage:**
```bash
claude code -p "/approve-action"
```

**Workflow:**
1. Lists pending actions
2. User selects action to approve
3. Moves file to `Approved/`
4. Triggers execution via orchestrator

**Files:**
- Skill: `.claude/skills/approve-action/SKILL.md`
- Reads: `AI_Employee_Vault/Pending_Approval/`
- Writes: `AI_Employee_Vault/Approved/`

---

### `/execute-approved`

**Purpose:** Execute approved actions via MCP servers.

**Usage:**
```bash
claude code -p "/execute-approved"
```

**Supported Actions:**
| Action Type | MCP Server | Function |
|-------------|------------|----------|
| Email reply | `gmail` | `send_email` |
| LinkedIn post | `linkedin_api` | `post_to_linkedin` |
| LinkedIn message reply | `linkedin` | `reply_to_message` |
| Meta post | `meta-api` | `post_to_facebook` / `post_to_instagram` |
| Twitter post | `twitter-api` | `post_tweet` |
| Odoo invoice | `odoo` | `post_invoice` |

**Files:**
- Skill: `.claude/skills/execute-approved/SKILL.md`

---

## Reporting Skills

### `/daily-summary`

**Purpose:** Generate daily summary and update Dashboard.

**Usage:**
```bash
claude code -p "/daily-summary"
```

**Output:**
- Updates `Dashboard.md` with:
  - Tasks processed today
  - Emails sent
  - Social posts published
  - Invoices created
  - Errors encountered

**Files:**
- Skill: `.claude/skills/daily-summary/SKILL.md`
- Updates: `AI_Employee_Vault/Dashboard.md`

---

### `/weekly-audit`

**Purpose:** Generate comprehensive CEO Briefing.

**Usage:**
```bash
claude code -p "/weekly-audit"
```

**Output:**
- Creates briefing in `Briefings/`
- Fetches data from Odoo (revenue, expenses, invoices)
- Analyzes vault data (tasks, posts, errors)
- Generates insights and recommendations
- **Auto-emails** briefing via Gmail MCP
- Updates `Dashboard.md`

**Cron:** Runs every Monday at 6 AM

**Files:**
- Skill: `.claude/skills/weekly-audit/SKILL.md`
- Output: `AI_Employee_Vault/Briefings/YYYY-MM-DD_Weekly_Briefing.md`

---

## Configuration Skills

### `/update-handbook`

**Purpose:** Add or update rules in `Company_Handbook.md`.

**Usage:**
```bash
claude code -p "/update-handbook"
```

**Categories:**
- Financial rules
- Communication rules
- Social media rules
- WhatsApp rules
- General constraints

**Files:**
- Skill: `.claude/skills/update-handbook/SKILL.md`
- Updates: `AI_Employee_Vault/Company_Handbook.md`

---

## Skill File Structure

Each skill follows this structure:

```
.claude/skills/
├── <skill-name>/
│   └── SKILL.md          # Skill definition
```

### SKILL.md Format

```markdown
---
description: Brief description of the skill
userInvocable: true|false
---

# Skill Name

Detailed instructions for the skill...

## Steps
1. First step
2. Second step
...

## Files
- Input: path/to/input
- Output: path/to/output
```

---

## Cron-Triggered Skills

These skills are triggered automatically by cron jobs:

| Skill | Schedule | Trigger Script |
|-------|----------|----------------|
| `linkedin-posting` | Daily 2:00 AM | `scripts/linkedin_cron_trigger.py` |
| `meta-posting` | Daily 3:00 AM | `scripts/meta_cron_trigger.py` |
| `twitter-posting` | Daily 4:00 AM | `scripts/twitter_cron_trigger.py` |
| `weekly-audit` | Monday 6:00 AM | `scripts/weekly_audit_cron_trigger.py` |

---

## Integration with MCP Servers

| Skill | MCP Server | Tools Used |
|-------|------------|------------|
| `check-accounting` | `odoo` | `get_revenue`, `get_expenses`, `get_invoices` |
| `create-invoice` | `odoo` | `create_draft_invoice` |
| `execute-approved` | `gmail` | `send_email` |
| `execute-approved` | `linkedin_api` | `post_to_linkedin` |
| `execute-approved` | `linkedin` | `reply_to_message` |
| `execute-approved` | `meta-api` | `post_to_facebook`, `post_to_instagram` |
| `execute-approved` | `twitter-api` | `post_tweet` |
| `execute-approved` | `odoo` | `post_invoice` |
| `weekly-audit` | `odoo` | `get_revenue`, `get_expenses` |
| `weekly-audit` | `gmail` | `send_email` |

---

## Related Documentation

- [Getting Started Guide](GETTING_STARTED.md)
- [Project Architecture](PROJECT_ARCHITECTURE.md)
- [MCP Server Documentation](mcp/)

---

*Generated: 2026-03-14*
*AI Employee Project - Platinum Tier Documentation*