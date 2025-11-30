# modules/study_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


# -----------------------------------------------------------
# Socratic Tutor Layer — BEFORE the 6 sections
# -----------------------------------------------------------
def socratic_layer(topic: str, grade_level: str):
    """
    Gives the student a gentle pre-thinking moment before the full answer.
    This appears BEFORE the six Homework Buddy sections.
    """
    return f"""
The student wants help studying this topic:

\"{topic}\"

Before giving the final six-section Homework Buddy answer:

1. Restate the topic in very simple, friendly words.
2. Give one tiny hint that helps the student begin thinking.
3. Ask one gentle guiding question (very small).
4. Give a soft nudge toward understanding, without giving away the full answer.

Then continue immediately with the six-section structure.
Keep everything warm, simple, and grade {grade_level} friendly.
"""


# -----------------------------------------------------------
# QUIZ prompt (still uses six sections)
# -----------------------------------------------------------
def build_quiz_prompt(topic: str, grade_level: str):
    return f"""
Create a gentle study quiz for the topic "{topic}" using ALL SIX Homework Buddy sections.
No bullet points. Use short paragraphs.

SECTION 1 — OVERVIEW
Introduce what the quiz is about in calm sentences.

SECTION 2 — KEY FACTS
Explain the most important ideas with 3–5 simple sentences.

SECTION 3 — CHRISTIAN VIEW
If relevant, gently explain how Christians understand meaning or purpose here.

SECTION 4 — AGREEMENT
Explain in simple paragraph form what most worldviews agree on.

SECTION 5 — DIFFERENCE
Explain respectfully how interpretations may differ.

SECTION 6 — PRACTICE
Write several quiz-style questions with very short example answers.
"""


# -----------------------------------------------------------
# FLASHCARDS prompt (still six sections)
# -----------------------------------------------------------
def build_flashcard_prompt(topic: str, grade_level: str):
    return f"""
Create flashcards for the topic "{topic}" using the six-section Homework Buddy format.
NO bullet points. Use small, simple paragraphs.

Flashcards should be extremely simple and kid-friendly.

SECTION 6 — PRACTICE should contain 3–5 flashcard-style Q&A pairs.
"""


# -----------------------------------------------------------
# PUBLIC FUNCTION — QUIZ GENERATOR (Socratic + 6 sections)
# -----------------------------------------------------------
def generate_quiz(topic: str, grade_level="8", character=None):

    if character is None:
        character = "theo"

    base = build_quiz_prompt(topic, grade_level)
    full_prompt = socratic_layer(topic, grade_level) + "\n" + base

    enriched = apply_personality(character, full_prompt)

    raw = study_buddy_ai(enriched, grade_level, character)
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


# -----------------------------------------------------------
# PUBLIC FUNCTION — FLASHCARDS (Socratic + 6 sections)
# -----------------------------------------------------------
def flashcards(topic: str, grade_level="8", character=None):

    if character is None:
        character = "theo"

    base = build_flashcard_prompt(topic, grade_level)
    full_prompt = socratic_layer(topic, grade_level) + "\n" + base

    enriched = apply_personality(character, full_prompt)

    raw = study_buddy_ai(enriched, grade_level, character)
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
