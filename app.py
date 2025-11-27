import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, render_template, request, redirect, session

# -------------------------------
# IMPORT HELPERS (ALL AI CALLS)
# -------------------------------
from modules.shared_ai import study_buddy_ai
from modules.personality_helper import get_all_characters

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


# -------------------------------
# FLASK APP – FIXED FOR RENDER
# -------------------------------
app = Flask(
    __name__,
    template_folder="website/templates",
    static_folder="website/static"
)

app.secret_key = "b3c2e773eaa84cd6841a9ffa54c918881b9fab30bb02f7128"


# -------------------------------
# SUBJECTS PAGE (PLANET GRID)
# -------------------------------
@app.route("/subjects")
def subjects():
    planets = [
        ("math",         "math.png",          "Math Planet"),
        ("science",      "science.png",       "Science Planet"),
        ("history",      "history.png",       "History Planet"),
        ("writing",      "writing.png",       "Writing Planet"),
        ("bible",        "bible.png",         "Bible Planet"),
        ("study",        "study.png",         "Study Planet"),
        ("text",         "text.png",          "Text Planet"),
        ("question",     "question.png",      "Question Planet"),
        ("apologetics",  "apologetics.png",   "Apologetics Planet"),
        ("accounting",   "accounting.png",    "Accounting Planet"),
        ("investment",   "investment.png",    "Investment Planet")
    ]
    return render_template("subjects.html", planets=planets)


# -------------------------------
# CHARACTER SELECTION
# -------------------------------
@app.route("/choose-character")
def choose_character_page():
    characters = get_all_characters()
    return render_template("choose_character.html", characters=characters)


@app.route("/select-character", methods=["POST"])
def select_character():
    selected = request.form.get("character")
    if selected:
        session["character"] = selected
    return redirect("/subjects")


# -------------------------------
# GRADE SELECTION FOR A SUBJECT
# -------------------------------
@app.route("/choose-grade")
def choose_grade():
    subject = request.args.get("subject")
    return render_template("subject_select_form.html", subject=subject)


# -------------------------------
# SUBJECT PROCESSING → AI HELPERS
# -------------------------------
@app.route("/subject", methods=["POST"])
def subject():
    grade = request.form.get("grade")
    subject = request.form.get("subject")
    question = request.form.get("question")

    character = session.get("character", "valor_strike")

    if subject == "math":
        answer = math_helper.explain_math(question, grade, character)
    elif subject == "text":
        answer = text_helper.summarize_text(question, grade, character)
    elif subject == "general":
        answer = question_helper.answer_question(question, grade, character)
    elif subject == "science":
        answer = science_helper.explain_science(question, grade, character)
    elif subject == "bible":
        answer = bible_helper.bible_lesson(question, grade, character)
    elif subject == "history":
        answer = history_helper.explain_history(question, grade, character)
    elif subject == "writing":
        answer = writing_helper.help_write(question, grade, character)
    elif subject == "study":
        answer = study_helper.generate_quiz(question, grade, character)
    elif subject == "apologetics":
        answer = apologetics_helper.apologetics_answer(question, grade, character)
    elif subject == "investment":
        answer = investment_helper.explain_investing(question, grade, character)
    elif subject == "money":
        answer = money_helper.explain_money(question, grade, character)
    else:
        answer = "I'm not sure what subject that is, but I can still help."

    return render_template("subject.html", answer=answer, character=character)


# -------------------------------
# STUDENT DASHBOARD
# -------------------------------
@app.route("/dashboard")
def dashboard():
    xp = 120
    level = 3
    subjects_count = 5
    character = session.get("character")

    return render_template(
        "dashboard.html",
        xp=xp,
        level=level,
        subjects_count=subjects_count,
        character=character
    )


# -------------------------------
# STUDY BUDDY CHAT PAGE
# -------------------------------
@app.route("/buddy")
def buddy():
    character = session.get("character")

    if not character:
        return redirect("/choose-character")

    return render_template("buddy.html", character=character)


# -------------------------------
# FREEFORM Q&A → AI
# -------------------------------
@app.route("/ask", methods=["POST"])
def ask():
    question = request.form.get("question")
    grade = request.form.get("grade", "8")
    character = session.get("character")

    if not character:
        return redirect("/choose-character")

    answer = study_buddy_ai(question, grade, character)

    return render_template("buddy.html", character=character, answer=answer)


# -------------------------------
# RUN SERVER
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)




