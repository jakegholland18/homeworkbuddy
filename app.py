import sys
import os
from flask import Flask, render_template, request, redirect, session, flash, url_for
from datetime import datetime, timedelta

# Make sure Python can see /modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ---------------------------------------
# IMPORT AI LOGIC
# ---------------------------------------
from modules.shared_ai import study_buddy_ai
from modules.personality_helper import get_all_characters

# Subject Helpers
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
# SHOP ITEMS
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
# FLASK APP SETUP
# ============================================================
app = Flask(
    __name__,
    template_folder="website/templates",
    static_folder="website/static"
)
app.secret_key = "b3c2e773eaa84cd6841a9ffa54c918881b9fab30bb02f7128"


# ============================================================
# INIT USER
# ============================================================
def init_user():
    defaults = {
        "tokens": 0,
        "xp": 0,
        "level": 1,
        "streak": 1,
        "last_visit": str(datetime.today().date()),
        "inventory": [],
        "character": None,
        "usage_minutes": 0,
        "progress": {
            "num_forge": {"questions": 0, "correct": 0},
            "atom_sphere": {"questions": 0, "correct": 0},
            "chrono_core": {"questions": 0, "correct": 0},
            "ink_haven": {"questions": 0, "correct": 0},
            "faith_realm": {"questions": 0, "correct": 0},
            "coin_quest": {"questions": 0, "correct": 0},
            "stock_star": {"questions": 0, "correct": 0},
            "story_verse": {"questions": 0, "correct": 0},
            "power_grid": {"questions": 0, "correct": 0},
            "terra_nova": {"questions": 0, "correct": 0},
            "truth_forge": {"questions": 0, "correct": 0},
        }
    }
    for key, value in defaults.items():
        if key not in session:
            session[key] = value

    update_streak()


# ============================================================
# STREAK SYSTEM
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
# XP / LEVEL SYSTEM
# ============================================================
def add_xp(amount):
    session["xp"] += amount
    xp_needed = session["level"] * 100

    if session["xp"] >= xp_needed:
        session["xp"] -= xp_needed
        session["level"] += 1
        flash(f"🎉 LEVEL UP! You reached Level {session['level']}!", "info")


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def home():
    init_user()
    return redirect("/dashboard")


# -------------------------------
# SELECT CHARACTER
# -------------------------------
@app.route("/choose-character")
def choose_character():
    init_user()
    characters = get_all_characters()

    return render_template(
        "choose_character.html",
        characters=characters,
        selected_character=session.get("character"),
        active_page="characters"
    )


@app.route("/select-character", methods=["POST"])
def select_character():
    init_user()

    chosen = request.form.get("character")  # OPTION A — backend expects "character"

    if not chosen:
        flash("Please select a character.", "error")
        return redirect(url_for("choose_character"))

    session["character"] = chosen
    return redirect(url_for("dashboard"))


# -------------------------------
# ASK QUESTION
# -------------------------------
@app.route("/ask-question")
def ask_question():
    init_user()
    subject = request.args.get("subject")
    grade = request.args.get("grade")
    return render_template(
        "ask_question.html",
        subject=subject,
        grade=grade,
        selected_character=session["character"]
    )


# -------------------------------
# SUBJECT ANSWERING LOGIC
# -------------------------------
@app.route("/subject", methods=["POST"])
def subject_answer():
    init_user()

    grade = request.form.get("grade")
    subject = request.form.get("subject")
    question = request.form.get("question")
    character = session["character"]

    session["progress"].setdefault(subject, {"questions": 0, "correct": 0})
    session["progress"][subject]["questions"] += 1

    subject_map = {
        "num_forge": math_helper.explain_math,
        "atom_sphere": science_helper.explain_science,
        "faith_realm": bible_helper.bible_lesson,
        "chrono_core": history_helper.explain_history,
        "ink_haven": writing_helper.help_write,
        "power_grid": study_helper.generate_quiz,
        "truth_forge": apologetics_helper.apologetics_answer,
        "stock_star": investment_helper.explain_investing,
        "coin_quest": money_helper.explain_money,
        "terra_nova": question_helper.answer_question,
        "story_verse": text_helper.summarize_text
    }

    answer = subject_map.get(subject, lambda *_: "Unknown subject.")(question, grade, character)

    add_xp(20)
    session["tokens"] += 2

    return render_template(
        "subject.html",
        answer=answer,
        selected_character=session["character"]
    )


# -------------------------------
# STUDENT DASHBOARD
# -------------------------------
@app.route("/dashboard")
def dashboard():
    init_user()

    xp = session["xp"]
    level = session["level"]
    tokens = session["tokens"]
    streak = session["streak"]
    character = session.get("character")

    xp_to_next = level * 100
    xp_percent = min(max(int((xp / xp_to_next) * 100), 0), 100)

    mission_items = [
        {"title": "Math", "tag": "Puzzle Portals · Logic Lanes"},
        {"title": "History", "tag": "Timeline Trek · Heroic Ages"},
        {"title": "Science", "tag": "Lab Galaxy · Experiment Hub"},
        {"title": "Reading", "tag": "StoryVerse · Lore Realms"},
        {"title": "Writing", "tag": "Idea Forge · Draft Dock"},
        {"title": "Test Prep", "tag": "Boss Battles · Victory Arena"},
    ]

    active_missions = [
        {"title": "Solve 5 Algebra Problems", "badge": "🔥 Priority", "desc": "Translate → Solve → Victory"},
        {"title": "History Summary", "badge": "✨ Quick Win", "desc": "Turn notes into storyline"},
    ]

    return render_template(
        "dashboard.html",
        xp=xp,
        level=level,
        tokens=tokens,
        streak=streak,
        xp_percent=xp_percent,
        xp_to_next=xp_to_next,
        selected_character=character,
        mission_items=mission_items,
        active_missions=active_missions,
        active_page="student"
    )


# -------------------------------
# INVENTORY
# -------------------------------
@app.route("/inventory")
def inventory():
    init_user()
    items = [SHOP_ITEMS[i] for i in session["inventory"]]
    return render_template(
        "inventory.html",
        inventory=items,
        selected_character=session.get("character")
    )


# -------------------------------
# SHOP
# -------------------------------
@app.route("/shop")
def shop():
    init_user()
    return render_template(
        "shop.html",
        items=SHOP_ITEMS,
        tokens=session["tokens"],
        inventory=session["inventory"],
        selected_character=session.get("character")
    )


@app.route("/buy/<item_id>")
def buy_item(item_id):
    init_user()

    if item_id not in SHOP_ITEMS:
        flash("Item not found.")
        return redirect("/shop")

    item = SHOP_ITEMS[item_id]
    if session["tokens"] < item["price"]:
        flash("Not enough Galaxy Tokens!", "error")
        return redirect("/shop")

    session["tokens"] -= item["price"]
    session["inventory"].append(item_id)

    flash(f"You bought {item['name']}!", "success")
    return redirect("/shop")


# -------------------------------
# PARENT DASHBOARD
# -------------------------------
@app.route("/parent_dashboard")
def parent_dashboard():
    init_user()

    total_usage = session["usage_minutes"]

    progress_display = {
        subject: int((data["correct"] / data["questions"]) * 100)
        if data["questions"] > 0 else 0
        for subject, data in session["progress"].items()
    }

    return render_template(
        "parent_dashboard.html",
        progress=progress_display,
        utilization=total_usage,
        xp=session["xp"],
        level=session["level"],
        tokens=session["tokens"],
        selected_character=session.get("character"),
        active_page="parent"
    )


# ============================================================
# RUN SERVER
# ============================================================
if __name__ == "__main__":
    app.run(debug=True)
