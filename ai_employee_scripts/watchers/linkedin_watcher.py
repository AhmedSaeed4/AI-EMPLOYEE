"""
LinkedIn Watcher - Monitors LinkedIn for messages and engagement

Uses Playwright Sync API for better WSL compatibility
"""
import logging
import time
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from base_watcher import BaseWatcher


class LinkedInWatcher(BaseWatcher):
    """Watches LinkedIn for messages and engagement."""

    def __init__(
        self,
        vault_path: str,
        session_path: str = None,
        check_interval: int = 300
    ):
        """
        Initialize LinkedIn Watcher.

        Args:
            vault_path: Path to AI_Employee_Vault
            session_path: Path to store LinkedIn session (for persisting login)
            check_interval: Seconds between checks (default: 300 = 5 min)
        """
        super().__init__(vault_path, check_interval)

        # Set up session path
        scripts_dir = Path(__file__).parent.parent
        if session_path:
            self.session_path = Path(session_path)
        else:
            self.session_path = scripts_dir / "sessions" / "linkedin"
        self.session_path.mkdir(parents=True, exist_ok=True)

        # Track seen items to prevent duplicates
        self.seen_messages: Set[str] = set()
        self.seen_requests: Set[str] = set()
        self._load_state()

        # Set up inbox path (for storing full messages)
        self.inbox = Path(__file__).parent.parent.parent / 'AI_Employee_Vault' / 'Inbox'
        self.inbox.mkdir(parents=True, exist_ok=True)

        # Check if this is first run (no session files exist)
        self.first_run = not any(self.session_path.iterdir())

        self.logger.info(f"Session path: {self.session_path}")
        self.logger.info(f"First run: {self.first_run}")

    def _setup_logger(self) -> logging.Logger:
        """Set up logging for this watcher."""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_state(self) -> None:
        """Load previously seen item IDs."""
        state_file = Path(__file__).parent.parent / 'AI_Employee_Vault' / 'Logs' / 'linkedin_state.json'
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text(encoding='utf-8'))
                self.seen_messages = set(data.get('messages', []))
                self.seen_requests = set(data.get('requests', []))
                self.logger.info(f"Loaded {len(self.seen_messages)} seen messages, {len(self.seen_requests)} seen requests")
            except Exception as e:
                self.logger.warning(f"Could not load state file: {e}")

    def _save_state(self) -> None:
        """Save seen item IDs to state file."""
        state_file = Path(__file__).parent.parent / 'AI_Employee_Vault' / 'Logs' / 'linkedin_state.json'
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state_data = {
            'messages': list(self.seen_messages),
            'requests': list(self.seen_requests),
            'last_updated': datetime.now().isoformat()
        }
        state_file.write_text(json.dumps(state_data, indent=2), encoding='utf-8')

    def _get_item_id(self, item: Dict) -> str:
        """Get unique identifier for a LinkedIn item."""
        return f"{item['type']}_{item['id']}"

    def check_for_updates(self) -> List[Dict]:
        """
        Check for new LinkedIn activities.

        Returns:
            List of new items (messages, connection requests, etc.)
        """
        updates = []

        self.logger.info("Starting LinkedIn check...")

        try:
            # Determine if we should use headless mode
            use_headless = not self.first_run
            self.logger.info(f"Creating browser context (headless={use_headless})...")

            p = sync_playwright().start()

            try:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=use_headless,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )

                page = browser.new_page()

                self.logger.info("Navigating to LinkedIn messaging...")
                page.goto('https://www.linkedin.com/messaging/', timeout=30000)

                # On first run, wait for user to complete login
                if self.first_run:
                    self.logger.info("=" * 50)
                    self.logger.info("FIRST RUN - MANUAL LOGIN REQUIRED")
                    self.logger.info("=" * 50)
                    self.logger.info("1. A browser window has opened")
                    self.logger.info("2. Log in to LinkedIn in that window")
                    self.logger.info("3. Wait for this script to detect login (up to 2 minutes)")
                    self.logger.info("=" * 50)

                    # Wait for successful login - check for messaging page elements
                    max_wait = 120  # 2 minutes
                    start_time = time.time()
                    logged_in = False

                    while time.time() - start_time < max_wait:
                        time.sleep(3)
                        try:
                            # Check if we're on messaging page (logged in)
                            current_url = page.url.lower()
                            has_login = 'login' in current_url
                            has_messaging = 'messaging' in current_url
                            has_checkpoint = 'checkpoint' in current_url or 'challenge' in current_url

                            # Log current state for debugging
                            self.logger.info(f"Checking URL: {current_url[:80]}...")
                            self.logger.info(f"  - has_login={has_login}, has_messaging={has_messaging}, has_checkpoint={has_checkpoint}")

                            if not has_login and has_messaging:
                                self.logger.info("✓ Login detected! Session saved.")
                                logged_in = True
                                break
                            elif has_checkpoint:
                                self.logger.info("Security verification detected, waiting...")
                                time.sleep(5)
                        except Exception as e:
                            self.logger.debug(f"Exception while checking URL: {e}")
                            time.sleep(2)

                    if not logged_in:
                        self.logger.warning("Login timeout - will try again on next run")
                    # Close browser after first-run setup
                    self.logger.info("Closing browser (first run complete)...")
                    browser.close()
                    p.stop()
                    return []

                # Subsequent runs - check for unread messages
                self.logger.info("Checking for unread messages...")

                # Use URL that goes directly to unread filter without auto-opening messages
                page.goto('https://www.linkedin.com/messaging/?filter=unread', timeout=30000)
                time.sleep(2)
                self.logger.info("Waited for initial page load")

                # Close conversation detail panel if it's open (prevents auto-opening first message)
                try:
                    close_button = page.query_selector('.msg-thread__close-icon, .artdeco-button[data-test-conversation-close-icon="true"]')
                    if close_button:
                        close_button.click()
                        self.logger.info("Closed conversation detail panel")
                        time.sleep(1)
                except:
                    self.logger.info("No conversation panel to close (or already closed)")

                # Wait a bit more for messages to stabilize
                time.sleep(2)
                self.logger.info("Waited for messages to render")

                # Wait for conversation list to load
                page.wait_for_selector('.msg-conversations-container__conversations-list', timeout=10000)
                self.logger.info("Conversation list loaded")

                # LinkedIn uses CSS classes for unread, not data attributes
                unread = page.query_selector_all('.msg-conversation-card__convo-item-container--unread')
                self.logger.info(f"Selector found {len(unread)} unread conversation(s)")

                for msg in unread[:10]:  # Check last 10 messages
                    try:
                        # Get participant names (sender)
                        sender_elem = msg.query_selector('.msg-conversation-listitem__participant-names')
                        sender = sender_elem.inner_text().strip() if sender_elem else 'Unknown'

                        # Get message preview text
                        text_elem = msg.query_selector('.msg-conversation-card__message-snippet')
                        text = text_elem.inner_text()[:100] if text_elem else 'No preview'

                        # Debug logging to see what we're extracting
                        self.logger.info(f"Extracted: sender={sender}, text={text[:30] if text else 'empty'}")

                        # Get message ID from data attributes or create hash
                        msg_id = str(hash(text))

                        self.logger.info(f"Message ID: {msg_id}, Is new: {msg_id not in self.seen_messages}")

                        if msg_id not in self.seen_messages:
                            updates.append({
                                'type': 'message',
                                'id': msg_id,
                                'sender': sender,
                                'preview': text,
                                'timestamp': datetime.now().isoformat()
                            })
                            self.seen_messages.add(msg_id)
                    except Exception as e:
                        self.logger.debug(f"Error processing message: {e}")
                        continue

                self.logger.info(f"Found {len(updates)} new unread messages")

                browser.close()
                p.stop()

            except PlaywrightTimeout as e:
                self.logger.error(f"Playwright timeout: {e}")
            except Exception as e:
                self.logger.error(f"LinkedIn check failed: {type(e).__name__}: {e}")
                self.logger.debug(traceback.format_exc())

        except Exception as e:
            self.logger.error(f"Critical error in LinkedIn watcher: {e}")
            self.logger.debug(traceback.format_exc())

        return updates

    def create_action_file(self, item: Dict) -> Path:
        """
        Create action file for a LinkedIn item.
        Creates TWO files:
        1. Inbox/LINKEDIN_[type]_[timestamp].md - Full content for reference
        2. Needs_Action/LINKEDIN_[type]_[timestamp].md - Task with inbox_ref

        Args:
            item: Dictionary with item details

        Returns:
            Path to created action file (Needs_Action)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:22]  # Use microseconds for unique filenames when processing multiple items
        filename = f'LINKEDIN_{item["type"].upper()}_{timestamp}.md'

        # Determine priority
        priority = 'high' if item['type'] == 'message' else 'medium'

        # ========================================
        # 1. Create file in Inbox/ (full content for reference)
        # ========================================
        inbox_content = f"""---
type: linkedin
source: linkedin
activity_type: {item['type']}
from: {item['sender']}
created: {datetime.now().isoformat()}
---

# LinkedIn {item['type'].replace('_', ' ').title()} from {item['sender']}

## Activity Details
- **Type:** {item['type'].replace('_', ' ').title()}
- **From:** {item['sender']}
- **Message ID:** {item['id']}

## Content/Message
{item.get('preview', '')}

---
*This file was automatically generated by LinkedIn Watcher.*
"""

        inbox_filepath = self.inbox / filename
        inbox_filepath.write_text(inbox_content, encoding='utf-8')
        self.logger.info(f"Stored full message in Inbox: {inbox_filepath.name}")

        # ========================================
        # 2. Create task file in Needs_Action/ (with inbox reference)
        # ========================================
        task_content = f"""---
type: linkedin
source: linkedin
activity_type: {item['type']}
from: {item['sender']}
priority: {priority}
status: pending
inbox_ref: {filename}
created: {datetime.now().isoformat()}
---

# LinkedIn {item['type'].replace('_', ' ').title()} from {item['sender']}

## Activity Details
- **Type:** {item['type'].replace('_', ' ').title()}
- **From:** {item['sender']}
- **Priority:** {priority}

## Content/Message
{item.get('preview', '')}

## Suggested Actions
- [ ] Review the {item['type'].replace('_', ' ')}
- [ ] Respond if needed
- [ ] Update CRM or notes

## Quick Response Ideas
"""

        # Add response templates based on type
        if item['type'] == 'connection_request':
            task_content += """- [ ] "Thank you for connecting! I look forward to..."
- [ ] "Great to connect! How did you find..."
"""
        elif item['type'] == 'message':
            task_content += """- [ ] "Thanks for reaching out! I'd be happy to..."
- [ ] "Let me check and get back to you by..."
"""
        elif item['type'] == 'comment':
            task_content += """- [ ] "Thanks for commenting!"
- [ ] "Great point! I appreciate..."
"""

        # Write to Needs_Action
        filepath = self.needs_action / filename
        filepath.write_text(task_content, encoding='utf-8')

        # Save updated seen items
        self._save_state()

        self.logger.info(f"Created action file: {filepath.name}")

        return filepath


def main():
    """Run the LinkedIn Watcher."""
    import sys

    # Default vault path
    vault_path = Path(__file__).parent.parent.parent / 'AI_Employee_Vault'

    # Allow command line override
    if len(sys.argv) > 1:
        vault_path = Path(sys.argv[1])

    if not vault_path.exists():
        print(f"Error: Vault path not found: {vault_path}")
        print("Usage: python linkedin_watcher.py [vault_path]")
        sys.exit(1)

    try:
        watcher = LinkedInWatcher(
            vault_path=str(vault_path),
            check_interval=300  # Check every 5 minutes
        )

        print("LinkedIn Watcher starting... Press Ctrl+C to stop.")
        watcher.run()  # This will run continuously with polling loop
    except Exception as e:
        print(f"\nError: {e}")
        print("\n⚠️  LinkedIn Watcher requires Playwright setup.")
        sys.exit(1)


if __name__ == '__main__':
    main()
