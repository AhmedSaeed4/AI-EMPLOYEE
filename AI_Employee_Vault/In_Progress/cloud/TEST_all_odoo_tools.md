---
type: finance
status: needs_action
created_by: human
created_at: 2026-03-08T23:30:00
priority: test
---

# TEST: All Odoo MCP Tools After Fixes

## Context
Fixed all issues in the Odoo MCP server:
- `create_draft_invoice`: Fixed `default_account_id` field and read method
- `get_invoice_history`: Fixed `amount_residual` field

## Test Task
Test all Odoo MCP tools through the Finance Agent to verify they work end-to-end.

## Test Checklist:

### 1. get_customer
- Get info for "Test Client"
- Verify returns: name, email, total_invoiced, debit, credit

### 2. search_partners
- Search for "Test"
- Verify returns list of partners with id, name, email

### 3. get_invoice_history
- Get invoice history for "Test Client"
- Verify returns: invoice, date, amount, state, payment_status, amount_due

### 4. get_pricing
- Get pricing for "consulting"
- Verify returns hourly_rate and daily_rate

### 5. create_draft_invoice
- Customer: Test Client
- Description: Comprehensive MCP Test
- Hours: 8
- Rate: $125/hour
- Total: $1,000.00
- Verify: invoice_id, state=draft, amount, URL

### 6. get_available_tools
- List all available tools
- Verify count = 6

## Expected Result:
All tools execute successfully and return proper JSON responses.

## Instructions:
Run each tool and report the results in a summary table.
