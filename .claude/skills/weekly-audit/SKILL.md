---
description: Generate comprehensive weekly CEO Briefing with financial, operational, and social media insights from Odoo and vault data. Auto-emails the briefing to you via Gmail.
---

# Weekly Audit (CEO Briefing)

Generates a comprehensive weekly business report combining Odoo accounting data, vault activity, and social media performance. **Automatically emails the briefing to you.**

## Usage

```
/weekly-audit
```

Creates a CEO Briefing in `AI_Employee_Vault/Briefings/` and **emails it to you** with:
- **Financial Summary**: Revenue, expenses, profit, payments received
- **Operational Summary**: Outstanding invoices, new partners, active tasks
- **Social Media Summary**: Posts published, content performance
- **System Status**: Watcher status, errors encountered
- **Business Insights**: Proactive suggestions and action items
- **Financial Summary**: Revenue, expenses, profit, payments received
- **Operational Summary**: Outstanding invoices, new partners, active tasks
- **Social Media Summary**: Posts published, content performance
- **System Status**: Watcher status, errors encountered
- **Business Insights**: Proactive suggestions and action items

## Instructions to Claude

1. **Read Business_Goals.md** for context

2. **Fetch data from Odoo**:
   ```python
   mcp__odoo__get_revenue(days=7)

   mcp__odoo__get_expenses(days=7)

   mcp__odoo__get_invoices(limit=20)

   mcp__odoo__get_payments(limit=20, payment_type="inbound")

   mcp__odoo__get_partners(limit=20)
   ```

3. **Read vault data**:
   - Check `Needs_Action/` for pending tasks count
   - Check `Content_To_Post/posted/` for social media posts this week
   - Check `Logs/` for any recent errors
   - Check `Done/` for completed tasks count this week

4. **Generate briefing file**:
   ```markdown
   # CEO Weekly Briefing
   Generated: [timestamp]
   Week: [Week Start] - [Week End]

   ---
   ## Executive Summary
   [2-3 sentence overview of the week - key wins, concerns, overall health]

   ---
   ## Financial Performance

   ### Revenue
   - This Week: $X,XXX
   - Last Week: $X,XXX ([% change])
   - vs Target: $X,XXX (XX%)
   - Trend: [⬆️/⬇️/➡️]

   ### Expenses
   - This Week: $XXX
   - Last Week: $XXX ([% change])
   - vs Budget: $XXX (XX%)

   ### Net Profit
   - This Week: $X,XXX
   - Margin: XX%
   - Profit vs Last Week: [% change]

   ### Cash Flow
   - Payments Received: $X,XXX ([X] payments)
   - Outstanding Invoices: $X,XXX ([X] invoices)

   ---
   ## Business Operations

   ### Outstanding Invoices
   | Invoice | Customer | Amount | Days Overdue | Action |
   |---------|----------|--------|--------------|--------|
   | [List aging invoices] |

   ### Payments Received This Week
   - [List top 3-5 payments with customers]

   ### New Partners/Customers This Week
   - [List any new partners from get_partners]

   ### Active Tasks
   - Pending Tasks: [X] (from Needs_Action/)
   - Completed This Week: [X] (from Done/)
   - Awaiting Approval: [X] (from Pending_Approval/)

   ---
   ## Social Media Performance

   ### Posts Published This Week
   | Platform | Posts | Topics |
   |----------|-------|--------|
   | LinkedIn | [X] | [list topics] |
   | Facebook | [X] | [list topics] |
   | Instagram | [X] | [list topics] |
   | Twitter/X | [X] | [list topics] |

   ### Content Insights
   - Top Performing Topics: [from posted content]
   - Engagement Notes: [any observed patterns]

   ---
   ## System Status

   ### Watchers
   - File System Watcher: [✅ Active / ⚠️ Inactive]
   - Gmail Watcher: [✅ Active / ⚠️ Inactive]
   - LinkedIn Watcher: [✅ Active / ⚠️ Inactive]

   ### Errors This Week
   - [List any errors from Logs/ folder]

   ---
   ## Proactive Insights

   ### What's Working Well
   - [Positive observations from data]

   ### Areas for Improvement
   - [Concerns or opportunities identified]

   ### Recommendations
   - [Specific action items with priorities]

   ---
   ## Upcoming Actions

   - [ ] Follow up on overdue invoices ([X] invoices)
   - [ ] [Specific invoice follow-ups]
   - [ ] [Specific business development actions]
   - [ ] [System maintenance if needed]
   ```

5. **Calculate week-over-week comparisons**:
   - Get current week data (days=7)
   - Get last week data (compare with previous 7 days before current week)
   - Show percentage changes

6. **Save to** `AI_Employee_Vault/Briefings/YYYY-MM-DD_Weekly_Briefing.md`

7. **Update Dashboard.md** with latest briefing link in Quick Links section

8. **Email the briefing via Gmail MCP**:
   ```python
   mcp__gmail__send_email(
       to="[your-email@example.com]",
       subject="CEO Briefing - Week of [Week Start Date]",
       body="[Full briefing content from the generated file]"
   )
   ```

   **Email Configuration**: Set your email in Company_Handbook.md or use the default from your Gmail account.

## Example Output

```markdown
# CEO Weekly Briefing
Generated: 2026-02-24
Week: 2026-02-17 - 2026-02-23

---

## Executive Summary
Strong week with 3 new invoices sent and 2 payments received. Revenue above target by 15%. One payment overdue requiring follow-up. Social media activity consistent with 4 posts published across platforms.

---

## Financial Performance

### Revenue
- This Week: $4,500
- Last Week: $3,750 (⬆️ +20%)
- vs Target: $4,000 (113%)
- Trend: ⬆️ Up 20% from last week

### Expenses
- This Week: $350
- Last Week: $420 (⬇️ -17%)
- vs Budget: $500 (70%)
- Under budget this week

### Net Profit
- This Week: $4,150
- Last Week: $3,330 (⬆️ +25%)
- Margin: 92%

### Cash Flow
- Payments Received: $2,400 (2 payments)
- Outstanding Invoices: $4,700 (5 invoices)

---

## Business Operations

### Outstanding Invoices
| Invoice | Customer | Amount | Days Overdue | Action |
|---------|----------|--------|--------------|--------|
| INV/2026/0003 | Acme Corp | $1,200 | 5 days | Email follow-up |
| INV/2026/0005 | Gamma LLC | $1,500 | 1 day | Monitor |
| INV/2026/0006 | Delta Inc | $2,000 | Due in 7 | Normal |

### Payments Received This Week
- $1,500 from TechStart Inc (INV/2026/0002)
- $900 from CreativeCo (INV/2026/0001)

### New Partners/Customers This Week
- TechStart Inc (Software company - AI Agent project)
- CreativeCo (Marketing agency - Reels package)

### Active Tasks
- Pending Tasks: 3 (from Needs_Action/)
- Completed This Week: 8 (from Done/)
- Awaiting Approval: 1 (from Pending_Approval/)

---

## Social Media Performance

### Posts Published This Week
| Platform | Posts | Topics |
|----------|-------|--------|
| LinkedIn | 2 | AI Automation, Digital FTEs |
| Facebook | 1 | 3D Animation Tips |
| Instagram | 1 | Behind-the-scenes Reel |
| Twitter/X | 1 | Productivity tip |

### Content Insights
- Top Performing Topics: AI Agents, Digital FTEs
- Engagement Notes: LinkedIn content getting 2x engagement on AI topics

---

## System Status

### Watchers
- File System Watcher: ✅ Active
- Gmail Watcher: ✅ Active
- LinkedIn Watcher: ✅ Active

### Errors This Week
- 2026-02-20: Twitter API returned 402 (expected - no credits)
- No critical errors

---

## Proactive Insights

### What's Working Well
- Customer acquisition trending up (2 new partners)
- Software costs well under budget
- Social media consistency maintained
- AI-focused content resonating with audience

### Areas for Improvement
- 1 invoice overdue (>5 days) - implement automated reminders
- Twitter posting blocked by API credits
- Consider upselling existing customers

### Recommendations
1. Follow up with Acme Corp for overdue payment (Priority: High)
2. Add Twitter API credits to enable posting (Priority: Medium)
3. Create email reminder workflow for aging invoices (Priority: Medium)

---

## Upcoming Actions
- [ ] Follow up with Acme Corp for overdue payment ($1,200)
- [ ] Send invoice to Epsilon Corp for completed AI Agent project
- [ ] Add Twitter API credits
- [ ] Create automated invoice reminder system
```

## Data Sources

| Source | Data Retrieved |
|--------|----------------|
| Odoo `get_revenue` | Weekly revenue breakdown |
| Odoo `get_expenses` | Weekly expense breakdown |
| Odoo `get_invoices` | Outstanding invoices list |
| Odoo `get_payments` | Payments received |
| Odoo `get_partners` | Customer/partner list |
| Vault `Needs_Action/` | Pending tasks count |
| Vault `Done/` | Completed tasks count |
| Vault `Content_To_Post/posted/` | Social media posts |
| Vault `Logs/` | System errors |

## Auto-Email Configuration

The briefing is automatically emailed to you after generation.

**Default recipient**: Your Gmail account (configured in `.env`)

**Subject format**: `CEO Briefing - Week of [YYYY-MM-DD]`

**To change recipient**: Add this to `Company_Handbook.md`:
```markdown
## Weekly Briefing Email
**Send to**: your-email@example.com
```

## Scheduled Usage

This skill can be called via cron for Monday morning briefings:
```bash
0 7 * * 1 cd "/home/adev/ai-employee" && claude code -p "/weekly-audit"
```

Recommended: Monday 7:00 AM (start of business week)
- Briefing saved to `Briefings/` folder
- Email delivered to your inbox
- Dashboard updated with link
