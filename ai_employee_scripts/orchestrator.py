#!/usr/bin/env python3
"""
AI Employee Orchestrator - Master Controller for Personal AI Employee

This is the 24/7 master process that:
1. Starts and manages all watcher scripts as subprocesses
2. Monitors folders for new tasks and approvals
3. Triggers Claude Code with appropriate skills
4. Handles graceful shutdown and process management
"""
import os
import subprocess
import time
import signal
import sys
import threading
import json
from pathlib import Path
from datetime import datetime


class Orchestrator:
    """Master controller for AI Employee system."""

    def __init__(self, vault_path: str, scripts_dir: str = None):
        """Initialize Orchestrator."""
        self.vault_path = Path(vault_path).resolve()

        if scripts_dir is None:
            self.scripts_dir = Path(__file__).parent.resolve()
        else:
            self.scripts_dir = Path(scripts_dir).resolve()

        # Folders to monitor
        self.needs_action = self.vault_path / 'Needs_Action'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.logs = self.vault_path / 'Logs'

        # Ensure folders exist
        for folder in [self.needs_action, self.approved, self.rejected, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)

        # Process management
        self.watcher_procs = {}
        self.running = False

        # State tracking
        self.seen_files = set()
        self._load_state()

        # PID file
        self.pid_file = Path(__file__).parent / 'orchestrator.pid'

    def _load_state(self):
        """Load previously seen files to avoid reprocessing."""
        state_file = self.logs / 'orchestrator_state.json'
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text(encoding='utf-8'))
                self.seen_files = set(data.get('seen_files', []))
                print(f"[Orchestrator] Loaded {len(self.seen_files)} known files")
            except Exception as e:
                print(f"[Orchestrator] Warning: Could not load state: {e}")
                self.seen_files = set()
        else:
            self._scan_existing_files()

    def _save_state(self):
        """Save seen files to state file."""
        state_file = self.logs / 'orchestrator_state.json'
        state_data = {
            'seen_files': list(self.seen_files),
            'last_updated': datetime.now().isoformat()
        }
        state_file.write_text(json.dumps(state_data, indent=2), encoding='utf-8')

    def _scan_existing_files(self):
        """Scan folders on startup to avoid reprocessing existing files."""
        # Only scan Needs_Action - Approved files should ALWAYS trigger
        for folder in [self.needs_action]:
            for item in folder.glob('*.md'):
                if item.is_file():
                    self.seen_files.add(str(item.resolve()))
        print(f"[Orchestrator] Scanned {len(self.seen_files)} existing files")

    def _log(self, message: str, level: str = "INFO"):
        """Log message to console and log file."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] [{level}] {message}"
        print(log_msg)

        # Write to daily log file
        log_file = self.logs / f"{datetime.now().strftime('%Y-%m-%d')}_orchestrator.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')

    def _call_claude_skill(self, skill_name: str) -> bool:
        """Trigger Claude Code to execute a skill."""
        self._log(f"Calling Claude Code: /{skill_name}", "TRIGGER")

        cmd = ['claude', 'code', '-p', '--dangerously-skip-permissions']

        try:
            result = subprocess.run(
                cmd,
                input=f"/{skill_name}\n",
                text=True,
                capture_output=True,
                timeout=1800,  # 30 minutes for batch processing
                cwd=str(self.vault_path)
            )

            if result.stdout:
                stdout_preview = result.stdout[:500]
                if len(result.stdout) > 500:
                    stdout_preview += "... (truncated)"
                self._log(f"Claude output: {stdout_preview}", "DEBUG")

            if result.returncode != 0:
                stderr_preview = result.stderr[:200] if result.stderr else "No error output"
                self._log(f"Claude error: {stderr_preview}", "ERROR")
                return False

            self._log(f"Claude completed: /{skill_name}", "SUCCESS")
            return True

        except subprocess.TimeoutExpired:
            self._log(f"Claude timed out after 30 minutes", "WARNING")
            return False
        except FileNotFoundError:
            self._log("Claude Code CLI not found!", "ERROR")
            self._log("Hint: npm install -g @anthropic/claude-code", "HINT")
            return False
        except Exception as e:
            self._log(f"Error calling Claude: {e}", "ERROR")
            return False

    def _start_watcher(self, name: str, script_path: Path) -> bool:
        """Start a single watcher script as subprocess."""
        if not script_path.exists():
            self._log(f"Watcher script not found: {script_path}", "ERROR")
            return False

        try:
            proc = subprocess.Popen(
                ['python3', str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.scripts_dir)
            )

            self.watcher_procs[name] = proc
            self._log(f"Started {name} (PID: {proc.pid})", "STARTUP")
            return True

        except Exception as e:
            self._log(f"Failed to start {name}: {e}", "ERROR")
            return False

    def start_watchers(self) -> int:
        """Start all watcher scripts as subprocesses."""
        self._log("=" * 60, "INFO")
        self._log("STARTING AI EMPLOYEE ORCHESTRATOR", "INFO")
        self._log("=" * 60, "INFO")
        self._log(f"Vault: {self.vault_path}", "INFO")
        self._log(f"Scripts: {self.scripts_dir}", "INFO")

        watchers_to_start = [
            ('File System', self.scripts_dir / 'watchers' / 'filesystem_watcher.py'),
            ('Gmail', self.scripts_dir / 'watchers' / 'gmail_watcher.py'),
            ('LinkedIn', self.scripts_dir / 'watchers' / 'linkedin_watcher.py'),
        ]

        started = 0
        for name, script_path in watchers_to_start:
            if self._start_watcher(name, script_path):
                started += 1
            time.sleep(1)

        self._log("-" * 60, "INFO")
        self._log(f"Started {started}/{len(watchers_to_start)} watchers", "INFO")
        return started

    def _check_watcher_health(self):
        """Check if all watchers are still running. Restart if needed."""
        for name, proc in list(self.watcher_procs.items()):
            if proc.poll() is not None:
                exit_code = proc.returncode
                self._log(f"{name} watcher exited (code: {exit_code})", "WARNING")
                del self.watcher_procs[name]

                self._log(f"Attempting to restart {name}...", "INFO")
                time.sleep(2)

                watchers = {
                    'File System': self.scripts_dir / 'watchers' / 'filesystem_watcher.py',
                    'Gmail': self.scripts_dir / 'watchers' / 'gmail_watcher.py',
                    'LinkedIn': self.scripts_dir / 'watchers' / 'linkedin_watcher.py',
                }

                if name in watchers:
                    self._start_watcher(name, watchers[name])

    def _monitor_needs_action(self):
        """Monitor Needs_Action folder for new tasks."""
        self._log("Monitoring Needs_Action/ for new tasks...", "INFO")

        while self.running:
            try:
                new_tasks = []
                for item in self.needs_action.glob('*.md'):
                    item_path = str(item.resolve())
                    if item_path not in self.seen_files:
                        new_tasks.append(item)
                        self.seen_files.add(item_path)

                if new_tasks:
                    self._log(f"Detected {len(new_tasks)} new task(s)", "TRIGGER")
                    for task in new_tasks:
                        self._log(f"  - {task.name}", "DEBUG")

                    self._call_claude_skill('process-file')
                    self._save_state()

                time.sleep(30)

            except Exception as e:
                self._log(f"Error in Needs_Action monitor: {e}", "ERROR")
                time.sleep(30)

    def _monitor_approved(self):
        """Monitor Approved folder and trigger execute-approved skill."""
        self._log("Monitoring Approved/ for executed actions...", "INFO")

        while self.running:
            try:
                new_approvals = []
                for item in self.approved.glob('*.md'):
                    item_path = str(item.resolve())
                    if item_path not in self.seen_files:
                        new_approvals.append(item)
                        self.seen_files.add(item_path)

                if new_approvals:
                    self._log(f"Detected {len(new_approvals)} approved action(s)", "TRIGGER")
                    for approval in new_approvals:
                        self._log(f"  - {approval.name}", "DEBUG")

                    self._call_claude_skill('execute-approved')
                    self._save_state()

                time.sleep(60)

            except Exception as e:
                self._log(f"Error in Approved monitor: {e}", "ERROR")
                time.sleep(60)

    def _monitor_rejected(self):
        """Monitor Rejected folder and log rejected actions."""
        self._log("Monitoring Rejected/ for rejected actions...", "INFO")

        while self.running:
            try:
                new_rejections = []
                for item in self.rejected.glob('*.md'):
                    item_path = str(item.resolve())
                    if item_path not in self.seen_files:
                        new_rejections.append(item)
                        self.seen_files.add(item_path)

                if new_rejections:
                    self._log(f"{len(new_rejections)} action(s) rejected by human", "NOTICE")
                    for rejection in new_rejections:
                        self._log(f"  - {rejection.name}", "DEBUG")

                    rejection_log = self.logs / 'rejected_actions.log'
                    with open(rejection_log, 'a', encoding='utf-8') as f:
                        timestamp = datetime.now().isoformat()
                        for rejection in new_rejections:
                            f.write(f"{timestamp} - REJECTED: {rejection.name}\n")

                    self._save_state()

                time.sleep(60)

            except Exception as e:
                self._log(f"Error in Rejected monitor: {e}", "ERROR")
                time.sleep(60)

    def _setup_signal_handlers(self):
        """Setup graceful shutdown on SIGINT/SIGTERM."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        sig_name = signal.Signals(signum).name
        self._log(f"Received {sig_name}, shutting down...", "NOTICE")
        self.stop()

    def start(self):
        """Start orchestrator and all components."""
        # Check for existing instance
        if self.pid_file.exists():
            try:
                existing_pid = int(self.pid_file.read_text().strip())
                os.kill(existing_pid, 0)
                print(f"[Orchestrator] ERROR: Already running (PID: {existing_pid})")
                print("[Orchestrator] Kill existing process or remove PID file:")
                print(f"[Orchestrator]   rm {self.pid_file}")
                sys.exit(1)
            except OSError:
                pass
            except (ValueError, FileNotFoundError):
                pass

        # Write our PID
        self.pid_file.write_text(str(os.getpid()))

        # Setup signal handlers
        self._setup_signal_handlers()

        # Start watchers
        started = self.start_watchers()
        if started == 0:
            self._log("No watchers started! Exiting.", "ERROR")
            sys.exit(1)

        # Give watchers time to initialize
        self._log("Waiting for watchers to initialize...", "INFO")
        time.sleep(3)

        # Start monitoring threads
        self.running = True

        needs_action_thread = threading.Thread(
            target=self._monitor_needs_action,
            daemon=True,
            name="Monitor-NeedsAction"
        )

        approved_thread = threading.Thread(
            target=self._monitor_approved,
            daemon=True,
            name="Monitor-Approved"
        )

        rejected_thread = threading.Thread(
            target=self._monitor_rejected,
            daemon=True,
            name="Monitor-Rejected"
        )

        needs_action_thread.start()
        approved_thread.start()
        rejected_thread.start()

        self._log("=" * 60, "INFO")
        self._log("ORCHESTRATOR NOW RUNNING", "INFO")
        self._log("=" * 60, "INFO")
        self._log("Press Ctrl+C to stop all watchers and exit", "INFO")
        print()

        # Main loop
        try:
            health_check_interval = 60
            last_health_check = time.time()

            while self.running:
                time.sleep(10)

                if time.time() - last_health_check >= health_check_interval:
                    self._check_watcher_health()
                    last_health_check = time.time()
                    self._save_state()

        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        """Stop all watchers and cleanup."""
        if not self.running:
            return

        self._log("Shutting down orchestrator...", "NOTICE")
        self.running = False

        # Stop all watcher processes
        self._log("Stopping watchers...", "INFO")
        for name, proc in self.watcher_procs.items():
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                    self._log(f"Stopped {name}", "INFO")
                except subprocess.TimeoutExpired:
                    proc.kill()
                    self._log(f"Force-killed {name}", "INFO")
            except Exception as e:
                self._log(f"Error stopping {name}: {e}", "ERROR")

        self.watcher_procs.clear()

        # Remove PID file
        if self.pid_file.exists():
            self.pid_file.unlink()

        # Save final state
        self._save_state()

        self._log("=" * 60, "INFO")
        self._log("ORCHESTRATOR STOPPED", "INFO")
        self._log("=" * 60, "INFO")


def main():
    """Entry point for orchestrator."""
    # Default vault path
    scripts_dir = Path(__file__).parent.resolve()
    default_vault = scripts_dir.parent / 'AI_Employee_Vault'

    vault_path = default_vault
    if len(sys.argv) > 1:
        vault_path = Path(sys.argv[1])

    if not vault_path.exists():
        print(f"[Orchestrator] ERROR: Vault path not found: {vault_path}")
        print("[Orchestrator] Usage: python orchestrator.py [vault_path]")
        sys.exit(1)

    # Create and start orchestrator
    orchestrator = Orchestrator(str(vault_path), str(scripts_dir))
    orchestrator.start()


if __name__ == '__main__':
    main()
