---
description: Create a draft invoice in Odoo accounting system. Requires human approval before posting.
---

# Create Invoice

Creates a draft invoice in Odoo for a customer. The invoice will be in "draft" state and requires human approval before being posted.

## Usage

```
/create-invoice
```

When invoked, ask the user for:
- Customer name
- Invoice amount
- Description of services/products

## Instructions to Claude

1. **Ask for details** if not provided:
   - Customer name
   - Amount
   - Description

2. **Use odoo MCP** to create draft invoice:
   ```python
   response = mcp__odoo__create_draft_invoice(
     partner_name="[customer name]",
     amount=[amount],
     description="[description]"
   )
   ```

3. **Parse JSON response** to extract invoice details:
   ```python
   import json
   data = json.loads(response)
   invoice_id = data["invoice_id"]
   invoice_name = data["name"]  # May be False for drafts
   amount = data["amount"]
   url = data["url"]
   ```

4. **Create approval file** in `Pending_Approval/`:
   ```markdown
   ---
   type: odoo_invoice
   invoice_id: [invoice_id from response]
   invoice_name: [invoice_name from response, or "Draft"]
   amount: [amount]
   customer: [customer name]
   created: [timestamp]
   status: pending_approval
   url: [url from response]
   ---

   # Invoice Approval Required

   ## Invoice Details
   - **Invoice ID:** [invoice_id]
   - **Invoice:** [invoice_name] (Draft - name assigned on posting)
   - **Customer:** [customer name]
   - **Amount:** $[amount]
   - **Description:** [description]

   ## To Approve
   1. Review in Odoo: [url]
   2. Move this file to /Approved/ folder
   3. Run /execute-approved to post the invoice

   ## To Reject
   Move this file to /Rejected/ folder
   ```

5. **Update Dashboard.md** with pending invoice count

## Example Flow

```
User: /create-invoice
AI: Which customer?
User: Acme Corp
AI: Amount and description?
User: $1500 for AI Agent Development
AI: [Creates draft in Odoo] → [Parses JSON] → [Creates approval file with invoice_id]
```

## Important Notes

- **invoice_id is the key identifier** - Use this for posting (drafts don't have names yet)
- **invoice_name may be False** - Draft invoices get their name only after posting
- **Both are stored** - invoice_id for posting, invoice_name for human reference

## Safety Rules

- Always create as **draft** (never post directly)
- Invoice >$1000 requires additional review note
- New customers always require approval
