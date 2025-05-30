#!/usr/bin/env python3
"""
monitor.py - NHS Digital Triage System Monitor

This script provides real-time monitoring of the NHS Digital Triage system,
including health checks, performance metrics, and alerting.
"""

import time
import json
import requests
import psutil
import sqlite3
from datetime import datetime, timezone
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SystemMonitor:
    def __init__(self, config_file='monitor_config.json'):
        self.config = self.load_config(config_file)
        self.base_url = self.config.get('base_url', 'http://localhost:5000')
        self.db_path = self.config.get('db_path', 'nhs_triage.db')
        self.alert_email = self.config.get('alert_email')
        self.smtp_config = self.config.get('smtp', {})
        
    def load_config(self, config_file):
        """Load monitoring configuration."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default configuration
            return {
                'base_url': 'http://localhost:5000',
                'db_path': 'nhs_triage.db',
                'check_interval': 60,
                'alert_thresholds': {
                    'response_time': 5.0,
                    'cpu_usage': 80.0,
                    'memory_usage': 85.0,
                    'disk_usage': 90.0,
                    'error_rate': 10.0
                }
            }
    
    def check_web_service(self):
        """Check if the web service is responding."""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/system-status", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'healthy',
                    'response_time': response_time,
                    'ollama_available': data.get('ollama_available', False),
                    'total_patients': data.get('total_patients', 0),
                    'total_assessments': data.get('total_assessments', 0)
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': f'HTTP {response.status_code}',
                    'response_time': response_time
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'status': 'down',
                'error': str(e),
                'response_time': None
            }
    
    def check_system_resources(self):
        """Check system resource usage."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        return {
            'cpu_usage': cpu_percent,
            'memory_usage': memory.percent,
            'memory_available': memory.available // (1024**3),  # GB
            'disk_usage': (disk.used / disk.total) * 100,
            'disk_free': disk.free // (1024**3)  # GB
        }
    
    def check_database(self):
        """Check database health and recent activity."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if database is accessible
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            # Check recent activity (last hour)
            cursor.execute("""
                SELECT COUNT(*) FROM triage_assessments 
                WHERE created_at > datetime('now', '-1 hour')
            """)
            recent_assessments = cursor.fetchone()[0]
            
            # Check for recent errors in system logs
            cursor.execute("""
                SELECT COUNT(*) FROM system_logs 
                WHERE level='ERROR' AND created_at > datetime('now', '-1 hour')
            """)
            recent_errors = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'status': 'healthy',
                'table_count': table_count,
                'recent_assessments': recent_assessments,
                'recent_errors': recent_errors
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_ollama_service(self):
        """Check Ollama AI service specifically."""
        try:
            response = requests.get('http://localhost:11434/api/version', timeout=5)
            if response.status_code == 200:
                return {'status': 'healthy', 'version': response.json().get('version')}
            else:
                return {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'status': 'down', 'error': str(e)}
    
    def send_alert(self, subject, message):
        """Send email alert if configured."""
        if not self.alert_email or not self.smtp_config:
            print(f"ALERT: {subject}\n{message}")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['username']
            msg['To'] = self.alert_email
            msg['Subject'] = f"NHS Triage Alert: {subject}"
            
            msg.attach(MIMEText(message, 'plain'))
            
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
                
            print(f"Alert sent: {subject}")
            
        except Exception as e:
            print(f"Failed to send alert: {e}")
    
    def evaluate_health(self, metrics):
        """Evaluate overall system health and generate alerts."""
        issues = []
        thresholds = self.config.get('alert_thresholds', {})
        
        # Check web service
        if metrics['web_service']['status'] != 'healthy':
            issues.append(f"Web service is {metrics['web_service']['status']}")
        elif metrics['web_service']['response_time'] > thresholds.get('response_time', 5.0):
            issues.append(f"Slow response time: {metrics['web_service']['response_time']:.2f}s")
        
        # Check system resources
        resources = metrics['system_resources']
        if resources['cpu_usage'] > thresholds.get('cpu_usage', 80):
            issues.append(f"High CPU usage: {resources['cpu_usage']:.1f}%")
        
        if resources['memory_usage'] > thresholds.get('memory_usage', 85):
            issues.append(f"High memory usage: {resources['memory_usage']:.1f}%")
        
        if resources['disk_usage'] > thresholds.get('disk_usage', 90):
            issues.append(f"High disk usage: {resources['disk_usage']:.1f}%")
        
        # Check database
        if metrics['database']['status'] != 'healthy':
            issues.append(f"Database issue: {metrics['database'].get('error', 'Unknown')}")
        
        if metrics['database'].get('recent_errors', 0) > thresholds.get('error_rate', 10):
            issues.append(f"High error rate: {metrics['database']['recent_errors']} errors in last hour")
        
        # Check Ollama
        if metrics['ollama']['status'] != 'healthy':
            issues.append(f"AI service (Ollama) is {metrics['ollama']['status']}")
        
        return issues
    
    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        print(f"\n🏥 NHS Digital Triage System Monitor - {timestamp}")
        print("=" * 60)
        
        # Collect metrics
        metrics = {
            'timestamp': timestamp,
            'web_service': self.check_web_service(),
            'system_resources': self.check_system_resources(),
            'database': self.check_database(),
            'ollama': self.check_ollama_service()
        }
        
        # Display results
        self.display_metrics(metrics)
        
        # Evaluate health and send alerts
        issues = self.evaluate_health(metrics)
        if issues:
            alert_message = f"System health issues detected at {timestamp}:\n\n"
            alert_message += "\n".join(f"• {issue}" for issue in issues)
            alert_message += f"\n\nFull metrics:\n{json.dumps(metrics, indent=2)}"
            
            self.send_alert("System Health Issues", alert_message)
        
        return metrics
    
    def display_metrics(self, metrics):
        """Display metrics in a readable format."""
        # Web service status
        web = metrics['web_service']
        status_icon = "✅" if web['status'] == 'healthy' else "❌"
        print(f"{status_icon} Web Service: {web['status']}")
        if web.get('response_time'):
            print(f"   Response time: {web['response_time']:.2f}s")
        if web.get('error'):
            print(f"   Error: {web['error']}")
        
        # System resources
        res = metrics['system_resources']
        print(f"💻 System Resources:")
        print(f"   CPU: {res['cpu_usage']:.1f}%")
        print(f"   Memory: {res['memory_usage']:.1f}% ({res['memory_available']}GB available)")
        print(f"   Disk: {res['disk_usage']:.1f}% ({res['disk_free']}GB free)")
        
        # Database
        db = metrics['database']
        db_icon = "✅" if db['status'] == 'healthy' else "❌"
        print(f"{db_icon} Database: {db['status']}")
        if db['status'] == 'healthy':
            print(f"   Recent assessments: {db['recent_assessments']}")
            print(f"   Recent errors: {db['recent_errors']}")
        
        # Ollama
        ollama = metrics['ollama']
        ollama_icon = "✅" if ollama['status'] == 'healthy' else "❌"
        print(f"{ollama_icon} AI Service (Ollama): {ollama['status']}")
        if ollama.get('version'):
            print(f"   Version: {ollama['version']}")
    
    def run_continuous_monitoring(self):
        """Run continuous monitoring with configurable interval."""
        interval = self.config.get('check_interval', 60)
        print(f"🔄 Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.run_monitoring_cycle()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")

def main():
    """Main function to run the monitor."""
    import argparse
    
    parser = argparse.ArgumentParser(description='NHS Digital Triage System Monitor')
    parser.add_argument('--config', default='monitor_config.json', 
                       help='Configuration file path')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=60,
                       help='Monitoring interval in seconds')
    
    args = parser.parse_args()
    
    monitor = SystemMonitor(args.config)
    
    if args.continuous:
        monitor.config['check_interval'] = args.interval
        monitor.run_continuous_monitoring()
    else:
        monitor.run_monitoring_cycle()

if __name__ == '__main__':
    main()