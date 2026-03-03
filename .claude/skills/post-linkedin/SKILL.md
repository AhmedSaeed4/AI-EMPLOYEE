---
description: Create LinkedIn post content and add to Content_To_Post/queued folder for automatic posting.
---

# Post LinkedIn Skill

This skill creates business content for LinkedIn and adds it to the queued content folder.

## How It Works

1. Asks for the post content/topic
2. Creates a markdown file with proper frontmatter
3. Saves to `AI_Employee_Vault/Content_To_Post/queued/`
4. The LinkedIn Auto-Poster will pick it up and post it

## Usage

```
/post-linkedin
```

## Content Template

```markdown
---
type: linkedin_post
status: queued
created: [timestamp]
scheduled: [optional - when to post]
---

# [Post Title or Hook]

[Post content - 1-3 paragraphs]

#hashtags #business #automation
```

## Instructions to Claude

When this skill is invoked:

1. **Ask the user** for the post topic or content
2. **Generate engaging content** based on the topic
3. **Include relevant hashtags** for the business niche
4. **Create the content file** in `Content_To_Post/queued/`
5. **Use the format** specified above
6. **Inform the user** that the content has been queued

## Best Practices

- **Hook:** Start with an engaging question or statement
- **Value:** Provide useful insights or tips
- **Length:** Keep posts under 1300 characters (LinkedIn limit)
- **Hashtags:** Use 3-5 relevant hashtags
- **Tone:** Professional but conversational
- **Call-to-action:** Include when appropriate

## Example Output

```
Created queued post: LINKEDIN_automation_tips_20260212.md

Content: "3 Ways AI Changed My Business...

#automation #AI #business"
```

## Scheduling (Optional)

If the user wants to schedule for later, add the scheduled time:

```markdown
scheduled: 2026-02-13T09:00:00Z
```

The Auto-Poster will wait until the scheduled time before posting.
