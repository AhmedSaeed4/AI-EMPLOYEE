{
  "permissions": {
    "allow": [
      "Bash(uv add:*)",
      "mcp__browsermcp__browser_click",
      "mcp__browsermcp__browser_type"
    ]
  },
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": [
    "gmail"
  ],
  "mcpServers": {
    "gmail": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "ai_employee_scripts/mcp_servers/gmail_mcp.py"
      ],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "ai_employee_scripts/credentials.json"
      }
    }
  },
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"/mnt/d/F drive backup/coding Q4/hackathon-0/ai-employee/.claude/hooks/ralph_wiggum.py\""
          }
        ]
      }
    ]
  }
}
