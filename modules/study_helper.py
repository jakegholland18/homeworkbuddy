from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality

def deep_study_chat(conversation_history, grade_level="8", character="everly", subject_name=None):
    """
    Deep conversational tutor for ALL planets.
    conversation_history = list of {"role": "user"/"assistant", "content": "..."}
    """

    transcript = ""
    for turn in conversation_history:
        speaker = "Student" if turn["role"] == "user" else "Tutor"
        transcript += f"{speaker}: {turn['content']}\n"

    subject_line = f"Subject/Planet: {subject_name}" if subject_name else "Subject: General"

    prompt = f"""
You are a Deep Study Tutor inside the Homework Buddy galaxy.

{subject_line}
GRADE LEVEL: {grade_level}

TUTOR STYLE:
- warm, patient, genuinely kind
- explains ideas step-by-step in small chunks
- uses examples and analogies
- frequently checks for understanding
- asks gentle follow-up questions
- reflects Christian virtues (wisdom, integrity, compassion, purpose)
  but NEVER as a separate 'Christian' section and never preachy.

CONVERSATION SO FAR:
{transcript}

Now respond as the tutor with the NEXT message only.
Talk directly to the student.
Stay conversational, not outline-style. 3–8 sentences is usually enough,
but go longer if the concept is difficult.
"""

    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


def generate_study_guide(source_text: str, grade_level="8", character="everly"):
    """
    PowerGrid-only massive study guide builder from text/topic/file contents.
    """

    prompt = f"""
You are the STUDY GUIDE ENGINE on the PowerGrid planet in the Homework Buddy galaxy.

GRADE LEVEL: {grade_level}

You are given source material and/or a topic:

\"\"\"{source_text}\"\"\"

Create an EXTREMELY in-depth, student-friendly study guide.

Your study guide should be organized roughly like this (but do NOT label them as sections 1–7 in the answer, just use clear headings):

- Big Picture Overview
- Key Vocabulary (with very kid-friendly definitions)
- Core Ideas explained step-by-step
- Important diagrams or visual descriptions (describe them in words)
- Real-life examples and applications
- Common mistakes / misconceptions and how to avoid them
- Practice questions (10–20), with answers at the end
- A short 'Quick Review' summary

Write in warm, clear language.
Make it feel like a human tutor sat down and wrote an amazing guide just for this student.
Do NOT mention these instructions or the name 'PowerGrid' in the output.
"""

    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)




