# modules/study_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -----------------------------------------------------------
# SOCRATIC TUTOR LAYER
# -----------------------------------------------------------
def socratic_layer(base_explanation: str, topic: str, grade_level: str):
    """
    Wraps any study material in a Socratic-style guided conversation.
    """

    return f"""
A student wants help studying the topic "{topic}".

Before giving the full quiz or flashcards, help them think on their own for a moment.

Begin by gently restating what the topic is about in kid-friendly language,
so the student feels understood and knows you're on the same page.

Then offer a small hint about the kinds of ideas this topic involves.
Make the hint simple, like pointing them toward the right corner of the idea.

After that, ask a guiding question. 
This question should get them thinking without pressure,
like a gentle nudge to explore the idea in their own mind.

Then offer a tiny bit of help, just enough so they don’t feel stuck,
but still not revealing the actual content of the quiz or flashcards.

Once you have guided their mind in these steps, 
transition softly into the full explanation or practice below.

Full Study Content:
{base_explanation}

End with a short, warm summary written at a grade {grade_level} level 
that reassures the student that curiosity and practice will help them grow.
"""


# -----------------------------------------------------------
# QUIZ PROMPT
# -----------------------------------------------------------
def build_quiz_prompt(topic: str, grade_level: str):
    """
    Builds a calm, conversational quiz prompt.
    No lists, numbers, or formatting.
    """

    return f"""
The student wants a study quiz about the topic "{topic}"
at a grade {grade_level} level.

Teach in a warm, gentle, conversational voice.
Ask a few short quiz questions the way a friendly tutor might ask them
while sitting with the student.

Leave a soft pause between each question so the student can think.
Then, after a moment in the conversation, offer the answers
in the same natural, spoken tone.

Avoid lists, bullets, numbering, or headings.
Just talk naturally.
"""


# -----------------------------------------------------------
# FLASHCARDS PROMPT
# -----------------------------------------------------------
def build_flashcard_prompt(topic: str, grade_level: str):
    """
    Builds conversational flashcards with NO structured formatting.
    """

    return f"""
The student wants flashcards to review the topic "{topic}" 
at a grade {grade_level} level.

Speak as though you are holding real cards
and showing them one at a time in a calm, friendly way.

Each flashcard should feel like a simple question spoken out loud,
followed gently by the answer.

Avoid lists, numbers, bullets, headings, or formatting.
Just speak naturally as though sitting beside the student.
"""


# -----------------------------------------------------------
# PUBLIC FUNCTIONS — WITH SOCRATIC TUTOR
# -----------------------------------------------------------
def generate_quiz(topic: str, grade_level="8", character=None):
    """
    Creates a gentle Socratic-style quiz with personality layer.
    """

    if character is None:
        character = "valor_strike"

    # Build base content
    base_prompt = build_quiz_prompt(topic, grade_level)

    # Wrap in Socratic tutor
    guided_prompt = socratic_layer(base_prompt, topic, grade_level)

    # Add character personality
    enriched_prompt = apply_personality(character, guided_prompt)

    # Send to AI
    return study_buddy_ai(enriched_prompt, grade_level, character)


def flashcards(topic: str, grade_level="8", character=None):
    """
    Creates Socratic-style flashcards with personality layer.
    """

    if character is None:
        character = "valor_strike"

    base_prompt = build_flashcard_prompt(topic, grade_level)

    guided_prompt = socratic_layer(base_prompt, topic, grade_level)

    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


