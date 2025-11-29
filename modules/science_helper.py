# modules/science_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


# -------------------------------------------------------
# Detect Christian-oriented science questions
# -------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "christianity", "god", "jesus", "bible",
        "biblical", "creation", "faith", "christian perspective",
        "from a christian view", "how does this relate to christianity",
        "how does this relate to god"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -------------------------------------------------------
# Build standard science prompt (FOR NEW 6-SECTION FORMAT)
# -------------------------------------------------------
def build_science_prompt(topic: str, grade_level: str):
    return f"""
The student asked a science question:

\"{topic}\"

Teach the idea using the **six-section Homework Buddy format**.

RULES:
• OVERVIEW must be 2–3 gentle sentences.
• KEY FACTS must be a short list using dash bullets ("- ").
• CHRISTIAN VIEW must stay soft and respectful.
• AGREEMENT and DIFFERENCE must use dash bullets.
• PRACTICE must include 2–3 tiny questions with short sample answers.
Keep it warm and very easy for a grade {grade_level} student.
"""


# -------------------------------------------------------
# Build Christian-directed science prompt
# -------------------------------------------------------
def build_christian_science_prompt(topic: str, grade_level: str):
    return f"""
The student asked this science question from a Christian perspective:

\"{topic}\"

Explain the idea using the **six-section Homework Buddy format**.

SECTION GUIDELINES:
• OVERVIEW: gentle recap
• KEY FACTS: dash-bullet list
• CHRISTIAN VIEW: soft explanation about order and creation
• AGREEMENT: dash-bullet list
• DIFFERENCE: dash-bullet list
• PRACTICE: 2–3 small questions with sample answers

Keep everything calm and simple for grade {grade_level}.
"""


# -------------------------------------------------------
# MAIN PUBLIC FUNCTION — FULLY UPDATED FOR NEW SYSTEM
# -------------------------------------------------------
def explain_science(topic: str, grade_level="8", character="everly"):

    # Pick the prompt style
    if is_christian_question(topic):
        base_prompt = build_christian_science_prompt(topic, grade_level)
    else:
        base_prompt = build_science_prompt(topic, grade_level)

    # Add character personality
    enriched = apply_personality(character, base_prompt)

    # Get the raw 6-section text from AI
    raw_output = study_buddy_ai(enriched, grade_level, character)

    # Convert raw text → structured dict
    parsed = parse_into_sections(raw_output)

    # Format final result for subject.html template
    return format_answer(
        overview=parsed.get("overview", ""),
        key_facts=parsed.get("key_facts", []),
        christian_view=parsed.get("christian_view", ""),
        agreement=parsed.get("agreement", []),
        difference=parsed.get("difference", []),
        practice=parsed.get("practice", [])
    )
