import sys
import os
from flask import Flask, render_template, request, redirect, session, flash
from datetime import datetime, timedelta

# ============================================================
# FIX STATIC + TEMPLATE PATHS FOR RENDER
# ============================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "website", "templates"),
    static_url_path="/static",
    static_folder=os.path.join(BASE_DIR, "website", "static")
)
import logging
import traceback
from flask import got_request_exception

def log_exception(sender, exception, **extra):
    sender.logger.error("Exception during request: %s", traceback.format_exc())

got_request_exception.connect(log_exception, app)

app.secret_key = "b3c2e773eaa84cd6841a9ffa54c918881b9fab30bb02f7128"

# Make sure Python can see /modules
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, "modules")))

# ---------------------------------------
# IMPORT AI LOGIC + CHARACTER DATA
# ---------------------------------------

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
# HIDDEN SHOP ITEMS
# ============================================================

SHOP_ITEMS = {
    "space_glasses": {"name": "Space Glasses", "price": 30},
    "angel_aura": {"name": "Angel Aura", "price": 50},
    "golden_cape": {"name": "Golden Cape", "price": 75},
    "galaxy_trail": {"name": "Galaxy Trail", "price": 100},
    "meteor_boots": {"name": "Meteor Boots", "price": 40},
    "cosmic_wings": {"name": "Cosmic Wings", "price": 90},

    "double_xp_card": {"name": "Double XP (30 minutes)", "price": 60},
    "token_booster": {"name": "Galaxy Token Booster", "price": 40},
    "subject_pass": {"name": "Subject Fast Pass (24hr)", "price": 25},

    "mystery_crate": {"name": "Mystery Crate", "price": 50},
    "legendary_crate": {"name": "Legendary Crate", "price": 120},

    "valor_galaxy_armor": {"name": "Valor Strike: Galaxy Armor", "price": 200},
    "everly_starlight": {"name": "Princess Everly: Starlight Dress", "price": 175},
    "nova_hypercoat": {"name": "Nova Circuit: Hypercoat", "price": 150},

    "shield_of_faith": {"name": "Shield of Faith", "price": 60},
    "light_aura": {"name": "Aura of Light", "price": 80},
    "dove_trail": {"name": "Dove Trail", "price": 75},
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

        "progress": {}
    }

    for key, val in defaults.items():
        if key not in session:
            session[key] = val

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
# XP & LEVEL SYSTEM
# ============================================================

def add_xp(amount):
    session["xp"] += amount

    xp_needed = session["level"] * 100
    if session["xp"] >= xp_needed:
        session["xp"] -= xp_needed
        session["level"] += 1
        flash(f"LEVEL UP! You reached Level {session['level']}!", "info")

# ============================================================
# ROOT → SUBJECTS
# ============================================================

@app.route("/")
def home():
    init_user()
    return redirect("/subjects")

# ============================================================
# SUBJECT PLANETS SCREEN
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
    ("truth_forge", "truth_forge.png", "TruthForge", "Christian Apologetics")
    ]

    return render_template("subjects.html", planets=planets, character=session["character"])

# ============================================================
# CHARACTER SELECTION
# ============================================================

@app.route("/choose-character")
def choose_character():
    init_user()
    characters = get_all_characters()
    return render_template("choose_character.html", characters=characters)

@app.route("/select-character", methods=["POST"])
def select_character():
    init_user()
    chosen = request.form.get("character")
    if chosen:
        session["character"] = chosen
    return redirect("/dashboard")

# ============================================================
# CHOOSE GRADE
# ============================================================

@app.route("/choose-grade")
def choose_grade():
    init_user()
    subject = request.args.get("subject")
    return render_template("subject_select_form.html", subject=subject)

# ============================================================
# ASK QUESTION SCREEN
# ============================================================

@app.route("/ask-question")
def ask_question():
    init_user()
    subject = request.args.get("subject")
    grade = request.args.get("grade")

    characters = get_all_characters()

    return render_template(
        "ask_question.html",
        subject=subject,
        grade=grade,
        character=session["character"],
        characters=characters
    )

# ============================================================
# SUBJECT → AI ANSWER PAGE  (FIXED)
# ============================================================

@app.route("/subject", methods=["POST"])
def subject_answer():
    init_user()

    grade = request.form.get("grade")
    subject = request.form.get("subject")
    question = request.form.get("question")
    character = session["character"]

    # Track progress safely
    session["progress"].setdefault(subject, {"questions": 0, "correct": 0})
    session["progress"][subject]["questions"] += 1

    subject_map = {
        "num_forge": math_helper.explain_math,
        "atom_sphere": science_helper.explain_science,
        "faith_realm": bible_helper.bible_lesson,
        "chrono_core": history_helper.explain_history,
        "ink_haven": writing_helper.help_write,
        "power_grid": study_helper.deep_study,
        "truth_forge": apologetics_helper.apologetics_answer,
        "stock_star": investment_helper.explain_investing,
        "coin_quest": money_helper.explain_money,
        "terra_nova": question_helper.answer_question,
        "story_verse": text_helper.explain_text,
    }

    # AI response (already structured dictionary)
    if subject in subject_map:
        answer = subject_map[subject](question, grade, character)
    else:
        answer = format_answer(
            overview="Unknown subject.",
            key_facts="",
            christian_view="",
            agreement="",
            difference="",
            practice=""
        )

    # Rewards
    add_xp(20)
    session["tokens"] += 2

    return render_template("subject.html", answer=answer, character=character)

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
    character = session["character"]

    xp_to_next = level * 100
    xp_percent = int((xp / xp_to_next) * 100)

    missions = [
        "Visit 2 different planets",
        "Ask 1 science question",
        "Earn 20 XP",
    ]

    locked_characters = {
        "Princess Everly": "Reach Level 3",
        "Nova Circuit": "3-day streak",
        "Agent Cluehart": "Earn 200 XP total",
        "Buddy Barkston": "Buy for 100 tokens",
    }

    return render_template(
        "dashboard.html",
        xp=xp,
        level=level,
        tokens=tokens,
        streak=streak,
        character=character,
        xp_percent=xp_percent,
        xp_to_next=xp_to_next,
        missions=missions,
        locked_characters=locked_characters
    )

# ============================================================
# SHOP (HIDDEN)
# ============================================================

@app.route("/shop")
def shop():
    return redirect("/dashboard")

@app.route("/buy/<item_id>")
def buy_item(item_id):
    return redirect("/dashboard")

@app.route("/inventory")
def inventory():
    return redirect("/dashboard")

# ============================================================
# PARENT DASHBOARD
# ============================================================

@app.route("/parent_dashboard")
def parent_dashboard():
    init_user()

    progress_display = {
        subject: int((data["correct"] / data["questions"]) * 100)
        if data["questions"] > 0 else 0
        for subject, data in session["progress"].items()
    }

    return render_template(
        "parent_dashboard.html",
        progress=progress_display,
        utilization=session["usage_minutes"],
        xp=session["xp"],
        level=session["level"],
        tokens=session["tokens"],
        character=session["character"]
    )

# ============================================================
# RUN SERVER
# ============================================================

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

if __name__ == "__main__":
    app.run(debug=True)

