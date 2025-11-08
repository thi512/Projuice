"""
Email Reporting System - Send scheduled reports via SMTP
Supports any email provider (Gmail, Outlook, custom SMTP servers)
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import schedule
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailReporter:
    """
    Email reporting system with SMTP support for any provider
    """

    def __init__(self, config):
        """
        Initialize email reporter

        Args:
            config: System configuration
        """
        self.config = config
        email_config = config.get('email_reporting', {})

        self.enabled = email_config.get('enabled', False)
        self.smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = email_config.get('smtp_port', 587)
        self.use_tls = email_config.get('use_tls', True)
        self.username = email_config.get('username', '')
        self.password = email_config.get('password', '')
        self.from_email = email_config.get('from_email', self.username)
        self.from_name = email_config.get('from_name', 'AI Camera System')

        # Recipients
        self.recipients = email_config.get('recipients', [])

        # Report schedules
        self.schedules = email_config.get('schedules', {
            'daily_summary': {'enabled': True, 'time': '08:00'},
            'weekly_summary': {'enabled': True, 'day': 'monday', 'time': '09:00'},
            'license_plate_report': {'enabled': True, 'time': '18:00'}
        })

        # Database and analytics references (set later)
        self.db = None
        self.plate_analytics = None

        logger.info(f"Email reporter initialized (enabled: {self.enabled})")

    def set_database(self, database_manager):
        """Set database manager reference"""
        self.db = database_manager

    def set_plate_analytics(self, plate_analytics):
        """Set plate analytics reference"""
        self.plate_analytics = plate_analytics

    def send_email(self, subject: str, body_html: str, recipients: List[str] = None,
                   attachments: List[Dict] = None) -> bool:
        """
        Send email via SMTP

        Args:
            subject: Email subject
            body_html: HTML email body
            recipients: List of recipient emails (uses config default if None)
            attachments: List of attachments [{filename, content, type}]

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.warning("Email reporting is disabled")
            return False

        if not recipients:
            recipients = self.recipients

        if not recipients:
            logger.error("No recipients configured")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = ', '.join(recipients)
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

            # Attach HTML body
            html_part = MIMEText(body_html, 'html')
            msg.attach(html_part)

            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                if self.username and self.password:
                    server.login(self.username, self.password)

                server.send_message(msg)

            logger.info(f"Email sent successfully to {len(recipients)} recipient(s)")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict):
        """Add attachment to email message"""
        filename = attachment.get('filename', 'attachment')
        content = attachment.get('content')
        att_type = attachment.get('type', 'application/octet-stream')

        if att_type.startswith('image/'):
            part = MIMEImage(content)
        else:
            part = MIMEApplication(content)

        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(part)

    def send_daily_summary(self):
        """Send daily summary report"""
        logger.info("Generating daily summary report...")

        # Get today's date range
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        time_range = {'start': today, 'end': tomorrow}

        # Gather statistics
        stats = self._gather_daily_stats(time_range)

        # Generate HTML report
        html = self._generate_daily_summary_html(stats, today)

        # Send email
        subject = f"Daily Summary Report - {today.strftime('%B %d, %Y')}"
        self.send_email(subject, html)

    def send_weekly_summary(self):
        """Send weekly summary report"""
        logger.info("Generating weekly summary report...")

        # Get week date range
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)

        time_range = {'start': week_ago, 'end': today}

        # Gather statistics
        stats = self._gather_weekly_stats(time_range)

        # Generate HTML report
        html = self._generate_weekly_summary_html(stats, week_ago, today)

        # Send email
        subject = f"Weekly Summary Report - {week_ago.strftime('%b %d')} to {today.strftime('%b %d, %Y')}"
        self.send_email(subject, html)

    def send_license_plate_report(self):
        """Send license plate activity report"""
        logger.info("Generating license plate report...")

        # Get today's date range
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        time_range = {'start': today, 'end': tomorrow}

        # Get plate statistics
        if self.plate_analytics:
            plate_stats = self.plate_analytics.get_plate_statistics(time_range)
            suspicious = self.plate_analytics.find_suspicious_patterns()
        else:
            plate_stats = {}
            suspicious = []

        # Generate HTML report
        html = self._generate_plate_report_html(plate_stats, suspicious, today)

        # Send email
        subject = f"License Plate Report - {today.strftime('%B %d, %Y')}"
        self.send_email(subject, html)

    def send_anomaly_alert(self, anomaly: Dict):
        """
        Send immediate email alert for anomaly

        Args:
            anomaly: Anomaly details
        """
        if not self.enabled:
            return

        html = self._generate_anomaly_alert_html(anomaly)
        subject = f"⚠️ Security Alert: {anomaly.get('anomaly_type', 'Unknown')}"
        self.send_email(subject, html)

    def _gather_daily_stats(self, time_range: Dict) -> Dict:
        """Gather statistics for daily report"""
        stats = {
            'total_detections': 0,
            'person_count': 0,
            'vehicle_count': 0,
            'license_plates': 0,
            'anomalies': 0,
            'top_plates': [],
            'peak_hour': 0
        }

        if not self.db:
            return stats

        try:
            from sqlalchemy import func
            session = self.db.Session()

            # Total detections
            stats['total_detections'] = session.query(self.db.Detection).filter(
                self.db.Detection.timestamp >= time_range['start'],
                self.db.Detection.timestamp <= time_range['end']
            ).count()

            # Person count
            stats['person_count'] = session.query(self.db.PersonAppearance).filter(
                self.db.PersonAppearance.timestamp >= time_range['start'],
                self.db.PersonAppearance.timestamp <= time_range['end']
            ).count()

            # Vehicle count
            stats['vehicle_count'] = session.query(self.db.VehicleRecord).filter(
                self.db.VehicleRecord.timestamp >= time_range['start'],
                self.db.VehicleRecord.timestamp <= time_range['end']
            ).count()

            # License plates
            stats['license_plates'] = session.query(self.db.LicensePlate).filter(
                self.db.LicensePlate.timestamp >= time_range['start'],
                self.db.LicensePlate.timestamp <= time_range['end']
            ).count()

            # Top plates
            top_plates = session.query(
                self.db.LicensePlate.plate_number,
                func.count(self.db.LicensePlate.id).label('count')
            ).filter(
                self.db.LicensePlate.timestamp >= time_range['start'],
                self.db.LicensePlate.timestamp <= time_range['end']
            ).group_by(
                self.db.LicensePlate.plate_number
            ).order_by(
                func.count(self.db.LicensePlate.id).desc()
            ).limit(5).all()

            stats['top_plates'] = [{'plate': p, 'count': c} for p, c in top_plates]

            # Anomalies
            stats['anomalies'] = session.query(self.db.Anomaly).filter(
                self.db.Anomaly.timestamp >= time_range['start'],
                self.db.Anomaly.timestamp <= time_range['end']
            ).count()

            session.close()

        except Exception as e:
            logger.error(f"Failed to gather daily stats: {e}")

        return stats

    def _gather_weekly_stats(self, time_range: Dict) -> Dict:
        """Gather statistics for weekly report"""
        stats = self._gather_daily_stats(time_range)
        stats['days'] = 7

        # Add weekly-specific data
        if self.db:
            try:
                from sqlalchemy import func
                session = self.db.Session()

                # Daily breakdown
                daily = session.query(
                    func.date(self.db.Detection.timestamp).label('date'),
                    func.count(self.db.Detection.id).label('count')
                ).filter(
                    self.db.Detection.timestamp >= time_range['start'],
                    self.db.Detection.timestamp <= time_range['end']
                ).group_by('date').all()

                stats['daily_breakdown'] = [
                    {'date': str(d), 'count': c} for d, c in daily
                ]

                session.close()

            except Exception as e:
                logger.error(f"Failed to gather weekly stats: {e}")

        return stats

    def _generate_daily_summary_html(self, stats: Dict, date: datetime) -> str:
        """Generate HTML for daily summary"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .stats {{
            padding: 30px;
        }}
        .stat-box {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
        }}
        .stat-box h3 {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .stat-box .value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }}
        .table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        .table th {{
            background: #667eea;
            color: white;
            padding: 10px;
            text-align: left;
        }}
        .table td {{
            padding: 10px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
        .alert {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Daily Summary Report</h1>
            <p>{date.strftime('%A, %B %d, %Y')}</p>
        </div>

        <div class="stats">
            <div class="stat-box">
                <h3>Total Detections</h3>
                <div class="value">{stats.get('total_detections', 0)}</div>
            </div>

            <div class="stat-box">
                <h3>👤 People Detected</h3>
                <div class="value">{stats.get('person_count', 0)}</div>
            </div>

            <div class="stat-box">
                <h3>🚗 Vehicles Detected</h3>
                <div class="value">{stats.get('vehicle_count', 0)}</div>
            </div>

            <div class="stat-box">
                <h3>🔢 License Plates Recognized</h3>
                <div class="value">{stats.get('license_plates', 0)}</div>
            </div>

            {f'''
            <div class="alert">
                <h3 style="margin: 0 0 10px 0; color: #856404;">⚠️ Anomalies Detected</h3>
                <div style="font-size: 24px; font-weight: bold; color: #856404;">
                    {stats.get('anomalies', 0)}
                </div>
            </div>
            ''' if stats.get('anomalies', 0) > 0 else ''}

            {f'''
            <h3 style="margin-top: 20px; color: #333;">Top License Plates Today</h3>
            <table class="table">
                <tr>
                    <th>License Plate</th>
                    <th>Appearances</th>
                </tr>
                {''.join([f'<tr><td>{p["plate"]}</td><td>{p["count"]}</td></tr>'
                          for p in stats.get('top_plates', [])])}
            </table>
            ''' if stats.get('top_plates') else ''}
        </div>

        <div class="footer">
            <p>Generated by AI Camera System on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>This is an automated report. Configure settings in config.yaml</p>
        </div>
    </div>
</body>
</html>
"""

    def _generate_weekly_summary_html(self, stats: Dict, start_date: datetime, end_date: datetime) -> str:
        """Generate HTML for weekly summary"""
        daily_data = stats.get('daily_breakdown', [])

        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 700px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .stats {{
            padding: 30px;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-box {{
            background: #f8f9fa;
            border-left: 4px solid #11998e;
            padding: 20px;
            border-radius: 5px;
        }}
        .stat-box h3 {{
            margin: 0 0 10px 0;
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        .stat-box .value {{
            font-size: 28px;
            font-weight: bold;
            color: #11998e;
        }}
        .table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        .table th {{
            background: #11998e;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        .table td {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Weekly Summary Report</h1>
            <p>{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}</p>
        </div>

        <div class="stats">
            <div class="stat-grid">
                <div class="stat-box">
                    <h3>Total Detections</h3>
                    <div class="value">{stats.get('total_detections', 0)}</div>
                </div>
                <div class="stat-box">
                    <h3>👤 People</h3>
                    <div class="value">{stats.get('person_count', 0)}</div>
                </div>
                <div class="stat-box">
                    <h3>🚗 Vehicles</h3>
                    <div class="value">{stats.get('vehicle_count', 0)}</div>
                </div>
                <div class="stat-box">
                    <h3>🔢 License Plates</h3>
                    <div class="value">{stats.get('license_plates', 0)}</div>
                </div>
            </div>

            <h3 style="color: #333; margin-top: 30px;">Daily Breakdown</h3>
            <table class="table">
                <tr>
                    <th>Date</th>
                    <th>Detections</th>
                </tr>
                {''.join([f'<tr><td>{d["date"]}</td><td>{d["count"]}</td></tr>'
                          for d in daily_data])}
            </table>

            <h3 style="color: #333; margin-top: 30px;">Most Frequent Plates This Week</h3>
            <table class="table">
                <tr>
                    <th>License Plate</th>
                    <th>Total Appearances</th>
                </tr>
                {''.join([f'<tr><td>{p["plate"]}</td><td>{p["count"]}</td></tr>'
                          for p in stats.get('top_plates', [])])}
            </table>
        </div>

        <div style="background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px;">
            <p>Generated by AI Camera System - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""

    def _generate_plate_report_html(self, plate_stats: Dict, suspicious: List[Dict], date: datetime) -> str:
        """Generate HTML for license plate report"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 650px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .stats {{
            padding: 30px;
        }}
        .stat-box {{
            background: #f8f9fa;
            border-left: 4px solid #f5576c;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
        }}
        .alert-box {{
            background: #fff3cd;
            border: 2px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        .table th {{
            background: #f5576c;
            color: white;
            padding: 10px;
            text-align: left;
        }}
        .table td {{
            padding: 10px;
            border-bottom: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔢 License Plate Report</h1>
            <p>{date.strftime('%A, %B %d, %Y')}</p>
        </div>

        <div class="stats">
            <div class="stat-box">
                <h3>Total Plates Detected</h3>
                <div style="font-size: 32px; font-weight: bold; color: #f5576c;">
                    {plate_stats.get('total_plates', 0)}
                </div>
            </div>

            <div class="stat-box">
                <h3>Unique Vehicles</h3>
                <div style="font-size: 32px; font-weight: bold; color: #f5576c;">
                    {plate_stats.get('unique_plates', 0)}
                </div>
            </div>

            {f'''
            <div class="alert-box">
                <h3 style="margin: 0 0 10px 0; color: #856404;">⚠️ Suspicious Activity</h3>
                <p style="margin: 0;">{len(suspicious)} suspicious pattern(s) detected</p>
            </div>
            ''' if suspicious else ''}

            <h3 style="margin-top: 20px; color: #333;">Most Frequent Plates</h3>
            <table class="table">
                <tr>
                    <th>License Plate</th>
                    <th>Appearances</th>
                </tr>
                {''.join([f'<tr><td><strong>{p["plate"]}</strong></td><td>{p["count"]}</td></tr>'
                          for p in plate_stats.get('most_frequent', [])])}
            </table>

            {f'''
            <h3 style="margin-top: 30px; color: #333;">⚠️ Suspicious Patterns</h3>
            <table class="table">
                <tr>
                    <th>Plate</th>
                    <th>Pattern</th>
                    <th>Severity</th>
                </tr>
                {''.join([f'<tr><td>{s.get("plate", "N/A")}</td><td>{s["type"]}</td><td>{s["severity"]}</td></tr>'
                          for s in suspicious[:10]])}
            </table>
            ''' if suspicious else ''}
        </div>

        <div style="background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px;">
            <p>Automated License Plate Recognition Report</p>
            <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""

    def _generate_anomaly_alert_html(self, anomaly: Dict) -> str:
        """Generate HTML for anomaly alert"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 500px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            background: #dc3545;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .content {{
            padding: 30px;
        }}
        .detail {{
            margin-bottom: 15px;
        }}
        .detail strong {{
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">⚠️ Security Alert</h1>
        </div>
        <div class="content">
            <div class="detail">
                <strong>Type:</strong> {anomaly.get('anomaly_type', 'Unknown')}
            </div>
            <div class="detail">
                <strong>Severity:</strong> {anomaly.get('severity', 0) * 100:.0f}%
            </div>
            <div class="detail">
                <strong>Description:</strong> {anomaly.get('description', 'No description')}
            </div>
            <div class="detail">
                <strong>Time:</strong> {anomaly.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </div>
</body>
</html>
"""

    def start_scheduled_reports(self):
        """Start scheduled report generation"""
        if not self.enabled:
            logger.info("Email reporting disabled, not starting scheduler")
            return

        logger.info("Starting scheduled email reports...")

        # Schedule daily summary
        if self.schedules.get('daily_summary', {}).get('enabled'):
            time_str = self.schedules['daily_summary'].get('time', '08:00')
            schedule.every().day.at(time_str).do(self.send_daily_summary)
            logger.info(f"Daily summary scheduled for {time_str}")

        # Schedule weekly summary
        if self.schedules.get('weekly_summary', {}).get('enabled'):
            day = self.schedules['weekly_summary'].get('day', 'monday')
            time_str = self.schedules['weekly_summary'].get('time', '09:00')
            getattr(schedule.every(), day).at(time_str).do(self.send_weekly_summary)
            logger.info(f"Weekly summary scheduled for {day} at {time_str}")

        # Schedule license plate report
        if self.schedules.get('license_plate_report', {}).get('enabled'):
            time_str = self.schedules['license_plate_report'].get('time', '18:00')
            schedule.every().day.at(time_str).do(self.send_license_plate_report)
            logger.info(f"License plate report scheduled for {time_str}")

        # Run scheduler in background thread
        def run_scheduler():
            while self.enabled:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Email report scheduler started")

    def test_email_connection(self) -> bool:
        """
        Test email configuration

        Returns:
            True if connection successful
        """
        try:
            test_html = "<h1>Test Email</h1><p>Your email configuration is working correctly!</p>"
            return self.send_email(
                "Test Email from AI Camera System",
                test_html
            )
        except Exception as e:
            logger.error(f"Email test failed: {e}")
            return False
