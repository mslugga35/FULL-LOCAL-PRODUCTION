#!/usr/bin/env python3
"""
Production Monitor for Telegram to Discord System
Provides real-time monitoring, health checks, and automated recovery.
"""

import os
import sys
import time
import json
import psutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import queue

class ProductionMonitor:
    def __init__(self):
        self.config = self.load_config()
        self.running = False
        self.monitor_thread = None
        self.stats = {
            'messages_processed': 0,
            'errors_detected': 0,
            'restarts_performed': 0,
            'start_time': datetime.now()
        }

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/production_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # GUI components
        self.root = None
        self.status_queue = queue.Queue()

    def load_config(self):
        """Load routing configuration"""
        try:
            with open('routing_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load config: {e}")
            return {}

    def check_system_controller_process(self):
        """Check if system controller is running"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'system_controller.py' in cmdline:
                        return {
                            'running': True,
                            'pid': proc.info['pid'],
                            'memory': proc.memory_info().rss / 1024 / 1024,  # MB
                            'cpu': proc.cpu_percent(),
                            'create_time': datetime.fromtimestamp(proc.create_time())
                        }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {'running': False}

    def check_message_queue_activity(self):
        """Check message queue for recent activity"""
        try:
            base_path = Path(self.config.get('windows_base_path', 'message_queue'))
            if not base_path.exists():
                return {'active': False, 'reason': 'Base path does not exist'}

            recent_files = []
            cutoff_time = datetime.now() - timedelta(minutes=10)

            # Check each enabled channel
            for channel_id, channel_config in self.config.get('telegram_channels', {}).items():
                if not channel_config.get('enabled', False):
                    continue

                queue_path = channel_config['queue_path']
                channel_dir = base_path / queue_path

                if channel_dir.exists():
                    for file_path in channel_dir.glob('*.json'):
                        try:
                            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if file_time > cutoff_time:
                                recent_files.append({
                                    'file': str(file_path),
                                    'channel': channel_config['name'],
                                    'time': file_time
                                })
                        except Exception:
                            continue

            return {
                'active': len(recent_files) > 0,
                'recent_files': len(recent_files),
                'files': recent_files[:5]  # Show last 5 files
            }

        except Exception as e:
            return {'active': False, 'error': str(e)}

    def check_log_files_for_errors(self):
        """Check log files for recent errors"""
        log_files = [
            'logs/system_controller.log',
            'logs/telegram_collector.log',
            'logs/discord_forwarder_production.log'
        ]

        errors = []
        cutoff_time = datetime.now() - timedelta(minutes=5)

        for log_file in log_files:
            log_path = Path(log_file)
            if not log_path.exists():
                continue

            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-50:]:  # Check last 50 lines
                        if 'ERROR' in line or 'CRITICAL' in line:
                            try:
                                # Simple time parsing for recent errors
                                if any(recent_indicator in line for recent_indicator in [
                                    datetime.now().strftime('%Y-%m-%d'),
                                    datetime.now().strftime('%H:%M')
                                ]):
                                    errors.append({
                                        'file': log_file,
                                        'line': line.strip(),
                                        'severity': 'ERROR' if 'ERROR' in line else 'CRITICAL'
                                    })
                            except:
                                continue

            except Exception:
                continue

        return errors

    def get_system_status(self):
        """Get comprehensive system status"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'system_controller': self.check_system_controller_process(),
            'message_queue': self.check_message_queue_activity(),
            'errors': self.check_log_files_for_errors(),
            'disk_usage': {},
            'memory_usage': psutil.virtual_memory().percent,
            'cpu_usage': psutil.cpu_percent()
        }

        # Check disk usage
        try:
            base_path = Path(self.config.get('windows_base_path', 'message_queue'))
            if base_path.exists():
                disk_usage = psutil.disk_usage(str(base_path))
                status['disk_usage'] = {
                    'total': disk_usage.total / (1024**3),  # GB
                    'used': disk_usage.used / (1024**3),   # GB
                    'free': disk_usage.free / (1024**3),   # GB
                    'percent': (disk_usage.used / disk_usage.total) * 100
                }
        except Exception:
            pass

        return status

    def restart_system_controller(self):
        """Restart the system controller"""
        try:
            self.logger.info("Attempting to restart system controller...")

            # First, try to stop existing process
            controller_status = self.check_system_controller_process()
            if controller_status['running']:
                try:
                    proc = psutil.Process(controller_status['pid'])
                    proc.terminate()
                    proc.wait(timeout=30)
                    self.logger.info("System controller stopped")
                except Exception as e:
                    self.logger.error(f"Failed to stop system controller: {e}")

            # Wait a moment
            time.sleep(5)

            # Start new process
            startup_script = Path('START_SYSTEM_CONTROLLER.bat')
            if startup_script.exists():
                subprocess.Popen([str(startup_script)], shell=True)
                self.logger.info("System controller restart initiated")
                self.stats['restarts_performed'] += 1
                return True
            else:
                self.logger.error("Startup script not found")
                return False

        except Exception as e:
            self.logger.error(f"Failed to restart system controller: {e}")
            return False

    def monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                status = self.get_system_status()

                # Check for critical issues
                critical_issues = []

                # System controller not running
                if not status['system_controller']['running']:
                    critical_issues.append("System controller not running")

                # Too many recent errors
                if len(status['errors']) > 5:
                    critical_issues.append(f"High error count: {len(status['errors'])}")

                # High resource usage
                if status['memory_usage'] > 90:
                    critical_issues.append(f"High memory usage: {status['memory_usage']:.1f}%")

                if status.get('disk_usage', {}).get('percent', 0) > 90:
                    critical_issues.append(f"High disk usage: {status['disk_usage']['percent']:.1f}%")

                # Log status
                if critical_issues:
                    self.logger.warning(f"Critical issues detected: {critical_issues}")
                    self.stats['errors_detected'] += 1

                    # Auto-restart if system controller is not running
                    if "System controller not running" in critical_issues:
                        self.restart_system_controller()

                else:
                    self.logger.info("System status: Normal")

                # Queue status for GUI
                self.status_queue.put(status)

                # Sleep before next check
                time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(10)

    def create_gui(self):
        """Create monitoring GUI"""
        self.root = tk.Tk()
        self.root.title("Telegram to Discord System Monitor")
        self.root.geometry("800x600")

        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Status tab
        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text="System Status")

        # Status display
        self.status_text = scrolledtext.ScrolledText(status_frame, height=15)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Control buttons
        button_frame = ttk.Frame(status_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(button_frame, text="Refresh Status", command=self.update_status_display).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Restart System", command=self.restart_system_controller).pack(side=tk.LEFT, padx=5)

        # Logs tab
        logs_frame = ttk.Frame(notebook)
        notebook.add(logs_frame, text="Recent Logs")

        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=20)
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Statistics tab
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Statistics")

        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=20)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Start periodic updates
        self.root.after(1000, self.periodic_gui_update)

    def update_status_display(self):
        """Update status display"""
        try:
            status = self.get_system_status()

            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, f"System Status - {status['timestamp']}\n")
            self.status_text.insert(tk.END, "=" * 50 + "\n\n")

            # System Controller Status
            sc_status = status['system_controller']
            self.status_text.insert(tk.END, "System Controller:\n")
            if sc_status['running']:
                self.status_text.insert(tk.END, f"  ✓ Running (PID: {sc_status['pid']})\n")
                self.status_text.insert(tk.END, f"  Memory: {sc_status['memory']:.1f} MB\n")
                self.status_text.insert(tk.END, f"  CPU: {sc_status['cpu']:.1f}%\n")
            else:
                self.status_text.insert(tk.END, "  ✗ Not Running\n")

            # Message Queue Activity
            mq_status = status['message_queue']
            self.status_text.insert(tk.END, f"\nMessage Queue:\n")
            if mq_status['active']:
                self.status_text.insert(tk.END, f"  ✓ Active ({mq_status['recent_files']} recent files)\n")
            else:
                self.status_text.insert(tk.END, "  ✗ No recent activity\n")

            # System Resources
            self.status_text.insert(tk.END, f"\nSystem Resources:\n")
            self.status_text.insert(tk.END, f"  Memory: {status['memory_usage']:.1f}%\n")
            self.status_text.insert(tk.END, f"  CPU: {status['cpu_usage']:.1f}%\n")

            if status['disk_usage']:
                du = status['disk_usage']
                self.status_text.insert(tk.END, f"  Disk: {du['percent']:.1f}% ({du['free']:.1f} GB free)\n")

            # Recent Errors
            if status['errors']:
                self.status_text.insert(tk.END, f"\nRecent Errors ({len(status['errors'])}):\n")
                for error in status['errors'][-5:]:
                    self.status_text.insert(tk.END, f"  {error['severity']}: {error['line'][:100]}...\n")

        except Exception as e:
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, f"Error updating status: {e}\n")

    def update_logs_display(self):
        """Update logs display"""
        try:
            self.logs_text.delete(1.0, tk.END)

            log_files = [
                'logs/production_monitor.log',
                'logs/system_controller.log'
            ]

            for log_file in log_files:
                log_path = Path(log_file)
                if log_path.exists():
                    self.logs_text.insert(tk.END, f"\n=== {log_file} ===\n")
                    try:
                        with open(log_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            # Show last 20 lines
                            for line in lines[-20:]:
                                self.logs_text.insert(tk.END, line)
                    except Exception as e:
                        self.logs_text.insert(tk.END, f"Error reading {log_file}: {e}\n")

            # Auto-scroll to bottom
            self.logs_text.see(tk.END)

        except Exception as e:
            self.logs_text.delete(1.0, tk.END)
            self.logs_text.insert(tk.END, f"Error updating logs: {e}\n")

    def update_stats_display(self):
        """Update statistics display"""
        try:
            self.stats_text.delete(1.0, tk.END)

            uptime = datetime.now() - self.stats['start_time']

            self.stats_text.insert(tk.END, "Production Monitor Statistics\n")
            self.stats_text.insert(tk.END, "=" * 30 + "\n\n")
            self.stats_text.insert(tk.END, f"Uptime: {uptime}\n")
            self.stats_text.insert(tk.END, f"Messages Processed: {self.stats['messages_processed']}\n")
            self.stats_text.insert(tk.END, f"Errors Detected: {self.stats['errors_detected']}\n")
            self.stats_text.insert(tk.END, f"Restarts Performed: {self.stats['restarts_performed']}\n")

            # Channel statistics
            self.stats_text.insert(tk.END, f"\nChannel Configuration:\n")
            for channel_id, channel_config in self.config.get('telegram_channels', {}).items():
                status = "✓ Enabled" if channel_config.get('enabled', False) else "✗ Disabled"
                self.stats_text.insert(tk.END, f"  {channel_config['name']}: {status}\n")

        except Exception as e:
            self.stats_text.insert(tk.END, f"Error updating stats: {e}\n")

    def periodic_gui_update(self):
        """Periodic GUI update"""
        if self.root:
            try:
                # Process any status updates from monitoring thread
                try:
                    status = self.status_queue.get_nowait()
                    # Update displays based on status
                except queue.Empty:
                    pass

                # Schedule next update
                self.root.after(5000, self.periodic_gui_update)  # Update every 5 seconds

            except Exception as e:
                self.logger.error(f"GUI update error: {e}")

    def start_monitoring(self, gui=True):
        """Start the monitoring system"""
        self.running = True
        self.logger.info("Starting production monitor...")

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitor_thread.start()

        if gui:
            # Start GUI
            self.create_gui()
            self.update_status_display()
            self.update_logs_display()
            self.update_stats_display()
            self.root.mainloop()
        else:
            # Console mode
            try:
                while self.running:
                    time.sleep(10)
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")

        self.stop_monitoring()

    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.running = False
        self.logger.info("Production monitor stopped")

def main():
    """Main entry point"""
    try:
        # Ensure we're in the right directory
        os.chdir(Path(__file__).parent)

        # Create logs directory
        os.makedirs('logs', exist_ok=True)

        # Create and start monitor
        monitor = ProductionMonitor()

        # Check command line arguments
        gui_mode = '--no-gui' not in sys.argv

        monitor.start_monitoring(gui=gui_mode)

        return 0

    except Exception as e:
        print(f"Monitor startup error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())