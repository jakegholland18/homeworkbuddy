# modules/money_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -----------------------------------------------------------
# Build prompts for money topics (budgeting, saving, credit)
# -----------------------------------------------------------
def build_money_topic_prompt(topic: str, grade_level: str):
    """
    Builds a gentle conversational money lesson prompt.
    No lists, no markdown, no formatting.
    Just warm, natural explanations.
    """

    return f"""
The student wants to learn about the money topic "{topic}" 
for a grade {grade_level} level.

Explain this in a calm, natural, conversational tone.
Avoid lists, bullet points, headings, or dramatic language.
Speak as if you are sitting beside the student, guiding them kindly.

You may cover ideas such as budgeting, saving, income, taxes, interest,
credit, spending, needs versus wants, financial decision making, 
and any other age-appropriate money concepts.

Keep everything clear, warm, simple, and friendly.
"""


# -----------------------------------------------------------
# Build prompts for accounting problem solving
# -----------------------------------------------------------
def build_accounting_problem_prompt(problem: str, grade_level: str):
    """
    Builds a conversational accounting problem-solving prompt.
    Includes step-by-step thinking, but no structured lists.
    """

    return f"""
The student needs help with an accounting problem:

"{problem}"

Explain the solution in a conversational, warm, encouraging tone
appropriate for a grade {grade_level} student.

Walk through your thought process naturally without using bullets,
lists, headings, or numbered steps. Just talk through it gently,
explaining how accounting ideas like debits, credits, assets, 
liabilities, expenses, and revenues work.

End with a simple recap in plain conversational language.
"""


# -----------------------------------------------------------
# Build money quiz prompt
# -----------------------------------------------------------
def build_money_quiz_prompt(topic: str, grade_level: str):
    """
    Creates a soft conversational money quiz.
    No lists or formal structure.
    """

    return f"""
Create a gentle, friendly quiz to help the student practice 
the topic "{topic}" at a grade {grade_level} level.

Speak as though you are sitting with the student.
Do not use lists, numbering, or formatting.
Ask simple questions in a natural conversational style,
pausing between each one as if waiting for them to think.
After a short break in the conversation, offer the answers 
in the same calm tone.
"""


# -----------------------------------------------------------
# Public functions sent to the AI
# -----------------------------------------------------------
def explain_money(topic: str, grade_level="8", character=None):
    """Teaches money topics in a warm, personality-aware tone."""

    if character is None:
        character = "valor_strike"

    base_prompt = build_money_topic_prompt(topic, grade_level)
    enriched_prompt = apply_personality(character, base_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


def solve_accounting_problem(problem: str, grade_level="8", character=None):
    """Solves accounting problems with natural conversation."""

    if character is None:
        character = "valor_strike"

    base_prompt = build_accounting_problem_prompt(problem, grade_level)
    enriched_prompt = apply_personality(character, base_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


def accounting_quiz(topic: str, grade_level="8", character=None):
    """Creates a conversational money/accounting quiz."""

    if character is None:
        character = "valor_strike"

    base_prompt = build_money_quiz_prompt(topic, grade_level)
    enriched_prompt = apply_personality(character, base_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


