# modules/money_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -----------------------------------------------------------
# SOCRATIC TUTOR LAYER
# -----------------------------------------------------------
def socratic_layer(base_explanation: str, question: str, grade_level: str):
    """
    Wraps the explanation in guided learning:
    restate → hint → guiding question → small nudge → full explanation.
    """

    return f"""
A student asked: "{question}"

Begin by helping the student think before giving the full answer.

First, restate the question or topic in gentle, kid-friendly language.

Next, offer a simple hint that points them toward understanding
without giving the full explanation yet.

Then, ask a guiding question that helps them think about real-life money
situations or what they already know about saving, spending, or planning.

After that, give a small nudge—just enough to help if they are stuck,
but still leaving space for their own thinking.

Only after these steps, move into the full explanation below.

Full Explanation:
{base_explanation}

End with a warm, encouraging summary written for a grade {grade_level} student,
letting them know they are doing well and money skills grow over time.
"""


# -----------------------------------------------------------
# Build prompts for money topics (budgeting, saving, credit)
# -----------------------------------------------------------
def build_money_topic_prompt(topic: str, grade_level: str):
    return f"""
The student wants to learn about the money topic "{topic}" 
for a grade {grade_level} level.

Explain this in a calm, natural, conversational tone.
Avoid lists, headings, or dramatic language.
Speak as if you are sitting beside the student.

You may cover ideas such as budgeting, saving, income, interest,
credit, spending choices, needs versus wants, and other simple money ideas.

Keep everything warm, clear, and friendly.
"""


# -----------------------------------------------------------
# Build prompts for accounting problem solving
# -----------------------------------------------------------
def build_accounting_problem_prompt(problem: str, grade_level: str):
    return f"""
The student needs help with an accounting problem:

"{problem}"

Solve this in a calm, conversational tone.
Walk through your thinking naturally without using bullets or lists.

Gently explain ideas like debits, credits, assets, liabilities,
expenses, and revenues in simple language a grade {grade_level} student
can follow.

End with a short recap in natural, friendly wording.
"""


# -----------------------------------------------------------
# Build money quiz prompt
# -----------------------------------------------------------
def build_money_quiz_prompt(topic: str, grade_level: str):
    return f"""
Create a gentle quiz about the topic "{topic}" 
for a grade {grade_level} student.

Speak warmly as if sitting beside them.
Do not use numbering, bullets, or formatting.
Ask simple practice questions in natural conversation,
and after a short pause, give the answers in the same calm tone.
"""


# -----------------------------------------------------------
# Public Functions (Socratic + Personality)
# -----------------------------------------------------------
def explain_money(topic: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    base_prompt = build_money_topic_prompt(topic, grade_level)

    # wrap in Socratic method
    guided_prompt = socratic_layer(base_prompt, topic, grade_level)

    # add character personality
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


def solve_accounting_problem(problem: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    base_prompt = build_accounting_problem_prompt(problem, grade_level)

    # Socratic method applied
    guided_prompt = socratic_layer(base_prompt, problem, grade_level)

    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


def accounting_quiz(topic: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    base_prompt = build_money_quiz_prompt(topic, grade_level)

    # same Socratic wrapper — even quizzes start with “think first”
    guided_prompt = socratic_layer(base_prompt, topic, grade_level)

    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)



