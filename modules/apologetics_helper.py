# modules/apologetics_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


# -----------------------------------------------------------
# Detect if the question directly asks from a Christian angle
# -----------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "christianity", "jesus", "god", "bible",
        "biblical", "christian perspective", "from a christian view",
        "what does the bible say", "how does this relate to god",
        "christian worldview"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -----------------------------------------------------------
# Build core apologetics prompt — consistent 6-section format
# -----------------------------------------------------------
def build_apologetics_prompt(question: str, grade_level: str, christian: bool):

    if christian:
        preface = f'The student asked this apologetics question from a Christian perspective:\n"{question}"'
    else:
        preface = f'The student asked an apologetics question:\n"{question}"'

    return f"""
{preface}

Explain the answer using the **six-section Homework Buddy format**:

SECTION 1 — OVERVIEW
A very short explanation (2–3 gentle sentences) of what the question is really about.

SECTION 2 — KEY FACTS
List 3–5 simple, important Christian ideas using dash bullets ("- ").

SECTION 3 — CHRISTIAN VIEW
Gently explain why many Christians believe what they do.
Keep it soft, short, and child-friendly.

SECTION 4 — AGREEMENT
Use dash bullets to list things Christians and non-Christians may both agree on.

SECTION 5 — DIFFERENCE
Use dash bullets to gently highlight worldview differences.
Be respectful and calm.

SECTION 6 — PRACTICE
Give 2–3 tiny reflection questions with sample answers.
Each question should start with "- ".

Tone: warm, slow, gentle, never argumentative.
Keep everything very simple for a grade {grade_level} student.
"""


# -----------------------------------------------------------
# PUBLIC FUNCTION — returns structured + formatted answer
# -----------------------------------------------------------
def apologetics_answer(question: str, grade_level="8", character="everly"):

    christian = is_christian_question(question)

    # Build main prompt in 6-section format
    base_prompt = build_apologetics_prompt(question, grade_level, christian)

    # Add the character's speaking style
    enriched = apply_personality(character, base_prompt)

    # Get structured text back (should contain all 6 sections)
    raw = study_buddy_ai(enriched, grade_level, character)

    # Convert AI text into structured dict
    sections = parse_into_sections(raw)

    # Format final HTML response
    return format_answer(
        overview=sections.get("overview", ""),
        key_facts=sections.get("key_facts", []),
        christian_view=sections.get("christian_view", ""),
        agreement=sections.get("agreement", []),
        difference=sections.get("difference", []),
        practice=sections.get("practice", [])
    )

