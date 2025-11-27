# modules/apologetics_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


def build_apologetics_prompt(question: str, grade_level: str):
    """
    Builds the base apologetics prompt before personality is applied.
    Conversational, gentle tone, subtle worldview.
    Includes well-known Christian apologists + Scripture.
    """

    return f"""
The student has asked a Christian apologetics question:

\"{question}\"

Your role:
Speak in a calm, warm, conversational tone suitable for a grade {grade_level} student.
Avoid lists, hype, debates, or dramatic language. 
You are simply explaining what many Christians believe and the gentle reasons behind it.

Key instructions for your explanation:
• Speak naturally and kindly, as if sitting beside the student.
• Explain what many Christians believe about this question.
• Mention ideas commonly discussed by respected Christian apologists,
  such as C.S. Lewis, William Lane Craig, Lee Strobel, John Lennox,
  Frank Turek, Alvin Plantinga, Wes Huff, Augustine, Aquinas,
  and early Christian teachers. These names should be woven in softly.
• Use Scripture references gently (for example: “Many Christians look to John 1:1…”).
• You may softly mention how Christians see support from history, logic, 
  moral reasoning, design in nature, or personal experience.
• Acknowledge respectfully that some people see things differently.
• The goal is understanding, not arguing.
• End with a short, simple summary in warm, kid-friendly language.

Tone guidelines:
Everything should feel like a calm, thoughtful conversation.
No lists, no bullet points, no headings, no markdown.
"""


def apologetics_answer(question: str, grade_level="8", character=None):
    """
    Provides a Christian apologetics-style answer that is:
    - calm
    - conversational
    - personality-aware
    - subtle
    - respectful of different beliefs
    """

    if character is None:
        character = "valor_strike"

    base_prompt = build_apologetics_prompt(question, grade_level)

    # Add the character's subtle voice layer
    enriched_prompt = apply_personality(character, base_prompt)

    # Send to AI
    return study_buddy_ai(enriched_prompt, grade_level, character)

 