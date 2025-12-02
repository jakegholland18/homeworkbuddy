# ============================================================
# PYTHON STANDARD LIBRARIES
# ============================================================

import os
import sys
import logging
import traceback
from datetime import datetime, timedelta

# ============================================================
# TEMPORARY: DELETE OLD DATABASE SO NEW SCHEMA CAN BE CREATED
# ============================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "cozmiclearning.db")

if os.path.exists(db_path):
    print("Deleting outdated cozmiclearning.db...")
    os.remove(db_path)


# ============================================================
# FLASK + SECURITY IMPORTS
# ============================================================

from flask import (
    Flask, render_template, request, redirect, session,
    flash, jsonify, send_file
)
from flask import got_request_exception
from werkzeug.security import generate_password_hash, check_password_hash

# ============================================================
# APP PATHS
# ============================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "website", "templates"),
    static_url_path="/static",
    static_folder=os.path.join(BASE_DIR, "website", "static"),
)

app.secret_key = "b3c2e773eaa84cd6841a9ffa54c918881b9fab30bb02f7128"

# ============================================================
# OWNER OVERRIDE
# ============================================================

OWNER_EMAIL = "jakegholland18@gmail.com"

# ============================================================
# ADMIN PASSWORD FOR FULL SYSTEM ACCESS
# ============================================================
ADMIN_PASSWORD = "Cash&Ollie123"

# ============================================================
# DATABASE + MODELS
# ============================================================

from models import (
    db,
    Teacher,
    Class,
    Student,
    AssessmentResult,
    AssignedPractice,
    AssignedQuestion,
)
from sqlalchemy import func

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cozmiclearning.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Create database tables automatically
with app.app_context():
    db.create_all()

# ============================================================
# DATABASE SCHEMA FIX — Add parent_id to students
# ============================================================
import sqlite3
import os

DB_PATH = os.path.join(BASE_DIR, "cozmiclearning.db")  # same DB as your config

def rebuild_database_if_needed():
    """Rebuild SQLite DB if parent_id column does not exist."""
    if not os.path.exists(DB_PATH):
        print("📦 No database found — creating new one...")
        db.create_all()
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check columns in students table
        cursor.execute("PRAGMA table_info(students);")
        columns = [col[1] for col in cursor.fetchall()]
        conn.close()

        if "parent_id" not in columns:
            print("⚠️ parent_id missing — rebuilding database...")
            os.remove(DB_PATH)
            db.create_all()
        else:
            print("✅ Database OK — parent_id found.")

    except Exception as e:
        print("⚠️ DB check error:", e)
        print("⚠️ Rebuilding DB just in case...")
        try:
            os.remove(DB_PATH)
        except:
            pass
        db.create_all()


with app.app_context():
    rebuild_database_if_needed()

with app.app_context():
    db.create_all()

# ============================================================
# ERROR LOGGING
# ============================================================

logging.basicConfig(level=logging.INFO)


def log_exception(sender, exception, **extra):
    sender.logger.error("Exception during request: %s", traceback.format_exc())


got_request_exception.connect(log_exception, app)

# ============================================================
# LOAD INTERNAL MODULES (AI, SUBJECT HELPERS, PRACTICE)
# ============================================================

sys.path.append(os.path.abspath(os.path.join(BASE_DIR, "modules")))

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import get_all_characters
from modules.practice_helper import generate_practice_session

import modules.math_helper as math_helper
import modules.text_helper as text_helper
import modules.question_helper as question_helper
import modules.science_helper as science_helper
import modules.bible_helper as bible_helper
import modules.history_helper as history_helper
import modules.writing_helper as writing_helper
import modules.study_helper as study_helper
import modules.apologetics_helper as apologetics_helper
import modules.investment_helper as investment_helper
import modules.money_helper as money_helper

# ============================================================
# SUBJECT → FUNCTION MAP
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
    "power_grid": None,
}

# ============================================================
# HELPER – TEACHER + OWNER
# ============================================================


def get_current_teacher():
    tid = session.get("teacher_id")
    if not tid:
        return None
    return Teacher.query.get(tid)


def is_owner(teacher: Teacher | None) -> bool:
    return bool(teacher and teacher.email and teacher.email.lower() == OWNER_EMAIL.lower())


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
        "practice": None,
        "practice_step": 0,          # used as current index
        "practice_attempts": 0,      # legacy; kept but per-question we use practice_progress
        "practice_progress": [],     # per-question state (attempts, status, last_answer, chat)
        # simple role flags for auth portal
        "user_role": None,           # "student", "parent", "teacher", "owner"
        "student_name": None,
        "parent_name": None,
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


def add_xp(amount):
    session["xp"] += amount
    xp_needed = session["level"] * 100

    if session["xp"] >= xp_needed:
        session["xp"] -= xp_needed
        session["level"] += 1
        flash(f"LEVEL UP! You are now Level {session['level']}!", "info")


# ============================================================
# HELPER: FLEXIBLE ANSWER MATCHING FOR PRACTICE
# ============================================================


def _normalize_numeric_token(text: str) -> str:
    """
    Make '4', '4%', '4 percent', '$4', '4 dollars' all reduce to '4'.
    We are intentionally generous for student inputs.
    """
    t = text.lower().strip()
    # remove common words
    for word in ["percent", "perc", "per cent", "dollars", "dollar", "usd"]:
        t = t.replace(word, "")
    # remove commas
    t = t.replace(",", "")
    # remove common symbols
    for ch in ["%", "$"]:
        t = t.replace(ch, "")
    return t.strip()


def _try_float(val: str):
    try:
        return float(val)
    except Exception:
        return None


def answers_match(user_raw: str, expected_raw: str) -> bool:
    """
    Flexible answer comparison:
    - Exact text match (case-insensitive)
    - '4' == '4%' == '4 percent'
    - '5' == '5.0'
    """
    if user_raw is None or expected_raw is None:
        return False

    u_norm = user_raw.strip().lower()
    e_norm = expected_raw.strip().lower()

    # Exact textual match
    if u_norm == e_norm and u_norm != "":
        return True

    # Numeric-form match (ignoring %, $, words like "percent", "dollars")
    u_num_str = _normalize_numeric_token(user_raw)
    e_num_str = _normalize_numeric_token(expected_raw)

    if u_num_str and e_num_str and u_num_str == e_num_str:
        return True

    # Try actual float comparison
    u_num = _try_float(u_num_str)
    e_num = _try_float(e_num_str)
    if u_num is not None and e_num is not None:
        if abs(u_num - e_num) < 1e-6:
            return True

    return False


# ============================================================
# HELPER: RECALC ABILITY + AVERAGE (DB-BASED)
# ============================================================


def recompute_student_ability(student: Student):
    """
    Recalculate a student's ability tier + average_score
    based on their last 10 AssessmentResult rows.
    """
    if not student:
        return

    results = (
        AssessmentResult.query
        .filter_by(student_id=student.id)
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
# ROUTES – CORE + LANDING
# ============================================================

@app.route("/")
def home():
    """
    Public landing page (CozmicLearning branded).
    Students/parents/teachers can still use sidebar + auth portal.
    """
    init_user()
    return render_template("home.html")


# ------------------------------------------------------------

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

    return render_template("subjects.html", planets=planets, character=session["character"])


# ============================================================
# AUTH PORTAL + ROLE SELECTION (FRONT DOOR)
# ============================================================

@app.route("/auth")
def auth_portal():
    """Big entry page with buttons for Student / Parent / Teacher."""
    init_user()
    return render_template("auth_portal.html")


@app.route("/choose_login_role")
def choose_login_role():
    """Older role chooser – keep it wired in case templates link here."""
    init_user()
    return render_template("choose_login_role.html")

# ============================================================
# UNIVERSAL LOGOUT ROUTE
# ============================================================

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/choose_login_role")


# ============================================================
# STUDENT + PARENT AUTH (REAL DB VERSION)
# ============================================================

from werkzeug.security import generate_password_hash, check_password_hash
from models import Student, Parent

# -------------------------------
# STUDENT SIGNUP (DB + parent auto-link)
# -------------------------------
@app.route("/student/signup", methods=["GET", "POST"])
def student_signup():
    init_user()
    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        parent_email = request.form.get("parent_email", "").strip().lower()

        # Validate
        if not name or not email or not password or not parent_email:
            flash("All fields are required, including parent email.", "error")
            return redirect("/student/signup")

        # Check if student already exists
        existing_student = Student.query.filter_by(student_email=email).first()
        if existing_student:
            flash("A student with that email already exists.", "error")
            return redirect("/student/login")

        # 1. Find or create parent
        parent = Parent.query.filter_by(email=parent_email).first()

        if not parent:
            parent = Parent(
                name="Parent of " + name,
                email=parent_email,
                password_hash=generate_password_hash(password)  # TEMP, parent can change later
            )
            db.session.add(parent)
            db.session.commit()

        # 2. Create the student and link to parent
        new_student = Student(
            student_name=name,
            student_email=email,
            parent_id=parent.id
        )

        db.session.add(new_student)
        db.session.commit()

        # 3. Log student in
        session["student_id"] = new_student.id
        session["user_role"] = "student"
        session["student_name"] = name
        session["student_email"] = email

        flash("Welcome to CozmicLearning, " + name + "!", "info")
        return redirect("/dashboard")

    return render_template("student_signup.html")


# -------------------------------
# STUDENT LOGIN (DB VERSION)
# -------------------------------
@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    init_user()
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        student = Student.query.filter_by(student_email=email).first()

        if not student:
            flash("No student found with that email.", "error")
            return redirect("/student/login")

        # No stored password for students yet; can add later
        session["student_id"] = student.id
        session["user_role"] = "student"
        session["student_name"] = student.student_name
        session["student_email"] = student.student_email

        flash("Welcome back, " + student.student_name + "!", "info")
        return redirect("/dashboard")

    return render_template("student_login.html")


# -------------------------------
# PARENT SIGNUP (DB VERSION)
# -------------------------------
@app.route("/parent/signup", methods=["GET", "POST"])
def parent_signup():
    init_user()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return redirect("/parent/signup")

        existing_parent = Parent.query.filter_by(email=email).first()
        if existing_parent:
            flash("Parent with that email already exists. Please login.", "error")
            return redirect("/parent/login")

        new_parent = Parent(
            name=name,
            email=email,
            password_hash=generate_password_hash(password)
        )

        db.session.add(new_parent)
        db.session.commit()

        session["parent_id"] = new_parent.id
        session["user_role"] = "parent"

        flash("Parent account created!", "info")
        return redirect("/parent_dashboard")

    return render_template("parent_signup.html")


# -------------------------------
# PARENT LOGIN (DB VERSION)
# -------------------------------
@app.route("/parent/login", methods=["GET", "POST"])
def parent_login():
    init_user()
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
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

        flash("Logged in!", "info")
        return redirect("/parent_dashboard")

    return render_template("parent_login.html")

# ============================================================
# CHARACTER SELECT
# ============================================================

@app.route("/choose-character")
def choose_character():
    init_user()
    return render_template("choose_character.html", characters=get_all_characters())


@app.route("/select-character", methods=["POST"])
def select_character():
    init_user()
    session["character"] = request.form.get("character")
    return redirect("/dashboard")


# ============================================================
# GRADE SELECT
# ============================================================

@app.route("/choose-grade")
def choose_grade():
    init_user()
    return render_template("subject_select_form.html", subject=request.args.get("subject"))


# ============================================================
# ASK QUESTION
# ============================================================

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


# ============================================================
# POWERGRID SUBMISSION
# ============================================================

@app.route("/powergrid_submit", methods=["POST"])
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
            text = open(path, "r").read()
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


# ============================================================
# PDF DOWNLOAD
# ============================================================

@app.route("/download_study_guide")
def download_study_guide():
    pdf = session.get("study_pdf")

    if not pdf or not os.path.exists(pdf):
        return "PDF not found."

    return send_file(pdf, as_attachment=True)


# ============================================================
# MAIN SUBJECT ANSWER
# ============================================================

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
# FOLLOWUP MESSAGE (SUBJECT CHAT)
# ============================================================

@app.route("/followup_message", methods=["POST"])
def followup_message():
    init_user()

    data = request.get_json() or {}
    grade = data.get("grade")
    character = data.get("character") or session["character"]
    message = data.get("message", "")

    conversation = session.get("conversation", [])
    conversation.append({"role": "user", "content": message})

    reply = study_helper.deep_study_chat(conversation, grade, character)

    conversation.append({"role": "assistant", "content": reply})
    session["conversation"] = conversation
    session.modified = True

    return jsonify({"reply": reply})


# ============================================================
# DEEP STUDY MESSAGE
# ============================================================

@app.route("/deep_study_message", methods=["POST"])
def deep_study_message():
    init_user()

    data = request.get_json() or {}
    message = data.get("message", "")

    grade = session.get("grade", "8")
    character = session.get("character", "everly")

    conversation = session.get("deep_study_chat", [])
    conversation.append({"role": "user", "content": message})

    dialogue_text = ""
    for turn in conversation:
        speaker = "Student" if turn["role"] == "user" else "Tutor"
        dialogue_text += f"{speaker}: {turn['content']}\n"

    prompt = f"""
You are the DEEP STUDY TUTOR.
Warm, patient, conversational.

GRADE LEVEL: {grade}

Conversation so far:
{dialogue_text}

Rules:
• Only answer last student message
• No long essays
• No repeating study guide
• Encourage deeper thinking
"""

    reply = study_buddy_ai(prompt, grade, character)
    reply = reply.get("raw_text") if isinstance(reply, dict) else reply

    conversation.append({"role": "assistant", "content": reply})
    session["deep_study_chat"] = conversation
    session.modified = True

    return jsonify({"reply": reply})


# ============================================================
# PRACTICE MODE — PAGE ROUTE
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


# ============================================================
# PRACTICE MODE — START (TOPIC → FIRST QUESTION)
# ============================================================

@app.route("/start_practice", methods=["POST"])
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
    )

    steps = practice_data.get("steps") or []
    if not steps:
        return jsonify({
            "status": "error",
            "message": "No practice questions were generated. Try a different topic.",
            "character": character,
        })

    # Per-question progress: attempts, status, last_answer, chat
    progress = []
    for _ in steps:
        progress.append({
            "attempts": 0,
            "status": "unanswered",
            "last_answer": "",
            "chat": [],
        })

    session["practice"] = practice_data
    session["practice_progress"] = progress
    session["practice_step"] = 0  # current index
    session["practice_attempts"] = 0
    session.modified = True

    first = steps[0]

    return jsonify({
        "status": "ok",
        "index": 0,
        "total": len(steps),
        "prompt": first.get("prompt", "Let's start practicing!"),
        "type": first.get("type", "free"),        # "multiple_choice" or "free"
        "choices": first.get("choices", []),      # list of options if MC
        "character": character,
        "last_answer": "",
        "chat": [],
    })


# ============================================================
# PRACTICE MODE — NAVIGATE BETWEEN QUESTIONS
# ============================================================

@app.route("/navigate_question", methods=["POST"])
def navigate_question():
    init_user()

    data = request.get_json() or {}
    index = int(data.get("index", 0))

    practice_data = session.get("practice")
    progress = session.get("practice_progress", [])
    character = session.get("character", "everly")

    if not practice_data:
        return jsonify({"status": "error", "message": "No active practice mission.", "character": character})

    steps = practice_data.get("steps") or []
    total = len(steps)

    if index < 0:
        index = 0
    if index >= total:
        index = total - 1

    step = steps[index]
    state = progress[index] if index < len(progress) else {
        "attempts": 0, "status": "unanswered", "last_answer": "", "chat": []
    }

    session["practice_step"] = index
    session.modified = True

    return jsonify({
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
    })


# ============================================================
# PRACTICE MODE — STEP PROCESS (ANSWER CHECK, HINTS, GUIDED)
# (NOTE: does NOT log to analytics; only teacher-entered scores do)
# ============================================================

@app.route("/practice_step", methods=["POST"])
def practice_step():
    init_user()

    data = request.get_json() or {}
    user_answer_raw = data.get("answer") or ""
    user_answer_stripped = user_answer_raw.strip()

    practice_data = session.get("practice")
    index = session.get("practice_step", 0)
    character = session.get("character", "everly")

    if not practice_data:
        return jsonify({
            "status": "error",
            "message": "Practice session not found. Try starting a new practice mission.",
            "character": character
        })

    steps = practice_data.get("steps") or []
    if not steps or index < 0 or index >= len(steps):
        return jsonify({
            "status": "finished",
            "message": practice_data.get("final_message", "Mission complete!"),
            "character": character
        })

    step = steps[index]

    progress = session.get("practice_progress", [])
    if index >= len(progress):
        # safety
        progress.extend(
            [{"attempts": 0, "status": "unanswered", "last_answer": "", "chat": []}
             for _ in range(index - len(progress) + 1)]
        )

    state = progress[index]
    attempts = state.get("attempts", 0)
    expected_list = step.get("expected", [])

    # If they somehow sent blank, treat as incorrect but don't bump attempts
    if not user_answer_stripped:
        return jsonify({
            "status": "incorrect",
            "hint": step.get("hint", "Try giving your best guess, even if you're not sure."),
            "character": character
        })

    # Flexible correctness check
    is_correct = False    # noqa: F841
    for exp in expected_list:
        # MC expected is like ["a"], free-response might be text/number
        if answers_match(user_answer_raw, str(exp)):
            is_correct = True
            break

    # ================= CORRECT ANSWER =================
    if is_correct:
        attempts += 1
        state["attempts"] = attempts
        state["status"] = "correct"
        state["last_answer"] = user_answer_raw
        progress[index] = state
        session["practice_progress"] = progress
        session.modified = True

        # Are all questions done?
        all_done = all(
            s.get("status") in ("correct", "given_up")
            for s in progress
        )

        if all_done:
            return jsonify({
                "status": "finished",
                "message": practice_data.get("final_message", "Great job! Mission complete 🚀"),
                "character": character
            })

        return jsonify({
            "status": "correct",
            "next_prompt": step.get("prompt", ""),  # stay on same question text
            "type": step.get("type", "free"),
            "choices": step.get("choices", []),
            "character": character
        })

    # ================= INCORRECT ANSWER =================
    attempts += 1
    state["attempts"] = attempts
    state["last_answer"] = user_answer_raw
    progress[index] = state
    session["practice_progress"] = progress
    session.modified = True

    # First two wrong tries → hints only
    if attempts < 2:
        return jsonify({
            "status": "incorrect",
            "hint": step.get("hint", "Try thinking about it step by step."),
            "character": character
        })

    # Third (or more) wrong try → guided walkthrough
    state["status"] = "given_up"
    progress[index] = state
    session["practice_progress"] = progress
    session.modified = True

    explanation = step.get(
        "explanation",
        step.get("hint", "Let's walk through how to solve this carefully.")
    )

    # Are all questions done now?
    all_done = all(
        s.get("status") in ("correct", "given_up")
        for s in progress
    )

    if all_done:
        return jsonify({
            "status": "finished",
            "message": practice_data.get("final_message", "Great effort! Mission complete 🚀"),
            "explanation": explanation,
            "character": character
        })

    # Otherwise, send explanation and keep them on this question
    return jsonify({
        "status": "guided",
        "explanation": explanation,
        "next_prompt": step.get("prompt", ""),
        "type": step.get("type", "free"),
        "choices": step.get("choices", []),
        "character": character
    })


# ============================================================
# PRACTICE HELP CHAT — TUTOR + DISPUTE SOLVER
# ============================================================

@app.route("/practice_help_message", methods=["POST"])
def practice_help_message():
    init_user()

    data = request.get_json() or {}
    student_msg = data.get("message", "").strip()

    practice_data = session.get("practice")
    index = session.get("practice_step", 0)
    character = session.get("character", "everly")
    grade = session.get("grade", "8")

    if not practice_data:
        return jsonify({"reply": "I can't find an active practice mission. Try starting one again!"})

    steps = practice_data.get("steps", [])
    if not steps or index < 0 or index >= len(steps):
        return jsonify({"reply": "You've completed all the questions for this mission! Want to start a new one?"})

    progress = session.get("practice_progress", [])
    if index >= len(progress):
        progress.extend(
            [{"attempts": 0, "status": "unanswered", "last_answer": "", "chat": []}
             for _ in range(index - len(progress) + 1)]
        )

    state = progress[index]
    attempts = state.get("attempts", 0)
    chat_history = state.get("chat", [])

    step = steps[index]
    prompt = step.get("prompt", "")
    expected = step.get("expected", [])
    explanation = step.get("explanation", "")
    topic = practice_data.get("topic", "")

    # Add student's message to chat history
    chat_history.append({"role": "student", "content": student_msg})

    # Build a rich tutoring prompt reflecting your preferences
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

    # Save tutor reply into per-question chat history
    chat_history.append({"role": "tutor", "content": reply_text})
    state["chat"] = chat_history
    progress[index] = state
    session["practice_progress"] = progress
    session.modified = True

    return jsonify({"reply": reply_text, "chat": chat_history})


# ============================================================
# DASHBOARD (STUDENT)
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
# PARENT DASHBOARD (SESSION-BASED FOR NOW)
# ============================================================

@app.route("/parent_dashboard")
def parent_dashboard():
    init_user()

    progress = {
        s: (int(data["correct"] / data["questions"] * 100) if data["questions"] else 0)
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
# TEACHER AUTH + DASHBOARD (CLEAN VERSION)
# ============================================================

@app.route("/teacher/signup", methods=["GET", "POST"])
def teacher_signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill out all fields.", "error")
            return redirect("/teacher/signup")

        existing = Teacher.query.filter_by(email=email).first()
        if existing:
            flash("An account with that email already exists.", "error")
            return redirect("/teacher/login")

        hashed = generate_password_hash(password)
        new_teacher = Teacher(name=name, email=email, password_hash=hashed)

        db.session.add(new_teacher)
        db.session.commit()

        session["teacher_id"] = new_teacher.id
        session["user_role"] = "teacher"

        flash("Welcome to CozmicLearning Teacher Portal!", "info")
        return redirect("/teacher/dashboard")

    return render_template("teacher_signup.html")


@app.route("/teacher/login", methods=["GET", "POST"])
def teacher_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
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
# ADMIN LOGIN (password-only)
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

    # FIX: point to choose_login_role instead of missing admin_login.html
    return render_template("choose_login_role.html")

@app.route("/teacher/dashboard")
def teacher_dashboard():
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    classes = teacher.classes if teacher else []

    return render_template(
        "teacher_dashboard.html",
        teacher=teacher,
        classes=classes,
        is_owner=is_owner(teacher),
    )

# ============================================================
# ADMIN DASHBOARD (FULL VISIBILITY)
# ============================================================

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("is_admin"):
        flash("Admin access required.", "error")
        return redirect("/choose_login_role")

    # Counts for stat cards
    total_teachers = Teacher.query.count()
    total_classes = Class.query.count()
    total_students = Student.query.count()

    # Full lists if you need them later for tables
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
        view_mode=session.get("view_mode", "admin")
    )

# ============================================================
# ADMIN VIEW MODE SWITCHER
# ============================================================

@app.route("/admin/switch/<mode>")
def admin_switch(mode):
    if not session.get("is_admin"):
        return redirect("/admin/login")

    valid_modes = ["admin", "teacher", "student", "parent"]

    if mode in valid_modes:
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
# TEACHER – MANAGE CLASSES & STUDENTS
# ============================================================

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

    new_class = Class(teacher_id=teacher.id, class_name=class_name, grade_level=grade)
    db.session.add(new_class)
    db.session.commit()

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

    new_student = Student(class_id=class_id, student_name=name, student_email=email)
    db.session.add(new_student)
    db.session.commit()

    flash("Student added to class.", "info")
    return redirect("/teacher/dashboard")


# ============================================================
# TEACHER – ASSIGNMENTS (CREATION + MANAGEMENT)
# ============================================================

@app.route("/teacher/assignments")
def teacher_assignments():
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    # Get all classes owned by this teacher
    classes = teacher.classes

    # Group assignments by class
    assignment_map = {}
    for cls in classes:
        assignment_map[cls.id] = (
            AssignedPractice.query
            .filter_by(class_id=cls.id, teacher_id=teacher.id)
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
        title = request.form.get("title", "").strip()
        subject = (request.form.get("subject", "") or "general").strip().lower()
        topic = (request.form.get("topic", "") or "").strip()
        instructions = request.form.get("instructions", "").strip()
        due_str = request.form.get("due_date", "").strip()

        if not class_id or not title:
            flash("Please choose a class and give this assignment a title.", "error")
            return redirect("/teacher/assignments/create")

        due_date = None
        if due_str:
            try:
                # Expecting YYYY-MM-DD
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
        )
        db.session.add(practice)
        db.session.commit()

        flash("Assignment created. Now add questions.", "info")
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


@app.route("/teacher/assignments/<int:practice_id>/questions/new", methods=["GET", "POST"])
def assignment_add_question(practice_id):
    teacher = get_current_teacher()
    if not teacher:
        return redirect("/teacher/login")

    assignment = AssignedPractice.query.get_or_404(practice_id)
    if not is_owner(teacher) and assignment.teacher_id != teacher.id:
        flash("Not authorized to modify this assignment.", "error")
        return redirect("/teacher/assignments")

    if request.method == "POST":
        question_text = request.form.get("question_text", "").strip()
        question_type = request.form.get("question_type", "free")

        choice_a = request.form.get("choice_a", "").strip() or None
        choice_b = request.form.get("choice_b", "").strip() or None
        choice_c = request.form.get("choice_c", "").strip() or None
        choice_d = request.form.get("choice_d", "").strip() or None
        correct_answer = request.form.get("correct_answer", "").strip() or None
        explanation = request.form.get("explanation", "").strip() or None
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

    # Re-use create_assignment.html as a simple "add question" form if you want,
    # but we also have explicit templates like edit_assignment.html.
    return render_template(
        "create_assignment.html",
        teacher=teacher,
        assignment=assignment,
        classes=teacher.classes,
        is_owner=is_owner(teacher),
    )


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
        question.question_text = request.form.get("question_text", "").strip()
        question.question_type = request.form.get("question_type", "free")

        question.choice_a = request.form.get("choice_a", "").strip() or None
        question.choice_b = request.form.get("choice_b", "").strip() or None
        question.choice_c = request.form.get("choice_c", "").strip() or None
        question.choice_d = request.form.get("choice_d", "").strip() or None
        question.correct_answer = request.form.get("correct_answer", "").strip() or None
        question.explanation = request.form.get("explanation", "").strip() or None
        question.difficulty_level = request.form.get("difficulty_level", "").strip() or None

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
# STUDENT – VIEW + TAKE ASSIGNMENTS
# ============================================================

@app.route("/student/assignments")
def student_assignments():
    """
    For now, show all active assignments.
    Later we can filter by the student's class_id.
    """
    init_user()
    assignments = (
        AssignedPractice.query
        .order_by(AssignedPractice.created_at.desc())
        .all()
    )
    return render_template(
        "student_assignments.html",
        assignments=assignments,
    )


@app.route("/assignment/<int:practice_id>/take", methods=["GET", "POST"])
def assignment_take(practice_id):
    init_user()
    assignment = AssignedPractice.query.get_or_404(practice_id)
    questions = assignment.questions or []

    if request.method == "POST":
        answers = {}
        num_correct = 0
        total = len(questions)

        for q in questions:
            key = f"q_{q.id}"
            ans = (request.form.get(key) or "").strip()
            answers[q.id] = ans

            if q.correct_answer:
                if q.question_type == "multiple_choice":
                    if ans.lower() == q.correct_answer.lower():
                        num_correct += 1
                else:
                    if answers_match(ans, q.correct_answer):
                        num_correct += 1

        score_percent = (num_correct / max(total, 1)) * 100.0

        # OPTIONAL: if a student_id was provided, log to analytics.
        student_id = request.form.get("student_id", type=int)
        student = Student.query.get(student_id) if student_id else None

        if student:
            result = AssessmentResult(
                student_id=student.id,
                subject=assignment.subject or "general",
                topic=assignment.topic or assignment.title,
                score_percent=score_percent,
                num_correct=num_correct,
                num_questions=total,
                difficulty_level=student.ability_level,
            )
            db.session.add(result)
            db.session.commit()
            recompute_student_ability(student)

        return render_template(
            "assignment_take.html",
            assignment=assignment,
            questions=questions,
            submitted=True,
            num_correct=num_correct,
            num_questions=total,
            score_percent=round(score_percent, 1),
            answers=answers,
        )

    return render_template(
        "assignment_take.html",
        assignment=assignment,
        questions=questions,
        submitted=False,
    )


# ============================================================
# TEACHER – CLASS ANALYTICS (HEATMAP, ABILITY, SUBJECT AVERAGES)
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

    students = cls.students

    # Recompute ability + average for each student based on DB
    for s in students:
        recompute_student_ability(s)

    # Subject-level averages across the class
    subject_averages = {}
    rows = (
        db.session.query(
            AssessmentResult.subject,
            func.avg(AssessmentResult.score_percent)
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

    # Pivot-style heatmap: student x (subject|topic)
    all_results = (
        AssessmentResult.query
        .join(Student, AssessmentResult.student_id == Student.id)
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
        agg[idx]["sum"] += (r.score_percent or 0.0)
        agg[idx]["count"] += 1

    # Build matrix: {student_id: {topic_key: avg_score}}
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


# ============================================================
# TEACHER – RECORD NEW RESULT (FEEDS ANALYTICS)
# ============================================================

@app.route("/teacher/record_result", methods=["POST"])
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

    # Update DB-based ability + average
    recompute_student_ability(student)

    flash("Result recorded.", "info")
    return redirect(f"/teacher/class/{student.class_id}/analytics")


# ============================================================
# TEACHER – STUDENT DETAIL REPORT
# ============================================================

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
        AssessmentResult.query
        .filter_by(student_id=student_id)
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
# LEGAL
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


# ============================================================
# RUN SERVER (LOCAL DEV)
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)

