# 🚀 Production Deployment Checklist

## Before Going Live

### ✅ Email Configuration (Required)

After your next deployment to Render, you MUST add these secret environment variables in the Render dashboard:

1. Go to: https://dashboard.render.com → Your Service → Environment
2. Add these variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `MAIL_USERNAME` | `jakegholland18@gmail.com` | Your Gmail address |
| `MAIL_PASSWORD` | `xpaa uzvz zuvb wmcl` | Gmail App Password from .env |

**Important**: The other email variables (`MAIL_SERVER`, `MAIL_PORT`, etc.) are already configured in `render.yaml` and will deploy automatically.

### 📧 Post-Deployment Email Test

1. Deploy and wait for it to complete
2. Log in to production site as a parent
3. Go to Settings → Email Preferences
4. Click "Send Test Report Now"
5. Verify email arrives in inbox

### ⚠️ Production Limitations (Current Setup)

**Gmail has a 500 emails/day limit.** This is fine for:
- Testing and initial launch
- Up to ~70 parents with weekly reports
- Small-scale operation

**Upgrade to Professional Email Service When:**
- You have 100+ parent accounts
- You want to send more frequent updates
- You need better deliverability and analytics

### 🔄 Optional: Weekly Reports Automation

The weekly reports currently require manual trigger. To automate:

**Option 1: Render Cron Job (Recommended)**
Add to `render.yaml`:
```yaml
  - type: cron
    name: weekly-reports
    env: python
    schedule: "0 9 * * 0"  # Every Sunday at 9 AM UTC
    buildCommand: pip install -r requirements.txt
    startCommand: python send_weekly_reports.py
    envVars:
      - key: FLASK_ENV
        value: production
      - key: OPENAI_API_KEY
        sync: false
      - key: MAIL_USERNAME
        sync: false
      - key: MAIL_PASSWORD
        sync: false
      # ... (same env vars as main service)
```

**Option 2: Manual Admin Route**
Create an admin-only route `/admin/send-weekly-reports` to trigger manually each week.

### 🎯 Future Email Service Upgrades

When you outgrow Gmail, switch to:

**SendGrid** (Recommended)
- Free: 100 emails/day
- Essentials: $15/month for 50,000 emails
- Easy setup, great deliverability
- Sign up: https://sendgrid.com

**Mailgun**
- Free: 5,000 emails/month (first 3 months)
- Then $35/month for 50,000 emails
- Sign up: https://mailgun.com

**To switch**: Just update these 3 env vars in Render:
- `MAIL_SERVER`: smtp.sendgrid.net
- `MAIL_USERNAME`: apikey
- `MAIL_PASSWORD`: (your SendGrid API key)

---

## Ready to Launch? ✨

- [x] Email config added to `render.yaml`
- [ ] Add `MAIL_USERNAME` and `MAIL_PASSWORD` to Render dashboard
- [ ] Deploy to production
- [ ] Test email delivery
- [ ] Monitor email usage (Gmail quota)

**Questions?** Check `EMAIL_SETUP.md` for detailed troubleshooting.
