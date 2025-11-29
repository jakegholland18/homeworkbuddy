# modules/apologetics_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import format_answer


# -----------------------------------------------------------
# Label extractor (global consistency)
# -----------------------------------------------------------
def _extract(raw: str, label: str) -> str:
    return raw.split(label)[-1].strip() if label in raw else "Not available."


# -----------------------------------------------------------
# STRUCTURED APOLOGETICS RESPONSE — 6 SECTIONS
# -----------------------------------------------------------
def apologetics_answer(question: str, grade_level="8", character="everly"):
    """
    Creates a gentle apologetics explanation using the same
    6-section Homework Buddy structure used across all helpers.
    """

    prompt = f"""
You are a warm, gentle Christian apologetics tutor teaching a grade {grade_level} student.

The student asked:
"{question}"

Answer using SIX soft, calm, child-friendly sections.

SECTION 1 — OVERVIEW
Explain in a few short sentences what the question is really about.
Use slow, gentle, everyday language.

SECTION 2 — KEY IDEAS
Explain a few simple ideas Christians believe about this topic.
Use calm sentences without lists or bullet formatting.

SECTION 3 — CHRISTIAN VIEW
Explain softly why Christians believe what they do,
why it matters to them,
and how it helps them live with hope or meaning.
Use Scripture gently if it fits.

SECTION 4 — AGREEMENT
Explain what Christians and non-Christians may both agree on.
Keep sentences simple and warm.

SECTION 5 — DIFFERENCE
Explain kindly where Christian and secular worldviews
may understand this topic differently.
Do not argue. Just explain softly.

SECTION 6 — PRACTICE
Ask 2–3 tiny reflection questions the student can think about.
Give short example answers to help guide them.

Tone rules:
gentle, slow, warm, respectful, child-friendly.
Never use debate or harsh language.
"""

    # Add character personality
    prompt = apply_personality(character, prompt)

    # Get structured AI response
    raw = study_buddy_ai(prompt, grade_level, character)

    # Extract all sections
    overview       = _extract(raw, "SECTION 1")
    key_ideas      = _extract(raw, "SECTION 2")
    christian_view = _extract(raw, "SECTION 3")
    agreement      = _extract(raw, "SECTION 4")
    difference     = _extract(raw, "SECTION 5")
    practice       = _extract(raw, "SECTION 6")

    # Return the formatted final answer object
    return format_answer(
        overview=overview,
        key_facts=key_ideas,
        christian_view=christian_view,
        agreement=agreement,
        difference=difference,
        practice=practice
    )
