# modules/apologetics_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


def socratic_layer(base_explanation: str, question: str, grade_level: str):
    """
    Wraps the final explanation in a guided-learning, Socratic tutoring style.
    The student receives:
    • interpretation of the question
    • a hint
    • a guiding question
    • a gentle nudge
    • THEN the full apologetics explanation
    """

    return f"""
A student asked: "{question}"

Begin by guiding the student without giving the full answer immediately.

First, restate what the question is really asking in simple, kid-friendly language.

Next, offer a helpful hint that points them in the right direction
without giving the answer away.

Then ask a gentle guiding question that encourages them to think.
It should make the student reflect on the deeper meaning of the topic
and move closer to understanding.

After that, give one more small nudge—just enough to help them
if they are stuck, but still not revealing the full explanation.

Once you have guided the student with these steps,
you may transition naturally into the full apologetics explanation below.

Full Explanation:
{base_explanation}

End with a warm summary that encourages them and praises their curiosity.
Keep everything conversational and age-appropriate for grade {grade_level}.
"""


def build_apologetics_prompt(question: str, grade_level: str):
    """
    Creates the base apologetics prompt (the final explanation),
    which then gets wrapped inside the Socratic method.
    """

    return f"""
The student has asked a Christian apologetics question:

\"{question}\"

Speak warmly and conversationally, as if you're talking to a grade {grade_level} student.

Explain what many Christians believe AND why thoughtful Christians—
including respected apologists like C.S. Lewis, John Lennox, Lee Strobel,
William Lane Craig, and Alvin Plantinga—find these beliefs compelling.

You may mention Scripture softly and naturally,
and you may gently acknowledge how a secular worldview might see the issue differently,
but the focus should remain on why Christians find their worldview meaningful.

Keep the tone gentle, thoughtful, and calm.
No lists. No headings. No markdown.
Just smooth, friendly conversation.
"""


def apologetics_answer(question: str, grade_level="8", character=None):
    """
    Produces a personality-aware, Socratic-guided apologetics explanation.
    """

    if character is None:
        character = "valor_strike"

    # First: Build the final apologetics explanation
    base_explanation = build_apologetics_prompt(question, grade_level)

    # Second: Wrap it with the Socratic tutor method
    guided_prompt = socratic_layer(base_explanation, question, grade_level)

    # Third: Apply the character’s voice/personality layer
    enriched_prompt = apply_personality(character, guided_prompt)

    # Fourth: Send it to the AI engine
    return study_buddy_ai(enriched_prompt, grade_level, character)


 