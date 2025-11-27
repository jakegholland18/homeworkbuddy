# modules/writing_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -------------------------
# Detect Christian-oriented questions
# -------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "Christian", "Christianity", "God", "Jesus",
        "Bible", "faith", "biblical",
        "from a Christian perspective",
        "Christian worldview",
        "how does this relate to Christianity",
        "how does this relate to God"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -------------------------
# Writing difficulty guidance per grade level
# -------------------------
WRITING_TOPICS = {
    "1": ["simple sentences", "capital letters", "punctuation", "writing about feelings"],
    "2": ["short paragraphs", "topic sentences", "story order"],
    "3": ["multi-sentence paragraphs", "details", "basic stories"],
    "4": ["strong paragraphs", "explanations", "transitions"],
    "5": ["multi-paragraph writing", "clear ideas", "simple essays"],
    "6": ["thesis sentences", "organization", "evidence"],
    "7": ["argument writing", "analysis", "longer essays"],
    "8": ["research basics", "structured essays", "clear reasoning"],
    "9": ["literary analysis", "strong thesis statements", "evidence paragraphs"],
    "10": ["research writing", "argument essays", "clarity and structure"],
    "11": ["advanced essays", "formal tone", "text analysis"],
    "12": ["college-style writing", "precision", "professional organization"]
}


# -------------------------------------------------------------
# EXPLAIN A WRITING SKILL
# -------------------------------------------------------------
def explain_writing(topic: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    if is_christian_question(topic):
        christian_prompt = f"""
The student asked for a Christian perspective about writing or communication.

Topic: {topic}

Offer a calm explanation about how many Christians value honesty,
clarity, and kindness in communication. Explain that writing can be a way
to express ideas thoughtfully and respectfully. Avoid claiming the Bible
teaches modern writing techniques.

Do not teach the writing skill here. Only give the worldview connection.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    grade_topics = ", ".join(WRITING_TOPICS.get(str(grade_level), []))

    prompt = f"""
Teach the writing skill: {topic}
Grade level: {grade_level}

Explain the topic gently and in a calm, natural way.
Avoid hype, dramatic language, or anything overly emotional.

Include:
A simple explanation of the writing skill
A step-by-step way to use the skill
A short example that shows how it works
A few reminders for students
Five practice tasks
Then the answers or model examples

Use the grade level topics for difficulty guidance: {grade_topics}
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


# -------------------------------------------------------------
# HELP WRITE SOMETHING
# -------------------------------------------------------------
def help_write(task: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    if is_christian_question(task):
        christian_prompt = f"""
The student asked for this writing task from a Christian viewpoint.

Task: {task}

Provide a gentle explanation of how Christians may view writing as a way
to communicate truthfully and thoughtfully. Show how the Bible's writing methods were used to share foundational ideas.
Then, help with the writing task as requested.
Keep it calm and age-appropriate.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    prompt = f"""
Help the student with this writing task:

{task}

Guide them through it in a calm, friendly, conversational way.
Avoid strong emotion or dramatic tone.
You may write example paragraphs or essays,
but keep them simple and age-appropriate.

Include:
A short explanation of what the student is trying to write
A gentle model example
A couple reminders about clarity and organization
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


# -------------------------------------------------------------
# EDIT STUDENT WRITING
# -------------------------------------------------------------
def edit_writing(text: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    if is_christian_question(text):
        christian_prompt = f"""
The student asked for feedback from a Christian viewpoint.

Text: {text}

Give a calm explanation about the value of thoughtful and honest communication.
Avoid intense or emotional tone.

Then gently suggest improvements to the student's writing.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    prompt = f"""
Read this student's writing and gently improve it.
Keep the tone warm, calm, and encouraging.
Correct grammar or clarity issues but do not change the student's meaning.

Text to improve:
{text}

Provide:
A smoother version of the paragraph
A short explanation of the improvements
A couple encouragements for next time
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


# -------------------------------------------------------------
# CREATIVE WRITING HELP
# -------------------------------------------------------------
def creative_writing(prompt_text: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    if is_christian_question(prompt_text):
        christian_prompt = f"""
The student wants a creative writing response with a Christian perspective.

Prompt: {prompt_text}

Offer an explanation of how Christians approach storytelling
through themes of hope, kindness, and responsibility.

Then create a gentle story for the student, suitable for grade {grade_level}.
No dramatic intensity. Keep it peaceful.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    prompt = f"""
Write a simple creative story based on this prompt:

{prompt_text}

Keep the storytelling calm, gentle, and understandable for grade {grade_level}.
Avoid dramatic scenes or intense emotion.
You may add soft personality influence based on the selected character.
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)

