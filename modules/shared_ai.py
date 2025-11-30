# modules/shared_ai.py

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ============================================================
# UNIVERSAL SAFETY LIMITS FOR RENDER
# ============================================================

# Prevents runaway responses and memory explosions
MAX_TOKENS_STUDY = 900          # for normal Q&A subjects
MAX_TOKENS_POWERGRID = 2400     # for Ultra PowerGrid Master Guide
MAX_TOKENS_FOLLOWUP = 600       # for deep study chat follow-ups


# ============================================================
# NORMAL SUBJECT AI (math, history, etc.)
# ============================================================

def study_buddy_ai(prompt, grade, character):
    """
    Standard AI call for all normal subjects.
    Returns short-to-medium responses.
    Render Safe.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_output_tokens=MAX_TOKENS_STUDY,
            messages=[
                {
                    "role": "system",
                    "content": f"""
You are Homework Buddy, a friendly intelligent tutor.
Speak clearly and at a grade {grade} level.
You take on the personality of the character: {character}.
Keep answers concise but helpful.
"""
                },
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"[Error generating response: {e}]"



# ============================================================
# POWERGRID — ULTRA MASTER STUDY GUIDE ENGINE
# ============================================================

def powergrid_master_ai(prompt, grade, character):
    """
    Generates the ULTRA PowerGrid Master Study Guide.
    Strictly limited tokens so Render does NOT crash.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_output_tokens=MAX_TOKENS_POWERGRID,
            temperature=0.35,  # more stable for long structured output
            messages=[
                {
                    "role": "system",
                    "content": f"""
You produce extremely detailed, structured study guides.
Character personality may influence tone gently: {character}.
GRADE: {grade}.
Follow instructions EXACTLY.
Never exceed token limits.
"""
                },
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0].message.content

    except Exception as e:
        return (
            "POWERGRID encountered an error while generating the study guide.\n"
            f"Error: {e}\n"
            "Try simplifying the topic or regenerating."
        )



# ============================================================
# DEEP STUDY FOLLOW-UP AI (chat after master guide)
# ============================================================

def powergrid_followup_ai(prompt, grade, character):
    """
    Short conversational follow-ups after generating the master guide.
    NOT used directly—wrapped by study_helper.deep_study_chat()
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_output_tokens=MAX_TOKENS_FOLLOWUP,
            temperature=0.5,
            messages=[
                {
                    "role": "system",
                    "content": f"""
You are a warm deep-study tutor.
Respond ONLY to the latest student message.
NO sections. NO long essays. NO study-guide format.
Grade level: {grade}
Character personality: {character}
"""
                },
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"[Follow-up error: {e}]"

