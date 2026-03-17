"""
Shared Deduplication Client

Used by both Local and Cloud watchers to check/register processed emails.
Provides real-time coordination via the Cloud API, with fallback to JSON if API is down.

Usage:
    from shared.dedup_client import DedupClient

    client = DedupClient(api_url="https://your-cloud-vm:5000")

    # Check before processing
    if client.is_processed(email_id):
        skip_email()

    # Register after processing
    client.register(email_id, source="local")
"""

import requests
from typing import Optional, Dict, Any
import logging


class DedupClient:
    """Client for the deduplication API on Cloud VM."""

    def __init__(
        self,
        api_url: str,
        api_key: Optional[str] = None,
        timeout: int = 5,
        enabled: bool = True
    ):
        """
        Initialize the dedup client.

        Args:
            api_url: URL of the Cloud API (e.g., "https://your-vm:5000")
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            enabled: If False, all checks return False (for testing/offline)
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.enabled = enabled
        self.logger = logging.getLogger('DedupClient')

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API request."""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        return headers

    def register(self, email_id: str, source: str = "unknown") -> bool:
        """
        Register a processed email ID with the Cloud API.

        Args:
            email_id: The email message ID to register
            source: Who processed it ("local" or "cloud")

        Returns:
            True if registered successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            response = requests.post(
                f"{self.api_url}/register",
                json={"email_id": email_id, "source": source},
                headers=self._get_headers(),
                timeout=self.timeout
            )

            if response.status_code == 200:
                self.logger.debug(f"Registered {email_id} with API (source: {source})")
                return True
            else:
                self.logger.warning(f"API register failed: {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            self.logger.warning(f"API timeout while registering {email_id}")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.warning(f"API connection error while registering {email_id}")
            return False
        except Exception as e:
            self.logger.error(f"API error while registering {email_id}: {e}")
            return False

    def is_processed(self, email_id: str) -> bool:
        """
        Check if an email ID has been processed.

        Args:
            email_id: The email message ID to check

        Returns:
            True if already processed, False otherwise (including API errors)
        """
        if not self.enabled:
            return False

        try:
            response = requests.get(
                f"{self.api_url}/check",
                params={"id": email_id},
                headers=self._get_headers(),
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                processed = data.get("processed", False)
                if processed:
                    source = data.get("source", "unknown")
                    self.logger.info(f"Email {email_id} already processed by {source} (via API)")
                return processed
            else:
                self.logger.warning(f"API check failed: {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            self.logger.warning(f"API timeout while checking {email_id}")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.warning(f"API connection error while checking {email_id}")
            return False
        except Exception as e:
            self.logger.error(f"API error while checking {email_id}: {e}")
            return False

    def health_check(self) -> bool:
        """
        Check if the API is healthy.

        Returns:
            True if API is responding, False otherwise
        """
        if not self.enabled:
            return False

        try:
            response = requests.get(
                f"{self.api_url}/health",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return response.status_code == 200
        except:
            return False

    def batch_register(self, email_ids: list, source: str = "unknown") -> Dict[str, bool]:
        """
        Register multiple email IDs at once.

        Args:
            email_ids: List of email message IDs to register
            source: Who processed them ("local" or "cloud")

        Returns:
            Dict mapping email_id to success (True/False)
        """
        results = {}
        for email_id in email_ids:
            results[email_id] = self.register(email_id, source)
        return results