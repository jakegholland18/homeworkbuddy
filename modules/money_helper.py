# modules/money_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import format_answer


# ------------------------------------------------------------
# Detect Christian-oriented money questions
# ------------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "biblical", "god", "jesus", "bible", "faith",
        "christian perspective", "christian worldview",
        "what does the bible say", "how does this relate to god"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# ------------------------------------------------------------
# Universal extractor (same across all helpers)
# ------------------------------------------------------------
def extract_sections(ai_text: str):
    def extract(label: str):
        if label not in ai_text:
            return "Not available."

        start = ai_text.find(label) + len(label)
        end = len(ai_text)

        # Detect next section label to stop extraction
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
# Base money explanation prompt
# ------------------------------------------------------------
def build_money_prompt(topic: str, grade: str):
    return f"""
You are a gentle money tutor helping a grade {grade} student.

The student asked:
"{topic}"

Answer using SIX child-friendly sections.

SECTION 1 — OVERVIEW
Explain the money idea in very simple language.

SECTION 2 — KEY FACTS
Teach basic ideas: saving, spending, earning, planning,
needs vs wants, value, and simple budgeting.

SECTION 3 — CHRISTIAN VIEW
Explain softly how Christians may think about money:
stewardship, responsibility, generosity, and avoiding greed.
If not a Christian topic, state this gently but still mention
how some Christians see money as something to use wisely.

SECTION 4 — AGREEMENT
Explain what nearly everyone agrees on:
saving helps the future, planning prevents problems, spending wisely matters.

SECTION 5 — DIFFERENCE
Explain kindly how motivation might differ between Christian and secular views.

SECTION 6 — PRACTICE
Ask 2–3 small reflection questions with simple sample answers.

Tone must be soft, slow, and kid-friendly.
"""


# ------------------------------------------------------------
# Christian-specific version
# ------------------------------------------------------------
def build_christian_money_prompt(topic: str, grade: str):
    return f"""
The student asked about money from a Christian perspective:

"{topic}"

Use SIX gentle sections.

SECTION 1 — OVERVIEW
Explain the idea simply.

SECTION 2 — KEY FACTS
Teach the basic money concepts.

SECTION 3 — CHRISTIAN VIEW
Explain stewardship, generosity, responsibility,
and the idea of using resources wisely.

SECTION 4 — AGREEMENT
Explain what all worldviews share in common.

SECTION 5 — DIFFERENCE
Explain in a kind way how motivation or values may differ.

SECTION 6 — PRACTICE
Ask 2–3 tiny reflection questions.

Tone must be soft, warm, and calm.
"""


# ------------------------------------------------------------
# MAIN FUNCTION — explain money
# ------------------------------------------------------------
def explain_money(topic: str, grade_level="8", character="everly"):

    if is_christian_question(topic):
        prompt = build_christian_money_prompt(topic, grade_level)
    else:
        prompt = build_money_prompt(topic, grade_level)

    prompt = apply_personality(character, prompt)

    raw = study_buddy_ai(prompt, grade_level, character)

    sections = extract_sections(raw)
    return format_answer(**sections)


# ------------------------------------------------------------
# GENERAL MONEY QUESTION
# ------------------------------------------------------------
def money_question(question: str, grade_level="8", character="everly"):

    prompt = build_money_prompt(question, grade_level)
    prompt = apply_personality(character, prompt)

    raw = study_buddy_ai(prompt, grade_level, character)

    sections = extract_sections(raw)
    return format_answer(**sections)


# ------------------------------------------------------------
# MONEY QUIZ
# ------------------------------------------------------------
def money_quiz(topic: str, grade_level="8", character="everly"):

    prompt = f"""
Create a gentle money quiz for grade {grade_level}.

Topic: "{topic}"

Use SIX SECTIONS:

SECTION 1 — OVERVIEW  
SECTION 2 — KEY FACTS  
SECTION 3 — CHRISTIAN VIEW  
SECTION 4 — AGREEMENT  
SECTION 5 — DIFFERENCE  
SECTION 6 — PRACTICE  

Tone must be slow, kind, and easy for kids.
"""

    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    sections = extract_sections(raw)
    return format_answer(**sections)






