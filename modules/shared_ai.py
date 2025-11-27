import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a friendly Study Buddy who speaks in a warm, calm, conversational tone.
You talk naturally, like you're sitting beside the student helping them understand.
No superheroes, no dramatic flair, and no emojis.
No markdown headers or lists.
Just natural, gentle, kid-friendly conversation.

If a character is selected, respond in that character’s voice
but lightly — subtle personality only.
"""

def study_buddy_ai(question, grade, character):
    character_name = character.replace("_", " ").title()

    character_prompt = (
        f"You are responding as {character_name}. "
        f"Your explanations should match a grade {grade} student's level. "
        "Speak warmly, clearly, and patiently. "
        "Avoid hype, dramatic language, or superhero themes."
    )

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": character_prompt},
            {"role": "user", "content": question}
        ]
    )

    return response.choices[0].message.content


