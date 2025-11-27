# modules/study_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


def build_quiz_prompt(topic: str, grade_level: str):
    """
    Builds a calm, conversational quiz prompt.
    No lists, no markdown, no headings.
    Just natural, friendly quiz questions.
    """

    return f"""
The student wants a study quiz about the topic "{topic}" 
at a grade {grade_level} level.

Speak in a warm, gentle, conversational tone. 
Do not use lists, bullets, headings, dashes, numbering, or formatting.
Just write naturally, as though you are talking to the student.

Create a simple quiz that feels like a friendly tutor speaking.
Include short questions they can answer on their own.
After a pause in the conversation, gently give the answers.
Make everything feel soft and encouraging.
"""


def build_flashcard_prompt(topic: str, grade_level: str):
    """
    Builds flashcards in conversational form.
    No lists or structured formatting.
    Just a natural back-and-forth flashcard style.
    """

    return f"""
The student wants flashcards to review the topic "{topic}" 
for a grade {grade_level} level.

Speak as though you are sitting with the student,
showing them one flashcard at a time.
Do not use lists, numbers, bullets, or headings of any kind.

Make each flashcard feel like a simple question and answer,
spoken naturally and gently, as if in a warm conversation.
"""


def generate_quiz(topic: str, grade_level="8", character=None):
    """
    Creates a gentle, conversational quiz.
    Personality-aware.
    """

    if character is None:
        character = "valor_strike"

    base_prompt = build_quiz_prompt(topic, grade_level)
    enriched_prompt = apply_personality(character, base_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


def flashcards(topic: str, grade_level="8", character=None):
    """
    Creates conversational flashcards.
    Personality-aware.
    """

    if character is None:
        character = "valor_strike"

    base_prompt = build_flashcard_prompt(topic, grade_level)
    enriched_prompt = apply_personality(character, base_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)

