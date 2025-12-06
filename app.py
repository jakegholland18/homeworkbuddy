# ============================================================
# PYTHON STANDARD LIBRARIES
# ============================================================

import os
import sys
import logging
import traceback
import secrets
import random
import string
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
    flash, jsonify, send_file, abort, make_response
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

app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production-' + secrets.token_hex(32))

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
# RATE LIMITING (FLASK-LIMITER)
# ============================================================

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],  # Global default limits
    storage_uri="memory://",  # Use memory storage (upgrade to Redis for production)
    strategy="fixed-window"
)

# ============================================================
# OWNER + ADMIN
# ============================================================

OWNER_EMAIL = "jakegholland18@gmail.com"
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Cash&Ollie123')

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
    HomeschoolLessonPlan,
    Message,
    StudentSubmission,
    QuestionLog,
)
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import json
import time

# ------------------------------------------------------------
# Database Helper Functions
# ------------------------------------------------------------

def safe_commit(retries=3, delay=0.1):
    """
    Safely commit database changes with error handling and retry logic.

    Args:
        retries: Number of retry attempts (default 3)
        delay: Initial delay between retries in seconds (default 0.1)

    Returns:
        (success: bool, error: str or None)
    """
    for attempt in range(retries):
        try:
            db.session.commit()
            return True, None
        except OperationalError as e:
            # Database is locked - retry with exponential backoff
            db.session.rollback()
            if attempt < retries - 1:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                app.logger.warning(f"Database locked, retrying in {wait_time}s (attempt {attempt + 1}/{retries})")
                time.sleep(wait_time)
            else:
                app.logger.error(f"Database commit failed after {retries} attempts: {str(e)}")
                return False, str(e)
        except SQLAlchemyError as e:
            # Other database error - don't retry
            db.session.rollback()
            app.logger.error(f"Database commit failed: {str(e)}")
            return False, str(e)
        except Exception as e:
            # Unexpected error - don't retry
            db.session.rollback()
            app.logger.error(f"Unexpected error during commit: {str(e)}")
            return False, str(e)

    return False, "Max retries exceeded"

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

# ============================================================
# DATABASE CONNECTION POOLING (Optimized for SQLite + Single Worker)
# ============================================================
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_size": 5,           # Reduced for single worker (was 10)
    "pool_recycle": 3600,     # Recycle connections after 1 hour to prevent stale connections
    "pool_pre_ping": True,    # Test connection health before using (prevents stale connection errors)
    "max_overflow": 2,        # Reduced overflow (was 5)
    "pool_timeout": 30,       # Wait up to 30 seconds for available connection before failing
    "connect_args": {
        "timeout": 20,        # SQLite-specific: wait up to 20s for lock
        "check_same_thread": False,  # Allow SQLite usage across threads
    }
}

db.init_app(app)

# ============================================================
# SEED OWNER SAFELY
# ============================================================

from werkzeug.security import generate_password_hash
from models import Teacher

def seed_owner():
    OWNER_EMAIL = "jakegholland18@gmail.com"
    default_password = "Cash&Ollie123"

    try:
        teacher = Teacher.query.filter_by(email=OWNER_EMAIL).first()
        if not teacher:
            t = Teacher(
                name="Jake Holland",
                email=OWNER_EMAIL,
                password_hash=generate_password_hash(default_password)
            )
            db.session.add(t)
            db.session.commit()
    except Exception as e:
        # If query fails (e.g., missing columns), skip seeding
        # This can happen if Stripe migration hasn't run yet
        app.logger.warning(f"Could not seed owner account: {e}")
        db.session.rollback()

with app.app_context():
    db.create_all()  # ensure tables exist

    # ============================================================
    # DATABASE MIGRATION: Add open_date column if missing
    # ============================================================
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if open_date column exists
        cursor.execute("PRAGMA table_info(assigned_practice)")
        columns = [row[1] for row in cursor.fetchall()]

        if "open_date" not in columns:
            print("🔧 Running migration: Adding open_date column to assigned_practice table...")
            cursor.execute("ALTER TABLE assigned_practice ADD COLUMN open_date TIMESTAMP")
            conn.commit()
            print("✅ Migration complete: open_date column added successfully!")
        else:
            print("✅ Database schema up to date: open_date column exists")

        # ============================================================
        # DATABASE MIGRATION: Add password reset tokens
        # ============================================================

        # Check which tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]

        # Migrate students table
        if 'students' in existing_tables:
            cursor.execute("PRAGMA table_info(students)")
            student_columns = [col[1] for col in cursor.fetchall()]

            if 'reset_token' not in student_columns:
                print("🔧 Adding password reset columns to students table...")
                cursor.execute("ALTER TABLE students ADD COLUMN reset_token VARCHAR(255)")
                cursor.execute("ALTER TABLE students ADD COLUMN reset_token_expires DATETIME")
                conn.commit()
                print("✅ Students table updated with password reset columns")

        # Migrate parents table
        if 'parents' in existing_tables:
            cursor.execute("PRAGMA table_info(parents)")
            parent_columns = [col[1] for col in cursor.fetchall()]

            if 'reset_token' not in parent_columns:
                print("🔧 Adding password reset columns to parents table...")
                cursor.execute("ALTER TABLE parents ADD COLUMN reset_token VARCHAR(255)")
                cursor.execute("ALTER TABLE parents ADD COLUMN reset_token_expires DATETIME")
                conn.commit()
                print("✅ Parents table updated with password reset columns")

        # Migrate teachers table
        if 'teachers' in existing_tables:
            cursor.execute("PRAGMA table_info(teachers)")
            teacher_columns = [col[1] for col in cursor.fetchall()]

            if 'reset_token' not in teacher_columns:
                print("🔧 Adding password reset columns to teachers table...")
                cursor.execute("ALTER TABLE teachers ADD COLUMN reset_token VARCHAR(255)")
                cursor.execute("ALTER TABLE teachers ADD COLUMN reset_token_expires DATETIME")
                conn.commit()
                print("✅ Teachers table updated with password reset columns")

        # ============================================================
        # DATABASE MIGRATION: Add join_code to classes table
        # ============================================================
        if 'classes' in existing_tables:
            cursor.execute("PRAGMA table_info(classes)")
            class_columns = [col[1] for col in cursor.fetchall()]

            if 'join_code' not in class_columns:
                print("🔧 Adding join_code column to classes table...")
                cursor.execute("ALTER TABLE classes ADD COLUMN join_code VARCHAR(8)")
                conn.commit()

                # Generate unique join codes for existing classes
                import random
                import string

                cursor.execute("SELECT id FROM classes WHERE join_code IS NULL")
                classes_without_codes = cursor.fetchall()

                if classes_without_codes:
                    print(f"🔄 Generating join codes for {len(classes_without_codes)} existing classes...")
                    for (class_id,) in classes_without_codes:
                        # Generate unique code
                        while True:
                            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                            cursor.execute("SELECT id FROM classes WHERE join_code = ?", (code,))
                            if not cursor.fetchone():
                                break

                        cursor.execute("UPDATE classes SET join_code = ? WHERE id = ?", (code, class_id))

                    conn.commit()
                    print(f"✅ Generated {len(classes_without_codes)} join codes")

                print("✅ Classes table updated with join_code column")

        conn.close()
    except Exception as e:
        print(f"⚠️ Migration warning: {e}")
    # ============================================================

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
        ensure_column("students", student_cols, "password_hash", "VARCHAR(255)")  # Security fix: password authentication
        ensure_column("students", student_cols, "date_of_birth", "DATE")  # COPPA compliance: age verification

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
# SUBJECT CONFIGURATION (Using centralized registry)
# ============================================================

from subjects_config import (
    get_subject_map,
    get_subject_labels,
    get_subjects_for_display,
    validate_subject,
    validate_grade,
    validate_grade_for_subject,
    get_subject,
)

# Get subject handlers and labels from centralized config
subject_map = get_subject_map()
SUBJECT_LABELS = get_subject_labels()

# ============================================================
# HELPERS – TEACHER + OWNER
# ============================================================


def get_current_teacher():
    """Get currently logged-in teacher (not for admin viewing)"""
    tid = session.get("teacher_id")
    if not tid:
        return None
    return Teacher.query.get(tid)


def get_teacher_or_admin():
    """
    Get current teacher, or return a placeholder for admin access.
    Used in routes where admins should be able to view teacher features.
    Returns: Teacher object, or special AdminTeacher placeholder, or None
    """
    # First check if there's a logged-in teacher
    teacher = get_current_teacher()
    if teacher:
        return teacher

    # If admin is authenticated, return a placeholder that indicates admin access
    if is_admin():
        # Return a special object that signals admin access without being a real teacher
        class AdminTeacher:
            id = None
            name = "Admin View"
            email = OWNER_EMAIL
            classes = []  # Will be populated by route if needed

            def __repr__(self):
                return "<AdminTeacher>"

        return AdminTeacher()

    return None


def is_owner(teacher: Teacher | None) -> bool:
    return bool(
        teacher and teacher.email and teacher.email.lower() == OWNER_EMAIL.lower()
    )


def is_admin() -> bool:
    """Check if current session user is admin (owner email in any role OR admin session flags)"""
    # Check for admin session flags (secret admin login)
    if session.get("admin_authenticated") or session.get("is_owner"):
        return True

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

def generate_join_code():
    """Generate a unique 8-character class join code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        # Check if code already exists
        existing = Class.query.filter_by(join_code=code).first()
        if not existing:
            return code


def init_user():
    # Preserve admin flags before setting defaults
    admin_flags = {
        "admin_authenticated": session.get("admin_authenticated"),
        "is_owner": session.get("is_owner"),
    }

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

    # Set all defaults if not present
    for k, v in defaults.items():
        if k not in session:
            session[k] = v

    # Restore admin flags after setting defaults
    for flag, value in admin_flags.items():
        if value is not None:
            session[flag] = value

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
    if session.get("admin_authenticated") or is_admin():
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
    """Remove common text/symbols from numeric answers for comparison."""
    if not text:
        return ""
    t = text.lower().strip()
    # Remove common words
    for word in ["percent", "perc", "per cent", "dollars", "dollar", "usd", "the answer is", "answer:", "="]:
        t = t.replace(word, "")
    # Remove commas and currency symbols
    t = t.replace(",", "")
    for ch in ["%", "$"]:
        t = t.replace(ch, "")
    return t.strip()


def _try_float(val: str):
    """Try to parse a string as a float, return None if it fails."""
    if not val:
        return None
    try:
        return float(val)
    except Exception:
        return None


def answers_match(user_raw: str, expected_raw: str) -> bool:
    """
    Compare user answer with expected answer.
    Handles:
    - Exact string matches (case-insensitive)
    - Numeric matches (with tolerance for floating point)
    - Different numeric formats (50, 50.0, 50%, $50, etc.)
    """
    if user_raw is None or expected_raw is None:
        return False

    # Normalize to lowercase and strip whitespace
    u_norm = user_raw.strip().lower()
    e_norm = expected_raw.strip().lower()

    # Exact string match
    if u_norm == e_norm and u_norm != "":
        return True

    # Normalize numeric tokens (remove %, $, commas, etc.)
    u_num_str = _normalize_numeric_token(user_raw)
    e_num_str = _normalize_numeric_token(expected_raw)

    # String match after numeric normalization
    if u_num_str and e_num_str and u_num_str == e_num_str:
        return True

    # Try numeric comparison
    u_num = _try_float(u_num_str)
    e_num = _try_float(e_num_str)
    if u_num is not None and e_num is not None:
        # Use small tolerance for floating point comparison
        if abs(u_num - e_num) < 1e-6:
            return True

    # Try parsing original strings as numbers (in case normalization failed)
    u_direct = _try_float(user_raw.strip())
    e_direct = _try_float(expected_raw.strip())
    if u_direct is not None and e_direct is not None:
        if abs(u_direct - e_direct) < 1e-6:
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
# GLOBAL ERROR HANDLERS
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 errors gracefully"""
    db.session.rollback()  # Rollback any failed transactions
    app.logger.error(f"500 Internal Server Error: {str(error)}")
    return render_template("error.html",
                         error_code=500,
                         error_message="Something went wrong. Please try again."), 500

@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors"""
    return render_template("error.html",
                         error_code=404,
                         error_message="Page not found"), 404

@app.errorhandler(Exception)
def handle_exception(error):
    """Catch-all exception handler to prevent crashes"""
    db.session.rollback()
    app.logger.error(f"Unhandled exception: {str(error)}", exc_info=True)

    # Return JSON for API endpoints, HTML for web pages
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({"error": "An error occurred. Please try again."}), 500

    return render_template("error.html",
                         error_code=500,
                         error_message="An unexpected error occurred. Please try again."), 500

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
    # Use centralized subject configuration
    planets = get_subjects_for_display()
    return render_template(
        "subjects.html",
        planets=planets,
        character=session.get("character", "everly"),
    )


@app.route("/subject/<subject_name>")
def subject_direct(subject_name):
    """
    Direct subject access route (e.g., /subject/atom_sphere).
    Redirects to grade selection for the specified subject.
    """
    init_user()

    # Validate subject exists
    if not validate_subject(subject_name):
        flash(f"Subject '{subject_name}' not found.", "error")
        return redirect("/subjects")

    # Get current grade from session or use default
    current_grade = session.get("grade", "8")

    # Redirect to choose grade for this subject
    return redirect(f"/choose-grade?subject={subject_name}")


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
        try:
            stats = get_student_stats(student_id)
        except Exception as e:
            # Database might not be migrated yet
            app.logger.warning(f"Could not load arcade stats: {e}")
            stats = None
    
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
        try:
            stats = get_student_stats(student_id, game_key)
        except Exception as e:
            app.logger.warning(f"Could not load game stats: {e}")
            stats = None

    # Get leaderboard
    try:
        leaderboard = get_leaderboard(game_key, grade, limit=10)
    except Exception as e:
        app.logger.warning(f"Could not load leaderboard: {e}")
        leaderboard = []
    
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
    from modules.arcade_enhancements import (
        check_and_award_badges,
        update_game_streak,
        check_daily_challenge_completion
    )
    from models import GameSession

    data = request.get_json()
    game_key = data.get("game_key")
    score = data.get("score", 0)
    correct = data.get("correct", 0)
    total = data.get("total", 0)
    time_seconds = data.get("time_seconds", 0)
    game_mode = data.get("mode", "timed")  # timed, practice, challenge

    student_id = session.get("student_id")

    # Get selected grade from current game session, fallback to student's grade
    current_game = session.get("current_game", {})
    grade = current_game.get("selected_grade") or session.get("grade", "5")

    if not student_id:
        return jsonify({"error": "Not logged in"}), 401

    # Save game session and get results
    results = save_game_session(student_id, game_key, grade, score, time_seconds, correct, total)

    # Get the saved game session for badge/challenge checking
    game_session = GameSession.query.filter_by(student_id=student_id).order_by(GameSession.id.desc()).first()

    # Update game mode in the session
    if game_session:
        game_session.game_mode = game_mode
        db.session.commit()

    # Only award XP/tokens/badges in timed/challenge mode (not practice)
    if game_mode != "practice" and game_session:
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

        # Update streak
        streak = update_game_streak(student_id)
        results["current_streak"] = streak.current_streak
        results["longest_streak"] = streak.longest_streak

        # Check and award badges
        newly_earned_badges = check_and_award_badges(student_id, game_session)
        if newly_earned_badges:
            results["badges_earned"] = [
                {"name": b.name, "icon": b.icon, "description": b.description}
                for b in newly_earned_badges
            ]

        # Check daily challenge completion
        challenge_completed = check_daily_challenge_completion(student_id, game_session)
        if challenge_completed:
            results["challenge_completed"] = True
            results["challenge_bonus_xp"] = game_session.xp_earned - results["xp_earned"]
            results["challenge_bonus_tokens"] = game_session.tokens_earned - results["tokens_earned"]

            # Update session tokens/xp with bonus
            session["xp"] += results.get("challenge_bonus_xp", 0)
            session["tokens"] += results.get("challenge_bonus_tokens", 0)
    else:
        # Practice mode - no rewards
        results["practice_mode"] = True
        results["xp_earned"] = 0
        results["tokens_earned"] = 0

    session.modified = True

    # Log activity
    log_activity(
        student_id=student_id,
        activity_type="arcade_game_completed",
        subject=game_key,
        description=f"Completed arcade game ({game_mode}) with {correct}/{total} correct",
        xp_earned=results["xp_earned"]
    )

    return jsonify(results)


# ============================================================
# ARCADE MODE ENHANCEMENTS - BADGES, POWERUPS, CHALLENGES
# ============================================================

@app.route("/arcade/badges")
def arcade_badges():
    """View all badges and student's earned badges"""
    init_user()

    try:
        from models import ArcadeBadge, StudentBadge

        student_id = session.get("student_id")

        # Get all badges grouped by category
        all_badges = ArcadeBadge.query.order_by(ArcadeBadge.category, ArcadeBadge.tier).all()
    except Exception as e:
        app.logger.error(f"Badges error: {e}")
        flash("Badges are not available yet. Please check back later!", "info")
        return redirect("/arcade")

    # Get student's earned badges
    earned_badge_ids = set()
    if student_id:
        earned = StudentBadge.query.filter_by(student_id=student_id).all()
        earned_badge_ids = {sb.badge_id for sb in earned}

    # Group badges by category
    badges_by_category = {}
    for badge in all_badges:
        if badge.category not in badges_by_category:
            badges_by_category[badge.category] = []

        badge_info = {
            "id": badge.id,
            "name": badge.name,
            "description": badge.description,
            "icon": badge.icon,
            "tier": badge.tier,
            "earned": badge.id in earned_badge_ids
        }
        badges_by_category[badge.category].append(badge_info)

    # Calculate badge stats
    total_badges = len(all_badges)
    earned_count = len(earned_badge_ids)

    return render_template(
        "arcade_badges.html",
        badges_by_category=badges_by_category,
        total_badges=total_badges,
        earned_count=earned_count,
        character=session["character"]
    )


@app.route("/arcade/powerups")
def arcade_powerups():
    """Power-up shop where students can buy power-ups with tokens"""
    init_user()

    try:
        from models import PowerUp
        from modules.arcade_enhancements import get_student_powerups

        student_id = session.get("student_id")
        tokens = session.get("tokens", 0)

        # Get all available power-ups
        all_powerups = PowerUp.query.all()
    except Exception as e:
        app.logger.error(f"Powerups error: {e}")
        flash("Power-ups are not available yet. Please check back later!", "info")
        return redirect("/arcade")

    # Get student's owned power-ups
    owned = {}
    if student_id:
        student_powerups = get_student_powerups(student_id)
        owned = {sp["key"]: sp["quantity"] for sp in student_powerups}

    powerups_data = []
    for powerup in all_powerups:
        powerups_data.append({
            "key": powerup.powerup_key,
            "name": powerup.name,
            "description": powerup.description,
            "icon": powerup.icon,
            "cost": powerup.token_cost,
            "owned": owned.get(powerup.powerup_key, 0),
            "uses_per_game": powerup.uses_per_game
        })

    return render_template(
        "arcade_powerups.html",
        powerups=powerups_data,
        tokens=tokens,
        character=session["character"]
    )


@app.route("/arcade/powerups/purchase", methods=["POST"])
def purchase_powerup():
    """Purchase a power-up with tokens"""
    init_user()

    from modules.arcade_enhancements import purchase_powerup as buy_powerup

    student_id = session.get("student_id")
    if not student_id:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    powerup_key = data.get("powerup_key")

    current_tokens = session.get("tokens", 0)

    success, message, remaining_tokens = buy_powerup(student_id, powerup_key, current_tokens)

    if success:
        session["tokens"] = remaining_tokens
        session.modified = True

    return jsonify({
        "success": success,
        "message": message,
        "tokens": remaining_tokens
    })


@app.route("/arcade/challenges")
def arcade_challenges():
    """View today's daily challenge"""
    init_user()

    try:
        from modules.arcade_enhancements import get_todays_challenge
        from modules.arcade_helper import ARCADE_GAMES
        from models import StudentChallengeProgress

        student_id = session.get("student_id")

        # Get today's challenge
        challenge = get_todays_challenge()
    except Exception as e:
        app.logger.error(f"Daily challenge error: {e}")
        flash("Daily challenges are not available yet. Please check back later!", "info")
        return redirect("/arcade")

    # Get game info
    game_info = next((g for g in ARCADE_GAMES if g["game_key"] == challenge.game_key), None)

    # Get student's progress on this challenge
    progress = None
    if student_id:
        progress = StudentChallengeProgress.query.filter_by(
            student_id=student_id,
            challenge_id=challenge.id
        ).first()

    challenge_data = {
        "game_key": challenge.game_key,
        "game_name": game_info["name"] if game_info else challenge.game_key,
        "game_icon": game_info["icon"] if game_info else "🎮",
        "grade_level": challenge.grade_level,
        "target_score": challenge.target_score,
        "target_accuracy": challenge.target_accuracy,
        "target_time": challenge.target_time,
        "bonus_xp": challenge.bonus_xp,
        "bonus_tokens": challenge.bonus_tokens,
        "completed": progress.completed if progress else False,
        "best_score": progress.best_score if progress else None,
        "best_accuracy": progress.best_accuracy if progress else None,
        "best_time": progress.best_time if progress else None
    }

    return render_template(
        "arcade_challenges.html",
        challenge=challenge_data,
        character=session["character"]
    )


@app.route("/arcade/stats")
def arcade_stats():
    """View detailed arcade statistics and progress"""
    init_user()

    try:
        from modules.arcade_enhancements import get_student_arcade_stats
        from modules.arcade_helper import get_student_stats, ARCADE_GAMES
        from models import GameSession
        import json

        student_id = session.get("student_id")

        if not student_id:
            flash("Please log in to view stats", "error")
            return redirect("/arcade")

        # Get comprehensive stats
        stats = get_student_arcade_stats(student_id)
    except Exception as e:
        app.logger.error(f"Stats error: {e}")
        flash("Statistics are not available yet. Please check back later!", "info")
        return redirect("/arcade")

    # Get per-game stats
    game_stats = []
    for game in ARCADE_GAMES:
        game_key = game["game_key"]
        sessions = GameSession.query.filter_by(
            student_id=student_id,
            game_key=game_key
        ).all()

        if sessions:
            plays = len(sessions)
            avg_score = sum(s.score for s in sessions) / plays
            avg_accuracy = sum(s.accuracy for s in sessions if s.accuracy) / len([s for s in sessions if s.accuracy])
            best_score = max(s.score for s in sessions)

            game_stats.append({
                "name": game["name"],
                "icon": game["icon"],
                "plays": plays,
                "avg_score": round(avg_score, 1),
                "avg_accuracy": round(avg_accuracy, 1),
                "best_score": best_score
            })

    # Sort by most played
    game_stats.sort(key=lambda x: x["plays"], reverse=True)

    # Get recent sessions for activity chart
    recent_sessions = GameSession.query.filter_by(
        student_id=student_id
    ).order_by(GameSession.started_at.desc()).limit(10).all()

    chart_data = {
        "dates": [s.started_at.strftime("%m/%d") for s in reversed(recent_sessions)],
        "scores": [s.score for s in reversed(recent_sessions)],
        "accuracy": [s.accuracy for s in reversed(recent_sessions)]
    }

    return render_template(
        "arcade_stats.html",
        stats=stats,
        game_stats=game_stats,
        chart_data=json.dumps(chart_data),
        character=session["character"]
    )


@app.route("/arcade/play/<game_key>/practice")
def arcade_play_practice(game_key):
    """Start a practice mode game (no timer, no pressure)"""
    init_user()

    # Practice mode uses same template but with practice flag
    return redirect(f"/arcade/play/{game_key}?mode=practice")


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
@csrf.exempt
def secret_admin_login():
    """Hidden admin login - accessed via secret button on landing page"""
    if request.method == "POST":
        admin_id = request.form.get("admin_id", "").strip()
        password = request.form.get("password", "").strip()

        # Simple check: ID = "admin" and password matches
        if admin_id.lower() == "admin" and password == ADMIN_PASSWORD:
            session["admin_authenticated"] = True
            flash("🔧 Admin access granted. Welcome!", "success")
            return redirect("/admin")
        else:
            flash("Invalid admin credentials.", "error")

    return render_template("secret_admin_login.html")


@app.route("/admin")
@app.route("/admin_portal")
def admin_portal():
    """Main admin dashboard with overview stats"""
    if not session.get("admin_authenticated"):
        flash("Admin authentication required.", "error")
        return redirect("/secret_admin_login")

    # Gather overview statistics
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_parents = Parent.query.count()
    total_classes = Class.query.count()
    total_assignments = AssignedPractice.query.count()

    # Recent activity (last 7 days)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_students = Student.query.filter(Student.created_at >= week_ago).count()
    recent_questions = QuestionLog.query.filter(QuestionLog.created_at >= week_ago).count()

    # Subscription stats
    active_subscriptions = Student.query.filter_by(subscription_active=True).count() + \
                          Teacher.query.filter_by(subscription_active=True).count() + \
                          Parent.query.filter_by(subscription_active=True).count()

    # Flagged content count
    flagged_content = QuestionLog.query.filter_by(flagged=True).count()

    return render_template("admin_dashboard.html",
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_parents=total_parents,
                         total_classes=total_classes,
                         total_assignments=total_assignments,
                         recent_students=recent_students,
                         recent_questions=recent_questions,
                         active_subscriptions=active_subscriptions,
                         flagged_content=flagged_content)


# ============================================================
# DEPRECATED: Old bypass mode routes - replaced with Option 3 admin dashboard
# These routes are kept for backwards compatibility but redirect to new system
# ============================================================

@app.route("/admin_mode/<mode>")
def admin_set_mode(mode):
    """Quick access to different user modes - auto-selects first available user"""
    if not session.get("admin_authenticated"):
        flash("Admin authentication required.", "error")
        return redirect("/secret_admin_login")

    # Handle different modes
    if mode == "student":
        # Find first student and switch to their view
        student = Student.query.first()
        if not student:
            flash("No students found in database. Create a student first.", "error")
            return redirect("/admin")
        return redirect(f"/admin/switch_to_student/{student.id}")

    elif mode == "parent":
        # Find first parent (non-homeschool) and switch to their view
        parent = Parent.query.filter(
            ~Parent.plan.in_(["homeschool_essential", "homeschool_complete"])
        ).first()
        if not parent:
            # If no regular parent, try any parent
            parent = Parent.query.first()
        if not parent:
            flash("No parents found in database. Create a parent first.", "error")
            return redirect("/admin")
        return redirect(f"/admin/switch_to_parent/{parent.id}")

    elif mode == "teacher":
        # Find first teacher and switch to their view
        teacher = Teacher.query.first()
        if not teacher:
            flash("No teachers found in database. Create a teacher first.", "error")
            return redirect("/admin")
        return redirect(f"/admin/switch_to_teacher/{teacher.id}")

    elif mode == "homeschool":
        # Redirect to homeschool switch (which auto-selects homeschool parent)
        return redirect("/admin/switch_to_homeschool")

    else:
        flash("Invalid mode specified.", "error")
        return redirect("/admin")


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

    # Save admin flags before clearing
    admin_authenticated = session.get("admin_authenticated")
    is_owner_flag = session.get("is_owner")

    # Clear session and log in as this student
    session.clear()
    session["student_id"] = student.id

    # Restore admin flags
    if admin_authenticated:
        session["admin_authenticated"] = True
    if is_owner_flag:
        session["is_owner"] = True

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

    # Save admin flags before clearing
    admin_authenticated = session.get("admin_authenticated")
    is_owner_flag = session.get("is_owner")

    # Clear session and log in as this parent
    session.clear()
    session["parent_id"] = parent.id

    # Restore admin flags
    if admin_authenticated:
        session["admin_authenticated"] = True
    if is_owner_flag:
        session["is_owner"] = True

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

    # Save admin flags before clearing
    admin_authenticated = session.get("admin_authenticated")
    is_owner_flag = session.get("is_owner")

    # Clear session and log in as this teacher
    session.clear()
    session["teacher_id"] = teacher.id

    # Restore admin flags
    if admin_authenticated:
        session["admin_authenticated"] = True
    if is_owner_flag:
        session["is_owner"] = True

    flash(f"🔧 Admin mode: Viewing as teacher {teacher.name}", "success")
    return redirect("/teacher/dashboard")


@app.route("/admin/switch_to_homeschool")
def admin_switch_to_homeschool():
    """Admin: switch to homeschool view using a demo homeschool parent account"""
    if not is_admin():
        flash("Access denied.", "error")
        return redirect("/")

    # Find any homeschool parent (one with homeschool plan)
    homeschool_parent = Parent.query.filter(
        (Parent.plan == "homeschool_essential") | (Parent.plan == "homeschool_complete")
    ).first()

    if not homeschool_parent:
        flash("No homeschool parent accounts found. Create one first.", "error")
        return redirect("/admin")

    # Save admin flags before clearing
    admin_authenticated = session.get("admin_authenticated")
    is_owner_flag = session.get("is_owner")

    # Clear session and log in as this homeschool parent
    session.clear()
    session["parent_id"] = homeschool_parent.id
    session["user_role"] = "homeschool"
    session["parent_name"] = homeschool_parent.name

    # Restore admin flags
    if admin_authenticated:
        session["admin_authenticated"] = True
    if is_owner_flag:
        session["is_owner"] = True

    init_user()

    flash(f"🔧 Admin mode: Viewing as homeschool parent {homeschool_parent.name}", "success")
    return redirect("/homeschool/dashboard")


# ============================================================
# ADMIN: CONTENT MODERATION DASHBOARD
# ============================================================

@app.route("/admin/moderation")
def admin_moderation():
    """Admin dashboard for reviewing flagged content and student questions"""
    if not is_admin() and not is_owner(None):
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
    if not is_admin() and not is_owner(None):
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
    if not is_admin() and not is_owner(None):
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
    if not is_admin() and not is_owner(None):
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
    if not is_admin() and not is_owner(None):
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
    from sqlalchemy import case
    student_flags = db.session.query(
        QuestionLog.student_id,
        func.count(QuestionLog.id).label('flagged_count'),
        func.sum(case((QuestionLog.severity == 'high', 1), else_=0)).label('high_count'),
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


# ============================================================
# ADMIN - STUDENTS MANAGEMENT
# ============================================================

@app.route("/admin/students")
def admin_students():
    """View all students with search and filter"""
    if not is_admin():
        flash("Access denied.", "error")
        return redirect("/")

    # Get filter parameters
    search = request.args.get("search", "").strip()
    plan_filter = request.args.get("plan", "")
    page = request.args.get("page", 1, type=int)
    per_page = 50

    # Build query
    query = Student.query

    if search:
        query = query.filter(
            db.or_(
                Student.student_name.ilike(f"%{search}%"),
                Student.student_email.ilike(f"%{search}%")
            )
        )

    if plan_filter:
        query = query.filter_by(plan=plan_filter)

    # Paginate results
    pagination = query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    students = pagination.items

    return render_template("admin_students.html",
                         students=students,
                         pagination=pagination,
                         search=search,
                         plan_filter=plan_filter)


@app.route("/admin/student/<int:student_id>")
def admin_student_detail(student_id):
    """View detailed information about a specific student"""
    if not is_admin():
        flash("Access denied.", "error")
        return redirect("/")

    student = Student.query.get_or_404(student_id)

    # Get recent questions (last 50)
    recent_questions = QuestionLog.query.filter_by(student_id=student_id).order_by(
        QuestionLog.created_at.desc()
    ).limit(50).all()

    # Get assignments and completions
    completions = PracticeCompletion.query.filter_by(student_id=student_id).order_by(
        PracticeCompletion.started_at.desc()
    ).limit(20).all()

    # Get parent info
    parent = Parent.query.get(student.parent_id) if student.parent_id else None

    # Get class info
    student_class = Class.query.get(student.class_id) if student.class_id else None

    return render_template("admin_student_detail.html",
                         student=student,
                         parent=parent,
                         student_class=student_class,
                         recent_questions=recent_questions,
                         completions=completions)


# ============================================================
# ADMIN - TEACHERS MANAGEMENT
# ============================================================

@app.route("/admin/teachers")
def admin_teachers():
    """View all teachers"""
    if not is_admin():
        flash("Access denied.", "error")
        return redirect("/")

    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 50

    query = Teacher.query

    if search:
        query = query.filter(
            db.or_(
                Teacher.name.ilike(f"%{search}%"),
                Teacher.email.ilike(f"%{search}%")
            )
        )

    pagination = query.order_by(Teacher.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    teachers = pagination.items

    return render_template("admin_teachers.html",
                         teachers=teachers,
                         pagination=pagination,
                         search=search)


@app.route("/admin/teacher/<int:teacher_id>")
def admin_teacher_detail(teacher_id):
    """View detailed information about a specific teacher"""
    if not is_admin():
        flash("Access denied.", "error")
        return redirect("/")

    teacher = Teacher.query.get_or_404(teacher_id)

    # Get classes
    classes = Class.query.filter_by(teacher_id=teacher_id).all()

    # Get assignments
    assignments = AssignedPractice.query.filter_by(teacher_id=teacher_id).order_by(
        AssignedPractice.created_at.desc()
    ).limit(20).all()

    # Get lesson plans
    lesson_plans = LessonPlan.query.filter_by(teacher_id=teacher_id).order_by(
        LessonPlan.created_at.desc()
    ).limit(10).all()

    # Calculate total students across all classes
    total_students = sum(len(cls.students or []) for cls in classes)

    return render_template("admin_teacher_detail.html",
                         teacher=teacher,
                         classes=classes,
                         assignments=assignments,
                         lesson_plans=lesson_plans,
                         total_students=total_students)


# ============================================================
# ADMIN - PARENTS MANAGEMENT
# ============================================================

@app.route("/admin/parents")
def admin_parents():
    """View all parents"""
    if not is_admin():
        flash("Access denied.", "error")
        return redirect("/")

    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 50

    query = Parent.query

    if search:
        query = query.filter(
            db.or_(
                Parent.name.ilike(f"%{search}%"),
                Parent.email.ilike(f"%{search}%"),
                Parent.access_code.ilike(f"%{search}%")
            )
        )

    pagination = query.order_by(Parent.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    parents = pagination.items

    return render_template("admin_parents.html",
                         parents=parents,
                         pagination=pagination,
                         search=search)


@app.route("/admin/parent/<int:parent_id>")
def admin_parent_detail(parent_id):
    """View detailed information about a specific parent"""
    if not is_admin():
        flash("Access denied.", "error")
        return redirect("/")

    parent = Parent.query.get_or_404(parent_id)

    # Get children
    students = Student.query.filter_by(parent_id=parent_id).all()

    # Get lesson plans created by parent
    lesson_plans = CustomLessonPlan.query.filter_by(parent_id=parent_id).order_by(
        CustomLessonPlan.created_at.desc()
    ).limit(10).all()

    return render_template("admin_parent_detail.html",
                         parent=parent,
                         students=students,
                         lesson_plans=lesson_plans)


# ============================================================
# ADMIN - ASSIGNMENTS OVERVIEW
# ============================================================

@app.route("/admin/assignments")
def admin_assignments():
    """View all assignments across all classes"""
    if not is_admin():
        flash("Access denied.", "error")
        return redirect("/")

    search = request.args.get("search", "").strip()
    subject_filter = request.args.get("subject", "")
    page = request.args.get("page", 1, type=int)
    per_page = 50

    query = AssignedPractice.query

    if search:
        query = query.filter(AssignedPractice.title.ilike(f"%{search}%"))

    if subject_filter:
        query = query.filter_by(subject=subject_filter)

    pagination = query.order_by(AssignedPractice.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    assignments = pagination.items

    # Get completion stats for each assignment
    assignment_stats = []
    for assignment in assignments:
        completions = PracticeCompletion.query.filter_by(assignment_id=assignment.id).all()
        completed_count = sum(1 for c in completions if c.completed)
        total_assigned = len(completions)

        assignment_stats.append({
            'assignment': assignment,
            'completed': completed_count,
            'total': total_assigned,
            'completion_rate': (completed_count / total_assigned * 100) if total_assigned > 0 else 0
        })

    return render_template("admin_assignments.html",
                         assignment_stats=assignment_stats,
                         pagination=pagination,
                         search=search,
                         subject_filter=subject_filter)


# ============================================================
# STRIPE CHECKOUT
# ============================================================

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

        # Get Stripe customer and subscription IDs
        customer_id = session_obj.get('customer')
        subscription_id = session_obj.get('subscription')

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
            user.stripe_customer_id = customer_id  # Save Stripe customer ID
            user.stripe_subscription_id = subscription_id  # Save Stripe subscription ID

            success, error = safe_commit()
            if success:
                logging.info(f"Activated subscription for {role} {user_id} (Stripe: {customer_id})")
            else:
                logging.error(f"Failed to save subscription: {error}")
    except Exception as e:
        logging.error(f"Error in handle_checkout_completed: {e}")


def handle_subscription_updated(subscription):
    """Handle subscription updates (plan changes, renewals)."""
    try:
        customer_id = subscription.get('customer')
        status = subscription.get('status')

        # Find user by Stripe customer ID
        user = (Student.query.filter_by(stripe_customer_id=customer_id).first() or
                Parent.query.filter_by(stripe_customer_id=customer_id).first() or
                Teacher.query.filter_by(stripe_customer_id=customer_id).first())

        if user:
            # Update subscription status based on Stripe status
            if status == 'active':
                user.subscription_active = True
            elif status in ['canceled', 'unpaid', 'incomplete_expired', 'past_due']:
                user.subscription_active = False

            success, error = safe_commit()
            if success:
                logging.info(f"Updated subscription for customer {customer_id}: {status}")
            else:
                logging.error(f"Failed to update subscription: {error}")
        else:
            logging.warning(f"No user found for customer {customer_id}")

    except Exception as e:
        logging.error(f"Error in handle_subscription_updated: {e}")


def handle_subscription_canceled(subscription):
    """Deactivate user account when subscription is canceled."""
    try:
        customer_id = subscription.get('customer')

        # Find user by Stripe customer ID
        user = (Student.query.filter_by(stripe_customer_id=customer_id).first() or
                Parent.query.filter_by(stripe_customer_id=customer_id).first() or
                Teacher.query.filter_by(stripe_customer_id=customer_id).first())

        if user:
            user.subscription_active = False
            user.plan = "free"
            user.stripe_subscription_id = None  # Clear subscription ID

            success, error = safe_commit()
            if success:
                logging.info(f"Deactivated subscription for customer {customer_id}")
            else:
                logging.error(f"Failed to deactivate subscription: {error}")
        else:
            logging.warning(f"No user found for customer {customer_id}")

    except Exception as e:
        logging.error(f"Error in handle_subscription_canceled: {e}")


def handle_payment_failed(invoice):
    """Handle failed payment (send email, grace period, etc)."""
    try:
        customer_id = invoice.get('customer')
        amount_due = invoice.get('amount_due') / 100  # Convert cents to dollars

        # Find user by Stripe customer ID
        user = (Student.query.filter_by(stripe_customer_id=customer_id).first() or
                Parent.query.filter_by(stripe_customer_id=customer_id).first() or
                Teacher.query.filter_by(stripe_customer_id=customer_id).first())

        if user:
            logging.warning(f"Payment failed for {user.email}: ${amount_due}")
            # TODO: Send email notification to user
            # TODO: Set grace period before deactivating (e.g., 7 days)
        else:
            logging.warning(f"Payment failed for unknown customer {customer_id}: ${amount_due}")

    except Exception as e:
        logging.error(f"Error in handle_payment_failed: {e}")


# ============================================================
# SUBSCRIPTION CANCELLATION ROUTES
# ============================================================

@app.route("/student/cancel-subscription", methods=["GET", "POST"])
def student_cancel_subscription():
    """Cancel student subscription"""
    if "student_id" not in session:
        return redirect("/student/login")

    student_id = session["student_id"]
    student = Student.query.get(student_id)

    if not student:
        flash("Student not found.", "error")
        return redirect("/student/dashboard")

    if request.method == "POST":
        # User confirmed cancellation
        reason = request.form.get("reason", "No reason provided")
        feedback = request.form.get("feedback", "")

        # Log cancellation
        app.logger.info(f"Student {student_id} canceled subscription. Reason: {reason}. Feedback: {feedback}")

        # Cancel in Stripe if subscription ID exists
        if student.stripe_subscription_id:
            try:
                stripe.Subscription.delete(student.stripe_subscription_id)
                app.logger.info(f"Canceled Stripe subscription: {student.stripe_subscription_id}")
            except Exception as e:
                app.logger.error(f"Failed to cancel Stripe subscription: {e}")
                flash("Error canceling subscription in Stripe. Please contact support.", "error")
                return redirect("/student/cancel-subscription")

        # Deactivate subscription locally
        student.subscription_active = False
        student.plan = "free"
        student.stripe_subscription_id = None  # Clear subscription ID

        success, error = safe_commit()

        if success:
            flash("Your subscription has been canceled. You now have a free account.", "info")
            return redirect("/student/dashboard")
        else:
            flash("Error canceling subscription. Please contact support.", "error")
            return redirect("/student/cancel-subscription")

    return render_template("cancel_subscription.html",
                         user_type="student",
                         user=student)


@app.route("/parent/cancel-subscription", methods=["GET", "POST"])
def parent_cancel_subscription():
    """Cancel parent subscription"""
    if "parent_id" not in session:
        return redirect("/parent/login")

    parent_id = session["parent_id"]
    parent = Parent.query.get(parent_id)

    if not parent:
        flash("Parent not found.", "error")
        return redirect("/parent/dashboard")

    if request.method == "POST":
        # User confirmed cancellation
        reason = request.form.get("reason", "No reason provided")
        feedback = request.form.get("feedback", "")

        # Log cancellation
        app.logger.info(f"Parent {parent_id} canceled subscription. Reason: {reason}. Feedback: {feedback}")

        # Cancel in Stripe if subscription ID exists
        if parent.stripe_subscription_id:
            try:
                stripe.Subscription.delete(parent.stripe_subscription_id)
                app.logger.info(f"Canceled Stripe subscription: {parent.stripe_subscription_id}")
            except Exception as e:
                app.logger.error(f"Failed to cancel Stripe subscription: {e}")
                flash("Error canceling subscription in Stripe. Please contact support.", "error")
                return redirect("/parent/cancel-subscription")

        # Deactivate subscription locally
        parent.subscription_active = False
        parent.plan = "free"
        parent.stripe_subscription_id = None  # Clear subscription ID

        success, error = safe_commit()

        if success:
            flash("Your subscription has been canceled. You now have a free account.", "info")
            return redirect("/parent/dashboard")
        else:
            flash("Error canceling subscription. Please contact support.", "error")
            return redirect("/parent/cancel-subscription")

    return render_template("cancel_subscription.html",
                         user_type="parent",
                         user=parent)


@app.route("/teacher/cancel-subscription", methods=["GET", "POST"])
def teacher_cancel_subscription():
    """Cancel teacher subscription"""
    if "teacher_id" not in session:
        return redirect("/teacher/login")

    teacher_id = session["teacher_id"]
    teacher = Teacher.query.get(teacher_id)

    if not teacher:
        flash("Teacher not found.", "error")
        return redirect("/teacher/dashboard")

    if request.method == "POST":
        # User confirmed cancellation
        reason = request.form.get("reason", "No reason provided")
        feedback = request.form.get("feedback", "")

        # Log cancellation
        app.logger.info(f"Teacher {teacher_id} canceled subscription. Reason: {reason}. Feedback: {feedback}")

        # Cancel in Stripe if subscription ID exists
        if teacher.stripe_subscription_id:
            try:
                stripe.Subscription.delete(teacher.stripe_subscription_id)
                app.logger.info(f"Canceled Stripe subscription: {teacher.stripe_subscription_id}")
            except Exception as e:
                app.logger.error(f"Failed to cancel Stripe subscription: {e}")
                flash("Error canceling subscription in Stripe. Please contact support.", "error")
                return redirect("/teacher/cancel-subscription")

        # Deactivate subscription locally
        teacher.subscription_active = False
        teacher.plan = "free"
        teacher.stripe_subscription_id = None  # Clear subscription ID

        success, error = safe_commit()

        if success:
            flash("Your subscription has been canceled. You now have a free account.", "info")
            return redirect("/teacher/dashboard")
        else:
            flash("Error canceling subscription. Please contact support.", "error")
            return redirect("/teacher/cancel-subscription")

    return render_template("cancel_subscription.html",
                         user_type="teacher",
                         user=teacher)


@app.route("/homeschool/cancel-subscription", methods=["GET", "POST"])
def homeschool_cancel_subscription():
    """Cancel homeschool parent subscription"""
    if "parent_id" not in session:
        return redirect("/homeschool/login")

    parent_id = session["parent_id"]
    parent = Parent.query.get(parent_id)

    if not parent:
        flash("Parent not found.", "error")
        return redirect("/homeschool/dashboard")

    if request.method == "POST":
        # User confirmed cancellation
        reason = request.form.get("reason", "No reason provided")
        feedback = request.form.get("feedback", "")

        # Log cancellation
        app.logger.info(f"Homeschool parent {parent_id} canceled subscription. Reason: {reason}. Feedback: {feedback}")

        # Cancel in Stripe if subscription ID exists
        if parent.stripe_subscription_id:
            try:
                stripe.Subscription.delete(parent.stripe_subscription_id)
                app.logger.info(f"Canceled Stripe subscription for homeschool parent {parent.email}: {parent.stripe_subscription_id}")
            except Exception as e:
                app.logger.error(f"Failed to cancel Stripe subscription for homeschool parent {parent.email}: {e}")
                flash("Error canceling subscription in Stripe. Please contact support.", "error")
                return redirect("/homeschool/cancel-subscription")

        # Deactivate subscription locally
        parent.subscription_active = False
        parent.plan = "free"
        parent.stripe_subscription_id = None  # Clear subscription ID

        success, error = safe_commit()

        if success:
            flash("Your subscription has been canceled. You now have a free account.", "info")
            return redirect("/homeschool/dashboard")
        else:
            flash("Error canceling subscription. Please contact support.", "error")
            return redirect("/homeschool/cancel-subscription")

    return render_template("cancel_subscription.html",
                         user_type="homeschool",
                         user=parent)


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
        date_of_birth_str = request.form.get("date_of_birth", "")
        parent_code = safe_text(request.form.get("parent_code", ""), 10).upper().strip()
        signup_mode = request.form.get("signup_mode", "standalone")  # standalone or parent_linked

        # Plan selections for standalone students
        plan = safe_text(request.form.get("plan", ""), 50) or "basic"
        billing = safe_text(request.form.get("billing", ""), 20) or "monthly"

        if not name or not email or not password or not date_of_birth_str:
            flash("Name, email, password, and date of birth are required.", "error")
            return redirect("/student/signup")

        # Parse and validate date of birth
        try:
            date_of_birth = datetime.strptime(date_of_birth_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date of birth format. Please use YYYY-MM-DD.", "error")
            return redirect("/student/signup")

        # Calculate age for COPPA compliance
        today = datetime.utcnow().date()
        age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))

        # COPPA Compliance: Children under 13 MUST have parent linking
        if age < 13 and (signup_mode != "parent_linked" or not parent_code):
            flash("Children under 13 must sign up with a parent access code for COPPA compliance. Please ask your parent or guardian to create an account first.", "error")
            return redirect("/student/signup")

        # Password strength validation
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
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

        # Hash password for secure storage
        password_hash = generate_password_hash(password)

        # Create student account
        new_student = Student(
            student_name=name,
            student_email=email,
            password_hash=password_hash,
            date_of_birth=date_of_birth,
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
@limiter.limit("10 per minute")  # Prevent brute force login attacks
def student_login():
    init_user()
    if request.method == "POST":
        email = safe_email(request.form.get("email", ""))
        password = request.form.get("password", "")

        student = Student.query.filter_by(student_email=email).first()
        if not student:
            flash("No student found with that email.", "error")
            return redirect("/student/login")

        # Verify password
        if not student.password_hash or not check_password_hash(student.password_hash, password):
            flash("Incorrect password. Please try again.", "error")
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

        # Set session after successful authentication
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
@limiter.limit("10 per minute")  # Prevent brute force login attacks
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
@limiter.limit("10 per minute")  # Prevent brute force login attacks
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
    teacher = get_teacher_or_admin()
    if not teacher:
        return redirect("/teacher/login")

    # Admin users bypass subscription checks
    if not is_admin():
        # Check subscription status for teachers
        access_check = check_subscription_access("teacher")
        if access_check != True:
            return access_check  # Redirect to trial_expired

    # Get trial days remaining (0 for admin)
    trial_days_remaining = get_days_remaining_in_trial(teacher) if hasattr(teacher, 'trial_end_date') else 0

    # Count unread messages (0 for admin)
    unread_messages = 0
    if teacher.id:  # Real teacher (not admin)
        unread_messages = Message.query.filter_by(
            recipient_type="teacher",
            recipient_id=teacher.id,
            is_read=False,
        ).count()

    classes = teacher.classes or []
    response = make_response(render_template(
        "teacher_dashboard.html",
        teacher=teacher,
        classes=classes,
        is_owner=is_owner(teacher),
        unread_messages=unread_messages,
        trial_days_remaining=trial_days_remaining,
    ))
    # Prevent caching to ensure layout updates are immediately visible
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


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
    teacher = get_teacher_or_admin()
    if not teacher:
        return redirect("/teacher/login")

    # If admin, show all classes; if real teacher, show their classes
    if is_admin():
        classes = Class.query.all()
    else:
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
        # Generate unique join code
        join_code = generate_join_code()
        cls = Class(
            teacher_id=teacher.id,
            class_name=class_name,
            grade_level=grade,
            join_code=join_code
        )
        db.session.add(cls)
        db.session.commit()

        # Log success
        print(f"✅ Class created: {class_name} (ID: {cls.id}, Join Code: {join_code}, Teacher: {teacher.id})")

        # Verify it was saved
        verify = Class.query.get(cls.id)
        if verify:
            print(f"✅ Class verified in database: {verify.class_name} - Code: {verify.join_code}")
        else:
            print(f"⚠️ Class NOT found after commit!")

        # Save backup after creating class
        backup_classes_to_json()

        flash(f"Class created successfully! Join code: {join_code}", "info")
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
    teacher = get_teacher_or_admin()
    if not teacher:
        return redirect("/teacher/login")

    classes = teacher.classes or []
    assignment_map = {}

    # Show assignments for each class
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


@csrf.exempt
@app.route("/teacher/assignments/<int:assignment_id>/update_schedule", methods=["POST"])
def assignment_update_schedule(assignment_id):
    """Update assignment open_date and due_date."""
    teacher = get_current_teacher()
    if not teacher:
        return jsonify({"error": "Not authenticated"}), 401

    assignment = AssignedPractice.query.get_or_404(assignment_id)
    if not is_owner(teacher) and assignment.teacher_id != teacher.id:
        return jsonify({"error": "Not authorized"}), 403

    data = request.get_json() or {}
    open_str = data.get("open_date", "").strip() if data.get("open_date") else ""
    due_str = data.get("due_date", "").strip() if data.get("due_date") else ""

    # Parse open date
    if open_str:
        try:
            assignment.open_date = datetime.strptime(open_str, "%Y-%m-%dT%H:%M")
        except Exception:
            try:
                assignment.open_date = datetime.strptime(open_str, "%Y-%m-%d")
            except Exception:
                return jsonify({"error": "Invalid open_date format"}), 400
    else:
        assignment.open_date = None

    # Parse due date
    if due_str:
        try:
            assignment.due_date = datetime.strptime(due_str, "%Y-%m-%dT%H:%M")
        except Exception:
            try:
                assignment.due_date = datetime.strptime(due_str, "%Y-%m-%d")
            except Exception:
                return jsonify({"error": "Invalid due_date format"}), 400
    else:
        assignment.due_date = None

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Schedule updated successfully"
    }), 200


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
# STUDENT – JOIN CLASS
# ============================================================

@app.route("/student/join-class", methods=["GET", "POST"])
def student_join_class():
    """Student can join a class using a join code"""
    init_user()

    student_id = session.get("student_id")
    student = Student.query.get(student_id) if student_id else None

    if not student:
        flash("Please log in to join a class.", "error")
        return redirect("/student/login")

    if request.method == "POST":
        join_code = request.form.get("join_code", "").strip().upper()

        if not join_code:
            flash("Please enter a join code.", "error")
            return redirect("/student/join-class")

        # Find class by join code
        class_obj = Class.query.filter_by(join_code=join_code).first()

        if not class_obj:
            flash("Invalid join code. Please check and try again.", "error")
            return redirect("/student/join-class")

        # Check if student is already in a class
        if student.class_id:
            current_class = Class.query.get(student.class_id)
            if current_class and current_class.id == class_obj.id:
                flash(f"You're already enrolled in {class_obj.class_name}!", "info")
                return redirect("/student/assignments")
            else:
                flash(f"You're already enrolled in {current_class.class_name}. Leave that class first to join a new one.", "error")
                return redirect("/student/join-class")

        # Join the class
        student.class_id = class_obj.id
        db.session.commit()

        print(f"✅ Student {student.student_name} (ID:{student.id}) joined class {class_obj.class_name} (Code: {join_code})")
        flash(f"Successfully joined {class_obj.class_name}!", "success")
        return redirect("/student/assignments")

    # GET request - show join form
    return render_template("student_join_class.html", student=student)


@app.route("/student/leave-class", methods=["POST"])
def student_leave_class():
    """Student can leave their current class"""
    init_user()

    student_id = session.get("student_id")
    student = Student.query.get(student_id) if student_id else None

    if not student or not student.class_id:
        flash("You're not enrolled in any class.", "error")
        return redirect("/student/join-class")

    class_name = student.class_ref.class_name if student.class_ref else "Unknown"

    # Remove from class
    student.class_id = None
    db.session.commit()

    print(f"✅ Student {student.student_name} (ID:{student.id}) left class {class_name}")
    flash(f"You've left {class_name}.", "info")
    return redirect("/student/join-class")


# ============================================================
# STUDENT – TAKE ASSIGNMENT
# ============================================================

@app.route("/student/assignments/<int:assignment_id>/start")
def student_start_assignment(assignment_id):
    """Student starts or continues an assignment"""
    init_user()

    student_id = session.get("student_id")
    student = Student.query.get(student_id) if student_id else None

    if not student:
        flash("Please log in to access assignments.", "error")
        return redirect("/student/login")

    # Get assignment
    assignment = AssignedPractice.query.get_or_404(assignment_id)

    # Verify student is in the right class and assignment is published
    if not assignment.is_published:
        flash("This assignment is not yet available.", "error")
        return redirect("/student/assignments")

    if assignment.class_id != student.class_id:
        flash("You don't have access to this assignment.", "error")
        return redirect("/student/assignments")

    # Check if assignment is within open/due dates
    now = datetime.utcnow()
    if assignment.open_date and now < assignment.open_date:
        flash("This assignment is not yet open.", "error")
        return redirect("/student/assignments")

    if assignment.due_date and now > assignment.due_date:
        flash("This assignment is past the due date.", "error")
        return redirect("/student/assignments")

    # Get or create submission record
    submission = StudentSubmission.query.filter_by(
        student_id=student.id,
        assignment_id=assignment.id
    ).first()

    if not submission:
        # Create new submission
        submission = StudentSubmission(
            student_id=student.id,
            assignment_id=assignment.id,
            status="in_progress",
            started_at=datetime.utcnow(),
            answers_json="{}"
        )
        db.session.add(submission)
        db.session.commit()
        print(f"✅ Created submission for student {student.id} on assignment {assignment.id}")
    elif submission.status == "not_started":
        # Update status to in_progress
        submission.status = "in_progress"
        submission.started_at = datetime.utcnow()
        db.session.commit()

    # Parse mission JSON to get questions
    try:
        mission = json.loads(assignment.preview_json) if assignment.preview_json else {}
    except:
        mission = {}

    questions = mission.get("steps", [])

    # Load saved answers if any
    saved_answers = {}
    try:
        saved_answers = json.loads(submission.answers_json) if submission.answers_json else {}
    except:
        saved_answers = {}

    return render_template(
        "student_take_assignment.html",
        assignment=assignment,
        submission=submission,
        questions=questions,
        saved_answers=saved_answers
    )


@app.route("/student/assignments/<int:assignment_id>/save", methods=["POST"])
def student_save_assignment(assignment_id):
    """Student saves progress on an assignment"""
    init_user()

    student_id = session.get("student_id")
    student = Student.query.get(student_id) if student_id else None

    if not student:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    # Get submission
    submission = StudentSubmission.query.filter_by(
        student_id=student.id,
        assignment_id=assignment_id
    ).first()

    if not submission:
        return jsonify({"success": False, "error": "No submission found"}), 404

    # Get answers from request
    data = request.get_json()
    answers = data.get("answers", {})

    # Save answers
    submission.answers_json = json.dumps(answers)
    db.session.commit()

    print(f"✅ Saved progress for student {student.id} on assignment {assignment_id}")
    return jsonify({"success": True})


@app.route("/student/assignments/<int:assignment_id>/submit", methods=["POST"])
def student_submit_assignment(assignment_id):
    """Student submits an assignment for grading"""
    init_user()

    student_id = session.get("student_id")
    student = Student.query.get(student_id) if student_id else None

    if not student:
        flash("Please log in to submit assignments.", "error")
        return redirect("/student/login")

    # Get assignment and submission
    assignment = AssignedPractice.query.get_or_404(assignment_id)
    submission = StudentSubmission.query.filter_by(
        student_id=student.id,
        assignment_id=assignment.id
    ).first()

    if not submission:
        flash("No submission found.", "error")
        return redirect("/student/assignments")

    # Get answers from request
    data = request.get_json() if request.is_json else request.form
    answers = {}

    if request.is_json:
        answers = data.get("answers", {})
    else:
        # Parse form data
        for key, value in request.form.items():
            if key.startswith("answer_"):
                question_idx = key.replace("answer_", "")
                answers[question_idx] = value

    # Save answers and mark as submitted
    submission.answers_json = json.dumps(answers)
    submission.status = "submitted"
    submission.submitted_at = datetime.utcnow()

    # Auto-grade multiple choice questions
    try:
        mission = json.loads(assignment.preview_json) if assignment.preview_json else {}
        questions = mission.get("steps", [])

        total_questions = len(questions)
        correct_count = 0

        for idx, question in enumerate(questions):
            student_answer = answers.get(str(idx), "")
            expected = question.get("expected", [])

            if question.get("type") == "multiple_choice" and expected:
                # For multiple choice, check if answer matches expected
                if student_answer in expected or student_answer == expected[0]:
                    correct_count += 1

        # Calculate score
        if total_questions > 0:
            score = (correct_count / total_questions) * 100
            submission.score = round(score, 2)
            submission.points_earned = correct_count
            submission.points_possible = total_questions
            submission.graded_at = datetime.utcnow()
            submission.status = "graded"

            print(f"✅ Auto-graded assignment {assignment_id} for student {student.id}: {score}% ({correct_count}/{total_questions})")

    except Exception as e:
        print(f"⚠️ Auto-grading failed for assignment {assignment_id}: {e}")
        # Still mark as submitted even if auto-grading fails
        pass

    db.session.commit()

    flash("Assignment submitted successfully!", "success")

    if request.is_json:
        return jsonify({"success": True, "redirect": "/student/assignments"})
    else:
        return redirect("/student/assignments")


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

    # If no preview exists yet, generate one
    if not assignment.preview_json:
        print(f"🔧 [ASSIGNMENT_PREVIEW] No preview_json found for assignment {practice_id}, generating...")

        # Generate AI questions
        try:
            payload = assign_questions(
                subject=assignment.subject or "terra_nova",
                topic=assignment.topic or "General Study",
                grade="8",  # Default grade
                character="everly",
                differentiation_mode=assignment.differentiation_mode or "none",
                student_ability="on_level",
                num_questions=10,
            )

            questions_data = payload.get("questions", [])
            print(f"✅ [ASSIGNMENT_PREVIEW] Generated {len(questions_data)} questions")

            # Build mission JSON
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

            # Store in assignment
            assignment.preview_json = json.dumps(mission_json)
            db.session.commit()
            print(f"💾 [ASSIGNMENT_PREVIEW] Stored preview_json for assignment {practice_id}")

        except Exception as e:
            print(f"❌ [ASSIGNMENT_PREVIEW] Error generating questions: {e}")
            flash("Failed to generate AI questions. Please try again.", "error")
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
# TEACHER - VIEW ASSIGNMENT SUBMISSIONS & GRADING
# ============================================================

@app.route("/teacher/assignments/<int:assignment_id>/submissions")
def teacher_view_submissions(assignment_id):
    """Teacher views all student submissions for an assignment"""
    init_user()

    teacher_id = session.get("teacher_id")
    teacher = Teacher.query.get(teacher_id) if teacher_id else None

    if not teacher:
        flash("Please log in as a teacher.", "error")
        return redirect("/teacher/login")

    assignment = AssignedPractice.query.get_or_404(assignment_id)

    # Verify teacher owns this assignment
    if assignment.teacher_id != teacher.id:
        flash("You don't have access to this assignment.", "error")
        return redirect("/teacher/assignments")

    # Get all students in the class
    students = Student.query.filter_by(class_id=assignment.class_id).all()

    # Get all submissions for this assignment
    submissions = StudentSubmission.query.filter_by(assignment_id=assignment.id).all()

    # Create a map of student_id -> submission
    submission_map = {sub.student_id: sub for sub in submissions}

    # Build list of students with their submission status
    student_submissions = []
    for student in students:
        submission = submission_map.get(student.id)
        student_submissions.append({
            "student": student,
            "submission": submission
        })

    # Parse assignment questions
    try:
        mission = json.loads(assignment.preview_json) if assignment.preview_json else {}
    except:
        mission = {}

    questions = mission.get("steps", [])

    return render_template(
        "teacher_grade_submissions.html",
        assignment=assignment,
        student_submissions=student_submissions,
        questions=questions
    )


@app.route("/teacher/submissions/<int:submission_id>/grade", methods=["GET", "POST"])
def teacher_grade_submission(submission_id):
    """Teacher grades a single student submission"""
    init_user()

    teacher_id = session.get("teacher_id")
    teacher = Teacher.query.get(teacher_id) if teacher_id else None

    if not teacher:
        flash("Please log in as a teacher.", "error")
        return redirect("/teacher/login")

    submission = StudentSubmission.query.get_or_404(submission_id)
    assignment = AssignedPractice.query.get(submission.assignment_id)

    # Verify teacher owns this assignment
    if not assignment or assignment.teacher_id != teacher.id:
        flash("You don't have access to this submission.", "error")
        return redirect("/teacher/assignments")

    if request.method == "POST":
        # Update grade and feedback
        try:
            score = float(request.form.get("score", 0))
            feedback = request.form.get("feedback", "").strip()

            submission.score = min(100, max(0, score))  # Clamp between 0-100
            submission.feedback = feedback if feedback else None
            submission.status = "graded"
            submission.graded_at = datetime.utcnow()

            # Update points if provided
            points_earned = request.form.get("points_earned")
            points_possible = request.form.get("points_possible")

            if points_earned and points_possible:
                submission.points_earned = float(points_earned)
                submission.points_possible = float(points_possible)

            db.session.commit()

            print(f"✅ Teacher {teacher.id} graded submission {submission.id}: {submission.score}%")
            flash("Submission graded successfully!", "success")
            return redirect(f"/teacher/assignments/{assignment.id}/submissions")

        except ValueError as e:
            flash(f"Invalid score value: {e}", "error")

    # GET request - show grading form
    student = Student.query.get(submission.student_id)

    # Parse answers
    try:
        answers = json.loads(submission.answers_json) if submission.answers_json else {}
    except:
        answers = {}

    # Parse questions
    try:
        mission = json.loads(assignment.preview_json) if assignment.preview_json else {}
    except:
        mission = {}

    questions = mission.get("steps", [])

    return render_template(
        "teacher_grade_single.html",
        submission=submission,
        assignment=assignment,
        student=student,
        answers=answers,
        questions=questions
    )


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
    open_str = data.get("open_date", "").strip()
    due_str = data.get("due_date", "").strip()

    if not class_id or not title or not topic:
        return jsonify({"error": "Missing required fields: class_id, title, topic"}), 400

    # Check teacher owns class
    cls = Class.query.get(class_id)
    if not cls:
        return jsonify({"error": "Class not found"}), 404
    if not is_owner(teacher) and cls.teacher_id != teacher.id:
        return jsonify({"error": "Not authorized for this class"}), 403

    # Parse open date (datetime-local format: YYYY-MM-DDTHH:MM)
    open_date = None
    if open_str:
        try:
            open_date = datetime.strptime(open_str, "%Y-%m-%dT%H:%M")
        except Exception:
            try:
                open_date = datetime.strptime(open_str, "%Y-%m-%d")
            except Exception:
                open_date = None

    # Parse due date (datetime-local format: YYYY-MM-DDTHH:MM)
    due_date = None
    if due_str:
        try:
            due_date = datetime.strptime(due_str, "%Y-%m-%dT%H:%M")
        except Exception:
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
        open_date=open_date,
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
    """Generate AI questions and redirect to preview/edit page."""
    teacher = get_teacher_or_admin()
    if not teacher:
        print("❌ [PREVIEW_QUESTIONS] Not authenticated")
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json() or {}
    print(f"✅ [PREVIEW_QUESTIONS] Received data: topic={data.get('topic')}, num_questions={data.get('num_questions')}")

    class_id = data.get("class_id")
    title = safe_text(data.get("title", ""), 200)
    subject = safe_text(data.get("subject", "terra_nova"), 50)
    topic = safe_text(data.get("topic", ""), 500)
    grade = safe_text(data.get("grade", "8"), 10)
    character = safe_text(data.get("character", "everly"), 50)
    differentiation_mode = data.get("differentiation_mode", "none")
    student_ability = data.get("student_ability", "on_level")
    num_questions = data.get("num_questions", 10)
    open_date = data.get("open_date")
    due_date = data.get("due_date")
    manual_questions = data.get("manual_questions")  # For manual assignment creation

    # Check if this is a manual assignment (blank questions)
    if manual_questions:
        questions = manual_questions
    elif num_questions == 0:
        # num_questions=0 signals manual mode but questions weren't provided
        return jsonify({"error": "No questions provided for manual assignment"}), 400
    else:
        # Generate AI questions
        if not topic:
            return jsonify({"error": "Topic is required for AI generation"}), 400

        print(f"🔧 [PREVIEW_QUESTIONS] Generating {num_questions} AI questions for topic: {topic}")
        payload = assign_questions(
            subject=subject,
            topic=topic,
            grade=grade,
            character=character,
            differentiation_mode=differentiation_mode,
            student_ability=student_ability,
            num_questions=num_questions,
        )
        questions = payload.get("questions", [])
        print(f"✅ [PREVIEW_QUESTIONS] Generated {len(questions)} questions")

    # Store in session for preview/edit page
    session["preview_assignment"] = {
        "class_id": class_id,
        "title": title or f"{subject.replace('_', ' ').title()}: {topic}",
        "subject": subject,
        "topic": topic,
        "grade": grade,
        "character": character,
        "differentiation_mode": differentiation_mode,
        "student_ability": student_ability,
        "questions": questions,
        "open_date": open_date,
        "due_date": due_date,
    }
    print(f"💾 [PREVIEW_QUESTIONS] Stored preview data in session with {len(questions)} questions")

    return jsonify({
        "success": True,
        "redirect": "/teacher/preview_assignment"
    }), 200


@app.route("/teacher/preview_assignment")
def teacher_preview_assignment():
    """Show preview/edit page for generated assignment."""
    teacher = get_teacher_or_admin()
    if not teacher:
        print("❌ [PREVIEW_ASSIGNMENT] Not authenticated, redirecting to login")
        return redirect("/teacher/login")

    # Get preview data from session
    preview_data = session.get("preview_assignment")
    if not preview_data:
        print("❌ [PREVIEW_ASSIGNMENT] No session data found - redirecting to dashboard")
        print(f"   Session keys: {list(session.keys())}")
        flash("No preview data found. Please generate questions first.", "error")
        return redirect("/teacher/dashboard")

    print(f"✅ [PREVIEW_ASSIGNMENT] Found session data with {len(preview_data.get('questions', []))} questions")

    # Get classes for dropdown (if admin, show all classes)
    if is_admin() or (hasattr(teacher, '__class__') and teacher.__class__.__name__ == 'AdminTeacher'):
        classes = Class.query.all()
    else:
        classes = teacher.classes or []

    return render_template(
        "teacher_assignment_preview.html",
        preview=preview_data,
        classes=classes,
        teacher=teacher,
        is_owner=is_owner(teacher),
    )


@csrf.exempt
@app.route("/teacher/regenerate_question", methods=["POST"])
def teacher_regenerate_question():
    """Regenerate a single question using AI."""
    teacher = get_teacher_or_admin()
    if not teacher:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json() or {}

    subject = safe_text(data.get("subject", "terra_nova"), 50)
    topic = safe_text(data.get("topic", ""), 500)
    grade = safe_text(data.get("grade", "8"), 10)
    character = safe_text(data.get("character", "everly"), 50)
    differentiation_mode = data.get("differentiation_mode", "none")
    student_ability = data.get("student_ability", "on_level")
    question_type = data.get("question_type", "multiple_choice")  # User can request specific type

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    # Generate a single question
    payload = assign_questions(
        subject=subject,
        topic=topic,
        grade=grade,
        character=character,
        differentiation_mode=differentiation_mode,
        student_ability=student_ability,
        num_questions=1,  # Generate just one question
    )

    questions = payload.get("questions", [])
    if not questions:
        return jsonify({"error": "Failed to generate question"}), 500

    return jsonify({
        "success": True,
        "question": questions[0]
    }), 200


@csrf.exempt
@app.route("/teacher/save_preview_assignment", methods=["POST"])
def teacher_save_preview_assignment():
    """Save edited assignment from preview page to database."""
    teacher = get_teacher_or_admin()
    if not teacher:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json() or {}

    class_id = data.get("class_id")
    title = safe_text(data.get("title", ""), 200)
    questions = data.get("questions", [])
    open_date_str = data.get("open_date")
    due_date_str = data.get("due_date")

    if not class_id:
        return jsonify({"error": "Class is required"}), 400
    if not title:
        return jsonify({"error": "Title is required"}), 400
    if not questions:
        return jsonify({"error": "At least one question is required"}), 400

    # Parse dates
    open_date = None
    due_date = None
    try:
        if open_date_str:
            open_date = datetime.fromisoformat(open_date_str.replace("Z", "+00:00"))
        if due_date_str:
            due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
    except:
        pass

    # Create assignment
    assignment = Practice(
        class_id=int(class_id),
        teacher_id=teacher.id if hasattr(teacher, 'id') and teacher.id else None,
        title=title,
        subject=data.get("subject", "terra_nova"),
        open_date=open_date,
        due_date=due_date,
        is_published=True,
    )
    db.session.add(assignment)
    db.session.flush()  # Get assignment ID

    # Save questions
    for idx, q in enumerate(questions):
        question = PracticeQuestion(
            practice_id=assignment.id,
            question_order=idx + 1,
            prompt=safe_text(q.get("prompt", ""), 1000),
            question_type=q.get("type", "multiple_choice"),
            choices=q.get("choices", []),
            expected_answer=q.get("expected"),
            explanation=safe_text(q.get("explanation", ""), 2000),
        )
        db.session.add(question)

    db.session.commit()

    # Clear session preview data
    session.pop("preview_assignment", None)

    return jsonify({
        "success": True,
        "assignment_id": assignment.id,
        "message": "Assignment created successfully!"
    }), 200


# ============================================================
# TEACHER - GENERATE LESSON PLAN
# ============================================================

@csrf.exempt
@app.route("/teacher/generate_lesson_plan", methods=["POST"])
def teacher_generate_lesson_plan():
    """Generate a six-section lesson plan and save to database."""
    try:
        # Check admin mode FIRST before parent detection
        teacher = get_current_teacher()
        if not teacher and is_admin():
            # Get or create demo teacher account for admin mode
            teacher = Teacher.query.filter_by(email=OWNER_EMAIL).first()
            if not teacher:
                teacher = Teacher(
                    name="Demo Teacher (Admin)",
                    email=OWNER_EMAIL,
                    password="admin_demo"  # Placeholder, won't be used for login
                )
                db.session.add(teacher)
                db.session.commit()

        # If not admin and not teacher, check if parent/homeschool account
        if not teacher and session.get("parent_id"):
            parent_id = session.get("parent_id")
            parent = Parent.query.get(parent_id)
            if parent:
                _, _, _, has_teacher_features = get_parent_plan_limits(parent)
                if has_teacher_features:
                    # This is a homeschool account, use homeschool lesson plan endpoint
                    return jsonify({
                        "error": "Please use the homeschool dashboard to create lesson plans",
                        "redirect": "/homeschool/dashboard"
                    }), 403

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

    except Exception as e:
        app.logger.error(f"Error generating lesson plan: {str(e)}")
        db.session.rollback()
        return jsonify({"error": f"Failed to generate lesson plan: {str(e)}"}), 500

# ============================================================
# TEACHER - LESSON PLAN LIBRARY
# ============================================================

@app.route("/teacher/lesson_plans")
def teacher_lesson_plans():
    """View all saved lesson plans for the logged-in teacher."""
    # Check admin mode FIRST before parent detection
    teacher = get_current_teacher()
    if not teacher and is_admin():
        # Get or create demo teacher account for admin mode
        teacher = Teacher.query.filter_by(email=OWNER_EMAIL).first()
        if not teacher:
            teacher = Teacher(
                name="Demo Teacher (Admin)",
                email=OWNER_EMAIL,
                password="admin_demo"
            )
            db.session.add(teacher)
            db.session.commit()

    # If not admin and not teacher, check if parent/homeschool account
    if not teacher and session.get("parent_id"):
        parent_id = session.get("parent_id")
        parent = Parent.query.get(parent_id)
        if parent:
            _, _, _, has_teacher_features = get_parent_plan_limits(parent)
            if has_teacher_features:
                # Homeschool account - redirect to homeschool dashboard lesson plans
                return redirect("/homeschool/dashboard")
            else:
                # Regular parent - redirect to parent lesson plans
                return redirect("/parent/lesson-plans")

    if not teacher:
        return redirect("/teacher/login")

    # Show lesson plans for this teacher
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

    # Check if assignment has AssignedQuestion records
    assigned_questions = assignment.questions or []
    
    if assigned_questions:
        # Use teacher's pre-defined questions
        steps = []
        for q in assigned_questions:
            # Parse correct answers (handle comma-separated values and whitespace)
            if q.correct_answer:
                expected = [ans.strip() for ans in q.correct_answer.split(",") if ans.strip()]
            else:
                expected = []
            
            step = {
                "prompt": q.question_text,
                "type": q.question_type or "free",
                "expected": expected,
                "hint": "",
                "explanation": q.explanation or ""
            }
            
            # Add choices for multiple choice questions
            if q.question_type == "multiple_choice":
                choices = []
                if q.choice_a: choices.append(q.choice_a)
                if q.choice_b: choices.append(q.choice_b)
                if q.choice_c: choices.append(q.choice_c)
                if q.choice_d: choices.append(q.choice_d)
                step["choices"] = choices
            
            steps.append(step)
        
        practice = {
            "steps": steps,
            "final_message": "Great work! Review your answers."
        }
    else:
        # No AssignedQuestions - fall back to AI generation
        student_id = session.get("student_id")
        student = Student.query.get(student_id) if student_id else None
        grade_level = student.class_ref.grade_level if student and student.class_ref else "8"
        differentiation = getattr(assignment, "differentiation_mode", "none")

        practice = generate_practice_session(
            topic=assignment.topic or assignment.title,
            subject=assignment.subject or "terra_nova",
            grade_level=grade_level,
            character="nova",
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
        student_answer = (request.form.get("student_answer") or "").strip()
        correct_answers = step.get("expected", [])

        # Use robust answer matching (handles numeric formats, case-insensitive, etc.)
        is_correct = False
        for expected in correct_answers:
            if answers_match(student_answer, str(expected)):
                is_correct = True
                break

        step["student_answer"] = student_answer
        step["status"] = "correct" if is_correct else "incorrect"

        # Debug logging for answer matching issues
        if not is_correct:
            app.logger.info(f"Assignment answer mismatch - User: '{student_answer}' | Expected: {correct_answers}")

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

    # Validate subject
    if not validate_subject(subject):
        flash(f"Invalid subject selected.", "error")
        return redirect("/subjects")

    # Get subject config for context
    subject_config = get_subject(subject)

    return render_template(
        "subject_select_form.html",
        subject=subject,
        subject_config=subject_config,
    )


@app.route("/ask-question")
@limiter.limit("30 per hour")  # Limit AI question asking to 30 per hour
def ask_question():
    init_user()
    subject = request.args.get("subject")
    grade = request.args.get("grade")

    # Validate subject
    if not validate_subject(subject):
        flash(f"Invalid subject selected.", "error")
        return redirect("/subjects")

    # Validate and normalize grade
    grade = str(validate_grade(grade))

    # Check if grade is appropriate for this subject
    if not validate_grade_for_subject(subject, grade):
        subject_config = get_subject(subject)
        flash(
            f"Grade {grade} is not available for {subject_config['name']}. "
            f"This subject is for grades {subject_config['min_grade']}-{subject_config['max_grade']}.",
            "warning"
        )
        return redirect(f"/choose-grade?subject={subject}")

    # Store validated grade in session
    session["grade"] = grade

    return render_template(
        "ask_question.html",
        subject=subject,
        grade=grade,
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

    # Get and validate inputs
    subject = request.form.get("subject")
    grade = request.form.get("grade")
    question = request.form.get("question")
    character = session["character"]

    # Validate subject
    if not validate_subject(subject):
        flash("Invalid subject selected.", "error")
        return redirect("/subjects")

    # Validate and normalize grade
    grade = str(validate_grade(grade))

    # Check grade is appropriate for subject
    if not validate_grade_for_subject(subject, grade):
        flash(f"Invalid grade for this subject.", "warning")
        return redirect(f"/choose-grade?subject={subject}")

    # Store validated grade in session
    session["grade"] = grade
    
    # CONTENT MODERATION - Check question safety
    student_id = session.get("user_id")
    moderation_result = moderate_content(question, student_id=student_id, context="question")

    # Initialize log_entry as None (will be created if student_id exists)
    log_entry = None

    # Log the question (flagged or not) - only if we have a real student_id (not admin)
    if student_id:
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
                        if log_entry:
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

    # Parse answer into sections for enhanced display
    from modules.answer_formatter import parse_into_sections
    sections = parse_into_sections(answer) if answer else None

    # Update log with AI response (only if log_entry exists)
    if log_entry:
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
        "subject_enhanced.html",
        subject=subject,
        grade=grade,
        question=question,
        answer=answer,
        sections=sections,
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
@limiter.limit("20 per hour")  # PowerGrid is computationally expensive
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
@limiter.limit("100 per hour")  # Practice steps - reasonable limit for active learners
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

    # Debug logging for answer matching issues
    if not is_correct:
        app.logger.info(f"Answer mismatch - User: '{user_answer_raw}' | Expected: {expected_list}")

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

    # Admin mode: get or create demo parent account
    if not parent_id and is_admin():
        parent = Parent.query.filter_by(email=OWNER_EMAIL).first()
        if not parent:
            parent = Parent(
                name="Demo Parent (Admin)",
                email=OWNER_EMAIL,
                password="admin_demo",
                subscription_tier="homeschool"  # Give full access
            )
            db.session.add(parent)
            db.session.commit()
        parent_id = parent.id
        session["parent_id"] = parent_id
        session["user_role"] = "parent"
        session["parent_name"] = parent.name

    if parent_id:
        if not parent:  # Only query if we didn't already get it above
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
            # Admin mode automatically enables all features
            if is_admin():
                has_teacher_features = True
                student_limit = float('inf')
                lesson_plans_limit = float('inf')
                assignments_limit = float('inf')
                # Admin mode: DON'T auto-redirect so we can view both dashboards separately
            else:
                student_limit, lesson_plans_limit, assignments_limit, has_teacher_features = get_parent_plan_limits(parent)
                # If this is a homeschool parent (non-admin), redirect to homeschool dashboard
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
# HOMESCHOOL AUTH + DASHBOARD (COMBINED PARENT + TEACHER FEATURES)
# ============================================================

@app.route("/homeschool/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")  # Prevent brute force login attacks
def homeschool_login():
    """Dedicated login portal for homeschool users."""
    init_user()
    if request.method == "POST":
        email = safe_email(request.form.get("email", ""))
        password = request.form.get("password", "")

        parent = Parent.query.filter_by(email=email).first()
        if not parent:
            flash("No homeschool account found with that email.", "error")
            return redirect("/homeschool/login")

        if not check_password_hash(parent.password_hash, password):
            flash("Incorrect password.", "error")
            return redirect("/homeschool/login")

        # Check if this parent has a homeschool plan
        _, _, _, has_teacher_features = get_parent_plan_limits(parent)

        if not has_teacher_features:
            flash("This account does not have a homeschool plan. Please upgrade or login at /parent/login", "error")
            return redirect("/homeschool/login")

        session["parent_id"] = parent.id
        session["user_role"] = "homeschool"
        session["parent_name"] = parent.name

        # Generate access code if parent doesn't have one
        if not parent.access_code:
            parent.access_code = generate_parent_access_code()
            db.session.commit()

        flash("Welcome to your Homeschool Dashboard!", "success")
        return redirect("/homeschool/dashboard")

    return render_template("homeschool_login.html")


@app.route("/homeschool/signup", methods=["GET", "POST"])
def homeschool_signup():
    """Dedicated signup portal for homeschool users."""
    init_user()

    # Default to homeschool_essential plan
    selected_plan = request.args.get("plan", "homeschool_essential")

    if request.method == "POST":
        name = safe_text(request.form.get("name", ""), 100)
        email = safe_email(request.form.get("email", ""))
        password = request.form.get("password", "")
        plan = safe_text(request.form.get("plan", ""), 50) or "homeschool_essential"
        billing = safe_text(request.form.get("billing", ""), 20) or "monthly"

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return redirect("/homeschool/signup")

        existing_parent = Parent.query.filter_by(email=email).first()
        if existing_parent:
            flash("An account with that email already exists. Please log in.", "error")
            return redirect("/homeschool/login")

        # Set trial period (7 days for all new accounts)
        trial_start = datetime.utcnow()
        trial_end = trial_start + timedelta(days=7)

        # Generate unique access code for children to link
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
            subscription_active=True,
        )
        db.session.add(parent)
        db.session.commit()

        session["parent_id"] = parent.id
        session["user_role"] = "homeschool"
        session["parent_name"] = parent.name
        session["access_code"] = access_code

        flash(f"Welcome to CozmicLearning Homeschool! Your Child Access Code is: {access_code} - Share this with your children to create their accounts.", "success")
        return redirect("/homeschool/dashboard")

    return render_template("homeschool_signup.html", selected_plan=selected_plan)


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

    # Enable teacher features in admin mode
    if session.get("admin_authenticated"):
        has_teacher_features = True
        student_limit = float('inf')
        lesson_plans_limit = float('inf')
        assignments_limit = float('inf')

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

            # Get plan limits for homeschool features (unless admin mode already set them)
            if not session.get("admin_authenticated"):
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


@csrf.exempt
@app.route("/homeschool/assign_questions", methods=["POST"])
def homeschool_assign_questions():
    """Generate AI questions and create assignment for homeschool parent's students."""
    parent_id = session.get("parent_id")
    if not parent_id:
        return jsonify({"error": "Not authenticated"}), 401

    parent = Parent.query.get(parent_id)
    if not parent:
        return jsonify({"error": "Parent not found"}), 404

    # Check if parent has homeschool plan (teacher features)
    _, _, _, has_teacher_features = get_parent_plan_limits(parent)
    if not has_teacher_features:
        return jsonify({"error": "Homeschool plan required for this feature"}), 403

    data = request.get_json() or {}

    title = safe_text(data.get("title", ""), 120)
    subject = safe_text(data.get("subject", "terra_nova"), 50)
    topic = safe_text(data.get("topic", ""), 500)
    grade = safe_text(data.get("grade", "8"), 10)
    num_questions = data.get("num_questions", 10)
    open_str = data.get("open_date", "").strip() if data.get("open_date") else ""
    due_str = data.get("due_date", "").strip() if data.get("due_date") else ""

    if not title or not topic:
        return jsonify({"error": "Missing required fields: title, topic"}), 400

    # Parse dates
    open_date = None
    if open_str:
        try:
            open_date = datetime.strptime(open_str, "%Y-%m-%d")
        except Exception:
            pass

    due_date = None
    if due_str:
        try:
            due_date = datetime.strptime(due_str, "%Y-%m-%d")
        except Exception:
            pass

    # Generate questions using teacher_tools.assign_questions
    from modules.teacher_tools import assign_questions

    payload = assign_questions(
        subject=subject,
        topic=topic,
        grade=grade,
        character="everly",
        differentiation_mode="none",
        student_ability="on_level",
        num_questions=num_questions,
    )

    # Build preview JSON in mission format
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

    # Create Practice record (not AssignedPractice since no class)
    # For homeschool, we'll create individual practice records for each student
    assignment = Practice(
        teacher_id=None,  # No teacher, this is a homeschool parent
        title=title,
        subject=subject,
        open_date=open_date,
        due_date=due_date,
        is_published=True,
    )
    db.session.add(assignment)
    db.session.flush()

    # Add questions to the practice
    for idx, q in enumerate(questions_data):
        question = PracticeQuestion(
            practice_id=assignment.id,
            question_order=idx + 1,
            prompt=safe_text(q.get("prompt", ""), 1000),
            question_type=q.get("type", "multiple_choice"),
            choices=q.get("choices", []),
            expected_answer=q.get("expected", ""),
            explanation=safe_text(q.get("explanation", ""), 2000),
        )
        db.session.add(question)

    # Assign to all parent's students
    for student in parent.students:
        assigned = AssignedPractice(
            student_id=student.id,
            practice_id=assignment.id,
            assigned_date=datetime.utcnow(),
        )
        db.session.add(assigned)

    db.session.commit()

    return jsonify({
        "success": True,
        "assignment_id": assignment.id,
        "message": f"Assignment created and assigned to {len(parent.students)} student(s)"
    }), 200


@app.route("/homeschool/assignments")
def homeschool_assignments():
    """View all assignments created by homeschool parent."""
    parent_id = session.get("parent_id")
    if not parent_id:
        flash("Please log in as a parent.", "error")
        return redirect("/parent/login")

    parent = Parent.query.get(parent_id)
    if not parent:
        flash("Parent not found.", "error")
        return redirect("/parent/login")

    # Check if parent has homeschool plan
    # Admin mode automatically has teacher features
    if session.get("admin_authenticated"):
        has_teacher_features = True
    else:
        _, _, _, has_teacher_features = get_parent_plan_limits(parent)

    if not has_teacher_features:
        flash("Homeschool plan required for assignment features.", "error")
        return redirect("/homeschool/dashboard")

    # Get all assignments for this parent's students
    student_ids = [s.id for s in parent.students] if parent.students else []

    if student_ids:
        assignments = (
            AssignedPractice.query
            .filter(AssignedPractice.student_id.in_(student_ids))
            .order_by(AssignedPractice.created_at.desc())
            .all()
        )
    else:
        assignments = []

    return render_template(
        "homeschool_assignments.html",
        parent=parent,
        assignments=assignments,
        is_homeschool=True,
    )


@app.route("/homeschool/assignments/create", methods=["GET", "POST"])
def homeschool_create_assignment():
    """Create manual assignment for homeschool parent's students."""
    parent_id = session.get("parent_id")
    if not parent_id:
        flash("Please log in as a parent.", "error")
        return redirect("/parent/login")

    parent = Parent.query.get(parent_id)
    if not parent:
        flash("Parent not found.", "error")
        return redirect("/parent/login")

    # Check if parent has homeschool plan
    # Admin mode automatically has teacher features
    if session.get("admin_authenticated"):
        has_teacher_features = True
    else:
        _, _, _, has_teacher_features = get_parent_plan_limits(parent)

    if not has_teacher_features:
        flash("Homeschool plan required for assignment features.", "error")
        return redirect("/homeschool/dashboard")

    if request.method == "POST":
        title = safe_text(request.form.get("title", ""), 120)
        subject = safe_text((request.form.get("subject", "") or "general"), 50).lower()
        topic = safe_text((request.form.get("topic", "") or ""), 500)
        instructions = safe_text(request.form.get("instructions", ""), 2000)
        due_str = request.form.get("due_date", "").strip()
        open_str = request.form.get("open_date", "").strip()

        if not title:
            flash("Please give this assignment a title.", "error")
            return redirect("/homeschool/assignments/create")

        # Parse dates
        due_date = None
        if due_str:
            try:
                due_date = datetime.strptime(due_str, "%Y-%m-%d")
            except Exception:
                pass

        open_date = None
        if open_str:
            try:
                open_date = datetime.strptime(open_str, "%Y-%m-%d")
            except Exception:
                pass

        # Create a dummy class for homeschool if parent has no students
        # or use first student's class_id if available
        class_id = None
        teacher_id = None

        if parent.students:
            # Use first student as reference
            first_student = parent.students[0]
            class_id = first_student.class_id if hasattr(first_student, 'class_id') else None

        # Note: AssignedPractice requires class_id and teacher_id, but for homeschool
        # we may need to create a virtual class or allow nulls
        # For now, creating with required fields set to placeholder values
        assignment = AssignedPractice(
            class_id=class_id or 0,  # Placeholder - may need to create virtual class
            teacher_id=teacher_id or 0,  # Placeholder for homeschool
            title=title,
            subject=subject,
            topic=topic,
            instructions=instructions,
            open_date=open_date,
            due_date=due_date,
            is_published=True,
        )
        db.session.add(assignment)
        db.session.commit()

        flash("Assignment created. Now add questions to it.", "success")
        return redirect(f"/homeschool/assignments/{assignment.id}")

    return render_template(
        "homeschool_create_assignment.html",
        parent=parent,
        is_homeschool=True,
    )


@app.route("/homeschool/assignments/<int:practice_id>")
def homeschool_assignment_overview(practice_id):
    """View specific assignment details."""
    parent_id = session.get("parent_id")
    if not parent_id:
        flash("Please log in as a parent.", "error")
        return redirect("/parent/login")

    parent = Parent.query.get(parent_id)
    if not parent:
        flash("Parent not found.", "error")
        return redirect("/parent/login")

    # Check if parent has homeschool plan
    _, _, _, has_teacher_features = get_parent_plan_limits(parent)
    if not has_teacher_features:
        flash("Homeschool plan required for assignment features.", "error")
        return redirect("/homeschool/dashboard")

    practice = Practice.query.get_or_404(practice_id)

    # Verify this assignment is for one of this parent's students
    student_ids = [s.id for s in parent.students]
    assigned_students = (
        db.session.query(AssignedPractice)
        .filter(
            AssignedPractice.practice_id == practice_id,
            AssignedPractice.student_id.in_(student_ids)
        )
        .all()
    )

    if not assigned_students:
        flash("This assignment is not for your students.", "error")
        return redirect("/homeschool/assignments")

    questions = practice.questions or []

    return render_template(
        "homeschool_assignment_overview.html",
        parent=parent,
        assignment=practice,
        questions=questions,
        assigned_students=assigned_students,
        is_homeschool=True,
    )


# ============================================================
# HOMESCHOOL - LESSON PLANS
# ============================================================

@csrf.exempt
@app.route("/homeschool/generate-lesson", methods=["POST"])
@limiter.limit("10 per hour")  # Lesson generation is very expensive - strict limit
def homeschool_generate_lesson():
    """Generate AI lesson plan for homeschool parent."""
    parent_id = session.get("parent_id")
    if not parent_id:
        return jsonify({"error": "Not authenticated"}), 401

    parent = Parent.query.get(parent_id)
    if not parent:
        return jsonify({"error": "Parent not found"}), 404

    # Check if parent has homeschool plan (teacher features)
    # Admin mode automatically has teacher features
    if session.get("admin_authenticated"):
        has_teacher_features = True
    else:
        _, _, _, has_teacher_features = get_parent_plan_limits(parent)

    if not has_teacher_features:
        return jsonify({"error": "Homeschool plan required for this feature"}), 403

    data = request.get_json() or {}
    title = safe_text(data.get("title", ""), 200)
    topic = safe_text(data.get("topic", ""), 500)
    subject = safe_text(data.get("subject", "general"), 50)
    grade = safe_text(data.get("grade", "8"), 10)
    duration = data.get("duration", 60)
    biblical_integration = data.get("biblical_integration", False)
    hands_on = data.get("hands_on", True)

    if not title or not topic:
        return jsonify({"error": "Title and topic are required"}), 400

    # Generate lesson plan using AI
    from modules.lesson_plan_generator import generate_lesson_plan

    result = generate_lesson_plan(
        title=title,
        topic=topic,
        subject=subject,
        grade=grade,
        duration=duration,
        biblical_integration=biblical_integration,
        hands_on=hands_on
    )

    if not result.get("success"):
        return jsonify({"error": result.get("error", "Failed to generate lesson plan")}), 500

    lesson_data = result.get("lesson", {})

    # Create HomeschoolLessonPlan record
    lesson_plan = HomeschoolLessonPlan(
        parent_id=parent.id,
        title=title,
        subject=subject,
        grade_level=grade,
        topic=topic,
        duration=duration,
        objectives=lesson_data.get("objectives", []),
        materials=lesson_data.get("materials", []),
        activities=lesson_data.get("activities", []),
        discussion_questions=lesson_data.get("discussion_questions", []),
        assessment=lesson_data.get("assessment", ""),
        homework=lesson_data.get("homework", ""),
        extensions=lesson_data.get("extensions", ""),
        biblical_integration=lesson_data.get("biblical_integration") if biblical_integration else None,
        source="ai_generated",
        status="not_started"
    )

    db.session.add(lesson_plan)
    db.session.commit()

    return jsonify({"success": True, "lesson_plan_id": lesson_plan.id}), 200


@app.route("/parent/lesson-plans")
def parent_lesson_plans():
    """View all lesson plans (homeschool library)."""
    parent_id = session.get("parent_id")
    if not parent_id:
        flash("Please log in as a parent.", "error")
        return redirect("/parent/login")

    parent = Parent.query.get(parent_id)
    if not parent:
        return redirect("/parent/login")

    # Check if parent has homeschool plan
    # Admin mode automatically has teacher features
    if session.get("admin_authenticated"):
        has_teacher_features = True
    else:
        _, _, _, has_teacher_features = get_parent_plan_limits(parent)

    if not has_teacher_features:
        flash("This feature requires a homeschool plan.", "error")
        return redirect("/homeschool/dashboard")

    # Get all lesson plans
    lesson_plans = HomeschoolLessonPlan.query.filter_by(parent_id=parent.id)\
        .order_by(HomeschoolLessonPlan.created_at.desc())\
        .all()

    return render_template(
        "lesson_plans_library.html",
        parent=parent,
        lesson_plans=lesson_plans
    )


@app.route("/parent/lesson-plans/<int:plan_id>")
def parent_lesson_plan_view(plan_id):
    """View a specific lesson plan."""
    parent_id = session.get("parent_id")
    if not parent_id:
        flash("Please log in as a parent.", "error")
        return redirect("/parent/login")

    parent = Parent.query.get(parent_id)
    if not parent:
        return redirect("/parent/login")

    lesson_plan = HomeschoolLessonPlan.query.get_or_404(plan_id)

    # Verify parent owns this lesson plan
    if lesson_plan.parent_id != parent.id:
        flash("Not authorized.", "error")
        return redirect("/parent/lesson-plans")

    return render_template(
        "lesson_plan_detail.html",
        parent=parent,
        lesson_plan=lesson_plan
    )


@app.route("/parent/lesson-plans/<int:plan_id>/favorite", methods=["POST"])
def parent_lesson_plan_favorite(plan_id):
    """Toggle favorite status on a lesson plan."""
    parent_id = session.get("parent_id")
    if not parent_id:
        return jsonify({"error": "Not authenticated"}), 401

    parent = Parent.query.get(parent_id)
    lesson_plan = HomeschoolLessonPlan.query.get_or_404(plan_id)

    # Verify parent owns this lesson plan
    if lesson_plan.parent_id != parent.id:
        return jsonify({"error": "Not authorized"}), 403

    # Toggle favorite
    lesson_plan.is_favorite = not lesson_plan.is_favorite
    db.session.commit()

    return jsonify({"success": True, "is_favorite": lesson_plan.is_favorite}), 200


@app.route("/parent/lesson-plans/<int:plan_id>/delete", methods=["POST"])
def parent_lesson_plan_delete(plan_id):
    """Delete a lesson plan."""
    parent_id = session.get("parent_id")
    if not parent_id:
        flash("Please log in as a parent.", "error")
        return redirect("/parent/login")

    parent = Parent.query.get(parent_id)
    lesson_plan = HomeschoolLessonPlan.query.get_or_404(plan_id)

    # Verify parent owns this lesson plan
    if lesson_plan.parent_id != parent.id:
        flash("Not authorized.", "error")
        return redirect("/parent/lesson-plans")

    db.session.delete(lesson_plan)
    db.session.commit()

    flash("Lesson plan deleted successfully.", "success")
    return redirect("/parent/lesson-plans")


# ============================================================
# ANSWER PAGE ENHANCEMENTS - FEEDBACK & CLARIFICATION
# ============================================================

@app.route("/section_feedback", methods=["POST"])
@csrf.exempt
def section_feedback():
    """Record section-level feedback (thumbs up/down)."""
    init_user()

    data = request.get_json() or {}
    subject = data.get("subject")
    question = data.get("question")
    section = data.get("section")
    feedback = data.get("feedback")

    student_id = session.get("user_id")

    # Log feedback (could be stored in database for analytics)
    app.logger.info(f"Section feedback: student={student_id}, subject={subject}, section={section}, feedback={feedback}")

    # TODO: Store in database for analytics
    # Could create a SectionFeedback model to track this

    return jsonify({"success": True, "message": "Feedback recorded"})


@app.route("/request_clarification", methods=["POST"])
@csrf.exempt
def request_clarification():
    """Handle clarification requests for specific sections."""
    init_user()

    # Check subscription status
    user_role = session.get("user_role")
    if user_role in ["student", "parent", "teacher"]:
        access_check = check_subscription_access(user_role)
        if access_check != True:
            return jsonify({"error": "Your trial has expired. Please upgrade to continue."})

    data = request.get_json() or {}
    subject = data.get("subject")
    question = data.get("question")
    section = data.get("section")
    clarification = data.get("clarification", "")

    grade = session.get("grade", "8")
    character = session.get("character", "everly")

    # Generate clarification response using AI
    prompt = f"""A student asked: "{question}"

They're reading Section {section} of the answer and requested clarification:
"{clarification}"

Provide a clear, concise clarification (2-3 sentences) that directly addresses their confusion while maintaining a friendly, encouraging tone."""

    from modules.ai_client import simple_ai_call

    try:
        reply = simple_ai_call(prompt, grade, character)
        reply_text = reply.get("raw_text") if isinstance(reply, dict) else reply
    except Exception as e:
        app.logger.error(f"Clarification request failed: {e}")
        reply_text = "I'd be happy to clarify! Could you ask your question in a different way? Sometimes rephrasing helps me understand what you need better."

    # Increment question count
    increment_question_count()

    return jsonify({"reply": reply_text})


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
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors with a friendly page."""
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    """Handle 403 errors (forbidden access)."""
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors (server crashes)."""
    app.logger.error(f"500 Error: {str(e)}")
    app.logger.error(traceback.format_exc())
    return render_template('errors/500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Catch-all for any unhandled exceptions."""
    # Log the full error
    app.logger.error(f"Unhandled exception: {str(e)}")
    app.logger.error(traceback.format_exc())

    # Return 500 error page
    return render_template('errors/500.html', error=str(e)), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors."""
    return render_template('errors/429.html'), 429


# ============================================================
# ADMIN MIGRATION BLUEPRINT (Temporary - for arcade setup)
# ============================================================

from admin_migrate import admin_migrate_bp
app.register_blueprint(admin_migrate_bp)


# ============================================================
# MAIN ENTRY (LOCAL DEV)
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)


