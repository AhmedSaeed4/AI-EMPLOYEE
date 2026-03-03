---
description: Check accounting status from Odoo - revenue, expenses, invoices, payments.
---

# Check Accounting

Reads accounting data from Odoo and provides a summary of financial status.

## Usage

```
/check-accounting
```

Shows summary of:
- Recent invoices
- Total revenue (last 30 days)
- Total expenses (last 30 days)
- Outstanding invoices
- Payment status

## Instructions to Claude

1. **Use odoo MCP** to fetch data:
   ```
   mcp__odoo__get_invoices(limit=10)

   mcp__odoo__get_revenue(days=30)

   mcp__odoo__get_expenses(days=30)
   ```

2. **Format output** as a readable summary:
   ```markdown
   ## Accounting Summary

   ### Revenue (Last 30 Days)
   Total: $X,XXX

   ### Expenses (Last 30 Days)
   Total: $X,XXX

   ### Net Profit
   $X,XXX

   ### Recent Invoices
   - INV/2026/0001 - $500 - Acme Corp - Paid
   - INV/2026/0002 - $1200 - Beta Inc - Draft
   ```

3. **Optional**: Update Dashboard.md with latest revenue total

## Examples

**Default: Last 30 days**
```
User: /check-accounting
AI: [Shows 30-day revenue/expense summary]
```

**Custom period**
```
User: /check-accounting for last 7 days
AI: [Shows 7-day summary]
```

**Specific invoices**
```
User: /check-accounting show all invoices
AI: [Shows list of all invoices]
```
