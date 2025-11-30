# modules/study_helper.py

from modules.shared_ai import study_buddy_ai
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

    # Tutor follow-up (NOT study guide, no sections)
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
• No 6-section format
• No repeating the master guide
• If asked for more detail, go deeper in a conversational way
"""

    reply = study_buddy_ai(prompt, grade_level, character)

    if isinstance(reply, dict):
        return reply.get("raw_text") or reply.get("text") or str(reply)

    return reply


def generate_master_study_guide(text, grade_level="8", character="everly"):
    """
    Generates the ULTRA MASTER STUDY GUIDE.
    Used ONLY when submitting through PowerGrid.
    """

    prompt = f"""
Create the most complete, extremely in-depth MASTER STUDY GUIDE possible.

CONTENT SOURCE:
{text}

GOALS:
• Teach EVERYTHING the AI knows about this topic
• Cover beginner, intermediate, advanced, and expert levels
• Break every major idea into bullet points
• Use sub-bullets for deeper detail
• Provide examples, analogies, comparisons
• Include diagrams-in-text when useful (ASCII)
• Provide formulas and equations when relevant
• List common mistakes students make
• Give exam-style memory tips
• Include mastery-level insights very few people know

STYLE:
• Very clear
• Very structured
• All bullet points (no paragraphs)
• Indented hierarchy
• No markdown formatting
• Friendly tutor tone
• Written for grade {grade_level} but extremely deep

FORMAT:
• Clean plain text
• Lots of sections
• Lots of bullet points
• Lots of sub-bullets
• As long as needed

OUTPUT:
• 5x–10x longer than a normal study guide
• A true master guide
"""

    # DO NOT apply personality to the master guide;
    # keep it neutral and purely focused on content.
    # prompt = apply_personality(character, prompt)

    response = study_buddy_ai(prompt, grade_level, character)

    if isinstance(response, dict):
        return response.get("raw_text") or response.get("text") or str(response)

    return response
