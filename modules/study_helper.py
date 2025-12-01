# modules/study_helper.py

from modules.shared_ai import study_buddy_ai, powergrid_master_ai, get_client
from modules.personality_helper import apply_personality
import json


# ============================================================
# DEEP STUDY CHAT FOLLOW-UP (Conversation Mode)
# ============================================================
def deep_study_chat(question, grade_level="8", character="everly"):
    """
    PowerGrid Deep Study Chat:
    Generates conversational follow-up responses
    AFTER the compressed PowerGrid study guide.
    """

    # Normalize input (string or list of turns)
    if isinstance(question, str):
        conversation = [{"role": "user", "content": question.strip()}]
    elif isinstance(question, list):
        conversation = []
        for turn in question:
            if isinstance(turn, dict):
                conversation.append({
                    "role": turn.get("role", "user"),
                    "content": str(turn.get("content", "")).strip()
                })
            else:
                conversation.append({
                    "role": "user",
                    "content": str(turn).strip()
                })
    else:
        conversation = [{"role": "user", "content": str(question)}]

    # Build readable dialogue
    dialogue_text = ""
    for turn in conversation:
        speaker = "Student" if turn["role"] == "user" else "Tutor"
        dialogue_text += f"{speaker}: {turn['content']}\n"

    # Tutor response prompt
    prompt = f"""
You are a warm, patient, expert tutor.

GRADE LEVEL: {grade_level}

Conversation so far:
{dialogue_text}

NOW RESPOND AS THE TUTOR.

RULES:
• Keep responses natural, friendly, and conversational
• Answer ONLY the student's most recent message
• No long essays
• No structured sections
• No study guide formatting
• No repeating the master study guide
• If student wants more detail, go deeper conversationally
"""

    reply = study_buddy_ai(prompt, grade_level, character)

    if isinstance(reply, dict):
        return reply.get("raw_text") or reply.get("text") or str(reply)

    return reply



# ============================================================
# OLD MASTER GUIDE (Bullet-Only) — STILL AVAILABLE
# ============================================================
def generate_master_study_guide(text, grade_level="8", character="everly"):
    """
    OLD bullet-only master guide for legacy subjects.
    """

    prompt = f"""
Create the most complete MASTER STUDY GUIDE possible.

CONTENT SOURCE:
{text}

GOALS:
• Extremely in-depth
• Beginner → expert
• Bullet points only
• Sub-bullets for detail
• Diagrams when needed
• Examples, analogies, memory tips
• Common mistakes
• Formulas when relevant

STYLE:
• Clean bullets only
• No paragraphs
• Highly structured
• Friendly tutor tone
• Grade {grade_level}

FORMAT:
• Plain text
• Very long
"""

    response = study_buddy_ai(prompt, grade_level, character)

    if isinstance(response, dict):
        return response.get("raw_text") or response.get("text") or str(response)

    return response



# ============================================================
# NEW COMPRESSED POWERGRID STUDY GUIDE (1,200 WORD LIMIT)
# ============================================================
def generate_powergrid_master_guide(text, grade_level="8", character="everly"):
    """
    COMPRESSED POWERGRID MASTER GUIDE
    Uses the new compressed strategy:
    • Hyper-efficient
    • Bullets + micro-paragraphs
    • 1,200-word hard cap
    • Christian worldview section at end
    """

    prompt = f"""
Create a COMPRESSED POWERGRID STUDY GUIDE.

CONTENT:
{text}

STRICT LIMIT:
⛔ NEVER exceed 1,200 words.
Stop early if needed.

STYLE:
• Extremely compact, information-dense
• Short sentences
• Crisp bullets allowed
• Micro-paragraphs only
• Avoid repetition
• Prioritize clarity + efficiency
• Definitions → insights → examples

MANDATORY FORMAT:
1. MICRO-OVERVIEW (3–5 sentences)
2. CORE IDEAS (compressed bullets)
3. FAST DEEP DIVE (micro-paragraphs)
4. MINI DIAGRAM (ASCII ≤ 5 lines, if helpful)
5. EXAMPLES (1–2 sentences each)
6. COMMON MISTAKES (compact bullets)
7. CHRISTIAN WORLDVIEW (1 paragraph)

TONE:
• Warm, clear, smart
• Grade {grade_level}-appropriate
"""

    response = powergrid_master_ai(prompt, grade_level, character)

    if isinstance(response, dict):
        return response.get("raw_text") or response.get("text") or str(response)

    return response

