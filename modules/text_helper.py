# modules/text_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


# ------------------------------------------------------------
# Detect Christian-oriented reading/literature questions
# ------------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "biblical", "god", "jesus", "faith",
        "christian worldview", "christian perspective",
        "how does this relate to god",
        "how does this relate to christianity",
    ]
    return any(k.lower() in text.lower() for k in keywords)


# ------------------------------------------------------------
# Standard reading / literature prompt
# ------------------------------------------------------------
def build_text_prompt(question: str, grade: str):
    return f"""
You are a gentle reading and literature tutor for a grade {grade} student.

The student asked:
"{question}"

Answer using all SIX labeled sections. NO bullet points.

SECTION 1 — OVERVIEW
Explain the reading or literary idea in simple, calm sentences.

SECTION 2 — KEY FACTS
Teach the important ideas: theme, setting, characters,
conflict, author's purpose, tone, or structure (depending on the topic).
Write 3–5 short sentences.

SECTION 3 — CHRISTIAN VIEW
Explain softly how Christians might think about stories:
truth, moral lessons, character, integrity, and meaning.
If the story is not Christian, simply state this gently.

SECTION 4 — AGREEMENT
Explain what almost everyone agrees on in reading:
how to find meaning, how to identify themes, how to understand characters.

SECTION 5 — DIFFERENCE
Explain kindly how Christian and secular interpretations
might emphasize different values or lessons.

SECTION 6 — PRACTICE
Give 2–3 tiny reading practice questions with short example answers.
Use simple sentences, no bullets.

Tone must be warm, gentle, and child-friendly.
"""


# ------------------------------------------------------------
# Christian-specific version of reading prompt
# ------------------------------------------------------------
def build_christian_text_prompt(question: str, grade: str):
    return f"""
The student asked a reading/literature question from a Christian perspective:

"{question}"

Use all SIX labeled sections. NO bullet points.

SECTION 1 — OVERVIEW
Explain the reading idea simply.

SECTION 2 — KEY FACTS
Teach the key reading skills or concepts gently.

SECTION 3 — CHRISTIAN VIEW
Explain how Christians may interpret stories through ideas such as:
virtue, morality, character, redemption, compassion, or truth.

SECTION 4 — AGREEMENT
Explain what all worldviews agree on when analyzing stories.

SECTION 5 — DIFFERENCE
Explain kindly how Christian and secular viewpoints may highlight
different themes or values.

SECTION 6 — PRACTICE
Give 2–3 tiny practice questions with short example answers.

Tone must stay soft, warm, and appropriate for kids.
"""


# ------------------------------------------------------------
# MAIN TEXT EXPLAINER
# ------------------------------------------------------------
def explain_text(topic: str, grade_level="8", character="everly"):

    if is_christian_question(topic):
        prompt = build_christian_text_prompt(topic, grade_level)
    else:
        prompt = build_text_prompt(topic, grade_level)

    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    sections = parse_into_sections(raw)

    # Prepare formatted final output
    return format_answer(
        overview=sections.get("overview", "").strip(),
        key_facts=sections.get("key_facts", []),
        christian_view=sections.get("christian_view", "").strip(),
        agreement=sections.get("agreement", []),
        difference=sections.get("difference", []),
        practice=sections.get("practice", []),
        raw_text=raw
    )


# ------------------------------------------------------------
# GENERAL READING QUESTION
# ------------------------------------------------------------
def reading_question(question: str, grade_level="8", character="everly"):

    prompt = build_text_prompt(question, grade_level)
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


# ------------------------------------------------------------
# TEXT / READING QUIZ
# ------------------------------------------------------------
def text_quiz(topic: str, grade_level="8", character="everly"):

    prompt = f"""
Create a gentle reading/literature quiz for a grade {grade_level} student.

Topic: "{topic}"

Use all SIX labeled sections:
SECTION 1 — OVERVIEW
SECTION 2 — KEY FACTS
SECTION 3 — CHRISTIAN VIEW
SECTION 4 — AGREEMENT
SECTION 5 — DIFFERENCE
SECTION 6 — PRACTICE

Tone must stay slow, warm, and kid-friendly. NO bullet points.
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
