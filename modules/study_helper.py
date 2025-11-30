# modules/study_helper.py

from modules.shared_ai import study_buddy_ai, powergrid_master_ai
from modules.personality_helper import apply_personality


def deep_study_chat(question, grade_level="8", character="everly"):
    """
    PowerGrid Deep Study Chat:
    Generates a conversational follow-up response.
    Used when the student is chatting AFTER the master study guide.
    """

    # Normalize question input (string or list)
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
                conversation.append({"role": "user", "content": str(turn).strip()})
    else:
        conversation = [{"role": "user", "content": str(question)}]

    # Build readable conversation text
    dialogue_text = ""
    for turn in conversation:
        speaker = "Student" if turn["role"] == "user" else "Tutor"
        dialogue_text += f"{speaker}: {turn['content']}\n"

    # Tutor follow-up
    prompt = f"""
You are a warm, patient, expert tutor.

GRADE LEVEL: {grade_level}

Conversation so far:
{dialogue_text}

NOW RESPOND AS THE TUTOR.

RULES:
• Keep response natural, friendly, helpful
• Answer ONLY the student's most recent message
• No long essays
• No structured sections
• No study guide formatting
• No repeating the master guide
• If asked for more detail, go deeper in a conversational way
"""

    reply = study_buddy_ai(prompt, grade_level, character)

    if isinstance(reply, dict):
        return reply.get("raw_text") or reply.get("text") or str(reply)

    return reply


# -------------------------------------------------------------
# OLD PowerGrid Study Guide Generator (kept for compatibility)
# -------------------------------------------------------------
def generate_master_study_guide(text, grade_level="8", character="everly"):
    """
    OLD bullet-only master guide.
    """
    prompt = f"""
Create the most complete, extremely in-depth MASTER STUDY GUIDE possible.

CONTENT SOURCE:
{text}

GOALS:
• Teach EVERYTHING the AI knows
• Beginner → expert levels
• Bullet points only
• Sub-bullets for depth
• Diagrams when useful
• Examples, analogies, memory tips
• Common mistakes
• Formulas where relevant

STYLE:
• Clean bullets only
• No paragraphs
• Very structured
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


# -------------------------------------------------------------
# NEW **ULTRA** SAFE PowerGrid Mixed-Format Master Guide
# -------------------------------------------------------------
def generate_powergrid_master_guide(text, grade_level="8", character="everly"):
    """
    ULTRA-DETAILED POWERGRID GUIDE (mixed format).
    SAFELY CONSTRAINED to avoid timeouts.
    """

    prompt = f"""
Create a highly detailed POWERGRID MASTER STUDY GUIDE.

CONTENT:
{text}

STRICT LENGTH LIMITS:
• Total output MUST stay within ~3,000–5,000 words.
• Do NOT exceed this limit.
• Do NOT generate endless or runaway text.
• Stop once all major ideas are clearly covered.

REQUIREMENTS:
• Mixed paragraphs AND bullet points
• Sub-bullets allowed
• ASCII diagrams if useful
• Formulas when relevant
• Examples + analogies
• Common mistakes
• Memory & exam strategies
• Beginner → Expert progression
• Smooth, warm, intelligent explanation

STRUCTURE:
1. Overview (1–2 paragraphs)
2. Key Concepts (bullets)
3. Deep Dive (mixed format)
4. ASCII Diagrams (optional)
5. Examples / Case Studies
6. Common Mistakes
7. Memory + Exam Strategies
8. Expert Insights
9. CHRISTIAN WORLDVIEW PERSPECTIVE
   • 1–3 paragraphs on truth, integrity, stewardship, purpose, compassion.

TONE:
• Inspirational but clear
• Smart but approachable
• Fit for grade {grade_level}
"""

    response = powergrid_master_ai(prompt, grade_level, character)

    if isinstance(response, dict):
        return response.get("raw_text") or response.get("text") or str(response)

    return response

