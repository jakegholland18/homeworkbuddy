# modules/math_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


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
# Build 6-section math prompt (standard)
# -----------------------------------------------------------
def build_math_prompt(question: str, grade: str):
    return f"""
You are a gentle math tutor for a grade {grade} student.

The student asked:
\"{question}\"

Teach it using the **six-section Homework Buddy format**.

SECTION 1 — OVERVIEW
Give 2–3 calm sentences that explain the idea simply.

SECTION 2 — KEY FACTS
List 3–5 simple facts or steps using dash bullets (“- ”).
Explain things slowly and clearly.

SECTION 3 — CHRISTIAN VIEW
Explain softly how some Christians appreciate the order and logic
in math, as part of seeing creation as structured and consistent.

SECTION 4 — AGREEMENT
List 2–4 things everyone agrees on about math (rules, steps, logic).

SECTION 5 — DIFFERENCE
List gentle worldview differences, noting math rules stay the same.

SECTION 6 — PRACTICE
Give 2–3 tiny practice problems with short example answers.
Each must begin with “- ”.
"""


# -----------------------------------------------------------
# Build Christian-directed math prompt
# -----------------------------------------------------------
def build_christian_math_prompt(question: str, grade: str):
    return f"""
The student asked this math question from a Christian perspective:

\"{question}\"

Use the **six-section Homework Buddy format**.

SECTION 1 — OVERVIEW
Explain the question in gentle, simple sentences.

SECTION 2 — KEY FACTS
List the math steps or rules needed, using dash bullets.

SECTION 3 — CHRISTIAN VIEW
Explain kindly how Christians value order, logic, truth, and fairness
as part of God’s creation.

SECTION 4 — AGREEMENT
List shared math ideas everyone accepts (rules, steps, solutions).

SECTION 5 — DIFFERENCE
List gentle differences in motivation (stewardship, truth, honesty),
while noting math rules never change.

SECTION 6 — PRACTICE
Write 2–3 practice questions with short sample answers.
Each starting with “- ”.
"""


# -----------------------------------------------------------
# MAIN PUBLIC FUNCTION
# -----------------------------------------------------------
def explain_math(question: str, grade_level="5", character="everly"):

    # Pick prompt type
    if is_christian_question(question):
        base_prompt = build_christian_math_prompt(question, grade_level)
    else:
        base_prompt = build_math_prompt(question, grade_level)

    # Add character voice
    final_prompt = apply_personality(character, base_prompt)

    # Get raw AI output (contains 6 sections)
    raw = study_buddy_ai(final_prompt, grade_level, character)

    # Convert to structured sections
    sections = parse_into_sections(raw)

    # Render consistent HTML output
    return format_answer(**sections)





