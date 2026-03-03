---
description: Process task files from the Needs_Action folder. Handles emails, LinkedIn messages, and files. Updates Dashboard.md after completing tasks.
---

# Process File

Process task files from the `AI_Employee_Vault/Needs_Action/` folder. This skill reads the file content, determines what action is needed, and either executes it or creates a plan for human review.

**Supported:** Emails (auto-reply), LinkedIn messages (auto-reply or human review), File processing (summarize, extract), Invoice requests (delegates to /create-invoice)

## What This Does

1. Lists available files in the Needs_Action folder
2. Reads the specified file content
3. **FIRST: Check for invoice requests** - Delegates to /create-invoice skill
4. Then analyzes content for other appropriate actions
5. Either executes simple actions or creates a plan for complex ones
6. Processes all files if requested without specifying a filename
7. Moves completed files to Done/ folder

**Note:** To send email replies, use the `gmail` MCP server.

## Usage

```
/process-file <filename> or /process-file
```

### Example

```
/process-file invoice.pdf
/process-file meeting_notes.txt
/process-file process all files
```

## Supported Actions

| File Type | Possible Actions |
|------------|-----------------|
| **Emails** | Invoice requests, auto-reply simple emails, flag important ones for review |
| **LinkedIn Messages** | Invoice requests, auto-reply greetings/simple questions, flag complex ones for review |
| **Images** | Extract text, generate description, create summary |
| **PDFs** | Extract text, log invoices, create metadata |
| **Text files** | Parse content, extract tasks, summarize |
| **Documents** | Read content, determine next steps |

---

## PRIORITY 1: Invoice Request Detection (Do This FIRST!)

**CRITICAL:** Before processing ANY email or LinkedIn message, FIRST check if it's an invoice request.

### Invoice Keywords to Look For:
- "send me an invoice", "can you invoice me", "need an invoice"
- "how do I pay", "payment request", "bill me", "invoice for"
- "create invoice", "generate invoice", "new invoice"
- "send invoice", "please invoice", "pay you for", "what's the invoice", "billing details"

### How to Check:
1. Read the original file content (email body, LinkedIn message, etc.)
2. Search for invoice keywords above (case-insensitive)
3. Check context: Is a customer asking for billing?

### If Invoice Request Detected:

**STOP! Do NOT continue with any other /process-file logic.**

**Your instructions:**
1. Extract available information from the message:
   - Customer name (from sender email/name)
   - Customer email (from email address)
   - Amount (if mentioned: "$500", "5 hours", "$100/hr", etc.)
   - Description (from message context: project name, service type)

2. **READ the /create-invoice skill:**
   ```
   Read the file: /mnt/d/F drive backup/coding Q4/hackathon-0/ai-employee/.claude/skills/create-invoice/SKILL.md
   ```

3. **FOLLOW all steps in /create-invoice skill exactly:**
   - Ask user for any missing info (customer name, amount, description)
   - Use odoo MCP to create draft invoice
   - Parse JSON response for invoice_id
   - Create approval file in Pending_Approval/ with proper frontmatter
   - Update Dashboard.md

4. **After /create-invoice completes:**
   - Move the original task file to Done/ with completion note
   - Create completion summary mentioning invoice created
   - Display terminal output with invoice details

5. **DONE - Skip all remaining /process-file steps** (no greeting check, no importance check, no auto-reply, nothing)

### If NOT an Invoice Request:

Continue with normal /process-file processing below...

---

## Task Complexity Detection

**SECOND:** After invoice check, decide if the task is SIMPLE or COMPLEX:

### SIMPLE (direct execution -> Done/)
- Single action, no coordination needed
- Informational processing only (extract, summarize, log)
- No external system changes
- Examples: Extract text from PDF, summarize a document, log metadata

### COMPLEX (needs workflow -> Plans/ -> ...)
- Multiple steps required
- External API actions beyond simple reads
- Dependencies or timing constraints
- Affects other systems/people
- Examples: Send email, post to social media, coordinate multi-step process

---

## Workflow For Complex Tasks

For complex tasks, follow this flow:

1. **Needs_Action/** -> Task detected by watcher
2. **Plans/** -> Create Plan.md with step-by-step checklist
3. **Pending_Approval/** -> Create approval request for sensitive actions (financial, new contacts, posting)
4. **Done/** -> Complete task or log summary (do NOT wait - summarize and move on)

---

## Email Handling

**IMPORTANT:** Invoice request detection happens FIRST (see above). If invoice keywords found -> delegates to /create-invoice skill instead.

When processing a file with `type: email` in frontmatter (and NOT an invoice request):

1. **Read full content** from the `Inbox/` reference (inbox_ref field)

2. **Check for GREETING first** (MUST reply - never skip):
   - Greeting keywords: "hi", "hello", "hey", "thanks", "thank you", "appreciate", "happy"
   - Short emails (< 100 words) with only greeting/small talk/thanks
   - **If greeting**:
     - Draft a warm, friendly reply (match the tone)
     - **USE gmail MCP to SEND the reply** (critical step - do not skip!)
     - Move original task to `Done/` with completed template
   - **NOTE:** Even if from yourself (test email) or same person - STILL REPLY! No exceptions.

3. **If NOT a greeting**, think through importance based on:
   - Sender (known vs unknown contact)
   - Subject keywords (urgent, deadline, payment - but NOT "invoice" - those are handled above)
   - Content type (informational vs actionable)
   - Priority level from watcher (high/medium/low)

4. **If NOT important**:
   - Draft a professional, brief reply
   - Use `gmail` MCP to send the reply
   - Move original task to `Done/`

5. **If important**:
   - Summarize the email and key points
   - Log the analysis to `Logs/` folder with timestamp
   - Move the task from `Needs_Action/` to `Pending_Approval/`
   - Add two sections at the end of the task file:
     - `## Claude Reasoning` - Explain WHY you decided human approval is needed
     - `## Human` - Empty section for human to write instructions if desired
   - DO NOT auto-reply - human will handle

---

## LinkedIn Message Handling

**IMPORTANT:** Invoice request detection happens FIRST (see above). If invoice keywords found -> delegates to /create-invoice skill instead.

When processing a file with `type: linkedin` and `activity_type: message` in frontmatter (and NOT an invoice request):

1. **Read full content** from the `Inbox/` reference (inbox_ref field)

2. **Analyze the message** to determine appropriate action based on:
   - Sender (known connection vs new contact)
   - Message content (greeting, business inquiry, job offer, spam, etc.)
   - Context (is this a sales pitch, genuine networking, etc.)

3. **SIMPLE CASES - Auto-reply:**

   **Greeting or small talk:**
   - Message is just "hi", "hello", "hey", "thanks for connecting"
   - No specific question or request
   - **Action:** Draft a warm, brief response
   - **USE linkedin MCP `reply_to_message` to SEND the reply**
   - Move original task to `Done/` with completed template

   **Clear, simple questions:**
   - "When are you available?" -> Check if you have availability, propose time
   - "Can you help with X?" -> If simple and within scope, draft helpful response
   - "What's your rate?" -> Provide standard rate information
   - **Action:** Draft response and send via linkedin MCP
   - Move to `Done/`

4. **COMPLEX CASES - Require human review:**

   Move to `Pending_Approval/` if message contains:
   - **Business proposals** or partnership offers
   - **Job inquiries** or recruitment messages
   - **Sales pitches** requiring thoughtful response
   - **Complex questions** about services/pricing
   - **Unknown senders** with vague messages
   - **Urgent requests** or deadline mentions
   - **Any financial** discussion (except invoice requests - those are delegated to /create-invoice)

   **Process for human review:**
   - Summarize the message and sender context
   - Draft suggested reply for human to edit
   - Move task from `Needs_Action/` to `Pending_Approval/`
   - Add two sections at the end:
     - `## Claude Reasoning` - Explain WHY human review is needed
     - `## Human` - Empty section with your drafted reply for human to edit
   - DO NOT auto-reply - human will handle

5. **SPAM/LOW VALUE - Archive:**
   - Obvious spam, mass outreach, or irrelevant messages
   - No action needed
   - Move directly to `Done/` with note: "Spam/irrelevant, no action taken"
   - Still update Dashboard.md

### LinkedIn Message Reply Templates

**For greetings:**
```
Thanks for connecting! Great to be part of your network. Let me know if there's anything I can help with.
```

**For "how can I help" type messages:**
```
Thanks for reaching out! I'd be happy to help. Could you share a bit more detail about what you're looking for?
```

**For simple availability questions:**
```
Thanks for your message! I'm generally available [mention availability]. What did you have in mind?
```

### Using linkedin MCP for Replies

To reply to LinkedIn messages, use the linkedin MCP's `reply_to_message` tool:

```python
mcp__linkedin__reply_to_message(
  conversation_url="[sender name or full URL]",
  message="[your reply text]",
  wait_before_send=2
)
```

**Note:** The conversation_url can be just the sender's name - the tool will search and find the conversation.

---

## Completed Task Template

When moving a task to `Done/`, wrap the original content with this format:

```markdown
---
type: completed_task
completed: YYYY-MM-DDTHH:MM:SS
completed_by: ai
original_task: TASK_filename
plan: PLAN_filename (if applicable)
time_taken: X minutes (optional)
tags: [category, action-type]
---

# Completed: [Task Title]

[Original task content here]

## Summary
[Brief description of what was accomplished]

## Actions Taken
- [x] Action 1
- [x] Action 2
- [x] Action 3

## Result
[Final outcome]

## Next Steps (if any)
- [ ] Follow-up item 1
- [ ] Follow-up item 2

## Related Files
- Link to plan, invoices, or other references

---
*Processed by AI Employee v0.1 on YYYY-MM-DD HH:MM*
```

**Example for invoice request processed:**
```markdown
---
type: completed_task
completed: 2026-02-22T10:30:00
completed_by: ai
original_task: EMAIL_invoice_request_20260222_103000.md
time_taken: 3 minutes
tags: [invoice_request, auto_processed]
---

# Completed: Invoice Request Auto-Processed

[Original email task content...]

## Summary
Detected invoice request in email and automatically created draft invoice in Odoo by delegating to /create-invoice skill.

## Actions Taken
- [x] Read email from Inbox/
- [x] Detected invoice request keywords
- [x] Extracted: Customer [name], Amount [amount], Description [description]
- [x] Delegated to /create-invoice skill
- [x] Draft invoice ID: [invoice_id] created
- [x] Approval file created in Pending_Approval/

## Result
Draft invoice created. Awaiting human approval to post and email to client.

---
*Processed by AI Employee v0.1 on 2026-02-22 10:30*
```

## Safety Rules

### File Operations
- **Moving files between vault folders** = normal workflow, no approval needed
- **Deleting files for moving purposes** (e.g., Needs_Action to Done) = no approval needed
- **Permanently deleting files** (removing data entirely) = NEVER
- **Deleting files outside vault** = NEVER

### Task-Specific Rules
- Financial documents -> Create approval request in Pending_Approval/
- Unknown file types -> Ask human what to do

### Email-Specific Rules
- **Never auto-reply to:** new/unknown contacts, urgent/deadline matters, financial inquiries (except invoice requests - those delegate to /create-invoice)
- **Keywords requiring approval:** urgent, deadline, payment, asap (but NOT "invoice" - those delegate to /create-invoice)
- **Important emails:** Summarize and log for human - DO NOT wait for approval
- **Always use:** gmail MCP for sending (not direct SMTP)
- **Reference:** `AI_Employee_Vault/Company_Handbook.md` for full communication guidelines

---

## Terminal Output Format

**IMPORTANT:** After completing any task, display a readable summary in the terminal WITHOUT markdown formatting.

The summary should be plain text, easy to read in a terminal:

```
==================================================
TASK COMPLETED
==================================================

Task: [Task name]
Status: [Completed / Moved to Pending_Approval / etc.]
Time Taken: [X minutes]

Summary:
[Brief description of what was done]

Actions Taken:
- Action 1
- Action 2
- Action 3

Result:
[Final outcome]

==================================================
```

**Rules:**
- NO markdown symbols (no **, ##, -, etc. in the terminal output)
- Use plain text formatting
- Keep it concise and readable
- Only show this AFTER the task is complete

---

## FINAL STEP: Update Dashboard.md

After EVERY completed task (moved to Done/), **ALWAYS update Dashboard.md**:

### When to Update Dashboard.md

Update Dashboard.md when:
- Task is completed and moved to `Done/`
- Email is auto-replied successfully
- File is processed and summarized
- Task is moved to `Pending_Approval/` (update Pending Tasks count)
- Invoice request is auto-processed (update Pending Approvals count)

### What to Add to Dashboard.md

**Add to Recent Activity section:**
```markdown
## Recent Activity

- [timestamp] [action description]
- [timestamp] [action description]

[... keep previous activities ...]
```

**Activity formats by task type:**
- Invoice request processed: `[timestamp] Invoice request auto-detected from [source] - Draft created for [customer]: $[amount]`
- Email auto-replied: `[timestamp] Email auto-replied to [sender] - [subject preview]`
- Email -> Pending Approval: `[timestamp] Email marked for review - [sender] - [subject]`
- LinkedIn message -> Pending Approval: `[timestamp] LinkedIn message queued for review - from [sender]`
- File processed: `[timestamp] Processed [filename] - [brief result]`
- Task completed: `[timestamp] Completed: [task description]`

### Update Quick Stats

After each action, update the stats:

| Metric | When to Update |
|--------|----------------|
| Pending Tasks | -1 when completed, +1 when new task created, -1 when moved to Pending_Approval |
| Pending Approvals | +1 when invoice draft created |
| Completed Today | +1 when task moved to Done/ |
| Active Watchers | No change (this doesn't start/stop watchers) |

### Example Dashboard Update After Processing Invoice Request

```markdown
## Quick Stats

| Metric | Value | Last Updated |
|--------|-------|--------------|
| Pending Tasks | 2 | 2026-02-22 10:30 |
| Pending Approvals | 1 (Invoice) | 2026-02-22 10:30 |
| Completed Today | 3 | 2026-02-22 10:30 |
| Active Watchers | 3 (File System, Gmail, LinkedIn) | OK |

---

## Recent Activity

- [2026-02-22 10:30] Invoice request auto-detected from email - Draft created for John Doe: $500
- [2026-02-22 10:15] Email auto-replied to newsletter@company.com - "Thank you for updates"
- [2026-02-22 10:00] LinkedIn message queued for review - from Jane Smith

[... older activities below ...]
```

### How to Update Dashboard.md

1. Read current `Dashboard.md`
2. Parse Quick Stats and Recent Activity
3. Update values based on action taken
4. Add new activity at top of Recent Activity
5. Keep last 10-20 activities (remove older to keep clean)
6. Update "Last updated" timestamp
7. Write back to `Dashboard.md`

### Dashboard.md Structure Reference

```markdown
# AI Employee Dashboard

---

## Quick Stats

| Metric | Value | Last Updated |
|--------|-------|--------------|
| Pending Tasks | [number] | [timestamp] |
| Pending Approvals | [number] | [timestamp] |
| Completed Today | [number] | [timestamp] |
| Active Watchers | [list] | OK |

---

## Recent Activity

- [timestamp] [action]
- [timestamp] [action]
[... last 10-20 ...]

---

## System Status

| Component | Status |
|-----------|--------|
| Obsidian Vault | OK |
| Claude Code | OK |
| File System Watcher | OK |
| Gmail Watcher | OK |
| LinkedIn Watcher | OK |
| MCP Servers | OK |

---

## Quick Links

- [[Company_Handbook]] - Rules and guidelines
- [[Business_Goals]] - Track objectives

---

*Last updated: [timestamp]*
```

### Why Update Dashboard.md?

- Dashboard.md is the **"Nerve Center"** showing real-time activity
- Provides **quick oversight** of what AI has been doing
- Used for **Monday Morning CEO Briefing** (Gold tier feature)
- **Single-writer rule**: Only this skill should update Dashboard.md
