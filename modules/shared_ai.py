import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------------------
# CONVERSATIONAL TUTOR PROMPT
# ---------------------------------------
BASE_SYSTEM_PROMPT = """
You are Homework Buddy, a friendly conversational tutor.
Your responses must be SHORT, SIMPLE, and INTERACTIVE.

Your required structure:
1. Give 2–4 short key facts (bullet-style or tiny sentences).
2. Ask the student a quick question about what they think.
3. Do NOT give long essays.
4. Do NOT solve the entire thing all at once.
5. Wait for their reply before giving the next chunk.
6. Keep it friendly, upbeat, and encouraging.

Forbidden:
- Big paragraphs
- Full essay answers
- Overloaded explanations
- Solving a student's graded assignment fully
"""

# ---------------------------------------
# BUILD PERSONALITY
# ---------------------------------------
def build_character_voice(character):
    voices = { 
        "valor_strike": "You sound brave, confident, heroic, like a supportive captain.",
        "princess_everly": "You sound warm, elegant, encouraging, like a kind princess mentor.",
        "nova_circuit": "You sound smart, curious, energetic, like a friendly scientist.",
        "agent_cluehart": "You sound witty, thoughtful, detective-like.",
        "buddy_barkston": "You sound happy, loyal, friendly, like a golden retriever.",
    }
    
    return voices.get(character, "You speak in a friendly, upbeat tutoring voice.")


# ---------------------------------------
# MAIN BUDDY AI FUNCTION
# ---------------------------------------
def study_buddy_ai(question, grade, character):

    character_voice = build_character_voice(character)

    # Merge prompts
    system_prompt = (
        BASE_SYSTEM_PROMPT
        + f"\n\nYour character voice: {character_voice}\n"
        + f"You are helping a grade {grade} student. Use simple language.\n"
    )

    # ----------------------------
    # FIX: Use input= instead of messages=
    # ----------------------------
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=f"""
SYSTEM:
{system_prompt}

USER QUESTION:
{question}
"""
    )

    return response.output_text



