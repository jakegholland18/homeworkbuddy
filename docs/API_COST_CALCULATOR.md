# CozmicLearning API Cost Calculator & Tracker

## 📊 Current Pricing (Updated Dec 2024)

### OpenAI Models

**GPT-4o-mini** (Primary model for questions, chat):
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens

**GPT-4.1-mini** (Practice sessions):
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens

### Anthropic Models

**Claude 3.5 Sonnet** (PowerGrid, Lesson Plans):
- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens

---

## 💰 Cost Per Feature (Based on Your Code)

### 1. Ask Question (GPT-4o-mini)
**Rate Limit:** 30/hour per user
- Average input: ~500 tokens (prompt + question)
- Average output: ~300 tokens (answer)
- **Cost per question:** ~$0.00025
- **Cost for 30 questions:** ~$0.0075
- **Monthly (900 questions/user):** ~$0.225/user

### 2. Practice Session (GPT-4.1-mini)
**Rate Limit:** 100/hour per user
**Output limit:** 1,800 tokens
- Average input: ~700 tokens (system prompt + context)
- Average output: ~1,500 tokens (10 questions with hints)
- **Cost per session:** ~$0.001
- **Cost for 10 sessions:** ~$0.01
- **Monthly (100 sessions/user):** ~$0.10/user

### 3. PowerGrid Study Guide (Claude 3.5 Sonnet)
**Rate Limit:** 20/hour per user
**Output limit:** 2,500 tokens
- Average input: ~1,200 tokens (prompt + content)
- Average output: ~2,000 tokens (comprehensive guide)
- **Cost per guide:** ~$0.034
- **Cost for 20 guides:** ~$0.68
- **Monthly (60 guides/user):** ~$2.04/user

### 4. Homeschool Lesson Plan (Claude 3.5 Sonnet)
**Rate Limit:** 10/hour per user
**Output limit:** 4,096 tokens
- Average input: ~1,000 tokens (prompt + preferences)
- Average output: ~3,500 tokens (full lesson plan)
- **Cost per lesson:** ~$0.056
- **Cost for 10 lessons:** ~$0.56
- **Monthly (30 lessons/user):** ~$1.68/user

### 5. Teacher's Pet Chat (GPT-4o-mini)
**No rate limit**
- Average input: ~400 tokens
- Average output: ~200 tokens (max 800 configured)
- **Cost per message:** ~$0.00018
- **Cost for 50 messages:** ~$0.009
- **Monthly (150 messages/user):** ~$0.027/user

---

## 🎯 User Scenario Calculations

### Scenario A: Light Student User
**Monthly Usage:**
- 50 ask questions
- 20 practice sessions
- 5 PowerGrid guides
- **Total Cost:** ~$0.34/month

### Scenario B: Active Student User
**Monthly Usage:**
- 200 ask questions
- 50 practice sessions
- 15 PowerGrid guides
- **Total Cost:** ~$0.61/month

### Scenario C: Homeschool Parent (Heavy User)
**Monthly Usage:**
- 100 ask questions
- 30 practice sessions (for kids)
- 20 PowerGrid guides
- 20 lesson plans
- 50 Teacher's Pet messages
- **Total Cost:** ~$2.23/month

### Scenario D: Teacher (Classroom)
**Monthly Usage:**
- 50 lesson plans (Teacher dashboard)
- 100 practice assignments created
- 30 PowerGrid guides
- 100 Teacher's Pet messages
- **Total Cost:** ~$3.85/month

---

## 📈 Projected Costs by User Base

### 10 Users (Friends & Family Alpha)
**Mix:** 5 students + 3 parents + 2 teachers
- Students (light): 5 × $0.34 = $1.70
- Parents (heavy): 3 × $2.23 = $6.69
- Teachers: 2 × $3.85 = $7.70
- **Monthly Total:** ~$16.09
- **Annual:** ~$193

### 100 Users (Beta Launch)
**Mix:** 60 students + 30 parents + 10 teachers
- Students (avg $0.50): 60 × $0.50 = $30
- Parents (avg $2.00): 30 × $2.00 = $60
- Teachers (avg $3.50): 10 × $3.50 = $35
- **Monthly Total:** ~$125
- **Annual:** ~$1,500

### 1,000 Users (Public Launch Year 1)
**Mix:** 600 students + 300 parents + 100 teachers
- Students: 600 × $0.50 = $300
- Parents: 300 × $2.00 = $600
- Teachers: 100 × $3.50 = $350
- **Monthly Total:** ~$1,250
- **Annual:** ~$15,000

---

## 🛡️ Cost Protection (Rate Limits You Already Have)

Your current rate limits **protect** you from runaway costs:

| Feature | Limit | Max Cost/Hour/User |
|---------|-------|-------------------|
| Ask Question | 30/hour | $0.0075 |
| Practice | 100/hour | $0.10 |
| PowerGrid | 20/hour | $0.68 |
| Lesson Plans | 10/hour | $0.56 |

**Worst case scenario:** If 1 user maxes out ALL limits for 1 hour:
- Total: ~$1.35/hour (which is impossible since they can't do all at once)

**Realistic worst case:** Heavy user over 30 days:
- ~$5-10/month per power user

---

## 📊 Revenue vs Cost Analysis

### Student Basic Plan: $7.99/month
- **Average API cost:** $0.50/month
- **Profit margin:** $7.49 (93.7%)
- **Break-even:** 16 users to cover $8/month in API costs

### Student Premium Plan: $12.99/month
- **Average API cost:** $1.00/month (more usage)
- **Profit margin:** $11.99 (92.3%)
- **Break-even:** 11 users

### Homeschool Complete: $29.99/month
- **Average API cost:** $3.00/month (heavy lesson plans)
- **Profit margin:** $26.99 (90%)
- **Break-even:** 4 users

**Safe Operating Ratio:** Aim to keep API costs under 15% of revenue.

---

## 🔍 How to Monitor Real Costs

### 1. OpenAI Dashboard Method
1. Go to [platform.openai.com/usage](https://platform.openai.com/usage)
2. Set date range (last 30 days)
3. View breakdown by:
   - Model (gpt-4o-mini, gpt-4.1-mini)
   - Tokens (input vs output)
   - Cost per day

### 2. Anthropic Dashboard Method
1. Go to [console.anthropic.com/settings/usage](https://console.anthropic.com/settings/usage)
2. View:
   - Total spend this month
   - Tokens by model
   - API calls per day

### 3. Set Up Budget Alerts

**OpenAI:**
```bash
# In OpenAI Dashboard → Settings → Limits
- Set hard limit: $100/month (adjustable)
- Set soft limit alert: $50/month
- Email notifications: enabled
```

**Anthropic:**
```bash
# In Anthropic Console → Settings → Billing
- Set monthly budget: $100
- Alert threshold: 80% ($80)
- Email alerts: enabled
```

### 4. Track Usage in Your App

Add this to your `app.py` to log API usage:

```python
import logging

# After each AI call, log usage
app.logger.info(f"API_USAGE: user={user_id}, feature={feature_name}, "
                f"input_tokens={input_tokens}, output_tokens={output_tokens}, "
                f"estimated_cost=${estimated_cost:.4f}")
```

---

## 💡 Cost Optimization Tips

### 1. Reduce Prompt Size
- ✅ Your prompts are already concise
- ✅ You use grade_depth_instruction() efficiently
- ✅ Character voices are minimal

### 2. Lower max_tokens Where Possible
- **Ask Question:** Could reduce from 800 to 600 (saves 25%)
- **Practice:** 1800 is appropriate for 10 questions
- **PowerGrid:** 2500 is appropriate for study guides
- **Lesson Plans:** 4096 is necessary for comprehensive plans

### 3. Cache Common Responses
For frequently asked questions:
```python
# Example: Cache "What is photosynthesis?" for 1 hour
from functools import lru_cache

@lru_cache(maxsize=100)
def get_common_answer(question_hash):
    # Return cached answer if exists
    pass
```

### 4. Use Cheaper Models When Possible
- ✅ You're already using GPT-4o-mini (cheapest)
- ✅ Claude is only for expensive operations (PowerGrid, Lessons)
- ✅ No unnecessary GPT-4o calls

---

## 🎯 Action Items for Cost Management

### Immediate (Now)
- [x] Rate limiting implemented (DONE!)
- [ ] Set up budget alerts in OpenAI dashboard
- [ ] Set up budget alerts in Anthropic dashboard
- [ ] Create spreadsheet to track monthly costs

### Beta Launch (Week 1-6)
- [ ] Log API usage to file for first 100 users
- [ ] Calculate actual average cost per user
- [ ] Adjust pricing if costs exceed 15% of revenue
- [ ] Consider implementing usage caps per subscription tier

### Public Launch (Month 3+)
- [ ] Implement in-app usage tracking dashboard
- [ ] Show users their API call count (transparency)
- [ ] Create "enterprise" tier for heavy users (unlimited)
- [ ] Consider Redis caching for common questions

---

## 📈 Example: Your First Month Projection

**Friends & Family Alpha (10 users):**
- Student users (5): 5 × $0.50 = $2.50
- Parent users (3): 3 × $2.00 = $6.00
- Teacher users (2): 2 × $3.50 = $7.00
- **Total API Cost:** $15.50/month

**Revenue (if they paid):**
- Students: 5 × $7.99 = $39.95
- Parents: 3 × $9.99 = $29.97
- Teachers: 2 × $15.99 = $31.98
- **Total Revenue:** $101.90

**Profit:** $86.40 (84.8% margin)

---

## 🚨 Warning Signs

Watch out for:
- **Sudden spike** in API costs (>200% increase)
  - Could indicate abuse or bot attacks
  - Check rate limiting is working

- **Cost per user > $10/month**
  - May need to reduce max_tokens
  - Or increase pricing

- **API costs > 20% of revenue**
  - Unsustainable long-term
  - Need pricing adjustment

---

## 📞 Support Resources

- OpenAI Pricing: https://openai.com/api/pricing/
- Anthropic Pricing: https://www.anthropic.com/pricing
- OpenAI Usage Dashboard: https://platform.openai.com/usage
- Anthropic Console: https://console.anthropic.com/

---

**Last Updated:** December 2024
**Next Review:** After 100 users or 3 months
