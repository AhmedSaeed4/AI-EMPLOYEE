"""
Cloud Orchestrator - Main Controller

Runs on cloud VM (Oracle Free Tier) to process tasks 24/7.
Monitors Needs_Action/, routes to Triage Agent, writes drafts to Pending_Approval/.

Architecture:
1. Poll Needs_Action/ for new tasks
2. Claim task by moving to In_Progress/cloud/
3. Route to Triage Agent
4. Process with specialist agent
5. Write draft to Updates/
6. Git push changes
7. Repeat
"""

import asyncio
import os
import signal
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
import json

from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import OpenAI Agents SDK
try:
    from agents import Runner, InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
    OPENAI_AGENTS_AVAILABLE = True
except ImportError:
    Runner = None
    InputGuardrailTripwireTriggered = None
    OutputGuardrailTripwireTriggered = None
    OPENAI_AGENTS_AVAILABLE = False

# Local imports - use absolute imports when run directly
try:
    from cloud.config.settings import get_settings, get_run_config
    from cloud.agent_definitions.triage_agent import triage_and_process, get_triage_agent
    from cloud.agent_definitions.models import TaskType, AgentType, EmailDraft, SocialPost, FinanceAction
    from cloud.tools.file_tools import (
        read_task, list_tasks, move_to_progress,
        write_draft, list_updates
    )
    from cloud.tools.git_tools import git_commit_push, create_commit_message
    from cloud.guardrails.input_guardrails import simple_input_check
    from cloud.guardrails.output_guardrails import simple_output_check
    from cloud.utils.logger import get_logger, log_activity
except ImportError:
    # Fallback to relative imports when run as module
    from .config.settings import get_settings, get_run_config
    from .agent_definitions.triage_agent import triage_and_process, get_triage_agent
    from .agent_definitions.models import TaskType, AgentType, EmailDraft, SocialPost, FinanceAction
    from .tools.file_tools import (
        read_task, list_tasks, move_to_progress,
        write_draft, list_updates
    )
    from .tools.git_tools import git_commit_push, create_commit_message
    from .guardrails.input_guardrails import simple_input_check
    from .guardrails.output_guardrails import simple_output_check
    from .utils.logger import get_logger, log_activity


class CloudOrchestrator:
    """
    Main cloud orchestrator that runs 24/7.

    Polls for tasks, processes them with agents, and writes results.
    """

    def __init__(self):
        """Initialize the cloud orchestrator."""
        self.settings = get_settings()
        self.logger = get_logger(
            log_dir=self.settings.vault_path / "Logs",
            log_level=self.settings.log_level
        )
        self.running = False
        self.tasks_processed = 0
        self.tasks_failed = 0
        self.start_time = None

        # Cloud watcher management
        self.watcher_procs: Dict[str, subprocess.Popen] = {}
        self.scripts_dir = Path(__file__).parent.parent

    def start(self):
        """Start the orchestrator main loop."""
        self.running = True
        self.start_time = datetime.now()

        self.logger.info("=" * 60)
        self.logger.info("Cloud Orchestrator Starting")
        self.logger.info(f"Vault Path: {self.settings.vault_path}")
        self.logger.info(f"Polling Interval: {self.settings.polling_interval}s")
        self.logger.info(f"OpenAI Agents SDK: {'Available' if OPENAI_AGENTS_AVAILABLE else 'NOT AVAILABLE'}")
        self.logger.info("=" * 60)

        # Check for SDK availability
        if not OPENAI_AGENTS_AVAILABLE:
            self.logger.warning("OpenAI Agents SDK not installed. Running in degraded mode.")
            self.logger.warning("Install with: uv add openai-agents")

        # Start cloud watchers
        self._start_cloud_watchers()
        time.sleep(2)  # Let watchers initialize

        # Run the main loop
        try:
            asyncio.run(self._main_loop())
        finally:
            self._stop_cloud_watchers()

    def stop(self, signum=None, frame=None):
        """Stop the orchestrator gracefully."""
        self.logger.info("Stopping Cloud Orchestrator...")
        self.running = False

        if self.start_time:
            uptime = datetime.now() - self.start_time
            self.logger.info(f"Uptime: {uptime}")

        self.logger.info(f"Tasks Processed: {self.tasks_processed}")
        self.logger.info(f"Tasks Failed: {self.tasks_failed}")
        self.logger.info("Cloud Orchestrator Stopped")

        if signum is not None:
            sys.exit(0)

    # ==========================================================================
    # Cloud Watcher Management
    # ==========================================================================

    def _start_cloud_watchers(self) -> int:
        """Start cloud watchers as subprocesses."""
        self.logger.info("Starting cloud watchers...")

        watchers_to_start = [
            ('Cloud Gmail', self.scripts_dir / 'cloud_watchers' / 'gmail_watcher.py'),
            ('Cloud LinkedIn', self.scripts_dir / 'cloud_watchers' / 'linkedin_watcher.py'),
        ]

        # Pass environment variables (including DEDUP_API_URL) to watchers
        watcher_env = os.environ.copy()

        # Use UV's Python (same as orchestrator)
        venv_python = self.scripts_dir / '.venv' / 'bin' / 'python'
        python_cmd = str(venv_python) if venv_python.exists() else 'python3'

        started = 0
        for name, script_path in watchers_to_start:
            if not script_path.exists():
                self.logger.warning(f"Watcher script not found: {script_path}")
                continue

            try:
                proc = subprocess.Popen(
                    [python_cmd, str(script_path), str(self.settings.vault_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(self.scripts_dir),
                    env=watcher_env  # Pass env vars (DEDUP_API_URL, etc.)
                )

                self.watcher_procs[name] = proc
                self.logger.info(f"Started {name} watcher (PID: {proc.pid})")
                started += 1
                time.sleep(1)  # Stagger starts
            except Exception as e:
                self.logger.error(f"Failed to start {name} watcher: {e}")

        self.logger.info(f"Started {started}/{len(watchers_to_start)} cloud watchers")
        return started

    def _check_watcher_health(self):
        """Check if all cloud watchers are still running. Restart if needed."""
        for name, proc in list(self.watcher_procs.items()):
            if proc.poll() is not None:
                exit_code = proc.returncode
                self.logger.warning(f"{name} watcher exited (code: {exit_code})")
                del self.watcher_procs[name]

                self.logger.info(f"Attempting to restart {name}...")
                time.sleep(2)

                watchers = {
                    'Cloud Gmail': self.scripts_dir / 'cloud_watchers' / 'gmail_watcher.py',
                    'Cloud LinkedIn': self.scripts_dir / 'cloud_watchers' / 'linkedin_watcher.py',
                }

                if name in watchers:
                    script_path = watchers[name]
                    if script_path.exists():
                        try:
                            new_proc = subprocess.Popen(
                                ['python3', str(script_path), str(self.settings.vault_path)],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd=str(self.scripts_dir)
                            )
                            self.watcher_procs[name] = new_proc
                            self.logger.info(f"Restarted {name} watcher (PID: {new_proc.pid})")
                        except Exception as e:
                            self.logger.error(f"Failed to restart {name}: {e}")

    def _stop_cloud_watchers(self):
        """Stop all cloud watchers."""
        self.logger.info("Stopping cloud watchers...")
        for name, proc in list(self.watcher_procs.items()):
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                    self.logger.info(f"Stopped {name} watcher")
                except subprocess.TimeoutExpired:
                    proc.kill()
                    self.logger.info(f"Force-killed {name} watcher")
            except Exception as e:
                self.logger.error(f"Error stopping {name} watcher: {e}")

        self.watcher_procs.clear()

    async def _main_loop(self):
        """Main processing loop."""
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        last_health_check = time.time()
        health_check_interval = 60  # Check watcher health every 60 seconds

        while self.running:
            try:
                # Process tasks
                await self._process_cycle()

                # Periodic health check for watchers
                if time.time() - last_health_check >= health_check_interval:
                    self._check_watcher_health()
                    last_health_check = time.time()

                await asyncio.sleep(self.settings.polling_interval)

            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(self.settings.polling_interval)

    async def _process_cycle(self):
        """Process one cycle of task handling."""
        # List available tasks
        tasks = list_tasks()

        if not tasks:
            return  # No tasks to process

        self.logger.info(f"Found {len(tasks)} task(s) to process")

        for task_info in tasks:
            if not self.running:
                break

            await self._process_task(task_info["filename"])

    async def _process_task(self, filename: str):
        """
        Process a single task file.

        Args:
            filename: Task filename to process
        """
        self.logger.info(f"Processing task: {filename}")

        try:
            # Step 1: Read task
            task_result = read_task(filename)
            if task_result.get("error"):
                self.logger.error(f"Error reading task: {task_result['error']}")
                self.tasks_failed += 1
                return

            task_content = task_result["content"]

            # Step 2: Move to In_Progress (claim the task)
            move_result = move_to_progress(filename, "cloud")
            if not move_result.get("success"):
                self.logger.error(f"Error claiming task: {move_result.get('error')}")
                self.tasks_failed += 1
                return

            self.logger.info(f"Task claimed: {filename}")

            # Step 3: Triage and process with specialist via handoff (with automatic guardrail checking)
            try:
                specialist_response = await triage_and_process(task_content)
            except InputGuardrailTripwireTriggered as e:
                self.logger.warning(f"Task blocked by input guardrail: {e}")
                log_activity(
                    "task_blocked",
                    f"Task {filename} blocked by input guardrail",
                    "failed",
                    {"guardrail_error": str(e)}
                )
                self.tasks_failed += 1
                return

            # Check if response requires human input (fallback from simple_route)
            if hasattr(specialist_response, 'requires_human_input') and specialist_response.requires_human_input:
                self.logger.info(f"Task requires human input: {specialist_response.questions_for_human}")
                await self._write_human_clarification(filename, task_content, specialist_response)
                self.tasks_processed += 1
                return

            self.logger.info(f"Specialist response received: {type(specialist_response).__name__}")

            # Step 4: Format specialist response for output
            draft_result = self._format_specialist_response(specialist_response, filename)

            # Step 5: Write draft to Updates/
            if draft_result:
                write_result = write_draft(
                    content=draft_result["content"],
                    original_task=filename,
                    draft_type=draft_result["type"],
                    original_content=task_content
                )

                if write_result.get("success"):
                    self.logger.info(f"Draft written: {write_result['filename']}")

                    # Step 6: Git push changes
                    await self._sync_to_git(
                        f"Processed task: {filename}",
                        f"Pending: {write_result['filename']}"
                    )

                    self.tasks_processed += 1
                else:
                    self.logger.error(f"Error writing draft: {write_result.get('error')}")
                    self.tasks_failed += 1

        except InputGuardrailTripwireTriggered as e:
            # Handle input guardrail triggered at any point
            self.logger.warning(f"Task blocked by input guardrail: {e}")
            log_activity(
                "task_blocked",
                f"Task {filename} blocked by input guardrail",
                "failed",
                {"guardrail_error": str(e)}
            )
            self.tasks_failed += 1

        except OutputGuardrailTripwireTriggered as e:
            # Handle output guardrail triggered
            self.logger.warning(f"Task blocked by output guardrail: {e}")
            log_activity(
                "task_blocked",
                f"Task {filename} blocked by output guardrail",
                "failed",
                {"guardrail_error": str(e)}
            )
            self.tasks_failed += 1

        except Exception as e:
            self.logger.error(f"Error processing task {filename}: {e}")
            self.tasks_failed += 1

    def _format_specialist_response(self, specialist_response, filename: str) -> Optional[dict]:
        """
        Format the specialist's response for writing to Updates/.

        Args:
            specialist_response: The response from specialist (EmailDraft, SocialPost, FinanceAction, or TriageDecision)
            filename: Task filename

        Returns:
            Dictionary with formatted content and type
        """
        try:
            # Handle EmailDraft response
            if isinstance(specialist_response, EmailDraft):
                return {
                    "content": f"""Subject: {specialist_response.subject}

To: {specialist_response.to}

{specialist_response.body}

---
Confidence: {specialist_response.confidence}
Suggested Changes: {', '.join(specialist_response.suggested_changes) if specialist_response.suggested_changes else 'None'}
Missing Info: {', '.join(specialist_response.missing_info) if specialist_response.missing_info else 'None'}
""",
                    "type": "email"
                }

            # Handle SocialPost response
            elif isinstance(specialist_response, SocialPost):
                hashtags_str = " ".join(specialist_response.hashtags) if specialist_response.hashtags else ""
                platform_display = specialist_response.platform.value if hasattr(specialist_response.platform, 'value') else str(specialist_response.platform)
                return {
                    "content": f"""Platform: {platform_display.title()}
Type: {specialist_response.post_type}

Content:
{specialist_response.content}

Hashtags: {hashtags_str}

Character Count: {specialist_response.character_count}
Confidence: {specialist_response.confidence}
""",
                    "type": "social"
                }

            # Handle FinanceAction response
            elif isinstance(specialist_response, FinanceAction):
                return {
                    "content": f"""Action: {specialist_response.action_type}
Description: {specialist_response.description}
Amount: {specialist_response.amount} {specialist_response.currency if specialist_response.amount else 'N/A'}
Risk Level: {specialist_response.risk_level}

Reasoning: {specialist_response.reasoning}

Warnings: {', '.join(specialist_response.warnings) if specialist_response.warnings else 'None'}

Suggested Data: {json.dumps(specialist_response.suggested_data, indent=2)}

Confidence: {specialist_response.confidence}
REQUIRES HUMAN APPROVAL: {specialist_response.needs_approval}
""",
                    "type": "finance"
                }

            # Handle TriageDecision (fallback when handoff didn't happen)
            elif hasattr(specialist_response, 'target_agent'):
                # This is a TriageDecision, not a specialist response
                return {
                    "content": f"""Task routed but not fully processed.

Target Agent: {specialist_response.target_agent}
Reasoning: {specialist_response.reasoning}
Confidence: {specialist_response.confidence}

Note: Handoff may not have completed. This task may need manual processing.
""",
                    "type": "general"
                }

            # Handle text response from specialist (via handoff) - just use it as-is
            elif isinstance(specialist_response, str):
                return {
                    "content": specialist_response,
                    "type": "general"
                }

            # Handle unknown response type
            else:
                return {
                    "content": f"""Received response from specialist but could not determine type.

Response Type: {type(specialist_response).__name__}

Original response:
{str(specialist_response)[:1000]}
""",
                    "type": "general"
                }

        except Exception as e:
            self.logger.error(f"Error formatting specialist response: {e}")
            return {
                "content": f"Error formatting response: {str(e)}",
                "type": "error"
            }

    async def _write_human_clarification(self, filename: str, task_content: str, routing):
        """Write a request for human clarification."""
        content = f"""# Human Clarification Needed

**Task:** {filename}

**Questions:**
{chr(10).join(f"- {q}" for q in routing.questions_for_human)}

**Original Task:**
{task_content}

**Routing Analysis:**
- Type: {routing.task_type}
- Confidence: {routing.confidence}
- Reasoning: {routing.reasoning}

Please provide clarification so the AI can process this task appropriately.
"""

        write_result = write_draft(
            content=content,
            original_task=filename,
            draft_type="clarification_needed",
            prefix="CLARIFICATION"
        )

        if write_result.get("success"):
            self.logger.info(f"Clarification request written: {write_result['filename']}")

    async def _sync_to_git(self, action: str, details: str):
        """Sync changes to git repository."""
        if not self.settings.git_auto_sync:
            return

        try:
            message = create_commit_message(action, details)
            result = git_commit_push(
                repo_path=str(self.settings.vault_path),
                message=message
            )

            if result.get("success"):
                self.logger.info("Changes synced to git")
            else:
                self.logger.warning(f"Git sync failed: {result.get('stderr', 'Unknown error')}")

        except Exception as e:
            self.logger.error(f"Error during git sync: {e}")

    def _parse_task_content(self, content: str) -> dict:
        """Parse task content for structured information."""
        parsed = {}

        # Try to extract key information
        lines = content.split('\n')

        for line in lines:
            line_lower = line.lower()

            if 'from:' in line_lower or 'sender:' in line_lower:
                parsed['sender'] = line.split(':', 1)[1].strip() if ':' in line else "Unknown"
            elif 'subject:' in line_lower:
                parsed['subject'] = line.split(':', 1)[1].strip() if ':' in line else ""
            elif 'body:' in line_lower:
                idx = lines.index(line)
                parsed['body'] = '\n'.join(lines[idx+1:]).strip()

        # Store full content as body if not found
        if 'body' not in parsed:
            parsed['body'] = content

        return parsed

    def _detect_platform(self, content: str) -> str:
        """Detect social platform from task content. Returns string."""
        content_lower = content.lower()

        if 'linkedin' in content_lower:
            return "linkedin"
        elif 'twitter' in content_lower or 'x.com' in content_lower:
            return "twitter"
        elif 'instagram' in content_lower:
            return "instagram"
        elif 'facebook' in content_lower:
            return "facebook"
        else:
            return "linkedin"  # Default


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """Entry point for running the cloud orchestrator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Cloud Orchestrator for AI Employee Platinum Tier"
    )
    parser.add_argument(
        "--vault-path",
        type=str,
        help="Path to the vault (default: from VAULT_PATH env var)"
    )
    parser.add_argument(
        "--polling-interval",
        type=int,
        help="Polling interval in seconds (default: from POLLING_INTERVAL env var)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: from LOG_LEVEL env var)"
    )
    parser.add_argument(
        "--test-run",
        action="store_true",
        help="Run once and exit (for testing)"
    )

    args = parser.parse_args()

    # Override settings from command line
    if args.vault_path:
        import os
        os.environ["VAULT_PATH"] = args.vault_path
    if args.polling_interval:
        import os
        os.environ["POLLING_INTERVAL"] = str(args.polling_interval)
    if args.log_level:
        import os
        os.environ["LOG_LEVEL"] = args.log_level

    # Create and start orchestrator
    orchestrator = CloudOrchestrator()

    if args.test_run:
        # Test run: process once and exit
        asyncio.run(orchestrator._process_cycle())
        print(f"\nTest run complete. Processed: {orchestrator.tasks_processed}, Failed: {orchestrator.tasks_failed}")
    else:
        # Normal run: start continuous loop
        orchestrator.start()


if __name__ == "__main__":
    main()
