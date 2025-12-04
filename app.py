# ============================================================
# PYTHON STANDARD LIBRARIES
# ============================================================

import os
import sys
import logging
import traceback
import secrets
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================
# PATHS + DB FILE  (UPDATED FOR PERSISTENT STORAGE)
# ============================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Create persistent DB folder if missing
PERSIST_DIR = os.path.join(BASE_DIR, "persistent_db")
os.makedirs(PERSIST_DIR, exist_ok=True)

# Use persistent SQLite file
DB_PATH = os.path.join(PERSIST_DIR, "cozmiclearning.db")

# Log database path for debugging
print(f"🗄️  Database path: {DB_PATH}")
print(f"📁 Database exists: {os.path.exists(DB_PATH)}")

# ============================================================
# FLASK + SECURITY IMPORTS
# ============================================================

from flask import (
    Flask, render_template, request, redirect, session,
    flash, jsonify, send_file
)
from flask import got_request_exception
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import CSRFProtect
from flask_mail import Mail, Message as EmailMessage
import stripe

# ============================================================
# FLASK APP SETUP
# ============================================================

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "website", "templates"),
    static_url_path="/static",
    static_folder=os.path.join(BASE_DIR, "website", "static"),
)

app.secret_key = "b3c2e773eaa84cd6841a9ffa54c918881b9fab30bb02f7128"

# ------------------------------------------------------------
# Secure session cookie configuration (essentials)
# ------------------------------------------------------------
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

# CSRF protection - enabled globally. We'll exempt JSON POST endpoints below
csrf = CSRFProtect(app)

# ============================================================
# EMAIL CONFIGURATION (FLASK-MAIL)
# ============================================================

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')  # Set in environment
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')  # Set in environment or use app password
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@cozmiclearning.com')

mail = Mail(app)

# ============================================================
# OWNER + ADMIN
# ============================================================

OWNER_EMAIL = "jakegholland18@gmail.com"
ADMIN_PASSWORD = "Cash&Ollie123"

# ============================================================
# STRIPE CONFIGURATION
# ============================================================

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')

# Stripe Price IDs (create these in Stripe Dashboard)
STRIPE_PRICES = {
    # Students
    'student_basic_monthly': os.environ.get('STRIPE_STUDENT_BASIC_MONTHLY'),
    'student_basic_yearly': os.environ.get('STRIPE_STUDENT_BASIC_YEARLY'),
    'student_premium_monthly': os.environ.get('STRIPE_STUDENT_PREMIUM_MONTHLY'),
    'student_premium_yearly': os.environ.get('STRIPE_STUDENT_PREMIUM_YEARLY'),
    
    # Parents
    'parent_basic_monthly': os.environ.get('STRIPE_PARENT_BASIC_MONTHLY'),
    'parent_basic_yearly': os.environ.get('STRIPE_PARENT_BASIC_YEARLY'),
    'parent_premium_monthly': os.environ.get('STRIPE_PARENT_PREMIUM_MONTHLY'),
    'parent_premium_yearly': os.environ.get('STRIPE_PARENT_PREMIUM_YEARLY'),
    
    # Teachers
    'teacher_basic_monthly': os.environ.get('STRIPE_TEACHER_BASIC_MONTHLY'),
    'teacher_basic_yearly': os.environ.get('STRIPE_TEACHER_BASIC_YEARLY'),
    'teacher_premium_monthly': os.environ.get('STRIPE_TEACHER_PREMIUM_MONTHLY'),
    'teacher_premium_yearly': os.environ.get('STRIPE_TEACHER_PREMIUM_YEARLY'),
    
    # Homeschool
    'homeschool_essential_monthly': os.environ.get('STRIPE_HOMESCHOOL_ESSENTIAL_MONTHLY'),
    'homeschool_essential_yearly': os.environ.get('STRIPE_HOMESCHOOL_ESSENTIAL_YEARLY'),
    'homeschool_complete_monthly': os.environ.get('STRIPE_HOMESCHOOL_COMPLETE_MONTHLY'),
    'homeschool_complete_yearly': os.environ.get('STRIPE_HOMESCHOOL_COMPLETE_YEARLY'),
}

# ============================================================
# DATABASE + MODELS
# ============================================================

from models import (
    db,
    Parent,
    Teacher,
    Class,
    Student,
    AssessmentResult,
    AssignedPractice,
    AssignedQuestion,
    LessonPlan,
    Message,
    StudentSubmission,
    QuestionLog,
)
from sqlalchemy import func
import json

# ------------------------------------------------------------
# Simple backup/restore for teachers/classes/students
# ------------------------------------------------------------

BACKUP_PATH = os.path.join(PERSIST_DIR, "classes_backup.json")

def backup_classes_to_json():
    try:
        teachers = Teacher.query.all()
        payload = []
        for t in teachers:
            t_classes = []
            for c in t.classes:
                c_students = []
                for s in c.students:
                    c_students.append({
                        "name": getattr(s, "name", None),
                        "email": getattr(s, "email", None),
                        "grade_level": getattr(c, "grade_level", None),
                    })
                t_classes.append({
                    "class_name": c.class_name,
                    "grade_level": c.grade_level,
                    "id": c.id,
                    "students": c_students,
                })
            payload.append({
                "teacher": {
                    "name": getattr(t, "name", None),
                    "email": getattr(t, "email", None),
                },
                "classes": t_classes,
            })

        with open(BACKUP_PATH, "w") as f:
            json.dump({"data": payload, "saved_at": datetime.utcnow().isoformat()}, f, indent=2)
        print(f"✅ Classes backup saved to {BACKUP_PATH}")
    except Exception as e:
        print(f"⚠️ Failed to backup classes: {e}")


def restore_classes_from_json_if_empty():
    try:
        existing = Class.query.count()
        if existing > 0:
            return
        if not os.path.exists(BACKUP_PATH):
            return
        with open(BACKUP_PATH, "r") as f:
            data = json.load(f)
        items = data.get("data", [])
        restored = 0
        for item in items:
            tinfo = item.get("teacher", {})
            email = (tinfo.get("email") or "").lower()
            if not email:
                continue
            teacher = Teacher.query.filter_by(email=email).first()
            if not teacher:
                # Create minimal teacher account (password not set here)
                teacher = Teacher(name=tinfo.get("name"), email=email, password_hash=generate_password_hash("TempPass123!"))
                db.session.add(teacher)
                db.session.flush()
            for c in item.get("classes", []):
                cls = Class(teacher_id=teacher.id, class_name=c.get("class_name"), grade_level=c.get("grade_level"))
                db.session.add(cls)
                db.session.flush()
                for s in c.get("students", []):
                    stu = Student(class_id=cls.id, name=s.get("name"), email=s.get("email"))
                    db.session.add(stu)
                restored += 1
        db.session.commit()
        if restored:
            print(f"✅ Restored {restored} classes from backup")
    except Exception as e:
        print(f"⚠️ Failed to restore classes: {e}")

# SQLAlchemy config
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# ============================================================
# SEED OWNER SAFELY
# ============================================================

from werkzeug.security import generate_password_hash
from models import Teacher

def seed_owner():
    OWNER_EMAIL = "jakegholland18@gmail.com"
    default_password = "Cash&Ollie123"

    teacher = Teacher.query.filter_by(email=OWNER_EMAIL).first()
    if not teacher:
        t = Teacher(
            name="Jake Holland",
            email=OWNER_EMAIL,
            password_hash=generate_password_hash(default_password)
        )
        db.session.add(t)
        db.session.commit()

with app.app_context():
    db.create_all()  # ensure tables exist
    seed_owner()
    # Attempt restore from backup if DB is empty
    restore_classes_from_json_if_empty()

# ============================================================
# SAFE DB VALIDATION (NO DELETE)
# ============================================================

import sqlite3

def rebuild_database_if_needed():
    """
    Validate schema but DO NOT delete the DB.
    Warn developer if something is missing.
    """

    if not os.path.exists(DB_PATH):
        print("📦 No DB found - creating new persistent database...")
        with app.app_context():
            db.create_all()
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("PRAGMA table_info(students);")
        student_cols = [col[1] for col in cur.fetchall()]
        cur.execute("PRAGMA table_info(parents);")
        parent_cols = [col[1] for col in cur.fetchall()]
        cur.execute("PRAGMA table_info(teachers);")
        teacher_cols = [col[1] for col in cur.fetchall()]

        cur.execute("PRAGMA table_info(assigned_practice);")
        practice_cols = [col[1] for col in cur.fetchall()]

        # Check if student_submissions table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_submissions';")
        submissions_exists = cur.fetchone() is not None
        
        # Check if question_logs table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='question_logs';")
        question_logs_exists = cur.fetchone() is not None
        
        # Define ensure_column helper BEFORE using it
        def ensure_column(table, cols, name, type_sql):
            if name not in cols:
                try:
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {type_sql}")
                    conn.commit()
                    print(f"✅ Added column {table}.{name}")
                except Exception as e:
                    print(f"⚠️ Could not add column {table}.{name}: {e}")
        
        if question_logs_exists:
            # Check for new columns in question_logs
            cur.execute("PRAGMA table_info(question_logs);")
            log_cols = [col[1] for col in cur.fetchall()]
            ensure_column("question_logs", log_cols, "severity", "VARCHAR(20)")
            ensure_column("question_logs", log_cols, "appeal_requested", "BOOLEAN DEFAULT 0")
            ensure_column("question_logs", log_cols, "appeal_reason", "TEXT")
            ensure_column("question_logs", log_cols, "appeal_status", "VARCHAR(20)")
            ensure_column("question_logs", log_cols, "appeal_reviewed_by", "VARCHAR(100)")
            ensure_column("question_logs", log_cols, "appeal_reviewed_at", "DATETIME")
            ensure_column("question_logs", log_cols, "appeal_notes", "TEXT")

        ensure_column("students", student_cols, "plan", "TEXT")
        ensure_column("students", student_cols, "billing", "TEXT")
        ensure_column("students", student_cols, "trial_start", "DATETIME")
        ensure_column("students", student_cols, "trial_end", "DATETIME")
        ensure_column("students", student_cols, "subscription_active", "BOOLEAN")

        ensure_column("parents", parent_cols, "plan", "TEXT")
        ensure_column("parents", parent_cols, "billing", "TEXT")
        ensure_column("parents", parent_cols, "trial_start", "DATETIME")
        ensure_column("parents", parent_cols, "trial_end", "DATETIME")
        ensure_column("parents", parent_cols, "subscription_active", "BOOLEAN")
        ensure_column("parents", parent_cols, "access_code", "TEXT UNIQUE")

        ensure_column("teachers", teacher_cols, "plan", "TEXT")
        ensure_column("teachers", teacher_cols, "billing", "TEXT")
        ensure_column("teachers", teacher_cols, "trial_start", "DATETIME")
        ensure_column("teachers", teacher_cols, "trial_end", "DATETIME")
        ensure_column("teachers", teacher_cols, "subscription_active", "BOOLEAN")

        ensure_column("assigned_practice", practice_cols, "assignment_type", "VARCHAR(20) DEFAULT 'practice'")

        # Create student_submissions table if it doesn't exist
        if not submissions_exists:
            try:
                with app.app_context():
                    db.create_all()
                print("✅ Created student_submissions table")
            except Exception as e:
                print(f"⚠️ Could not create student_submissions table: {e}")
        
        # Create question_logs table if it doesn't exist
        if not question_logs_exists:
            try:
                with app.app_context():
                    db.create_all()
                print("✅ Created question_logs table for content moderation")
            except Exception as e:
                print(f"⚠️ Could not create question_logs table: {e}")

        conn.close()

        warnings = []

        if "parent_id" not in student_cols:
            warnings.append("parent_id missing from students table")

        if "differentiation_mode" not in practice_cols:
            warnings.append("differentiation_mode missing from assigned_practice")

        if "assignment_type" not in practice_cols:
            warnings.append("assignment_type missing from assigned_practice")

        if not submissions_exists:
            warnings.append("student_submissions table missing")

        if warnings:
            print("⚠️ Database schema warning:")
            for w in warnings:
                print("   -", w)
            print("⚠️ No destructive rebuild performed. Apply migrations manually if needed.")
        else:
            print("✅ Database OK - all required columns exist.")

    except Exception as e:
        print("⚠️ DB validation failed:", e)
        print("⚠️ No destructive rebuild performed.")

rebuild_database_if_needed()

# Initialize achievements
try:
    from modules.achievement_helper import initialize_achievements
    with app.app_context():
        initialize_achievements()
    print("✅ Achievements initialized")
except Exception as e:
    print(f"⚠️ Achievement initialization failed: {e}")

# Initialize arcade games
try:
    from modules.arcade_helper import initialize_arcade_games
    with app.app_context():
        initialize_arcade_games()
    print("✅ Arcade games initialized")
except Exception as e:
    print(f"⚠️ Arcade initialization failed: {e}")

# ============================================================
# PASSWORD RESET TOKEN STORE (In-memory for now)
# ============================================================

password_reset_tokens = {}  # {token: {"email": email, "role": role, "expires": datetime}}

def generate_reset_token(email, role):
    """Generate a password reset token valid for 1 hour"""
    token = secrets.token_urlsafe(32)
    password_reset_tokens[token] = {
        "email": email.lower(),
        "role": role,
        "expires": datetime.now() + timedelta(hours=1)
    }
    return token

def verify_reset_token(token):
    """Verify token and return email/role if valid, None otherwise"""
    data = password_reset_tokens.get(token)
    if not data:
        return None
    if datetime.now() > data["expires"]:
        del password_reset_tokens[token]
        return None
    return data

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(level=logging.INFO)


def log_exception(sender, exception, **extra):
    sender.logger.error("Exception during request: %s", traceback.format_exc())


got_request_exception.connect(log_exception, app)

# ------------------------------------------------------------
# SIMPLE INPUT SANITIZATION HELPERS (essentials)
# ------------------------------------------------------------
def safe_text(value: str, max_len: int = 500) -> str:
    if not isinstance(value, str):
        return ""
    v = value.strip()
    if len(v) > max_len:
        v = v[:max_len]
    return v

def safe_email(value: str, max_len: int = 254) -> str:
    v = safe_text(value.lower(), max_len)
    return v

# ============================================================
# JINJA2 FILTERS
# ============================================================

import json

@app.template_filter('fromjson')
def fromjson_filter(value):
    """Parse JSON string to Python object"""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {}
    return value

# ============================================================
# MODULE IMPORTS (AI + SUBJECT HELPERS + PRACTICE)
# ============================================================

sys.path.append(os.path.join(BASE_DIR, "modules"))

from modules.shared_ai import study_buddy_ai  # AI wrapper
from modules.personality_helper import get_all_characters
from modules.content_moderation import moderate_content, get_moderation_summary
from modules import (
    math_helper,
    text_helper,
    question_helper,
    science_helper,
    bible_helper,
    history_helper,
    writing_helper,
    study_helper,
    apologetics_helper,
    investment_helper,
    money_helper,
)
from modules.practice_helper import generate_practice_session
from modules.answer_formatter import parse_into_sections
from modules.teacher_tools import assign_questions, generate_lesson_plan
import string

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def generate_parent_access_code():
    """Generate a unique 6-character alphanumeric access code for parents."""
    while True:
        # Generate uppercase alphanumeric code (no ambiguous chars like O/0, I/1)
        chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')
        code = ''.join(secrets.choice(chars) for _ in range(6))
        
        # Ensure uniqueness
        existing = Parent.query.filter_by(access_code=code).first()
        if not existing:
            return code

# ============================================================
# SUBJECT → FUNCTION MAP (PLANETS)
# ============================================================

subject_map = {
    "num_forge": math_helper.explain_math,
    "atom_sphere": science_helper.explain_science,
    "faith_realm": bible_helper.bible_lesson,
    "chrono_core": history_helper.explain_history,
    "ink_haven": writing_helper.help_write,
    "truth_forge": apologetics_helper.apologetics_answer,
    "stock_star": investment_helper.explain_investing,
    "coin_quest": money_helper.explain_money,
    "terra_nova": question_helper.answer_question,
    "story_verse": text_helper.explain_text,
    "power_grid": None,  # handled separately
}

# Human-friendly subject labels for UI switchers
SUBJECT_LABELS = {
    "chrono_core": "ChronoCore (History)",
    "num_forge": "NumForge (Math)",
    "atom_sphere": "AtomSphere (Science)",
    "story_verse": "StoryVerse (Reading)",
    "ink_haven": "InkHaven (Writing)",
    "faith_realm": "FaithRealm (Bible)",
    "coin_quest": "CoinQuest (Money)",
    "stock_star": "StockStar (Investing)",
    "terra_nova": "TerraNova (General)",
    "power_grid": "PowerGrid (Deep Study)",
    "truth_forge": "TruthForge (Apologetics)",
}

# ============================================================
# HELPERS – TEACHER + OWNER
# ============================================================


def get_current_teacher():
    tid = session.get("teacher_id")
    if not tid:
        return None
    return Teacher.query.get(tid)


def is_owner(teacher: Teacher | None) -> bool:
    return bool(
        teacher and teacher.email and teacher.email.lower() == OWNER_EMAIL.lower()
    )


def is_admin() -> bool:
    """Check if current session user is admin (owner email in any role)"""
    # Check if logged in as teacher/owner
    if session.get("teacher_id"):
        teacher = Teacher.query.get(session["teacher_id"])
        if teacher and teacher.email and teacher.email.lower() == OWNER_EMAIL.lower():
            return True
    
    # Check if logged in as student with owner email
    if session.get("student_id"):
        student = Student.query.get(session["student_id"])
        if student and student.student_email and student.student_email.lower() == OWNER_EMAIL.lower():
            return True
    
    # Check if logged in as parent with owner email
    if session.get("parent_id"):
        parent = Parent.query.get(session["parent_id"])
        if parent and parent.email and parent.email.lower() == OWNER_EMAIL.lower():
            return True
    
    return False


# ============================================================
# USER SESSION DEFAULTS (STUDENT SIDE)
# ============================================================


def init_user():
    defaults = {
        "tokens": 0,
        "xp": 0,
        "level": 1,
        "streak": 1,
        "last_visit": str(datetime.today().date()),
        "inventory": [],
        "character": "everly",
        "usage_minutes": 0,
        "progress": {},
        "conversation": [],
        "deep_study_chat": [],
        # practice mission storage
        "practice": None,
        "practice_step": 0,
        "practice_attempts": 0,
        "practice_progress": [],
        # role flags
        "user_role": None,  # student / parent / teacher / owner
        "student_name": None,
        "student_email": None,
        "parent_name": None,
        "grade": "8",
        # usage tracking for plan limits
        "questions_this_month": 0,
        "month_start": str(datetime.today().replace(day=1).date()),
    }
    for k, v in defaults.items():
        if k not in session:
            session[k] = v
    update_streak()
    check_monthly_reset()


# ============================================================
# DAILY STREAK
# ============================================================


def update_streak():
    today = datetime.today().date()
    last_str = session.get("last_visit")
    if not last_str:
        session["last_visit"] = str(today)
        session["streak"] = 1
        return

    last = datetime.strptime(last_str, "%Y-%m-%d").date()
    if today != last:
        if today - last == timedelta(days=1):
            session["streak"] += 1
        else:
            session["streak"] = 1
        session["last_visit"] = str(today)


def check_monthly_reset():
    """Reset question count if new month has started."""
    month_start = session.get("month_start")
    today = datetime.today().date()
    first_of_month = today.replace(day=1)
    
    if not month_start or datetime.strptime(month_start, "%Y-%m-%d").date() < first_of_month:
        session["questions_this_month"] = 0
        session["month_start"] = str(first_of_month)
        session.modified = True


def check_question_limit():
    """Check if student has exceeded their plan's question limit. Returns (allowed, remaining, limit)."""
    if session.get("user_role") != "student":
        return (True, float('inf'), float('inf'))
    
    student = Student.query.filter_by(student_email=session.get("student_email")).first()
    if not student:
        return (True, float('inf'), float('inf'))
    
    # Premium or trial gets unlimited
    if student.plan == "premium" or not student.subscription_active:
        return (True, float('inf'), float('inf'))
    
    # Basic plan: 100 questions/month
    limit = 100
    used = session.get("questions_this_month", 0)
    remaining = max(0, limit - used)
    allowed = used < limit
    
    return (allowed, remaining, limit)


def increment_question_count():
    """Increment question counter for the current month."""
    if session.get("user_role") == "student":
        session["questions_this_month"] = session.get("questions_this_month", 0) + 1
        session.modified = True


def get_parent_plan_limits(parent):
    """Get plan limits for parent/homeschool accounts. Returns (student_limit, lesson_plans_limit, assignments_limit, has_teacher_features)."""
    if not parent or not parent.plan:
        return (3, 0, 0, False)  # Default free limits
    
    plan = parent.plan.lower()
    
    # Homeschool plans (hybrid parent + teacher features)
    if plan == "homeschool_essential":
        return (5, 50, 100, True)  # 5 students, 50 lesson plans/mo, 100 assignments/mo, teacher features enabled
    elif plan == "homeschool_complete":
        return (float('inf'), float('inf'), float('inf'), True)  # Unlimited everything, teacher features enabled
    
    # Regular parent plans (no teacher features)
    elif plan == "basic":
        return (3, 0, 0, False)  # 3 students, no teacher tools
    elif plan == "premium":
        return (float('inf'), 0, 0, False)  # Unlimited students, no teacher tools
    
    # Default for unknown plans
    return (3, 0, 0, False)


def check_parent_student_limit(parent):
    """Check if parent can add more students. Returns (allowed, current_count, limit)."""
    if not parent:
        return (False, 0, 0)
    
    student_limit, _, _, _ = get_parent_plan_limits(parent)
    current_count = len(parent.students) if parent.students else 0
    allowed = current_count < student_limit
    
    return (allowed, current_count, student_limit)


# ============================================================
# SUBSCRIPTION STATUS HELPERS
# ============================================================

def is_trial_expired(user):
    """
    Check if user's trial period has ended.
    Returns True if trial expired, False otherwise.
    """
    if not user:
        return True
    
    # If they have an active paid subscription, trial doesn't matter
    if user.subscription_active:
        return False
    
    # If no trial_end set, consider expired
    if not user.trial_end:
        return True
    
    # Check if current time is past trial end
    now = datetime.utcnow()
    return now > user.trial_end


def check_subscription_access(user_role):
    """
    Middleware-style check for subscription access.
    Redirects to trial_expired page if subscription is inactive and trial is over.
    Returns True if access allowed, redirects if not.
    ADMIN USERS BYPASS ALL SUBSCRIPTION CHECKS.
    """
    # Admin mode: bypass all subscription checks
    if session.get("admin_authenticated") or session.get("bypass_auth") or is_admin():
        return True
    
    user = None
    
    if user_role == "student":
        student_id = session.get("student_id")
        if student_id:
            user = Student.query.get(student_id)
    elif user_role == "parent":
        parent_id = session.get("parent_id")
        if parent_id:
            user = Parent.query.get(parent_id)
    elif user_role == "teacher":
        teacher_id = session.get("teacher_id")
        if teacher_id:
            user = Teacher.query.get(teacher_id)
    
    if not user:
        flash("Please log in to continue.", "error")
        return redirect("/choose_login_role")
    
    # Check if trial expired and no active subscription
    if is_trial_expired(user):
        return redirect(f"/trial_expired?role={user_role}")
    
    return True  # Access allowed


def get_days_remaining_in_trial(user):
    """Returns number of days remaining in trial, or 0 if expired/no trial."""
    if not user or not user.trial_end:
        return 0
    
    if user.subscription_active:
        return 0  # Paid subscription active
    
    now = datetime.utcnow()
    if now > user.trial_end:
        return 0  # Expired
    
    delta = user.trial_end - now
    return max(0, delta.days)


def get_stripe_price_id(role, plan, billing):
    """
    Get Stripe Price ID based on role, plan tier, and billing cycle.
    role: 'student', 'parent', 'teacher', 'homeschool'
    plan: 'basic', 'premium', 'essential', 'complete'
    billing: 'monthly', 'yearly'
    """
    key = f"{role}_{plan}_{billing}"
    return STRIPE_PRICES.get(key)


# ============================================================
# XP SYSTEM
# ============================================================


def add_xp(amount: int):
    session["xp"] += amount
    xp_needed = session["level"] * 100
    
    # Log level up activity
    if session["xp"] >= xp_needed:
        session["xp"] -= xp_needed
        session["level"] += 1
        flash(f"LEVEL UP! You are now Level {session['level']}!", "info")
        
        # Log level up event
        student_id = session.get("student_id")
        if student_id:
            try:
                from modules.achievement_helper import log_activity
                log_activity(
                    student_id=student_id,
                    activity_type="level_up",
                    description=f"Leveled up to Level {session['level']}!",
                    xp_earned=0
                )
            except Exception as e:
                print(f"Failed to log level up activity: {e}")


# ============================================================
# ANSWER FLEX – USED BY PRACTICE (MC + NUMERIC-friendly)
# ============================================================


def _normalize_numeric_token(text: str) -> str:
    t = text.lower().strip()
    for word in ["percent", "perc", "per cent", "dollars", "dollar", "usd"]:
        t = t.replace(word, "")
    t = t.replace(",", "")
    for ch in ["%", "$"]:
        t = t.replace(ch, "")
    return t.strip()


def _try_float(val: str):
    try:
        return float(val)
    except Exception:
        return None


def answers_match(user_raw: str, expected_raw: str) -> bool:
    if user_raw is None or expected_raw is None:
        return False

    u_norm = user_raw.strip().lower()
    e_norm = expected_raw.strip().lower()

    if u_norm == e_norm and u_norm != "":
        return True

    u_num_str = _normalize_numeric_token(user_raw)
    e_num_str = _normalize_numeric_token(expected_raw)

    if u_num_str and e_num_str and u_num_str == e_num_str:
        return True

    u_num = _try_float(u_num_str)
    e_num = _try_float(e_num_str)
    if u_num is not None and e_num is not None:
        if abs(u_num - e_num) < 1e-6:
            return True

    return False


# ============================================================
# RECALC ABILITY + AVERAGE (DB-BASED, TEACHER SCORES ONLY)
# ============================================================


def recompute_student_ability(student: Student):
    if not student:
        return

    results = (
        AssessmentResult.query.filter_by(student_id=student.id)
        .order_by(AssessmentResult.created_at.desc())
        .limit(10)
        .all()
    )

    if not results:
        student.ability_level = "on_level"
        student.average_score = 0.0
    else:
        avg = sum((r.score_percent or 0.0) for r in results) / len(results)
        student.average_score = avg

        if avg >= 85:
            tier = "advanced"
        elif avg < 60:
            tier = "struggling"
        else:
            tier = "on_level"

        student.ability_level = tier

    db.session.commit()


# ============================================================
# CORE ROUTES – LANDING + SUBJECTS
# ============================================================

@app.route("/")
def home():
    init_user()
    return render_template("home.html")


@app.route("/subjects")
def subjects():
    init_user()
    planets = [
        ("chrono_core", "chrono_core.png", "ChronoCore", "History"),
        ("num_forge", "num_forge.png", "NumForge", "Math"),
        ("atom_sphere", "atom_sphere.png", "AtomSphere", "Science"),
        ("story_verse", "story_verse.png", "StoryVerse", "Reading"),
        ("ink_haven", "ink_haven.png", "InkHaven", "Writing"),
        ("faith_realm", "faith_realm.png", "FaithRealm", "Bible"),
        ("coin_quest", "coin_quest.png", "CoinQuest", "Money"),
        ("stock_star", "stock_star.png", "StockStar", "Investing"),
        ("terra_nova", "terra_nova.png", "TerraNova", "General Knowledge"),
        ("power_grid", "power_grid.png", "PowerGrid", "Deep Study"),
        ("truth_forge", "truth_forge.png", "TruthForge", "Apologetics"),
    ]
    return render_template(
        "subjects.html",
        planets=planets,
        character=session["character"],
    )


# ============================================================
# ARCADE MODE - LEARNING GAMES
# ============================================================

@app.route("/arcade")
def arcade_hub():
    """Main arcade hub showing all available games"""
    init_user()
    
    from modules.arcade_helper import ARCADE_GAMES, get_student_stats
    
    student_id = session.get("student_id")
    grade = session.get("grade", "5")
    
    # Get student's arcade stats
    stats = None
    if student_id:
        stats = get_student_stats(student_id)
    
    # Group games by subject
    games_by_subject = {}
    for game in ARCADE_GAMES:
        subject = game["subject"]
        if subject not in games_by_subject:
            games_by_subject[subject] = []
        games_by_subject[subject].append(game)
    
    return render_template(
        "arcade_hub.html",
        games_by_subject=games_by_subject,
        all_games=ARCADE_GAMES,
        stats=stats,
        grade=grade,
        character=session["character"]
    )


@app.route("/arcade/game/<game_key>")
def arcade_game(game_key):
    """Load a specific game"""
    init_user()
    
    from modules.arcade_helper import ARCADE_GAMES, get_student_stats, get_leaderboard
    
    # Find game info
    game_info = next((g for g in ARCADE_GAMES if g["game_key"] == game_key), None)
    if not game_info:
        flash("Game not found!", "error")
        return redirect("/arcade")
    
    student_id = session.get("student_id")
    grade = session.get("grade", "5")
    
    # Get student's stats for this game
    stats = None
    if student_id:
        stats = get_student_stats(student_id, game_key)
    
    # Get leaderboard
    leaderboard = get_leaderboard(game_key, grade, limit=10)
    
    return render_template(
        "arcade_game.html",
        game=game_info,
        stats=stats,
        leaderboard=leaderboard,
        grade=grade,
        character=session["character"]
    )


@app.route("/arcade/play/<game_key>", methods=["GET", "POST"])
def arcade_play(game_key):
    """Generate and play a game - with optional grade selection"""
    init_user()
    
    from modules.arcade_helper import (
        generate_speed_math,
        generate_number_detective,
        generate_fraction_frenzy,
        generate_equation_race,
        generate_element_match,
        generate_vocab_builder,
        generate_spelling_sprint,
        generate_grammar_quest,
        generate_science_quiz,
        generate_history_timeline,
        generate_geography_dash,
        ARCADE_GAMES
    )
    
    game_info = next((g for g in ARCADE_GAMES if g["game_key"] == game_key), None)
    if not game_info:
        flash("Game not found!", "error")
        return redirect("/arcade")
    
    # Check if grade was provided in URL (from grade selection screen)
    selected_grade = request.args.get("grade")
    
    # If no grade selected, show grade selection screen
    if not selected_grade:
        return render_template(
            "arcade_grade_select.html",
            game=game_info,
            character=session.get("character", "everly")
        )
    
    # Use selected grade instead of session grade
    grade = selected_grade
    
    # Map each game to its specific generator
    game_generators = {
        "speed_math": generate_speed_math,
        "number_detective": generate_number_detective,
        "fraction_frenzy": generate_fraction_frenzy,
        "equation_race": generate_equation_race,
        "element_match": generate_element_match,
        "lab_quiz_rush": generate_science_quiz,
        "planet_explorer": generate_science_quiz,
        "vocab_builder": generate_vocab_builder,
        "spelling_sprint": generate_spelling_sprint,
        "grammar_quest": generate_grammar_quest,
        "history_timeline": generate_history_timeline,
        "geography_dash": generate_geography_dash,
    }
    
    # Get the appropriate generator for this game
    generator = game_generators.get(game_key, generate_speed_math)
    questions = generator(grade)
    
    # Store questions in session along with selected grade
    session["current_game"] = {
        "game_key": game_key,
        "questions": questions,
        "current_index": 0,
        "correct": 0,
        "selected_grade": grade,
        "start_time": datetime.utcnow().isoformat()
    }
    session.modified = True
    
    return render_template(
        "arcade_play.html",
        game=game_info,
        questions=questions,
        grade=grade,
        character=session.get("character", "everly")
    )


@app.route("/arcade/submit", methods=["POST"])
@csrf.exempt
def arcade_submit():
    """Submit game results"""
    init_user()
    
    from modules.arcade_helper import save_game_session
    from modules.achievement_helper import log_activity
    
    data = request.get_json()
    game_key = data.get("game_key")
    score = data.get("score", 0)
    correct = data.get("correct", 0)
    total = data.get("total", 0)
    time_seconds = data.get("time_seconds", 0)
    
    student_id = session.get("student_id")
    
    # Get selected grade from current game session, fallback to student's grade
    current_game = session.get("current_game", {})
    grade = current_game.get("selected_grade") or session.get("grade", "5")
    
    if not student_id:
        return jsonify({"error": "Not logged in"}), 401
    
    # Save game session and get results
    results = save_game_session(student_id, game_key, grade, score, time_seconds, correct, total)
    
    # Add XP and tokens to session
    session["xp"] = session.get("xp", 0) + results["xp_earned"]
    session["tokens"] = session.get("tokens", 0) + results["tokens_earned"]
    
    # Check for level up
    xp_needed = session["level"] * 100
    if session["xp"] >= xp_needed:
        session["xp"] -= xp_needed
        session["level"] += 1
        results["level_up"] = True
        results["new_level"] = session["level"]
    
    session.modified = True
    
    # Log activity
    log_activity(
        student_id=student_id,
        activity_type="arcade_game_completed",
        subject=game_key,
        description=f"Completed arcade game with {correct}/{total} correct",
        xp_earned=results["xp_earned"]
    )
    
    return jsonify(results)


# ------------------------------------------------------------
# SUBJECT PREVIEW (Modal fragment) - Six-section with bullets
# ------------------------------------------------------------
@app.route("/subject-preview")
def subject_preview():
    init_user()

    subject = request.args.get("subject", "terra_nova")
    grade = session.get("grade", "8")
    character = session.get("character", "everly")

    # PowerGrid handled separately; return brief guidance
    if subject == "power_grid":
        preview_text = (
            "SECTION 1 - OVERVIEW\nPowerGrid is your deep study hub with plan → research → draft → review.\n\n"
            "SECTION 2 - KEY FACTS\n• Plan tasks clearly.\n• Keep sources organized.\n• Iterate drafts.\n\n"
            "SECTION 3 - CHRISTIAN VIEW\nWe value truth, diligence, and wisdom in learning.\n\n"
            "SECTION 4 - AGREEMENT\n• Careful reasoning matters.\n• Evidence strengthens claims.\n\n"
            "SECTION 5 - DIFFERENCE\n• Worldviews shape conclusions.\n\n"
            "SECTION 6 - PRACTICE\n• Build a study plan with 3 steps."
        )
    else:
        func = subject_map.get(subject)
        if not func:
            return "<p>Unknown subject.</p>"

        # Tailored preview prompts per subject for product feel
        preview_prompts = {
            "num_forge": "SECTION 1 - OVERVIEW\nExplain what the Mastery Ladder in math covers.\nSECTION 2 - KEY FACTS\n• Core skills\n• Typical mistakes\n• Tips\nSECTION 3 - CHRISTIAN VIEW\nPurpose, diligence, truth.\nSECTION 4 - AGREEMENT\n• Math consistency matters\nSECTION 5 - DIFFERENCE\n• Approaches to learning\nSECTION 6 - PRACTICE\n• Solve: 3 mixed problems (fractions, percents, algebra).",
            "atom_sphere": "SECTION 1 - OVERVIEW\nExperiment Sim: hypothesis → variables → result.\nSECTION 2 - KEY FACTS\n• Variables\n• Controls\n• Data\nSECTION 3 - CHRISTIAN VIEW\nCreation care, wonder, order.\nSECTION 4 - AGREEMENT\n• Evidence matters\nSECTION 5 - DIFFERENCE\n• Interpretations vary\nSECTION 6 - PRACTICE\n• Design a simple experiment.",
            "ink_haven": "SECTION 1 - OVERVIEW\nRevision Coach: thesis → body → conclusion.\nSECTION 2 - KEY FACTS\n• Thesis clarity\n• Cohesion\n• Tone\nSECTION 3 - CHRISTIAN VIEW\nSpeak truth with grace.\nSECTION 4 - AGREEMENT\n• Clear writing helps\nSECTION 5 - DIFFERENCE\n• Styles vary\nSECTION 6 - PRACTICE\n• Improve a sample paragraph.",
            "chrono_core": "SECTION 1 - OVERVIEW\nTimeline Builder: eras and causes.\nSECTION 2 - KEY FACTS\n• Primary vs secondary sources\n• Cause-effect\n• Context\nSECTION 3 - CHRISTIAN VIEW\nProvidence and responsibility.\nSECTION 4 - AGREEMENT\n• Sources matter\nSECTION 5 - DIFFERENCE\n• Interpretations differ\nSECTION 6 - PRACTICE\n• Place 3 events on a timeline.",
            "story_verse": "SECTION 1 - OVERVIEW\nReading Lab: theme, plot, inference.\nSECTION 2 - KEY FACTS\n• Theme\n• Characters\n• Setting\nSECTION 3 - CHRISTIAN VIEW\nTruth, beauty, goodness.\nSECTION 4 - AGREEMENT\n• Careful reading\nSECTION 5 - DIFFERENCE\n• Interpretations\nSECTION 6 - PRACTICE\n• Identify theme from a short passage.",
            "truth_forge": "SECTION 1 - OVERVIEW\nWorldview Compare: claim, reasons, evidence.\nSECTION 2 - KEY FACTS\n• Claims\n• Logic\n• Evidence\nSECTION 3 - CHRISTIAN VIEW\nFaith seeks understanding.\nSECTION 4 - AGREEMENT\n• Reasoning matters\nSECTION 5 - DIFFERENCE\n• Worldview contrasts\nSECTION 6 - PRACTICE\n• Analyze a claim with two reasons.",
            "faith_realm": "SECTION 1 - OVERVIEW\nPassage Deep Dive: context and application.\nSECTION 2 - KEY FACTS\n• Context\n• Cross-references\n• Application\nSECTION 3 - CHRISTIAN VIEW\nScripture and wisdom.\nSECTION 4 - AGREEMENT\n• Seek understanding\nSECTION 5 - DIFFERENCE\n• Denominational views\nSECTION 6 - PRACTICE\n• Summarize a short passage.",
            "coin_quest": "SECTION 1 - OVERVIEW\nBudget Lab: earn, save, spend, give.\nSECTION 2 - KEY FACTS\n• Needs vs wants\n• Percent allocations\n• Tracking\nSECTION 3 - CHRISTIAN VIEW\nStewardship and generosity.\nSECTION 4 - AGREEMENT\n• Plan wisely\nSECTION 5 - DIFFERENCE\n• Budget styles\nSECTION 6 - PRACTICE\n• Build a 100-dollar budget.",
            "stock_star": "SECTION 1 - OVERVIEW\nROI Simulator: risk vs return.\nSECTION 2 - KEY FACTS\n• Diversification\n• Time horizon\n• Compounding\nSECTION 3 - CHRISTIAN VIEW\nWisdom and prudence.\nSECTION 4 - AGREEMENT\n• Risk management\nSECTION 5 - DIFFERENCE\n• Strategies\nSECTION 6 - PRACTICE\n• Compare two investments.",
            "terra_nova": "SECTION 1 - OVERVIEW\nGeneral Knowledge: curiosity missions.\nSECTION 2 - KEY FACTS\n• Inquiry\n• Evidence\n• Synthesis\nSECTION 3 - CHRISTIAN VIEW\nSeek truth with humility.\nSECTION 4 - AGREEMENT\n• Careful thinking\nSECTION 5 - DIFFERENCE\n• Perspectives\nSECTION 6 - PRACTICE\n• Draft three curious questions.",
        }

        question = preview_prompts.get(subject, "Give a concise overview and sample practice for this subject.")
        result = func(question, grade, character)
        preview_text = result.get("raw_text") if isinstance(result, dict) else str(result)

    sections = parse_into_sections(preview_text)

    def render_list(items):
        if not items:
            return "<p></p>"
        return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"

    html = (
        f"<div>"
        f"<h3>Section 1 - Overview</h3><p>{sections.get('overview','')}</p>"
        f"<h3>Section 2 - Key Facts</h3>{render_list(sections.get('key_facts',[]))}"
        f"<h3>Section 3 - Christian View</h3><p>{sections.get('christian_view','')}</p>"
        f"<h3>Section 4 - Agreement</h3>{render_list(sections.get('agreement',[]))}"
        f"<h3>Section 5 - Difference</h3>{render_list(sections.get('difference',[]))}"
        f"<h3>Section 6 - Practice</h3>{render_list(sections.get('practice',[]))}"
        f"</div>"
    )

    return html


# ============================================================
# AUTH PORTAL + ROLE SELECTION
# ============================================================

@app.route("/auth")
def auth_portal():
    init_user()
    return render_template("auth_portal.html")


@app.route("/choose_login_role")
def choose_login_role():
    init_user()
    return render_template("choose_login_role.html")


@app.route("/plans")
def plans():
    init_user()
    return render_template("plans.html")


@app.route("/trial_expired")
@csrf.exempt
def trial_expired():
    """Show upgrade page when trial has expired - no subscription check needed."""
    # Don't call init_user() or check subscription - this is the upgrade page
    role = request.args.get("role", "student")
    return render_template("trial_expired.html", role=role)


@app.route("/secret_admin_login", methods=["GET", "POST"])
def secret_admin_login():
    """Hidden admin login - accessed via secret button on landing page"""
    if request.method == "POST":
        admin_id = request.form.get("admin_id", "").strip()
        password = request.form.get("password", "").strip()
        
        # Simple check: ID = "admin" and password matches
        if admin_id.lower() == "admin" and password == ADMIN_PASSWORD:
            session["admin_authenticated"] = True
            session["admin_mode"] = "portal"  # Start at portal selection
            flash("🔧 Admin access granted. Welcome!", "success")
            return redirect("/admin_portal")
        else:
            flash("Invalid admin credentials.", "error")
    
    return render_template("secret_admin_login.html")


@app.route("/admin_portal")
def admin_portal():
    """Main admin portal - select Student, Parent, Teacher, or Homeschool mode"""
    if not session.get("admin_authenticated"):
        flash("Admin authentication required.", "error")
        return redirect("/secret_admin_login")
    
    # Show portal with 4 mode options
    return render_template("admin_portal.html")


@app.route("/admin_mode/<mode>")
def admin_set_mode(mode):
    """Set admin mode and redirect to appropriate view"""
    if not session.get("admin_authenticated"):
        flash("Admin authentication required.", "error")
        return redirect("/secret_admin_login")
    
    valid_modes = ["student", "parent", "teacher", "homeschool"]
    if mode not in valid_modes:
        flash("Invalid mode.", "error")
        return redirect("/admin_portal")
    
    # Clear any existing user sessions
    session.pop("student_id", None)
    session.pop("parent_id", None)
    session.pop("teacher_id", None)
    
    # Set admin mode and bypass flag - no user required!
    session["admin_mode"] = mode
    session["bypass_auth"] = True  # Flag to bypass all auth checks
    session["is_owner"] = True  # Give owner privileges
    session.modified = True  # Force session to save
    
    # Set appropriate redirect based on mode
    if mode == "student":
        flash(f"🔧 Admin mode: Student View (Full Access)", "success")
        return redirect("/dashboard")  # Go to student dashboard
    
    elif mode == "parent":
        flash(f"🔧 Admin mode: Parent View (Full Access)", "success")
        return redirect("/parent_dashboard")
    
    elif mode == "teacher":
        flash(f"🔧 Admin mode: Teacher View (Full Access)", "success")
        return redirect("/teacher/dashboard")
    
    elif mode == "homeschool":
        session["homeschool_mode"] = True
        flash(f"🔧 Admin mode: Homeschool View (Full Access)", "success")
        return redirect("/homeschool/dashboard")
    
    return redirect("/admin_portal")


@app.route("/admin_logout")
def admin_logout():
    """Logout from admin mode"""
    session.clear()
    flash("Admin logged out.", "info")
    return redirect("/")


@app.route("/admin/switch_to_student/<int:student_id>")
def admin_switch_to_student(student_id):
    """Admin: switch to student view"""
    if not is_admin():
        flash("Access denied.", "error")
        return redirect("/")
    
    student = Student.query.get(student_id)
    if not student:
        flash("Student not found.", "error")
        return redirect("/admin")
    
    # Clear session and log in as this student
    session.clear()
    session["student_id"] = student.id
    session["admin_mode"] = True
    init_user()
    
    flash(f"🔧 Admin mode: Viewing as student {student.student_name}", "success")
    return redirect("/dashboard")


@app.route("/admin/switch_to_parent/<int:parent_id>")
def admin_switch_to_parent(parent_id):
    """Admin: switch to parent view"""
    if not is_admin():
        flash("Access denied.", "error")
        return redirect("/")
    
    parent = Parent.query.get(parent_id)
    if not parent:
        flash("Parent not found.", "error")
        return redirect("/admin")
    
    # Clear session and log in as this parent
    session.clear()
    session["parent_id"] = parent.id
    session["admin_mode"] = True
    
    flash(f"🔧 Admin mode: Viewing as parent {parent.name}", "success")
    return redirect("/parent_dashboard")


@app.route("/admin/switch_to_teacher/<int:teacher_id>")
def admin_switch_to_teacher(teacher_id):
    """Admin: switch to teacher view"""
    if not is_admin():
        flash("Access denied.", "error")
        return redirect("/")
    
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        flash("Teacher not found.", "error")
        return redirect("/admin")
    
    # Clear session and log in as this teacher
    session.clear()
    session["teacher_id"] = teacher.id
    session["admin_mode"] = True
    
    flash(f"🔧 Admin mode: Viewing as teacher {teacher.name}", "success")
    return redirect("/teacher/dashboard")


# ============================================================
# ADMIN: CONTENT MODERATION DASHBOARD
# ============================================================

@app.route("/admin/moderation")
def admin_moderation():
    """Admin dashboard for reviewing flagged content and student questions"""
    if not is_admin() and not is_owner():
        flash("Access denied.", "error")
        return redirect("/")
    
    # Get filter parameters
    filter_type = request.args.get("filter", "all")
    student_filter = request.args.get("student_id", "")
    
    # Build query
    query = QuestionLog.query
    
    if filter_type == "flagged":
        query = query.filter_by(flagged=True)
    elif filter_type == "blocked":
        query = query.filter_by(allowed=False)
    elif filter_type == "pending":
        query = query.filter_by(flagged=True, reviewed=False)
    
    if student_filter:
        try:
            query = query.filter_by(student_id=int(student_filter))
        except ValueError:
            pass
    
    # Get logs ordered by most recent
    logs = query.order_by(QuestionLog.created_at.desc()).limit(500).all()
    
    # Calculate stats
    total_logs = QuestionLog.query.count()
    flagged_count = QuestionLog.query.filter_by(flagged=True).count()
    pending_review = QuestionLog.query.filter_by(flagged=True, reviewed=False).count()
    reviewed_count = QuestionLog.query.filter_by(reviewed=True).count()
    
    return render_template(
        "admin_moderation.html",
        logs=logs,
        total_logs=total_logs,
        flagged_count=flagged_count,
        pending_review=pending_review,
        reviewed_count=reviewed_count,
        filter_type=filter_type,
        student_filter=student_filter
    )


@app.route("/admin/moderation/<int:log_id>")
def admin_moderation_detail(log_id):
    """Get detailed information about a specific question log"""
    if not is_admin() and not is_owner():
        return jsonify({"error": "Access denied"}), 403
    
    log = QuestionLog.query.get_or_404(log_id)
    
    return jsonify({
        "id": log.id,
        "student_id": log.student_id,
        "student_name": log.student.student_name if log.student else "Unknown",
        "question_text": log.question_text,
        "sanitized_text": log.sanitized_text,
        "subject": log.subject,
        "context": log.context,
        "grade_level": log.grade_level,
        "ai_response": log.ai_response,
        "flagged": log.flagged,
        "allowed": log.allowed,
        "moderation_reason": log.moderation_reason,
        "reviewed": log.reviewed,
        "reviewed_by": log.reviewed_by,
        "admin_notes": log.admin_notes,
        "parent_notified": log.parent_notified,
        "created_at": log.created_at.isoformat()
    })


@app.route("/admin/moderation/<int:log_id>/review", methods=["POST"])
def admin_moderation_review(log_id):
    """Mark a question log as reviewed with admin notes"""
    if not is_admin() and not is_owner():
        flash("Access denied.", "error")
        return redirect("/")
    
    log = QuestionLog.query.get_or_404(log_id)
    
    log.reviewed = True
    log.reviewed_by = session.get("admin_email", "admin")
    log.reviewed_at = datetime.utcnow()
    log.admin_notes = request.form.get("notes", "")
    
    db.session.commit()
    
    flash("Question log marked as reviewed.", "success")
    return redirect("/admin/moderation")


@app.route("/admin/moderation/<int:log_id>/notify", methods=["POST"])
def admin_moderation_notify(log_id):
    """Send notification email to parent about flagged content"""
    if not is_admin() and not is_owner():
        return jsonify({"error": "Access denied"}), 403
    
    log = QuestionLog.query.get_or_404(log_id)
    student = log.student
    
    if not student:
        return jsonify({"error": "Student not found"}), 404
    
    # Find parent
    parent = Parent.query.get(student.parent_id) if student.parent_id else None
    
    if not parent:
        return jsonify({"error": "No parent associated with this student"}), 404
    
    # Send email notification
    try:
        msg = EmailMessage(
            subject=f"CozmicLearning: Content Alert for {student.student_name}",
            sender=app.config["MAIL_DEFAULT_SENDER"],
            recipients=[parent.email]
        )
        
        msg.body = f"""
Dear {parent.email},

This is an automated notification from CozmicLearning's content moderation system.

A question submitted by your student {student.student_name} was flagged for review:

Question: "{log.question_text[:200]}"
Date: {log.created_at.strftime('%B %d, %Y at %I:%M %p')}
Reason: {log.moderation_reason or 'Policy violation'}

Our AI system automatically monitors all student interactions to ensure appropriate educational content. This question was flagged and blocked from being processed.

If you have any concerns or questions, please don't hesitate to contact us.

Thank you for helping us maintain a safe learning environment!

Best regards,
The CozmicLearning Team
"""
        
        mail.send(msg)
        
        # Mark as notified
        log.parent_notified = True
        log.parent_notified_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({"message": "Parent notification sent successfully!"})
        
    except Exception as e:
        app.logger.error(f"Failed to send parent notification: {e}")
        return jsonify({"error": "Failed to send email"}), 500


@app.route("/admin/moderation/stats")
def admin_moderation_stats():
    """Statistics and reporting dashboard for moderation"""
    if not is_admin() and not is_owner():
        flash("Access denied.", "error")
        return redirect("/")
    
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Get time period filter
    period = request.args.get("period", "30")
    
    if period == "all":
        start_date = datetime(2020, 1, 1)
    else:
        days = int(period)
        start_date = datetime.utcnow() - timedelta(days=days)
    
    # Calculate stats
    total_questions = QuestionLog.query.filter(QuestionLog.created_at >= start_date).count()
    flagged_questions = QuestionLog.query.filter(
        QuestionLog.created_at >= start_date,
        QuestionLog.flagged == True
    ).count()
    blocked_questions = QuestionLog.query.filter(
        QuestionLog.created_at >= start_date,
        QuestionLog.allowed == False
    ).count()
    parent_notifications = QuestionLog.query.filter(
        QuestionLog.created_at >= start_date,
        QuestionLog.parent_notified == True
    ).count()
    
    # Severity breakdown
    high_severity = QuestionLog.query.filter(
        QuestionLog.created_at >= start_date,
        QuestionLog.severity == "high"
    ).count()
    medium_severity = QuestionLog.query.filter(
        QuestionLog.created_at >= start_date,
        QuestionLog.severity == "medium"
    ).count()
    low_severity = QuestionLog.query.filter(
        QuestionLog.created_at >= start_date,
        QuestionLog.severity == "low"
    ).count()
    
    # Calculate percentages
    flag_rate = round((flagged_questions / total_questions * 100), 2) if total_questions > 0 else 0
    block_rate = round((blocked_questions / total_questions * 100), 2) if total_questions > 0 else 0
    notification_rate = round((parent_notifications / flagged_questions * 100), 2) if flagged_questions > 0 else 0
    
    total_severity = high_severity + medium_severity + low_severity
    high_severity_pct = round((high_severity / total_severity * 100), 1) if total_severity > 0 else 0
    medium_severity_pct = round((medium_severity / total_severity * 100), 1) if total_severity > 0 else 0
    low_severity_pct = round((low_severity / total_severity * 100), 1) if total_severity > 0 else 0
    
    # Top flagged reasons
    flagged_logs = QuestionLog.query.filter(
        QuestionLog.created_at >= start_date,
        QuestionLog.flagged == True
    ).all()
    
    reason_counts = {}
    for log in flagged_logs:
        reason = log.moderation_reason or "Unknown"
        # Simplify reason to first sentence or first 50 chars
        reason = reason.split('.')[0][:50]
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    
    top_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Daily trend (last 14 days within period)
    daily_trend = []
    trend_days = min(14, int(period) if period != "all" else 14)
    max_daily = 0
    
    for i in range(trend_days):
        day = datetime.utcnow() - timedelta(days=trend_days - i - 1)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        count = QuestionLog.query.filter(
            QuestionLog.created_at >= day_start,
            QuestionLog.created_at < day_end,
            QuestionLog.flagged == True
        ).count()
        
        max_daily = max(max_daily, count)
        daily_trend.append({
            "date": day.strftime("%m/%d"),
            "count": count
        })
    
    # Students with most flagged content
    student_flags = db.session.query(
        QuestionLog.student_id,
        func.count(QuestionLog.id).label('flagged_count'),
        func.sum(func.case([(QuestionLog.severity == 'high', 1)], else_=0)).label('high_count'),
        func.max(QuestionLog.created_at).label('last_flagged')
    ).filter(
        QuestionLog.created_at >= start_date,
        QuestionLog.flagged == True
    ).group_by(QuestionLog.student_id).order_by(func.count(QuestionLog.id).desc()).limit(10).all()
    
    top_students = []
    for student_id, flagged_count, high_count, last_flagged in student_flags:
        student = Student.query.get(student_id)
        if student:
            top_students.append({
                "name": student.student_name,
                "flagged_count": flagged_count,
                "high_count": high_count or 0,
                "last_flagged": last_flagged
            })
    
    stats = {
        "total_questions": total_questions,
        "flagged_questions": flagged_questions,
        "blocked_questions": blocked_questions,
        "parent_notifications": parent_notifications,
        "flag_rate": flag_rate,
        "block_rate": block_rate,
        "notification_rate": notification_rate,
        "question_change": 0,  # TODO: Calculate vs previous period
        "flag_rate_change": 0,
        "block_rate_change": 0,
        "high_severity": high_severity,
        "medium_severity": medium_severity,
        "low_severity": low_severity,
        "high_severity_pct": high_severity_pct,
        "medium_severity_pct": medium_severity_pct,
        "low_severity_pct": low_severity_pct,
        "top_reasons": top_reasons,
        "daily_trend": daily_trend,
        "max_daily": max_daily if max_daily > 0 else 1,
        "top_students": top_students
    }
    
    return render_template(
        "admin_moderation_stats.html",
        stats=stats,
        period=period
    )


@app.route("/create-checkout-session", methods=["POST"])

@csrf.exempt  # Stripe checkout doesn't support CSRF - exempt AFTER route decorator
def create_checkout_session():
    """Create Stripe checkout session for subscription."""
    try:
        role = request.form.get("role")
        plan = request.form.get("plan")
        billing = request.form.get("billing")
        user_id = request.form.get("user_id")
        
        # Get Stripe price ID
        price_id = get_stripe_price_id(role, plan, billing)
        
        if not price_id:
            flash(f"Invalid plan configuration: {role} {plan} {billing}", "error")
            return redirect(f"/trial_expired?role={role}")
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url.rstrip('/') + f'/subscription-success?session_id={{CHECKOUT_SESSION_ID}}&role={role}&user_id={user_id}',
            cancel_url=request.host_url.rstrip('/') + f'/trial_expired?role={role}',
            client_reference_id=f"{role}:{user_id}",  # Track which user is subscribing
            metadata={
                'role': role,
                'user_id': user_id,
                'plan': plan,
                'billing': billing,
            }
        )
        
        return redirect(checkout_session.url, code=303)
        
    except Exception as e:
        logging.error(f"Stripe checkout error: {e}")
        flash("Payment processing error. Please try again.", "error")
        return redirect(f"/trial_expired?role={role}")


@app.route("/subscription-success")
def subscription_success():
    """Handle successful subscription payment."""
    session_id = request.args.get("session_id")
    role = request.args.get("role")
    user_id = request.args.get("user_id")
    
    if not session_id:
        flash("Invalid session.", "error")
        return redirect("/choose_login_role")
    
    try:
        # Retrieve checkout session from Stripe
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        if checkout_session.payment_status == "paid":
            # Activate subscription for user
            if role == "student":
                user = Student.query.get(user_id)
            elif role == "parent":
                user = Parent.query.get(user_id)
            elif role == "teacher":
                user = Teacher.query.get(user_id)
            else:
                flash("Invalid role.", "error")
                return redirect("/choose_login_role")
            
            if user:
                user.subscription_active = True
                user.trial_end = None  # Clear trial end since they're now paid
                db.session.commit()
                
                flash(f"🎉 Welcome to CozmicLearning {user.plan.replace('_', ' ').title()} plan! Your subscription is now active.", "success")
                
                # Redirect to appropriate dashboard
                if role == "student":
                    return redirect("/dashboard")
                elif role == "parent":
                    return redirect("/parent_dashboard")
                elif role == "teacher":
                    return redirect("/teacher/dashboard")
            else:
                flash("User not found.", "error")
                return redirect("/choose_login_role")
        else:
            flash("Payment not completed. Please try again.", "error")
            return redirect(f"/trial_expired?role={role}")
            
    except Exception as e:
        logging.error(f"Subscription activation error: {e}")
        flash("Error activating subscription. Please contact support.", "error")
        return redirect(f"/trial_expired?role={role}")



@app.route("/stripe-webhook", methods=["POST"])
@csrf.exempt  # Stripe webhooks can't have CSRF - exempt AFTER route decorator
def stripe_webhook():
    """Handle Stripe webhook events for subscription management."""
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        logging.error("Invalid webhook payload")
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        logging.error("Invalid webhook signature")
        return jsonify({"error": "Invalid signature"}), 400
    
    # Handle different event types
    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        handle_checkout_completed(session_obj)
        
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)
        
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_canceled(subscription)
        
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_payment_failed(invoice)
    
    return jsonify({"status": "success"}), 200


def handle_checkout_completed(session_obj):
    """Activate subscription when checkout is completed."""
    try:
        metadata = session_obj.get('metadata', {})
        role = metadata.get('role')
        user_id = metadata.get('user_id')
        
        if role == "student":
            user = Student.query.get(user_id)
        elif role == "parent":
            user = Parent.query.get(user_id)
        elif role == "teacher":
            user = Teacher.query.get(user_id)
        else:
            logging.error(f"Unknown role in webhook: {role}")
            return
        
        if user:
            user.subscription_active = True
            user.trial_end = None
            db.session.commit()
            logging.info(f"Activated subscription for {role} {user_id}")
    except Exception as e:
        logging.error(f"Error in handle_checkout_completed: {e}")


def handle_subscription_updated(subscription):
    """Handle subscription updates (plan changes, renewals)."""
    try:
        customer_id = subscription.get('customer')
        status = subscription.get('status')
        
        # You would need to store customer_id in your database to look up users
        # For now, we'll log the event
        logging.info(f"Subscription updated for customer {customer_id}: {status}")
    except Exception as e:
        logging.error(f"Error in handle_subscription_updated: {e}")


def handle_subscription_canceled(subscription):
    """Deactivate user account when subscription is canceled."""
    try:
        customer_id = subscription.get('customer')
        
        # Find user by Stripe customer ID (would need to add this field to models)
        # For now, log the event
        logging.warning(f"Subscription canceled for customer {customer_id}")
        
        # TODO: Add stripe_customer_id field to Student, Parent, Teacher models
        # Then query and deactivate: user.subscription_active = False
    except Exception as e:
        logging.error(f"Error in handle_subscription_canceled: {e}")


def handle_payment_failed(invoice):
    """Handle failed payment (send email, grace period, etc)."""
    try:
        customer_id = invoice.get('customer')
        amount_due = invoice.get('amount_due') / 100  # Convert cents to dollars
        
        logging.warning(f"Payment failed for customer {customer_id}: ${amount_due}")
        
        # TODO: Send email notification to user about failed payment
        # TODO: Set grace period before deactivating account
    except Exception as e:
        logging.error(f"Error in handle_payment_failed: {e}")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/choose_login_role")


# ============================================================
# STUDENT + PARENT AUTH (DB-BACKED)
# ============================================================

@app.route("/student/signup", methods=["GET", "POST"])
def student_signup():
    init_user()
    
    # Get plan from query string for standalone students
    selected_plan = request.args.get("plan", "basic")
    selected_billing = request.args.get("billing", "monthly")
    
    if request.method == "POST":
        name = safe_text(request.form.get("name", ""), 100)
        email = safe_email(request.form.get("email", ""))
        password = request.form.get("password", "")
        parent_code = safe_text(request.form.get("parent_code", ""), 10).upper().strip()
        signup_mode = request.form.get("signup_mode", "standalone")  # standalone or parent_linked
        
        # Plan selections for standalone students
        plan = safe_text(request.form.get("plan", ""), 50) or "basic"
        billing = safe_text(request.form.get("billing", ""), 20) or "monthly"

        if not name or not email or not password:
            flash("Name, email, and password are required.", "error")
            return redirect("/student/signup")

        existing_student = Student.query.filter_by(student_email=email).first()
        if existing_student:
            flash("A student with that email already exists.", "error")
            return redirect("/student/login")

        # Handle parent-linked signup
        if signup_mode == "parent_linked" and parent_code:
            parent = Parent.query.filter_by(access_code=parent_code).first()
            if not parent:
                flash("Invalid parent access code. Please check with your parent.", "error")
                return redirect("/student/signup")
            
            # Check parent's subscription limits using new helper
            allowed, current_count, limit = check_parent_student_limit(parent)
            if not allowed:
                if limit == float('inf'):
                    # Should never happen, but safety check
                    pass
                else:
                    plan_name = parent.plan.replace('_', ' ').title()
                    flash(f"Your parent's {plan_name} plan only allows {int(limit)} students. They need to upgrade.", "error")
                    return redirect("/student/signup")

            # Student inherits parent's subscription plan
            trial_start = parent.trial_start
            trial_end = parent.trial_end
            subscription_active = parent.subscription_active
            student_plan = parent.plan
            student_billing = parent.billing
            parent_id = parent.id
            welcome_msg = f"Welcome to CozmicLearning, {name}! Your account is linked to {parent.name}."
        else:
            # Standalone student signup (independent account)
            trial_start = datetime.utcnow()
            trial_end = trial_start + timedelta(days=7)
            subscription_active = True  # Trial is active
            student_plan = plan
            student_billing = billing
            parent_id = None
            welcome_msg = f"Welcome to CozmicLearning, {name}! Your 7-day free trial has started."

        # Create student account
        new_student = Student(
            student_name=name,
            student_email=email,
            parent_id=parent_id,
            plan=student_plan,
            billing=student_billing,
            trial_start=trial_start,
            trial_end=trial_end,
            subscription_active=subscription_active,
        )
        db.session.add(new_student)
        db.session.commit()

        session["student_id"] = new_student.id
        session["user_role"] = "student"
        session["student_name"] = name
        session["student_email"] = email

        flash(welcome_msg, "info")
        return redirect("/dashboard")

    return render_template("student_signup.html", selected_plan=selected_plan, selected_billing=selected_billing)


@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    init_user()
    if request.method == "POST":
        email = safe_email(request.form.get("email", ""))
        password = request.form.get("password", "")

        student = Student.query.filter_by(student_email=email).first()
        if not student:
            flash("No student found with that email.", "error")
            return redirect("/student/login")

        # Track login time and reset daily minutes if new day
        now = datetime.utcnow()
        today = now.date()
        
        if student.last_login:
            last_login_date = student.last_login.date()
            if last_login_date != today:
                # New day - reset minutes
                student.today_minutes = 0
        else:
            # First login ever
            student.today_minutes = 0
        
        student.last_login = now
        db.session.commit()

        # Currently students don't use a password hash in DB.
        session["student_id"] = student.id
        session["user_role"] = "student"
        session["student_name"] = student.student_name
        session["student_email"] = student.student_email
        session["login_time"] = now.isoformat()  # Track session start

        flash(f"Welcome back, {student.student_name}!", "info")
        return redirect("/dashboard")

    return render_template("student_login.html")


@app.route("/parent/plans")
def parent_plans():
    """Display subscription plans for parents."""
    init_user()
    return render_template("parent_plans.html")


@app.route("/parent/signup", methods=["GET", "POST"])
def parent_signup():
    init_user()
    
    # Get plan from query string (from plans page)
    selected_plan = request.args.get("plan", "basic")
    
    if request.method == "POST":
        name = safe_text(request.form.get("name", ""), 100)
        email = safe_email(request.form.get("email", ""))
        password = request.form.get("password", "")
        # Pricing selections
        plan = safe_text(request.form.get("plan", ""), 50) or "free"
        billing = safe_text(request.form.get("billing", ""), 20) or "monthly"

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return redirect("/parent/signup")

        existing_parent = Parent.query.filter_by(email=email).first()
        if existing_parent:
            flash("Parent with that email already exists. Please log in.", "error")
            return redirect("/parent/login")

        # Set trial period (7 days for all new accounts)
        trial_start = datetime.utcnow()
        trial_end = trial_start + timedelta(days=7)
        
        # Generate unique access code
        access_code = generate_parent_access_code()
        
        parent = Parent(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            access_code=access_code,
            plan=plan,
            billing=billing,
            trial_start=trial_start,
            trial_end=trial_end,
            subscription_active=True,  # All plans are paid
        )
        db.session.add(parent)
        db.session.commit()

        session["parent_id"] = parent.id
        session["user_role"] = "parent"
        session["parent_name"] = parent.name
        session["access_code"] = access_code  # Store to display on dashboard

        flash(f"Welcome! Your Parent Access Code is: {access_code} - Share this with your children to link their accounts.", "success")
        return redirect("/parent_dashboard")

    return render_template("parent_signup.html", selected_plan=selected_plan)


@csrf.exempt
@app.route("/parent/login", methods=["GET", "POST"])
def parent_login():
    init_user()
    if request.method == "POST":
        email = safe_email(request.form.get("email", ""))
        password = request.form.get("password", "")

        parent = Parent.query.filter_by(email=email).first()
        if not parent:
            flash("No parent found with that email.", "error")
            return redirect("/parent/login")

        if not check_password_hash(parent.password_hash, password):
            flash("Incorrect password.", "error")
            return redirect("/parent/login")

        session["parent_id"] = parent.id
        session["user_role"] = "parent"
        session["parent_name"] = parent.name
        
        # Generate access code if parent doesn't have one (for existing accounts)
        if not parent.access_code:
            parent.access_code = generate_parent_access_code()
            db.session.commit()

        flash("Logged in!", "info")
        
        # Check if this is a homeschool parent (has teacher features)
        _, _, _, has_teacher_features = get_parent_plan_limits(parent)
        
        if has_teacher_features:
            # Redirect homeschool parents to homeschool dashboard
            return redirect("/homeschool/dashboard")
        else:
            # Regular parents go to parent dashboard
            return redirect("/parent_dashboard")

    return render_template("parent_login.html")


# ============================================================
# TEACHER AUTH + DASHBOARD
# ============================================================

@app.route("/teacher/signup", methods=["GET", "POST"])
def teacher_signup():
    if request.method == "POST":
        name = safe_text(request.form.get("name", ""), 100)
        email = safe_email(request.form.get("email", ""))
        password = request.form.get("password", "")
        # Pricing selections
        plan = safe_text(request.form.get("plan", ""), 50) or None
        billing = safe_text(request.form.get("billing", ""), 20) or None

        if not name or not email or not password:
            flash("Please fill out all fields.", "error")
            return redirect("/teacher/signup")

        existing = Teacher.query.filter_by(email=email).first()
        if existing:
            flash("An account with that email already exists.", "error")
            return redirect("/teacher/login")

        hashed = generate_password_hash(password)
        trial_start = datetime.utcnow()
        trial_end = trial_start + timedelta(days=7)
        teacher = Teacher(
            name=name,
            email=email,
            password_hash=hashed,
            plan=plan,
            billing=billing,
            trial_start=trial_start,
            trial_end=trial_end,
            subscription_active=False,
        )
        db.session.add(teacher)
        db.session.commit()

        session["teacher_id"] = teacher.id
        session["user_role"] = "teacher"

        flash("Welcome to CozmicLearning Teacher Portal!", "info")
        return redirect("/teacher/dashboard")

    return render_template("teacher_signup.html")


@app.route("/teacher/login", methods=["GET", "POST"])
def teacher_login():
    if request.method == "POST":
        email = safe_email(request.form.get("email", ""))
        password = request.form.get("password", "")

        teacher = Teacher.query.filter_by(email=email).first()
        if teacher and check_password_hash(teacher.password_hash, password):
            session["teacher_id"] = teacher.id
            session["user_role"] = "teacher"
            # Set is_owner flag for navbar admin button
            session["is_owner"] = is_owner(teacher)
            flash("Logged in successfully.", "info")
            return redirect("/teacher/dashboard")

        flash("Invalid email or password.", "error")

    return render_template("teacher_login.html")


@app.route("/teacher/logout")
def teacher_logout():
    session.pop("teacher_id", None)
    session.pop("user_role", None)
    flash("You have been logged out.", "info")
    return redirect("/teacher/login")


# ============================================================
# FORGOT PASSWORD FLOW
# ============================================================

@app.route("/forgot-password/<role>", methods=["GET", "POST"])
def forgot_password(role):
    """Unified forgot password for student/parent/teacher"""
    if role not in ["student", "parent", "teacher"]:
        flash("Invalid role.", "error")
        return redirect("/choose_login_role")
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        
        if not email:
            flash("Please enter your email address.", "error")
            return render_template("forgot_password.html", role=role)
        
        # Generate reset token
        token = generate_reset_token(email, role)
        
        # In production, send email here. For now, display token directly
        reset_url = request.host_url.rstrip('/') + f"/reset-password/{token}"
        
        flash(f"Password reset link (demo): {reset_url}", "info")
        flash("In production, this would be emailed to you.", "info")
        
        return render_template("forgot_password.html", role=role, reset_url=reset_url)
    
    return render_template("forgot_password.html", role=role)


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Reset password with valid token"""
    token_data = verify_reset_token(token)
    
    if not token_data:
        flash("Invalid or expired reset link.", "error")
        return redirect("/choose_login_role")
    
    email = token_data["email"]
    role = token_data["role"]
    
    if request.method == "POST":
        new_password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not new_password or not confirm_password:
            flash("Please enter and confirm your new password.", "error")
            return render_template("reset_password.html", token=token, role=role)
        
        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("reset_password.html", token=token, role=role)
        
        if len(new_password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("reset_password.html", token=token, role=role)
        
        # Update password based on role
        hashed = generate_password_hash(new_password)
        
        if role == "student":
            # Students don't currently use password_hash in DB
            # For now, just show success message
            flash("Password reset successful! You can now log in.", "success")
            del password_reset_tokens[token]
            return redirect("/student/login")
        
        elif role == "parent":
            parent = Parent.query.filter_by(email=email).first()
            if parent:
                parent.password_hash = hashed
                db.session.commit()
                flash("Password reset successful! You can now log in.", "success")
                del password_reset_tokens[token]
                return redirect("/parent/login")
        
        elif role == "teacher":
            teacher = Teacher.query.filter_by(email=email).first()
            if teacher:
                teacher.password_hash = hashed
                db.session.commit()
                flash("Password reset successful! You can now log in.", "success")
                del password_reset_tokens[token]
                return redirect("/teacher/login")
        
        flash("Account not found.", "error")
        return redirect("/choose_login_role")
    
    return render_template("reset_password.html", token=token, role=role)


@app.route("/teacher/dashboard")
def teacher_dashboard():
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")
    
    # Check subscription status for teachers
    access_check = check_subscription_access("teacher")
    if access_check != True:
        return access_check  # Redirect to trial_expired
    
    # Get trial days remaining
    trial_days_remaining = get_days_remaining_in_trial(teacher)

    # Count unread messages
    unread_messages = Message.query.filter_by(
        recipient_type="teacher",
        recipient_id=teacher.id,
        is_read=False,
    ).count()

    classes = teacher.classes or []
    return render_template(
        "teacher_dashboard.html",
        teacher=teacher,
        classes=classes,
        is_owner=is_owner(teacher),
        unread_messages=unread_messages,
        trial_days_remaining=trial_days_remaining,
    )


@app.route("/teacher/settings", methods=["GET", "POST"])
def teacher_settings():
    """Teacher account settings - subscription, profile, password"""
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")
    
    # Check subscription status
    access_check = check_subscription_access("teacher")
    if access_check != True:
        return access_check
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "update_profile":
            name = request.form.get("name", "").strip()
            if name:
                teacher.name = name
                db.session.commit()
                flash("Profile updated successfully.", "success")
            else:
                flash("Name cannot be empty.", "error")
        
        elif action == "change_password":
            current_pw = request.form.get("current_password", "")
            new_pw = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_password", "")
            
            if not check_password_hash(teacher.password_hash, current_pw):
                flash("Current password is incorrect.", "error")
            elif new_pw != confirm_pw:
                flash("New passwords do not match.", "error")
            elif len(new_pw) < 6:
                flash("Password must be at least 6 characters.", "error")
            else:
                teacher.password_hash = generate_password_hash(new_pw)
                db.session.commit()
                flash("Password changed successfully.", "success")
        
        return redirect("/teacher/settings")
    
    # Get trial info
    trial_days_remaining = get_days_remaining_in_trial(teacher)
    
    return render_template(
        "teacher_settings.html",
        teacher=teacher,
        is_owner=is_owner(teacher),
        trial_days_remaining=trial_days_remaining
    )


# ============================================================
# TEACHER – CLASSES + STUDENTS
# ============================================================

@app.route("/teacher/classes")
def teacher_classes():
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    classes = teacher.classes or []
    return render_template(
        "teacher_dashboard.html",
        teacher=teacher,
        classes=classes,
        is_owner=is_owner(teacher),
    )

@app.route("/teacher/add_class", methods=["POST"])
def add_class():
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    class_name = request.form.get("class_name", "").strip()
    grade = request.form.get("grade_level", "").strip()

    if not class_name:
        flash("Class name is required.", "error")
        return redirect("/teacher/dashboard")

    try:
        cls = Class(teacher_id=teacher.id, class_name=class_name, grade_level=grade)
        db.session.add(cls)
        db.session.commit()
        
        # Log success
        print(f"✅ Class created: {class_name} (ID: {cls.id}, Teacher: {teacher.id})")
        
        # Verify it was saved
        verify = Class.query.get(cls.id)
        if verify:
            print(f"✅ Class verified in database: {verify.class_name}")
        else:
            print(f"⚠️ Class NOT found after commit!")
        
        # Save backup after creating class
        backup_classes_to_json()

        flash("Class created successfully.", "info")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating class: {e}")
        flash(f"Error creating class: {str(e)}", "error")
    
    return redirect("/teacher/dashboard")


@app.route("/teacher/add_student/<int:class_id>", methods=["POST"])
def add_student(class_id):
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    cls = Class.query.get(class_id)
    if not cls or (not is_owner(teacher) and cls.teacher_id != teacher.id):
        flash("Class not found or not authorized.", "error")
        return redirect("/teacher/dashboard")

    name = request.form.get("student_name", "").strip()
    email = request.form.get("email", "").strip()

    if not name:
        flash("Student name is required.", "error")
        return redirect("/teacher/dashboard")

    student = Student(class_id=class_id, student_name=name, student_email=email)
    db.session.add(student)
    db.session.commit()
    # Save backup after adding student
    backup_classes_to_json()

    flash("Student added to class.", "info")
    return redirect("/teacher/dashboard")


@app.route("/teacher/delete_class/<int:class_id>", methods=["POST"])
def delete_class(class_id):
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    cls = Class.query.get(class_id)
    if not cls or (not is_owner(teacher) and cls.teacher_id != teacher.id):
        flash("Class not found or not authorized.", "error")
        return redirect("/teacher/dashboard")

    class_name = cls.class_name
    
    # Delete all students in the class (cascade should handle this, but explicit is safer)
    Student.query.filter_by(class_id=class_id).delete()
    
    # Delete all assignments for this class
    AssignedPractice.query.filter_by(class_id=class_id).delete()
    
    # Delete the class
    db.session.delete(cls)
    db.session.commit()
    
    # Update backup
    backup_classes_to_json()
    
    flash(f"Class '{class_name}' and all its students have been deleted.", "info")
    return redirect("/teacher/dashboard")


@app.route("/teacher/delete_student/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    student = Student.query.get(student_id)
    if not student:
        flash("Student not found.", "error")
        return redirect("/teacher/dashboard")
    
    # Check if teacher owns the class this student belongs to
    cls = Class.query.get(student.class_id)
    if not cls or (not is_owner(teacher) and cls.teacher_id != teacher.id):
        flash("Not authorized to delete this student.", "error")
        return redirect("/teacher/dashboard")
    
    student_name = student.student_name
    
    # Delete all assessment results for this student
    AssessmentResult.query.filter_by(student_id=student_id).delete()
    
    # Delete the student
    db.session.delete(student)
    db.session.commit()
    
    # Update backup
    backup_classes_to_json()
    
    flash(f"Student '{student_name}' has been deleted.", "info")
    return redirect("/teacher/dashboard")


# ============================================================
# TEACHER – ASSIGNMENTS (CREATE + MANAGE)
# ============================================================

@app.route("/teacher/assignments")
def teacher_assignments():
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    classes = teacher.classes or []
    assignment_map = {}
    for cls in classes:
        assignment_map[cls.id] = (
            AssignedPractice.query.filter_by(class_id=cls.id, teacher_id=teacher.id)
            .order_by(AssignedPractice.created_at.desc())
            .all()
        )

    return render_template(
        "teacher_assignments.html",
        teacher=teacher,
        classes=classes,
        assignment_map=assignment_map,
        is_owner=is_owner(teacher),
    )


@app.route("/teacher/assignments/create", methods=["GET", "POST"])
def create_assignment():
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    if request.method == "POST":
        class_id = request.form.get("class_id", type=int)
        title = safe_text(request.form.get("title", ""), 120)
        subject = safe_text((request.form.get("subject", "") or "general"), 50).lower()
        topic = safe_text((request.form.get("topic", "") or ""), 500)
        instructions = safe_text(request.form.get("instructions", ""), 2000)
        due_str = request.form.get("due_date", "").strip()
        differentiation_mode = request.form.get("differentiation_mode", "none")

        if not class_id or not title:
            flash("Please choose a class and give this assignment a title.", "error")
            return redirect("/teacher/assignments/create")

        due_date = None
        if due_str:
            try:
                due_date = datetime.strptime(due_str, "%Y-%m-%d")
            except Exception:
                due_date = None

        practice = AssignedPractice(
            class_id=class_id,
            teacher_id=teacher.id,
            title=title,
            subject=subject,
            topic=topic,
            instructions=instructions,
            due_date=due_date,
            differentiation_mode=differentiation_mode,
        )
        db.session.add(practice)
        db.session.commit()

        flash("Assignment created. Now add questions (optional).", "info")
        return redirect(f"/teacher/assignments/{practice.id}")

    return render_template(
        "create_assignment.html",
        teacher=teacher,
        classes=teacher.classes,
        is_owner=is_owner(teacher),
    )


@app.route("/teacher/assignments/<int:practice_id>")
def assignment_overview(practice_id):
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    assignment = AssignedPractice.query.get_or_404(practice_id)
    if not is_owner(teacher) and assignment.teacher_id != teacher.id:
        flash("Not authorized to view this assignment.", "error")
        return redirect("/teacher/assignments")

    questions = assignment.questions or []

    return render_template(
        "assignment_overview.html",
        teacher=teacher,
        assignment=assignment,
        questions=questions,
        class_obj=assignment.class_ref,
        is_owner=is_owner(teacher),
    )


@app.route("/teacher/assignments/<int:practice_id>/edit", methods=["GET", "POST"])
def assignment_edit(practice_id):
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    assignment = AssignedPractice.query.get_or_404(practice_id)
    if not is_owner(teacher) and assignment.teacher_id != teacher.id:
        flash("Not authorized to edit this assignment.", "error")
        return redirect("/teacher/assignments")

    if request.method == "POST":
        # Bulk update: iterate posted questions
        qids = request.form.getlist("q_id")
        for qid in qids:
            q = AssignedQuestion.query.get(int(qid))
            if not q or q.practice_id != assignment.id:
                continue
            q.question_text = safe_text(request.form.get(f"question_text_{qid}", ""), 4000)
            q.question_type = request.form.get(f"question_type_{qid}", "free")
            q.choice_a = safe_text(request.form.get(f"choice_a_{qid}", ""), 1000) or None
            q.choice_b = safe_text(request.form.get(f"choice_b_{qid}", ""), 1000) or None
            q.choice_c = safe_text(request.form.get(f"choice_c_{qid}", ""), 1000) or None
            q.choice_d = safe_text(request.form.get(f"choice_d_{qid}", ""), 1000) or None
            q.correct_answer = safe_text(request.form.get(f"correct_answer_{qid}", ""), 1000) or None
            q.explanation = safe_text(request.form.get(f"explanation_{qid}", ""), 4000) or None
            q.difficulty_level = request.form.get(f"difficulty_level_{qid}", "") or None
        db.session.commit()
        flash("Questions updated.", "info")
        return redirect(f"/teacher/assignments/{practice_id}/edit")

    return render_template(
        "assignment_edit.html",
        teacher=teacher,
        assignment=assignment,
        questions=assignment.questions,
        is_owner=is_owner(teacher),
    )


@app.route(
    "/teacher/assignments/<int:practice_id>/questions/new", methods=["GET", "POST"]
)
def assignment_add_question(practice_id):
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    assignment = AssignedPractice.query.get_or_404(practice_id)
    if not is_owner(teacher) and assignment.teacher_id != teacher.id:
        flash("Not authorized to modify this assignment.", "error")
        return redirect("/teacher/assignments")

    if request.method == "POST":
        question_text = safe_text(request.form.get("question_text", ""), 2000)
        question_type = request.form.get("question_type", "free")

        choice_a = safe_text(request.form.get("choice_a", ""), 500) or None
        choice_b = safe_text(request.form.get("choice_b", ""), 500) or None
        choice_c = safe_text(request.form.get("choice_c", ""), 500) or None
        choice_d = safe_text(request.form.get("choice_d", ""), 500) or None
        correct_answer = safe_text(request.form.get("correct_answer", ""), 500) or None
        explanation = safe_text(request.form.get("explanation", ""), 2000) or None
        difficulty = request.form.get("difficulty_level", "").strip() or None

        if not question_text:
            flash("Question text is required.", "error")
            return redirect(f"/teacher/assignments/{practice_id}")

        q = AssignedQuestion(
            practice_id=assignment.id,
            question_text=question_text,
            question_type=question_type,
            choice_a=choice_a,
            choice_b=choice_b,
            choice_c=choice_c,
            choice_d=choice_d,
            correct_answer=correct_answer,
            explanation=explanation,
            difficulty_level=difficulty,
        )
        db.session.add(q)
        db.session.commit()

        flash("Question added.", "info")
        return redirect(f"/teacher/assignments/{practice_id}")

    return render_template(
        "create_assignment.html",  # reuse layout
        teacher=teacher,
        assignment=assignment,
        classes=teacher.classes,
        is_owner=is_owner(teacher),
    )


@csrf.exempt
@app.route("/teacher/assignments/<int:practice_id>/generate_more", methods=["POST"])
def assignment_generate_more(practice_id):
    """Generate additional AI questions and add to existing assignment."""
    teacher = get_current_teacher()
    if not teacher:
        return jsonify({"error": "Not authenticated"}), 401

    assignment = AssignedPractice.query.get_or_404(practice_id)
    if not is_owner(teacher) and assignment.teacher_id != teacher.id:
        return jsonify({"error": "Not authorized"}), 403

    data = request.get_json() or {}
    num_questions = data.get("num_questions", 5)

    # Generate questions using existing assignment settings
    payload = assign_questions(
        subject=assignment.subject,
        topic=assignment.topic,
        grade=str(assignment.class_ref.grade_level or "8"),
        character="everly",
        differentiation_mode=assignment.differentiation_mode or "none",
        student_ability="on_level",
        num_questions=num_questions,
    )

    # Add new questions to assignment
    questions_data = payload.get("questions", [])
    for q in questions_data:
        choices = q.get("choices", [])
        expected = q.get("expected", [])

        new_q = AssignedQuestion(
            practice_id=assignment.id,
            question_text=q.get("prompt", ""),
            question_type=q.get("type", "free"),
            choice_a=choices[0] if len(choices) > 0 else None,
            choice_b=choices[1] if len(choices) > 1 else None,
            choice_c=choices[2] if len(choices) > 2 else None,
            choice_d=choices[3] if len(choices) > 3 else None,
            correct_answer=",".join(expected) if isinstance(expected, list) else str(expected),
            explanation=q.get("explanation", ""),
            difficulty_level="medium",
        )
        db.session.add(new_q)

    db.session.commit()

    return jsonify({
        "success": True,
        "questions_added": len(questions_data),
        "message": f"Added {len(questions_data)} more questions to assignment"
    }), 201


@app.route("/teacher/questions/<int:question_id>/edit", methods=["GET", "POST"])
def edit_question(question_id):
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    question = AssignedQuestion.query.get_or_404(question_id)
    assignment = question.practice

    if not is_owner(teacher) and assignment.teacher_id != teacher.id:
        flash("Not authorized to edit this question.", "error")
        return redirect("/teacher/assignments")

    if request.method == "POST":
        question.question_text = safe_text(request.form.get("question_text", ""), 2000)
        question.question_type = request.form.get("question_type", "free")

        question.choice_a = safe_text(request.form.get("choice_a", ""), 500) or None
        question.choice_b = safe_text(request.form.get("choice_b", ""), 500) or None
        question.choice_c = safe_text(request.form.get("choice_c", ""), 500) or None
        question.choice_d = safe_text(request.form.get("choice_d", ""), 500) or None
        question.correct_answer = safe_text(request.form.get("correct_answer", ""), 500) or None
        question.explanation = safe_text(request.form.get("explanation", ""), 2000) or None
        question.difficulty_level = (
            request.form.get("difficulty_level", "").strip() or None
        )

        db.session.commit()
        flash("Question updated.", "info")
        return redirect(f"/teacher/assignments/{assignment.id}")

    return render_template(
        "edit_assignment.html",
        question=question,
        assignment=assignment,
        teacher=teacher,
        is_owner=is_owner(teacher),
    )


# ============================================================
# STUDENT – VIEW ASSIGNMENTS LIST
# ============================================================

@app.route("/student/assignments")
def student_assignments():
    init_user()

    student_id = session.get("student_id")
    student = Student.query.get(student_id) if student_id else None

    if not student:
        flash("Student not logged in.", "error")
        return redirect("/student/login")

    # ONLY show fully published assignments for this student's class
    assignments = (
        AssignedPractice.query
        .filter_by(class_id=student.class_id, is_published=True)
        .order_by(AssignedPractice.created_at.desc())
        .all()
    )

    return render_template(
        "student_assignments.html",
        assignments=assignments
    )

# ============================================================
# TEACHER - PREVIEW STORED AI MISSION
# ============================================================

@app.route("/teacher/assignments/<int:practice_id>/preview")
def assignment_preview(practice_id):
    init_user()

    assignment = AssignedPractice.query.get_or_404(practice_id)

    # Only teacher who created it can preview
    if assignment.teacher_id != session.get("teacher_id"):
        flash("Access denied.", "error")
        return redirect("/teacher/dashboard")

    # Validate that a preview exists
    if not assignment.preview_json:
        flash("This assignment has no AI preview yet.", "error")
        return redirect(f"/teacher/assignments/{practice_id}")

    # Load stored JSON safely
    try:
        import json
        mission = json.loads(assignment.preview_json)
    except Exception:
        mission = {"steps": [], "final_message": "Preview unavailable"}

    return render_template(
        "assignment_preview.html",
        assignment=assignment,
        mission=mission
    )

# ============================================================
# TEACHER - UPDATE PREVIEW JSON (FROM INTERACTIVE PREVIEW)
# ============================================================

@csrf.exempt
@app.route("/teacher/assignments/<int:assignment_id>/update_preview", methods=["POST"])
def update_assignment_preview(assignment_id):
    """Update the preview JSON for an assignment after teacher edits."""
    teacher = get_current_teacher()
    if not teacher:
        return jsonify({"error": "Not authenticated"}), 401

    assignment = AssignedPractice.query.get_or_404(assignment_id)

    # Only teacher who created it can update
    if assignment.teacher_id != teacher.id:
        return jsonify({"error": "Not authorized"}), 403

    data = request.get_json() or {}
    steps = data.get("steps", [])
    final_message = data.get("final_message", "Great work!")

    # Build updated mission JSON
    mission_json = {
        "steps": steps,
        "final_message": final_message
    }

    # Update the preview_json field
    assignment.preview_json = json.dumps(mission_json)
    db.session.commit()

    return jsonify({"success": True, "message": "Preview updated successfully"}), 200

# ============================================================
# TEACHER - PUBLISH AI-GENERATED MISSION
# ============================================================

@app.route("/teacher/assignments/<int:assignment_id>/publish")
def assignment_publish(assignment_id):
    init_user()

    assignment = AssignedPractice.query.get_or_404(assignment_id)

    # Only teacher can publish their own assignment
    if assignment.teacher_id != session.get("teacher_id"):
        flash("Unauthorized.", "error")
        return redirect("/teacher/dashboard")

    # Must have a JSON preview from the AI generation
    if not assignment.preview_json:
        flash("You must preview this mission before publishing.", "error")
        return redirect(f"/teacher/assignments/{assignment.id}")

    import json
    try:
        mission = json.loads(assignment.preview_json)
    except Exception:
        flash("Mission preview data is corrupted.", "error")
        return redirect(f"/teacher/assignments/{assignment.id}")

    steps = mission.get("steps", [])
    if not steps:
        flash("Mission contains no steps.", "error")
        return redirect(f"/teacher/assignments/{assignment.id}")

    # ---------------------------------------------
    # CLEAR OLD QUESTIONS FIRST (to avoid duplicates)
    # ---------------------------------------------
    for q in assignment.questions:
        db.session.delete(q)
    db.session.commit()

    # ---------------------------------------------
    # Convert AI steps → AssignedQuestion records
    # ---------------------------------------------
    for step in steps:
        choices = step.get("choices", [])
        qtype = step.get("type", "free")

        new_q = AssignedQuestion(
            practice_id=assignment.id,
            question_text=step.get("prompt", ""),
            question_type=qtype,
            choice_a=choices[0] if len(choices) > 0 else None,
            choice_b=choices[1] if len(choices) > 1 else None,
            choice_c=choices[2] if len(choices) > 2 else None,
            choice_d=choices[3] if len(choices) > 3 else None,
            correct_answer=",".join(step.get("expected", [])),
            explanation=step.get("explanation", ""),
            difficulty_level="medium"
        )

        db.session.add(new_q)

    # Mark assignment as published
    assignment.is_published = True
    db.session.commit()

    flash("Mission published successfully!", "success")
    return redirect(f"/teacher/assignments/{assignment.id}")

# ============================================================
# TEACHER - AI QUESTION ASSIGNMENT GENERATOR
# ============================================================

@csrf.exempt
@app.route("/teacher/assign_questions", methods=["POST"])
def teacher_assign_questions():
    """Generate AI questions and create assignment with AssignedQuestions."""
    teacher = get_current_teacher()
    if not teacher:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json() or {}

    class_id = data.get("class_id", type=int)
    title = safe_text(data.get("title", ""), 120)
    subject = safe_text(data.get("subject", "terra_nova"), 50)
    topic = safe_text(data.get("topic", ""), 500)
    grade = safe_text(data.get("grade", "8"), 10)
    character = safe_text(data.get("character", "everly"), 50)
    differentiation_mode = data.get("differentiation_mode", "none")
    student_ability = data.get("student_ability", "on_level")
    num_questions = data.get("num_questions", 10)
    due_str = data.get("due_date", "").strip()

    if not class_id or not title or not topic:
        return jsonify({"error": "Missing required fields: class_id, title, topic"}), 400

    # Check teacher owns class
    cls = Class.query.get(class_id)
    if not cls:
        return jsonify({"error": "Class not found"}), 404
    if not is_owner(teacher) and cls.teacher_id != teacher.id:
        return jsonify({"error": "Not authorized for this class"}), 403

    # Parse due date
    due_date = None
    if due_str:
        try:
            due_date = datetime.strptime(due_str, "%Y-%m-%d")
        except Exception:
            due_date = None

    # Generate questions using teacher_tools.assign_questions
    payload = assign_questions(
        subject=subject,
        topic=topic,
        grade=grade,
        character=character,
        differentiation_mode=differentiation_mode,
        student_ability=student_ability,
        num_questions=num_questions,
    )

    # Build preview JSON in mission format (compatible with assignment_preview.html)
    questions_data = payload.get("questions", [])
    mission_json = {
        "steps": [
            {
                "prompt": q.get("prompt", ""),
                "type": q.get("type", "free"),
                "choices": q.get("choices", []),
                "expected": q.get("expected", []),
                "hint": q.get("hint", ""),
                "explanation": q.get("explanation", "")
            }
            for q in questions_data
        ],
        "final_message": payload.get("final_message", "Great work! Review your answers and submit when ready.")
    }

    # Create AssignedPractice record with preview JSON
    assignment = AssignedPractice(
        class_id=class_id,
        teacher_id=teacher.id,
        title=title,
        subject=subject,
        topic=topic,
        due_date=due_date,
        differentiation_mode=differentiation_mode,
        is_published=False,  # Teacher can review before publishing
        preview_json=json.dumps(mission_json)  # Store the mission preview
    )
    db.session.add(assignment)
    db.session.flush()  # Get assignment.id

    # Create AssignedQuestion records from generated questions
    for q in questions_data:
        choices = q.get("choices", [])
        expected = q.get("expected", [])

        new_q = AssignedQuestion(
            practice_id=assignment.id,
            question_text=q.get("prompt", ""),
            question_type=q.get("type", "free"),
            choice_a=choices[0] if len(choices) > 0 else None,
            choice_b=choices[1] if len(choices) > 1 else None,
            choice_c=choices[2] if len(choices) > 2 else None,
            choice_d=choices[3] if len(choices) > 3 else None,
            correct_answer=",".join(expected) if isinstance(expected, list) else str(expected),
            explanation=q.get("explanation", ""),
            difficulty_level="medium",
        )
        db.session.add(new_q)

    db.session.commit()

    return jsonify({
        "success": True,
        "assignment_id": assignment.id,
        "message": f"Generated {len(questions_data)} questions for assignment '{title}'",
        "edit_url": f"/teacher/assignments/{assignment.id}/edit",
    }), 201

# ============================================================
# TEACHER - PREVIEW AI QUESTIONS (NO PERSISTENCE)
# ============================================================

@csrf.exempt
@app.route("/teacher/preview_questions", methods=["POST"])
def teacher_preview_questions():
    """Generate AI questions for preview only (no DB write)."""
    teacher = get_current_teacher()
    if not teacher:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json() or {}

    subject = safe_text(data.get("subject", "terra_nova"), 50)
    topic = safe_text(data.get("topic", ""), 500)
    grade = safe_text(data.get("grade", "8"), 10)
    character = safe_text(data.get("character", "everly"), 50)
    differentiation_mode = data.get("differentiation_mode", "none")
    student_ability = data.get("student_ability", "on_level")
    num_questions = data.get("num_questions", 10)

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    # Generate questions using teacher_tools.assign_questions
    payload = assign_questions(
        subject=subject,
        topic=topic,
        grade=grade,
        character=character,
        differentiation_mode=differentiation_mode,
        student_ability=student_ability,
        num_questions=num_questions,
    )

    return jsonify({
        "success": True,
        "questions": payload.get("questions", []),
        "metadata": {
            "subject": subject,
            "topic": topic,
            "grade": grade,
            "differentiation_mode": differentiation_mode,
            "student_ability": student_ability,
        }
    }), 200

# ============================================================
# TEACHER - GENERATE LESSON PLAN
# ============================================================

@csrf.exempt
@app.route("/teacher/generate_lesson_plan", methods=["POST"])
def teacher_generate_lesson_plan():
    """Generate a six-section lesson plan and save to database."""
    teacher = get_current_teacher()
    if not teacher:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json() or {}

    subject = safe_text(data.get("subject", "terra_nova"), 50)
    topic = safe_text(data.get("topic", ""), 500)
    grade = safe_text(data.get("grade", "8"), 10)
    character = safe_text(data.get("character", "everly"), 50)

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    # Generate lesson plan using teacher_tools
    lesson = generate_lesson_plan(
        subject=subject,
        topic=topic,
        grade=grade,
        character=character,
    )

    # Save to database
    lesson_plan = LessonPlan(
        teacher_id=teacher.id,
        title=f"{subject.replace('_', ' ').title()}: {topic}",
        subject=subject,
        topic=topic,
        grade=grade,
        sections_json=json.dumps(lesson.get("sections", {})),
        full_text=lesson.get("raw", ""),
    )
    db.session.add(lesson_plan)
    db.session.commit()

    return jsonify({
        "success": True,
        "lesson_plan_id": lesson_plan.id,
        "redirect_url": f"/teacher/lesson_plans/{lesson_plan.id}",
    }), 201

# ============================================================
# TEACHER - LESSON PLAN LIBRARY
# ============================================================

@app.route("/teacher/lesson_plans")
def teacher_lesson_plans():
    """View all saved lesson plans for the logged-in teacher."""
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    lesson_plans = LessonPlan.query.filter_by(teacher_id=teacher.id).order_by(LessonPlan.created_at.desc()).all()

    return render_template(
        "lesson_plans_library.html",
        teacher=teacher,
        lesson_plans=lesson_plans,
        is_owner=is_owner(teacher),
    )


@app.route("/teacher/lesson_plans/<int:lesson_id>")
def view_lesson_plan(lesson_id):
    """View a single lesson plan with options to edit, regenerate, export."""
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    lesson = LessonPlan.query.get_or_404(lesson_id)
    if not is_owner(teacher) and lesson.teacher_id != teacher.id:
        flash("Not authorized to view this lesson plan.", "error")
        return redirect("/teacher/lesson_plans")

    # Parse sections from JSON
    sections = json.loads(lesson.sections_json) if lesson.sections_json else {}

    return render_template(
        "lesson_plan_view.html",
        teacher=teacher,
        lesson=lesson,
        sections=sections,
        is_owner=is_owner(teacher),
    )


@app.route("/teacher/lesson_plans/<int:lesson_id>/edit", methods=["GET", "POST"])
def edit_lesson_plan(lesson_id):
    """Edit lesson plan sections manually."""
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    lesson = LessonPlan.query.get_or_404(lesson_id)
    if not is_owner(teacher) and lesson.teacher_id != teacher.id:
        flash("Not authorized to edit this lesson plan.", "error")
        return redirect("/teacher/lesson_plans")

    if request.method == "POST":
        # Update sections with new 9-section teacher format
        sections = {
            "learning_objectives": safe_text(request.form.get("learning_objectives", ""), 5000),
            "materials_needed": safe_text(request.form.get("materials_needed", ""), 5000),
            "introduction_hook": safe_text(request.form.get("introduction_hook", ""), 5000),
            "main_teaching_points": safe_text(request.form.get("main_teaching_points", ""), 5000),
            "activities_practice": safe_text(request.form.get("activities_practice", ""), 5000),
            "assessment": safe_text(request.form.get("assessment", ""), 5000),
            "differentiation_tips": safe_text(request.form.get("differentiation_tips", ""), 5000),
            "christian_integration": safe_text(request.form.get("christian_integration", ""), 5000),
            "closure_summary": safe_text(request.form.get("closure_summary", ""), 5000),
        }
        
        # Rebuild full text with new format
        full_text = f"""SECTION 1 - LEARNING OBJECTIVES
{sections['learning_objectives']}

SECTION 2 - MATERIALS NEEDED
{sections['materials_needed']}

SECTION 3 - INTRODUCTION/HOOK
{sections['introduction_hook']}

SECTION 4 - MAIN TEACHING POINTS
{sections['main_teaching_points']}

SECTION 5 - ACTIVITIES/PRACTICE
{sections['activities_practice']}

SECTION 6 - ASSESSMENT
{sections['assessment']}

SECTION 7 - DIFFERENTIATION TIPS
{sections['differentiation_tips']}

SECTION 8 - CHRISTIAN INTEGRATION
{sections['christian_integration']}

SECTION 9 - CLOSURE/SUMMARY
{sections['closure_summary']}"""

        lesson.sections_json = json.dumps(sections)
        lesson.full_text = full_text
        lesson.title = safe_text(request.form.get("title", lesson.title), 200)
        db.session.commit()
        
        flash("Lesson plan updated.", "info")
        return redirect(f"/teacher/lesson_plans/{lesson_id}")

    sections = json.loads(lesson.sections_json) if lesson.sections_json else {}

    return render_template(
        "lesson_plan_edit.html",
        teacher=teacher,
        lesson=lesson,
        sections=sections,
        is_owner=is_owner(teacher),
    )


@csrf.exempt
@app.route("/teacher/lesson_plans/<int:lesson_id>/regenerate_section", methods=["POST"])
def regenerate_lesson_section(lesson_id):
    """Regenerate a specific section of a lesson plan."""
    teacher = get_current_teacher()
    if not teacher:
        return jsonify({"error": "Not authenticated"}), 401

    lesson = LessonPlan.query.get_or_404(lesson_id)
    if not is_owner(teacher) and lesson.teacher_id != teacher.id:
        return jsonify({"error": "Not authorized"}), 403

    data = request.get_json() or {}
    section_name = data.get("section")

    valid_sections = [
        "learning_objectives", "materials_needed", "introduction_hook",
        "main_teaching_points", "activities_practice", "assessment",
        "differentiation_tips", "christian_integration", "closure_summary"
    ]
    
    if section_name not in valid_sections:
        return jsonify({"error": "Invalid section name"}), 400

    # Regenerate full lesson and extract the requested section
    new_lesson = generate_lesson_plan(
        subject=lesson.subject,
        topic=lesson.topic,
        grade=lesson.grade,
        character="everly",
    )

    new_sections = new_lesson.get("sections", {})
    new_section_content = new_sections.get(section_name, "")

    return jsonify({
        "success": True,
        "section": section_name,
        "content": new_section_content,
    }), 200


@app.route("/teacher/lesson_plans/<int:lesson_id>/print")
def print_lesson_plan(lesson_id):
    """Print-friendly view of lesson plan."""
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    lesson = LessonPlan.query.get_or_404(lesson_id)
    if not is_owner(teacher) and lesson.teacher_id != teacher.id:
        flash("Not authorized to view this lesson plan.", "error")
        return redirect("/teacher/lesson_plans")

    sections = json.loads(lesson.sections_json) if lesson.sections_json else {}

    return render_template(
        "lesson_plan_print.html",
        lesson=lesson,
        sections=sections,
    )


# ============================================================
# GRADEBOOK - TEACHER & HOMESCHOOL
# ============================================================

@app.route("/teacher/gradebook")
def teacher_gradebook():
    """Teacher gradebook - view all classes and their assignments."""
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    # Get all classes for this teacher
    if is_owner(teacher):
        classes = Class.query.all()
    else:
        classes = Class.query.filter_by(teacher_id=teacher.id).all()

    # For each class, get assignment summary with average scores
    class_data = []
    for cls in classes:
        assignments = AssignedPractice.query.filter_by(class_id=cls.id, is_published=True).all()
        
        assignment_summary = []
        for assignment in assignments:
            # Get all submissions for this assignment
            submissions = StudentSubmission.query.filter_by(assignment_id=assignment.id, status='graded').all()
            
            if submissions:
                avg_score = sum(s.score for s in submissions if s.score) / len(submissions)
                graded_count = len(submissions)
            else:
                avg_score = None
                graded_count = 0
            
            assignment_summary.append({
                'assignment': assignment,
                'avg_score': avg_score,
                'graded_count': graded_count,
                'total_students': len(cls.students)
            })
        
        class_data.append({
            'class': cls,
            'assignments': assignment_summary,
            'student_count': len(cls.students)
        })

    return render_template(
        "gradebook.html",
        teacher=teacher,
        class_data=class_data,
        is_owner=is_owner(teacher),
    )


@app.route("/teacher/gradebook/class/<int:class_id>")
def teacher_gradebook_class(class_id):
    """Gradebook for a specific class - detailed view with all students and assignments."""
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    cls = Class.query.get_or_404(class_id)
    
    # Check authorization
    if not is_owner(teacher) and cls.teacher_id != teacher.id:
        flash("Not authorized to view this class.", "error")
        return redirect("/teacher/gradebook")

    # Get all published assignments for this class
    assignments = AssignedPractice.query.filter_by(class_id=class_id, is_published=True).order_by(AssignedPractice.due_date).all()
    
    # Get all students in this class
    students = cls.students
    
    # Build gradebook matrix: students x assignments
    gradebook_data = []
    for student in students:
        student_row = {
            'student': student,
            'grades': {},
            'average': None
        }
        
        total_score = 0
        graded_count = 0
        
        for assignment in assignments:
            submission = StudentSubmission.query.filter_by(
                student_id=student.id,
                assignment_id=assignment.id
            ).first()
            
            if submission and submission.status == 'graded' and submission.score is not None:
                student_row['grades'][assignment.id] = {
                    'score': submission.score,
                    'status': 'graded',
                    'submission': submission
                }
                total_score += submission.score
                graded_count += 1
            elif submission and submission.status == 'submitted':
                student_row['grades'][assignment.id] = {
                    'score': None,
                    'status': 'submitted',
                    'submission': submission
                }
            else:
                student_row['grades'][assignment.id] = {
                    'score': None,
                    'status': 'not_submitted',
                    'submission': None
                }
        
        if graded_count > 0:
            student_row['average'] = total_score / graded_count
        
        gradebook_data.append(student_row)
    
    # Calculate class averages per assignment
    assignment_averages = {}
    for assignment in assignments:
        submissions = StudentSubmission.query.filter_by(
            assignment_id=assignment.id,
            status='graded'
        ).all()
        
        if submissions:
            scores = [s.score for s in submissions if s.score is not None]
            if scores:
                assignment_averages[assignment.id] = sum(scores) / len(scores)
            else:
                assignment_averages[assignment.id] = None
        else:
            assignment_averages[assignment.id] = None

    return render_template(
        "gradebook_class.html",
        teacher=teacher,
        cls=cls,
        assignments=assignments,
        gradebook_data=gradebook_data,
        assignment_averages=assignment_averages,
        is_owner=is_owner(teacher),
    )


@app.route("/homeschool/gradebook")
def homeschool_gradebook():
    """Homeschool gradebook - view student progress grouped by subject."""
    init_user()
    
    parent_id = session.get("parent_id")
    
    # Temporary debug - auto-login test homeschool parent
    if not parent_id:
        test_parent = Parent.query.filter_by(email='homeschool@test.com').first()
        if test_parent:
            session["parent_id"] = test_parent.id
            session["user_role"] = "parent"
            session["parent_name"] = test_parent.name if hasattr(test_parent, 'name') else "Homeschool Parent"
            parent_id = test_parent.id
    
    if not session.get("bypass_auth"):
        access_check = check_subscription_access("parent")
        if access_check != True:
            return access_check

    if not parent_id:
        flash("Please log in as a parent.", "error")
        return redirect("/parent/login")
    
    parent = Parent.query.get(parent_id)
    if not parent:
        return redirect("/parent/login")
    
    # Check if parent has teacher features (homeschool plan)
    _, _, _, has_teacher_features = get_parent_plan_limits(parent)
    
    if not has_teacher_features:
        flash("Gradebook is only available with Homeschool plans.", "warning")
        return redirect("/homeschool/dashboard")
    
    # Get all students linked to this parent
    students = parent.students
    
    # Group assessment results and submissions by student
    student_data = []
    for student in students:
        # Get submissions for any assignments (if we create homeschool assignments)
        submissions = StudentSubmission.query.filter_by(student_id=student.id, status='graded').all()
        
        # Get assessment results (from practice missions)
        results = AssessmentResult.query.filter_by(student_id=student.id).order_by(AssessmentResult.created_at.desc()).limit(20).all()
        
        # Calculate subject averages
        subject_scores = {}
        for result in results:
            if result.subject not in subject_scores:
                subject_scores[result.subject] = []
            if result.score_percent is not None:
                subject_scores[result.subject].append(result.score_percent)
        
        subject_averages = {
            subject: sum(scores) / len(scores) if scores else None
            for subject, scores in subject_scores.items()
        }
        
        student_data.append({
            'student': student,
            'submissions': submissions,
            'subject_averages': subject_averages,
            'overall_average': student.average_score
        })
    
    return render_template(
        "homeschool_gradebook.html",
        parent=parent,
        student_data=student_data,
    )


@app.route("/teacher/lesson_plans/<int:lesson_id>/export/pdf")
def export_lesson_plan_pdf(lesson_id):
    """Export lesson plan as PDF (placeholder for now - can use reportlab later)."""
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    lesson = LessonPlan.query.get_or_404(lesson_id)
    if not is_owner(teacher) and lesson.teacher_id != teacher.id:
        flash("Not authorized to export this lesson plan.", "error")
        return redirect("/teacher/lesson_plans")

    # For now, redirect to print view - can add PDF generation later
    return redirect(f"/teacher/lesson_plans/{lesson_id}/print")


# ============================================================
# TEACHER - MESSAGING SYSTEM
# ============================================================

@app.route("/teacher/messages")
def teacher_messages():
    """Teacher inbox - view all messages from parents."""
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")
    
    # Get all messages where teacher is recipient
    received = Message.query.filter_by(
        recipient_type='teacher',
        recipient_id=teacher.id
    ).order_by(Message.created_at.desc()).all()
    
    # Get all messages teacher sent
    sent = Message.query.filter_by(
        sender_type='teacher',
        sender_id=teacher.id
    ).order_by(Message.created_at.desc()).all()
    
    # Count unread
    unread_count = Message.query.filter_by(
        recipient_type='teacher',
        recipient_id=teacher.id,
        is_read=False
    ).count()
    
    return render_template(
        "teacher_messages.html",
        teacher=teacher,
        received=received,
        sent=sent,
        unread_count=unread_count,
        is_owner=is_owner(teacher),
    )


@app.route("/teacher/messages/<int:message_id>")
def teacher_view_message(message_id):
    """View a specific message."""
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")
    
    message = Message.query.get_or_404(message_id)
    
    # Check authorization
    is_recipient = (message.recipient_type == 'teacher' and message.recipient_id == teacher.id)
    is_sender = (message.sender_type == 'teacher' and message.sender_id == teacher.id)
    
    if not (is_recipient or is_sender or is_owner(teacher)):
        flash("Not authorized to view this message.", "error")
        return redirect("/teacher/messages")
    
    # Mark as read if recipient
    if is_recipient and not message.is_read:
        message.is_read = True
        db.session.commit()
    
    # Get student info
    student = Student.query.get(message.student_id) if message.student_id else None
    
    # Get sender/recipient names
    if message.sender_type == 'parent':
        sender = Parent.query.get(message.sender_id)
        sender_name = sender.name if sender else "Unknown Parent"
    else:
        sender = Teacher.query.get(message.sender_id)
        sender_name = sender.name if sender else "Unknown Teacher"
    
    if message.recipient_type == 'parent':
        recipient = Parent.query.get(message.recipient_id)
        recipient_name = recipient.name if recipient else "Unknown Parent"
    else:
        recipient = Teacher.query.get(message.recipient_id)
        recipient_name = recipient.name if recipient else "Unknown Teacher"
    
    # Parse progress report if exists
    progress_report = None
    if message.progress_report_json:
        progress_report = json.loads(message.progress_report_json)
    
    return render_template(
        "view_message.html",
        teacher=teacher,
        message=message,
        student=student,
        sender_name=sender_name,
        recipient_name=recipient_name,
        progress_report=progress_report,
        is_owner=is_owner(teacher),
    )


@app.route("/teacher/messages/compose", methods=["GET", "POST"])
def teacher_compose_message():
    """Compose a new message to a parent."""
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")
    
    if request.method == "POST":
        student_id = request.form.get("student_id")
        subject = safe_text(request.form.get("subject", ""), 255)
        body = safe_text(request.form.get("body", ""), 5000)
        
        if not student_id or not subject or not body:
            flash("Student, subject, and message are required.", "error")
            return redirect("/teacher/messages/compose")
        
        student = Student.query.get(int(student_id))
        if not student or not student.parent_id:
            flash("Student not found or has no parent account.", "error")
            return redirect("/teacher/messages/compose")
        
        # Create message
        message = Message(
            sender_type='teacher',
            sender_id=teacher.id,
            recipient_type='parent',
            recipient_id=student.parent_id,
            student_id=student.id,
            subject=subject,
            body=body,
        )
        db.session.add(message)
        db.session.commit()
        
        flash("Message sent successfully!", "info")
        return redirect("/teacher/messages")
    
    # GET - show compose form
    # Get all students with parent accounts
    classes = teacher.classes or []
    students_with_parents = []
    for cls in classes:
        for student in cls.students or []:
            if student.parent_id:
                students_with_parents.append({
                    "id": student.id,
                    "name": student.student_name,
                    "class": cls.class_name,
                    "parent_id": student.parent_id,
                })
    
    return render_template(
        "compose_message.html",
        teacher=teacher,
        students=students_with_parents,
        is_owner=is_owner(teacher),
    )


@app.route("/teacher/send_progress_report/<int:student_id>", methods=["GET", "POST"])
def teacher_send_progress_report(student_id):
    """Send automated progress report to parent."""
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")
    
    student = Student.query.get_or_404(student_id)
    
    # Check authorization
    cls = Class.query.get(student.class_id)
    if not cls or (not is_owner(teacher) and cls.teacher_id != teacher.id):
        flash("Not authorized.", "error")
        return redirect("/teacher/dashboard")
    
    if not student.parent_id:
        flash("This student has no parent account.", "error")
        return redirect("/teacher/dashboard")
    
    if request.method == "POST":
        # Generate progress report
        from modules.teacher_tools import build_progress_report
        report_data = build_progress_report(student_id)
        
        # Create personalized message
        avg = report_data.get("avg", 0)
        subject = f"Progress Report for {student.student_name}"
        body = f"""Dear Parent,

Here is the latest progress report for {student.student_name}:

Overall Average: {avg:.1f}%
Ability Level: {student.ability_level or 'on_level'}

Recent Performance:
"""
        for result in report_data.get("results", [])[:5]:
            body += f"- {result['subject']}: {result['score']:.0f}% ({result['created_at'][:10]})\n"
        
        body += f"\n{request.form.get('additional_notes', '').strip()}\n\nBest regards,\n{teacher.name}"
        
        # Create message with progress report attached
        message = Message(
            sender_type='teacher',
            sender_id=teacher.id,
            recipient_type='parent',
            recipient_id=student.parent_id,
            student_id=student.id,
            subject=subject,
            body=body,
            progress_report_json=json.dumps(report_data),
        )
        db.session.add(message)
        db.session.commit()
        
        flash(f"Progress report sent to {student.student_name}'s parent!", "info")
        return redirect("/teacher/messages")
    
    # GET - show confirm/customize form
    from modules.teacher_tools import build_progress_report
    report_data = build_progress_report(student_id)
    
    return render_template(
        "send_progress_report.html",
        teacher=teacher,
        student=student,
        report_data=report_data,
        is_owner=is_owner(teacher),
    )


# ============================================================
# TEACHER - TEACHER'S PET AI ASSISTANT (CONTINUED)
# ============================================================

@csrf.exempt
@app.route("/teacher/teachers_pet", methods=["POST"])
def teachers_pet_assistant():
    """Teacher's Pet: AI assistant for teachers to ask questions about CozmicLearning and teaching."""
    teacher = get_current_teacher()
    if not teacher:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json() or {}
    question = safe_text(data.get("question", ""), 2000)
    history = data.get("history", [])

    if not question:
        return jsonify({"error": "Question is required"}), 400

    # Build context about CozmicLearning for Teacher's Pet
    context_prompt = """You are Teacher's Pet, a warm AI assistant for teachers using CozmicLearning.

RESPONSE STYLE - CRITICAL:
• Keep answers SHORT and POWER-PACKED (3-5 sentences max for most questions)
• Get straight to the point - no long introductions
• Use bullet points for lists (max 3-5 items)
• One key Scripture reference when relevant, not multiple verses
• Action-oriented: "Here's what to do..." not theory
• Save long explanations only for complex "how-to" questions

CozmicLearning Quick Reference:
- 11 planets: NumForge (math), AtomSphere (science), FaithRealm (Bible), ChronoCore (history), InkHaven (writing), TruthForge (apologetics), StockStar (investing), CoinQuest (money), TerraNova (general), StoryVerse (reading), PowerGrid (study guide)
- Differentiation: adaptive, gap_fill, mastery, scaffold
- Six-section format includes Christian View in every lesson
- Tools: assign questions, lesson plans, analytics, progress reports

Your Voice:
• Warm but efficient - respect teachers' time"
• Quick encouragement with Scripture when fitting
• Practical tips over long explanations
• Celebrate their calling briefly
• For non-Christians: gracious, brief seed-planting

Examples of GOOD responses:
Q: "How do I use differentiation modes?"
A: "Choose based on student needs: scaffold for struggling students (simpler steps), adaptive for on-level (adjusts difficulty), mastery for advanced (harder challenges). Set it when creating assignments. God gave each child unique gifts - differentiation honors that! (Psalm 139:14)"

Q: "Student won't engage in lessons"
A: "Try these 3 quick wins: 1) Use gamification (tokens/XP motivate!), 2) Let them pick their character, 3) Start with TerraNova for confidence. Pray for them - teaching is spiritual warfare too! Need specific subject ideas?"

Keep it SHORT, HELPFUL, and HOPEFUL."""

    # Build conversation with history
    messages = [{"role": "system", "content": context_prompt}]
    
    # Add previous conversation history (last 10 exchanges to avoid token limit)
    for msg in history[-10:]:
        messages.append(msg)
    
    # Add current question
    messages.append({"role": "user", "content": question})

    try:
        from modules.shared_ai import get_client
        client = get_client()
        
        response = client.responses.create(
            model="gpt-4.1-mini",
            max_output_tokens=800,
            input=messages,
        )
        
        answer = response.output_text.strip()
        
        # Update history
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})
        
        return jsonify({
            "success": True,
            "answer": answer,
            "history": history,
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"AI error: {str(e)}"}), 500

# ============================================================
# STUDENT – TAKE AI–GENERATED DIFFERENTIATED ASSIGNMENT
# ============================================================

@app.route("/assignment/<int:practice_id>/take", methods=["GET"])
def assignment_take(practice_id):
    init_user()

    assignment = AssignedPractice.query.get_or_404(practice_id)

    # Load student + grade level (fallback 8)
    student_id = session.get("student_id")
    student = Student.query.get(student_id) if student_id else None
    grade_level = student.class_ref.grade_level if student and student.class_ref else "8"

    differentiation = getattr(assignment, "differentiation_mode", "none")

    # Generate AI mission
    practice = generate_practice_session(
        topic=assignment.topic or assignment.title,
        subject=assignment.subject or "terra_nova",
        grade_level=grade_level,
        character="nova",  # could be pulled from student later
        differentiation_mode=differentiation,
    )

    session["practice"] = practice
    session["practice_step"] = 0
    session["student_answers"] = []
    session.modified = True

    return redirect(f"/assignment/{practice_id}/step")

@app.route("/assignment/<int:practice_id>/step", methods=["GET", "POST"])
def assignment_step(practice_id):
    init_user()

    assignment = AssignedPractice.query.get_or_404(practice_id)

    practice = session.get("practice")
    step_index = session.get("practice_step", 0)

    if not practice:
        return redirect(f"/assignment/{practice_id}/take")

    steps = practice["steps"]
    total_steps = len(steps)
    step = steps[step_index]

    # ----------------------------------------------------
    # NEW: Calculate progress bar % (1–100)
    # ----------------------------------------------------
    progress_percent = round(((step_index + 1) / total_steps) * 100, 2)

    show_hint = False

    # ----------------------------------------------------
    # POST - student action (answer or hint)
    # ----------------------------------------------------
    if request.method == "POST":

        # -----------------------------
        # Student pressed HINT
        # -----------------------------
        if "hint" in request.form:
            show_hint = True
            return render_template(
                "assignment_step.html",
                assignment=assignment,
                step=step,
                index=step_index,
                total=total_steps,
                show_hint=True,
                submitted=False,
                progress_percent=progress_percent
            )

        # -----------------------------
        # Student submitted an answer
        # -----------------------------
        student_answer = (request.form.get("student_answer") or "").strip().lower()
        correct_answers = [a.lower() for a in step.get("expected", [])]

        step["student_answer"] = student_answer
        step["status"] = "correct" if student_answer in correct_answers else "incorrect"

        session["student_answers"].append(student_answer)
        session["practice_step"] = step_index + 1

        # -----------------------------
        # If final step → summary page
        # -----------------------------
        if step_index + 1 >= total_steps:
            score = sum(1 for s in steps if s.get("status") == "correct")
            score_percent = round((score / total_steps) * 100, 1)

            return render_template(
                "assignment_complete.html",
                assignment=assignment,
                score_percent=score_percent,
                final_message=practice.get("final_message", "Great work!"),
                steps=steps
            )

        return redirect(f"/assignment/{practice_id}/step")

    # ----------------------------------------------------
    # GET - show question normally
    # ----------------------------------------------------
    return render_template(
        "assignment_step.html",
        assignment=assignment,
        step=step,
        index=step_index,
        total=total_steps,
        show_hint=False,
        submitted=False,
        progress_percent=progress_percent
    )

# ============================================================
# CLASS ANALYTICS (TEACHER VIEW) – DB RESULTS ONLY
# ============================================================

@app.route("/teacher/analytics")
def teacher_analytics_overview():
    """General analytics overview showing all classes with summary stats."""
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    # Get all teacher's classes
    if is_owner(teacher):
        classes = Class.query.order_by(Class.class_name).all()
    else:
        classes = Class.query.filter_by(teacher_id=teacher.id).order_by(Class.class_name).all()

    # Build summary stats for each class
    class_summaries = []
    for cls in classes:
        students = cls.students or []
        total_students = len(students)
        
        # Recompute abilities
        for s in students:
            recompute_student_ability(s)
        
        # Ability distribution
        struggling = sum(1 for s in students if (s.ability_level or "").lower() == "struggling")
        on_level = sum(1 for s in students if (s.ability_level or "").lower() == "on_level")
        advanced = sum(1 for s in students if (s.ability_level or "").lower() == "advanced")
        
        # Class average from recent assessments
        recent_scores = (
            db.session.query(func.avg(AssessmentResult.score_percent))
            .join(Student, AssessmentResult.student_id == Student.id)
            .filter(Student.class_id == cls.id)
            .scalar()
        )
        class_avg = round(recent_scores, 1) if recent_scores else 0.0
        
        # Total assessments
        total_assessments = (
            db.session.query(func.count(AssessmentResult.id))
            .join(Student, AssessmentResult.student_id == Student.id)
            .filter(Student.class_id == cls.id)
            .scalar()
        ) or 0
        
        class_summaries.append({
            "class": cls,
            "total_students": total_students,
            "struggling": struggling,
            "on_level": on_level,
            "advanced": advanced,
            "class_avg": class_avg,
            "total_assessments": total_assessments,
        })
    
    return render_template(
        "analytics_overview.html",
        teacher=teacher,
        class_summaries=class_summaries,
        is_owner=is_owner(teacher),
    )


@app.route("/teacher/class/<int:class_id>/analytics")
def teacher_class_analytics(class_id):
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    cls = Class.query.get(class_id)
    if not cls or (not is_owner(teacher) and cls.teacher_id != teacher.id):
        flash("Class not found or not authorized.", "error")
        return redirect("/teacher/dashboard")

    students = cls.students or []

    for s in students:
        recompute_student_ability(s)

    # Subject-level averages
    subject_averages = {}
    rows = (
        db.session.query(
            AssessmentResult.subject,
            func.avg(AssessmentResult.score_percent),
        )
        .join(Student, AssessmentResult.student_id == Student.id)
        .filter(Student.class_id == class_id)
        .group_by(AssessmentResult.subject)
        .all()
    )
    for subj, avg_score in rows:
        subject_averages[subj] = round(avg_score, 1)

    # Ability distribution
    ability_counts = {"struggling": 0, "on_level": 0, "advanced": 0}
    for s in students:
        lvl = (s.ability_level or "on_level").lower()
        if lvl not in ability_counts:
            ability_counts[lvl] = 0
        ability_counts[lvl] += 1

    # Heatmap by topic
    all_results = (
        AssessmentResult.query.join(Student, AssessmentResult.student_id == Student.id)
        .filter(Student.class_id == class_id)
        .all()
    )

    topic_keys = []
    topic_seen = set()
    agg = {}

    for r in all_results:
        subj = (r.subject or "").strip().lower() or "general"
        topic = (r.topic or "").strip() or "General"
        key = f"{subj.title()} | {topic}"

        if key not in topic_seen:
            topic_seen.add(key)
            topic_keys.append(key)

        idx = (r.student_id, key)
        if idx not in agg:
            agg[idx] = {"sum": 0.0, "count": 0}
        agg[idx]["sum"] += r.score_percent or 0.0
        agg[idx]["count"] += 1

    student_topic_matrix = {}
    for (student_id, key), data in agg.items():
        avg_score = data["sum"] / max(data["count"], 1)
        if student_id not in student_topic_matrix:
            student_topic_matrix[student_id] = {}
        student_topic_matrix[student_id][key] = round(avg_score, 1)

    return render_template(
        "class_analytics.html",
        cls=cls,
        students=students,
        subject_averages=subject_averages,
        ability_counts=ability_counts,
        topic_keys=topic_keys,
        matrix=student_topic_matrix,
        is_owner=is_owner(teacher),
    )


@app.route("/teacher/record_result", methods=["POST"])
@csrf.exempt
def teacher_record_result():
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    student_id = request.form.get("student_id", type=int)
    subject = (request.form.get("subject", "") or "general").strip().lower()
    topic = (request.form.get("topic", "") or "General").strip()
    num_correct = int(request.form.get("num_correct") or 0)
    num_questions = int(request.form.get("num_questions") or 1)
    difficulty_level = request.form.get("difficulty_level") or None

    student = Student.query.get(student_id)
    if not student:
        flash("Student not found.", "error")
        return redirect("/teacher/dashboard")

    if not is_owner(teacher) and student.class_ref.teacher_id != teacher.id:
        flash("Not authorized for this student.", "error")
        return redirect("/teacher/dashboard")

    score_percent = (num_correct / max(num_questions, 1)) * 100.0

    result = AssessmentResult(
        student_id=student.id,
        subject=subject,
        topic=topic,
        score_percent=score_percent,
        num_correct=num_correct,
        num_questions=num_questions,
        difficulty_level=difficulty_level or student.ability_level,
    )

    db.session.add(result)
    db.session.commit()

    recompute_student_ability(student)

    flash("Result recorded.", "info")
    return redirect(f"/teacher/class/{student.class_id}/analytics")


@app.route("/teacher/student/<int:student_id>/report")
def teacher_student_report(student_id):
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    student = Student.query.get(student_id)
    if not student:
        flash("Student not found.", "error")
        return redirect("/teacher/dashboard")

    if not is_owner(teacher) and student.class_ref.teacher_id != teacher.id:
        flash("Not authorized for this student.", "error")
        return redirect("/teacher/dashboard")

    results = (
        AssessmentResult.query.filter_by(student_id=student_id)
        .order_by(AssessmentResult.created_at.desc())
        .all()
    )

    return render_template(
        "student_report.html",
        student=student,
        results=results,
        is_owner=is_owner(teacher),
    )


# ============================================================
# CHARACTER SELECT + GRADE + SUBJECT Q&A
# ============================================================

@app.route("/choose-character")
def choose_character():
    init_user()
    return render_template("choose_character.html", characters=get_all_characters())


@app.route("/select-character", methods=["POST"])
def select_character():
    init_user()
    session["character"] = request.form.get("character") or "everly"
    return redirect("/dashboard")


@app.route("/choose-grade")
def choose_grade():
    init_user()
    subject = request.args.get("subject")
    return render_template("subject_select_form.html", subject=subject)


@app.route("/ask-question")
def ask_question():
    init_user()
    return render_template(
        "ask_question.html",
        subject=request.args.get("subject"),
        grade=request.args.get("grade"),
        character=session["character"],
        characters=get_all_characters(),
        subjects=SUBJECT_LABELS,
    )


@app.route("/subject", methods=["POST"])
def subject_answer():
    init_user()
    
    # Check subscription status first
    user_role = session.get("user_role")
    if user_role in ["student", "parent", "teacher"]:
        access_check = check_subscription_access(user_role)
        if access_check != True:
            return access_check  # Redirect to trial_expired

    # Check question limit for Basic plan students
    allowed, remaining, limit = check_question_limit()
    if not allowed:
        flash(f"You've reached your monthly limit of {limit} questions. Upgrade to Premium for unlimited access!", "warning")
        return redirect("/plans")

    grade = request.form.get("grade")
    subject = request.form.get("subject")
    question = request.form.get("question")
    character = session["character"]
    
    # CONTENT MODERATION - Check question safety
    student_id = session.get("user_id")
    moderation_result = moderate_content(question, student_id=student_id, context="question")
    
    # Log the question (flagged or not)
    log_entry = QuestionLog(
        student_id=student_id,
        question_text=question,
        sanitized_text=moderation_result.get("sanitized_text"),
        subject=subject,
        context="question",
        grade_level=grade,
        flagged=moderation_result.get("flagged", False),
        allowed=moderation_result.get("allowed", True),
        moderation_reason=moderation_result.get("reason"),
        moderation_data_json=str(moderation_result.get("moderation_data", {})),
        severity=moderation_result.get("severity", "low")
    )
    db.session.add(log_entry)
    db.session.commit()
    
    # If content was blocked, show error and don't process
    if not moderation_result["allowed"]:
        warning = moderation_result.get("warning")
        if warning:
            flash(warning, "warning")
        flash(moderation_result.get("reason", "Your question could not be processed."), "error")
        
        # High severity = notify parent immediately
        if moderation_result.get("severity") == "high":
            try:
                student = Student.query.get(student_id)
                if student and student.parent_id:
                    parent = Parent.query.get(student.parent_id)
                    if parent:
                        # Send immediate notification
                        from flask_mail import Message as EmailMessage
                        msg = EmailMessage(
                            subject=f"⚠️ URGENT: High-Risk Content Alert for {student.student_name}",
                            sender=app.config["MAIL_DEFAULT_SENDER"],
                            recipients=[parent.email]
                        )
                        msg.body = f"""URGENT ALERT

Your student {student.student_name} attempted to submit high-risk content:

Question: "{question[:200]}"
Date: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p')}
Severity: HIGH
Reason: {moderation_result.get('reason')}

This content was automatically blocked and flagged for immediate review.

Please discuss appropriate online behavior with your student.

CozmicLearning Team
"""
                        mail.send(msg)
                        log_entry.parent_notified = True
                        log_entry.parent_notified_at = datetime.utcnow()
                        db.session.commit()
            except Exception as e:
                app.logger.error(f"Failed to send high-risk notification: {e}")
        
        return redirect("/subjects")

    session["grade"] = grade

    session["progress"].setdefault(subject, {"questions": 0, "correct": 0})
    session["progress"][subject]["questions"] += 1

    if subject == "power_grid":
        return redirect(f"/ask-question?subject=power_grid&grade={grade}")

    func = subject_map.get(subject)
    if func is None:
        flash("Unknown subject selected.", "error")
        return redirect("/subjects")

    result = func(question, grade, character)
    answer = result.get("raw_text") if isinstance(result, dict) else result
    
    # Update log with AI response
    log_entry.ai_response = answer[:5000]  # Store first 5000 chars
    db.session.commit()

    session["conversation"] = []
    session.modified = True

    add_xp(20)
    session["tokens"] += 2
    
    # Log question activity
    student_id = session.get("student_id")
    if student_id:
        try:
            from modules.achievement_helper import log_activity
            log_activity(
                student_id=student_id,
                activity_type="question_answered",
                subject=subject,
                description=f"Asked a question in {SUBJECT_LABELS.get(subject, subject)}",
                xp_earned=20
            )
        except Exception as e:
            print(f"Failed to log question activity: {e}")
    
    # Increment question count for Basic plan tracking
    increment_question_count()

    return render_template(
        "subject.html",
        subject=subject,
        grade=grade,
        question=question,
        answer=answer,
        character=character,
        conversation=session["conversation"],
        pdf_url=None,
        subjects=SUBJECT_LABELS,
    )


# ============================================================
# FOLLOWUP / DEEP STUDY (CHAT MODES)
# ============================================================

@app.route("/followup_message", methods=["POST"])
@csrf.exempt
def followup_message():
    init_user()
    
    # Check subscription status first
    user_role = session.get("user_role")
    if user_role in ["student", "parent", "teacher"]:
        access_check = check_subscription_access(user_role)
        if access_check != True:
            return jsonify({"error": "Your trial has expired. Please upgrade to continue.", "trial_expired": True})

    # Check question limit for Basic plan students
    allowed, remaining, limit = check_question_limit()
    if not allowed:
        return jsonify({"error": f"Monthly limit of {limit} questions reached. Upgrade to Premium for unlimited access!", "upgrade_required": True})

    data = request.get_json() or {}
    grade = data.get("grade")
    character = data.get("character") or session["character"]
    message = data.get("message", "")
    
    # CONTENT MODERATION
    student_id = session.get("user_id")
    moderation_result = moderate_content(message, student_id=student_id, context="chat")
    
    # Log the message
    log_entry = QuestionLog(
        student_id=student_id,
        question_text=message,
        sanitized_text=moderation_result.get("sanitized_text"),
        context="deep_study_chat",
        grade_level=grade,
        flagged=moderation_result.get("flagged", False),
        allowed=moderation_result.get("allowed", True),
        moderation_reason=moderation_result.get("reason"),
        moderation_data_json=str(moderation_result.get("moderation_data", {})),
        severity=moderation_result.get("severity", "low")
    )
    db.session.add(log_entry)
    db.session.commit()
    
    # If blocked, return error
    if not moderation_result["allowed"]:
        return jsonify({
            "error": moderation_result.get("reason", "Message could not be processed."),
            "warning": moderation_result.get("warning"),
            "severity": moderation_result.get("severity")
        })

    conversation = session.get("conversation", [])
    conversation.append({"role": "user", "content": message})

    reply = study_helper.deep_study_chat(conversation, grade, character)
    reply_text = reply.get("raw_text") if isinstance(reply, dict) else reply
    
    # Update log with AI response
    log_entry.ai_response = reply_text[:5000]
    db.session.commit()

    conversation.append({"role": "assistant", "content": reply_text})
    session["conversation"] = conversation
    session.modified = True
    
    # Increment question count
    increment_question_count()

    return jsonify({"reply": reply_text})


@app.route("/deep_study_message", methods=["POST"])
@csrf.exempt
def deep_study_message():
    init_user()
    
    # Check subscription status first
    user_role = session.get("user_role")
    if user_role in ["student", "parent", "teacher"]:
        access_check = check_subscription_access(user_role)
        if access_check != True:
            return jsonify({"error": "Your trial has expired. Please upgrade to continue.", "trial_expired": True})

    # Check question limit for Basic plan students
    allowed, remaining, limit = check_question_limit()
    if not allowed:
        return jsonify({"error": f"Monthly limit of {limit} questions reached. Upgrade to Premium for unlimited access!", "upgrade_required": True})

    data = request.get_json() or {}
    message = data.get("message", "")

    grade = session.get("grade", "8")
    character = session.get("character", "everly")
    
    # CONTENT MODERATION
    student_id = session.get("user_id")
    moderation_result = moderate_content(message, student_id=student_id, context="deep_study_chat")
    
    # Log the message
    log_entry = QuestionLog(
        student_id=student_id,
        question_text=message,
        sanitized_text=moderation_result.get("sanitized_text"),
        context="deep_study_message",
        grade_level=grade,
        flagged=moderation_result.get("flagged", False),
        allowed=moderation_result.get("allowed", True),
        moderation_reason=moderation_result.get("reason"),
        moderation_data_json=str(moderation_result.get("moderation_data", {})),
        severity=moderation_result.get("severity", "low")
    )
    db.session.add(log_entry)
    db.session.commit()
    
    # If blocked, return error
    if not moderation_result["allowed"]:
        return jsonify({
            "error": moderation_result.get("reason", "Message could not be processed."),
            "warning": moderation_result.get("warning"),
            "severity": moderation_result.get("severity")
        })

    conversation = session.get("deep_study_chat", [])
    conversation.append({"role": "user", "content": message})

    dialogue = ""
    for turn in conversation:
        speaker = "Student" if turn["role"] == "user" else "Tutor"
        dialogue += f"{speaker}: {turn['content']}\n"

    prompt = f"""
You are the DEEP STUDY TUTOR.
Warm, patient, conversational.

GRADE LEVEL: {grade}

Conversation so far:
{dialogue}

Rules:
• Only answer last student message
• No long essays
• No repeating study guide
• Encourage deeper thinking
"""

    reply = study_buddy_ai(prompt, grade, character)
    reply_text = reply.get("raw_text") if isinstance(reply, dict) else reply
    
    # Update log with AI response
    log_entry.ai_response = reply_text[:5000]
    db.session.commit()

    conversation.append({"role": "assistant", "content": reply_text})
    session["deep_study_chat"] = conversation
    session.modified = True
    
    # Increment question count
    increment_question_count()

    return jsonify({"reply": reply_text})


# ============================================================
# POWERGRID STUDY GUIDE + PDF
# ============================================================

@app.route("/powergrid_submit", methods=["POST"])
@csrf.exempt
def powergrid_submit():
    init_user()

    grade = request.form.get("grade")
    topic = request.form.get("topic", "").strip()
    url_input = request.form.get("url", "").strip()
    youtube_url = request.form.get("youtube_url", "").strip()
    study_mode = request.form.get("study_mode", "standard")  # quick, standard, deep, socratic
    learning_style = request.form.get("learning_style", "balanced")  # visual, auditory, kinesthetic, balanced
    
    uploaded_files = request.files.getlist("file")  # Multiple files support

    session["grade"] = grade

    text_parts = []
    
    # Process URL import
    if url_input:
        try:
            import requests
            from bs4 import BeautifulSoup
            response = requests.get(url_input, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            # Extract main content (simplified - would need better parsing)
            for script in soup(["script", "style"]):
                script.decompose()
            web_text = soup.get_text()
            text_parts.append(f"--- Content from {url_input} ---\n{web_text[:5000]}")  # Limit to 5000 chars
        except Exception as e:
            app.logger.error(f"URL import error: {e}")
            text_parts.append(f"Could not import from URL: {str(e)}")
    
    # Process YouTube transcript
    if youtube_url:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            import re
            # Extract video ID
            video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', youtube_url)
            if video_id_match:
                video_id = video_id_match.group(1)
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                transcript_text = ' '.join([entry['text'] for entry in transcript])
                text_parts.append(f"--- YouTube Transcript ---\n{transcript_text}")
        except Exception as e:
            app.logger.error(f"YouTube transcript error: {e}")
            text_parts.append(f"Could not extract YouTube transcript: {str(e)}")
    
    # Process uploaded files (multiple files)
    if uploaded_files and uploaded_files[0].filename:
        for uploaded in uploaded_files:
            if not uploaded.filename:
                continue
                
            ext = uploaded.filename.lower()
            path = os.path.join("/tmp", uploaded.filename)
            uploaded.save(path)

            try:
                if ext.endswith(".txt"):
                    with open(path, "r", encoding='utf-8') as f:
                        text_parts.append(f"--- From {uploaded.filename} ---\n{f.read()}")
                
                elif ext.endswith(".pdf"):
                    try:
                        from PyPDF2 import PdfReader
                        pdf = PdfReader(path)
                        pdf_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                        text_parts.append(f"--- From {uploaded.filename} ---\n{pdf_text}")
                    except Exception as e:
                        text_parts.append(f"Could not read PDF {uploaded.filename}: {str(e)}")
                
                elif ext.endswith((".docx", ".doc")):
                    try:
                        from docx import Document
                        doc = Document(path)
                        docx_text = "\n".join([para.text for para in doc.paragraphs])
                        text_parts.append(f"--- From {uploaded.filename} ---\n{docx_text}")
                    except Exception as e:
                        text_parts.append(f"Could not read DOCX {uploaded.filename}: {str(e)}")
                
                elif ext.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
                    try:
                        import pytesseract
                        from PIL import Image
                        img = Image.open(path)
                        ocr_text = pytesseract.image_to_string(img)
                        text_parts.append(f"--- OCR from {uploaded.filename} ---\n{ocr_text}")
                    except Exception as e:
                        text_parts.append(f"Could not OCR image {uploaded.filename}: {str(e)}")
                
                else:
                    text_parts.append(f"Unsupported file type: {uploaded.filename}")
                    
            except Exception as e:
                app.logger.error(f"File processing error for {uploaded.filename}: {e}")
                text_parts.append(f"Error processing {uploaded.filename}")
    
    # Add manual topic if provided
    if topic:
        # CONTENT MODERATION for topic
        student_id = session.get("user_id")
        moderation_result = moderate_content(topic, student_id=student_id, context="powergrid")
        
        # Log the topic request
        log_entry = QuestionLog(
            student_id=student_id,
            question_text=topic,
            sanitized_text=moderation_result.get("sanitized_text"),
            subject="power_grid",
            context="powergrid",
            grade_level=grade,
            flagged=moderation_result.get("flagged", False),
            allowed=moderation_result.get("allowed", True),
            moderation_reason=moderation_result.get("reason"),
            moderation_data_json=str(moderation_result.get("moderation_data", {})),
            severity=moderation_result.get("severity", "low")
        )
        db.session.add(log_entry)
        db.session.commit()
        
        # If blocked, redirect with error
        if not moderation_result["allowed"]:
            warning = moderation_result.get("warning")
            if warning:
                flash(warning, "warning")
            flash(moderation_result.get("reason", "Topic could not be processed."), "error")
            return redirect("/powergrid")
        
        text_parts.append(f"--- Topic Request ---\n{topic}")
    
    # Combine all text sources with length limits to prevent memory issues
    if text_parts:
        combined_text = "\n\n".join(text_parts)
        # Limit total input to 15000 characters to prevent timeout/memory issues
        if len(combined_text) > 15000:
            combined_text = combined_text[:15000] + "\n\n[Content truncated due to length...]"
    else:
        combined_text = "No content provided."

    # Generate study guide with mode and style
    study_guide = study_helper.generate_powergrid_master_guide(
        combined_text, grade, session["character"], 
        mode=study_mode, learning_style=learning_style
    )
    
    # Update log with AI response if topic was provided
    if topic and 'log_entry' in locals():
        log_entry.ai_response = study_guide[:5000]
        db.session.commit()

    # Generate PDF
    import uuid
    from textwrap import wrap

    pdf_path = f"/tmp/study_guide_{uuid.uuid4().hex}.pdf"

    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch

        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        y = height - 50

        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, y, "PowerGrid Master Study Guide")
        y -= 30
        c.setFont("Helvetica", 10)
        c.drawString(40, y, f"Generated: {datetime.now().strftime('%B %d, %Y')}")
        y -= 30

        # Content
        c.setFont("Helvetica", 11)
        for line in study_guide.split("\n"):
            for wrapped in wrap(line if line else " ", 95):
                if y < 40:
                    c.showPage()
                    y = height - 50
                    c.setFont("Helvetica", 11)
                c.drawString(40, y, wrapped)
                y -= 15

        c.save()
        session["study_pdf"] = pdf_path
        pdf_url = "/download_study_guide"
    except Exception as e:
        app.logger.error(f"PDF generation error: {e}")
        pdf_url = None

    session["conversation"] = []
    session["deep_study_chat"] = []
    session.modified = True

    return render_template(
        "powergrid.html",
        subject="power_grid",
        grade=grade,
        question=topic or "Multi-source study guide",
        answer=study_guide,
        character=session["character"],
        conversation=session["conversation"],
        pdf_url=pdf_url,
    )


@app.route("/download_study_guide")
def download_study_guide():
    pdf = session.get("study_pdf")
    if not pdf or not os.path.exists(pdf):
        return "PDF not found."
    return send_file(pdf, as_attachment=True)


# ============================================================
# GENERIC PRACTICE MODE (NOT TIED TO ASSIGNMENTS)
# ============================================================

@app.route("/practice")
def practice():
    init_user()

    subject = request.args.get("subject", "")
    topic = request.args.get("topic", "")
    character = session.get("character", "everly")
    grade = session.get("grade", "8")

    return render_template(
        "practice.html",
        subject=subject,
        topic=topic,
        character=character,
        grade=grade,
        subjects=SUBJECT_LABELS,
    )


@app.route("/start_practice", methods=["POST"])
@csrf.exempt
def start_practice():
    init_user()

    data = request.get_json() or {}
    topic = data.get("topic", "").strip()
    subject = data.get("subject", "")
    grade = session.get("grade", "8")
    character = session.get("character", "everly")

    practice_data = generate_practice_session(
        topic=topic,
        subject=subject,
        grade_level=grade,
        character=character,
        differentiation_mode="none",  # generic practice, no teacher mode
    )

    steps = practice_data.get("steps") or []
    if not steps:
        return jsonify(
            {
                "status": "error",
                "message": "No practice questions were generated. Try a different topic.",
                "character": character,
            }
        )

    progress = []
    for _ in steps:
        progress.append(
            {"attempts": 0, "status": "unanswered", "last_answer": "", "chat": []}
        )

    session["practice"] = practice_data
    session["practice_progress"] = progress
    session["practice_step"] = 0
    session["practice_attempts"] = 0
    session.modified = True

    first = steps[0]

    return jsonify(
        {
            "status": "ok",
            "index": 0,
            "total": len(steps),
            "prompt": first.get("prompt", "Let's start practicing!"),
            "type": first.get("type", "free"),
            "choices": first.get("choices", []),
            "character": character,
            "last_answer": "",
            "chat": [],
        }
    )


@app.route("/navigate_question", methods=["POST"])
@csrf.exempt
def navigate_question():
    init_user()

    data = request.get_json() or {}
    index = int(data.get("index", 0))

    practice_data = session.get("practice")
    progress = session.get("practice_progress", [])
    character = session.get("character", "everly")

    if not practice_data:
        return jsonify(
            {
                "status": "error",
                "message": "No active practice mission.",
                "character": character,
            }
        )

    steps = practice_data.get("steps") or []
    total = len(steps)

    if index < 0:
        index = 0
    if index >= total:
        index = total - 1

    step = steps[index]
    if index >= len(progress):
        progress.extend(
            [
                {
                    "attempts": 0,
                    "status": "unanswered",
                    "last_answer": "",
                    "chat": [],
                }
                for _ in range(index - len(progress) + 1)
            ]
        )

    state = progress[index]

    session["practice_step"] = index
    session["practice_progress"] = progress
    session.modified = True

    return jsonify(
        {
            "status": "ok",
            "index": index,
            "total": total,
            "prompt": step.get("prompt", ""),
            "type": step.get("type", "free"),
            "choices": step.get("choices", []),
            "last_answer": state.get("last_answer", ""),
            "question_status": state.get("status", "unanswered"),
            "chat": state.get("chat", []),
            "character": character,
        }
    )


@app.route("/practice_step", methods=["POST"])
@csrf.exempt
def practice_step():
    init_user()

    data = request.get_json() or {}
    user_answer_raw = data.get("answer") or ""
    user_answer_stripped = user_answer_raw.strip()

    practice_data = session.get("practice")
    index = session.get("practice_step", 0)
    character = session.get("character", "everly")

    if not practice_data:
        return jsonify(
            {
                "status": "error",
                "message": "Practice session not found. Try starting a new practice mission.",
                "character": character,
            }
        )

    steps = practice_data.get("steps") or []
    if not steps or index < 0 or index >= len(steps):
        return jsonify(
            {
                "status": "finished",
                "message": practice_data.get(
                    "final_message", "Mission complete!"
                ),
                "character": character,
            }
        )

    step = steps[index]
    progress = session.get("practice_progress", [])

    if index >= len(progress):
        progress.extend(
            [
                {
                    "attempts": 0,
                    "status": "unanswered",
                    "last_answer": "",
                    "chat": [],
                }
                for _ in range(index - len(progress) + 1)
            ]
        )

    state = progress[index]
    attempts = state.get("attempts", 0)
    expected_list = step.get("expected", [])

    if not user_answer_stripped:
        return jsonify(
            {
                "status": "incorrect",
                "hint": step.get(
                    "hint",
                    "Try giving your best guess, even if you're not sure.",
                ),
                "character": character,
            }
        )

    is_correct = False
    for exp in expected_list:
        if answers_match(user_answer_raw, str(exp)):
            is_correct = True
            break

    if is_correct:
        attempts += 1
        state["attempts"] = attempts
        state["status"] = "correct"
        state["last_answer"] = user_answer_raw
        progress[index] = state
        session["practice_progress"] = progress
        session.modified = True

        all_done = all(
            s.get("status") in ("correct", "given_up") for s in progress
        )
        if all_done:
            return jsonify(
                {
                    "status": "finished",
                    "message": practice_data.get(
                        "final_message", "Great job! Mission complete 🚀"
                    ),
                    "character": character,
                }
            )

        return jsonify(
            {
                "status": "correct",
                "next_prompt": step.get("prompt", ""),
                "type": step.get("type", "free"),
                "choices": step.get("choices", []),
                "character": character,
            }
        )

    # INCORRECT
    attempts += 1
    state["attempts"] = attempts
    state["last_answer"] = user_answer_raw
    progress[index] = state
    session["practice_progress"] = progress
    session.modified = True

    if attempts < 2:
        return jsonify(
            {
                "status": "incorrect",
                "hint": step.get("hint", "Try thinking about it step by step."),
                "character": character,
            }
        )

    state["status"] = "given_up"
    progress[index] = state
    session["practice_progress"] = progress
    session.modified = True

    explanation = step.get(
        "explanation",
        step.get("hint", "Let's walk through how to solve this carefully."),
    )

    all_done = all(
        s.get("status") in ("correct", "given_up") for s in progress
    )
    if all_done:
        return jsonify(
            {
                "status": "finished",
                "message": practice_data.get(
                    "final_message", "Great effort! Mission complete 🚀"
                ),
                "explanation": explanation,
                "character": character,
            }
        )

    return jsonify(
        {
            "status": "guided",
            "explanation": explanation,
            "next_prompt": step.get("prompt", ""),
            "type": step.get("type", "free"),
            "choices": step.get("choices", []),
            "character": character,
        }
    )


@app.route("/practice_help_message", methods=["POST"])
@csrf.exempt
def practice_help_message():
    init_user()

    data = request.get_json() or {}
    student_msg = data.get("message", "").strip()

    practice_data = session.get("practice")
    index = session.get("practice_step", 0)
    character = session.get("character", "everly")
    grade = session.get("grade", "8")

    if not practice_data:
        return jsonify(
            {
                "reply": "I can't find an active practice mission. Try starting one again!"
            }
        )

    steps = practice_data.get("steps", [])
    if not steps or index < 0 or index >= len(steps):
        return jsonify(
            {
                "reply": "You've completed all the questions for this mission! Want to start a new one?"
            }
        )

    progress = session.get("practice_progress", [])
    if index >= len(progress):
        progress.extend(
            [
                {
                    "attempts": 0,
                    "status": "unanswered",
                    "last_answer": "",
                    "chat": [],
                }
                for _ in range(index - len(progress) + 1)
            ]
        )

    state = progress[index]
    attempts = state.get("attempts", 0)
    chat_history = state.get("chat", [])

    step = steps[index]
    prompt = step.get("prompt", "")
    expected = step.get("expected", [])
    explanation = step.get("explanation", "")
    topic = practice_data.get("topic", "")

    chat_history.append({"role": "student", "content": student_msg})

    ai_prompt = f"""
You are COZMICLEARNING - a warm, patient cozmic mentor guiding students through the galaxy of learning.

The student is asking for help about a practice question.

CONTEXT:
- Topic: {topic}
- Grade level: {grade}
- Character voice: {character}

Current question:
{prompt}

Expected correct answers (could be letters or short answers):
{expected}

Official explanation / teacher notes:
{explanation}

Attempts used so far on this question: {attempts}

CHAT HISTORY for this question:
{chat_history}

STUDENT JUST SAID:
{student_msg}

RESPONSE RULES (VERY IMPORTANT):
- Tone: encouraging, calm, never harsh.
- 1–3 short guiding sentences first.
- Then up to 8 short bullet points that walk through the idea step-by-step.
- Keep language efficient and easy to follow.
- BEFORE 2 graded attempts: do NOT give the full direct answer. Use hints, guiding questions, and partial steps.
- AFTER 2 graded attempts: you MAY give the direct answer, but still explain why in a clear, kind way.
- Encourage the student to keep going and remind them you're there to help.
- If they dispute correctness, compare their reasoning with the expected answer gently and clearly.

Do NOT use markdown syntax markers like '*' or '-' in your bullets.
Instead, start each bullet with a simple symbol like '•'.
"""

    reply = study_buddy_ai(ai_prompt, grade, character)
    reply_text = reply.get("raw_text") if isinstance(reply, dict) else reply

    chat_history.append({"role": "tutor", "content": reply_text})
    state["chat"] = chat_history
    progress[index] = state
    session["practice_progress"] = progress
    session.modified = True

    return jsonify({"reply": reply_text, "chat": chat_history})


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():
    init_user()
    
    # Check subscription status for students
    access_check = check_subscription_access("student")
    if access_check != True:
        return access_check  # Redirect to trial_expired

    # Time limit enforcement (Phase 3)
    student_id = session.get("student_id")
    time_limit_active = False
    minutes_remaining = None
    daily_limit = None
    trial_days_remaining = 0
    
    if student_id:
        student = Student.query.get(student_id)
        
        # Get trial days remaining to show in UI
        trial_days_remaining = get_days_remaining_in_trial(student)
        
        if student and student.parent_id:
            parent = Parent.query.get(student.parent_id)
            if parent and parent.daily_limit_minutes:
                daily_limit = parent.daily_limit_minutes
                time_limit_active = True
                
                # Update current session minutes
                if session.get("login_time"):
                    login_time = datetime.fromisoformat(session["login_time"])
                    session_minutes = int((datetime.utcnow() - login_time).total_seconds() / 60)
                    student.today_minutes = max(student.today_minutes, session_minutes)
                    db.session.commit()
                
                # Check if limit exceeded
                if student.today_minutes >= daily_limit:
                    flash(f"Daily time limit reached ({daily_limit} minutes). Please try again tomorrow!", "warning")
                    return render_template(
                        "time_limit_reached.html",
                        daily_limit=daily_limit,
                        minutes_used=student.today_minutes
                    )
                
                minutes_remaining = daily_limit - student.today_minutes

    xp = session["xp"]
    level = session["level"]
    tokens = session["tokens"]
    streak = session["streak"]

    xp_to_next = level * 100
    xp_percent = int((xp / xp_to_next) * 100) if xp_to_next > 0 else 0

    missions = [
        "Visit 2 different planets",
        "Ask 1 science question",
        "Earn 20 XP",
    ]

    locked = {
        "Princess Everly": "Reach Level 3",
        "Nova Circuit": "3-day streak",
        "Agent Cluehart": "Earn 200 XP",
        "Buddy Barkston": "Buy for 100 tokens",
    }
    
    # Plan usage tracking
    allowed, remaining, limit = check_question_limit()
    questions_used = session.get("questions_this_month", 0)
    show_usage = session.get("user_role") == "student" and limit != float('inf')
    
    # Achievement & activity data
    from modules.achievement_helper import get_student_achievements, get_recent_activities, check_and_award_achievements
    
    student_achievements = []
    recent_activities = []
    newly_unlocked = []
    progress_data = {"dates": [], "xp": [], "subjects": {}}
    
    if student_id:
        # Check for new achievements
        session_data = {
            "xp": xp,
            "level": level,
            "streak": streak,
            "tokens": tokens
        }
        newly_unlocked = check_and_award_achievements(student_id, session_data)
        
        # Get earned achievements and recent activity
        student_achievements = get_student_achievements(student_id)
        recent_activities = get_recent_activities(student_id, limit=8)
        
        # Generate progress chart data (last 7 days)
        from datetime import timedelta
        from models import ActivityLog, AssessmentResult
        
        today = datetime.utcnow()
        dates = []
        xp_values = []
        
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            dates.append(day.strftime('%a'))
            
            # Sum XP earned on this day
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_xp = db.session.query(db.func.sum(ActivityLog.xp_earned)).filter(
                ActivityLog.student_id == student_id,
                ActivityLog.created_at >= day_start,
                ActivityLog.created_at < day_end
            ).scalar() or 0
            
            xp_values.append(day_xp)
        
        progress_data["dates"] = dates
        progress_data["xp"] = xp_values
        
        # Subject performance (count by subject)
        subject_counts = db.session.query(
            ActivityLog.subject,
            db.func.count(ActivityLog.id)
        ).filter(
            ActivityLog.student_id == student_id,
            ActivityLog.subject.isnot(None)
        ).group_by(ActivityLog.subject).all()
        
        progress_data["subjects"] = {subj.replace('_', ' ').title(): count for subj, count in subject_counts if subj}

    return render_template(
        "dashboard.html",
        xp=xp,
        level=level,
        tokens=tokens,
        streak=streak,
        character=session["character"],
        xp_percent=xp_percent,
        xp_to_next=xp_to_next,
        missions=missions,
        locked_characters=locked,
        time_limit_active=time_limit_active,
        minutes_remaining=minutes_remaining,
        daily_limit=daily_limit,
        show_usage=show_usage,
        questions_used=questions_used,
        questions_limit=limit if limit != float('inf') else None,
        questions_remaining=remaining if remaining != float('inf') else None,
        trial_days_remaining=trial_days_remaining,
        achievements=student_achievements,
        recent_activities=recent_activities,
        newly_unlocked=newly_unlocked,
        progress_data=progress_data,
    )


# ============================================================
# PARENT DASHBOARD (SESSION-BASED SNAPSHOT)
# ============================================================

@app.route("/parent_dashboard")
def parent_dashboard():
    init_user()
    
    # Admin bypass - allow access without parent_id
    if not session.get("bypass_auth"):
        # Check subscription status for parents
        access_check = check_subscription_access("parent")
        if access_check != True:
            return access_check  # Redirect to trial_expired

    parent_id = session.get("parent_id")
    parent = None
    unread_messages = 0
    has_teacher_features = False
    student_limit = 3
    lesson_plans_limit = 0
    assignments_limit = 0
    trial_days_remaining = 0
    
    if parent_id:
        parent = Parent.query.get(parent_id)
        
        if parent:
            # Get trial days remaining
            trial_days_remaining = get_days_remaining_in_trial(parent)
            
            unread_messages = Message.query.filter_by(
                recipient_type="parent",
                recipient_id=parent_id,
                is_read=False,
            ).count()
            
            # Get plan limits for homeschool features
            student_limit, lesson_plans_limit, assignments_limit, has_teacher_features = get_parent_plan_limits(parent)
            
            # If this is a homeschool parent, redirect to homeschool dashboard
            if has_teacher_features:
                return redirect("/homeschool/dashboard")

    progress = {
        s: (
            int(data["correct"] / data["questions"] * 100)
            if data["questions"]
            else 0
        )
        for s, data in session["progress"].items()
    }
    
    # Get all planets for subject explorer
    planets = [
        ("chrono_core", "chrono_core.png", "ChronoCore", "History"),
        ("num_forge", "num_forge.png", "NumForge", "Math"),
        ("atom_sphere", "atom_sphere.png", "AtomSphere", "Science"),
        ("story_verse", "story_verse.png", "StoryVerse", "Reading"),
        ("ink_haven", "ink_haven.png", "InkHaven", "Writing"),
        ("faith_realm", "faith_realm.png", "FaithRealm", "Bible"),
        ("coin_quest", "coin_quest.png", "CoinQuest", "Money"),
        ("stock_star", "stock_star.png", "StockStar", "Investing"),
        ("terra_nova", "terra_nova.png", "TerraNova", "General Knowledge"),
        ("power_grid", "power_grid.png", "PowerGrid", "Deep Study"),
        ("truth_forge", "truth_forge.png", "TruthForge", "Apologetics"),
    ]

    return render_template(
        "parent_dashboard.html",
        parent=parent,
        progress=progress,
        utilization=session["usage_minutes"],
        xp=session["xp"],
        level=session["level"],
        tokens=session["tokens"],
        unread_messages=unread_messages,
        character=session["character"],
        has_teacher_features=has_teacher_features,
        student_limit=student_limit if student_limit != float('inf') else None,
        lesson_plans_limit=lesson_plans_limit if lesson_plans_limit != float('inf') else None,
        assignments_limit=assignments_limit if assignments_limit != float('inf') else None,
        trial_days_remaining=trial_days_remaining,
        planets=planets,
    )


# ============================================================
# HOMESCHOOL DASHBOARD (COMBINED PARENT + TEACHER FEATURES)
# ============================================================

@app.route("/homeschool/dashboard")
def homeschool_dashboard():
    """Unified dashboard for homeschool parents with teacher features."""
    init_user()
    
    parent_id = session.get("parent_id")
    
    # Temporary debug - remove after testing
    if not parent_id:
        # Try to find the homeschool parent for testing
        test_parent = Parent.query.filter_by(email='homeschool@test.com').first()
        if test_parent:
            session["parent_id"] = test_parent.id
            session["user_role"] = "parent"
            session["parent_name"] = test_parent.name if hasattr(test_parent, 'name') else "Homeschool Parent"
            parent_id = test_parent.id
    
    # Admin bypass - allow access without parent_id
    if not session.get("bypass_auth"):
        # Check subscription status for homeschool
        access_check = check_subscription_access("parent")
        if access_check != True:
            return access_check  # Redirect to trial_expired

    parent = None
    unread_messages = 0
    has_teacher_features = False
    student_limit = 3
    lesson_plans_limit = 0
    assignments_limit = 0
    trial_days_remaining = 0
    classes = []
    recent_assignments = []
    
    if parent_id:
        parent = Parent.query.get(parent_id)
        
        if parent:
            # Get trial days remaining
            trial_days_remaining = get_days_remaining_in_trial(parent)
            
            unread_messages = Message.query.filter_by(
                recipient_type="parent",
                recipient_id=parent_id,
                is_read=False,
            ).count()
            
            # Get plan limits for homeschool features
            student_limit, lesson_plans_limit, assignments_limit, has_teacher_features = get_parent_plan_limits(parent)
            
            # If parent has teacher features, get their "classes" (which are just student groups)
            # For homeschool, we treat the parent's students as a virtual class
            if has_teacher_features and parent.students:
                # Get recent assignments if parent has any linked teacher account
                # For now, we'll create a virtual class concept
                pass

    progress = {
        s: (
            int(data["correct"] / data["questions"] * 100)
            if data["questions"]
            else 0
        )
        for s, data in session["progress"].items()
    }
    
    # Get all planets for subject explorer
    planets = [
        ("chrono_core", "chrono_core.png", "ChronoCore", "History"),
        ("num_forge", "num_forge.png", "NumForge", "Math"),
        ("atom_sphere", "atom_sphere.png", "AtomSphere", "Science"),
        ("story_verse", "story_verse.png", "StoryVerse", "Reading"),
        ("ink_haven", "ink_haven.png", "InkHaven", "Writing"),
        ("faith_realm", "faith_realm.png", "FaithRealm", "Bible"),
        ("coin_quest", "coin_quest.png", "CoinQuest", "Money"),
        ("stock_star", "stock_star.png", "StockStar", "Investing"),
        ("terra_nova", "terra_nova.png", "TerraNova", "General Knowledge"),
        ("power_grid", "power_grid.png", "PowerGrid", "Deep Study"),
        ("truth_forge", "truth_forge.png", "TruthForge", "Apologetics"),
    ]

    return render_template(
        "homeschool_dashboard.html",
        parent=parent,
        progress=progress,
        utilization=session["usage_minutes"],
        xp=session["xp"],
        level=session["level"],
        tokens=session["tokens"],
        unread_messages=unread_messages,
        character=session["character"],
        has_teacher_features=has_teacher_features,
        student_limit=student_limit if student_limit != float('inf') else None,
        lesson_plans_limit=lesson_plans_limit if lesson_plans_limit != float('inf') else None,
        assignments_limit=assignments_limit if assignments_limit != float('inf') else None,
        trial_days_remaining=trial_days_remaining,
        planets=planets,
    )


# ============================================================
# PARENT - MESSAGING SYSTEM
# ============================================================

@app.route("/parent/students")
def parent_students():
    """Parent student management page - view and remove students."""
    parent_id = session.get("parent_id")
    if not parent_id:
        flash("Please log in as a parent.", "error")
        return redirect("/parent/login")
    
    parent = Parent.query.get(parent_id)
    if not parent:
        return redirect("/parent/login")
    
    return render_template("parent_students.html", parent=parent)


@app.route("/parent/students/<int:student_id>/remove", methods=["POST"])
def parent_remove_student(student_id):
    """Unlink a student from parent account."""
    parent_id = session.get("parent_id")
    if not parent_id:
        flash("Please log in as a parent.", "error")
        return redirect("/parent/login")
    
    parent = Parent.query.get(parent_id)
    student = Student.query.get_or_404(student_id)
    
    # Verify parent owns this student
    if student.parent_id != parent.id:
        flash("Not authorized.", "error")
        return redirect("/parent/students")
    
    # Unlink student (set parent_id to None)
    student.parent_id = None
    db.session.commit()
    
    flash(f"{student.student_name} has been unlinked from your account.", "success")
    return redirect("/parent/students")


# ============================================================
# PARENT - TIME LIMITS (PHASE 3)
# ============================================================

@app.route("/parent/time-limits", methods=["GET", "POST"])
def parent_time_limits():
    """Parent time limit controls - set daily minutes for all students."""
    parent_id = session.get("parent_id")
    if not parent_id:
        flash("Please log in as a parent.", "error")
        return redirect("/parent/login")
    
    parent = Parent.query.get(parent_id)
    if not parent:
        return redirect("/parent/login")
    
    if request.method == "POST":
        limit = request.form.get("daily_limit_minutes")
        
        if limit == "" or limit is None:
            # Remove limit
            parent.daily_limit_minutes = None
            flash("Daily time limit removed. Students have unlimited access.", "success")
        else:
            try:
                minutes = int(limit)
                if minutes < 5:
                    flash("Time limit must be at least 5 minutes.", "error")
                elif minutes > 480:
                    flash("Time limit cannot exceed 480 minutes (8 hours).", "error")
                else:
                    parent.daily_limit_minutes = minutes
                    flash(f"Daily time limit set to {minutes} minutes.", "success")
            except ValueError:
                flash("Invalid time limit value.", "error")
        
        db.session.commit()
        return redirect("/parent/time-limits")
    
    return render_template("parent_time_limits.html", parent=parent)


@app.route("/parent/analytics")
def parent_analytics():
    """Parent analytics page with detailed subject performance."""
    parent_id = session.get("parent_id")
    if not parent_id:
        flash("Please log in as a parent.", "error")
        return redirect("/parent/login")
    
    parent = Parent.query.get(parent_id)
    if not parent:
        return redirect("/parent/login")
    
    # Get selected student (default to first student)
    student_id = request.args.get("student_id", type=int)
    if student_id:
        selected_student = Student.query.get(student_id)
        # Verify parent owns this student
        if not selected_student or selected_student.parent_id != parent.id:
            selected_student = parent.students[0] if parent.students else None
    else:
        selected_student = parent.students[0] if parent.students else None
    
    # Calculate subject statistics
    subject_stats = {}
    subject_count = 0
    
    if selected_student:
        for result in selected_student.assessment_results:
            subject = result.subject
            if subject not in subject_stats:
                subject_stats[subject] = {'total': 0, 'count': 0, 'scores': []}
                subject_count += 1
            
            subject_stats[subject]['scores'].append(result.score_percent)
            subject_stats[subject]['total'] += result.score_percent
            subject_stats[subject]['count'] += 1
    
    return render_template(
        "parent_analytics.html",
        parent=parent,
        selected_student=selected_student,
        subject_stats=subject_stats,
        subject_count=subject_count,
    )


@app.route("/parent/safety")
def parent_safety():
    """Parent view of their children's flagged content and safety alerts"""
    parent_id = session.get("parent_id")
    if not parent_id:
        flash("Please log in as a parent.", "error")
        return redirect("/parent/login")
    
    parent = Parent.query.get(parent_id)
    if not parent:
        return redirect("/parent/login")
    
    # Get selected student filter
    student_filter = request.args.get("student_id", type=int)
    
    # Get all question logs for this parent's students
    student_ids = [s.id for s in parent.students]
    
    query = QuestionLog.query.filter(QuestionLog.student_id.in_(student_ids))
    
    if student_filter:
        query = query.filter_by(student_id=student_filter)
    
    # Get flagged questions only
    flagged_logs = query.filter_by(flagged=True).order_by(QuestionLog.created_at.desc()).limit(100).all()
    
    # Calculate stats
    total_flagged = query.filter_by(flagged=True).count()
    high_severity_count = query.filter_by(flagged=True, severity="high").count()
    recent_flags = query.filter(
        QuestionLog.flagged == True,
        QuestionLog.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    return render_template(
        "parent_safety.html",
        parent=parent,
        flagged_logs=flagged_logs,
        total_flagged=total_flagged,
        high_severity_count=high_severity_count,
        recent_flags=recent_flags,
        student_filter=student_filter
    )


# ============================================================
# PARENT - WEEKLY EMAIL REPORTS (PHASE 4)
# ============================================================

def generate_weekly_report_data(parent):
    """Generate weekly progress report data for a parent's students."""
    report_data = {
        'parent_name': parent.name,
        'parent_email': parent.email,
        'week_start': (datetime.utcnow() - timedelta(days=7)).strftime('%B %d, %Y'),
        'week_end': datetime.utcnow().strftime('%B %d, %Y'),
        'students': []
    }
    
    for student in parent.students:
        # Get assessments from past 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_assessments = [
            r for r in student.assessment_results 
            if r.created_at and r.created_at >= week_ago
        ]
        
        if not weekly_assessments:
            continue  # Skip students with no activity
        
        # Calculate stats
        total_score = sum(r.score_percent for r in weekly_assessments)
        avg_score = total_score / len(weekly_assessments) if weekly_assessments else 0
        
        # Subject breakdown
        subject_performance = {}
        for result in weekly_assessments:
            if result.subject not in subject_performance:
                subject_performance[result.subject] = {'scores': [], 'count': 0}
            subject_performance[result.subject]['scores'].append(result.score_percent)
            subject_performance[result.subject]['count'] += 1
        
        # Calculate subject averages
        for subject in subject_performance:
            scores = subject_performance[subject]['scores']
            subject_performance[subject]['average'] = sum(scores) / len(scores)
        
        # Time spent (from today_minutes tracking)
        time_spent = student.today_minutes or 0
        
        student_data = {
            'name': student.student_name,
            'assessments_completed': len(weekly_assessments),
            'average_score': round(avg_score, 1),
            'time_spent_minutes': time_spent,
            'subjects_practiced': len(subject_performance),
            'subject_performance': subject_performance,
            'ability_level': student.ability_level or 'on_level'
        }
        
        report_data['students'].append(student_data)
    
    return report_data


def send_weekly_report_email(parent):
    """Send weekly progress report email to parent."""
    if not parent.email_reports_enabled:
        return False
    
    report_data = generate_weekly_report_data(parent)
    
    # Skip if no student activity this week
    if not report_data['students']:
        return False
    
    try:
        msg = EmailMessage(
            subject=f"📊 CozmicLearning Weekly Progress Report",
            recipients=[parent.email],
        )
        
        msg.html = render_template(
            'emails/weekly_report.html',
            **report_data
        )
        
        mail.send(msg)
        
        # Update last report sent timestamp
        parent.last_report_sent = datetime.utcnow()
        db.session.commit()
        
        return True
    except Exception as e:
        print(f"Error sending email to {parent.email}: {e}")
        return False


@app.route("/parent/email-preferences", methods=["GET", "POST"])
def parent_email_preferences():
    """Parent email preferences - enable/disable weekly reports."""
    parent_id = session.get("parent_id")
    if not parent_id:
        flash("Please log in as a parent.", "error")
        return redirect("/parent/login")
    
    parent = Parent.query.get(parent_id)
    if not parent:
        return redirect("/parent/login")
    
    if request.method == "POST":
        enabled = request.form.get("email_reports_enabled") == "on"
        parent.email_reports_enabled = enabled
        db.session.commit()
        
        if enabled:
            flash("Weekly email reports enabled! You'll receive updates every Sunday.", "success")
        else:
            flash("Weekly email reports disabled.", "success")
        
        return redirect("/parent/email-preferences")
    
    return render_template("parent_email_preferences.html", parent=parent)


@app.route("/parent/send-test-report")
def parent_send_test_report():
    """Manual trigger for testing weekly report emails."""
    parent_id = session.get("parent_id")
    if not parent_id:
        flash("Please log in as a parent.", "error")
        return redirect("/parent/login")
    
    parent = Parent.query.get(parent_id)
    if not parent:
        return redirect("/parent/login")
    
    success = send_weekly_report_email(parent)
    
    if success:
        flash("✅ Test report sent! Check your email.", "success")
    else:
        flash("⚠️ No student activity this week, or email reports disabled.", "warning")
    
    return redirect("/parent/email-preferences")


@app.route("/parent/messages")
def parent_messages():
    """Parent inbox - view all messages from teachers."""
    parent_id = session.get("parent_id")
    if not parent_id:
        flash("Please log in as a parent.", "error")
        return redirect("/parent/login")
    
    parent = Parent.query.get(parent_id)
    if not parent:
        return redirect("/parent/login")
    
    # Get all messages where parent is recipient
    received = Message.query.filter_by(
        recipient_type='parent',
        recipient_id=parent.id
    ).order_by(Message.created_at.desc()).all()
    
    # Get all messages parent sent
    sent = Message.query.filter_by(
        sender_type='parent',
        sender_id=parent.id
    ).order_by(Message.created_at.desc()).all()
    
    # Count unread
    unread_count = Message.query.filter_by(
        recipient_type='parent',
        recipient_id=parent.id,
        is_read=False
    ).count()
    
    return render_template(
        "parent_messages.html",
        parent=parent,
        received=received,
        sent=sent,
        unread_count=unread_count,
    )


@app.route("/parent/messages/<int:message_id>")
def parent_view_message(message_id):
    """View a specific message."""
    parent_id = session.get("parent_id")
    if not parent_id:
        return redirect("/parent/login")
    
    parent = Parent.query.get(parent_id)
    message = Message.query.get_or_404(message_id)
    
    # Check authorization
    is_recipient = (message.recipient_type == 'parent' and message.recipient_id == parent.id)
    is_sender = (message.sender_type == 'parent' and message.sender_id == parent.id)
    
    if not (is_recipient or is_sender):
        flash("Not authorized to view this message.", "error")
        return redirect("/parent/messages")
    
    # Mark as read if recipient
    if is_recipient and not message.is_read:
        message.is_read = True
        db.session.commit()
    
    # Get student info
    student = Student.query.get(message.student_id) if message.student_id else None
    
    # Get sender/recipient names
    if message.sender_type == 'parent':
        sender = Parent.query.get(message.sender_id)
        sender_name = sender.name if sender else "Unknown Parent"
    else:
        sender = Teacher.query.get(message.sender_id)
        sender_name = sender.name if sender else "Unknown Teacher"
    
    if message.recipient_type == 'parent':
        recipient = Parent.query.get(message.recipient_id)
        recipient_name = recipient.name if recipient else "Unknown Parent"
    else:
        recipient = Teacher.query.get(message.recipient_id)
        recipient_name = recipient.name if recipient else "Unknown Teacher"
    
    # Parse progress report if exists
    progress_report = None
    if message.progress_report_json:
        progress_report = json.loads(message.progress_report_json)
    
    return render_template(
        "view_message.html",
        parent=parent,
        message=message,
        student=student,
        sender_name=sender_name,
        recipient_name=recipient_name,
        progress_report=progress_report,
    )


@app.route("/parent/messages/reply/<int:message_id>", methods=["GET", "POST"])
def parent_reply_message(message_id):
    """Reply to a teacher's message."""
    parent_id = session.get("parent_id")
    if not parent_id:
        return redirect("/parent/login")
    
    parent = Parent.query.get(parent_id)
    original_message = Message.query.get_or_404(message_id)
    
    # Must be recipient of original message
    if not (original_message.recipient_type == 'parent' and original_message.recipient_id == parent.id):
        flash("Not authorized.", "error")
        return redirect("/parent/messages")
    
    if request.method == "POST":
        body = safe_text(request.form.get("body", ""), 5000)
        
        if not body:
            flash("Message cannot be empty.", "error")
            return redirect(f"/parent/messages/reply/{message_id}")
        
        # Create reply message
        reply = Message(
            sender_type='parent',
            sender_id=parent.id,
            recipient_type='teacher',
            recipient_id=original_message.sender_id,
            student_id=original_message.student_id,
            subject=f"Re: {original_message.subject}",
            body=body,
            thread_id=original_message.thread_id or original_message.id,
        )
        db.session.add(reply)
        db.session.commit()
        
        flash("Reply sent successfully!", "info")
        return redirect("/parent/messages")
    
    # GET - show reply form
    student = Student.query.get(original_message.student_id) if original_message.student_id else None
    teacher = Teacher.query.get(original_message.sender_id)
    
    return render_template(
        "reply_message.html",
        parent=parent,
        original_message=original_message,
        student=student,
        teacher=teacher,
    )


# ============================================================
# LEGAL PAGES
# ============================================================

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")

# TEMPORARY - DEBUG TEACHER ID
@app.route("/debug/teacher_id")
def debug_teacher_id():
    from models import Teacher
    t = Teacher.query.filter_by(email="jakegholland18@gmail.com").first()
    if not t:
        return "Teacher not found"
    return f"Your teacher ID is: {t.id}"

# ============================================================
# MAIN ENTRY (LOCAL DEV)
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)


