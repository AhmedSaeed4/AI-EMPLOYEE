#!/bin/bash
#
# Setup Cron Jobs for AI Employee Watchers
# This script configures automatic startup of watchers on system boot
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project paths
PROJECT_DIR="/mnt/d/F drive backup/coding Q4/hackathon-0/ai-employee/ai_employee_scripts"
VLOG_DIR="/tmp"

# Watcher scripts
WATCHERS=("filesystem_watcher" "gmail_watcher" "linkedin_watcher" "orchestrator")

echo -e "${GREEN}=== AI Employee Cron Setup ===${NC}"
echo ""
echo "This will set up cron jobs to automatically start watchers on system boot."
echo ""

# Get UV path
UV_PATH=$(which uv || echo "$HOME/.local/bin/uv")
echo -e "UV Path: ${YELLOW}${UV_PATH}${NC}"
echo ""

# Create startup script
cat > "${PROJECT_DIR}/start_all_watchers.sh" << 'EOF'
#!/bin/bash
# Auto-start all AI Employee watchers

cd "$(dirname "$0")"

# Check if already running
if pgrep -f "filesystem_watcher.py" > /dev/null; then
    echo "File System Watcher already running"
else
    echo "Starting File System Watcher..."
    uv run python watchers/filesystem_watcher.py > /tmp/filesystem_watcher.log 2>&1 &
fi

if pgrep -f "gmail_watcher.py" > /dev/null; then
    echo "Gmail Watcher already running"
else
    echo "Starting Gmail Watcher..."
    uv run python watchers/gmail_watcher.py > /tmp/gmail_watcher.log 2>&1 &
fi

if pgrep -f "linkedin_watcher.py" > /dev/null; then
    echo "LinkedIn Watcher already running"
else
    echo "Starting LinkedIn Watcher..."
    uv run python watchers/linkedin_watcher.py > /tmp/linkedin_watcher.log 2>&1 &
fi

if pgrep -f "orchestrator.py" > /dev/null; then
    echo "Orchestrator already running"
else
    echo "Starting Orchestrator..."
    uv run python orchestrator.py > /tmp/orchestrator.log 2>&1 &
fi

echo "All watchers started"
EOF

chmod +x "${PROJECT_DIR}/start_all_watchers.sh"

echo -e "${GREEN}✅ Created startup script:${NC} ${PROJECT_DIR}/start_all_watchers.sh"
echo ""

# Show current crontab
echo -e "${YELLOW}Current crontab:${NC}"
crontab -l 2>/dev/null || echo "(no crontab yet)"
echo ""

# Ask if user wants to add cron job
read -p "$(echo -e ${GREEN}Add cron job for auto-start on boot? [y/N]: ${NC})" -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Add to crontab
    (crontab -l 2>/dev/null; echo "@reboot cd ${PROJECT_DIR} && ./start_all_watchers.sh") | crontab -
    echo -e "${GREEN}✅ Cron job added!${NC}"
    echo ""
    echo "Watchers will start automatically on system boot."
    echo ""
    echo "To manually start all watchers now, run:"
    echo -e "${YELLOW}cd ${PROJECT_DIR} && ./start_all_watchers.sh${NC}"
else
    echo -e "${YELLOW}Cron setup skipped.${NC}"
    echo "You can run this script again later or add manually with:"
    echo "  crontab -e"
fi

echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Useful commands:"
echo "  Check status:  /check-watchers"
echo "  Start all:     cd ${PROJECT_DIR} && ./start_all_watchers.sh"
echo "  Stop all:      /stop-watcher all"
echo ""
echo "Log files:"
echo "  File System:  /tmp/filesystem_watcher.log"
echo "  Gmail:        /tmp/gmail_watcher.log"
echo "  LinkedIn:      /tmp/linkedin_watcher.log"
echo "  Orchestrator:  /tmp/orchestrator.log"
