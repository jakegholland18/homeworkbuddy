# modules/history_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import format_answer


# ------------------------------------------------------------
# Detect Christian-worldview history questions
# ------------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "christianity", "god", "jesus", "bible", "biblical",
        "faith", "christian worldview", "from a christian perspective",
        "how does this relate to christianity", "how does this relate to god"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# ------------------------------------------------------------
# Universal extractor (keeps everything consistent)
# ------------------------------------------------------------
def _extract(raw: str, label: str) -> str:
    return raw.split(label)[-1].strip() if label in raw else "Not available."


# ------------------------------------------------------------
# Build prompt for non-Christian history questions
# ------------------------------------------------------------
def build_history_prompt(topic: str, grade: str):
    return f"""
You are a gentle history tutor for a grade {grade} student.

The student asked about:
"{topic}"

Answer using SIX soft, child-friendly sections.

SECTION 1 — OVERVIEW
Explain the topic in calm, short sentences.

SECTION 2 — KEY FACTS
Explain the important ideas using slow, simple sentences.
Talk about when it happened, who was involved, and why it matters.

SECTION 3 — CHRISTIAN VIEW
Explain softly how many Christians look at history.
Focus on choices, character, and learning from the past.
If Christianity is not part of the topic, explain that Christians
still try to learn moral lessons from history.

SECTION 4 — AGREEMENT
Explain what people of all worldviews agree on
(what happened, cause and effect, lessons about human behavior).

SECTION 5 — DIFFERENCE
Explain gently how Christian and secular views may differ
in meaning, purpose, or lessons learned.

SECTION 6 — PRACTICE
Ask 2–3 small reflection questions and give short example answers.

Tone must stay slow, warm, gentle, and simple.
"""


# ------------------------------------------------------------
# Build prompt for Christian-directed questions
# ------------------------------------------------------------
def build_christian_history_prompt(topic: str, grade: str):
    return f"""
The student asked this history question from a Christian perspective:

"{topic}"

Answer using SIX warm, gentle sections.

SECTION 1 — OVERVIEW
Explain the topic slowly and clearly.

SECTION 2 — KEY FACTS
Explain the basic historical ideas in short sentences.

SECTION 3 — CHRISTIAN VIEW
Explain softly how Christians understand the event,
focusing on choices, character, and God’s long-term plan,
while staying gentle and age-appropriate.

SECTION 4 — AGREEMENT
Explain what people of any worldview agree on about the event.

SECTION 5 — DIFFERENCE
Explain kindly how interpretations may differ.

SECTION 6 — PRACTICE
Ask 2–3 small reflection questions with short example answers.
"""


# ------------------------------------------------------------
# MAIN HISTORY EXPLAINER
# ------------------------------------------------------------
def explain_history(topic: str, grade_level="8", character="everly"):

    if is_christian_question(topic):
        prompt = build_christian_history_prompt(topic, grade_level)
    else:
        prompt = build_history_prompt(topic, grade_level)

    prompt = apply_personality(character, prompt)

    raw = study_buddy_ai(prompt, grade_level, character)

    overview       = _extract(raw, "SECTION 1")
    key_facts      = _extract(raw, "SECTION 2")
    christian_view = _extract(raw, "SECTION 3")
    agreement      = _extract(raw, "SECTION 4")
    difference     = _extract(raw, "SECTION 5")
    practice       = _extract(raw, "SECTION 6")

    return format_answer(
        overview=overview,
        key_facts=key_facts,
        christian_view=christian_view,
        agreement=agreement,
        difference=difference,
        practice=practice
    )


# ------------------------------------------------------------
# GENERAL HISTORY QUESTION
# ------------------------------------------------------------
def answer_history_question(question: str, grade_level="8", character="everly"):

    # Always reuse the standard structure
    prompt = build_history_prompt(question, grade_level)
    prompt = apply_personality(character, prompt)

    raw = study_buddy_ai(prompt, grade_level, character)

    overview       = _extract(raw, "SECTION 1")
    key_facts      = _extract(raw, "SECTION 2")
    christian_view = _extract(raw, "SECTION 3")
    agreement      = _extract(raw, "SECTION 4")
    difference     = _extract(raw, "SECTION 5")
    practice       = _extract(raw, "SECTION 6")

    return format_answer(
        overview=overview,
        key_facts=key_facts,
        christian_view=christian_view,
        agreement=agreement,
        difference=difference,
        practice=practice
    )


# ------------------------------------------------------------
# HISTORY QUIZ
# ------------------------------------------------------------
def generate_history_quiz(topic: str, grade_level="8", character="everly"):

    prompt = f"""
Create a calm, gentle history quiz for a grade {grade_level} student.

Topic: "{topic}"

Use SIX sections:

SECTION 1 — OVERVIEW
Explain the topic softly.

SECTION 2 — KEY FACTS
Explain the basics they should remember.

SECTION 3 — CHRISTIAN VIEW
Soft explanation of how many Christians understand moral lessons in history.

SECTION 4 — AGREEMENT
Explain what all worldviews agree on.

SECTION 5 — DIFFERENCE
Explain respectful differences in interpretation.

SECTION 6 — PRACTICE
Write a few quiz questions with short answers.

Tone must stay warm, slow, and non-dramatic.
"""

    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    overview       = _extract(raw, "SECTION 1")
    key_facts      = _extract(raw, "SECTION 2")
    christian_view = _extract(raw, "SECTION 3")
    agreement      = _extract(raw, "SECTION 4")
    difference     = _extract(raw, "SECTION 5")
    practice       = _extract(raw, "SECTION 6")

    return format_answer(
        overview=overview,
        key_facts=key_facts,
        christian_view=christian_view,
        agreement=agreement,
        difference=difference,
        practice=practice
    )



