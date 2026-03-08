---
type: finance
status: needs_action
created_by: human
created_at: 2026-03-08T22:55:00
priority: test
---

# TEST: Journal + Income Account from Journal Fix

## Context
Updated code to get income account from the journal's default credit account (instead of searching with wrong field).

## Test Task
Create a draft invoice using the journal's default credit account for income.

## Invoice Details:
- **Customer:** Test Client
- **Description:** Web Development Services (Final Fix Test)
- **Hours:** 10
- **Rate:** $100/hour
- **Total:** $1,000.00

## Expected Result:
- Draft invoice created successfully
- Uses Sales Journal
- Uses Journal's default credit account for income
- Returns invoice_id, amount, state, URL

## Instructions:
1. Get customer info for "Test Client"
2. Create draft invoice with proper journal and income account
3. Report full details
