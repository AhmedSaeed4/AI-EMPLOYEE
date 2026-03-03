---
type: odoo_invoice
invoice_id: 8
invoice_name: Draft
amount: 50.0
customer: Ahmed Saeed
created: 2026-02-22T08:15:00
status: pending_approval
url: http://localhost:8069/web#id=8&model=account.move
---

# Invoice Approval Required

## Invoice Details
- **Invoice ID:** 8
- **Invoice:** Draft (name assigned on posting)
- **Customer:** Ahmed Saeed <ahmedbilalyt20@gmail.com>
- **Amount:** $50.00
- **Description:** 3D video edit

## Source
Invoice request from email: "can you send me a invoice for 50$ for the 3d video edit you did thanks"

## To Approve
1. Review in Odoo: http://localhost:8069/web#id=8&model=account.move
2. Move this file to /Approved/ folder
3. Run /execute-approved to post the invoice

## To Reject
Move this file to /Rejected/ folder
