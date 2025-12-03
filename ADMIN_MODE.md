# Admin Mode - Hidden Administrator Access

## Overview
Admin mode is a hidden feature that allows the owner (jakegholland18@gmail.com) to navigate between any user account freely without subscription restrictions. This is designed for testing, debugging, and making updates across different user perspectives.

## Key Features

### 1. **Automatic Admin Detection**
- The system automatically detects if you're logged in with the owner email
- Works across all three user types: Student, Parent, Teacher
- No password needed - email-based authentication only

### 2. **Subscription Bypass**
- Admin users **completely bypass all subscription checks**
- No trial expiration enforcement when in admin mode
- All features accessible regardless of subscription status
- Perfect for testing features without needing active subscriptions

### 3. **Account Switching**
- Switch to any student, parent, or teacher account instantly
- Maintain admin privileges while viewing as that user type
- Quick access to test features from different user perspectives

## How to Access Admin Mode

### Step 1: Log In as Owner
Log in with your owner email (jakegholland18@gmail.com) using any role:
- Teacher login (recommended)
- Student login
- Parent login

### Step 2: Access Admin Dashboard
Once logged in, you'll see a **🔧 Admin Mode** button in the navbar (highlighted with pink border).

Click it to access `/admin` - the admin dashboard.

### Step 3: Switch Between Accounts
From the admin dashboard, you can:
- View all students, parents, and teachers
- See subscription status (Trial, Paid, Expired) for each user
- Click "Switch →" to instantly switch to that user's account
- Test features as if you were that user

## Admin Dashboard Features

### User Lists
- **Students Section**: All student accounts with grade, plan, and trial status
- **Parents Section**: All parent accounts with plan and billing info
- **Teachers Section**: All teacher accounts with subscription details

### Status Badges
- 🟢 **PAID**: Active subscription
- 🟡 **TRIAL**: Currently in 7-day free trial
- 🔴 **EXPIRED**: Trial ended, no active subscription

### Quick Switching
Click "Switch →" next to any user to instantly:
1. Clear your current session
2. Log in as that user
3. Set `admin_mode` flag in session
4. Redirect to their dashboard

## Admin Mode Indicator

When viewing as a student or parent in admin mode, you'll see:
- **🔧 Admin Mode** button in navbar (pink highlighted)
- Success flash message: "🔧 Admin mode: Viewing as [user type] [name]"
- Quick access back to admin dashboard

## Technical Details

### Code Changes Made

#### `app.py`
1. **`is_admin()` function** (line ~500)
   - Checks if current session user has owner email
   - Works across all three user types
   
2. **`check_subscription_access()` update** (line ~683)
   - First checks `if is_admin()` and returns `True` immediately
   - Bypasses all trial and subscription checks for admin users

3. **Admin Routes** (lines ~973-1070):
   - `/admin` - Admin dashboard listing all users
   - `/admin/switch_to_student/<id>` - Switch to student view
   - `/admin/switch_to_parent/<id>` - Switch to parent view
   - `/admin/switch_to_teacher/<id>` - Switch to teacher view

#### `_navbar.html`
Added admin mode buttons with pink highlighting:
- Shows for owner when logged in as teacher
- Shows when `session.admin_mode` is True (viewing as other user)
- Hidden from all other users

#### `admin_mode.html` (NEW)
Beautiful admin dashboard with:
- Cosmic theme matching site design
- Three-column grid layout
- Scrollable user lists
- Subscription status badges
- Quick switch buttons

### Old Admin System Removed
- Removed password-based admin login (`ADMIN_PASSWORD`)
- Removed old `/admin/dashboard` route
- Removed old `/admin/switch/<mode>` switcher
- Simplified to email-based owner authentication

## Usage Examples

### Testing Trial Expiration Flow
1. Go to `/admin`
2. Find a student with EXPIRED badge
3. Click "Switch →"
4. Navigate to dashboard - should load normally (admin bypass)
5. Test features that would normally be blocked

### Testing Student Features
1. Go to `/admin`
2. Switch to any student account
3. Test AI tutoring, practice missions, subjects
4. No subscription restrictions apply
5. Click "🔧 Admin Mode" to return to admin dashboard

### Testing Parent Dashboard
1. Go to `/admin`
2. Switch to a parent account
3. View student reports and analytics
4. Test time limits and email preferences
5. Return to admin via navbar button

## Security Notes

✅ **Hidden from Regular Users**
- Admin button only appears for owner email
- Regular users never see admin functionality
- No public links or menu items

✅ **Email-Based Authentication**
- No shared passwords
- Automatically detects owner email
- Works across all login types

✅ **Session-Based**
- Admin mode stored in session
- Cleared on logout
- Doesn't persist across browsers

## Limitations

⚠️ **Not for Production User Management**
- This is a development/testing tool
- Don't use for regular administrative tasks
- Use proper parent/teacher roles for actual user management

⚠️ **Database Changes Affect Real Data**
- When viewing as a user, any actions affect real database
- Be careful when testing destructive operations
- Consider using test accounts for risky operations

## Future Enhancements (Optional)

Potential additions if needed:
- [ ] Create test student/parent/teacher accounts from admin dashboard
- [ ] Reset user progress from admin view
- [ ] View system logs and errors
- [ ] Manually adjust subscription status
- [ ] Export analytics data
- [ ] Impersonate mode (view-only, no database changes)

## Quick Reference

| URL | Purpose |
|-----|---------|
| `/admin` | Main admin dashboard |
| `/admin/switch_to_student/<id>` | Switch to student view |
| `/admin/switch_to_parent/<id>` | Switch to parent view |
| `/admin/switch_to_teacher/<id>` | Switch to teacher view |

**Owner Email**: jakegholland18@gmail.com

**Visual Indicator**: 🔧 Admin Mode button (pink border, highlighted)

**Key Function**: `is_admin()` - Returns True if current user is owner
