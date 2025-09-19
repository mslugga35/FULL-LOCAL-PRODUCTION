#!/usr/bin/env python3
"""
Comprehensive System Controller for Telegram to Discord Pipeline
Manages the complete message routing system using the updated routing_config.json structure.

Features:
- Configuration validation and folder structure setup
- Unified process management for Telegram collector and Discord forwarder
- Health monitoring and automatic restarts
- Comprehensive logging and status reporting
- Production-ready startup/shutdown procedures
"""

import asyncio
import json
import logging
import os
import sys
import time
import subprocess
import signal
import psutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import threading
import queue
import traceback

# Force UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class SystemController:
    def __init__(self, config_path: str = "routing_config.json"):
        self.config_path = config_path
        self.config = {}
        self.processes = {}
        self.running = False
        self.shutdown_event = threading.Event()
        self.status_queue = queue.Queue()

        # Setup logging
        self.setup_logging()

        # Load and validate configuration
        self.load_configuration()
        self.validate_configuration()

        # Setup folder structure
        self.setup_folder_structure()

        # Process monitoring
        self.process_monitor_thread = None
        self.health_check_thread = None

        # Status tracking
        self.last_health_check = {}
        self.restart_counts = {}

        self.logger.info("System Controller initialized successfully")

    def setup_logging(self):
        """Setup comprehensive logging system"""
        # Create logs directory
        os.makedirs("logs", exist_ok=True)

        # Configure main logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/system_controller.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Create component-specific loggers
        self.telegram_logger = logging.getLogger('telegram_collector')
        self.discord_logger = logging.getLogger('discord_forwarder')
        self.monitor_logger = logging.getLogger('process_monitor')

    def load_configuration(self):
        """Load routing configuration from JSON file"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

            self.logger.info(f"Configuration loaded from {self.config_path}")
            self.logger.info(f"Config version: {self.config.get('version', 'unknown')}")

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise

    def validate_configuration(self):
        """Validate the loaded configuration"""
        required_keys = ['windows_base_path', 'telegram_channels', 'discord_forwarder_integration', 'queue_management']

        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required configuration key: {key}")

        # Validate base path
        base_path = Path(self.config['windows_base_path'])
        if not base_path.is_absolute():
            raise ValueError(f"Base path must be absolute: {self.config['windows_base_path']}")

        # Validate telegram channels
        if not self.config['telegram_channels']:
            raise ValueError("No Telegram channels configured")

        # Validate enabled channels
        enabled_channels = [ch for ch in self.config['telegram_channels'].values() if ch.get('enabled', False)]
        if not enabled_channels:
            self.logger.warning("No enabled Telegram channels found")

        self.logger.info(f"Configuration validated: {len(enabled_channels)} enabled channels")

    def setup_folder_structure(self):
        """Create the complete folder structure based on configuration"""
        base_path = Path(self.config['windows_base_path'])

        try:
            # Create base directory
            base_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created base directory: {base_path}")

            # Create channel-specific directories
            for channel_id, channel_config in self.config['telegram_channels'].items():
                if not channel_config.get('enabled', False):
                    continue

                queue_path = channel_config['queue_path']
                channel_dir = base_path / queue_path

                # Create main channel directory
                channel_dir.mkdir(parents=True, exist_ok=True)

                # Create subdirectories if enabled
                if self.config['queue_management'].get('create_media_subdirs', False):
                    (channel_dir / 'media').mkdir(exist_ok=True)
                    (channel_dir / 'images').mkdir(exist_ok=True)
                    (channel_dir / 'documents').mkdir(exist_ok=True)

                # Create processed and failed folders
                if self.config['queue_management'].get('processed_folder'):
                    (channel_dir / self.config['queue_management']['processed_folder']).mkdir(exist_ok=True)

                if self.config['queue_management'].get('failed_folder'):
                    (channel_dir / self.config['queue_management']['failed_folder']).mkdir(exist_ok=True)

                self.logger.info(f"Setup directory structure for {channel_config['name']}: {channel_dir}")

            # Create system directories
            system_dirs = ['logs', 'processed_messages', 'sent_archive', 'inbox']
            for dir_name in system_dirs:
                Path(dir_name).mkdir(exist_ok=True)

            self.logger.info("Folder structure setup completed")

        except Exception as e:
            self.logger.error(f"Failed to setup folder structure: {e}")
            raise

    def get_process_command(self, component: str) -> List[str]:
        """Get the command to start a specific component"""
        python_exe = sys.executable

        commands = {
            'telegram_collector': [
                python_exe, 'telegram_collector_updated.py'
            ],
            'discord_forwarder': [
                python_exe, 'discord_forwarder_production.py'
            ]
        }

        if component not in commands:
            raise ValueError(f"Unknown component: {component}")

        return commands[component]

    def start_component(self, component: str) -> Optional[subprocess.Popen]:
        """Start a specific component"""
        try:
            command = self.get_process_command(component)
            self.logger.info(f"Starting {component}: {' '.join(command)}")

            # Create log files for the component
            log_dir = Path('logs')
            stdout_log = log_dir / f"{component}_stdout.log"
            stderr_log = log_dir / f"{component}_stderr.log"

            # Start the process
            process = subprocess.Popen(
                command,
                stdout=open(stdout_log, 'a', encoding='utf-8'),
                stderr=open(stderr_log, 'a', encoding='utf-8'),
                cwd=Path.cwd(),
                env=os.environ.copy()
            )

            self.processes[component] = {
                'process': process,
                'start_time': datetime.now(),
                'restart_count': self.restart_counts.get(component, 0),
                'stdout_log': stdout_log,
                'stderr_log': stderr_log
            }

            self.logger.info(f"{component} started with PID: {process.pid}")
            return process

        except Exception as e:
            self.logger.error(f"Failed to start {component}: {e}")
            return None

    def stop_component(self, component: str, timeout: int = 30):
        """Stop a specific component"""
        if component not in self.processes:
            self.logger.warning(f"Component {component} is not running")
            return

        process_info = self.processes[component]
        process = process_info['process']

        try:
            self.logger.info(f"Stopping {component} (PID: {process.pid})")

            # Try graceful shutdown first
            process.terminate()

            try:
                process.wait(timeout=timeout)
                self.logger.info(f"{component} stopped gracefully")
            except subprocess.TimeoutExpired:
                self.logger.warning(f"{component} did not stop gracefully, forcing kill")
                process.kill()
                process.wait()

            # Close log files
            if process.stdout and not process.stdout.closed:
                process.stdout.close()
            if process.stderr and not process.stderr.closed:
                process.stderr.close()

            del self.processes[component]

        except Exception as e:
            self.logger.error(f"Error stopping {component}: {e}")

    def restart_component(self, component: str):
        """Restart a specific component"""
        self.logger.info(f"Restarting {component}")

        # Increment restart count
        self.restart_counts[component] = self.restart_counts.get(component, 0) + 1

        # Stop the component
        self.stop_component(component)

        # Wait a moment before restarting
        time.sleep(2)

        # Start the component
        self.start_component(component)

    def check_component_health(self, component: str) -> Dict[str, Any]:
        """Check the health of a specific component"""
        if component not in self.processes:
            return {
                'status': 'not_running',
                'pid': None,
                'uptime': None,
                'memory_usage': None,
                'cpu_percent': None
            }

        process_info = self.processes[component]
        process = process_info['process']

        try:
            # Check if process is still running
            if process.poll() is not None:
                return {
                    'status': 'stopped',
                    'exit_code': process.poll(),
                    'pid': process.pid,
                    'uptime': None,
                    'memory_usage': None,
                    'cpu_percent': None
                }

            # Get process stats using psutil
            try:
                ps_process = psutil.Process(process.pid)
                memory_info = ps_process.memory_info()
                cpu_percent = ps_process.cpu_percent()

                uptime = datetime.now() - process_info['start_time']

                return {
                    'status': 'running',
                    'pid': process.pid,
                    'uptime': str(uptime),
                    'memory_usage': f"{memory_info.rss / 1024 / 1024:.1f} MB",
                    'cpu_percent': f"{cpu_percent:.1f}%",
                    'restart_count': process_info['restart_count']
                }

            except psutil.NoSuchProcess:
                return {
                    'status': 'process_not_found',
                    'pid': process.pid,
                    'uptime': None,
                    'memory_usage': None,
                    'cpu_percent': None
                }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'pid': process.pid if process else None
            }

    def health_check_loop(self):
        """Continuous health checking and auto-restart"""
        while not self.shutdown_event.is_set():
            try:
                current_time = datetime.now()

                for component in ['telegram_collector', 'discord_forwarder']:
                    health = self.check_component_health(component)
                    self.last_health_check[component] = {
                        'timestamp': current_time,
                        'health': health
                    }

                    # Auto-restart if component is stopped
                    if health['status'] in ['stopped', 'not_running', 'process_not_found']:
                        self.monitor_logger.warning(f"{component} is {health['status']}, restarting...")
                        self.restart_component(component)

                # Sleep before next check
                self.shutdown_event.wait(30)  # Check every 30 seconds

            except Exception as e:
                self.monitor_logger.error(f"Health check error: {e}")
                self.shutdown_event.wait(10)

    def process_monitor_loop(self):
        """Monitor process output and log important events"""
        while not self.shutdown_event.is_set():
            try:
                # Check for any messages in the status queue
                try:
                    message = self.status_queue.get_nowait()
                    self.logger.info(f"Status update: {message}")
                except queue.Empty:
                    pass

                # Monitor log files for errors
                self.monitor_log_files()

                self.shutdown_event.wait(5)  # Check every 5 seconds

            except Exception as e:
                self.monitor_logger.error(f"Process monitor error: {e}")
                self.shutdown_event.wait(10)

    def monitor_log_files(self):
        """Monitor component log files for critical errors"""
        for component in self.processes:
            process_info = self.processes[component]
            stderr_log = process_info.get('stderr_log')

            if stderr_log and stderr_log.exists():
                try:
                    # Read last few lines of stderr
                    with open(stderr_log, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if lines:
                            recent_lines = lines[-5:]  # Last 5 lines
                            for line in recent_lines:
                                if any(keyword in line.lower() for keyword in ['error', 'exception', 'failed']):
                                    self.monitor_logger.warning(f"{component} error: {line.strip()}")
                except Exception as e:
                    pass  # Ignore file reading errors

    def start_system(self):
        """Start the complete system"""
        self.logger.info("=== STARTING TELEGRAM TO DISCORD SYSTEM ===")
        self.running = True

        try:
            # Start components
            components = ['telegram_collector', 'discord_forwarder']

            for component in components:
                if self.start_component(component):
                    self.logger.info(f"✓ {component} started successfully")
                else:
                    self.logger.error(f"✗ Failed to start {component}")
                    return False

            # Start monitoring threads
            self.health_check_thread = threading.Thread(target=self.health_check_loop, daemon=True)
            self.process_monitor_thread = threading.Thread(target=self.process_monitor_loop, daemon=True)

            self.health_check_thread.start()
            self.process_monitor_thread.start()

            self.logger.info("=== SYSTEM STARTUP COMPLETE ===")
            self.print_status()

            return True

        except Exception as e:
            self.logger.error(f"System startup failed: {e}")
            self.logger.error(traceback.format_exc())
            return False

    def stop_system(self):
        """Stop the complete system"""
        self.logger.info("=== STOPPING TELEGRAM TO DISCORD SYSTEM ===")
        self.running = False

        # Signal shutdown to monitoring threads
        self.shutdown_event.set()

        # Stop all components
        components = list(self.processes.keys())
        for component in components:
            self.stop_component(component)

        # Wait for monitoring threads to finish
        if self.health_check_thread and self.health_check_thread.is_alive():
            self.health_check_thread.join(timeout=5)

        if self.process_monitor_thread and self.process_monitor_thread.is_alive():
            self.process_monitor_thread.join(timeout=5)

        self.logger.info("=== SYSTEM SHUTDOWN COMPLETE ===")

    def print_status(self):
        """Print current system status"""
        print("\n" + "="*60)
        print("TELEGRAM TO DISCORD SYSTEM STATUS")
        print("="*60)

        print(f"Configuration: {self.config_path}")
        print(f"Base Path: {self.config['windows_base_path']}")
        print(f"Running: {self.running}")

        print("\nCOMPONENTS:")
        for component in ['telegram_collector', 'discord_forwarder']:
            health = self.check_component_health(component)
            status_icon = "✓" if health['status'] == 'running' else "✗"
            print(f"  {status_icon} {component}: {health['status']}")
            if health['status'] == 'running':
                print(f"    PID: {health['pid']}, Uptime: {health['uptime']}")
                print(f"    Memory: {health['memory_usage']}, CPU: {health['cpu_percent']}")

        print("\nCHANNELS:")
        enabled_count = 0
        for channel_id, channel_config in self.config['telegram_channels'].items():
            if channel_config.get('enabled', False):
                enabled_count += 1
                print(f"  ✓ {channel_config['display_name']} -> {channel_config['queue_path']}")

        print(f"\nTotal Enabled Channels: {enabled_count}")
        print("="*60 + "\n")

    def run_interactive_mode(self):
        """Run in interactive mode with command processing"""
        self.logger.info("Starting interactive mode...")

        try:
            while self.running:
                try:
                    print("\nCommands: status, restart <component>, stop, help")
                    cmd = input("system> ").strip().lower()

                    if cmd == 'status':
                        self.print_status()

                    elif cmd.startswith('restart '):
                        component = cmd.split(' ', 1)[1]
                        if component in ['telegram_collector', 'discord_forwarder']:
                            self.restart_component(component)
                        else:
                            print(f"Unknown component: {component}")

                    elif cmd == 'stop':
                        break

                    elif cmd == 'help':
                        print("Available commands:")
                        print("  status - Show system status")
                        print("  restart <component> - Restart telegram_collector or discord_forwarder")
                        print("  stop - Stop the system")
                        print("  help - Show this help")

                    elif cmd == '':
                        continue

                    else:
                        print(f"Unknown command: {cmd}")

                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
                except Exception as e:
                    print(f"Command error: {e}")

        finally:
            self.stop_system()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nReceived shutdown signal, stopping system...")
    global controller
    if controller:
        controller.stop_system()
    sys.exit(0)

def main():
    """Main entry point"""
    global controller

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize controller
        controller = SystemController()

        # Start the system
        if controller.start_system():
            # Run interactive mode
            controller.run_interactive_mode()
        else:
            print("Failed to start system")
            return 1

    except Exception as e:
        print(f"System error: {e}")
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())