# Vault Structure Guide

The AI Employee Vault (`AI_Employee_Vault/`) is the central data store for all tasks, content, and state. It's an Obsidian-compatible Markdown vault.

---

## Overview

The vault follows a **folder-based state machine** pattern:

```
Inbox → Needs_Action → [Processing] → Done
                           │
                           ▼
                   Pending_Approval → Approved → Done
                                      │
                                      ▼
                                   Rejected
```

---

## Folder Structure

```
AI_Employee_Vault/
├── Dashboard.md                 # Central status hub
├── Company_Handbook.md          # AI behavior rules & constraints
├── Business_Goals.md            # Business context & posting topics
│
├── Inbox/                       # Raw content storage
│   ├── EMAIL_[id].md
│   ├── LINKEDIN_MESSAGE_[timestamp].md
│   └── [copied files from Drop_Zone]
│
├── Needs_Action/                # Tasks awaiting Claude processing
│   ├── EMAIL_[subject]_[timestamp].md
│   ├── LINKEDIN_MESSAGE_[timestamp].md
│   └── FILE_[name]_[timestamp].md
│
├── Pending_Approval/            # Actions requiring human approval
│   ├── ACTION_EMAIL_[recipient]_[date].md
│   ├── ACTION_LINKEDIN_POST_[topic]_[date].md
│   ├── ACTION_META_POST_[topic]_[date].md
│   ├── ACTION_TWITTER_POST_[topic]_[date].md
│   ├── ACTION_ODOO_INVOICE_[customer]_[date].md
│   └── LINKEDIN_POST_[topic]_[date].md
│
├── Approved/                    # Approved actions (triggers execution)
│   └── ACTION_[type]_[target]_[date].md
│
├── Rejected/                    # Rejected actions (logged)
│   └── ACTION_[type]_[target]_[date].md
│
├── Done/                        # Completed tasks
│   ├── COMPLETED_[type]_[timestamp].md
│   └── [processed files]
│
├── Failed_Queue/                # Failed actions for human review
│   └── FAILED_[type]_[timestamp].md
│
├── Plans/                       # Complex task plans
│   └── Plan.md
│
├── Logs/                        # System logs and state files
│   ├── YYYY-MM-DD_orchestrator.log
│   ├── orchestrator_state.json
│   ├── gmail_processed_ids.json
│   ├── linkedin_state.json
│   ├── rejected_actions.log
│   ├── vault_sync.log
│   ├── cron.log
│   └── [watcher logs]
│
├── Briefings/                   # Weekly CEO Briefings
│   └── YYYY-MM-DD_Weekly_Briefing.md
│
├── Content_To_Post/             # Social media content queue
│   ├── queued/                  # Posts ready to publish
│   │   ├── LINKEDIN_POST_[topic]_[timestamp].md
│   │   ├── META_POST_[topic]_[timestamp].md
│   │   └── TWITTER_POST_[topic]_[timestamp].md
│   ├── posted/                  # Published posts
│   │   └── [moved from queued after posting]
│   └── rejected/                # Rejected posts
│       └── [moved from queued after rejection]
│
└── .obsidian/                   # Obsidian configuration
    └── workspace.json
```

---

## File Naming Conventions

### Email Files

**Inbox:**
```
EMAIL_[message_id].md
```

**Needs_Action:**
```
EMAIL_[subject_slug]_[YYYYMMDD_HHMMSS].md
```

**Example:**
```
EMAIL_19cd0aa8032661e4.md
EMAIL_project_update_20260314_143000.md
```

### LinkedIn Files

**Inbox:**
```
LINKEDIN_MESSAGE_[YYYYMMDD_HHMMSS].md
```

**Needs_Action:**
```
LINKEDIN_MESSAGE_[YYYYMMDD_HHMMSS].md
```

### Social Media Posts

**Queued:**
```
[PLATFORM]_POST_[topic_slug]_[YYYYMMDD_HHMMSS].md
```

**Example:**
```
LINKEDIN_POST_visual_storytelling_20260311_143000.md
META_POST_3d_trends_20260312_150000.md
TWITTER_POST_ai_agent_blueprint_20260310_143000.md
```

### Action Files

**Pending Approval:**
```
ACTION_[type]_[target]_[YYYYMMDD].md
```

**Example:**
```
ACTION_EMAIL_john_example_com_20260314.md
ACTION_ODOO_INVOICE_Food_Ninja_20260222.md
```

---

## Core Files

### Dashboard.md

**Purpose:** Central status hub showing current state.

**Updated by:** `daily-summary` skill, various processing skills

**Content:**
```markdown
# AI Employee Dashboard

## Status
- **Last Updated:** 2026-03-14 14:30:00
- **Mode:** Active

## Pending Tasks
- [ ] EMAIL_project_update_20260314_143000.md
- [ ] LINKEDIN_MESSAGE_20260314_140000.md

## Recent Activity
- 2026-03-14 14:00: Processed email from John
- 2026-03-14 13:30: Published LinkedIn post

## Statistics (Today)
- Emails Processed: 5
- Posts Published: 2
- Invoices Created: 1
```

### Company_Handbook.md

**Purpose:** AI behavior rules and constraints.

**Updated by:** `update-handbook` skill

**Key Rules:**
- Financial: Payments >$100 require approval
- WhatsApp: Never auto-reply
- Social Media: Drafts require approval
- Never without permission: Send money, commit to deadlines, share contacts

### Business_Goals.md

**Purpose:** Business context for content generation.

**Content:**
- Industries: AI Agents, 3D Animation, 2D VFX
- Services: Custom agents, reels, short-form content
- Target audience: Businesses + Content creators
- Posting topics and CTAs

---

## Workflow States

### 1. Inbox

**Purpose:** Raw content storage from watchers.

**Who writes:** Watchers (Gmail, LinkedIn, FileSystem)

**When:** When new content arrives

**Format:** Full content with metadata

**Example (Email):**
```markdown
---
type: email
message_id: 19cd0aa8032661e4
received: 2026-03-14T14:00:00
sender: john@example.com
subject: Project Update
---

# Email Content

Hi,

I wanted to follow up on the project status...

---
*Raw email body stored here*
```

### 2. Needs_Action

**Purpose:** Tasks awaiting Claude processing.

**Who writes:** Watchers

**Who reads:** Claude Code (via `/process-file` skill)

**Processing:**
1. Orchestrator detects new file
2. Calls `/process-file` skill
3. Claude reads and processes
4. Moves to `Done/` or creates action in `Pending_Approval/`

### 3. Pending_Approval

**Purpose:** Sensitive actions requiring human approval.

**Who writes:** Claude Code (after processing)

**Who reads:** Human (review and decide)

**Decision:**
- **Approve:** Move to `Approved/`
- **Reject:** Move to `Rejected/`

**Example (Invoice):**
```markdown
---
type: odoo_invoice
created: 2026-02-22T10:30:00
customer: Food Ninja
amount: 500.00
---

# Draft Invoice

## Customer
- Name: Food Ninja
- Email: billing@foodninja.com

## Line Items
| Description | Amount |
|-------------|--------|
| AI Agent Development | $500.00 |

## Human Section
[ ] Approve this invoice
[ ] Modify amount: _______
[ ] Reject (reason): _______
```

### 4. Approved

**Purpose:** Approved actions ready for execution.

**Who writes:** Human (moves file from Pending_Approval)

**Who reads:** Orchestrator (triggers `/execute-approved`)

**Processing:**
1. Orchestrator detects new file
2. Calls `/execute-approved` skill
3. Executes via appropriate MCP server
4. Moves to `Done/`

### 5. Rejected

**Purpose:** Rejected actions for audit trail.

**Who writes:** Human (moves file from Pending_Approval)

**Processing:**
1. Orchestrator logs rejection
2. File stays for audit trail

### 6. Done

**Purpose:** Completed tasks archive.

**Who writes:** Claude Code (after processing/execution)

**Format:** Original file with completion metadata

### 7. Failed_Queue

**Purpose:** Failed actions for retry/review.

**Who writes:** Orchestrator (on error)

**Processing:**
- Auto-retry up to 3 times
- After 3 failures, requires human review

---

## Logs

### Log Files

| Log File | Purpose | Updated By |
|----------|---------|------------|
| `YYYY-MM-DD_orchestrator.log` | Orchestrator activity | Orchestrator |
| `orchestrator_state.json` | State persistence | Orchestrator |
| `gmail_processed_ids.json` | Processed email IDs | Gmail Watcher |
| `linkedin_state.json` | LinkedIn state | LinkedIn Watcher |
| `rejected_actions.log` | Rejected actions | Orchestrator |
| `vault_sync.log` | Git sync activity | vault_sync.py |
| `cron.log` | Cron job output | Cron |

### State Files

**gmail_processed_ids.json:**
```json
{
  "processed_ids": [
    "19cd0aa8032661e4",
    "19cd1861fb1a9076"
  ],
  "last_updated": "2026-03-14T14:00:00"
}
```

**orchestrator_state.json:**
```json
{
  "seen_files": [
    "EMAIL_project_update_20260314_143000.md",
    "LINKEDIN_MESSAGE_20260314_140000.md"
  ],
  "watcher_pids": {
    "filesystem": 12345,
    "gmail": 12346,
    "linkedin": 12347
  }
}
```

---

## Content_To_Post

### Folder Structure

```
Content_To_Post/
├── queued/                    # Posts ready to publish
│   └── LINKEDIN_POST_topic_20260314_143000.md
├── posted/                    # Published posts
│   └── LINKEDIN_POST_topic_20260314_143000.md
└── rejected/                  # Rejected posts
    └── LINKEDIN_POST_topic_20260314_143000.md
```

### Post File Format

```markdown
---
platform: linkedin
created: 2026-03-14T14:30:00
scheduled: 2026-03-14T18:00:00
status: queued
hashtags:
  - AI
  - Automation
---

# Post Content

Your post text here...

#hashtag1 #hashtag2
```

---

## Obsidian Integration

The vault is compatible with Obsidian:

1. Open Obsidian
2. Select "Open folder as vault"
3. Navigate to `AI_Employee_Vault/`

**Features:**
- Graph view of linked notes
- Quick file navigation
- Markdown preview
- Tags and links

---

## Related Documentation

- [Project Architecture](PROJECT_ARCHITECTURE.md)
- [Agent Skills Reference](AGENT_SKILLS_REFERENCE.md)
- [Getting Started Guide](GETTING_STARTED.md)

---

*Generated: 2026-03-14*
*AI Employee Project - Platinum Tier Documentation*