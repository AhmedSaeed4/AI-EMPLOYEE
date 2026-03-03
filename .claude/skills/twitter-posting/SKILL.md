---
description: Generate a Twitter (X) post for business. Creates clean file in Content_To_Post/queued/ and review copy with Human Section in Pending_Approval/.
---

# Twitter Posting Skill

Generate business-focused content for Twitter (X) designed to generate engagement and drive traffic.

## How It Works

1. **Analyzes business context** from your vault
2. **Generates ONE tweet idea**
3. **Creates TWO files**:
   - `Content_To_Post/queued/TWITTER_POST_[timestamp].md` → Clean post content only
   - `Pending_Approval/TWITTER_POST_[timestamp].md` → Post content + Human Section for review

## Usage

```
/twitter-posting
```

## What Each File Contains

### File 1: `Content_To_Post/queued/TWITTER_POST_[timestamp].md` (Clean - No Human Section)

```markdown
---
type: twitter_post
status: queued
created: [timestamp]
post_type: engagement
topic: [generated topic]
target_audience: [who this is for]
---

[Tweet content - max 280 characters]

[Hashtags]
```

### File 2: `Pending_Approval/TWITTER_POST_[timestamp].md` (With Human Section for Review)

```markdown
---
type: twitter_post
status: pending_approval
created: [timestamp]
post_type: engagement
topic: [generated topic]
target_audience: [who this is for]
queued_copy: Content_To_Post/queued/TWITTER_POST_[timestamp].md
---

[Tweet content - max 280 characters]

[Hashtags]

---

## Human Section
**Status:** [ ] Approve for posting  [ ] Request changes  [ ] Reject

**Your Instructions:**
<!-- Write your feedback, edits, or instructions here -->

**Action if Approved:** Move this file to Approved/ folder
**Action if Changes:** Edit content above, then move to Approved/
**Action if Reject:** Move to Rejected/ folder (queued copy will be removed too)
```

## Instructions to Claude

When this skill is invoked:

1. **Read Business_Goals.md** first to understand business context, services, and target audience

2. **Check Content_To_Post/posted/** folder for previous posts - avoid creating the EXACT same post

3. **Generate ONE tweet idea** focused on:
   - Business value propositions
   - Quick tips and insights
   - Engagement questions
   - Industry news commentary
   - Behind-the-scenes updates

4. **Vary the content types** between calls:
   - Quick tips (thread ideas)
   - Questions to audience
   - Industry hot takes
   - Resource sharing
   - Achievement sharing
   - Thought leadership

5. **Twitter-specific formatting:**
   - **Max 280 characters** (Twitter limit)
   - Use 1-3 hashtags maximum
   - Ask questions to drive engagement
   - Use threads for longer content (mark as [Thread 1/X])

6. **Include call-to-action:**
   - "What do you think? 👇"
   - "Retweet if you agree"
   - "Reply with your thoughts"
   - "Link in bio for more"

7. **Add 1-3 hashtags** (Twitter uses fewer than Instagram)

8. **Create TWO files**:
   - `Content_To_Post/queued/` → Clean post content (no Human Section)
   - `Pending_Approval/` → Post content + Human Section for your review

9. **Use filename format**: `TWITTER_POST_[topic_slug]_[timestamp].md`

10. **Inform the user** where the files were created

## File Naming Convention

```
TWITTER_POST_[topic_slug]_[YYYYMMDD_HHMMSS].md

Example: TWITTER_POST_automation_tip_20260224_143000.md
```

## Topic Ideas (Draw from these)

**Primary Source**: Read topics from `Business_Goals.md` "Topics to Post About" section

**Backup ideas** if Business_Goals.md not found:
- Automation tips: Quick wins, tool recommendations
- Business insights: Growth strategies, common mistakes
- Industry trends: What's happening, predictions
- Tips: Single-point value bombs
- Behind the scenes: Work process, project updates
- Quotes: Motivational or business-related
- Questions: Engage the audience

## Hashtags to Use

Twitter uses fewer hashtags than Instagram:
- **Broad**: #business #entrepreneur #growth
- **Niche**: #automation #AI #productivity #tech
- **1-3 hashtags total** (don't overdo it)

## Length Guidelines

| Platform | Character Limit | Recommended |
|----------|-----------------|-------------|
| **Twitter** | 280 characters | 230-270 (leave room for engagement) |

**Important:** Stay under 280 characters!

## Example Output Format

```
✅ Created Twitter post: "Automation tip that saves 2 hours/day"

Files created:
📁 Content_To_Post/queued/TWITTER_POST_automation_tip_20260224_143000.md
📁 Pending_Approval/TWITTER_POST_automation_tip_20260224_143000.md

Review in Pending_Approval/ and move to Approved/ when ready to post.

---
TWEET PREVIEW:
Stop doing these 3 things that kill your productivity 🛑

[rest of content - under 280 chars]
```

## Notes

- The queued file stays in `Content_To_Post/queued/` as backup
- The approval file in `Pending_Approval/` is for YOUR review
- Use the Human Section to write your feedback or edits
- Move to `Approved/` when ready → orchestrator will post via MCP
- Move to `Rejected/` if you don't want to post this
