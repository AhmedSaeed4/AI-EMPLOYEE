---
type: finance
status: needs_action
created_by: human
created_at: 2026-03-08T23:20:00
priority: test
---

# TEST: Final Invoice Creation Fix

## Context
Fixed the `create_draft_invoice` tool:
1. Use `default_account_id` (not `default_credit_account_id`)
2. Use `Journal.read()` to get the value (not `browse()`)

## Test Task
Create a draft invoice through the agent to verify the MCP tool works end-to-end.

## Invoice Details:
- **Customer:** Test Client
- **Description:** Final Test Invoice - Agent Verification
- **Hours:** 5
- **Rate:** $150/hour
- **Total:** $750.00

## Expected Result:
- Draft invoice created successfully
- Invoice state: "draft"
- Returns invoice_id, amount, and URL

## Instructions:
Use the create_draft_invoice MCP tool to create this invoice.
