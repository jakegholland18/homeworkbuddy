import sys
import os
import logging
import traceback
from datetime import datetime, timedelta

from flask import (
    Flask, render_template, request, redirect, session,
    flash, jsonify, send_file
)
from flask import got_request_exception

# ============================================================
# STATIC + TEMPLATE PATHS
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

logging.basicConfig(level=logging.INFO)

def log_exception(sender, exception, **extra):
    sender.logger.error("Exception during request: %s", traceback.format_exc())

got_request_exception.connect(log_exception, app)

# ============================================================
# LOAD MODULES
# ============================================================

sys.path.append(os.path.abspath(os.path.join(BASE_DIR, "modules")))

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import get_all_characters, apply_personality
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
    "truth_forge": apologetics_helper.apologetics_answer,
    "stock_star": investment_helper.explain_investing,
    "coin_quest": money_helper.explain_money,
    "terra_nova": question_helper.answer_question,
    "story_verse": text_helper.explain_text,
    "power_grid": study_helper.deep_study_chat,  # conversation-style deep study
}

# ============================================================
# USER SESSION DEFAULTS
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
    }
    for k, v in defaults.items():
        if k not in session:
            session[k] = v
    update_streak()

# ============================================================
# DAILY STREAK SYSTEM
# ============================================================

def update_streak():
    today = datetime.today().date()
    last = datetime.strptime(session["last_visit"], "%Y-%m-%d").date()

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
# ROUTES
# ============================================================

@app.route("/")
def home():
    init_user()
    return redirect("/subjects")


# ============================================================
# SUBJECTS PAGE
# ============================================================

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
        characters=get_all_characters(),
    )


# ============================================================
# POWERGRID STUDY GUIDE SUBMISSION
# ============================================================

@app.route("/powergrid_submit", methods=["POST"])
def powergrid_submit():
    init_user()

    grade = request.form.get("grade")
    topic = request.form.get("topic", "").strip()
    uploaded = request.files.get("file")

    text = ""

    # extract file text if uploaded
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
            text = f"Study this topic:\n\n{topic}"

    else:
        text = topic or "No topic provided."

    # build study guide prompt
    prompt = f"""
Create a full, extremely in-depth study guide.

CONTENT SOURCE:
{text}

STYLE:
• Very detailed
• Step-by-step explanations
• Examples
• Key terms
• Study tips
• Summary
• Written for grade {grade}

FORMAT:
Use clean text (no markdown).
"""

    prompt = apply_personality(session["character"], prompt)

    study_guide = study_buddy_ai(prompt, grade, session["character"])

    # generate PDF
    pdf_path = "/tmp/study_guide.pdf"

    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        y = height - 50
        for line in study_guide.split("\n"):
            c.drawString(40, y, line[:110])
            y -= 15
            if y < 40:
                c.showPage()
                y = height - 50
        c.save()

        pdf_url = "/download_study_guide"
        session["study_pdf"] = pdf_path

    except Exception as e:
        app.logger.error("Error generating PDF: %s", e)
        pdf_url = None

    # save conversation memory start
    session["conversation"] = [
        {"role": "assistant", "content": study_guide}
    ]

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
    if pdf and os.path.exists(pdf):
        return send_file(pdf, as_attachment=True)
    return "PDF not found."


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

    # progress tracking
    session["progress"].setdefault(subject, {"questions": 0, "correct": 0})
    session["progress"][subject]["questions"] += 1

    func = subject_map.get(subject)
    if func is None:
        flash("Unknown subject selected.", "error")
        return redirect("/subjects")

    # Call the subject handler.
    # deep_study_chat is written to accept either a string or a conversation list.
    result = func(question, grade, character)

    # Some helpers may return dicts; others raw text.
    six_section_answer = result.get("raw_text") if isinstance(result, dict) else result

    # start conversation memory with the answer
    session["conversation"] = [
        {"role": "assistant", "content": six_section_answer}
    ]
    session.modified = True

    add_xp(20)
    session["tokens"] += 2

    return render_template(
        "subject.html",
        subject=subject,
        grade=grade,
        question=question,
        answer=six_section_answer,
        character=character,
        conversation=session["conversation"],
        pdf_url=None,
    )


# ============================================================
# FOLLOW-UP MESSAGE (ALL SUBJECTS)
# ============================================================

@app.route("/followup_message", methods=["POST"])
def followup_message():
    init_user()

    data = request.get_json() or {}
    subject = data.get("subject")
    grade = data.get("grade")
    character = data.get("character") or session["character"]
    message = data.get("message", "")

    conversation = session.get("conversation", [])
    conversation.append({"role": "user", "content": message})

    # deep conversational response (PowerGrid-style)
    reply = study_helper.deep_study_chat(conversation, grade, character)

    conversation.append({"role": "assistant", "content": reply})
    session["conversation"] = conversation
    session.modified = True

    return jsonify({"reply": reply})


# ============================================================
# DASHBOARD
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
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)






