---
description: Approve a pending action by moving it from Pending_Approval to Approved folder. Triggers execution via Orchestrator.
---

# Approve Action Skill

This skill approves a pending action that requires human authorization.

## How It Works

1. Lists all pending actions in `Pending_Approval/` folder
2. User selects an action to approve
3. Moves the file to `Approved/` folder
4. Orchestrator detects and executes the approved action

## Usage

```
/approve-action
```

Or with specific action:

```
/approve-action EMAIL_invoice_client_20260212
```

## Human-in-the-Loop Flow

```
┌─────────────────────────────────────────────────────────┐
│  Workflow                                          │
├─────────────────────────────────────────────────────────┤
│  1. AI detects action requiring approval              │
│  2. AI creates approval file in                   │
│     Pending_Approval/                               │
│  3. Human reviews the approval request              │
│  4. Human invokes /approve-action                  │
│  5. File moves to Approved/                        │
│  6. Orchestrator executes the action              │
│  7. File moves to Done/ with execution result       │
└─────────────────────────────────────────────────────────┘
```

## Instructions to Claude

When this skill is invoked:

1. **List all pending actions** in `Pending_Approval/` folder
2. **Show each action** with:
   - Action type (email, payment, post, etc.)
   - Target/recipient
   - Amount (if payment)
   - Risk level
3. **Ask user** which action to approve (or show all)
4. **If user specifies** an action name, approve that specific one
5. **If no name specified**, show the list and ask to choose
6. **Move approved file** from `Pending_Approval/` to `Approved/`
7. **Inform user** that action is queued for execution
8. **Remind user** that Orchestrator will execute it within 30 seconds

## Example Output

```
Pending Actions:

1. PAYMENT_vendor_x_20260212.md
   - Type: Payment
   - To: Vendor X
   - Amount: $250.00
   - Risk: HIGH

2. EMAIL_client_abc_20260212.md
   - Type: Email
   - To: client@abc.com
   - Subject: Invoice #1234
   - Risk: LOW

Which action to approve? (enter number or name)
```

After approval:

```
✅ Approved: PAYMENT_vendor_x_20260212.md
📤 Moved to Approved folder
⏱️ Orchestrator will execute within 30 seconds
```

## Security Rules

**Always verify before approving:**

| Action Type | Verify Before Approving |
|-------------|------------------------|
| Payment | Recipient, amount, invoice/receipt |
| Email (new contact) | Recipient address, content |
| Social Media Post | Content, hashtags, timing |
| File Deletion | File path, reason |
| Credential Access | Purpose, scope |

**High Risk Actions** (always double-check):
- Payments to new recipients
- Payments > $100
- Bulk emails
- Deleting files outside vault
- Sharing credentials

## Cancel an Approval

To cancel a pending action, use:

```
/reject-action [action_name]
```

This moves the file to `Rejected/` folder instead.
