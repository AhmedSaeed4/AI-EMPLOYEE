# Cloud Agents Guide

Cloud Agents are autonomous AI agents built with OpenAI Agents SDK that run on the cloud VM for 24/7 task processing.

---

## Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLOUD ORCHESTRATOR                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    TriageAgent                          │   │
│  │  - Routes tasks to specialists                          │   │
│  │  - Analyzes task type                                   │   │
│  │  - Handoffs to appropriate agent                        │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│                          │                                      │
│          ┌───────────────┼───────────────┐                     │
│          │               │               │                     │
│          ▼               ▼               ▼                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │ EmailAgent │  │SocialAgent │  │FinanceAgent│               │
│  │            │  │            │  │            │               │
│  │ - Reply    │  │ - Posts    │  │ - Invoices │               │
│  │ - Draft    │  │ - Schedule │  │ - Reports  │               │
│  │ - Search   │  │ - Analyze  │  │ - Odoo MCP │               │
│  └────────────┘  └────────────┘  └────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Agents

| Agent | Purpose | Tools | MCP Integration |
|-------|---------|-------|-----------------|
| **TriageAgent** | Routes tasks to specialists | Handoffs | Attaches MCP to specialists |
| **EmailAgent** | Email processing | Vault tools | None |
| **SocialAgent** | Social media management | Vault tools | None |
| **FinanceAgent** | Accounting/invoicing | Vault tools | **Odoo MCP** (per-request) |

---

## File Structure

```
ai_employee_scripts/cloud/
├── __init__.py
├── cloud_orchestrator.py      # Main orchestrator
├── test_cloud_agent.py        # Test script
│
├── agent_definitions/
│   ├── __init__.py
│   ├── base_agent.py          # Base agent with guardrails
│   ├── triage_agent.py        # Router agent
│   ├── email_agent.py         # Email specialist
│   ├── social_agent.py        # Social media specialist
│   ├── finance_agent.py       # Finance specialist
│   └── models.py              # Shared data models
│
├── mcp_servers/
│   ├── __init__.py
│   └── odoo_server.py         # Odoo MCP (read-only + draft-only)
│
├── guardrails/
│   ├── __init__.py
│   ├── input_guardrails.py    # Input validation
│   └── output_guardrails.py   # Output validation
│
├── tools/
│   ├── __init__.py
│   ├── vault_tools.py         # Vault file operations
│   ├── file_tools.py          # File system tools
│   └── git_tools.py           # Git operations
│
├── config/
│   ├── __init__.py
│   └── settings.py            # Configuration
│
└── utils/
    ├── __init__.py
    └── logger.py              # Logging utilities
```

---

## Agent Details

### TriageAgent

**Purpose:** Analyzes incoming tasks and routes them to the appropriate specialist.

**File:** `cloud/agent_definitions/triage_agent.py`

**Behavior:**
1. Receives task from orchestrator
2. Analyzes task type (email, social, finance)
3. Hands off to appropriate specialist
4. Attaches MCP servers to specialist if needed

**Handoffs:**
- Email tasks → EmailAgent
- Social media tasks → SocialAgent
- Finance tasks → FinanceAgent (with Odoo MCP)

---

### EmailAgent

**Purpose:** Handles email-related tasks.

**File:** `cloud/agent_definitions/email_agent.py`

**Capabilities:**
- Draft email replies
- Summarize email threads
- Extract action items
- Categorize emails

**Tools:**
- `read_vault_file` - Read files from vault
- `write_vault_file` - Write files to vault
- `list_vault_files` - List files in folder

---

### SocialAgent

**Purpose:** Handles social media tasks.

**File:** `cloud/agent_definitions/social_agent.py`

**Capabilities:**
- Generate post ideas
- Schedule posts
- Analyze engagement
- Create content calendar

**Tools:**
- `read_vault_file` - Read files from vault
- `write_vault_file` - Write files to vault
- `list_vault_files` - List files in folder

---

### FinanceAgent

**Purpose:** Handles accounting and finance tasks.

**File:** `cloud/agent_definitions/finance_agent.py`

**Capabilities:**
- Create draft invoices
- Get customer information
- Check invoice history
- Generate financial reports

**MCP Integration:** Odoo MCP (per-request lifecycle)

**Tools:**
- `get_customer` - Get customer info from Odoo
- `search_partners` - Search customers/vendors
- `get_invoice_history` - Get customer's past invoices
- `get_pricing` - Get service pricing
- `create_draft_invoice` - Create draft invoice

**Security:** Read-only + draft-only (cannot post/finalize invoices)

---

## MCP Integration

### Per-Request Lifecycle Pattern

**Critical:** MCP servers must be created and connected **per-request**, not globally cached.

```python
# ❌ WRONG - Global caching (causes issues)
server = MCPServerStdio(...)
agent.mcp_servers = [server]

# ✅ CORRECT - Per-request lifecycle
async def handle_request():
    server = MCPServerStdio(...)
    agent.mcp_servers = [server]
    await server.connect()
    try:
        result = await Runner.run(agent, ...)
    finally:
        await server.cleanup()
        agent.mcp_servers = []
```

### Odoo MCP Server

**File:** `cloud/mcp_servers/odoo_server.py`

**Tools:**

| Tool | Purpose | Status |
|------|---------|--------|
| `get_customer` | Get customer information | ✅ |
| `search_partners` | Search for customers/vendors | ✅ |
| `get_invoice_history` | Get customer's past invoices | ✅ |
| `get_pricing` | Get service pricing rates | ✅ |
| `create_draft_invoice` | Create draft invoice | ✅ |
| `get_available_tools` | List all tools | ✅ |

**Security:** Read-only + draft-only (cloud cannot post/finalize invoices)

---

## Guardrails

### Input Guardrails

**File:** `cloud/guardrails/input_guardrails.py`

**Purpose:** Validate and sanitize input before processing.

**Checks:**
- Input length limits
- Content type validation
- Injection attack prevention
- PII detection

### Output Guardrails

**File:** `cloud/guardrails/output_guardrails.py`

**Purpose:** Validate and sanitize output before returning.

**Checks:**
- Output format validation
- Sensitive data filtering
- Response length limits

---

## Configuration

### Settings

**File:** `cloud/config/settings.py`

```python
# Agent settings
DEFAULT_MODEL = "gpt-4o"
MAX_TOKENS = 4096
TEMPERATURE = 0.7

# MCP settings
ODOO_MCP_PATH = "cloud/mcp_servers/odoo_server.py"

# Guardrail settings
MAX_INPUT_LENGTH = 10000
MAX_OUTPUT_LENGTH = 5000
```

---

## Usage

### Running Cloud Orchestrator

```bash
cd ai_employee_scripts
uv run python cloud/cloud_orchestrator.py
```

### Testing Cloud Agents

```bash
cd ai_employee_scripts
uv run python cloud/test_cloud_agent.py
```

### With PM2

```bash
pm2 start ecosystem.cloud.config.js
```

---

## Testing

### Test Script

**File:** `cloud/test_cloud_agent.py`

```bash
# Run tests
cd ai_employee_scripts
uv run python cloud/test_cloud_agent.py
```

### Test Cases

1. **Triage Test:** Verify task routing
2. **Email Test:** Verify email processing
3. **Social Test:** Verify social media handling
4. **Finance Test:** Verify Odoo MCP integration

---

## Troubleshooting

### "FinanceAction is not defined"

**Cause:** Import structure issue

**Solution:** Separated models import from SDK import

### "cannot import ClientSession"

**Cause:** Namespace collision

**Solution:** Renamed `cloud/mcp/` → `cloud/mcp_servers/`

### Tools not executing

**Cause:** Wrong agent instance

**Solution:** Attach MCP to handoff agent, not global cache

### Missing Journal

**Cause:** Odoo requires explicit journal_id

**Solution:** Auto-find Sales Journal in code

### Serialization error

**Cause:** `browse()` returns functions

**Solution:** Use `Journal.read()` instead

---

## Key Fixes Applied

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| `FinanceAction is not defined` | Import structure | Separated models import from SDK import |
| `cannot import ClientSession` | Namespace collision | Renamed `cloud/mcp/` → `cloud/mcp_servers/` |
| Tools not executing | Wrong agent instance | Attach MCP to handoff agent, not global cache |
| Missing Journal | Odoo requires explicit journal_id | Auto-find Sales Journal |
| Serialization error | `browse()` returns functions | Use `Journal.read()` instead |
| Invalid field `residual` | Wrong field name | Use `amount_residual` |
| Invalid field `default_credit_account_id` | Wrong field name | Use `default_account_id` |

---

## Related Documentation

- [Cloud Deployment Guide](CLOUD_DEPLOYMENT_GUIDE.md)
- [MCP Integration Guide](../MCP_INTEGRATION_GUIDE.md)
- [Agent Skills Reference](AGENT_SKILLS_REFERENCE.md)

---

*Generated: 2026-03-14*
*AI Employee Project - Platinum Tier Documentation*