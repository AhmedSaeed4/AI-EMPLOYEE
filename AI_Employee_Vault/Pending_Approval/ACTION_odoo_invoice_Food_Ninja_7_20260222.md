---
type: odoo_invoice
invoice_id: 7
invoice_name: Draft
amount: 300.0
customer: Food Ninja
created: 2026-02-22T08:15:00
status: pending_approval
url: http://localhost:8069/web#id=7&model=account.move
---

# Invoice Approval Required

## Invoice Details
- **Invoice ID:** 7
- **Invoice:** Draft (name assigned on posting)
- **Customer:** Food Ninja <foodninja2069@gmail.com>
- **Amount:** $300.00
- **Description:** PC power supply

## Source
Invoice request from email: "send me an invoice for 300 dollar for the pc power supply thanks"

## To Approve
1. Review in Odoo: http://localhost:8069/web#id=7&model=account.move
2. Move this file to /Approved/ folder
3. Run /execute-approved to post the invoice

## To Reject
Move this file to /Rejected/ folder
