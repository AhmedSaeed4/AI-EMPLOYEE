# AI Employee Documentation

Welcome to the AI Employee documentation. This folder contains comprehensive guides for setting up, configuring, and running the AI Employee system.

---

## Quick Links

| Document | Description |
|----------|-------------|
| [Getting Started](GETTING_STARTED.md) | Installation and initial setup |
| [Project Architecture](PROJECT_ARCHITECTURE.md) | System architecture overview |
| [Agent Skills Reference](AGENT_SKILLS_REFERENCE.md) | All 18 skills documented |
| [Vault Structure Guide](VAULT_STRUCTURE_GUIDE.md) | Vault folder organization |
| [Configuration Reference](CONFIGURATION_REFERENCE.md) | All configuration files |
| [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md) | Common issues and solutions |
| [Security & Credentials](SECURITY_CREDENTIALS_GUIDE.md) | Credential management |

---

## Deployment

| Document | Description |
|----------|-------------|
| [PM2 Setup Guide](PM2_SETUP_GUIDE.md) | 24/7 operation setup |
| [Vault Sync Setup Guide](VAULT_SYNC_SETUP_GUIDE.md) | Git-based vault sync |
| [Cloud Deployment Guide](CLOUD_DEPLOYMENT_GUIDE.md) | Deploy to cloud VM |
| [Cloud Agents Guide](CLOUD_AGENTS_GUIDE.md) | OpenAI Agents SDK agents |

---

## MCP Servers

Detailed documentation for each MCP server:

| Server | Document | Purpose |
|--------|----------|---------|
| Gmail | [mcp/gmail-mcp.md](mcp/gmail-mcp.md) | Email operations |
| LinkedIn API | [mcp/linkedin-api-mcp.md](mcp/linkedin-api-mcp.md) | LinkedIn posting |
| LinkedIn | [mcp/linkedin-mcp.md](mcp/linkedin-mcp.md) | LinkedIn messaging |
| Meta API | [mcp/meta-api-mcp.md](mcp/meta-api-mcp.md) | Facebook/Instagram |
| Twitter API | [mcp/twitter-api-mcp.md](mcp/twitter-api-mcp.md) | Twitter posting |
| Odoo | [mcp/odoo-mcp.md](mcp/odoo-mcp.md) | Accounting |

---

## Watchers

Detailed documentation for each watcher:

| Watcher | Document | Purpose |
|---------|----------|---------|
| Base Watcher | [watchers/base-watcher.md](watchers/base-watcher.md) | Abstract base class |
| File System | [watchers/filesystem-watcher.md](watchers/filesystem-watcher.md) | Monitor Drop_Zone |
| Gmail | [watchers/gmail-watcher.md](watchers/gmail-watcher.md) | Monitor Gmail |
| LinkedIn | [watchers/linkedin-watcher.md](watchers/linkedin-watcher.md) | Monitor LinkedIn |

---

## Documentation Structure

```
documentation/
├── README.md                    # This file
├── GETTING_STARTED.md           # Installation guide
├── PROJECT_ARCHITECTURE.md      # System architecture
├── AGENT_SKILLS_REFERENCE.md    # Skills documentation
├── VAULT_STRUCTURE_GUIDE.md     # Vault organization
├── CONFIGURATION_REFERENCE.md   # Configuration files
├── TROUBLESHOOTING_GUIDE.md     # Troubleshooting
├── SECURITY_CREDENTIALS_GUIDE.md # Security guide
├── PM2_SETUP_GUIDE.md           # PM2 setup
├── VAULT_SYNC_SETUP_GUIDE.md    # Vault sync
├── CLOUD_DEPLOYMENT_GUIDE.md    # Cloud deployment
├── CLOUD_AGENTS_GUIDE.md        # Cloud agents
├── mcp/                         # MCP server docs
│   ├── gmail-mcp.md
│   ├── linkedin-api-mcp.md
│   ├── linkedin-mcp.md
│   ├── meta-api-mcp.md
│   ├── twitter-api-mcp.md
│   └── odoo-mcp.md
└── watchers/                    # Watcher docs
    ├── base-watcher.md
    ├── filesystem-watcher.md
    ├── gmail-watcher.md
    └── linkedin-watcher.md
```

---

## Tier Progress

| Tier | Status | Documentation |
|------|--------|---------------|
| Bronze | ✅ Complete | Vault, Dashboard, Handbook |
| Silver | ✅ Complete | Gmail/LinkedIn watchers, MCP servers |
| Gold | ✅ Complete | Odoo, Meta, Twitter, CEO Briefing |
| Platinum | ⏳ 80% | Cloud deployment, Vault sync |

---

## Contributing

To update documentation:

1. Edit the appropriate `.md` file
2. Follow existing formatting conventions
3. Update the README.md index if adding new files
4. Keep code examples accurate and tested

---

## Related Files

| File | Location | Purpose |
|------|----------|---------|
| CLAUDE.md | Project root | Claude Code instructions |
| PROJECT_STATUS.md | Project root | Project status and progress |
| Company_Handbook.md | Vault | AI behavior rules |
| Business_Goals.md | Vault | Business context |

---

*Generated: 2026-03-14*
*AI Employee Project - Platinum Tier Documentation*