# modules/question_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -------------------------------------------------------
# Detect if student asked for Christianity link
# -------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "Christian", "Christianity", "Jesus", "God", "faith",
        "biblical", "Bible", "how does this relate to God",
        "from a Christian perspective"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -------------------------------------------------------
# Build Christian worldview explanation
# -------------------------------------------------------
def build_christian_prompt(question: str, grade_level: str):
    """
    Creates a gentle Christian worldview response.
    Calm, warm, and thoughtful.
    """

    return f"""
The student asked this question from a Christian perspective:

"{question}"

Explain the topic in a gentle, conversational way.
Show how many Christians think about this topic,
and how Scripture or Christian teaching may relate to it,
but do not claim that the Bible directly teaches modern ideas
unless the connection is historically or theologically accurate.

Avoid lists, headings, or dramatic tone.
Speak in a warm, calm voice appropriate for a grade {grade_level} student.
Encourage thoughtful reflection and honest curiosity.
"""


# -------------------------------------------------------
# Build regular general question explanation
# -------------------------------------------------------
def build_general_prompt(question: str, grade_level: str):
    """
    Creates a natural explanation for ANY general question:
school topics, life advice, reasoning, curiosity, etc.
    """

    return f"""
The student asked this question:

"{question}"

Explain the answer in a warm, calm, conversational tone.
Imagine sitting beside them and talking through the idea gently.
Speak at a grade {grade_level} level.

Avoid hype, dramatic language, or strong character themes.
Avoid lists and headings.
Keep the explanation simple and natural,
helping them understand the idea step by step.

End with a short, encouraging thought.
"""


# -------------------------------------------------------
# Main public function
# -------------------------------------------------------
def answer_question(question: str, grade_level="8", character=None):
    """
    Provides a warm, conversational answer to ANY question.
    Character voice is subtle and gentle.
    Christian worldview appears ONLY if specifically requested.
    """

    if character is None:
        character = "valor_strike"

    if is_christian_question(question):
        base_prompt = build_christian_prompt(question, grade_level)
    else:
        base_prompt = build_general_prompt(question, grade_level)

    enriched_prompt = apply_personality(character, base_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)

