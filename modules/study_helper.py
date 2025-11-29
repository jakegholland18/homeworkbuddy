# modules/study_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


# -----------------------------------------------------------
# Socratic Tutor Layer
# -----------------------------------------------------------
def socratic_layer(topic: str, grade_level: str):
    """
    Adds a gentle pre-explanation to help students think before giving the final
    6-section structured answer.
    """
    return f"""
The student wants help studying this topic:

\"{topic}\"

Before giving the final 6-section answer:

1. Restate what they are trying to study in very simple words.
2. Give one small hint to make them think.
3. Ask one gentle guiding question.
4. Give one tiny nudge without revealing the whole answer.

After this guidance, continue with the full 6-section Homework Buddy format.
Everything should be warm, simple, and grade {grade_level} friendly.
"""


# -----------------------------------------------------------
# QUIZ prompt using the new 6-section structure
# -----------------------------------------------------------
def build_quiz_prompt(topic: str, grade_level: str):
    return f"""
Create a gentle study quiz for the topic "{topic}" using the 6-section Homework Buddy model.

OVERVIEW: Very short introduction to what the quiz is about.
KEY FACTS: The most basic facts a student should know.
CHRISTIAN VIEW (if relevant): Keep soft and non-confrontational.
AGREEMENT & DIFFERENCE: Only include if naturally relevant.
PRACTICE: Include several quiz questions with short example answers.

Questions should be calm, short, and easy for grade {grade_level}.
"""


# -----------------------------------------------------------
# FLASHCARD prompt using the 6-section structure
# -----------------------------------------------------------
def build_flashcard_prompt(topic: str, grade_level: str):
    return f"""
Create flashcards for the topic "{topic}" using the 6-section Homework Buddy format.

Flashcards should be extremely simple:
- One idea per card
- Clear, short explanation
- Friendly tutoring tone

In the PRACTICE section, include 3–5 flashcard-style Q&A pairs.
"""


# -----------------------------------------------------------
# PUBLIC FUNCTIONS — SOCratic + 6-SECTION ANSWER
# -----------------------------------------------------------

def generate_quiz(topic: str, grade_level="8", character=None):

    if character is None:
        character = "theo"

    base_prompt = build_quiz_prompt(topic, grade_level)
    full_prompt = socratic_layer(topic, grade_level) + "\n" + base_prompt

    enriched = apply_personality(character, full_prompt)
    ai_text = study_buddy_ai(enriched, grade_level, character)

    sections = parse_into_sections(ai_text)
    return format_answer(**sections)



def flashcards(topic: str, grade_level="8", character=None):

    if character is None:
        character = "theo"

    base_prompt = build_flashcard_prompt(topic, grade_level)
    full_prompt = socratic_layer(topic, grade_level) + "\n" + base_prompt

    enriched = apply_personality(character, full_prompt)
    ai_text = study_buddy_ai(enriched, grade_level, character)

    sections = parse_into_sections(ai_text)
    return format_answer(**sections)

