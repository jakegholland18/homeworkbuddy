# modules/bible_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


# ------------------------------------------------------------
# Detect Christian / Bible questions
# ------------------------------------------------------------
def is_christian_request(text: str) -> bool:
    keywords = [
        "bible", "jesus", "god", "christian", "faith", "scripture",
        "christianity", "biblical", "verse",
        "christian worldview",
        "how does this relate to god",
        "what does this mean biblically"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# ------------------------------------------------------------
# Build 6-section Bible prompt (Main Lesson)
# ------------------------------------------------------------
def build_bible_lesson_prompt(topic: str, grade: str):
    return f"""
You are a gentle Christian Bible tutor for a grade {grade} student.

The student asked:
\"{topic}\"

Answer using the **six-section Homework Buddy format**.

SECTION 1 — OVERVIEW
Give a calm 2–3 sentence explanation of what this Bible topic is about.

SECTION 2 — KEY FACTS
List 3–5 simple truths Christians believe about this topic.
Use dash bullets ("- ").

SECTION 3 — CHRISTIAN VIEW
Explain softly why Christians believe this matters
and how it fits into everyday life.
Use Scripture gently only if it naturally fits.

SECTION 4 — AGREEMENT
List 2–4 things Christians and non-Christians could both notice
or agree on about this topic.
Use dash bullets.

SECTION 5 — DIFFERENCE
List gentle worldview differences between Christians and secular views.
Use dash bullets.
Be respectful and peaceful.

SECTION 6 — PRACTICE
Give 2–3 tiny reflection questions with short example answers.
Each question should begin with "- ".

Tone:
warm, slow, simple, encouraging, child-friendly.
"""


# ------------------------------------------------------------
# Build prompt for explaining a Bible verse
# ------------------------------------------------------------
def build_verse_prompt(reference: str, text: str, grade: str):
    verse_q = f"What does {reference} mean? The verse says: {text}"

    return f"""
You are a gentle Christian Bible tutor teaching a grade {grade} student.

The student asked:
\"{verse_q}\"

Answer using the **six-section Homework Buddy format**.

SECTION 1 — OVERVIEW
Explain what the verse means in simple, warm language.

SECTION 2 — KEY FACTS
List a few simple truths Christians learn from this verse.
Use dash bullets.

SECTION 3 — CHRISTIAN VIEW
Explain softly what Christians believe this verse teaches
and how it encourages them.

SECTION 4 — AGREEMENT
List things anyone might notice or agree on about the verse.
Use dash bullets.

SECTION 5 — DIFFERENCE
List gentle worldview differences between Christian and secular interpretations.
Use dash bullets.

SECTION 6 — PRACTICE
Give 2–3 tiny reflection questions with short example answers.
Each question should begin with "- ".

Tone: calm, warm, simple.
"""


# ------------------------------------------------------------
# Build prompt for Bible story
# ------------------------------------------------------------
def build_story_prompt(story: str, grade: str):
    return f"""
You are a gentle Christian Bible tutor for a grade {grade} student.

Tell the story of:
\"{story}\"

Then explain it using the **six-section Homework Buddy format**.

SECTION 1 — OVERVIEW
Retell the story slowly in simple, warm language.

SECTION 2 — KEY FACTS
List a few simple truths Christians learn from the story.
Use dash bullets.

SECTION 3 — CHRISTIAN VIEW
Explain gently why Christians believe this story matters
and what God is teaching through it.

SECTION 4 — AGREEMENT
List things anyone could notice or agree on.
Use dash bullets.

SECTION 5 — DIFFERENCE
List soft worldview differences between Christian and secular interpretations.
Use dash bullets.

SECTION 6 — PRACTICE
Give 2–3 small reflection questions with short example answers.
Each must begin with "- ".

Tone:
calm, warm, simple, not dramatic.
"""


# ------------------------------------------------------------
# Build prompt for general Christian worldview questions
# ------------------------------------------------------------
def build_worldview_prompt(question: str, grade: str):
    return f"""
You are a gentle Christian worldview tutor for a grade {grade} student.

The student asked:
\"{question}\"

Answer using the **six-section Homework Buddy format**.

SECTION 1 — OVERVIEW
Explain the idea in soft, everyday language.

SECTION 2 — KEY FACTS
List a few basic truths Christians think about this topic.
Use dash bullets.

SECTION 3 — CHRISTIAN VIEW
Explain softly why Christians believe this
and why it matters to them.

SECTION 4 — AGREEMENT
List things Christians and non-Christians may both agree on.
Use dash bullets.

SECTION 5 — DIFFERENCE
List gentle worldview differences.
Use dash bullets.

SECTION 6 — PRACTICE
Offer 2–3 reflection questions with example answers.
Each must begin with "- ".

Tone:
peaceful, warm, kind, encouraging.
"""


# ------------------------------------------------------------
# MAIN PUBLIC FUNCTIONS (all use parser + format_answer)
# ------------------------------------------------------------
def bible_lesson(topic: str, grade_level="8", character="everly"):
    prompt = build_bible_lesson_prompt(topic, grade_level)
    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    sections = parse_into_sections(raw)

    return format_answer(**sections)


def explain_verse(reference: str, text: str, grade_level="8", character="everly"):
    prompt = build_verse_prompt(reference, text, grade_level)
    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    sections = parse_into_sections(raw)

    return format_answer(**sections)


def explain_bible_story(story: str, grade_level="8", character="everly"):
    prompt = build_story_prompt(story, grade_level)
    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    sections = parse_into_sections(raw)

    return format_answer(**sections)


def christian_worldview(question: str, grade_level="8", character="everly"):
    prompt = build_worldview_prompt(question, grade_level)
    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    sections = parse_into_sections(raw)

    return format_answer(**sections)

