# ============================================================
# PYTHON STANDARD LIBRARIES
# ============================================================

import os
import sys
import logging
import traceback
import secrets
from datetime import datetime, timedelta

# ============================================================
# PATHS + DB FILE  (UPDATED FOR PERSISTENT STORAGE)
# ============================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Create persistent DB folder if missing
PERSIST_DIR = os.path.join(BASE_DIR, "persistent_db")
os.makedirs(PERSIST_DIR, exist_ok=True)

# Use persistent SQLite file
DB_PATH = os.path.join(PERSIST_DIR, "cozmiclearning.db")

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

# CSRF protection — enabled globally. We'll exempt JSON POST endpoints below
csrf = CSRFProtect(app)

# ============================================================
# OWNER + ADMIN
# ============================================================

OWNER_EMAIL = "jakegholland18@gmail.com"
ADMIN_PASSWORD = "Cash&Ollie123"

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
        print("📦 No DB found — creating new persistent database...")
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

        # Attempt light, non-destructive ALTERs for new subscription columns
        def ensure_column(table, cols, name, type_sql):
            if name not in cols:
                try:
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {type_sql}")
                    conn.commit()
                    print(f"✅ Added column {table}.{name}")
                except Exception as e:
                    print(f"⚠️ Could not add column {table}.{name}: {e}")

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

        ensure_column("teachers", teacher_cols, "plan", "TEXT")
        ensure_column("teachers", teacher_cols, "billing", "TEXT")
        ensure_column("teachers", teacher_cols, "trial_start", "DATETIME")
        ensure_column("teachers", teacher_cols, "trial_end", "DATETIME")
        ensure_column("teachers", teacher_cols, "subscription_active", "BOOLEAN")

        conn.close()

        warnings = []

        if "parent_id" not in student_cols:
            warnings.append("parent_id missing from students table")

        if "differentiation_mode" not in practice_cols:
            warnings.append("differentiation_mode missing from assigned_practice")

        if warnings:
            print("⚠️ Database schema warning:")
            for w in warnings:
                print("   -", w)
            print("⚠️ No destructive rebuild performed. Apply migrations manually if needed.")
        else:
            print("✅ Database OK — all required columns exist.")

    except Exception as e:
        print("⚠️ DB validation failed:", e)
        print("⚠️ No destructive rebuild performed.")

rebuild_database_if_needed()

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
    }
    for k, v in defaults.items():
        if k not in session:
            session[k] = v
    update_streak()


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


# ============================================================
# XP SYSTEM
# ============================================================


def add_xp(amount: int):
    session["xp"] += amount
    xp_needed = session["level"] * 100
    if session["xp"] >= xp_needed:
        session["xp"] -= xp_needed
        session["level"] += 1
        flash(f"LEVEL UP! You are now Level {session['level']}!", "info")


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


# ------------------------------------------------------------
# SUBJECT PREVIEW (Modal fragment) — Six-section with bullets
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
            "SECTION 1 — OVERVIEW\nPowerGrid is your deep study hub with plan → research → draft → review.\n\n"
            "SECTION 2 — KEY FACTS\n• Plan tasks clearly.\n• Keep sources organized.\n• Iterate drafts.\n\n"
            "SECTION 3 — CHRISTIAN VIEW\nWe value truth, diligence, and wisdom in learning.\n\n"
            "SECTION 4 — AGREEMENT\n• Careful reasoning matters.\n• Evidence strengthens claims.\n\n"
            "SECTION 5 — DIFFERENCE\n• Worldviews shape conclusions.\n\n"
            "SECTION 6 — PRACTICE\n• Build a study plan with 3 steps."
        )
    else:
        func = subject_map.get(subject)
        if not func:
            return "<p>Unknown subject.</p>"

        # Tailored preview prompts per subject for product feel
        preview_prompts = {
            "num_forge": "SECTION 1 — OVERVIEW\nExplain what the Mastery Ladder in math covers.\nSECTION 2 — KEY FACTS\n• Core skills\n• Typical mistakes\n• Tips\nSECTION 3 — CHRISTIAN VIEW\nPurpose, diligence, truth.\nSECTION 4 — AGREEMENT\n• Math consistency matters\nSECTION 5 — DIFFERENCE\n• Approaches to learning\nSECTION 6 — PRACTICE\n• Solve: 3 mixed problems (fractions, percents, algebra).",
            "atom_sphere": "SECTION 1 — OVERVIEW\nExperiment Sim: hypothesis → variables → result.\nSECTION 2 — KEY FACTS\n• Variables\n• Controls\n• Data\nSECTION 3 — CHRISTIAN VIEW\nCreation care, wonder, order.\nSECTION 4 — AGREEMENT\n• Evidence matters\nSECTION 5 — DIFFERENCE\n• Interpretations vary\nSECTION 6 — PRACTICE\n• Design a simple experiment.",
            "ink_haven": "SECTION 1 — OVERVIEW\nRevision Coach: thesis → body → conclusion.\nSECTION 2 — KEY FACTS\n• Thesis clarity\n• Cohesion\n• Tone\nSECTION 3 — CHRISTIAN VIEW\nSpeak truth with grace.\nSECTION 4 — AGREEMENT\n• Clear writing helps\nSECTION 5 — DIFFERENCE\n• Styles vary\nSECTION 6 — PRACTICE\n• Improve a sample paragraph.",
            "chrono_core": "SECTION 1 — OVERVIEW\nTimeline Builder: eras and causes.\nSECTION 2 — KEY FACTS\n• Primary vs secondary sources\n• Cause-effect\n• Context\nSECTION 3 — CHRISTIAN VIEW\nProvidence and responsibility.\nSECTION 4 — AGREEMENT\n• Sources matter\nSECTION 5 — DIFFERENCE\n• Interpretations differ\nSECTION 6 — PRACTICE\n• Place 3 events on a timeline.",
            "story_verse": "SECTION 1 — OVERVIEW\nReading Lab: theme, plot, inference.\nSECTION 2 — KEY FACTS\n• Theme\n• Characters\n• Setting\nSECTION 3 — CHRISTIAN VIEW\nTruth, beauty, goodness.\nSECTION 4 — AGREEMENT\n• Careful reading\nSECTION 5 — DIFFERENCE\n• Interpretations\nSECTION 6 — PRACTICE\n• Identify theme from a short passage.",
            "truth_forge": "SECTION 1 — OVERVIEW\nWorldview Compare: claim, reasons, evidence.\nSECTION 2 — KEY FACTS\n• Claims\n• Logic\n• Evidence\nSECTION 3 — CHRISTIAN VIEW\nFaith seeks understanding.\nSECTION 4 — AGREEMENT\n• Reasoning matters\nSECTION 5 — DIFFERENCE\n• Worldview contrasts\nSECTION 6 — PRACTICE\n• Analyze a claim with two reasons.",
            "faith_realm": "SECTION 1 — OVERVIEW\nPassage Deep Dive: context and application.\nSECTION 2 — KEY FACTS\n• Context\n• Cross-references\n• Application\nSECTION 3 — CHRISTIAN VIEW\nScripture and wisdom.\nSECTION 4 — AGREEMENT\n• Seek understanding\nSECTION 5 — DIFFERENCE\n• Denominational views\nSECTION 6 — PRACTICE\n• Summarize a short passage.",
            "coin_quest": "SECTION 1 — OVERVIEW\nBudget Lab: earn, save, spend, give.\nSECTION 2 — KEY FACTS\n• Needs vs wants\n• Percent allocations\n• Tracking\nSECTION 3 — CHRISTIAN VIEW\nStewardship and generosity.\nSECTION 4 — AGREEMENT\n• Plan wisely\nSECTION 5 — DIFFERENCE\n• Budget styles\nSECTION 6 — PRACTICE\n• Build a 100-dollar budget.",
            "stock_star": "SECTION 1 — OVERVIEW\nROI Simulator: risk vs return.\nSECTION 2 — KEY FACTS\n• Diversification\n• Time horizon\n• Compounding\nSECTION 3 — CHRISTIAN VIEW\nWisdom and prudence.\nSECTION 4 — AGREEMENT\n• Risk management\nSECTION 5 — DIFFERENCE\n• Strategies\nSECTION 6 — PRACTICE\n• Compare two investments.",
            "terra_nova": "SECTION 1 — OVERVIEW\nGeneral Knowledge: curiosity missions.\nSECTION 2 — KEY FACTS\n• Inquiry\n• Evidence\n• Synthesis\nSECTION 3 — CHRISTIAN VIEW\nSeek truth with humility.\nSECTION 4 — AGREEMENT\n• Careful thinking\nSECTION 5 — DIFFERENCE\n• Perspectives\nSECTION 6 — PRACTICE\n• Draft three curious questions.",
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
        f"<h3>Section 1 — Overview</h3><p>{sections.get('overview','')}</p>"
        f"<h3>Section 2 — Key Facts</h3>{render_list(sections.get('key_facts',[]))}"
        f"<h3>Section 3 — Christian View</h3><p>{sections.get('christian_view','')}</p>"
        f"<h3>Section 4 — Agreement</h3>{render_list(sections.get('agreement',[]))}"
        f"<h3>Section 5 — Difference</h3>{render_list(sections.get('difference',[]))}"
        f"<h3>Section 6 — Practice</h3>{render_list(sections.get('practice',[]))}"
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
    if request.method == "POST":
        name = safe_text(request.form.get("name", ""), 100)
        email = safe_email(request.form.get("email", ""))
        password = request.form.get("password", "")
        parent_email = safe_email(request.form.get("parent_email", ""))
        # Pricing selections
        plan = safe_text(request.form.get("plan", ""), 50) or None
        billing = safe_text(request.form.get("billing", ""), 20) or None

        if not name or not email or not password or not parent_email:
            flash("All fields are required, including parent email.", "error")
            return redirect("/student/signup")

        existing_student = Student.query.filter_by(student_email=email).first()
        if existing_student:
            flash("A student with that email already exists.", "error")
            return redirect("/student/login")

        # Find or create parent
        parent = Parent.query.filter_by(email=parent_email).first()
        if not parent:
            trial_start = datetime.utcnow()
            trial_end = trial_start + timedelta(days=7)
            parent = Parent(
                name=f"Parent of {name}",
                email=parent_email,
                password_hash=generate_password_hash(password),
                plan=plan,
                billing=billing,
                trial_start=trial_start,
                trial_end=trial_end,
                subscription_active=False,
            )
            db.session.add(parent)
            db.session.commit()
        else:
            # If parent exists, update selections if provided
            if plan:
                parent.plan = plan
            if billing:
                parent.billing = billing
            if not parent.trial_start and not parent.trial_end:
                parent.trial_start = datetime.utcnow()
                parent.trial_end = parent.trial_start + timedelta(days=7)
            db.session.commit()

        new_student = Student(
            student_name=name,
            student_email=email,
            parent_id=parent.id,
            plan=plan,
            billing=billing,
            trial_start=datetime.utcnow(),
            trial_end=datetime.utcnow() + timedelta(days=7),
            subscription_active=False,
        )
        db.session.add(new_student)
        db.session.commit()

        session["student_id"] = new_student.id
        session["user_role"] = "student"
        session["student_name"] = name
        session["student_email"] = email

        flash(f"Welcome to CozmicLearning, {name}!", "info")
        return redirect("/dashboard")

    return render_template("student_signup.html")


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

        # Currently students don't use a password hash in DB.
        session["student_id"] = student.id
        session["user_role"] = "student"
        session["student_name"] = student.student_name
        session["student_email"] = student.student_email

        flash(f"Welcome back, {student.student_name}!", "info")
        return redirect("/dashboard")

    return render_template("student_login.html")


@app.route("/parent/signup", methods=["GET", "POST"])
def parent_signup():
    init_user()
    if request.method == "POST":
        name = safe_text(request.form.get("name", ""), 100)
        email = safe_email(request.form.get("email", ""))
        password = request.form.get("password", "")
        # Pricing selections
        plan = safe_text(request.form.get("plan", ""), 50) or None
        billing = safe_text(request.form.get("billing", ""), 20) or None

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return redirect("/parent/signup")

        existing_parent = Parent.query.filter_by(email=email).first()
        if existing_parent:
            flash("Parent with that email already exists. Please log in.", "error")
            return redirect("/parent/login")

        trial_start = datetime.utcnow()
        trial_end = trial_start + timedelta(days=7)
        parent = Parent(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            plan=plan,
            billing=billing,
            trial_start=trial_start,
            trial_end=trial_end,
            subscription_active=False,
        )
        db.session.add(parent)
        db.session.commit()

        session["parent_id"] = parent.id
        session["user_role"] = "parent"
        session["parent_name"] = parent.name

        flash("Parent account created!", "info")
        return redirect("/parent_dashboard")

    return render_template("parent_signup.html")


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

        flash("Logged in!", "info")
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

    classes = teacher.classes or []
    return render_template(
        "teacher_dashboard.html",
        teacher=teacher,
        classes=classes,
        is_owner=is_owner(teacher),
    )

# ============================================================
# ADMIN PORTAL
# ============================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        pw = request.form.get("password", "").strip()
        if pw == ADMIN_PASSWORD:
            session["is_admin"] = True
            session["view_mode"] = "admin"
            flash("Admin access granted.", "info")
            return redirect("/admin/dashboard")

        flash("Incorrect admin password.", "error")

    # Reuse role chooser as admin login view
    return render_template("choose_login_role.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("is_admin"):
        flash("Admin access required.", "error")
        return redirect("/choose_login_role")

    total_teachers = Teacher.query.count()
    total_classes = Class.query.count()
    total_students = Student.query.count()

    all_teachers = Teacher.query.all()
    all_classes = Class.query.all()
    all_students = Student.query.all()

    return render_template(
        "admin_dashboard.html",
        total_teachers=total_teachers,
        total_classes=total_classes,
        total_students=total_students,
        teachers=all_teachers,
        classes=all_classes,
        students=all_students,
        view_mode=session.get("view_mode", "admin"),
    )


@app.route("/admin/switch/<mode>")
def admin_switch(mode):
    if not session.get("is_admin"):
        return redirect("/admin/login")

    valid = ["admin", "teacher", "student", "parent"]
    if mode in valid:
        session["view_mode"] = mode

    if mode == "admin":
        return redirect("/admin/dashboard")
    if mode == "teacher":
        return redirect("/teacher/dashboard")
    if mode == "student":
        return redirect("/subjects")
    if mode == "parent":
        return redirect("/parent_dashboard")

    return redirect("/admin/dashboard")


# ============================================================
# ADMIN – VIEW STUDENTS
# ============================================================

@app.route("/admin/students")
def admin_students():
    if not session.get("is_admin"):
        flash("Admin access required.", "error")
        return redirect("/choose_login_role")

    all_students = Student.query.all()
    return render_template(
        "admin_dashboard.html",
        students=all_students,
        view_mode="admin",
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

    cls = Class(teacher_id=teacher.id, class_name=class_name, grade_level=grade)
    db.session.add(cls)
    db.session.commit()
    # Save backup after creating class
    backup_classes_to_json()

    flash("Class created successfully.", "info")
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
# TEACHER — PREVIEW STORED AI MISSION
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
# TEACHER — PUBLISH AI-GENERATED MISSION
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
# TEACHER — AI QUESTION ASSIGNMENT GENERATOR
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

    # Create AssignedPractice record
    assignment = AssignedPractice(
        class_id=class_id,
        teacher_id=teacher.id,
        title=title,
        subject=subject,
        topic=topic,
        due_date=due_date,
        differentiation_mode=differentiation_mode,
        is_published=False,  # Teacher can review before publishing
    )
    db.session.add(assignment)
    db.session.flush()  # Get assignment.id

    # Create AssignedQuestion records from generated questions
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
        "assignment_id": assignment.id,
        "message": f"Generated {len(questions_data)} questions for assignment '{title}'",
        "edit_url": f"/teacher/assignments/{assignment.id}/edit",
    }), 201

# ============================================================
# TEACHER — PREVIEW AI QUESTIONS (NO PERSISTENCE)
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
# TEACHER — GENERATE LESSON PLAN
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
# TEACHER — TEACHER'S PET AI ASSISTANT
# ============================================================

@csrf.exempt
@app.route("/teacher/teachers_pet", methods=["POST"])
def teachers_pet_assistant():
    \"\"\"Teacher's Pet: AI assistant for teachers to ask questions about CozmicLearning and teaching.\"\"\"
    teacher = get_current_teacher()
    if not teacher:
        return jsonify({\"error\": \"Not authenticated\"}), 401

    data = request.get_json() or {}
    question = safe_text(data.get(\"question\", \"\"), 2000)
    history = data.get(\"history\", [])

    if not question:
        return jsonify({\"error\": \"Question is required\"}), 400

    # Build context about CozmicLearning for Teacher's Pet
    context_prompt = \"\"\"You are Teacher's Pet, a warm AI assistant for teachers using CozmicLearning.

RESPONSE STYLE — CRITICAL:
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
• Warm but efficient - respect teachers' time


# ============================================================
# TEACHER — LESSON PLAN LIBRARY
# ============================================================

@app.route(\"/teacher/lesson_plans\")
def teacher_lesson_plans():
    \"\"\"View all saved lesson plans for the logged-in teacher.\"\"\"
    teacher = get_current_teacher()
    if not teacher:
        return redirect(\"/teacher/login\")

    lesson_plans = LessonPlan.query.filter_by(teacher_id=teacher.id).order_by(LessonPlan.created_at.desc()).all()

    return render_template(
        \"lesson_plans_library.html\",
        teacher=teacher,
        lesson_plans=lesson_plans,
        is_owner=is_owner(teacher),
    )


@app.route(\"/teacher/lesson_plans/<int:lesson_id>\")
def view_lesson_plan(lesson_id):
    \"\"\"View a single lesson plan with options to edit, regenerate, export.\"\"\"
    teacher = get_current_teacher()
    if not teacher:
        return redirect(\"/teacher/login\")

    lesson = LessonPlan.query.get_or_404(lesson_id)
    if not is_owner(teacher) and lesson.teacher_id != teacher.id:
        flash(\"Not authorized to view this lesson plan.\", \"error\")
        return redirect(\"/teacher/lesson_plans\")

    # Parse sections from JSON
    sections = json.loads(lesson.sections_json) if lesson.sections_json else {}

    return render_template(
        \"lesson_plan_view.html\",
        teacher=teacher,
        lesson=lesson,
        sections=sections,
        is_owner=is_owner(teacher),
    )


@app.route(\"/teacher/lesson_plans/<int:lesson_id>/edit\", methods=[\"GET\", \"POST\"])
def edit_lesson_plan(lesson_id):
    \"\"\"Edit lesson plan sections manually.\"\"\"
    teacher = get_current_teacher()
    if not teacher:
        return redirect(\"/teacher/login\")

    lesson = LessonPlan.query.get_or_404(lesson_id)
    if not is_owner(teacher) and lesson.teacher_id != teacher.id:
        flash(\"Not authorized to edit this lesson plan.\", \"error\")
        return redirect(\"/teacher/lesson_plans\")

    if request.method == \"POST\":
        # Update sections
        sections = {
            \"overview\": safe_text(request.form.get(\"overview\", \"\"), 5000),
            \"key_facts\": safe_text(request.form.get(\"key_facts\", \"\"), 5000),
            \"christian_view\": safe_text(request.form.get(\"christian_view\", \"\"), 5000),
            \"agreement\": safe_text(request.form.get(\"agreement\", \"\"), 5000),
            \"difference\": safe_text(request.form.get(\"difference\", \"\"), 5000),
            \"practice\": safe_text(request.form.get(\"practice\", \"\"), 5000),
        }
        
        # Rebuild full text
        full_text = f\"\"\"SECTION 1 — OVERVIEW
{sections['overview']}

SECTION 2 — KEY FACTS
{sections['key_facts']}

SECTION 3 — CHRISTIAN VIEW
{sections['christian_view']}

SECTION 4 — AGREEMENT
{sections['agreement']}

SECTION 5 — DIFFERENCE
{sections['difference']}

SECTION 6 — PRACTICE
{sections['practice']}\"\"\"

        lesson.sections_json = json.dumps(sections)
        lesson.full_text = full_text
        lesson.title = safe_text(request.form.get(\"title\", lesson.title), 200)
        db.session.commit()
        
        flash(\"Lesson plan updated.\", \"info\")
        return redirect(f\"/teacher/lesson_plans/{lesson_id}\")

    sections = json.loads(lesson.sections_json) if lesson.sections_json else {}

    return render_template(
        \"lesson_plan_edit.html\",
        teacher=teacher,
        lesson=lesson,
        sections=sections,
        is_owner=is_owner(teacher),
    )


@csrf.exempt
@app.route(\"/teacher/lesson_plans/<int:lesson_id>/regenerate_section\", methods=[\"POST\"])
def regenerate_lesson_section(lesson_id):
    \"\"\"Regenerate a specific section of a lesson plan.\"\"\"
    teacher = get_current_teacher()
    if not teacher:
        return jsonify({\"error\": \"Not authenticated\"}), 401

    lesson = LessonPlan.query.get_or_404(lesson_id)
    if not is_owner(teacher) and lesson.teacher_id != teacher.id:
        return jsonify({\"error\": \"Not authorized\"}), 403

    data = request.get_json() or {}
    section_name = data.get(\"section\")  # overview, key_facts, etc.

    if section_name not in [\"overview\", \"key_facts\", \"christian_view\", \"agreement\", \"difference\", \"practice\"]:
        return jsonify({\"error\": \"Invalid section name\"}), 400

    # Regenerate full lesson and extract the requested section
    new_lesson = generate_lesson_plan(
        subject=lesson.subject,
        topic=lesson.topic,
        grade=lesson.grade,
        character=\"everly\",
    )

    new_sections = new_lesson.get(\"sections\", {})
    new_section_content = new_sections.get(section_name, \"\")

    return jsonify({
        \"success\": True,
        \"section\": section_name,
        \"content\": new_section_content,
    }), 200


@app.route(\"/teacher/lesson_plans/<int:lesson_id>/print\")
def print_lesson_plan(lesson_id):
    \"\"\"Print-friendly view of lesson plan.\"\"\"
    teacher = get_current_teacher()
    if not teacher:
        return redirect(\"/teacher/login\")

    lesson = LessonPlan.query.get_or_404(lesson_id)
    if not is_owner(teacher) and lesson.teacher_id != teacher.id:
        flash(\"Not authorized to view this lesson plan.\", \"error\")
        return redirect(\"/teacher/lesson_plans\")

    sections = json.loads(lesson.sections_json) if lesson.sections_json else {}

    return render_template(
        \"lesson_plan_print.html\",
        lesson=lesson,
        sections=sections,
    )


@app.route(\"/teacher/lesson_plans/<int:lesson_id>/export/pdf\")
def export_lesson_plan_pdf(lesson_id):
    \"\"\"Export lesson plan as PDF (placeholder for now - can use reportlab later).\"\"\"
    teacher = get_current_teacher()
    if not teacher:
        return redirect(\"/teacher/login\")

    lesson = LessonPlan.query.get_or_404(lesson_id)
    if not is_owner(teacher) and lesson.teacher_id != teacher.id:
        flash(\"Not authorized to export this lesson plan.\", \"error\")
        return redirect(\"/teacher/lesson_plans\")

    # For now, redirect to print view - can add PDF generation later
    return redirect(f\"/teacher/lesson_plans/{lesson_id}/print\")


# ============================================================
# TEACHER — TEACHER'S PET AI ASSISTANT (CONTINUED)
# ============================================================

@csrf.exempt
@app.route(\"/teacher/teachers_pet\", methods=[\"POST\"])
def teachers_pet_assistant():
    \"\"\"Teacher's Pet: AI assistant for teachers to ask questions about CozmicLearning and teaching.\"\"\"
    teacher = get_current_teacher()
    if not teacher:
        return jsonify({\"error\": \"Not authenticated\"}), 401

    data = request.get_json() or {}
    question = safe_text(data.get(\"question\", \"\"), 2000)
    history = data.get(\"history\", [])

    if not question:
        return jsonify({\"error\": \"Question is required\"}), 400

    # Build context about CozmicLearning for Teacher's Pet
    context_prompt = \"\"\"You are Teacher's Pet, a warm AI assistant for teachers using CozmicLearning.

RESPONSE STYLE — CRITICAL:
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
    # POST — student action (answer or hint)
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
    # GET — show question normally
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
    )


@app.route("/subject", methods=["POST"])
def subject_answer():
    init_user()

    grade = request.form.get("grade")
    subject = request.form.get("subject")
    question = request.form.get("question")
    character = session["character"]

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

    session["conversation"] = []
    session.modified = True

    add_xp(20)
    session["tokens"] += 2

    return render_template(
        "subject.html",
        subject=subject,
        grade=grade,
        question=question,
        answer=answer,
        character=character,
        conversation=session["conversation"],
        pdf_url=None,
    )


# ============================================================
# FOLLOWUP / DEEP STUDY (CHAT MODES)
# ============================================================

@app.route("/followup_message", methods=["POST"])
@csrf.exempt
def followup_message():
    init_user()

    data = request.get_json() or {}
    grade = data.get("grade")
    character = data.get("character") or session["character"]
    message = data.get("message", "")

    conversation = session.get("conversation", [])
    conversation.append({"role": "user", "content": message})

    reply = study_helper.deep_study_chat(conversation, grade, character)
    reply_text = reply.get("raw_text") if isinstance(reply, dict) else reply

    conversation.append({"role": "assistant", "content": reply_text})
    session["conversation"] = conversation
    session.modified = True

    return jsonify({"reply": reply_text})


@app.route("/deep_study_message", methods=["POST"])
@csrf.exempt
def deep_study_message():
    init_user()

    data = request.get_json() or {}
    message = data.get("message", "")

    grade = session.get("grade", "8")
    character = session.get("character", "everly")

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

    conversation.append({"role": "assistant", "content": reply_text})
    session["deep_study_chat"] = conversation
    session.modified = True

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
    uploaded = request.files.get("file")

    session["grade"] = grade

    text = ""
    if uploaded and uploaded.filename:
        ext = uploaded.filename.lower()
        path = os.path.join("/tmp", uploaded.filename)
        uploaded.save(path)

        if ext.endswith(".txt"):
            with open(path, "r") as f:
                text = f.read()
        elif ext.endswith(".pdf"):
            try:
                from PyPDF2 import PdfReader

                pdf = PdfReader(path)
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            except Exception:
                text = "Could not read PDF content."
        else:
            text = f"Study this:\n\n{topic}"
    else:
        text = topic or "No topic provided."

    study_guide = study_helper.generate_powergrid_master_guide(
        text, grade, session["character"]
    )

    import uuid
    from textwrap import wrap

    pdf_path = f"/tmp/study_guide_{uuid.uuid4().hex}.pdf"

    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        y = height - 50

        for line in study_guide.split("\n"):
            for wrapped in wrap(line, 110):
                c.drawString(40, y, wrapped)
                y -= 15
                if y < 40:
                    c.showPage()
                    y = height - 50

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
        "subject.html",
        subject="power_grid",
        grade=grade,
        question=topic,
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
You are COZMICLEARNING — a warm, patient cozmic mentor guiding students through the galaxy of learning.

The student is asking for help about a practice question.

CONTEXT:
- Topic: {topic}
- Grade level: {grade}
- Character voice: {character}

Current question:
\"\"\"{prompt}\"\"\"

Expected correct answers (could be letters or short answers):
{expected}

Official explanation / teacher notes:
\"\"\"{explanation}\"\"\"

Attempts used so far on this question: {attempts}

CHAT HISTORY for this question:
{chat_history}

STUDENT JUST SAID:
\"\"\"{student_msg}\"\"\"

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
    )


# ============================================================
# PARENT DASHBOARD (SESSION-BASED SNAPSHOT)
# ============================================================

@app.route("/parent_dashboard")
def parent_dashboard():
    init_user()

    progress = {
        s: (
            int(data["correct"] / data["questions"] * 100)
            if data["questions"]
            else 0
        )
        for s, data in session["progress"].items()
    }

    return render_template(
        "parent_dashboard.html",
        progress=progress,
        utilization=session["usage_minutes"],
        xp=session["xp"],
        level=session["level"],
        tokens=session["tokens"],
        character=session["character"],
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

# TEMPORARY — DEBUG TEACHER ID
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


