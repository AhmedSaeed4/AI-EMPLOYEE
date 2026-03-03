---
description: Execute approved actions from Approved folder. Handles email replies (gmail MCP), LinkedIn posts (linkedin_api MCP), LinkedIn message replies (linkedin MCP), Meta posts (meta-api MCP - Facebook/Instagram), Twitter posts (twitter-api MCP), and Odoo invoices (odoo MCP). Updates Dashboard.md after each completed action.
---

# Execute Approved Actions

Reads and executes actions from `AI_Employee_Vault/Approved/` folder.

## What This Does

1. Reads all `.md` files from `/Approved/` folder
2. For each file, determines the action type and executes
3. Moves executed files to `/Done/` with completed template
4. Shows terminal summary for each action
5. **Updates Dashboard.md** with activity and stats

## Usage

```
/execute-approved
```

---

## Email Actions (type: email)

When the file has `type: email` in frontmatter:

### Step 1: Read the Human Section
- Look for `## Human` section in the file
- This contains the human's instructions after reviewing

### Step 2: Determine Action

**If Human section says "approve", "send", "ok", or is empty:**
- Draft a reply based on the original email (use `inbox_ref` to read it)
- Use `gmail` MCP to send the reply
- Move to `/Done/`

**If Human section has specific instructions:**
- Follow those instructions exactly
- Use `gmail` MCP to send if instructed to reply
- Move to `/Done/`

**If Human section says "no reply", "ignore", "skip":**
- Log that no action was taken
- Move to `/Done/`

### Step 3: Use gmail MCP
To send email replies, use the `gmail` MCP server.

### Step 4: Completed Template
After execution, wrap the file with the completed task template (see process-file skill).

---

## LinkedIn Post Actions (type: linkedin_post)

When the file has `type: linkedin_post` in frontmatter:

### Step 1: Read the Post Content
- Extract the full post body from the file
- The content is between the frontmatter and the `---` separator before Human Section
- Check for any human edits in the content

### Step 2: Read the Human Section
- Look for the approval checkbox status
- Check for any edits or modifications in Human section
- `queued_copy` field tells you where the clean version is

### Step 3: Determine Action

**If approved (checkbox checked or Human says "approve", "post", "ok"):**
- Use **linkedin_api MCP** to post to LinkedIn (uses official API - more reliable!)
- Move original from `Pending_Approval/` to `/Done/`
- Move copy from `Content_To_Post/queued/` to `Content_To_Post/posted/`
- Add post URN and timestamp to the posted file

**If rejected (Human says "no", "don't", "cancel", "reject"):**
- Move both files to `Rejected/`
- Delete the queued copy
- Log rejection

### Step 4: Use linkedin_api MCP to Post

**Important:** Use the linkedin_api MCP (official API) for posting - more reliable than browser automation!

**API Flow:**
1. Call `linkedin_api` MCP's `post_to_linkedin` tool
2. Pass the post content (text from the approved file)
3. The API handles authentication and posting
4. Get the post URN as confirmation

**Tool call:**
```python
mcp__linkedin_api__post_to_linkedin(
  text="[post content body]",
  title="[optional title/headline]"
)
```

### Step 5: Move and Update Files
After successful post:
1. Move `Pending_Approval/LINKEDIN_POST_*.md` → `Done/`
2. Move `Content_To_Post/queued/LINKEDIN_POST_*.md` → `Content_To_Post/posted/`
3. Add posting metadata to the posted file:
```markdown
## Posted
- **Posted at:** [timestamp]
- **Posted via:** linkedin_api MCP
- **Post URN:** [from API response]
- **Visibility:** PUBLIC
```

### Step 6: Terminal Output
```
==================================================
ACTION EXECUTED
==================================================

Action: LinkedIn Post
Status: Posted successfully

Summary:
Posted lead-generation content to LinkedIn

Actions Taken:
- Read approved post from Pending_Approval/
- Used linkedin_api MCP to post via LinkedIn API
- Moved to Done/ and Content_To_Post/posted/

Result:
Post published to LinkedIn feed

==================================================
```

---

## Meta Post Actions (type: meta_post)

When the file has `type: meta_post` in frontmatter:

### Step 1: Read the Post Content
- Extract the full post body from the file
- The content is between the frontmatter and the `---` separator before Human Section
- Check for any human edits in the content

### Step 2: Read the Human Section
- Look for **Platform Selection** checkboxes:
  - `[ ] Facebook only`
  - `[ ] Instagram only`
  - `[ ] Both Facebook and Instagram`
- Look for **Image URL** (required for Instagram)
- Check `queued_copy` field for clean version location

### Step 3: Determine Action

**If approved (checkbox checked or Human says "approve", "post", "ok"):**
- Parse which platforms are selected
- Read image URL if Instagram is selected
- Use **meta-api MCP** to post
- Move original from `Approved/` to `/Done/`
- Move copy from `Content_To_Post/queued/` to `Content_To_Post/posted/`
- Add post metadata to the posted file

**If rejected:**
- Move both files to `Rejected/`
- Delete the queued copy
- Log rejection

### Step 4: Use meta-api MCP to Post

**Tool calls:**

**For Facebook only:**
```python
mcp__meta-api__post_to_facebook(
  text="[post content body]"
)
```

**For Instagram only:**
```python
mcp__meta-api__post_to_instagram(
  caption="[post content body]",
  image_url="[image URL from Human Section]"
)
```

**For both platforms:**
```python
mcp__meta-api__post_to_both(
  text="[post content body - Facebook version]",
  image_url="[image URL from Human Section]",
  instagram_caption="[post content body - Instagram version]"
)
```

**Important:** Instagram **requires** an image URL. If Instagram is selected but no image URL is provided:
- Skip Instagram and post to Facebook only
- OR show error and ask for image URL

### Step 5: Move and Update Files
After successful post:
1. Move `Approved/META_POST_*.md` → `Done/`
2. Move `Content_To_Post/queued/META_POST_*.md` → `Content_To_Post/posted/`
3. Add posting metadata to the posted file:
```markdown
## Posted
- **Posted at:** [timestamp]
- **Posted via:** meta-api MCP
- **Platforms:** [Facebook/Instagram/Both]
- **Post IDs:** [from API response]
```

### Terminal Output
```
==================================================
ACTION EXECUTED
==================================================

Action: Meta Post (Facebook + Instagram)
Status: Posted successfully

Summary:
Posted lead-generation content to [platforms]

Actions Taken:
- Read approved post from Approved/
- Parsed platform selection: [Facebook/Instagram/Both]
- Used meta-api MCP to post
- Moved to Done/ and Content_To_Post/posted/

Result:
Post published to [Facebook/Instagram/Both]

==================================================
```

---

## LinkedIn Message Reply Actions (type: linkedin_message)

When the file has `type: linkedin_message` in frontmatter (created by LinkedIn Watcher):

### Step 1: Read the Message Details
- Extract sender name, message preview, conversation details
- Check `inbox_ref` for full message in `Inbox/` folder
- Note: conversation_url may be included or needs to be found

### Step 2: Read the Human Section
- Look for the reply content or instructions
- Human may have written a specific reply
- Or given instructions on what to say

### Step 3: Determine Action

**If Human provided a reply or said "approve", "send", "ok":**
- Use **linkedin MCP** `reply_to_message` tool (this works!)
- Send the reply to the conversation
- Move original from `Pending_Approval/` to `/Done/`
- Log the reply

**If Human says "no reply", "ignore", "skip":**
- Log that no action was taken
- Move to `/Done/`

### Step 4: Use linkedin MCP to Reply

**This tool works!** Use the linkedin MCP's `reply_to_message` tool:

```python
mcp__linkedin__reply_to_message(
  conversation_url="[conversation URL or sender name]",
  message="[reply content from Human Section]",
  wait_before_send=2
)
```

**Parameters:**
- `conversation_url`: Can be full LinkedIn messaging URL OR just sender name (tool will search)
- `message`: The reply text from Human Section
- `wait_before_send`: Seconds to wait before sending (default: 2)

### Step 5: Move to Done
After successful reply:
1. Move `Pending_Approval/LINKEDIN_MESSAGE_*.md` → `Done/`
2. Add reply metadata:
```markdown
## Replied
- **Replied at:** [timestamp]
- **Replied via:** linkedin MCP
- **To:** [sender name]
```

### Terminal Output
```
==================================================
ACTION EXECUTED
==================================================

Action: LinkedIn Message Reply
Status: Sent successfully

Summary:
Replied to LinkedIn message from [sender name]

Actions Taken:
- Read message from Inbox/ reference
- Used linkedin MCP reply_to_message tool
- Moved to Done/

Result:
Reply sent to LinkedIn conversation

==================================================
```

---

## Odoo Invoice Actions (type: odoo_invoice)

When the file has `type: odoo_invoice` in frontmatter:

### Step 1: Read the Invoice Details
- Extract `invoice_id`, `invoice_name`, `amount`, `customer` from frontmatter
- Review the invoice details that were created
- **IMPORTANT:** Use `invoice_id` for posting (draft invoices don't have names yet)

### Step 2: Use odoo MCP to Post Invoice

**Important:** The invoice was already created as a draft. This action posts it.

**Tool call (use invoice_id):**
```python
mcp__odoo__post_invoice(
  invoice_id=[invoice_id from frontmatter]
)
```

**Note:** The `post_invoice` tool now accepts both `invoice_id` (for drafts) and `invoice_name` (for already-posted invoices). Always prefer `invoice_id` when available.

### Step 3: Move to Done
After successful posting:
1. Move file from `Approved/` to `Done/`
2. Add posted metadata:
```markdown
## Posted
- **Posted at:** [timestamp]
- **Posted via:** odoo MCP
- **Invoice ID:** [invoice_id]
- **Final Invoice Name:** [name from response, e.g., INV/2026/00002]
- **Amount:** $[amount]
- **Customer:** [customer]
```

### Terminal Output
```
==================================================
ACTION EXECUTED
==================================================

Action: Odoo Invoice Posted
Status: Posted successfully

Summary:
Posted invoice to Odoo accounting system

Actions Taken:
- Read invoice details from frontmatter
- Used odoo MCP post_invoice tool with invoice_id
- Moved to Done/

Result:
Invoice [final_name] is now posted and confirmed

==================================================
```

---

## Non-Email Actions

For other action types (payment, other social posts, etc.):

1. Read the action details from frontmatter
2. Log the action
3. For now: Move to `/Done/` with note "Action logged, manual execution required"
4. Future: Add MCP servers for payments, other platforms

---

## Terminal Output

After each action, display a plain-text summary:

```
==================================================
ACTION EXECUTED
==================================================

Action: Email Reply
Status: Sent
To: recipient@example.com

Summary:
Replied to approved email

Actions Taken:
- Read Human section instructions
- Drafted reply based on approval
- Sent via gmail MCP
- Moved to Done/

Result:
Email sent successfully

==================================================
```

---

## Example Email Flow

1. **Original email** arrives → watcher creates task in `Needs_Action/`
2. **AI processes** → moves to `Pending_Approval/` with Claude Reasoning + Human sections
3. **Human reviews** → fills Human section (e.g., "approve", "send reply saying X")
4. **Human moves** to `Approved/`
5. **Orchestrator detects** → calls `/execute-approved`
6. **This skill executes** → reads Human section → sends reply → moves to `Done/`

---

## Example LinkedIn Message Reply Flow

1. **LinkedIn Watcher** detects unread message → creates task in `Needs_Action/`
2. **AI processes** via `/process-file` → drafts reply suggestion → moves to `Pending_Approval/`
3. **Human reviews** → edits reply or approves as-is
4. **Human moves** to `Approved/`
5. **Orchestrator detects** → calls `/execute-approved`
6. **This skill executes** → uses linkedin MCP `reply_to_message` → moves to `Done/`

---

## Example LinkedIn Post Flow

1. **User calls** `/linkedin-posting` → generates lead-gen post idea
2. **Two files created**:
   - `Content_To_Post/queued/LINKEDIN_POST_[timestamp].md` (clean copy)
   - `Pending_Approval/LINKEDIN_POST_[timestamp].md` (with Human Section)
3. **Human reviews** in `Pending_Approval/` → edits if needed, checks "Approve" box
4. **Human moves** to `Approved/`
5. **Orchestrator detects** → calls `/execute-approved`
6. **This skill executes** → uses linkedin_api MCP to post → moves both files appropriately

---

## Example Meta Post Flow

1. **User calls** `/meta-posting` → generates lead-gen post idea
2. **Two files created**:
   - `Content_To_Post/queued/META_POST_[timestamp].md` (clean copy)
   - `Pending_Approval/META_POST_[timestamp].md` (with Human Section)
3. **Human reviews** in `Pending_Approval/` →:
   - Selects platforms (Facebook / Instagram / Both)
   - Adds Instagram image URL
   - Edits content if needed
4. **Human moves** to `Approved/`
5. **Orchestrator detects** → calls `/execute-approved`
6. **This skill executes** →:
   - Reads platform selection
   - Uses meta-api MCP to post
   - Moves both files appropriately

---

## Twitter Post Actions (type: twitter_post)

When the file has `type: twitter_post` in frontmatter:

### Step 1: Read the Post Content
- Extract the tweet from the file
- The content is between the frontmatter and the `---` separator before Human Section
- Check for any human edits in the content

### Step 2: Read the Human Section
- Look for approval checkbox status
- Check for any edits or modifications in Human section
- `queued_copy` field tells you where the clean version is

### Step 3: Determine Action

**If approved (checkbox checked or Human says "approve", "post", "ok"):**
- Use **twitter-api MCP** to post
- Move original from `Approved/` to `/Done/`
- Move copy from `Content_To_Post/queued/` to `Content_To_Post/posted/`
- Add post metadata to the posted file

**If rejected:**
- Move both files to `Rejected/`
- Delete the queued copy
- Log rejection

### Step 4: Use twitter-api MCP to Post

**Tool call:**
```python
mcp__twitter-api__post_tweet(
  text="[tweet content - max 280 characters]"
)
```

**Alternative:** For formatted business updates:
```python
mcp__twitter-api__post_business_update(
  update_type="[invoice_sent|project_complete|new_service|milestone|general]",
  details="[specific details]",
  hashtags="[optional hashtags]"
)
```

### Step 5: Move and Update Files
After successful post:
1. Move `Approved/TWITTER_POST_*.md` → `Done/`
2. Move `Content_To_Post/queued/TWITTER_POST_*.md` → `Content_To_Post/posted/`
3. Add posting metadata to the posted file:
```markdown
## Posted
- **Posted at:** [timestamp]
- **Posted via:** twitter-api MCP
- **Tweet ID:** [from API response]
- **Visibility:** Public
```

### Terminal Output
```
==================================================
ACTION EXECUTED
==================================================

Action: Twitter Post
Status: Posted successfully

Summary:
Posted engagement content to Twitter (X)

Actions Taken:
- Read approved post from Approved/
- Used twitter-api MCP to post
- Moved to Done/ and Content_To_Post/posted/

Result:
Tweet published successfully

==================================================
```

---

## Safety Rules

- **Always read** the Human section before acting
- **Never send** if Human says "no", "don't", "cancel", "reject"
- **Always log** actions to `/Logs/` folder
- **Always use** completed template when moving to `/Done/`

---

## Error Handling (Graceful Degradation)

When an MCP tool call fails (returns error instead of success):

### Step 1: Detect Failure
Check if the MCP response contains error indicators like:
- `"Error:"` at the start of response
- `"failed"` in response
- HTTP status codes (401, 403, 429, 500, 503, etc.)
- Exception messages

### Step 2: Create Failed_Queue File
Instead of moving to `Done/`, create a file in `Failed_Queue/`:

```markdown
---
timestamp: [current timestamp]
action_type: [linkedin_post|meta_post|twitter_post|email|odoo_invoice]
original_file: [name of approved file]
error_message: [the error from MCP]
---

# Failed Action: [action type]

## Original File
[original file name from Approved/]

## Error
[full error message from MCP]

## Context
[copy relevant frontmatter and content from original file]
```

### Step 3: Move to Failed_Queue
- Move the failed file from `Approved/` to `Failed_Queue/` (rename to include FAILED prefix)
- **NO automatic retry** - file stays in Failed_Queue/

### Step 4: Human Review
**Human should periodically check `Failed_Queue/` folder and decide:**
- If retry needed → Move to `Needs_Action/` (it will be re-processed)
- If resolved manually → Move to `Done/`
- If should be ignored → Delete

### Step 5: Terminal Output for Failure
```
==================================================
ACTION FAILED
==================================================

Action: [action type]
Status: Failed

Error:
[error message]

Actions Taken:
- Attempted to execute approved action
- MCP call returned error
- Created file in Failed_Queue/

Result:
File moved to Failed_Queue/ for manual review

==================================================
```

### Error Classification

| Error Type | Action |
|------------|--------|
| **Transient** (timeout, 429, 503, 504) | Queue - human can retry later |
| **Auth** (401, 403, forbidden) | Queue - human needs to fix credentials |
| **Data** (invalid input, missing fields) | Queue - human needs to fix data |
| **Payment** (banking, invoice) | Queue - requires fresh approval |

---

## FINAL STEP: Update Dashboard.md

After EVERY successfully executed action (email, LinkedIn post, LinkedIn message, Meta post), **ALWAYS update Dashboard.md**:

### What to Add to Dashboard.md

Add the completed action to the **Recent Activity** section:

```markdown
## Recent Activity

- [timestamp] Email sent to [recipient] - [subject preview]
- [timestamp] LinkedIn post published - [topic preview]
- [timestamp] LinkedIn message replied to [sender]
- [timestamp] Meta post published - [topic preview] - [Facebook/Instagram/Both]
- [timestamp] Invoice posted - [invoice_name] for [customer] - $[amount]

[... keep previous activities ...]
```

### Update Quick Stats

After each action, update the **Quick Stats** section:

| Metric | Update Rule |
|--------|-------------|
| Pending Tasks | Decrease by 1 |
| Completed Today | Increase by 1 |
| Active Watchers | Keep current |

### Example Dashboard Update

```markdown
## Quick Stats

| Metric | Value | Last Updated |
|--------|-------|--------------|
| Pending Tasks | 3 | 2026-02-18 14:30 |
| Completed Today | 2 | 2026-02-18 14:30 |
| Active Watchers | 3 (File System, Gmail, LinkedIn) | ✅ |

---

## Recent Activity

- [2026-02-18 14:30] LinkedIn post published: "3 Automation Mistakes Costing You Sales"
- [2026-02-18 14:27] Meta post published: "How I reclaimed 15+ hours each week" - [Facebook + Instagram]
- [2026-02-18 14:25] Replied to LinkedIn message from John Smith
- [2026-02-18 14:20] Email sent to client@example.com - "Re: Project Update"
- [2026-02-18 12:00] File detected via File System Watcher: `document.pdf`

[... older activities below ...]
```

### How to Update Dashboard.md

1. Read the current `Dashboard.md` file
2. Parse existing Quick Stats and Recent Activity
3. Update the values (increment/decrement as appropriate)
4. Add new activity entry at the top of Recent Activity
5. Keep last 10-20 activities (remove older ones to keep it clean)
6. Write back to `Dashboard.md`

### Dashboard.md Template Structure

```markdown
# AI Employee Dashboard

Welcome to your Personal AI Employee dashboard. This is the central hub where Claude Code will report status, updates, and summaries.

---

## Quick Stats

| Metric | Value | Last Updated |
|--------|-------|--------------|
| Pending Tasks | [number] | [timestamp] |
| Completed Today | [number] | [timestamp] |
| Active Watchers | [list] | ✅ |

---

## Recent Activity

- [timestamp] [action description]
- [timestamp] [action description]
[... keep last 10-20 ...]

---

## System Status

| Component | Status |
|-----------|--------|
| Obsidian Vault | ✅ Active |
| Claude Code | ✅ Connected |
| File System Watcher | ✅ Active (Polling Mode) |
| Gmail Watcher | ✅ Active |
| LinkedIn Watcher | ✅ Active |
| MCP Servers | ✅ Gmail, LinkedIn (API + Messaging) configured |

---

## Quick Links

- [[Company_Handbook]] - Rules and guidelines for your AI Employee
- [[Business_Goals]] - Track your objectives and metrics

---

*Last updated: [timestamp]*
```

### Why Update Dashboard.md?

From hackathon requirements:
- Dashboard.md is the **"Nerve Center"** - real-time summary of activity
- Used for **Monday Morning CEO Briefing** (Gold tier)
- Provides **quick oversight** of what AI has been doing
- **Single-writer rule**: Only local updates Dashboard.md (not cloud agents)
