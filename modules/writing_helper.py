# modules/writing_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


# ------------------------------------------------------------
# Detect Christian-oriented writing questions
# ------------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "biblical", "god", "jesus", "faith",
        "christian worldview", "from a christian perspective",
        "how does this relate to god", "how does this relate to christianity",
    ]
    return any(k.lower() in text.lower() for k in keywords)


# ------------------------------------------------------------
# Base writing prompt
# ------------------------------------------------------------
def build_writing_prompt(topic: str, grade: str):
    return f"""
You are a gentle writing tutor helping a grade {grade} student.

The student asked:
"{topic}"

Answer using all SIX labeled sections.

SECTION 1 — OVERVIEW
Explain the writing idea in simple, calm sentences.

SECTION 2 — KEY FACTS
Teach the important writing concepts: structure, clarity, purpose,
audience, word choice, and simple grammar ideas.

SECTION 3 — CHRISTIAN VIEW
Explain softly how Christians may think about communication:
truthfulness, encouragement, kindness, clarity, and using words wisely.
If the topic is not naturally Christian, simply mention this gently.

SECTION 4 — AGREEMENT
Explain what nearly everyone agrees on about good writing.

SECTION 5 — DIFFERENCE
Explain how Christian and secular motivations may differ kindly.

SECTION 6 — PRACTICE
Give 2–3 small practice prompts with example answers in sentences.

Tone must be calm, slow, warm, and kid-friendly.
"""


# ------------------------------------------------------------
# Christian-specific writing prompt
# ------------------------------------------------------------
def build_christian_writing_prompt(topic: str, grade: str):
    return f"""
The student asked a writing question from a Christian perspective:

"{topic}"

Answer using SIX warm and gentle sections.

SECTION 1 — OVERVIEW
Explain the writing idea simply.

SECTION 2 — KEY FACTS
Teach the important writing skills for this topic.

SECTION 3 — CHRISTIAN VIEW
Explain how Christians think about speech: truth, grace, encouragement,
purpose, and kindness in communication.

SECTION 4 — AGREEMENT
Explain what all worldviews agree on about good writing.

SECTION 5 — DIFFERENCE
Explain softly how motivations may differ.

SECTION 6 — PRACTICE
Give 2–3 tiny writing practice ideas with example answers.

Tone must be soft and child-friendly.
"""


# ------------------------------------------------------------
# MAIN WRITING EXPLAINER (USED BY APP)
# ------------------------------------------------------------
def help_write(topic: str, grade_level="8", character="everly"):

    # Choose correct prompt
    if is_christian_question(topic):
        prompt = build_christian_writing_prompt(topic, grade_level)
    else:
        prompt = build_writing_prompt(topic, grade_level)

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
# WRITING QUIZ
# ------------------------------------------------------------
def writing_quiz(topic: str, grade_level="8", character="everly"):

    prompt = f"""
Create a gentle writing quiz for a grade {grade_level} student.

Topic: "{topic}"

Use SIX labeled sections:
SECTION 1 — OVERVIEW
SECTION 2 — KEY FACTS
SECTION 3 — CHRISTIAN VIEW
SECTION 4 — AGREEMENT
SECTION 5 — DIFFERENCE
SECTION 6 — PRACTICE

Tone must be slow, warm, kid-friendly, and clear.
"""

    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    sections = parse_into_sections(raw)

    return format_answer(
        overview=sections.get("overview", "").strip(),
        key_facts=sections.get("key_facts", []),
        christian_view=sections.get("christian_view", "").strip(),
        agreement=sections.get("agreement", []),
        difference=sections.get("difference", []),
        practice=sections.get("practice", []),
        raw_text=raw
    )
