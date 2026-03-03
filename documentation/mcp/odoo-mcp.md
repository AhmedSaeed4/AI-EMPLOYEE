# Odoo MCP Server Documentation

## Overview

The Odoo MCP Server provides accounting integration via Odoo 19+ JSON-RPC API. It enables reading financial data (invoices, payments, revenue, expenses), creating draft invoices, and posting approved invoices through the Model Context Protocol (MCP).

**Location:** `ai_employee_scripts/mcp_servers/odoo_mcp.py`

**MCP Name:** `odoo`

---

## Features

### Available Tools

| Tool | Description | Async |
|------|-------------|-------|
| `get_invoices` | Fetch recent invoices from Odoo | Yes |
| `get_revenue` | Get total revenue for a period | Yes |
| `get_expenses` | Get total vendor bills/expenses | Yes |
| `get_payments` | Fetch payment records | Yes |
| `create_draft_invoice` | Create a draft invoice (not posted) | Yes |
| `post_invoice` | Post a draft invoice (requires approval) | Yes |
| `get_partners` | Get list of customers/vendors | Yes |

### Tool Parameters

#### `get_invoices`

```python
mcp__odoo__get_invoices(
    limit: int = 10,    # Maximum number of invoices
    state: str = ""     # Filter: '', 'draft', 'posted', 'paid'
)
```

**Returns:** List of invoices with customer, amount, date, state, payment status

#### `get_revenue`

```python
mcp__odoo__get_revenue(
    days: int = 30      # Number of days to look back
)
```

**Returns:** Revenue summary with total, invoice count, recent invoices

#### `get_expenses`

```python
mcp__odoo__get_expenses(
    days: int = 30      # Number of days to look back
)
```

**Returns:** Expense summary with total, bill count, recent bills

#### `get_payments`

```python
mcp__odoo__get_payments(
    limit: int = 20,            # Maximum number of payments
    payment_type: str = ""      # Filter: '', 'inbound', 'outbound'
)
```

**Returns:** List of payments with type, amount, date, state, journal, linked invoices

#### `create_draft_invoice`

```python
mcp__odoo__create_draft_invoice(
    partner_name: str,    # Customer name
    amount: float,        # Invoice amount
    description: str      # Line item description
)
```

**Returns:** JSON string with invoice details:
```json
{
  "invoice_id": 123,
  "name": "INV/2026/0001",
  "amount": 1500.00,
  "customer": "Client Name",
  "state": "draft",
  "url": "http://localhost:8069/web#id=123&model=account.move"
}
```

#### `post_invoice`

```python
mcp__odoo__post_invoice(
    invoice_name: str = None,    # Invoice name (e.g., "INV/2026/0001")
    invoice_id: int = None       # Direct Odoo invoice ID
)
```

**Note:** At least one parameter required. For draft invoices, use `invoice_id`.

**Returns:** Confirmation with final invoice name and amount

#### `get_partners`

```python
mcp__odoo__get_partners(
    limit: int = 20      # Maximum number of partners
)
```

**Returns:** List of companies with email and phone

---

## Setup Guide

### Prerequisites

1. **Odoo 19+** instance (local or cloud)
2. **Python 3.13+** with UV package manager
3. **Odoo admin credentials** or user with accounting access

### Step 1: Install/Run Odoo

**Option A: Local Docker (Recommended for development)**

```bash
docker run -d -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo \
  -e POSTGRES_DB=postgres --name db postgres:16

docker run -d -p 8069:8069 --name odoo --link db:db \
  -e HOST=db -e USER=odoo -e PASSWORD=odoo \
  odoo:19
```

**Option B: Odoo.sh (Cloud)**

1. Sign up at [odoo.sh](https://odoo.sh)
2. Create a new database
3. Note your URL, database name, and credentials

**Option C: Local Installation**

Download from [odoo.com](https://www.odoo.com/page/download) and follow installation guide.

### Step 2: Enable Accounting Module

1. Log in to Odoo
2. Go to **Apps** → Search **"Accounting"**
3. Click **Install**
4. Wait for installation to complete

### Step 3: Configure Connection

Add to `ai_employee_scripts/.env`:

```bash
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin
ODOO_PASSWORD=admin
```

**Replace with your actual values if different.**

### Step 4: Install Dependencies

```bash
cd ai_employee_scripts
uv sync
```

Required packages:
- `odoorpc>=0.10.1`
- `mcp>=0.1.0`

---

## Configuration

### MCP Server Configuration

The Odoo MCP is configured in `AI_Employee_Vault/.mcp.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/ai-employee/ai_employee_scripts",
        "run",
        "mcp_servers/odoo_mcp.py"
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

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ODOO_URL` | Odoo instance URL | `http://localhost:8069` | No |
| `ODOO_DB` | Database name | `odoo` | No |
| `ODOO_USER` | Database user | `admin` | No |
| `ODOO_PASSWORD` | Database password | `admin` | No |

---

## Authentication

### JSON-RPC Authentication

The Odoo MCP uses JSON-RPC authentication (not OAuth):

```
┌─────────────────────────────────────┐
│  Odoo Instance Running              │
│  (Docker/Cloud/Local)               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Enable Accounting Module           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Add credentials to .env:           │
│  ODOO_URL=http://localhost:8069     │
│  ODOO_DB=odoo                       │
│  ODOO_USER=admin                    │
│  ODOO_PASSWORD=admin                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  MCP Server connects via JSON-RPC   │
│  odoorpc.ODOO(hostname, port)       │
│  odoo.login(db, user, password)     │
└─────────────────────────────────────┘
```

---

## Usage Examples

### In Agent Skills

#### Checking Accounting Status (check-accounting skill)

```python
# Get financial overview
invoices = mcp__odoo__get_invoices(limit=10)
revenue = mcp__odoo__get_revenue(days=30)
expenses = mcp__odoo__get_expenses(days=30)
payments = mcp__odoo__get_payments(limit=20, payment_type="inbound")
```

#### Creating Draft Invoice (create-invoice skill)

```python
# Create draft invoice
import json
response = mcp__odoo__create_draft_invoice(
    partner_name="Acme Corp",
    amount=1500.00,
    description="Web Development Services - January 2026"
)

# Parse JSON response
data = json.loads(response)
invoice_id = data["invoice_id"]  # Use this for posting
invoice_name = data["name"]        # May be False for drafts
```

#### Posting Approved Invoice (execute-approved skill)

```python
# Post draft invoice
result = mcp__odoo__post_invoice(
    invoice_id=123  # Use invoice_id for drafts
)
```

---

## Files and Paths

| File | Location | Purpose |
|------|----------|---------|
| MCP Server | `ai_employee_scripts/mcp_servers/odoo_mcp.py` | Main MCP server code |
| Credentials | `ai_employee_scripts/.env` | Odoo connection credentials |
| MCP Config | `AI_Employee_Vault/.mcp.json` | MCP server configuration |

---

## Troubleshooting

### Issue: "Failed to connect to Odoo"

**Error Message:**
```
❌ Failed to connect to Odoo: [Errno 111] Connection refused
```

**Solution:**
1. Verify Odoo is running: `docker ps` or check cloud status
2. Check `ODOO_URL` in `.env` matches your Odoo instance
3. Test connection: Open `http://localhost:8069` in browser
4. Check firewall/network settings

---

### Issue: "Access Denied"

**Error Message:**
```
❌ Failed to connect to Odoo: AccessDenied
```

**Solution:**
1. Verify `ODOO_USER` and `ODOO_PASSWORD` are correct
2. Ensure user has **Accounting** module access
3. Check user permissions in Odoo: **Settings** → **Users** → **Your User**

---

### Issue: "Database not found"

**Error Message:**
```
❌ Failed to connect to Odoo: Database not found
```

**Solution:**
1. Verify `ODOO_DB` name in `.env`
2. List databases: Visit `http://localhost:8069/web/database/manager`
3. Use exact database name (case-sensitive)

---

### Issue: Invoice not found when posting

**Error Message:**
```
Error: Invoice not found (ID: 123)
```

**Solution:**
1. Verify `invoice_id` is correct
2. Check invoice exists in Odoo
3. For draft invoices, use `invoice_id` (not `invoice_name`)
4. For posted invoices, use `invoice_name`

---

### Issue: "Invoice already posted"

**Message:**
```
Invoice INV/2026/0001 is already posted (state: posted)
```

**Cause:** Invoice was already posted

**Solution:** This is informational - no action needed. Invoice is already confirmed.

---

## Invoice Workflow

### Draft → Posted Flow

```
┌─────────────────────────────────────┐
│  1. Create Draft Invoice            │
│  mcp__odoo__create_draft_invoice()  │
│                                     │
│  Returns: invoice_id, name (False)  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. Create Approval File            │
│  Pending_Approval/                  │
│  type: odoo_invoice                 │
│  invoice_id: [id]                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. Human Reviews & Approves        │
│  Move to Approved/                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  4. Execute Approved                │
│  mcp__odoo__post_invoice(           │
│    invoice_id=[id]                  │
│  )                                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  5. Invoice Posted                  │
│  State: posted                      │
│  Name: INV/2026/0001                │
└─────────────────────────────────────┘
```

---

## Skills Using Odoo MCP

| Skill | Tools Used | Description |
|-------|------------|-------------|
| `check-accounting` | All read tools | Financial status overview |
| `create-invoice` | `create_draft_invoice` | Create draft invoices |
| `execute-approved` | `post_invoice` | Post approved invoices |
| `weekly-audit` | All read tools | CEO briefing with financials |

---

## Dependencies

```
odoorpc>=0.10.1
mcp>=0.1.0
```

Install via:
```bash
cd ai_employee_scripts
uv sync
```

---

## Odoo Data Models Used

| Model | Purpose |
|-------|---------|
| `account.move` | Invoices and bills |
| `account.payment` | Payments |
| `res.partner` | Customers/Vendors |

---

## Security Notes

1. **Never commit** `.env` file with Odoo credentials to git
2. **Use read-only user** for operations that don't need write access
3. **Odoo URL** should be `localhost` for development
4. **Password strength** - Use strong passwords for production
5. **Database backup** - Regular backups recommended

---

## Related Documentation

- [Odoo Accounting Documentation](https://www.odoo.com/documentation/19.0/accounting.html)
- [Odoo RPC API](https://www.odoo.com/documentation/15.0/developer/reference/external_api.html)
- [ODOORPC Documentation](https://python-odoorpc.readthedocs.io/)
- [Check Accounting Skill](../../.claude/skills/check-accounting/SKILL.md)
- [Create Invoice Skill](../../.claude/skills/create-invoice/SKILL.md)
- [Execute Approved Skill](../../.claude/skills/execute-approved/SKILL.md)

---

*Generated: 2026-02-28*
*AI Employee Project - Gold Tier Documentation*
