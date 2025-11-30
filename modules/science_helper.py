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
    text_low = text.lower()
    return any(k in text_low for k in keywords)


# -------------------------------------------------------
# Standard science prompt (NO bullets, 6 sections)
# -------------------------------------------------------
def build_science_prompt(topic: str, grade_level: str):
    return f"""
The student asked a science question:

\"{topic}\"

Explain it using the SIX-section Homework Buddy format.
NO bullet points. Only short, gentle paragraphs.

SECTION 1 — OVERVIEW
Give 2–3 calm sentences introducing the idea.

SECTION 2 — KEY FACTS
Write a short paragraph explaining the most important scientific ideas.

SECTION 3 — CHRISTIAN VIEW
Gently explain how many Christians understand the order and design in nature.

SECTION 4 — AGREEMENT
Explain in a short paragraph what Christians and secular views agree on.

SECTION 5 — DIFFERENCE
Explain respectfully how interpretations may differ.

SECTION 6 — PRACTICE
Write 2–3 tiny practice questions with short example answers.
"""


# -------------------------------------------------------
# Christian-specific science prompt
# -------------------------------------------------------
def build_christian_science_prompt(topic: str, grade_level: str):
    return f"""
The student asked this science question from a Christian perspective:

\"{topic}\"

Explain it using the SIX-section Homework Buddy format.
NO bullet points. Only short, gentle paragraphs.

SECTION 1 — OVERVIEW
Introduce the idea simply and calmly.

SECTION 2 — KEY FACTS
Explain the important scientific ideas in a few slow sentences.

SECTION 3 — CHRISTIAN VIEW
Explain softly how many Christians understand creation, order, and purpose.

SECTION 4 — AGREEMENT
Explain what most worldviews agree on in this topic.

SECTION 5 — DIFFERENCE
Explain gently how interpretations may differ.

SECTION 6 — PRACTICE
Ask 2–3 small practice questions with very short example answers.
"""


# -------------------------------------------------------
# MAIN PUBLIC FUNCTION — uses universal parser + formatter
# -------------------------------------------------------
def explain_science(topic: str, grade_level="8", character="everly"):

    # Pick which base prompt to use
    if is_christian_question(topic):
        base_prompt = build_christian_science_prompt(topic, grade_level)
    else:
        base_prompt = build_science_prompt(topic, grade_level)

    # Add character personality
    enriched_prompt = apply_personality(character, base_prompt)

    # Get raw output from the AI
    raw = study_buddy_ai(enriched_prompt, grade_level, character)

    # Parse into six sections
    sections = parse_into_sections(raw)

    # Return normalized final answer for subject.html
    return format_answer(
        overview=sections.get("overview", ""),
        key_facts=sections.get("key_facts", []),
        christian_view=sections.get("christian_view", ""),
        agreement=sections.get("agreement", []),
        difference=sections.get("difference", []),
        practice=sections.get("practice", []),
        raw_text=raw
    )
