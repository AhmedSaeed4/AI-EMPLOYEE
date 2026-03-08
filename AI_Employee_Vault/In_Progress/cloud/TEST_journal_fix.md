---
type: finance
status: needs_action
created_by: human
created_at: 2026-03-08T22:45:00
priority: test
---

# TEST: Journal Fix for Draft Invoice Creation

## Context
The previous test (`TEST_draft_invoice.md`) revealed that Odoo requires an explicit `journal_id` when creating invoices. The code has been fixed to automatically find the default Sales Journal.

## Test Task
Create a draft invoice to verify the journal_id fix works.

## Invoice Details:
- **Customer:** Test Client
- **Description:** Web Development Services (Journal Fix Test)
- **Hours:** 10
- **Rate:** $100/hour
- **Total Amount:** $1,000.00

## Expected Result:
- Draft invoice created successfully in Odoo
- Invoice state: "draft"
- Journal assigned (Sales Journal)
- No "Missing Journal" error

## Instructions for Finance Agent:
1. Get customer info for "Test Client" (or create if not exists)
2. Create draft invoice with the details above
3. Verify the invoice was created with a valid journal_id
4. Report the invoice details including the journal used
