from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality

def deep_study_chat(conversation_history, grade, character):
    # Turn memory into transcript text
    transcript = ""
    for turn in conversation_history:
        role = "Student" if turn["role"] == "user" else "Tutor"
        transcript += f"{role}: {turn['content']}\n"

    prompt = f"""
You are a Deep Study Tutor inside the Power Grid planet.

TUTOR STYLE:
• warm, patient, friendly  
• extremely detailed explanations  
• break ideas down step-by-step  
• challenge the student gently  
• always ask follow-up questions  
• bring in Christian wisdom but not as a separate section  
• pure conversation, no labeled sections  
• act like a real mentor talking to the student  

CONVERSATION SO FAR:
{transcript}

Continue the conversation as the tutor speaking directly to the student.
"""

    prompt = apply_personality(character, prompt)

    return study_buddy_ai(prompt, grade, character)



