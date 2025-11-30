# modules/bible_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


# ------------------------------------------------------------
# Detect Christian / Bible requests
# ------------------------------------------------------------
def is_christian_request(text: str) -> bool:
    keywords = [
        "bible", "jesus", "god", "christian", "faith", "scripture",
        "christianity", "biblical", "verse",
        "christian worldview",
        "how does this relate to god",
        "what does this mean biblically"
    ]
    txt = text.lower()
    return any(k in txt for k in keywords)


# ------------------------------------------------------------
# Main Bible Topic — 6 Sections, NO bullets
# ------------------------------------------------------------
def bible_lesson(topic: str, grade_level="8", character="everly"):
    """
    Full Bible lesson using the mandatory 6-section Homework Buddy format.
    Output is paragraph-based only — no bullet points.
    """

    prompt = f"""
You are a gentle Christian Bible tutor for a grade {grade_level} student.

The student asked:
\"{topic}\"

Use the SIX-section Homework Buddy format.
NO bullet points allowed — only short paragraphs.

SECTION 1 — OVERVIEW
Give a calm, simple explanation of what this topic is about in 2–3 sentences.

SECTION 2 — KEY IDEAS
Explain a few important ideas Christians believe about this topic
using a small paragraph of simple sentences.

SECTION 3 — CHRISTIAN VIEW
Describe softly why Christians believe this matters,
what they think it teaches, and how it connects to daily life.
Use Scripture only if it naturally fits.

SECTION 4 — AGREEMENT
Explain what Christians and non-Christians may both notice or agree on
about this topic using a short paragraph.

SECTION 5 — DIFFERENCE
Explain kindly how Christian and secular interpretations may differ.
Keep the tone peaceful and respectful.

SECTION 6 — PRACTICE
Ask 2–3 tiny reflection questions with short example answers written
as plain sentences (not bullets).
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


# ------------------------------------------------------------
# Explain a Specific Verse — 6 sections, paragraph-only
# ------------------------------------------------------------
def explain_verse(reference: str, text: str, grade_level="8", character="everly"):

    verse_question = f"What does {reference} mean? The verse says: {text}"

    prompt = f"""
You are a gentle Bible tutor teaching a grade {grade_level} student.

The student asked:
\"{verse_question}\"

Use the SIX-section Homework Buddy format.
NO bullet points — only short, calm paragraphs.

SECTION 1 — OVERVIEW
Explain what the verse is about in 2–3 simple sentences.

SECTION 2 — KEY IDEAS
Describe a few key ideas Christians learn from this verse using a small paragraph.

SECTION 3 — CHRISTIAN VIEW
Explain softly how Christians understand this verse and how it encourages them.

SECTION 4 — AGREEMENT
Explain what anyone might notice or agree on about this verse.

SECTION 5 — DIFFERENCE
Explain kindly how the meaning may differ between a Christian and secular view.

SECTION 6 — PRACTICE
Ask 2–3 tiny reflection questions with short example answers written as sentences.
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


# ------------------------------------------------------------
# Explain a Whole Bible Story — 6 sections
# ------------------------------------------------------------
def explain_bible_story(story: str, grade_level="8", character="everly"):

    prompt = f"""
You are a gentle Bible tutor for a grade {grade_level} student.

Tell the story of:
\"{story}\"

Then explain it using SIX short, calm paragraphs.
NO bullet points.

SECTION 1 — OVERVIEW
Retell the story slowly in warm, simple sentences.

SECTION 2 — KEY IDEAS
Explain basic truths Christians learn from this story in one short paragraph.

SECTION 3 — CHRISTIAN VIEW
Explain gently why Christians believe this story matters
and what God may be teaching through it.

SECTION 4 — AGREEMENT
Explain what anyone might notice or agree on about the story.

SECTION 5 — DIFFERENCE
Explain softly how Christian and secular interpretations differ.

SECTION 6 — PRACTICE
Ask 2–3 tiny reflection questions with short example answers.
All responses must be sentence-based, not bullets.
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


# ------------------------------------------------------------
# General Christian worldview question — 6 sections
# ------------------------------------------------------------
def christian_worldview(question: str, grade_level="8", character="everly"):

    prompt = f"""
You are a gentle Christian worldview tutor for a grade {grade_level} student.

The student asked:
\"{question}\"

Use the SIX-section Homework Buddy format.
NO bullets — all paragraphs.

SECTION 1 — OVERVIEW
Explain the question simply in 2–3 calm sentences.

SECTION 2 — KEY IDEAS
Describe a few basic ideas Christians think about this topic in a small paragraph.

SECTION 3 — CHRISTIAN VIEW
Explain softly what Christians believe and why it matters.

SECTION 4 — AGREEMENT
Explain what Christians and non-Christians may both agree on.

SECTION 5 — DIFFERENCE
Explain kindly how their worldviews may differ.

SECTION 6 — PRACTICE
Ask 2–3 reflection questions with short example answers as sentences.
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
