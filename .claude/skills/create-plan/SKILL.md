---
description: Create a Plan.md file for a task that requires multiple steps. Reads task details from Needs_Action and generates a structured plan.
---

# Create Plan Skill

This skill creates a structured Plan.md file for tasks that require multiple steps.

## How It Works

1. Reads the task file from Needs_Action folder
2. Analyzes what needs to be done
3. Creates a Plan.md file in Plans folder with:
   - Objective
   - Step-by-step checklist
   - Resources needed
   - Approval requirements (if sensitive)

## Usage

```
/create-plan [task_name]
```

Example:
```
/create-plan FILE_email_urgent_client_20260212_053000
```

## Plan Template

```markdown
---
created: [timestamp]
status: pending
original_task: [link to Needs_Action file]
priority: [high/medium/low]
---

# Objective
[What needs to be accomplished]

## Steps
- [ ] Step 1: [Description]
- [ ] Step 2: [Description]
- [ ] Step 3: [Description]
- [ ] Step 4: [Description]

## Resources Needed
- [ ] Information: [what info is needed]
- [ ] Tools: [what tools/APIs are needed]
- [ ] Approval: [if human approval is required]

## Timeline
- **Estimated time:** [hours/days]
- **Deadline:** [if applicable]

## Notes
[Any additional context or constraints]
```

## Instructions to Claude

When this skill is invoked:

1. **Read the task file** from Needs_Action folder
2. **Analyze the task** to determine what needs to be done
3. **Create a Plan.md file** in the Plans folder
4. **Include all relevant steps** as checkboxes
5. **Mark approval required** if the task involves:
   - Financial transactions (> $100)
   - Sending emails to new contacts
   - Posting on social media
   - Sharing confidential information
6. **Update the original task file** to reference the new Plan

## Example Plan

```markdown
---
created: 2026-02-12T05:30:00Z
status: pending
original_task: ../Needs_Action/FILE_client_invoice_request_20260212.md
priority: high
---

# Objective
Generate and send invoice to Client A for January 2026 services.

## Steps
- [ ] Review contract/rates for Client A
- [ ] Calculate hours worked in January
- [ ] Generate invoice PDF
- [ ] Create approval request for sending
- [ ] Wait for approval
- [ ] Send invoice via email
- [ ] Log transaction in Accounting

## Resources Needed
- [ ] Contract: AI_Employee_Vault/Clients/Client_A_contract.md
- [ ] Hours log: AI_Employee_Vault/Accounting/2026-01_hours.md
- [ ] Invoice template: ai_employee_scripts/templates/invoice_template.md
- [ ] Approval: Required (sending email to new recipient)

## Timeline
- **Estimated time:** 2 hours
- **Deadline:** 2026-02-14

## Notes
- Client A requires invoices by 15th of each month
- Payment terms: Net 30 days
- Rate: $75/hour for consulting work
```
