# modules/text_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -------------------------------------------------------
# Detect Christian-oriented questions
# -------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "christianity", "bible", "god", "jesus",
        "faith", "biblical", "christian perspective"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -------------------------------------------------------
# Socratic Tutor Layer
# -------------------------------------------------------
def socratic_layer(base_explanation: str, question: str, grade_level: str):
    """
    Wraps the lesson in guided thinking steps:
    - clarify the question
    - offer a gentle hint
    - ask a guiding question
    - give a tiny nudge
    - transition into full answer
    """
    return f"""
A student needs help understanding something about reading:

"{question}"

Before giving the full explanation, help the student think on their own.

Begin by restating the question in simple, kid-friendly words
so the student feels understood.

Next, offer a small hint that gently points toward the idea
without revealing the explanation too quickly.

Then ask a guiding question that invites the student to notice something
about the passage or the text they are reading.

After that, offer a tiny nudge—just enough to help them move forward
if they feel stuck, but not enough to give the full answer.

Once you have guided them through these steps, transition naturally
into the complete explanation below.

Full Explanation:
{base_explanation}

End with a soft, encouraging summary suitable for a grade {grade_level} student,
reminding them that reading gets easier the more they practice.
"""


# -------------------------------------------------------
# Grade-Level Reading Topics
# -------------------------------------------------------
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


# -------------------------------------------------------
# SUMMARIZE TEXT
# -------------------------------------------------------
def summarize_text(text: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    # Christian worldview request
    if is_christian_question(text):
        base_prompt = f"""
The student asked for a Christian perspective related to this reading.

Text: {text}

Explain calmly how Christians value careful reading and thoughtful
reflection. Avoid claiming the Bible teaches modern reading strategies.

Then provide a gentle summary of the text in a warm, simple tone.
"""
    else:
        base_prompt = f"""
Summarize this text for a grade {grade_level} student:

{text}

Make the summary clear, friendly, and conversational.
Include the main idea and one or two gentle reminders
for how to understand texts like this in the future.
"""

    # Add Socratic tutor
    guided_prompt = socratic_layer(base_prompt, text, grade_level)

    # Add personality
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


# -------------------------------------------------------
# READING COMPREHENSION
# -------------------------------------------------------
def reading_help(question: str, passage: str, grade_level="8", character=None):

    if character is None:
        character = "valor_strike"

    # Christian version
    if is_christian_question(question + " " + passage):
        base_prompt = f"""
The student asked for reading comprehension help with a Christian viewpoint.

Passage:
{passage}

Question:
{question}

Explain calmly how Christians value thoughtful understanding.
Then answer the comprehension question in a gentle, clear way.
"""
    else:
        base_prompt = f"""
The student needs help with this reading comprehension question.

Passage:
{passage}

Question:
{question}

Explain what the answer is, refer gently to the part of the passage 
that supports it, and finish with a short tip for better comprehension.
"""

    guided_prompt = socratic_layer(base_prompt, question, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


# -------------------------------------------------------
# MAIN IDEA HELP
# -------------------------------------------------------
def find_main_idea(passage: str, grade_level="8", character=None):

    if character is None:
        character = "valor_strike"

    # Christian version
    if is_christian_question(passage):
        base_prompt = f"""
The student wants help finding the main idea from a Christian perspective.

Passage:
{passage}

Explain that Christians value careful reading, then gently identify
the main idea and explain why it fits.
"""
    else:
        base_prompt = f"""
Help the student find the main idea of this passage:

{passage}

Explain what the passage is mostly about, why that is the main idea,
and give one small tip for recognizing main ideas.
"""

    guided_prompt = socratic_layer(base_prompt, passage, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


# -------------------------------------------------------
# GENERAL READING TASK HELP
# -------------------------------------------------------
def help_with_reading_task(task: str, grade_level="8", character=None):

    if character is None:
        character = "valor_strike"

    # Christian worldview
    if is_christian_question(task):
        base_prompt = f"""
The student asked for this reading task from a Christian perspective.

Task:
{task}

Explain gently how Christians value careful reading and understanding.
Then complete the task calmly and clearly.
"""
    else:
        base_prompt = f"""
Help the student with this reading task:

{task}

Explain how to approach it in a simple, warm tone.
Give a short example if helpful.
"""

    guided_prompt = socratic_layer(base_prompt, task, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


