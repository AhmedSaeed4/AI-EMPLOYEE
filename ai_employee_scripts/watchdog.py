#!/usr/bin/env python3
"""
AI Employee Watchdog - Process Monitor for Orchestrator

This is a SEPARATE standalone process that monitors the Orchestrator.
If the Orchestrator crashes, the Watchdog restarts it.

IMPORTANT: This file should be run independently, ideally managed by PM2 or systemd.
The Watchdog watches the Orchestrator; the Orchestrator watches its own watchers.

Usage:
    python watchdog.py

Or with PM2:
    pm2 start watchdog.py --interpreter python3 --name ai-employee-watchdog
"""

import os
import sys
import time
import signal
import subprocess
import logging
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
VAULT_PATH = SCRIPT_DIR.parent / "AI_Employee_Vault"
LOGS_DIR = VAULT_PATH / "Logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Check interval (seconds)
CHECK_INTERVAL = 30

# PID file location
PID_DIR = Path("/tmp")
WATCHDOG_PID_FILE = PID_DIR / "ai_employee_watchdog.pid"

# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging():
    """Set up logging for watchdog."""
    logger = logging.getLogger('ai_employee_watchdog')
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - [WATCHDOG] - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    log_file = LOGS_DIR / "watchdog.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - [WATCHDOG] - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logging()

# =============================================================================
# FIND UV EXECUTABLE
# =============================================================================

UV_PATH = shutil.which("uv")
if not UV_PATH:
    logger.error("uv executable not found in PATH!")
    logger.error("Please install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
    sys.exit(1)

logger.info(f"Found uv at: {UV_PATH}")

# =============================================================================
# PROCESSES TO MONITOR
# =============================================================================

# Processes to monitor (Watchdog watches Orchestrator ONLY)
# Orchestrator manages its own watchers
PROCESSES = {
    "orchestrator": {
        "command": [str(UV_PATH), "run", "python", "orchestrator.py"],
        "working_dir": str(SCRIPT_DIR),
        "max_restarts": 5,          # Max restarts per hour
        "restart_window": 3600,     # 1 hour window
        "startup_delay": 5,         # Seconds to wait before checking if process started
        "env": None,                # Optional: dict of environment variables
    }
}

# =============================================================================
# PROCESS MANAGEMENT
# =============================================================================

class MonitoredProcess:
    """Represents a process being monitored by the watchdog."""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.proc: Optional[subprocess.Popen] = None
        self.pid_file = PID_DIR / f"ai_employee_{name}.pid"
        self.restart_times: list[datetime] = []

    def is_running(self) -> bool:
        """Check if the process is currently running."""
        if self.proc is None:
            return False

        # Check if process is still alive
        return self.proc.poll() is None

    def should_restart(self) -> bool:
        """Check if process should be restarted (hasn't exceeded max restarts)."""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.config["restart_window"])

        # Filter restart times to within the window
        self.restart_times = [t for t in self.restart_times if t > window_start]

        restart_count = len(self.restart_times)
        max_restarts = self.config["max_restarts"]

        if restart_count >= max_restarts:
            logger.error(
                f"{self.name}: Exceeded max restarts ({restart_count}/{max_restarts}) "
                f"within {self.config['restart_window']}s window. Giving up."
            )
            return False

        return True

    def start(self) -> bool:
        """Start the monitored process."""
        if self.is_running():
            logger.debug(f"{self.name}: Already running (PID {self.proc.pid})")
            return True

        try:
            logger.info(f"{self.name}: Starting process...")

            # Prepare environment
            env = os.environ.copy()
            if self.config.get("env"):
                env.update(self.config["env"])

            # Start the process
            self.proc = subprocess.Popen(
                self.config["command"],
                cwd=self.config["working_dir"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # Detach from parent process group
            )

            # Write PID file
            self.pid_file.write_text(str(self.proc.pid))

            # Record restart time
            self.restart_times.append(datetime.now())

            logger.info(f"{self.name}: Started successfully (PID {self.proc.pid})")

            # Wait a bit to ensure it started
            time.sleep(self.config.get("startup_delay", 2))

            # Check if it's still running
            if not self.is_running():
                logger.error(f"{self.name}: Process exited immediately after start")
                return_code = self.proc.returncode
                logger.error(f"{self.name}: Exit code: {return_code}")

                # Try to get stderr
                if self.proc.stderr:
                    try:
                        stderr = self.proc.stderr.read().decode()
                        if stderr:
                            logger.error(f"{self.name}: stderr: {stderr[:500]}")
                    except:
                        pass

                return False

            return True

        except Exception as e:
            logger.error(f"{self.name}: Failed to start: {e}")
            return False

    def stop(self) -> bool:
        """Stop the monitored process."""
        if self.proc is None:
            return True

        try:
            logger.info(f"{self.name}: Stopping process...")

            # Try graceful shutdown first
            self.proc.terminate()

            try:
                self.proc.wait(timeout=10)
                logger.info(f"{self.name}: Stopped gracefully")
            except subprocess.TimeoutExpired:
                logger.warning(f"{self.name}: Did not stop gracefully, killing...")
                self.proc.kill()
                self.proc.wait(timeout=5)
                logger.info(f"{self.name}: Killed")

            # Remove PID file
            if self.pid_file.exists():
                self.pid_file.unlink()

            return True

        except Exception as e:
            logger.error(f"{self.name}: Error stopping: {e}")
            return False

    def restart(self) -> bool:
        """Restart the monitored process."""
        logger.info(f"{self.name}: Restarting...")
        self.stop()
        time.sleep(2)
        return self.start()


class Watchdog:
    """Main watchdog class that monitors and restarts processes."""

    def __init__(self):
        self.processes: Dict[str, MonitoredProcess] = {}
        self.running = False
        self.pid_file = WATCHDOG_PID_FILE

        # Initialize monitored processes
        for name, config in PROCESSES.items():
            self.processes[name] = MonitoredProcess(name, config)

    def _write_pid(self):
        """Write watchdog PID to file."""
        self.pid_file.write_text(str(os.getpid()))

    def _remove_pid(self):
        """Remove watchdog PID file."""
        if self.pid_file.exists():
            self.pid_file.unlink()

    def _check_existing_watchdog(self) -> bool:
        """Check if another watchdog is already running."""
        if not self.pid_file.exists():
            return False

        try:
            existing_pid = int(self.pid_file.read_text().strip())
            os.kill(existing_pid, 0)  # Check if process exists
            return True
        except (OSError, ValueError):
            # Process doesn't exist, stale PID file
            self.pid_file.unlink()
            return False

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, shutting down...")
        self.stop()

    def check_and_restart(self):
        """Check all processes and restart if needed."""
        for name, monitored_proc in self.processes.items():
            if not monitored_proc.is_running():
                logger.warning(f"{name}: Process is not running!")

                # Check if we should restart
                if monitored_proc.should_restart():
                    logger.info(f"{name}: Attempting to restart...")
                    if monitored_proc.start():
                        logger.info(f"{name}: Restarted successfully")
                    else:
                        logger.error(f"{name}: Failed to restart")
                else:
                    logger.error(
                        f"{name}: Will not restart (max restarts exceeded). "
                        f"Human intervention required."
                    )

    def start(self):
        """Start the watchdog."""
        # Check for existing watchdog
        if self._check_existing_watchdog():
            logger.error("Watchdog is already running!")
            sys.exit(1)

        # Write our PID
        self._write_pid()

        # Setup signal handlers
        self._setup_signal_handlers()

        logger.info("=" * 60)
        logger.info("AI EMPLOYEE WATCHDOG STARTING")
        logger.info("=" * 60)
        logger.info(f"Watchdog PID: {os.getpid()}")
        logger.info(f"Monitoring {len(self.processes)} process(es)")
        logger.info("")

        # Start all monitored processes
        for name, monitored_proc in self.processes.items():
            logger.info(f"Starting {name}...")
            if monitored_proc.start():
                logger.info(f"{name}: Started successfully")
            else:
                logger.error(f"{name}: Failed to start!")

        logger.info("")
        logger.info("=" * 60)
        logger.info("WATCHDOG NOW RUNNING")
        logger.info("=" * 60)
        logger.info(f"Check interval: {CHECK_INTERVAL}s")
        logger.info("Press Ctrl+C to stop")
        logger.info("")

        # Main monitoring loop
        self.running = True
        try:
            while self.running:
                time.sleep(CHECK_INTERVAL)
                self.check_and_restart()

        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        """Stop the watchdog and all monitored processes."""
        if not self.running:
            return

        logger.info("")
        logger.info("=" * 60)
        logger.info("WATCHDOG SHUTTING DOWN")
        logger.info("=" * 60)

        self.running = False

        # Stop all monitored processes
        logger.info("Stopping all monitored processes...")
        for name, monitored_proc in self.processes.items():
            monitored_proc.stop()

        # Remove PID file
        self._remove_pid()

        logger.info("Watchdog stopped")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point for watchdog."""
    # Check if orchestrator script exists
    orchestrator_path = SCRIPT_DIR / "orchestrator.py"
    if not orchestrator_path.exists():
        logger.error(f"Orchestrator not found at: {orchestrator_path}")
        sys.exit(1)

    # Create and start watchdog
    watchdog = Watchdog()
    watchdog.start()


if __name__ == "__main__":
    main()
