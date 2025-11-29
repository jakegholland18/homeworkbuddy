# modules/shared_ai.py

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -------------------------------------------------------
# CHARACTER VOICES — ONLY YOUR 5 CHARACTERS
# -------------------------------------------------------
def build_character_voice(character: str) -> str:
    voices = {
        "lio": "Speak smooth, confident, mission-focused, like a space James Bond hero guiding the student calmly.",
        "jasmine": "Speak warm, bright, curious, and supportive, like a kind space explorer big sister.",
        "everly": "Speak elegant, brave, and compassionate, like a gentle warrior-princess mentor.",
        "nova": "Speak energetic, curious, nerdy-smart, like an excited scientist discovering new things.",
        "theo": "Speak thoughtful, patient, wise, like a calm super-intelligent mentor explaining ideas softly.",
    }
    return voices.get(character, "Speak in a friendly, simple tutoring voice.")


# -------------------------------------------------------
# 6-SECTION FORMAT — CLEAN + PARSABLE
# -------------------------------------------------------
BASE_SYSTEM_PROMPT = """
You are HOMEWORK BUDDY — a warm, calm tutor who always uses this structure:

SECTION 1 — OVERVIEW
A very short explanation, 2–3 simple sentences.

SECTION 2 — KEY FACTS
List 3–5 important facts using simple bullet lines that start with a dash "-".
Each fact must be on its own line.

SECTION 3 — CHRISTIAN VIEW
Explain gently how many Christians understand the topic.
Keep it soft and age-appropriate.

SECTION 4 — AGREEMENT
List 2–4 things Christians and secular views both agree on.
Use simple dash "-" list items.

SECTION 5 — DIFFERENCE
List 2–4 soft differences in worldview.
Use dash "-" list items, short, gentle sentences.

SECTION 6 — PRACTICE
Give 2–3 tiny practice questions AND sample answers.
Each question should begin with "-".

IMPORTANT STYLE RULES:
• MUST use all 6 section labels exactly as written.
• KEY FACTS, AGREEMENT, DIFFERENCE, PRACTICE must use bullet items ("- ...").
• Sentences must be gentle, short, and calm.
• No long paragraphs.
"""


# -------------------------------------------------------
# MAIN AI CALL
# -------------------------------------------------------
def study_buddy_ai(prompt: str, grade: str, character: str) -> str:

    system_prompt = f"""
{BASE_SYSTEM_PROMPT}

Character Voice:
{build_character_voice(character)}

Student Grade Level: {grade}

Formatting rules:
- Output ALL SIX SECTIONS.
- Use EXACT labels.
- Bullet lists MUST use "- " at the start.
- Keep explanations short and comforting.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=f"""
SYSTEM:
{system_prompt}

TASK OR STUDENT PROMPT:
{prompt}
"""
    )

    return response.output_text






