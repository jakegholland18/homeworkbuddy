# modules/study_helper.py

from modules.shared_ai import study_buddy_ai

def deep_study_chat(question, grade_level="8", character="everly"):
    """
    A robust deep conversation handler for PowerGrid.

    It accepts:
    • A single string (normal subject question)
    • A list of messages like:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

    It ALWAYS converts everything into a valid conversation structure
    and then generates a deep tutor response.
    """

    # ============================================================
    # NORMALIZE INPUT → ALWAYS return a list with dict messages
    # ============================================================

    # Case 1: A plain string question
    if isinstance(question, str):
        conversation = [{"role": "user", "content": question.strip()}]

    # Case 2: A list (chat history or raw strings)
    elif isinstance(question, list):
        conversation = []
        for turn in question:
            # Already a dict (valid)
            if isinstance(turn, dict) and "content" in turn:
                conversation.append({
                    "role": turn.get("role", "user"),
                    "content": str(turn.get("content", "")).strip()
                })
            # A raw string inside the list → treat as user message
            else:
                conversation.append({
                    "role": "user",
                    "content": str(turn).strip()
                })

    # Case 3: Unknown format → convert to string
    else:
        conversation = [{"role": "user", "content": str(question)}]

    # ============================================================
    # BUILD HUMAN-FRIENDLY DIALOGUE CONTEXT
    # ============================================================

    dialogue_text = ""
    for turn in conversation:
        role = turn.get("role", "user")
        content = turn.get("content", "")

        speaker = "Student" if role == "user" else "Tutor"
        dialogue_text += f"{speaker}: {content}\n"

    # ============================================================
    # THE AI PROMPT (Deep Study Tutor)
    # ============================================================

    prompt = f"""
You are the DEEP STUDY TUTOR of PowerGrid.

Your personality:
• Warm, calm, clear
• Gentle Christian virtues (wisdom, patience, clarity, moral grounding)
• Speak with purpose and depth
• Guide the student step-by-step
• Never shame or judge — always empower

GRADE LEVEL: {grade_level}

Here is the conversation so far:

{dialogue_text}

Now continue as the PowerGrid tutor.
Go deep.
Explain with clarity.
Guide the student's understanding.
""".strip()

    # ============================================================
    # CALL THE MODEL
    # ============================================================

    response = study_buddy_ai(prompt, grade_level, character)

    # Ensure a clean text return, even if helper returns dicts
    if isinstance(response, dict):
        return response.get("raw_text") or response.get("text") or str(response)

    return response






