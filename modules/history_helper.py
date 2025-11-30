# modules/history_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


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
# Build prompt for non-Christian history questions
# ------------------------------------------------------------
def build_history_prompt(topic: str, grade: str):
    return f"""
You are a gentle history tutor for a grade {grade} student.

The student asked about:
\"{topic}\"

Explain it using the **six-section Homework Buddy format**.

SECTION 1 — OVERVIEW
Give a calm 2–3 sentence explanation of the topic.

SECTION 2 — KEY FACTS
List the basic facts: what happened, who was involved,
why it matters. Use dash bullets ("- ").

SECTION 3 — CHRISTIAN VIEW
Explain softly how many Christians look at history:
choices, character, learning moral lessons.
If Christianity is not part of the event,
explain Christians still learn principles from history.

SECTION 4 — AGREEMENT
List 2–4 things people of all worldviews agree on
(cause/effect, human behavior, evidence). Use dash bullets.

SECTION 5 — DIFFERENCE
List gentle worldview differences about meaning,
purpose, or interpretation. Use dash bullets.

SECTION 6 — PRACTICE
Give 2–3 reflection questions with short example answers.
Each question must begin with "- ".
"""


# ------------------------------------------------------------
# Build prompt for Christian-directed questions
# ------------------------------------------------------------
def build_christian_history_prompt(topic: str, grade: str):
    return f"""
The student asked this history question from a Christian perspective:

\"{topic}\"

Answer using the **six-section Homework Buddy format**.

SECTION 1 — OVERVIEW
Explain the topic slowly and clearly.

SECTION 2 — KEY FACTS
List the simple historical facts using dash bullets.

SECTION 3 — CHRISTIAN VIEW
Explain softly how Christians understand this event:
choices, character, moral lessons, trusting God’s plan.

SECTION 4 — AGREEMENT
List 2–4 things people of any worldview agree on.
Use dash bullets.

SECTION 5 — DIFFERENCE
List gentle differences in how Christian and secular views
interpret meaning or lessons. Use dash bullets.

SECTION 6 — PRACTICE
Give 2–3 reflection questions with short example answers.
Each must begin with "- ".
"""


# ------------------------------------------------------------
# MAIN HISTORY EXPLAINER
# ------------------------------------------------------------
def explain_history(topic: str, grade_level="8", character="everly"):

    if is_christian_question(topic):
        base_prompt = build_christian_history_prompt(topic, grade_level)
    else:
        base_prompt = build_history_prompt(topic, grade_level)

    prompt = apply_personality(character, base_prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    sections = parse_into_sections(raw)

    return format_answer(**sections)


# ------------------------------------------------------------
# GENERAL HISTORY QUESTION
# ------------------------------------------------------------
def answer_history_question(question: str, grade_level="8", character="everly"):

    base_prompt = build_history_prompt(question, grade_level)
    prompt = apply_personality(character, base_prompt)

    raw = study_buddy_ai(prompt, grade_level, character)
    sections = parse_into_sections(raw)

    return format_answer(**sections)


# ------------------------------------------------------------
# HISTORY QUIZ
# ------------------------------------------------------------
def generate_history_quiz(topic: str, grade_level="8", character="everly"):

    prompt = f"""
Create a gentle history quiz for a grade {grade_level} student.

Topic: \"{topic}\"

Use the **six-section Homework Buddy format**.

SECTION 1 — OVERVIEW
A soft introduction to what the quiz is about.

SECTION 2 — KEY FACTS
List the main historical points using dash bullets.

SECTION 3 — CHRISTIAN VIEW
Explain softly what moral lessons Christians draw from history.

SECTION 4 — AGREEMENT
List 2–4 shared ideas all worldviews accept. Use dash bullets.

SECTION 5 — DIFFERENCE
List respectful worldview differences in interpretation. Use dash bullets.

SECTION 6 — PRACTICE
Write a few quiz-style questions with short example answers.
Each must start with "- ".
"""

    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    sections = parse_into_sections(raw)

    return format_answer(**sections)
