# modules/bible_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import format_answer


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
# Universal extraction helper
# ------------------------------------------------------------
def _extract(raw: str, label: str) -> str:
    return raw.split(label)[-1].strip() if label in raw else "Not available."


# ------------------------------------------------------------
# MAIN BIBLE LESSON — 6 sections
# ------------------------------------------------------------
def bible_lesson(topic: str, grade_level="8", character="everly"):
    """
    Explains a Bible topic using the 6-section Homework Buddy system.
    """

    prompt = f"""
You are a gentle Christian Bible tutor teaching a grade {grade_level} student.

The student asked:
"{topic}"

Answer using SIX warm, child-friendly sections.

SECTION 1 — OVERVIEW
Explain in calm, short sentences what this topic is about.

SECTION 2 — KEY IDEAS
Explain a few simple ideas Christians believe about this topic.
Use gentle and very clear sentences.

SECTION 3 — CHRISTIAN VIEW
Explain softly why Christians believe this matters,
how they understand it, and how it connects to everyday life.
Use Scripture gently only if it fits naturally.

SECTION 4 — AGREEMENT
Explain what Christians and non-Christians might both notice
or agree on in this topic.

SECTION 5 — DIFFERENCE
Explain kindly how Christian and secular interpretations differ,
but stay peaceful and respectful.

SECTION 6 — PRACTICE
Ask 2–3 small reflection questions.
Give short example answers.

Tone:
slow, warm, simple, encouraging, never forceful.
"""

    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    overview       = _extract(raw, "SECTION 1")
    key_ideas      = _extract(raw, "SECTION 2")
    christian_view = _extract(raw, "SECTION 3")
    agreement      = _extract(raw, "SECTION 4")
    difference     = _extract(raw, "SECTION 5")
    practice       = _extract(raw, "SECTION 6")

    return format_answer(
        overview=overview,
        key_facts=key_ideas,
        christian_view=christian_view,
        agreement=agreement,
        difference=difference,
        practice=practice
    )


# ------------------------------------------------------------
# EXPLAIN A VERSE — 6 sections
# ------------------------------------------------------------
def explain_verse(reference: str, text: str, grade_level="8", character="everly"):

    verse_question = f"What does {reference} mean? The verse says: {text}"

    prompt = f"""
You are a gentle Bible tutor helping a grade {grade_level} student.

The student asked:
"{verse_question}"

Answer using SIX warm sections.

SECTION 1 — OVERVIEW
Explain simply what this verse is about in calm, short sentences.

SECTION 2 — KEY IDEAS
Explain a few simple things Christians learn from this verse.

SECTION 3 — CHRISTIAN VIEW
Explain softly what Christians believe this verse teaches
and how it encourages them.

SECTION 4 — AGREEMENT
Explain what anyone might notice or agree on about the verse.

SECTION 5 — DIFFERENCE
Explain kindly how Christian and secular views may understand the verse differently.

SECTION 6 — PRACTICE
Ask 2–3 small reflection questions with short example answers.

Keep tone warm, calm, simple.
"""

    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    overview       = _extract(raw, "SECTION 1")
    key_ideas      = _extract(raw, "SECTION 2")
    christian_view = _extract(raw, "SECTION 3")
    agreement      = _extract(raw, "SECTION 4")
    difference     = _extract(raw, "SECTION 5")
    practice       = _extract(raw, "SECTION 6")

    return format_answer(
        overview=overview,
        key_facts=key_ideas,
        christian_view=christian_view,
        agreement=agreement,
        difference=difference,
        practice=practice
    )


# ------------------------------------------------------------
# BIBLE STORY — 6 sections
# ------------------------------------------------------------
def explain_bible_story(story: str, grade_level="8", character="everly"):

    prompt = f"""
You are a gentle Bible tutor teaching a grade {grade_level} student.

Tell the story of:
"{story}"

Then explain it using SIX small child-friendly sections.

SECTION 1 — OVERVIEW
Retell the story slowly in simple, warm language.

SECTION 2 — KEY IDEAS
Explain a few simple truths Christians learn from this story.

SECTION 3 — CHRISTIAN VIEW
Explain gently why Christians believe this story matters
and what they think God is teaching through it.

SECTION 4 — AGREEMENT
Explain what anyone could notice or agree on about the story.

SECTION 5 — DIFFERENCE
Explain softly how Christian and secular views may differ
in meaning or interpretation.

SECTION 6 — PRACTICE
Ask 2–3 reflection questions with very short example answers.

Tone:
calm, warm, simple, not dramatic.
"""

    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    overview       = _extract(raw, "SECTION 1")
    key_ideas      = _extract(raw, "SECTION 2")
    christian_view = _extract(raw, "SECTION 3")
    agreement      = _extract(raw, "SECTION 4")
    difference     = _extract(raw, "SECTION 5")
    practice       = _extract(raw, "SECTION 6")

    return format_answer(
        overview=overview,
        key_facts=key_ideas,
        christian_view=christian_view,
        agreement=agreement,
        difference=difference,
        practice=practice
    )


# ------------------------------------------------------------
# GENERAL CHRISTIAN WORLDVIEW QUESTIONS
# ------------------------------------------------------------
def christian_worldview(question: str, grade_level="8", character="everly"):

    prompt = f"""
You are a gentle Christian worldview tutor for a grade {grade_level} student.

The student asked:
"{question}"

Answer using SIX soft, calm sections.

SECTION 1 — OVERVIEW
Explain the question in simple, everyday language.

SECTION 2 — KEY IDEAS
Explain a few basic ideas Christians think about on this topic.

SECTION 3 — CHRISTIAN VIEW
Explain softly what Christians believe and why it matters to them.

SECTION 4 — AGREEMENT
Explain what Christians and non-Christians may agree on.

SECTION 5 — DIFFERENCE
Explain kindly how Christian and secular worldviews differ.

SECTION 6 — PRACTICE
Ask 2–3 reflection questions with short example answers.

Tone:
peaceful, warm, welcoming, not forceful.
"""

    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    overview       = _extract(raw, "SECTION 1")
    key_ideas      = _extract(raw, "SECTION 2")
    christian_view = _extract(raw, "SECTION 3")
    agreement      = _extract(raw, "SECTION 4")
    difference     = _extract(raw, "SECTION 5")
    practice       = _extract(raw, "SECTION 6")

    return format_answer(
        overview=overview,
        key_facts=key_ideas,
        christian_view=christian_view,
        agreement=agreement,
        difference=difference,
        practice=practice
    )
