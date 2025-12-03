#!/usr/bin/env python3
"""
Weekly Email Report Cron Job
Run this script every Sunday at 9:00 AM to send weekly progress reports to all parents.

Setup instructions:
1. Make executable: chmod +x send_weekly_reports.py
2. Add to crontab: crontab -e
3. Add line: 0 9 * * 0 /path/to/cozmiclearning/send_weekly_reports.py

Or use a task scheduler like Render Cron Jobs, Heroku Scheduler, or AWS EventBridge.
"""

import os
import sys

# Add project directory to path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

# Set up Flask app context
from app import app, db, Parent, send_weekly_report_email
from datetime import datetime

def send_all_weekly_reports():
    """Send weekly reports to all parents who have email reports enabled."""
    with app.app_context():
        print(f"[{datetime.now()}] Starting weekly report job...")
        
        # Get all parents with email reports enabled
        parents = Parent.query.filter_by(email_reports_enabled=True).all()
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for parent in parents:
            try:
                # Check if parent has students
                if not parent.students:
                    skip_count += 1
                    continue
                
                # Send report
                success = send_weekly_report_email(parent)
                
                if success:
                    success_count += 1
                    print(f"✅ Sent report to {parent.email}")
                else:
                    skip_count += 1
                    print(f"⏭️  Skipped {parent.email} (no activity or disabled)")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ Error sending to {parent.email}: {e}")
        
        print(f"\n[{datetime.now()}] Job complete!")
        print(f"📊 Results: {success_count} sent, {skip_count} skipped, {error_count} errors")
        
        return success_count, skip_count, error_count

if __name__ == "__main__":
    send_all_weekly_reports()
