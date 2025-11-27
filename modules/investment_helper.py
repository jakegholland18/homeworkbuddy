# modules/investment_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -----------------------------------------------------------
# Build prompt for general investing lessons
# -----------------------------------------------------------
def build_investing_lesson_prompt(topic: str, grade_level: str):
    """
    Creates a gentle, conversational prompt for explaining investing topics.
    No lists, no formatting, just natural, warm conversation.
    """

    return f"""
The student wants to learn about the investment topic "{topic}" 
at a grade {grade_level} level.

Teach in a calm, warm, conversational tone, as though you are
sitting beside the student and helping them understand.
Avoid lists, headings, bullet points, or dramatic language.

Explain only age-appropriate ideas such as stocks, bonds, savings,
risk, interest, long-term thinking, diversification, retirement basics,
compound growth, simple markets, or how money can grow slowly over time.

Keep everything simple, kind, and encouraging so it feels like
a real conversation with a gentle tutor.
"""


# -----------------------------------------------------------
# Build prompt for investment quizzes
# -----------------------------------------------------------
def build_investing_quiz_prompt(topic: str, grade_level: str):
    """
    Creates a conversational investing quiz.
    No lists or structure — just soft spoken questions.
    """

    return f"""
Create a gentle practice quiz for the investment topic "{topic}"
for a grade {grade_level} student.

Speak like a warm tutor having a conversation.
Do not use bullet points, numbering, or headings.
Ask a few simple questions one at a time, leaving space for the student
to think about their answers.

After a short pause in the conversation, offer the answers in the same
natural and friendly tone.
"""


# -----------------------------------------------------------
# Build prompt for investment scenarios (optional practice)
# -----------------------------------------------------------
def build_scenario_prompt(topic: str, grade_level: str):
    """
    Builds a conversational scenario that helps students understand
    investing by imagining real-life situations.
    """

    return f"""
Create a simple imagined scenario that helps a grade {grade_level} student 
understand the investing topic "{topic}".

Speak gently and conversationally.
Guide them through the situation slowly, as if the two of you 
are thinking through the decisions together.

Avoid lists, formatting, or dramatic language. 
Make everything feel soft, practical, and easy to follow.
"""


# -----------------------------------------------------------
# Public functions
# -----------------------------------------------------------
def explain_investing(topic: str, grade_level="8", character=None):
    """Explains investing concepts in a warm, personality-aware tone."""

    if character is None:
        character = "valor_strike"

    base_prompt = build_investing_lesson_prompt(topic, grade_level)
    enriched_prompt = apply_personality(character, base_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


def investment_quiz(topic: str, grade_level="8", character=None):
    """Creates a soft conversational quiz about investing."""

    if character is None:
        character = "valor_strike"

    base_prompt = build_investing_quiz_prompt(topic, grade_level)
    enriched_prompt = apply_personality(character, base_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


def investment_scenario(topic: str, grade_level="8", character=None):
    """Creates a real-life example scenario in a gentle tone."""

    if character is None:
        character = "valor_strike"

    base_prompt = build_scenario_prompt(topic, grade_level)
    enriched_prompt = apply_personality(character, base_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


