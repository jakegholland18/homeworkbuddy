# Stripe Payment Integration Setup Guide

## Overview
CozmicLearning uses Stripe to process subscription payments for students, parents, teachers, and homeschool plans. This guide walks you through setting up Stripe from scratch.

---

## Step 1: Create a Stripe Account

1. Go to [https://stripe.com](https://stripe.com)
2. Click "Start now" or "Sign up"
3. Create your account with business email
4. Complete business verification (required for production)

---

## Step 2: Get Your API Keys

### Development (Test Mode)
1. Log into Stripe Dashboard: [https://dashboard.stripe.com](https://dashboard.stripe.com)
2. Make sure you're in **Test Mode** (toggle in top right)
3. Go to **Developers** → **API keys**
4. Copy your keys:
   - **Publishable key**: Starts with `pk_test_...`
   - **Secret key**: Starts with `sk_test_...` (click "Reveal test key")

### Production (Live Mode)
1. Toggle to **Live Mode** in Stripe Dashboard
2. Go to **Developers** → **API keys**
3. Copy your live keys:
   - **Publishable key**: Starts with `pk_live_...`
   - **Secret key**: Starts with `sk_live_...`

---

## Step 3: Create Products and Prices in Stripe

You need to create **16 subscription products** (4 roles × 2 plans × 2 billing cycles).

### Method 1: Via Stripe Dashboard (Recommended for Beginners)

1. Go to **Products** in Stripe Dashboard
2. Click **Add product**
3. For each product below, fill in:
   - **Name**: (see table below)
   - **Description**: Brief plan description
   - **Pricing**: Recurring
   - **Price**: (see table below)
   - **Billing period**: Monthly or Yearly
4. Click **Save product**
5. **Copy the Price ID** (starts with `price_...`) - you'll need this!

### Products to Create:

| Product Name | Price | Billing | Price ID Variable Name |
|-------------|-------|---------|----------------------|
| Student Basic Monthly | $7.99 | Monthly | `STRIPE_STUDENT_BASIC_MONTHLY` |
| Student Basic Yearly | $85.00 | Yearly | `STRIPE_STUDENT_BASIC_YEARLY` |
| Student Premium Monthly | $12.99 | Monthly | `STRIPE_STUDENT_PREMIUM_MONTHLY` |
| Student Premium Yearly | $140.00 | Yearly | `STRIPE_STUDENT_PREMIUM_YEARLY` |
| Parent Basic Monthly | $9.99 | Monthly | `STRIPE_PARENT_BASIC_MONTHLY` |
| Parent Basic Yearly | $75.00 | Yearly | `STRIPE_PARENT_BASIC_YEARLY` |
| Parent Premium Monthly | $15.99 | Monthly | `STRIPE_PARENT_PREMIUM_MONTHLY` |
| Parent Premium Yearly | $160.00 | Yearly | `STRIPE_PARENT_PREMIUM_YEARLY` |
| Teacher Basic Monthly | $15.99 | Monthly | `STRIPE_TEACHER_BASIC_MONTHLY` |
| Teacher Basic Yearly | $170.00 | Yearly | `STRIPE_TEACHER_BASIC_YEARLY` |
| Teacher Premium Monthly | $25.99 | Monthly | `STRIPE_TEACHER_PREMIUM_MONTHLY` |
| Teacher Premium Yearly | $280.00 | Yearly | `STRIPE_TEACHER_PREMIUM_YEARLY` |
| Homeschool Essential Monthly | $19.99 | Monthly | `STRIPE_HOMESCHOOL_ESSENTIAL_MONTHLY` |
| Homeschool Essential Yearly | $215.00 | Yearly | `STRIPE_HOMESCHOOL_ESSENTIAL_YEARLY` |
| Homeschool Complete Monthly | $29.99 | Monthly | `STRIPE_HOMESCHOOL_COMPLETE_MONTHLY` |
| Homeschool Complete Yearly | $320.00 | Yearly | `STRIPE_HOMESCHOOL_COMPLETE_YEARLY` |

### Method 2: Via Stripe CLI (Advanced)

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login to your account
stripe login

# Create products and prices (example for one)
stripe products create --name="Student Basic Monthly" \
  --description="Basic plan for students - 100 questions/month"

stripe prices create --product=prod_XXX \
  --unit-amount=799 \
  --currency=usd \
  --recurring[interval]=month
```

---

## Step 4: Configure Environment Variables

Add these to your `.env` file:

```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_test_XXXXXXXXXXXXXXXXXXXXX
STRIPE_PUBLISHABLE_KEY=pk_test_XXXXXXXXXXXXXXXXXXXXX

# Stripe Price IDs (get these from Step 3)
STRIPE_STUDENT_BASIC_MONTHLY=price_XXXXXXXXXXXXXXXXXXXXX
STRIPE_STUDENT_BASIC_YEARLY=price_XXXXXXXXXXXXXXXXXXXXX
STRIPE_STUDENT_PREMIUM_MONTHLY=price_XXXXXXXXXXXXXXXXXXXXX
STRIPE_STUDENT_PREMIUM_YEARLY=price_XXXXXXXXXXXXXXXXXXXXX
STRIPE_PARENT_BASIC_MONTHLY=price_XXXXXXXXXXXXXXXXXXXXX
STRIPE_PARENT_BASIC_YEARLY=price_XXXXXXXXXXXXXXXXXXXXX
STRIPE_PARENT_PREMIUM_MONTHLY=price_XXXXXXXXXXXXXXXXXXXXX
STRIPE_PARENT_PREMIUM_YEARLY=price_XXXXXXXXXXXXXXXXXXXXX
STRIPE_TEACHER_BASIC_MONTHLY=price_XXXXXXXXXXXXXXXXXXXXX
STRIPE_TEACHER_BASIC_YEARLY=price_XXXXXXXXXXXXXXXXXXXXX
STRIPE_TEACHER_PREMIUM_MONTHLY=price_XXXXXXXXXXXXXXXXXXXXX
STRIPE_TEACHER_PREMIUM_YEARLY=price_XXXXXXXXXXXXXXXXXXXXX
STRIPE_HOMESCHOOL_ESSENTIAL_MONTHLY=price_XXXXXXXXXXXXXXXXXXXXX
STRIPE_HOMESCHOOL_ESSENTIAL_YEARLY=price_XXXXXXXXXXXXXXXXXXXXX
STRIPE_HOMESCHOOL_COMPLETE_MONTHLY=price_XXXXXXXXXXXXXXXXXXXXX
STRIPE_HOMESCHOOL_COMPLETE_YEARLY=price_XXXXXXXXXXXXXXXXXXXXX
```

For **Render.com** deployment, add these in the **Environment** section of your web service.

---

## Step 5: Set Up Webhooks

Webhooks allow Stripe to notify your app when subscriptions are created, updated, or canceled.

### Local Development with Stripe CLI

1. Install Stripe CLI (see Method 2 above)
2. Forward events to your local server:
   ```bash
   stripe listen --forward-to localhost:5000/stripe-webhook
   ```
3. Copy the **webhook signing secret** (starts with `whsec_...`)
4. Add to `.env`:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXXXXXXXXXXXXX
   ```

### Production Webhooks (Render.com)

1. Go to **Developers** → **Webhooks** in Stripe Dashboard
2. Click **Add endpoint**
3. Enter your endpoint URL:
   ```
   https://your-app-name.onrender.com/stripe-webhook
   ```
4. Select events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
5. Click **Add endpoint**
6. Copy the **Signing secret** (starts with `whsec_...`)
7. Add to Render environment variables:
   ```
   STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXXXXXXXXXXXXX
   ```

---

## Step 6: Test the Integration

### Test in Development

1. Start your Flask app:
   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=development
   flask run
   ```

2. In another terminal, start webhook forwarding:
   ```bash
   stripe listen --forward-to localhost:5000/stripe-webhook
   ```

3. Visit your app at `http://localhost:5000`
4. Create a test account (student/parent/teacher)
5. Let trial expire (or manually set `trial_end` in DB to yesterday)
6. Visit dashboard - should redirect to trial_expired page
7. Click a plan button
8. Use Stripe test card: `4242 4242 4242 4242`
   - Any future expiry date
   - Any 3-digit CVC
   - Any ZIP code
9. Complete checkout
10. Verify you're redirected to dashboard with active subscription

### Stripe Test Cards

| Card Number | Description |
|------------|-------------|
| `4242 4242 4242 4242` | Successful payment |
| `4000 0025 0000 3155` | Requires authentication (3D Secure) |
| `4000 0000 0000 9995` | Declined (insufficient funds) |

Full list: [https://stripe.com/docs/testing](https://stripe.com/docs/testing)

---

## Step 7: Database Fields for Stripe Customer IDs (Optional Enhancement)

**Future improvement**: Add `stripe_customer_id` field to Student, Parent, Teacher models to track Stripe customers. This enables:
- Subscription updates without re-entering payment info
- Better webhook handling
- Customer portal access

### Migration (when ready):

```python
# In models.py, add to Student, Parent, Teacher:
stripe_customer_id = db.Column(db.String(100), nullable=True)

# When creating checkout session, save customer ID:
customer = stripe.Customer.create(email=user.email)
user.stripe_customer_id = customer.id
db.session.commit()
```

---

## Troubleshooting

### "Invalid plan configuration" error
- Check that all 16 Price IDs are set in environment variables
- Verify Price IDs match exactly (copy from Stripe Dashboard)
- Ensure no typos in variable names

### Webhooks not firing
- Verify webhook endpoint is publicly accessible (use ngrok for local testing)
- Check webhook signing secret matches
- Look for webhook events in Stripe Dashboard → Developers → Webhooks

### Payment succeeds but subscription not activated
- Check webhook handler logs in terminal
- Verify `handle_checkout_completed()` is being called
- Check database to see if `subscription_active` was updated

### Test mode vs Live mode mismatch
- Use test keys with test price IDs
- Use live keys with live price IDs
- Don't mix test and live!

---

## Security Best Practices

1. **Never commit API keys to git**
   - Use `.env` file (already in `.gitignore`)
   - Use environment variables in production

2. **Verify webhook signatures**
   - Already implemented in `/stripe-webhook` route
   - Prevents fake webhook events

3. **Use HTTPS in production**
   - Render.com provides this automatically
   - Required for live Stripe integration

4. **Restrict API key permissions**
   - Use restricted keys if possible
   - Only grant necessary permissions

---

## Going Live Checklist

- [ ] Complete Stripe business verification
- [ ] Switch to Live API keys
- [ ] Create all 16 products in Live mode
- [ ] Update environment variables with live keys
- [ ] Set up production webhook endpoint
- [ ] Test with real payment method (refund after)
- [ ] Enable Stripe Billing Customer Portal (optional)
- [ ] Set up tax collection (if required)
- [ ] Configure email receipts in Stripe settings
- [ ] Review Stripe Dashboard for first few transactions

---

## Support Resources

- Stripe Documentation: [https://stripe.com/docs](https://stripe.com/docs)
- Stripe API Reference: [https://stripe.com/docs/api](https://stripe.com/docs/api)
- Stripe Support: [https://support.stripe.com](https://support.stripe.com)
- Stripe Status: [https://status.stripe.com](https://status.stripe.com)

---

## Summary

You've now integrated:
✅ 7-day free trials with automatic expiration
✅ Stripe checkout for 16 different subscription plans
✅ Webhook handling for subscription lifecycle
✅ Trial expiration enforcement across all features
✅ Upgrade prompts with direct payment links

Users can now:
- Sign up and try for 7 days free
- Get prompted to upgrade when trial expires
- Pay securely through Stripe Checkout
- Access full features after subscribing
