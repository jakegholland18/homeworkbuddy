#!/usr/bin/env python3
"""
Test email configuration for CozmicLearning
Run this to verify your email settings work before using the weekly reports.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project to path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

def test_email_config():
    """Test email configuration and send a test message."""
    print("=" * 60)
    print("CozmicLearning Email Configuration Test")
    print("=" * 60)
    print()
    
    # Check environment variables
    print("📋 Checking environment variables...")
    print()
    
    required_vars = {
        'MAIL_SERVER': os.environ.get('MAIL_SERVER'),
        'MAIL_PORT': os.environ.get('MAIL_PORT'),
        'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS'),
        'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
        'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER'),
    }
    
    missing = []
    for var, value in required_vars.items():
        if value:
            # Mask password
            display_value = value if var != 'MAIL_PASSWORD' else ('*' * 8 + value[-4:] if len(value) > 4 else '****')
            print(f"  ✓ {var}: {display_value}")
        else:
            print(f"  ✗ {var}: NOT SET")
            missing.append(var)
    
    print()
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print()
        print("Please update your .env file with valid credentials.")
        print("See EMAIL_SETUP.md for detailed instructions.")
        return False
    
    # Try importing Flask-Mail
    print("📦 Checking Flask-Mail installation...")
    try:
        from flask_mail import Mail, Message
        print("  ✓ Flask-Mail is installed")
    except ImportError:
        print("  ✗ Flask-Mail is NOT installed")
        print()
        print("Run: pip install Flask-Mail")
        return False
    
    print()
    
    # Try initializing the app
    print("🚀 Initializing Flask app...")
    try:
        from app import app, mail
        print("  ✓ App initialized successfully")
    except Exception as e:
        print(f"  ✗ Error initializing app: {e}")
        return False
    
    print()
    
    # Send test email
    print("📧 Sending test email...")
    recipient = input("Enter your email address to receive test: ").strip()
    
    if not recipient:
        print("  ✗ No email address provided")
        return False
    
    try:
        with app.app_context():
            from flask_mail import Message as EmailMessage
            
            msg = EmailMessage(
                subject="✅ CozmicLearning Email Test",
                recipients=[recipient],
            )
            
            msg.html = """
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background: #f5f7fa;">
                <div style="max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    <h1 style="color: #5c6bff; margin: 0 0 20px;">🎉 Email Test Successful!</h1>
                    <p style="color: #666; line-height: 1.6;">
                        Your CozmicLearning email configuration is working correctly!
                    </p>
                    <p style="color: #666; line-height: 1.6;">
                        You're now ready to send weekly progress reports to parents.
                    </p>
                    <div style="background: #f5f7fa; padding: 15px; border-radius: 8px; margin-top: 20px;">
                        <strong style="color: #333;">Configuration:</strong><br>
                        <span style="color: #8a92b3; font-size: 14px;">
                            Server: {}<br>
                            Port: {}<br>
                            From: {}
                        </span>
                    </div>
                </div>
            </body>
            </html>
            """.format(
                required_vars['MAIL_SERVER'],
                required_vars['MAIL_PORT'],
                required_vars['MAIL_DEFAULT_SENDER']
            )
            
            mail.send(msg)
            print(f"  ✓ Test email sent to {recipient}")
            print()
            print("🎉 SUCCESS! Check your inbox (and spam folder).")
            print()
            return True
            
    except Exception as e:
        print(f"  ✗ Error sending email: {e}")
        print()
        print("Common issues:")
        print("  - Gmail: Use App Password, not regular password")
        print("  - Check MAIL_USERNAME and MAIL_PASSWORD are correct")
        print("  - Verify 2-Step Verification is enabled (Gmail)")
        print("  - Check firewall/network allows SMTP connections")
        print()
        return False

if __name__ == "__main__":
    success = test_email_config()
    sys.exit(0 if success else 1)
