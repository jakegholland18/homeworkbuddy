import sys
import os
import logging
import traceback
from datetime import datetime, timedelta

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash,
    jsonify
)
from flask import got_request_exception

# ============================================================
# STATIC + TEMPLATE PATHS (RENDER SAFE)
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
# ERROR LOGGING
# ============================================================

def log_exception(sender, exception, **extra):
    sender.logger.error("Exception during request: %s", traceback.format_exc())

got_request_exception.connect(log_exception, app)

# ============================================================
# PYTHON PATH: /modules
# ============================================================

sys.path.append(os.path.abspath(os.path.join(BASE_DIR, "modules")))

# IMPORT AI HELPERS
from modules.shared_ai import study_buddy_ai
from modules.personality_helper import get_all_characters
from modules.answer_formatter import format_answer

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
    "power_grid": study_helper.deep_study_chat,  # Chat-based
    "truth_forge": apologetics_helper.apologetics_answer,
    "stock_star": investment_helper.explain_investing,
    "coin_quest": money_helper.explain_money,
    "terra_nova": question_helper.answer_question,
    "story_verse": text_helper.explain_text,
}

# ============================================================
# INITIALIZE USER SESSION
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
    last = datetime.strptime(session["last_visit"], "%Y-%m-%d").date()

    if today == last:
        return

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
# ROOT → SUBJECTS
# ============================================================

@app.route("/")
def home():
    init_user()
    return redirect("/subjects")

# ============================================================
# SUBJECT PLANET SELECT
# ============================================================

@app.route("/subjects")
def subjects():
    init_user()

    planets = [
        ("chrono_core", "chrono_core.png", "ChronoCore", "History & Social Studies"),
        ("num_forge", "num_forge.png", "NumForge", "Math Planet"),
        ("atom_sphere", "atom_sphere.png", "AtomSphere", "Science Planet"),
        ("story_verse", "story_verse.png", "StoryVerse", "Reading & Literature"),
        ("ink_haven", "ink_haven.png", "InkHaven", "Writing & Composition"),
        ("faith_realm", "faith_realm.png", "FaithRealm", "Bible & Christian Studies"),
        ("coin_quest", "coin_quest.png", "CoinQuest", "Money Skills"),
        ("stock_star", "stock_star.png", "StockStar", "Investing Basics"),
        ("terra_nova", "terra_nova.png", "TerraNova", "General Knowledge"),
        ("power_grid", "power_grid.png", "PowerGrid", "In Depth Study"),
        ("truth_forge", "truth_forge.png", "TruthForge", "Christian Apologetics"),
    ]

    return render_template("subjects.html", planets=planets, character=session["character"])

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
# CHOOSE GRADE
# ============================================================

@app.route("/choose-grade")
def choose_grade():
    init_user()
    return render_template("subject_select_form.html", subject=request.args.get("subject"))

# ============================================================
# ASK QUESTION PAGE
# ============================================================

@app.route("/ask-question")
def ask_question():
    init_user()
    return render_template(
        "ask_question.html",
        subject=request.args.get("subject"),
        grade=request.args.get("grade"),
        character=session["character"],
        characters=get_all_characters()
    )

# ============================================================
# SUBJECT → AI ANSWER (NOT POWERGRID)
# ============================================================

@app.route("/subject", methods=["POST"])
def subject_answer():
    init_user()

    grade = request.form.get("grade")
    subject = request.form.get("subject")
    question = request.form.get("question")
    character = session["character"]

    # --- POWERGRID REDIRECT (Chat Mode Only) ---
    if subject == "power_grid":
        session["deep_memory"] = []
        session["grade_level"] = grade
        return redirect("/deep_study_chat")

    # Normal subjects
    session["progress"].setdefault(subject, {"questions": 0, "correct": 0})
    session["progress"][subject]["questions"] += 1

    func = subject_map.get(subject)
    if func:
        result = func(question, grade, character)
        answer = result.get("raw_text") if isinstance(result, dict) else result
    else:
        answer = "Unknown subject."

    add_xp(20)
    session["tokens"] += 2
    session.modified = True

    return render_template(
        "subject.html",
        subject=subject,
        grade=grade,
        question=question,
        answer=answer,
        character=character,
    )

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
    xp_percent = int((xp / xp_to_next) * 100)

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
# PARENT DASHBOARD
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
# LEGAL PAGES
# ============================================================

@app.route("/terms")
def terms(): return render_template("terms.html")

@app.route("/privacy")
def privacy(): return render_template("privacy.html")

@app.route("/disclaimer")
def disclaimer(): return render_template("disclaimer.html")

# ============================================================
# POWERGRID — CONVERSATIONAL CHAT
# ============================================================

@app.route("/deep_study_chat")
def deep_study_chat_page():
    init_user()
    return render_template(
        "deep_study_chat.html",
        character=session["character"],
        conversation=session.get("deep_memory", []),
    )

@app.route("/deep_study_message", methods=["POST"])
def deep_study_message():
    init_user()

    data = request.get_json(silent=True) or {}
    user_msg = (data.get("message") or "").strip()

    if "deep_memory" not in session:
        session["deep_memory"] = []

    if not user_msg:
        return jsonify({"reply": "Try asking your question in a full sentence 😊"})

    # Save user message
    session["deep_memory"].append({"role": "user", "content": user_msg})

    # --- CORRECT POSITIONAL CALL ---
    grade = session.get("grade_level", "8")
    character = session["character"]

    ai_text = study_helper.deep_study_chat(user_msg, grade, character)

    session["deep_memory"].append({"role": "assistant", "content": ai_text})
    session.modified = True

    return jsonify({"reply": ai_text})

# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)

