# modules/question_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -------------------------------------------------------
# Detect if student asked for Christianity link
# -------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "christianity", "jesus", "god", "faith",
        "biblical", "bible", "how does this relate to god",
        "from a christian perspective"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -------------------------------------------------------
# SOCRATIC TEACHING LAYER
# -------------------------------------------------------
def socratic_layer(base_explanation: str, question: str, grade_level: str):
    """
    Wraps any explanation inside Socratic guidance:
    restate → hint → guiding question → small nudge → full explanation.
    """

    return f"""
A student asked: "{question}"

Begin by helping the student think before offering the full explanation.

First, restate the question in gentle, kid-friendly language so they feel understood.

Next, give a soft hint that points in the right direction without giving away the answer.

Then, ask a guiding question that helps them think about what they already know 
or have seen in school, in life, or in their own experiences.

After that, offer a small nudge that helps them make progress if they feel stuck,
but still avoids revealing the complete explanation too early.

Only then should you slowly transition into the full explanation below.

Full Explanation:
{base_explanation}

End with a warm, encouraging summary written at a grade {grade_level} level,
letting the student know that asking questions is a great way to grow.
"""


# -------------------------------------------------------
# Build Christian worldview explanation
# -------------------------------------------------------
def build_christian_prompt(question: str, grade_level: str):
    return f"""
The student asked this question from a Christian perspective:

"{question}"

Explain gently how many Christians think about this topic.
Use a warm, conversational tone suitable for grade {grade_level}.
Avoid dramatic language or pressure.

If Scripture is relevant, mention it softly.
If the connection is theological or historical, explain it calmly.

Do not claim the Bible teaches modern academic concepts unless accurate.
Let the tone feel steady, kind, and thoughtful.
"""


# -------------------------------------------------------
# Build general question explanation
# -------------------------------------------------------
def build_general_prompt(question: str, grade_level: str):
    return f"""
The student asked this question:

"{question}"

Explain the answer in a warm, calm, conversational tone.
Speak as if sitting beside the student.
Use natural language for a grade {grade_level} learner.

Keep everything simple and easy to understand
without using lists, headings, or dramatic descriptions.

Help them feel confident that they can understand it step by step.
"""


# -------------------------------------------------------
# Main public function (Socratic + Personality)
# -------------------------------------------------------
def answer_question(question: str, grade_level="8", character=None):
    """
    Provides a warm, conversational answer to ANY question.
    Adds Socratic guidance + character personality.
    """

    if character is None:
        character = "valor_strike"

    # Choose base prompt
    if is_christian_question(question):
        base_prompt = build_christian_prompt(question, grade_level)
    else:
        base_prompt = build_general_prompt(question, grade_level)

    # Add Socratic layer
    guided_prompt = socratic_layer(base_prompt, question, grade_level)

    # Add character personality
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)
