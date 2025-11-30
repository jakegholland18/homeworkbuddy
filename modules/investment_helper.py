# modules/investment_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import format_answer


# ------------------------------------------------------------
# Detect Christian-oriented investing questions
# ------------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "biblical", "god", "jesus", "bible", "faith",
        "christian perspective", "christian view",
        "what does the bible say", "how does this relate to god"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# ------------------------------------------------------------
# Universal extractor (same as all helpers)
# ------------------------------------------------------------
def extract_sections(ai_text: str):
    def extract(label):
        if label not in ai_text:
            return "Not available."

        start = ai_text.find(label) + len(label)
        end = len(ai_text)

        for nxt in [
            "SECTION 1", "SECTION 2", "SECTION 3",
            "SECTION 4", "SECTION 5", "SECTION 6"
        ]:
            pos = ai_text.find(nxt, start)
            if pos != -1 and pos < end:
                end = pos

        return ai_text[start:end].strip()

    return {
        "overview": extract("SECTION 1"),
        "key_facts": extract("SECTION 2"),
        "christian_view": extract("SECTION 3"),
        "agreement": extract("SECTION 4"),
        "difference": extract("SECTION 5"),
        "practice": extract("SECTION 6"),
    }


# ------------------------------------------------------------
# Build investing prompt — standard version
# ------------------------------------------------------------
def build_investing_prompt(topic: str, grade: str):
    return f"""
You are a gentle investing tutor for a grade {grade} student.

The student asked:
"{topic}"

Use SIX warm, child-friendly sections.

SECTION 1 — OVERVIEW
Explain the idea in simple, calm sentences.

SECTION 2 — KEY FACTS
Explain basic ideas (saving, risk, long-term thinking, value).
Slow and simple.

SECTION 3 — CHRISTIAN VIEW
Explain stewardship, avoiding greed, wise choices.
If not a Christian question, simply mention that some Christians
see money management as responsibility and generosity.

SECTION 4 — AGREEMENT
Explain what all people agree on: saving, planning, being careful.

SECTION 5 — DIFFERENCE
Explain gently how Christian motivation may differ
from a “money-first” view.

SECTION 6 — PRACTICE
Ask 2–3 tiny reflection questions with example answers.

Tone: slow, warm, kid-friendly, not technical.
"""


# ------------------------------------------------------------
# Build Christian prompt
# ------------------------------------------------------------
def build_christian_investing_prompt(topic: str, grade: str):
    return f"""
The student asked this investing question from a Christian perspective:

"{topic}"

Use SIX gentle sections.

SECTION 1 — OVERVIEW
Explain the idea slowly.

SECTION 2 — KEY FACTS
Explain the basic financial ideas.

SECTION 3 — CHRISTIAN VIEW
Explain stewardship, responsibility, generosity.

SECTION 4 — AGREEMENT
Explain what all worldviews agree on.

SECTION 5 — DIFFERENCE
Explain gently how motivation differs.

SECTION 6 — PRACTICE
Ask 2–3 tiny reflection questions.

Tone: calm, warm, non-technical.
"""


# ------------------------------------------------------------
# MAIN PUBLIC FUNCTION — explain investing
# ------------------------------------------------------------
def explain_investing(topic: str, grade_level="8", character="everly"):

    if is_christian_question(topic):
        prompt = build_christian_investing_prompt(topic, grade_level)
    else:
        prompt = build_investing_prompt(topic, grade_level)

    prompt = apply_personality(character, prompt)

    raw = study_buddy_ai(prompt, grade_level, character)

    sections = extract_sections(raw)
    return format_answer(**sections)


# ------------------------------------------------------------
# GENERAL INVESTING QUESTION
# ------------------------------------------------------------
def investment_question(question: str, grade_level="8", character="everly"):

    prompt = build_investing_prompt(question, grade_level)
    prompt = apply_personality(character, prompt)

    raw = study_buddy_ai(prompt, grade_level, character)

    sections = extract_sections(raw)
    return format_answer(**sections)


# ------------------------------------------------------------
# INVESTING QUIZ (still six sections)
# ------------------------------------------------------------
def investment_quiz(topic: str, grade_level="8", character="everly"):

    prompt = f"""
Create a gentle investing quiz for grade {grade_level}.

Topic: "{topic}"

Use SIX SECTIONS:

SECTION 1 — OVERVIEW
SECTION 2 — KEY FACTS
SECTION 3 — CHRISTIAN VIEW
SECTION 4 — AGREEMENT
SECTION 5 — DIFFERENCE
SECTION 6 — PRACTICE

Make it calm, warm, slow-paced.
"""

    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    sections = extract_sections(raw)
    return format_answer(**sections)


