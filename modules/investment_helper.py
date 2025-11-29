# modules/investment_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import format_answer


# ------------------------------------------------------------
# Detect Christian-oriented investing questions
# ------------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "biblical", "god", "jesus", "bible", "faith",
        "christian perspective", "christian view",
        "what does the bible say", "how does this relate to god"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# ------------------------------------------------------------
# Build investing prompt — standard version
# ------------------------------------------------------------
def build_investing_prompt(topic: str, grade: str):
    return f"""
You are a gentle investing tutor for a grade {grade} student.

The student asked:
"{topic}"

Answer using SIX warm, child-friendly sections.

SECTION 1 — OVERVIEW
Explain the investing idea in simple, calm sentences.

SECTION 2 — KEY FACTS
Explain the important ideas (saving, risk, long-term thinking,
companies, stocks, value) using slow, soft sentences.

SECTION 3 — CHRISTIAN VIEW
Explain softly how many Christians think about money:
stewardship, responsibility, avoiding greed, generosity,
and wise choices. If the question is not Christian,
still mention that some Christians see investing as part of wise planning.

SECTION 4 — AGREEMENT
Explain what all worldviews agree on (saving, planning,
risk-taking carefully, long-term thinking).

SECTION 5 — DIFFERENCE
Explain gently where Christian motivation (stewardship, generosity)
may differ from a “money-first” view.

SECTION 6 — PRACTICE
Ask 2–3 tiny reflection questions with simple example answers.

Tone must be soft, slow, friendly, and not technical.
"""


# ------------------------------------------------------------
# Build Christian-directed investing prompt
# ------------------------------------------------------------
def build_christian_investing_prompt(topic: str, grade: str):
    return f"""
The student asked this investing question from a Christian perspective:

"{topic}"

Answer using SIX simple, warm sections.

SECTION 1 — OVERVIEW
Explain the idea slowly and clearly.

SECTION 2 — KEY FACTS
Explain the simple financial ideas needed to understand the topic.

SECTION 3 — CHRISTIAN VIEW
Explain softly how Christians think about money as stewardship,
responsibility, and avoiding greed.

SECTION 4 — AGREEMENT
Explain what all worldviews agree on (saving, planning, earning).

SECTION 5 — DIFFERENCE
Explain gently how Christian motivation may differ from secular motivation.

SECTION 6 — PRACTICE
Ask 2–3 reflection questions with calm example answers.
"""


# ------------------------------------------------------------
# Extract helper (universal)
# ------------------------------------------------------------
def _extract(raw: str, label: str) -> str:
    return raw.split(label)[-1].strip() if label in raw else "No information provided."


# ------------------------------------------------------------
# MAIN PUBLIC FUNCTION — explain investing
# ------------------------------------------------------------
def explain_investing(topic: str, grade_level="8", character="everly"):

    # Choose which prompt type
    if is_christian_question(topic):
        prompt = build_christian_investing_prompt(topic, grade_level)
    else:
        prompt = build_investing_prompt(topic, grade_level)

    # Add personality
    prompt = apply_personality(character, prompt)

    # Get AI output
    raw = study_buddy_ai(prompt, grade_level, character)

    # Extract six sections
    overview       = _extract(raw, "SECTION 1")
    key_facts      = _extract(raw, "SECTION 2")
    christian_view = _extract(raw, "SECTION 3")
    agreement      = _extract(raw, "SECTION 4")
    difference     = _extract(raw, "SECTION 5")
    practice       = _extract(raw, "SECTION 6")

    # Format into clean HTML-ready object
    return format_answer(
        overview=overview,
        key_facts=key_facts,
        christian_view=christian_view,
        agreement=agreement,
        difference=difference,
        practice=practice
    )


# ------------------------------------------------------------
# GENERAL INVESTING QUESTION
# ------------------------------------------------------------
def investment_question(question: str, grade_level="8", character="everly"):

    # Always use the same structure
    prompt = build_investing_prompt(question, grade_level)
    prompt = apply_personality(character, prompt)

    raw = study_buddy_ai(prompt, grade_level, character)

    overview       = _extract(raw, "SECTION 1")
    key_facts      = _extract(raw, "SECTION 2")
    christian_view = _extract(raw, "SECTION 3")
    agreement      = _extract(raw, "SECTION 4")
    difference     = _extract(raw, "SECTION 5")
    practice       = _extract(raw, "SECTION 6")

    return format_answer(
        overview=overview,
        key_facts=key_facts,
        christian_view=christian_view,
        agreement=agreement,
        difference=difference,
        practice=practice
    )


# ------------------------------------------------------------
# INVESTING QUIZ — still six sections
# ------------------------------------------------------------
def investment_quiz(topic: str, grade_level="8", character="everly"):

    prompt = f"""
Create a simple investing quiz for a grade {grade_level} student.

Topic: "{topic}"

Use SIX SECTIONS:

SECTION 1 — OVERVIEW
Explain the topic softly.

SECTION 2 — KEY FACTS
Explain the important ideas they should remember.

SECTION 3 — CHRISTIAN VIEW
Explain stewardship gently.

SECTION 4 — AGREEMENT
Explain what all people agree on.

SECTION 5 — DIFFERENCE
Explain respectfully how worldviews may differ.

SECTION 6 — PRACTICE
Create a few quiz questions with short answers.

Tone: calm, slow, and not technical.
"""

    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    overview       = _extract(raw, "SECTION 1")
    key_facts      = _extract(raw, "SECTION 2")
    christian_view = _extract(raw, "SECTION 3")
    agreement      = _extract(raw, "SECTION 4")
    difference     = _extract(raw, "SECTION 5")
    practice       = _extract(raw, "SECTION 6")

    return format_answer(
        overview=overview,
        key_facts=key_facts,
        christian_view=christian_view,
        agreement=agreement,
        difference=difference,
        practice=practice
    )

