# Email Configuration for CozmicLearning

## Setup Instructions

### 1. Gmail Setup (Recommended for Testing)

1. **Create a Gmail App Password** (if using Gmail):
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification if not already enabled
   - Go to "App passwords"
   - Generate new app password for "Mail"
   - Copy the 16-character password

2. **Set Environment Variables**:

```bash
# For local development (add to .env file)
export MAIL_SERVER=smtp.gmail.com
export MAIL_PORT=587
export MAIL_USE_TLS=True
export MAIL_USERNAME=your-email@gmail.com
export MAIL_PASSWORD=your-app-password-here
export MAIL_DEFAULT_SENDER=noreply@cozmiclearning.com
```

3. **For Production (Render/Heroku)**:
   - Add these as environment variables in your hosting dashboard
   - Same names as above

### 2. Alternative Email Services

#### SendGrid
```bash
export MAIL_SERVER=smtp.sendgrid.net
export MAIL_PORT=587
export MAIL_USERNAME=apikey
export MAIL_PASSWORD=your-sendgrid-api-key
```

#### Mailgun
```bash
export MAIL_SERVER=smtp.mailgun.org
export MAIL_PORT=587
export MAIL_USERNAME=postmaster@your-domain.mailgun.org
export MAIL_PASSWORD=your-mailgun-password
```

#### AWS SES
```bash
export MAIL_SERVER=email-smtp.us-east-1.amazonaws.com
export MAIL_PORT=587
export MAIL_USERNAME=your-ses-smtp-username
export MAIL_PASSWORD=your-ses-smtp-password
```

### 3. Testing Email Setup

1. Log in as a parent account
2. Go to Settings → Email Preferences
3. Make sure "Weekly Reports" is enabled
4. Click "Send Test Report Now"
5. Check your email inbox (and spam folder)

### 4. Automated Weekly Reports

#### Option A: Cron Job (Linux/Mac Server)
```bash
# Make script executable
chmod +x send_weekly_reports.py

# Edit crontab
crontab -e

# Add this line to run every Sunday at 9 AM
0 9 * * 0 /path/to/cozmiclearning/send_weekly_reports.py
```

#### Option B: Render Cron Jobs
```yaml
# Add to render.yaml
services:
  - type: web
    name: cozmiclearning
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    
  - type: cron
    name: weekly-reports
    env: python
    schedule: "0 9 * * 0"  # Every Sunday at 9 AM UTC
    buildCommand: pip install -r requirements.txt
    startCommand: python send_weekly_reports.py
```

#### Option C: Heroku Scheduler
1. Install Heroku Scheduler addon
2. Add job: `python send_weekly_reports.py`
3. Set frequency: Every Sunday at 9:00 AM

#### Option D: Manual Trigger (for testing)
Access `/parent/send-test-report` route while logged in as parent

### 5. Email Template Customization

Edit `website/templates/emails/weekly_report.html` to customize:
- Colors and branding
- Logo images
- Footer text
- Layout and styling

### 6. Troubleshooting

**Emails not sending?**
- Check environment variables are set correctly
- Verify MAIL_USERNAME and MAIL_PASSWORD
- Check spam/junk folders
- Look for error messages in app logs
- Test with simple email first

**Gmail blocking access?**
- Use App Password, not regular password
- Enable "Less secure app access" (not recommended)
- Or switch to SendGrid/Mailgun

**Weekly reports empty?**
- Parents need students linked via access codes
- Students need assessment results in past 7 days
- Check `email_reports_enabled` is True in database

### 7. Production Best Practices

1. **Use a dedicated email service** (SendGrid, Mailgun, SES)
   - Gmail has daily sending limits (500/day)
   - Dedicated services have better deliverability

2. **Set up SPF/DKIM records** for your domain
   - Improves email deliverability
   - Reduces spam flags

3. **Monitor bounce rates and complaints**
   - Use email service analytics
   - Remove invalid addresses

4. **Add unsubscribe link** (already included in template)
   - Required by CAN-SPAM Act
   - Improves user experience

5. **Test before mass sending**
   - Send to yourself first
   - Check all email clients (Gmail, Outlook, iPhone)
   - Verify all data displays correctly
