# modules/text_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -------------------------
# Detect Christian-oriented questions
# -------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "Christian", "Christianity", "Bible", "God", "Jesus",
        "faith", "biblical", "Christian perspective"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -------------------------
# READING SKILL MAP PER GRADE
# -------------------------
READING_TOPICS = {
    "1": ["main idea", "characters", "simple sentences", "beginning-middle-end"],
    "2": ["story retelling", "details", "characters", "setting"],
    "3": ["summary", "theme", "paragraph meaning"],
    "4": ["inference", "main idea", "text structure"],
    "5": ["summaries", "explanations", "compare and contrast"],
    "6": ["claims and evidence", "author purpose"],
    "7": ["analysis", "theme", "argument structure"],
    "8": ["evaluating reasoning", "finding evidence"],
    "9": ["literary analysis", "symbolism", "plot development"],
    "10": ["complex text analysis", "tone", "purpose"],
    "11": ["advanced comprehension", "argument evaluation"],
    "12": ["college-level reading analysis"]
}


# -------------------------------------------------------------
# SUMMARIZE TEXT (MAIN READING FEATURE)
# -------------------------------------------------------------
def summarize_text(text: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    # Christian worldview request
    if is_christian_question(text):
        christian_prompt = f"""
The student asked for a Christian perspective related to this reading or summary.

Text: {text}

Give a calm explanation about how many Christians value understanding,
thoughtfulness, and careful reading. Do not claim the Bible teaches
modern reading strategies. Then provide a gentle summary of the text.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    prompt = f"""
Summarize the following text in a way a grade {grade_level} student
can easily understand. Keep the tone calm, friendly, and conversational.

Text to summarize:
{text}

Your response should include:
A simple, clear summary
A short note about the main idea
One or two gentle reminders for how to understand texts like this
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


# -------------------------------------------------------------
# HELP WITH READING COMPREHENSION
# -------------------------------------------------------------
def reading_help(question: str, passage: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    if is_christian_question(question + " " + passage):
        christian_prompt = f"""
The student wants reading comprehension help with a Christian viewpoint.

Passage: {passage}
Question: {question}

Explain gently how Christians may value learning, understanding,
and careful reading.

Then provide a clear, calm answer to the comprehension question.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    prompt = f"""
The student is asking a reading comprehension question.

Passage:
{passage}

Question:
{question}

Answer the question in a calm, friendly way appropriate for grade {grade_level}.
Include:
A simple explanation of the answer
A brief reference to the part of the passage that supports it
A small tip to help the student improve reading comprehension
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


# -------------------------------------------------------------
# HELP WITH MAIN IDEA
# -------------------------------------------------------------
def find_main_idea(passage: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    if is_christian_question(passage):
        christian_prompt = f"""
The student wants help finding the main idea with a Christian viewpoint.

Passage: {passage}

Explain that many Christians value reading carefully and thoughtfully.

Then gently identify the main idea of the passage.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    prompt = f"""
Help the student find the main idea of this passage:

{passage}

Explain in a calm, conversational way:
What the passage is mostly about
Why this is the main idea
A short tip for recognizing main ideas in future reading
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


# -------------------------------------------------------------
# HELP WITH A READING ASSIGNMENT (GENERAL)
# -------------------------------------------------------------
def help_with_reading_task(task: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    if is_christian_question(task):
        christian_prompt = f"""
The student asked for this reading task from a Christian perspective.

Task: {task}

Give a gentle explanation about how Christians may value thoughtful
communication and careful reading.

Then complete the task calmly and clearly.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    prompt = f"""
Help the student with this reading-related task:

{task}

Explain how to approach the task in a calm, simple way.
If needed, provide an example or model.
Offer one or two small tips to help them understand similar tasks.
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)

