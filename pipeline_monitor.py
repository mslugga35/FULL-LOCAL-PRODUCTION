#!/usr/bin/env python3
"""
Pipeline Health Monitor - Monitors the complete message flow pipeline
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

class PipelineMonitor:
    def __init__(self):
        self.base_dir = Path(r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION")
        self.recent_messages_dir = self.base_dir / "recent_messages"
        self.message_queue_dir = self.base_dir / "message_queue"
        self.logs_dir = self.base_dir / "logs"

        self.queue_folders = ['uatb', 'diamond', 'free_cappers', 'paid_chamba', 'paid_diamond', 'paid_uatb']

    def count_files_in_directory(self, directory):
        """Count JSON files in a directory"""
        if not directory.exists():
            return 0
        return len(list(directory.glob("*.json")))

    def get_recent_files(self, directory, hours=1):
        """Get files modified in the last N hours"""
        if not directory.exists():
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_files = []

        for file_path in directory.glob("*.json"):
            try:
                if datetime.fromtimestamp(file_path.stat().st_mtime) > cutoff_time:
                    recent_files.append(file_path)
            except:
                continue

        return recent_files

    def check_log_activity(self, log_file, hours=1):
        """Check if a log file has recent activity"""
        log_path = self.logs_dir / log_file
        if not log_path.exists():
            return False, "Log file not found"

        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            if datetime.fromtimestamp(log_path.stat().st_mtime) > cutoff_time:
                return True, "Recent activity"
            else:
                return False, f"No activity in {hours} hours"
        except:
            return False, "Cannot read log file"

    def analyze_queue_distribution(self):
        """Analyze message distribution across queue folders"""
        distribution = {}
        total_queued = 0

        for folder in self.queue_folders:
            folder_path = self.message_queue_dir / folder
            count = self.count_files_in_directory(folder_path)
            distribution[folder] = count
            total_queued += count

        return distribution, total_queued

    def check_pipeline_flow(self):
        """Check the flow rate of messages through the pipeline"""
        # Recent messages waiting to be processed
        recent_count = self.count_files_in_directory(self.recent_messages_dir)
        recent_files_1h = len(self.get_recent_files(self.recent_messages_dir, 1))

        # Messages in queue folders
        queue_distribution, total_queued = self.analyze_queue_distribution()

        # Recent activity in queues
        recent_queue_activity = 0
        for folder in self.queue_folders:
            folder_path = self.message_queue_dir / folder
            recent_queue_activity += len(self.get_recent_files(folder_path, 1))

        return {
            'recent_messages': {
                'total': recent_count,
                'recent_1h': recent_files_1h
            },
            'message_queue': {
                'total': total_queued,
                'distribution': queue_distribution,
                'recent_1h': recent_queue_activity
            }
        }

    def check_service_health(self):
        """Check health of each service based on log activity"""
        services = {
            'telegram-collector': ['telegram-collector-out.log', 'telegram-collector-error.log'],
            'message-processor': ['message-processor-out.log', 'message-processor-error.log'],
            'discord-sender': ['discord-sender-out.log', 'discord-sender-error.log'],
            'discord-forwarder': ['discord-forwarder-out.log', 'discord-forwarder-error.log']
        }

        service_status = {}

        for service, (out_log, err_log) in services.items():
            out_active, out_msg = self.check_log_activity(out_log, 0.5)  # 30 minutes
            err_active, err_msg = self.check_log_activity(err_log, 0.5)

            if out_active:
                status = "🟢 ACTIVE"
            elif err_active:
                status = "🟡 ERRORS"
            else:
                status = "🔴 INACTIVE"

            service_status[service] = {
                'status': status,
                'out_log': out_msg,
                'err_log': err_msg
            }

        return service_status

    def generate_report(self):
        """Generate a comprehensive pipeline health report"""
        print("\n" + "="*70)
        print("📊 MESSAGE PIPELINE HEALTH REPORT")
        print("="*70)
        print(f"🕒 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Pipeline flow analysis
        flow_data = self.check_pipeline_flow()

        print("📥 MESSAGE FLOW STATUS")
        print("-" * 30)
        print(f"Recent Messages (inbox):     {flow_data['recent_messages']['total']:4d} total, {flow_data['recent_messages']['recent_1h']:3d} in last hour")
        print(f"Message Queue (processing):  {flow_data['message_queue']['total']:4d} total, {flow_data['message_queue']['recent_1h']:3d} in last hour")
        print()

        # Queue distribution
        print("📂 QUEUE DISTRIBUTION")
        print("-" * 30)
        for folder, count in flow_data['message_queue']['distribution'].items():
            bar = "█" * min(20, count // 5) if count > 0 else "-"
            print(f"{folder:15s}: {count:4d} {bar}")
        print()

        # Service health
        print("🔧 SERVICE HEALTH")
        print("-" * 30)
        service_status = self.check_service_health()

        for service, status in service_status.items():
            print(f"{service:18s}: {status['status']}")
            if "INACTIVE" in status['status'] or "ERRORS" in status['status']:
                print(f"                     Out: {status['out_log']}")
                print(f"                     Err: {status['err_log']}")
        print()

        # Pipeline health assessment
        print("🩺 PIPELINE ASSESSMENT")
        print("-" * 30)

        issues = []
        recommendations = []

        # Check for bottlenecks
        if flow_data['recent_messages']['total'] > 100:
            issues.append("⚠️  Large backlog in recent_messages")
            recommendations.append("🔧 Check message processor service")

        if flow_data['message_queue']['total'] > 500:
            issues.append("⚠️  Large backlog in message queues")
            recommendations.append("🔧 Check Discord sender service")

        if flow_data['recent_messages']['recent_1h'] == 0:
            issues.append("⚠️  No new messages in last hour")
            recommendations.append("🔧 Check Telegram collector service")

        if flow_data['message_queue']['recent_1h'] == 0 and flow_data['message_queue']['total'] > 0:
            issues.append("⚠️  No queue activity in last hour")
            recommendations.append("🔧 Check message processor and Discord sender")

        # Check service status
        inactive_services = [name for name, status in service_status.items() if "INACTIVE" in status['status']]
        if inactive_services:
            issues.append(f"❌ Inactive services: {', '.join(inactive_services)}")
            recommendations.append("🔧 Restart inactive services with PM2")

        if not issues:
            print("✅ Pipeline appears healthy")
        else:
            print("Issues found:")
            for issue in issues:
                print(f"  {issue}")
            print("\nRecommendations:")
            for rec in recommendations:
                print(f"  {rec}")

        print("\n" + "="*70)

    def run_continuous_monitoring(self, interval_minutes=5):
        """Run continuous monitoring"""
        print(f"🔍 Starting continuous pipeline monitoring (every {interval_minutes} minutes)")
        print("Press Ctrl+C to stop")

        try:
            while True:
                self.generate_report()
                time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")

def main():
    import sys

    monitor = PipelineMonitor()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--continuous':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            monitor.run_continuous_monitoring(interval)
        elif sys.argv[1] == '--help':
            print("Pipeline Monitor Usage:")
            print("  python pipeline_monitor.py              # Single report")
            print("  python pipeline_monitor.py --continuous # Continuous monitoring (5 min)")
            print("  python pipeline_monitor.py --continuous 2 # Custom interval (2 min)")
    else:
        monitor.generate_report()

if __name__ == '__main__':
    main()