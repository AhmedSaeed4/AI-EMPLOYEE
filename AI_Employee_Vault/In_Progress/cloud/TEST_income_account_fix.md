---
type: finance
status: needs_action
created_by: human
created_at: 2026-03-08T22:50:00
priority: test
---

# TEST: Income Account Fix for Draft Invoice Creation

## Context
Previous test revealed Odoo also requires an income account for invoice line items. The code has been updated to find the default income account automatically.

## Test Task
Create a draft invoice to verify both journal_id AND income_account_id work together.

## Invoice Details:
- **Customer:** Test Client
- **Description:** Web Development Services (Full Fix Test)
- **Hours:** 10
- **Rate:** $100/hour
- **Total Amount:** $1,000.00

## Expected Result:
- Draft invoice created successfully in Odoo
- Invoice state: "draft"
- Journal assigned (Sales Journal)
- Income account assigned
- Return invoice_id and URL for review

## Instructions for Finance Agent:
1. Get customer info for "Test Client"
2. Create draft invoice with both journal and income account
3. Report full invoice details
