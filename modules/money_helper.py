# modules/money_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


# ------------------------------------------------------------
# Detect Christian-oriented money questions
# ------------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "biblical", "god", "jesus", "bible", "faith",
        "christian perspective", "christian worldview",
        "what does the bible say", "how does this relate to god"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# ------------------------------------------------------------
# Base money prompt
# ------------------------------------------------------------
def build_money_prompt(topic: str, grade: str):
    return f"""
You are a gentle money tutor helping a grade {grade} student.

The student asked:
"{topic}"

Answer using SIX child-friendly sections.

SECTION 1 — OVERVIEW
Explain the money idea in simple words.

SECTION 2 — KEY FACTS
Teach basic ideas: saving, spending, earning, planning,
needs vs wants, value, and simple budgeting.

SECTION 3 — CHRISTIAN VIEW
Explain softly how Christians may think about money:
stewardship, responsibility, generosity, and avoiding greed.

SECTION 4 — AGREEMENT
Explain what nearly everyone agrees on about money.

SECTION 5 — DIFFERENCE
Explain kindly how motivations may differ.

SECTION 6 — PRACTICE
Ask 2–3 tiny reflection questions with example answers.

Tone must be soft, slow, and child-friendly.
"""


def build_christian_money_prompt(topic: str, grade: str):
    return f"""
The student asked about money from a Christian perspective:

"{topic}"

Use SIX gentle sections.

SECTION 1 — OVERVIEW
Explain the idea simply.

SECTION 2 — KEY FACTS
Teach the basic money concepts.

SECTION 3 — CHRISTIAN VIEW
Explain stewardship, generosity, responsibility,
and the idea of using resources wisely.

SECTION 4 — AGREEMENT
Explain what all worldviews share in common.

SECTION 5 — DIFFERENCE
Explain how motivations may differ.

SECTION 6 — PRACTICE
Ask 2–3 tiny reflection questions.

Tone must be soft and calm.
"""


# ------------------------------------------------------------
# MAIN FUNCTION — explain money
# ------------------------------------------------------------
def explain_money(topic: str, grade_level="8", character="everly"):

    if is_christian_question(topic):
        prompt = build_christian_money_prompt(topic, grade_level)
    else:
        prompt = build_money_prompt(topic, grade_level)

    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    sections = parse_into_sections(raw)

    return format_answer(
        overview=sections.get("overview", ""),
        key_facts=sections.get("key_facts", []),
        christian_view=sections.get("christian_view", ""),
        agreement=sections.get("agreement", []),
        difference=sections.get("difference", []),
        practice=sections.get("practice", []),
        raw_text=raw
    )


# ------------------------------------------------------------
# GENERAL MONEY QUESTION
# ------------------------------------------------------------
def money_question(question: str, grade_level="8", character="everly"):

    prompt = build_money_prompt(question, grade_level)
    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    sections = parse_into_sections(raw)

    return format_answer(
        overview=sections.get("overview", ""),
        key_facts=sections.get("key_facts", []),
        christian_view=sections.get("christian_view", ""),
        agreement=sections.get("agreement", []),
        difference=sections.get("difference", []),
        practice=sections.get("practice", []),
        raw_text=raw
    )


# ------------------------------------------------------------
# MONEY QUIZ
# ------------------------------------------------------------
def money_quiz(topic: str, grade_level="8", character="everly"):

    prompt = f"""
Create a gentle money quiz for grade {grade_level}.

Topic: "{topic}"

Use SIX SECTIONS:
SECTION 1 — OVERVIEW
SECTION 2 — KEY FACTS
SECTION 3 — CHRISTIAN VIEW
SECTION 4 — AGREEMENT
SECTION 5 — DIFFERENCE
SECTION 6 — PRACTICE
"""

    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    sections = parse_into_sections(raw)

    return format_answer(
        overview=sections.get("overview", ""),
        key_facts=sections.get("key_facts", []),
        christian_view=sections.get("christian_view", ""),
        agreement=sections.get("agreement", []),
        difference=sections.get("difference", []),
        practice=sections.get("practice", []),
        raw_text=raw
    )







