# modules/apologetics_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


# ------------------------------------------------------------
# Detect if question is Christian / apologetics related
# ------------------------------------------------------------
def is_apologetics_question(text: str) -> bool:
    keywords = [
        "why does god", "why did god",
        "why does the bible", "why does christianity",
        "how do christians defend", "christian defense",
        "apologetics", "faith question",
        "why does evil exist", "problem of evil",
        "why does god allow", "bible explanation"
    ]
    txt = text.lower()
    return any(k in txt for k in keywords)


# ------------------------------------------------------------
# MAIN APOLOGETICS ANSWER — 6 SECTIONS, NO BULLETS
# ------------------------------------------------------------
def apologetics_answer(question: str, grade_level="8", character="everly"):
    """
    Full apologetics explanation using the 6-section Homework Buddy style.
    Output must contain 6 labeled sections, all paragraph-based.
    """

    prompt = f"""
You are a gentle Christian apologetics tutor for a grade {grade_level} student.

The student asked:
\"{question}\"

Answer using the SIX-section Homework Buddy format.
NO bullet points — only calm, simple paragraphs.

SECTION 1 — OVERVIEW
Explain in 2–3 warm, gentle sentences what the question is really about.

SECTION 2 — KEY FACTS
Explain a few simple ideas Christians believe about this topic
in a short, child-friendly paragraph.

SECTION 3 — CHRISTIAN VIEW
Explain softly why Christians believe this matters.
Describe how Christians understand the topic through Scripture,
hope, and meaning, but keep it simple and peaceful.

SECTION 4 — AGREEMENT
Explain what Christians and non-Christians may both agree on
in a gentle paragraph.

SECTION 5 — DIFFERENCE
Explain kindly how Christian and secular worldviews may understand
this question differently. Do not argue, only explain.

SECTION 6 — PRACTICE
Ask 2–3 tiny reflection questions.
Give a small example answer for each.
Write them as sentences, not bullet points.

Tone: warm, gentle, calm, respectful, kid-safe, never preachy.
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


# ------------------------------------------------------------
# APOLOGETICS FOLLOW-UP / CLARIFICATION FUNCTION
# ------------------------------------------------------------
def apologetics_clarify(question: str, grade_level="8", character="everly"):
    """
    A softer, simpler apologetics answer for younger students,
    still following the 6-section Homework Buddy style.
    """

    prompt = f"""
You are a gentle Christian apologetics tutor.

The student said:
\"{question}\"

Give a softer version of the SIX-section Homework Buddy format.
NO bullet points — only paragraphs.

SECTION 1 — OVERVIEW
Explain what the student seems confused about.

SECTION 2 — KEY FACTS
Explain simple background ideas.

SECTION 3 — CHRISTIAN VIEW
Explain gently what many Christians believe.

SECTION 4 — AGREEMENT
Describe what most people can agree on.

SECTION 5 — DIFFERENCE
Explain softly where views may differ.

SECTION 6 — PRACTICE
Ask 2–3 tiny reflection questions with short sentence-length example answers.
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


