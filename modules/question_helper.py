# modules/question_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


# -------------------------------------------------------
# Detect Christian perspective in general questions
# -------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "christianity", "jesus", "god", "faith",
        "biblical", "bible",
        "how does this relate to god",
        "from a christian perspective",
        "christian worldview"
    ]
    text_low = text.lower()
    return any(k in text_low for k in keywords)


# -------------------------------------------------------
# Build general 6-section prompt (NO bullets)
# -------------------------------------------------------
def build_general_prompt(question: str, grade_level: str):
    return f"""
The student asked a general question:

\"{question}\"

Please answer using the SIX-section Homework Buddy format.
NO bullet points anywhere. Only calm, short paragraphs.

SECTION 1 — OVERVIEW
Give a simple explanation of what the question is really about.

SECTION 2 — KEY FACTS
Explain the most important ideas in 3–5 short, gentle sentences.

SECTION 3 — CHRISTIAN VIEW
Explain softly how many Christians think about this topic,
if it naturally applies. Otherwise explain that Christians reflect
on meaning, purpose, and wisdom in all topics.

SECTION 4 — AGREEMENT
Explain in one short paragraph what most worldviews agree on.

SECTION 5 — DIFFERENCE
Explain softly how worldviews might differ in interpretation.

SECTION 6 — PRACTICE
Ask 2–3 tiny practice questions and provide short example answers.
"""


# -------------------------------------------------------
# Build Christian-directed 6-section prompt (NO bullets)
# -------------------------------------------------------
def build_christian_prompt(question: str, grade_level: str):
    return f"""
The student asked this question from a Christian perspective:

\"{question}\"

Please answer using the SIX-section Homework Buddy structure.
NO bullet points.

SECTION 1 — OVERVIEW
Explain the question in very simple, calm language.

SECTION 2 — KEY FACTS
Explain the most important ideas Christians consider.

SECTION 3 — CHRISTIAN VIEW
Explain softly what Christians believe and why it matters.

SECTION 4 — AGREEMENT
Explain briefly what Christians and non-Christians may agree on.

SECTION 5 — DIFFERENCE
Explain gently where worldviews may differ in interpretation.

SECTION 6 — PRACTICE
Ask 2–3 small reflection questions with short example answers.
"""


# -------------------------------------------------------
# MAIN PUBLIC FUNCTION
# -------------------------------------------------------
def answer_question(question: str, grade_level="8", character="everly"):

    # Choose which base prompt to use
    if is_christian_question(question):
        base_prompt = build_christian_prompt(question, grade_level)
    else:
        base_prompt = build_general_prompt(question, grade_level)

    # Apply personality voice
    enriched_prompt = apply_personality(character, base_prompt)

    # AI OUTPUT (strict 6 sections)
    raw = study_buddy_ai(enriched_prompt, grade_level, character)

    # Parse using universal parser
    sections = parse_into_sections(raw)

    # Return HTML-ready structure
    return format_answer(
        overview=sections.get("overview", ""),
        key_facts=sections.get("key_facts", []),
        christian_view=sections.get("christian_view", ""),
        agreement=sections.get("agreement", []),
        difference=sections.get("difference", []),
        practice=sections.get("practice", []),
        raw_text=raw
    )
