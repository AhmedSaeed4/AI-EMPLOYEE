"""
Base Watcher - Template for all watchers
All watchers inherit from this class.
"""
import time
import logging
import traceback
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime


class BaseWatcher(ABC):
    """Abstract base class for all watcher scripts."""

    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.failed_queue = self.vault_path / 'Failed_Queue'
        self.logs = self.vault_path / 'Logs'

        # Ensure folders exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.failed_queue.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

        self.check_interval = check_interval
        self.logger = self._setup_logger()
        self.running = False

        # Error tracking
        self.consecutive_errors = 0
        self.max_consecutive_errors = 10

    def _setup_logger(self):
        """Set up logging for this watcher."""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            # Console handler
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            # File handler
            log_file = self.logs / f"{self.__class__.__name__}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    @abstractmethod
    def check_for_updates(self) -> list:
        """Return list of new items to process."""
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Create .md file in Needs_Action folder."""
        pass

    def _create_failed_queue_file(self, item, error: Exception, retry_count: int = 0):
        """
        Create a failed queue file when an action cannot be processed.

        Args:
            item: The item that failed
            error: The exception that occurred
            retry_count: Current retry attempt
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"FAILED_{self.__class__.__name__}_{timestamp}.md"
        failed_file = self.failed_queue / filename

        content = f"""# Failed Action - {self.__class__.__name__}

retry_count: {retry_count}
timestamp: {datetime.now().isoformat()}
watcher: {self.__class__.__name__}

## Error
{type(error).__name__}: {str(error)}

## Item Details
```
{str(item)}
```

## Traceback
```
{traceback.format_exc()}
```

## Notes
This action will be retried automatically. After 3 failed attempts,
it will be moved to the archived folder and a human review alert
will be created.
"""

        try:
            failed_file.write_text(content, encoding='utf-8')
            self.logger.info(f"Created failed queue file: {filename}")
        except Exception as e:
            self.logger.error(f"Failed to create failed queue file: {e}")

    def run(self):
        """Main loop - continuously check for updates."""
        self.running = True
        self.logger.info(f'Starting {self.__class__.__name__}...')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Check interval: {self.check_interval}s')

        try:
            while self.running:
                try:
                    items = self.check_for_updates()
                    if items:
                        self.logger.info(f'Found {len(items)} new item(s)')
                        for item in items:
                            try:
                                filepath = self.create_action_file(item)
                                self.logger.info(f'Created: {filepath.name}')
                                # Reset error counter on success
                                self.consecutive_errors = 0
                            except Exception as e:
                                self.logger.error(f'Error creating action file: {e}')
                                self._create_failed_queue_file(item, e)

                except Exception as e:
                    self.consecutive_errors += 1
                    self.logger.error(f'Error in loop ({self.consecutive_errors}/{self.max_consecutive_errors}): {e}')

                    # If too many consecutive errors, wait longer before retry
                    if self.consecutive_errors >= self.max_consecutive_errors:
                        self.logger.error(f'Too many consecutive errors, waiting 60s before retry')
                        time.sleep(60)

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info('Stopped by user')
            self.running = False
        except Exception as e:
            self.logger.error(f'Fatal error in {self.__class__.__name__}: {e}')
            self.logger.error(traceback.format_exc())
            raise

    def stop(self):
        """Stop the watcher."""
        self.running = False
