# modules/investment_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -----------------------------------------------------------
# SOCRATIC TUTOR LAYER (used for all investing answers)
# -----------------------------------------------------------
def socratic_layer(base_explanation: str, question: str, grade_level: str):
    """
    Wraps the final explanation in guided Socratic teaching:
    gentle rephrase → hint → guiding question → soft nudge → full answer.
    """

    return f"""
A student asked about: "{question}"

Begin by helping the student think without giving the full answer right away.

First, restate what the question is really asking using gentle, kid-friendly wording.

Next, offer one helpful hint that points them in the right direction.

Then, ask a guiding question that encourages the student to think about how money,
savings, or investing might work in everyday life.

After that, give a small nudge that helps them move closer to the idea,
but still avoid giving away the full explanation.

Only after these steps should you transition into the full investing explanation below.

Full Explanation:
{base_explanation}

End with a warm, encouraging summary written for a grade {grade_level} student,
reminding them that learning how money grows takes patience and curiosity.
"""


# -----------------------------------------------------------
# Build prompt for general investing lessons
# -----------------------------------------------------------
def build_investing_lesson_prompt(topic: str, grade_level: str):
    """
    Creates a gentle, conversational prompt for explaining investing topics.
    No lists or formatting — just soft conversation.
    """

    return f"""
The student wants to learn about the investment topic "{topic}"
at a grade {grade_level} level.

Teach in a calm, warm, conversational tone, as though you are sitting beside them.
Avoid lists, headings, or dramatic language.

Explain age-appropriate ideas such as saving, interest, compound growth,
risk, simple stocks and bonds, long-term thinking, budgeting, or diversification.

Keep everything gentle, supportive, and easy to understand.
"""


# -----------------------------------------------------------
# Build prompt for investment quizzes (conversational)
# -----------------------------------------------------------
def build_investing_quiz_prompt(topic: str, grade_level: str):
    """
    Creates a conversational investing quiz with Socratic feel.
    No lists — just spoken-style questions.
    """

    return f"""
Create a gentle practice quiz about the investing topic "{topic}"
for a grade {grade_level} student.

Ask a few soft, thoughtful questions one at a time,
leaving space for the student to think.

After a short pause in the conversation,
offer the answers in the same warm tone.
"""


# -----------------------------------------------------------
# Build prompt for investment scenarios
# -----------------------------------------------------------
def build_scenario_prompt(topic: str, grade_level: str):
    """
    Builds a conversational real-life example to explain investing.
    """

    return f"""
Create a simple imagined scenario that helps a grade {grade_level} student
understand the investing topic "{topic}".

Speak in a slow, gentle, conversational style.
Guide them through the situation step by step as if you are thinking together.

Avoid lists and dramatic language.
Make the situation peaceful, practical, and easy to picture.
"""


# -----------------------------------------------------------
# Public functions (Socratic + Personality)
# -----------------------------------------------------------
def explain_investing(topic: str, grade_level="8", character=None):
    """Explains investing concepts in a warm, personality-aware Socratic tone."""

    if character is None:
        character = "valor_strike"

    base_prompt = build_investing_lesson_prompt(topic, grade_level)

    # Add Socratic step-by-step teaching
    guided_prompt = socratic_layer(base_prompt, topic, grade_level)

    # Personality layer
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


def investment_quiz(topic: str, grade_level="8", character=None):
    """Creates a soft conversational Socratic investing quiz."""

    if character is None:
        character = "valor_strike"

    base_prompt = build_investing_quiz_prompt(topic, grade_level)
    guided_prompt = socratic_layer(base_prompt, topic, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


def investment_scenario(topic: str, grade_level="8", character=None):
    """Creates an investing scenario in a gentle Socratic tone."""

    if character is None:
        character = "valor_strike"

    base_prompt = build_scenario_prompt(topic, grade_level)
    guided_prompt = socratic_layer(base_prompt, topic, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)



