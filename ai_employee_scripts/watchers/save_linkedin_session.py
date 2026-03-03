"""
LinkedIn Session Saver - One-time setup to save LinkedIn login session

Run this script on Windows (not WSL) to:
1. Open LinkedIn in a visible browser
2. Let you log in manually
3. Save session cookies for headless watcher use

Usage:
    python save_linkedin_session.py
"""
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright


class LinkedInSessionSaver:
    """Saves LinkedIn login session for headless watcher use."""

    def __init__(self, vault_path: str, session_path: str = None):
        """
        Initialize session saver.

        Args:
            vault_path: Path to AI_Employee_Vault
            session_path: Path to save session (default: .linkedin_session)
        """
        self.vault_path = Path(vault_path)
        if session_path is None:
            session_path = Path(__file__).parent.parent / '.linkedin_session'
        else:
            session_path = Path(session_path)

        self.session_path = session_path
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Set up logging for this script."""
        logger = logging.getLogger('LinkedInSessionSaver')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def save_session(self) -> bool:
        """
        Open browser, navigate to LinkedIn, and save session after login.

        Returns:
            True if session saved successfully, False otherwise
        """
        try:
            with sync_playwright() as p:
                # Launch browser with visible window (for manual login)
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=False,  # Visible window needed for login
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                    ]
                )

                page = browser.new_page()

                self.logger.info('Navigating to LinkedIn...')
                page.goto('https://www.linkedin.com/feed/', timeout=60000)

                # Check if already logged in
                if 'login' not in page.url.lower():
                    self.logger.info('Already logged in! Session saved.')
                    browser.close()
                    return True

                self.logger.info('=' * 60)
                self.logger.info('LINKEDIN LOGIN REQUIRED')
                self.logger.info('=' * 60)
                self.logger.info('1. Log in to LinkedIn in the browser window')
                self.logger.info('2. Once logged in, come back here and press Enter')
                self.logger.info('=' * 60)

                # Wait for user to complete login
                input('\nPress Enter after you have logged in to LinkedIn...')

                # Wait a moment for any redirects to complete
                page.wait_for_timeout(2000)

                # Session is automatically saved by persistent context
                self.logger.info('Session saved to: %s', self.session_path)
                self.logger.info('You can now close the browser if still open.')
                result = True

                browser.close()
                return result

        except Exception as e:
            self.logger.error(f'Error saving session: {e}')
            return False


def main():
    """Run session saver."""
    # Determine vault path
    vault_path = Path(__file__).parent.parent.parent / 'AI_Employee_Vault'

    saver = LinkedInSessionSaver(
        vault_path=str(vault_path)
    )

    print("LinkedIn Session Saver")
    print("=" * 40)
    print("This will open a browser window for you to log in to LinkedIn.")
    print("Your session will be saved for the LinkedIn Watcher to use.")
    print()

    success = saver.save_session()

    if success:
        print()
        print("SUCCESS! Session saved.")
        print("You can now run the LinkedIn Watcher in headless mode.")
    else:
        print()
        print("FAILED! Please check the error messages above and try again.")


if __name__ == '__main__':
    main()
