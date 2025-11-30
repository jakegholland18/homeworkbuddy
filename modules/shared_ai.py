# modules/shared_ai.py
import os

# -------------------------------
# Lazy-load OpenAI client
# -------------------------------
def get_client():
    from openai import OpenAI
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
# GRADE LEVEL DEPTH RULES
# -------------------------------------------------------
def grade_depth_instruction(grade: str) -> str:
    g = int(grade)

    if g <= 3:
        return "Use extremely simple words and very short sentences. Explain slowly and gently."
    if g <= 5:
        return "Use simple language with clear examples. Keep ideas small and concrete."
    if g <= 8:
        return "Use moderate detail and gentle reasoning."
    if g <= 10:
        return "Use deeper reasoning with clear examples and explanations."
    if g <= 12:
        return "Use high-school level clarity, logic, and real-world examples."

    return "Use college-level conceptual precision and depth."


# -------------------------------------------------------
# HOMEWORK BUDDY SYSTEM PROMPT — STRICT SIX SECTIONS
# -------------------------------------------------------
BASE_SYSTEM_PROMPT = """
You are HOMEWORK BUDDY — a warm, gentle tutor.

You MUST ALWAYS output EXACTLY these SIX sections with EXACT ASCII labels:

SECTION 1 — OVERVIEW
SECTION 2 — KEY FACTS
SECTION 3 — CHRISTIAN VIEW
SECTION 4 — AGREEMENT
SECTION 5 — DIFFERENCE
SECTION 6 — PRACTICE

STRICT FORMAT RULES:
• No bullet points.
• No dashes used as list items.
• No numbered lists.
• No asterisk lists.
• ONLY paragraphs of full sentences.
• Each section MUST contain 2–5 sentences.
• After each label, put one blank line, then the paragraph.
• Never modify section labels.
• Never merge or remove sections.
• Never add new sections.
"""


# -------------------------------------------------------
# MAIN AI CALL (HOMEWORK BUDDY)
# -------------------------------------------------------
def study_buddy_ai(prompt: str, grade: str, character: str) -> str:

    depth_rule = grade_depth_instruction(grade)
    voice = build_character_voice(character)

    system_prompt = f"""
{BASE_SYSTEM_PROMPT}

CHARACTER VOICE:
{voice}

GRADE LEVEL DEPTH RULE:
{depth_rule}

OUTPUT REQUIREMENT:
For ALL SIX sections:
• Use EXACT labels.
• Write 2–5 full sentences.
• No bullets. No lists. No line breaks inside paragraphs.
"""

    client = get_client()

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=f"""
SYSTEM:
{system_prompt}

STUDENT QUESTION:
{prompt}
"""
    )

    return response.output_text


# -------------------------------------------------------
# POWERGRID MASTER GUIDE ENGINE (NO SIX-SECTIONS)
# -------------------------------------------------------
def powergrid_master_ai(prompt: str, grade: str, character: str) -> str:
    """
    Generates ULTRA-DETAILED PowerGrid mixed-format guides.
    No section restrictions. Allows bullets + paragraphs + diagrams.
    """

    depth_rule = grade_depth_instruction(grade)
    voice = build_character_voice(character)

    system_prompt = f"""
You are POWERGRID — the ultimate deep-study tutor.

GOALS:
• Produce extremely detailed, structured educational material
• Mix paragraphs, bullet points, sub-bullets, diagrams, and examples
• Go deep from beginner → expert
• Explain with clarity and intelligence
• Maintain a warm, encouraging teaching tone
• Adapt depth to grade level: {grade}
• Use character voice: {voice}

FINAL REQUIREMENT:
The LAST SECTION must be titled exactly:
CHRISTIAN WORLDVIEW PERSPECTIVE
and must contain 1–3 thoughtful paragraphs relating the topic
to Christian principles such as purpose, truth, stewardship,
wisdom, compassion, courage, and integrity.
"""

    client = get_client()

    response = client.responses.create(
        model="gpt-4.1",
        input=f"""
SYSTEM:
{system_prompt}

WRITE THE STUDY GUIDE BASED ON THIS CONTENT:
{prompt}
"""
    )

    return response.output_text
