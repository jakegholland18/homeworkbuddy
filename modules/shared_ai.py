# modules/shared_ai.py
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -------------------------------------------------------
# CHARACTER VOICES
# -------------------------------------------------------
def build_character_voice(character: str) -> str:
    voices = {
        "lio":    "Speak smooth, confident, mission-focused, like a calm space agent.",
        "jasmine": "Speak warm, bright, curious, like a kind space big sister.",
        "everly":  "Speak elegant, brave, compassionate, like a gentle warrior-princess.",
        "nova":    "Speak energetic, curious, nerdy-smart, excited about learning.",
        "theo":    "Speak thoughtful, patient, wise, like a soft academic mentor.",
    }
    return voices.get(character, "Speak in a friendly, warm tutoring voice.")


# -------------------------------------------------------
# GRADE LEVEL DEPTH CONTROL
# -------------------------------------------------------
def grade_depth_instruction(grade: str) -> str:
    """Return depth rules for the AI output based on grade."""
    g = int(grade)

    if g <= 3:
        return "Use extremely simple language. Use very short sentences. Explain like the student is very young."
    if g <= 5:
        return "Use simple language with clear examples. Do not use advanced vocabulary."
    if g <= 8:
        return "Use moderate detail, clear logic, and age-appropriate examples."
    if g <= 10:
        return "Use deeper reasoning, more detailed explanations, and clearer examples."
    if g <= 12:
        return "Use full high-school level explanations, real-world examples, and deeper analysis."
    return "Use college-level clarity, detailed reasoning, and strong conceptual analysis."


# -------------------------------------------------------
# SYSTEM PROMPT — STRICT, PARAGRAPH ONLY
# -------------------------------------------------------
BASE_SYSTEM_PROMPT = """
You are HOMEWORK BUDDY — a warm, gentle tutor.

You MUST ALWAYS answer using EXACTLY these SIX labeled sections:

SECTION 1 — OVERVIEW
SECTION 2 — KEY FACTS
SECTION 3 — CHRISTIAN VIEW
SECTION 4 — AGREEMENT
SECTION 5 — DIFFERENCE
SECTION 6 — PRACTICE

STRICT FORMATTING RULES:
• NO bullet points at all.
• NO numbered lists.
• ALL sections must be written in paragraph sentences only.
• Each section must be 2–5 sentences depending on complexity.
• Never skip a section.
• Never merge sections.
"""


# -------------------------------------------------------
# MAIN AI CALL
# -------------------------------------------------------
def study_buddy_ai(prompt: str, grade: str, character: str) -> str:

    depth_rule = grade_depth_instruction(grade)
    voice = build_character_voice(character)

    system_prompt = f"""
{BASE_SYSTEM_PROMPT}

CHARACTER VOICE:
{voice}

GRADE LEVEL RULE:
{depth_rule}

ADDITIONAL RULES:
• Older students (grades 9–12) MUST receive deeper detail, more reasoning,
  more real-world application, and stronger conceptual clarity.
• Younger students receive simpler, slower, gentler explanations.
• ALL SIX sections MUST contain full paragraph sentences.
• Absolutely no bullet points or list formatting.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=f"""
SYSTEM:
{system_prompt}

USER TASK:
{prompt}
"""
    )

    return response.output_text


