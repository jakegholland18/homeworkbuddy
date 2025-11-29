# modules/math_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import format_answer


# -----------------------------------------------------------
# Detect Christian-related math questions
# -----------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "christianity", "god", "jesus", "bible",
        "biblical", "faith", "christian perspective",
        "how does this relate to christianity",
        "how does this relate to god"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -----------------------------------------------------------
# Build 6-section math prompt (normal)
# -----------------------------------------------------------
def build_math_prompt(question: str, grade: str):
    return f"""
You are a gentle math tutor for a grade {grade} student.

The student asked:
"{question}"

Answer using SIX warm and simple sections.

SECTION 1 — OVERVIEW
Explain the math idea in 3–4 slow, kid-friendly sentences.

SECTION 2 — KEY FACTS
Explain the important steps or truths about the math topic
using small, calm sentences. No lists or bullets.

SECTION 3 — CHRISTIAN VIEW
Explain softly how many Christians appreciate the order and logic
seen in math. If the topic is not naturally Christian, simply say
that Christians still see value in clear thinking and problem solving.

SECTION 4 — AGREEMENT
Explain what everyone agrees on about the math
(the rules, the steps, how numbers work the same for everyone).

SECTION 5 — DIFFERENCE
Explain gently whether worldview affects the topic.
For most math, it does not change the steps.

SECTION 6 — PRACTICE
Give 2–3 tiny practice problems with short example answers
spoken in a calm, simple voice.

Keep tone slow, warm, and child-friendly.
"""


# -----------------------------------------------------------
# Build Christian-directed math prompt
# -----------------------------------------------------------
def build_christian_math_prompt(question: str, grade: str):
    return f"""
The student asked this math question from a Christian perspective:

"{question}"

Answer using SIX calm sections.

SECTION 1 — OVERVIEW
Explain the question in slow and simple words.

SECTION 2 — KEY FACTS
Explain the important rules, steps, or ideas behind the math.

SECTION 3 — CHRISTIAN VIEW
Explain kindly how Christians may appreciate order, logic,
consistency, and truth as part of creation.

SECTION 4 — AGREEMENT
Explain what all worldviews agree on about the math.

SECTION 5 — DIFFERENCE
Explain gently that math rules remain the same regardless of worldview,
but motivations (such as stewardship, truth, fairness) may differ.

SECTION 6 — PRACTICE
Give a couple of tiny practice questions and simple answers.

Keep everything soft and warm.
"""


# -----------------------------------------------------------
# Section extractor — works with your new answer structure
# -----------------------------------------------------------
def _extract(raw: str, label: str) -> str:
    return raw.split(label)[-1].strip() if label in raw else "No information provided."


# -----------------------------------------------------------
# MAIN PUBLIC FUNCTION — final math explanation
# -----------------------------------------------------------
def explain_math(question: str, grade_level="5", character="everly"):

    # Choose which 6-section structure to use
    if is_christian_question(question):
        prompt = build_christian_math_prompt(question, grade_level)
    else:
        prompt = build_math_prompt(question, grade_level)

    # Personality wrapper
    prompt = apply_personality(character, prompt)

    # Ask AI
    raw = study_buddy_ai(prompt, grade_level, character)

    # Extract all six sections
    overview       = _extract(raw, "SECTION 1")
    key_facts      = _extract(raw, "SECTION 2")
    christian_view = _extract(raw, "SECTION 3")
    agreement      = _extract(raw, "SECTION 4")
    difference     = _extract(raw, "SECTION 5")
    practice       = _extract(raw, "SECTION 6")

    # Format for the HTML
    return format_answer(
        overview=overview,
        key_facts=key_facts,
        christian_view=christian_view,
        agreement=agreement,
        difference=difference,
        practice=practice
    )




