#!/usr/bin/env python3
"""
LinkedIn Setup Script - First-time login for MCP server

Run this once to login and save session for LinkedIn MCP server.
"""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

# Session path (same as MCP server)
SCRIPT_DIR = Path(__file__).parent
SESSION_PATH = SCRIPT_DIR / 'sessions' / 'linkedin_mcp'
SESSION_PATH.mkdir(parents=True, exist_ok=True)

def main():
    print("=" * 60)
    print("LINKEDIN MCP - FIRST TIME SETUP")
    print("=" * 60)
    print(f"Session path: {SESSION_PATH}")
    print()
    print("1. A browser window will open")
    print("2. Log in to LinkedIn")
    print("3. Wait for 'Login Successful' message")
    print("4. Close the browser window to finish")
    print("=" * 60)
    print()

    input("Press Enter to open browser...")

    p = sync_playwright().start()
    browser = p.chromium.launch_persistent_context(
        user_data_dir=str(SESSION_PATH),
        headless=False,  # Visible browser for login
        args=['--no-sandbox', '--disable-setuid-sandbox'],
        viewport={'width': 1280, 'height': 720}
    )

    page = browser.new_page()
    print("Navigating to LinkedIn...")
    page.goto('https://www.linkedin.com/feed/', timeout=30000)

    # Wait for login
    print("Waiting for you to login...")
    max_wait = 300  # 5 minutes
    start_time = time.time()

    while time.time() - start_time < max_wait:
        time.sleep(3)
        try:
            current_url = page.url.lower()
            has_login = 'login' in current_url
            has_feed = 'feed' in current_url
            has_checkpoint = 'checkpoint' in current_url or 'challenge' in current_url

            if not has_login and has_feed:
                print()
                print("=" * 60)
                print("LOGIN SUCCESSFUL!")
                print("=" * 60)
                print("Session saved. You can now use LinkedIn MCP.")
                print()
                input("Press Enter to close browser and finish...")
                break
            elif has_checkpoint:
                print("Security verification detected, please complete it...")
        except Exception as e:
            print(f"Checking... ({e})")
            time.sleep(2)

    browser.close()
    p.stop()

    print("Setup complete!")

if __name__ == "__main__":
    main()
