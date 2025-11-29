# modules/question_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import format_answer, parse_into_sections


# -------------------------------------------------------
# Detect if student wants Christian perspective
# -------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "christianity", "jesus", "god", "faith",
        "biblical", "bible",
        "how does this relate to god",
        "from a christian perspective",
        "christian worldview"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -------------------------------------------------------
# Build 6-section prompt (general question)
# -------------------------------------------------------
def build_general_prompt(question: str, grade_level: str):
    return f"""
The student asked a general question:

\"{question}\"

Explain it using the **six-section Homework Buddy format**.

SECTION REQUIREMENTS:
• OVERVIEW: 2–3 calm sentences.
• KEY FACTS: short dash-bullet list (“- ”).
• CHRISTIAN VIEW: gentle explanation of purpose, morality, meaning.
• AGREEMENT: short dash-bullet list of things all worldviews share.
• DIFFERENCE: dash-bullet list showing worldview additions.
• PRACTICE: 2–3 kid-sized questions with short example answers.

Make everything smooth and simple for grade {grade_level}.
"""


# -------------------------------------------------------
# Build 6-section prompt (Christian question)
# -------------------------------------------------------
def build_christian_prompt(question: str, grade_level: str):
    return f"""
The student asked this question from a Christian perspective:

\"{question}\"

Explain using the **six-section Homework Buddy format**.

RULES:
• OVERVIEW is short and gentle.
• KEY FACTS list uses dash bullets.
• CHRISTIAN VIEW explains beliefs kindly, with Scripture only if natural.
• AGREEMENT uses dash bullets.
• DIFFERENCE uses dash bullets.
• PRACTICE lists 2–3 tiny reflection questions with example answers.

Keep everything soft, slow, and age-appropriate for grade {grade_level}.
"""


# -------------------------------------------------------
# MAIN PUBLIC FUNCTION — uses formatter + parser
# -------------------------------------------------------
def answer_question(question: str, grade_level="8", character="everly"):

    # Choose which prompt to build
    if is_christian_question(question):
        base_prompt = build_christian_prompt(question, grade_level)
    else:
        base_prompt = build_general_prompt(question, grade_level)

    # Add personality
    final_prompt = apply_personality(character, base_prompt)

    # Get raw AI output (already in 6-section text form)
    raw_output = study_buddy_ai(final_prompt, grade_level, character)

    # Convert AI text → clean structured dictionary
    sections = parse_into_sections(raw_output)

    # Return HTML-ready formatted answer
    return format_answer(
        overview=sections.get("overview", ""),
        key_facts=sections.get("key_facts", []),
        christian_view=sections.get("christian_view", ""),
        agreement=sections.get("agreement", []),
        difference=sections.get("difference", []),
        practice=sections.get("practice", [])
    )
