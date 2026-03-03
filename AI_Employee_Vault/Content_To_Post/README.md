# Content_To_Post Folder

This folder holds business content scheduled for posting on LinkedIn.

## Folder Structure

| Folder | Purpose |
|---------|---------|
| `queued/` | Content ready to be posted |
| `posted/` | Successfully posted content (with timestamp) |
| `rejected/` | Content that was not approved for posting |

## Content Format

Each piece of content should be a markdown file with frontmatter:

```markdown
---
type: linkedin_post
status: queued
created: 2026-01-07T10:00:00Z
scheduled: 2026-01-07T09:00:00Z
---

# Your Post Title Here

Your post content goes here. This will be automatically posted to LinkedIn.

#hashtags #business #automation
```

## Workflow

1. Create content file in `queued/`
2. LinkedIn Auto-Poster picks it up
3. Posts to LinkedIn
4. Moves file to `posted/` with timestamp and post ID
5. Logs the action to `Logs/YYYY-MM-DD.json`
