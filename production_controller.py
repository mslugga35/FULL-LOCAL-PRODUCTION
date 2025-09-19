#!/usr/bin/env python3
"""
Production System Controller - Unified management for Telegram to Discord routing pipeline
Manages message processor, Discord forwarder, and system health monitoring
"""

import os
import sys
import time
import json
import signal
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import io
import logging

# Force UTF-8 on Windows - more compatible approach
if sys.platform == "win32":
    import locale
    if locale.getpreferredencoding().upper() != 'UTF-8':
        os.environ['PYTHONIOENCODING'] = 'utf-8'

# Import our configuration manager
from config_manager import ConfigurationManager

class ProductionController:
    """Unified controller for the complete Telegram to Discord routing system"""

    def __init__(self):
        """Initialize the production controller"""
        self.config_manager = ConfigurationManager()
        self.base_dir = Path(__file__).parent

        # Process management
        self.processes = {}
        self.process_configs = {
            'message_processor': {
                'script': 'message_processor_windows.py',
                'name': 'Message Processor',
                'description': 'Routes messages from recent_messages to queue folders',
                'restart_on_failure': True,
                'restart_delay': 30
            },
            'discord_forwarder': {
                'script': 'discord_forwarder_simple.py',
                'name': 'Discord Forwarder',
                'description': 'Sends messages from queue folders to Discord',
                'restart_on_failure': True,
                'restart_delay': 30
            }
        }

        # System state
        self.running = False
        self.start_time = None
        self.last_health_check = None
        self.health_check_interval = 60  # seconds
        self.stats = {
            'total_restarts': 0,
            'process_restarts': {},
            'last_activity': {},
            'uptime_start': None
        }

        # Setup logging
        self.setup_logging()

        # Signal handlers
        self.setup_signal_handlers()

        print("[INIT] Production Controller initialized")

    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = self.base_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Main controller logger
        self.logger = logging.getLogger('ProductionController')
        self.logger.setLevel(logging.INFO)

        # File handler
        log_file = log_dir / f"production_controller_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self.logger.info("Production Controller logging initialized")

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown()
            sys.exit(0)

        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)

    def start_process(self, process_name: str) -> bool:
        """Start a specific process"""
        if process_name not in self.process_configs:
            self.logger.error(f"Unknown process: {process_name}")
            return False

        config = self.process_configs[process_name]
        script_path = self.base_dir / config['script']

        if not script_path.exists():
            self.logger.error(f"Script not found: {script_path}")
            return False

        try:
            # Start the process
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(self.base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )

            self.processes[process_name] = {
                'process': process,
                'config': config,
                'start_time': datetime.now(),
                'restart_count': 0,
                'last_output': None
            }

            self.logger.info(f"[OK] Started {config['name']} (PID: {process.pid})")
            return True

        except Exception as e:
            self.logger.error(f"[ERROR] Failed to start {config['name']}: {e}")
            return False

    def stop_process(self, process_name: str) -> bool:
        """Stop a specific process"""
        if process_name not in self.processes:
            return True

        process_info = self.processes[process_name]
        process = process_info['process']
        config = process_info['config']

        try:
            # Terminate gracefully
            process.terminate()

            # Wait for termination
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if needed
                process.kill()
                process.wait()

            self.logger.info(f"[STOP] Stopped {config['name']}")
            del self.processes[process_name]
            return True

        except Exception as e:
            self.logger.error(f"[ERROR] Error stopping {config['name']}: {e}")
            return False

    def restart_process(self, process_name: str) -> bool:
        """Restart a specific process"""
        self.logger.info(f"[RESTART] Restarting {process_name}...")

        if process_name in self.processes:
            self.processes[process_name]['restart_count'] += 1
            self.stats['process_restarts'][process_name] = \
                self.stats['process_restarts'].get(process_name, 0) + 1

        success = self.stop_process(process_name)
        if success:
            time.sleep(2)  # Brief pause
            success = self.start_process(process_name)

        if success:
            self.stats['total_restarts'] += 1

        return success

    def check_process_health(self, process_name: str) -> Tuple[bool, str]:
        """Check if a process is healthy"""
        if process_name not in self.processes:
            return False, "Process not running"

        process_info = self.processes[process_name]
        process = process_info['process']

        # Check if process is still alive
        if process.poll() is not None:
            return False, f"Process terminated with code {process.returncode}"

        # Check runtime
        runtime = datetime.now() - process_info['start_time']
        if runtime < timedelta(seconds=5):
            return True, "Starting up"

        # Process is running
        return True, f"Running for {runtime}"

    def health_check(self):
        """Perform comprehensive health check"""
        self.last_health_check = datetime.now()
        issues = []
        healthy_processes = 0

        # Check each process
        for process_name in self.process_configs:
            is_healthy, status = self.check_process_health(process_name)

            if is_healthy:
                healthy_processes += 1
                self.stats['last_activity'][process_name] = datetime.now()
            else:
                issues.append(f"{process_name}: {status}")

                # Auto-restart if configured
                config = self.process_configs[process_name]
                if config.get('restart_on_failure', False):
                    self.logger.warning(f"[AUTO-RESTART] Auto-restarting {process_name}: {status}")
                    if self.restart_process(process_name):
                        issues.pop()  # Remove issue if restart successful

        # Check system resources
        try:
            stats = self.config_manager.get_processing_stats()
            recent_count = stats['recent_messages_count']
            total_queued = stats['total_queued']

            # Log processing stats
            if recent_count > 0 or total_queued > 0:
                self.logger.info(f"[STATS] Processing: {recent_count} recent, {total_queued} queued")

        except Exception as e:
            issues.append(f"Config check failed: {e}")

        # Overall health status
        if len(issues) == 0:
            self.logger.info(f"[HEALTHY] System healthy: {healthy_processes}/{len(self.process_configs)} processes running")
        else:
            self.logger.warning(f"[WARNING] System issues detected: {', '.join(issues)}")

        return len(issues) == 0

    def start_all(self):
        """Start all configured processes"""
        self.logger.info("[START] Starting complete production system...")

        # Ensure directories exist
        self.config_manager.ensure_directories()

        # Start each process
        success_count = 0
        for process_name in self.process_configs:
            if self.start_process(process_name):
                success_count += 1
                time.sleep(1)  # Brief delay between starts

        self.running = True
        self.start_time = datetime.now()
        self.stats['uptime_start'] = self.start_time

        self.logger.info(f"[OK] Production system started: {success_count}/{len(self.process_configs)} processes")
        return success_count == len(self.process_configs)

    def stop_all(self):
        """Stop all processes"""
        self.logger.info("[STOP] Stopping all processes...")

        success_count = 0
        for process_name in list(self.processes.keys()):
            if self.stop_process(process_name):
                success_count += 1

        self.running = False
        self.logger.info(f"[OK] All processes stopped: {success_count} processes")
        return success_count

    def run_monitoring_loop(self):
        """Main monitoring and management loop"""
        self.logger.info("[MONITOR] Starting monitoring loop...")

        try:
            while self.running:
                # Perform health check
                self.health_check()

                # Print status periodically
                if datetime.now().minute % 5 == 0:  # Every 5 minutes
                    self.print_status()

                # Sleep until next check
                time.sleep(self.health_check_interval)

        except KeyboardInterrupt:
            self.logger.info("[STOP] Monitoring interrupted by user")
        except Exception as e:
            self.logger.error(f"[ERROR] Error in monitoring loop: {e}")
        finally:
            self.shutdown()

    def print_status(self):
        """Print detailed system status"""
        print("\n" + "=" * 70)
        print("PRODUCTION SYSTEM STATUS")
        print("=" * 70)

        # Uptime
        if self.start_time:
            uptime = datetime.now() - self.start_time
            print(f"Uptime: {uptime}")

        # Process status
        print(f"Processes: {len(self.processes)}/{len(self.process_configs)} running")
        for process_name, process_info in self.processes.items():
            config = process_info['config']
            runtime = datetime.now() - process_info['start_time']
            restart_count = process_info['restart_count']
            print(f"   - {config['name']}: Running {runtime}, Restarts: {restart_count}")

        # Configuration and message stats
        try:
            stats = self.config_manager.get_processing_stats()
            print(f"Messages: {stats['recent_messages_count']} recent, {stats['total_queued']} queued")

            # Show queue details
            if stats['queue_folders']:
                print("Queue Status:")
                for folder, count in stats['queue_folders'].items():
                    if count > 0:
                        print(f"   - {folder}: {count} messages")

        except Exception as e:
            print(f"[WARNING] Stats error: {e}")

        # System stats
        print(f"Total Restarts: {self.stats['total_restarts']}")
        if self.last_health_check:
            check_age = datetime.now() - self.last_health_check
            print(f"Last Health Check: {check_age.total_seconds():.0f}s ago")

        print("=" * 70)

    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("[SHUTDOWN] Initiating system shutdown...")

        self.running = False
        stop_count = self.stop_all()

        # Print final stats
        if self.start_time:
            total_uptime = datetime.now() - self.start_time
            self.logger.info(f"[STATS] Final stats: Uptime {total_uptime}, Total restarts: {self.stats['total_restarts']}")

        self.logger.info("[OK] System shutdown complete")

    def run_status_only(self):
        """Print status and exit (for monitoring scripts)"""
        try:
            self.config_manager.print_system_status()
            self.print_status()
            return 0
        except Exception as e:
            print(f"[ERROR] Status check failed: {e}")
            return 1

def main():
    """Main entry point"""
    controller = ProductionController()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'status':
            return controller.run_status_only()
        elif command == 'start':
            if controller.start_all():
                controller.run_monitoring_loop()
            return 0
        elif command == 'stop':
            controller.stop_all()
            return 0
        elif command == 'restart':
            controller.stop_all()
            time.sleep(2)
            if controller.start_all():
                controller.run_monitoring_loop()
            return 0
        else:
            print(f"Unknown command: {command}")
            print("Usage: python production_controller.py [start|stop|restart|status]")
            return 1
    else:
        # Default: start and monitor
        if controller.start_all():
            controller.run_monitoring_loop()
        return 0

if __name__ == '__main__':
    exit(main())