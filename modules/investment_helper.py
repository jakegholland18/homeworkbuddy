# modules/investment_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


# ------------------------------------------------------------
# Detect Christian-oriented investing questions
# ------------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "biblical", "god", "jesus", "bible", "faith",
        "christian perspective", "christian view",
        "what does the bible say", "how does this relate to god"
    ]
    txt = text.lower()
    return any(k in txt for k in keywords)


# ------------------------------------------------------------
# Standard investing prompt (NO BULLETS)
# ------------------------------------------------------------
def build_investing_prompt(topic: str, grade: str):
    return f"""
You are a gentle investing tutor helping a grade {grade} student.

The student asked:
\"{topic}\"

Use the SIX-section Homework Buddy format.
NO bullet points. ONLY short paragraphs.

SECTION 1 — OVERVIEW
Explain the investing idea in 2–3 short, simple sentences.

SECTION 2 — KEY FACTS
Describe several important ideas such as saving, risk, long term thinking,
value, growth, and basic financial responsibility using small paragraph sentences.
No bullet lists.

SECTION 3 — CHRISTIAN VIEW
Explain softly how many Christians think about money with stewardship,
responsibility, generosity, avoiding greed, and planning wisely.

SECTION 4 — AGREEMENT
Explain in one small paragraph what Christians and secular worldviews
both agree on, such as the importance of saving, planning, and understanding risk.

SECTION 5 — DIFFERENCE
Explain gently how Christian motivation such as stewardship and generosity
may differ from a money-first or purely secular perspective.

SECTION 6 — PRACTICE
Give 2–3 tiny practice questions with simple example answers.
Write them in short paragraph sentences.
"""


# ------------------------------------------------------------
# Christian-directed investing prompt (NO BULLETS)
# ------------------------------------------------------------
def build_christian_investing_prompt(topic: str, grade: str):
    return f"""
The student asked this investing question from a Christian perspective:

\"{topic}\"

Use the SIX-section Homework Buddy format.
NO bullet points.

SECTION 1 — OVERVIEW
Explain the idea calmly in 2–3 sentences.

SECTION 2 — KEY FACTS
Describe the basic ideas needed to understand this investing topic
using short, clear sentences.

SECTION 3 — CHRISTIAN VIEW
Explain softly how Christians understand stewardship, responsibility,
avoiding greed, and using resources wisely.

SECTION 4 — AGREEMENT
Explain one short paragraph of ideas that all worldviews agree on.

SECTION 5 — DIFFERENCE
Explain gently how motivations or values may differ.

SECTION 6 — PRACTICE
Give 2–3 reflection questions with tiny example answers.
"""


# ------------------------------------------------------------
# MAIN PUBLIC FUNCTION — explain investing
# ------------------------------------------------------------
def explain_investing(topic: str, grade_level="8", character="everly"):

    # Choose base prompt
    if is_christian_question(topic):
        base_prompt = build_christian_investing_prompt(topic, grade_level)
    else:
        base_prompt = build_investing_prompt(topic, grade_level)

    # Add personality layer
    enriched = apply_personality(character, base_prompt)

    # Get AI response
    raw = study_buddy_ai(enriched, grade_level, character)

    # Parse into universal structure
    sections = parse_into_sections(raw)

    # Return HTML-friendly data
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
# GENERAL INVESTING QUESTION (same structure)
# ------------------------------------------------------------
def investment_question(question: str, grade_level="8", character="everly"):

    base_prompt = build_investing_prompt(question, grade_level)
    enriched = apply_personality(character, base_prompt)
    raw = study_buddy_ai(enriched, grade_level, character)

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
# INVESTING QUIZ — still six sections (NO BULLETS)
# ------------------------------------------------------------
def investment_quiz(topic: str, grade_level="8", character="everly"):

    prompt = f"""
Create a gentle investing quiz for a grade {grade_level} student.

Topic: \"{topic}\"

Use the SIX-section Homework Buddy format.
NO bullet points.

SECTION 1 — OVERVIEW
Explain the topic in a small, calm paragraph.

SECTION 2 — KEY FACTS
Describe the most important ideas the student should remember.

SECTION 3 — CHRISTIAN VIEW
Explain stewardship and wise planning softly and clearly.

SECTION 4 — AGREEMENT
Explain what all worldviews agree on in one small paragraph.

SECTION 5 — DIFFERENCE
Explain gently how perspectives differ.

SECTION 6 — PRACTICE
Write a few tiny quiz questions with short example answers.
"""

    enriched = apply_personality(character, prompt)
    raw = study_buddy_ai(enriched, grade_level, character)
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



