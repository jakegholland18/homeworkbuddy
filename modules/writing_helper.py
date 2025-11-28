# modules/writing_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -------------------------------------------------------
# Detect Christian-oriented questions
# -------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "christianity", "god", "jesus",
        "bible", "faith", "biblical",
        "from a christian perspective",
        "christian worldview",
        "how does this relate to christianity",
        "how does this relate to god"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -------------------------------------------------------
# Socratic Tutor Layer
# -------------------------------------------------------
def socratic_layer(base_explanation: str, question: str, grade_level: str):
    """
    Gives guided steps before the main writing explanation:
    - Clarify question
    - Give gentle hint
    - Ask guiding question
    - Provide tiny nudge
    - Transition into full explanation
    """

    return f"""
A student needs writing help with this:

"{question}"

Before giving the full explanation, guide them gently so they think on their own.

Start by restating what the student is really asking in simple,
kid-friendly language so they feel understood.

Then offer a small hint that nudges them in the right direction
without giving away the full explanation.

After that, ask a guiding question that invites the student to notice
something about writing, such as structure, clarity, purpose,
or how ideas connect.

Next, provide a tiny nudge that helps them move forward if they feel stuck,
but still keeps them thinking rather than giving the answer.

Once they have had a chance to think,
transition naturally into the complete explanation below.

Full Explanation:
{base_explanation}

Finish with a warm, encouraging summary for a grade {grade_level} student,
reminding them that writing improves with practice and patience.
"""


# -------------------------------------------------------
# Writing difficulty guidance by grade
# -------------------------------------------------------
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


# -------------------------------------------------------
# EXPLAIN A WRITING SKILL (with Socratic tutor)
# -------------------------------------------------------
def explain_writing(topic: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    if is_christian_question(topic):
        base_prompt = f"""
The student asked for a Christian perspective about writing.

Topic: {topic}

Explain gently how Christians often value honesty, clarity,
and kindness in communication. Mention that writing can be a way
to express ideas thoughtfully and respectfully.

Do not claim that the Bible teaches modern writing methods.
Here you are only offering the worldview connection.
"""
    else:
        grade_topics = ", ".join(WRITING_TOPICS.get(str(grade_level), []))

        base_prompt = f"""
Teach the writing skill: {topic}
Grade level: {grade_level}

Speak in a calm, conversational tone.
Explain what the skill means and how a student can use it.
Include a gentle example, reminders about clarity, and a few tasks.
Avoid lists or dramatic language.

Use these grade-level topics to choose difficulty: {grade_topics}
"""

    guided_prompt = socratic_layer(base_prompt, topic, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


# -------------------------------------------------------
# HELP WITH A WRITING TASK (with Socratic tutor)
# -------------------------------------------------------
def help_write(task: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    if is_christian_question(task):
        base_prompt = f"""
The student asked for writing help from a Christian viewpoint.

Task:
{task}

Explain gently how Christians may view writing as a way to express truth,
kindness, and thoughtfulness. Then complete the writing task calmly
and age-appropriately.
"""
    else:
        base_prompt = f"""
Help the student with this writing task:

{task}

Explain what the task is asking for in a calm, simple tone.
Guide them with a friendly example and a few soft reminders about clarity.
"""

    guided_prompt = socratic_layer(base_prompt, task, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


# -------------------------------------------------------
# EDIT STUDENT WRITING (with Socratic tutor)
# -------------------------------------------------------
def edit_writing(text: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    if is_christian_question(text):
        base_prompt = f"""
The student wants writing feedback from a Christian viewpoint.

Text to edit:
{text}

Show how Christians value thoughtful and honest communication.
Then gently improve the writing while preserving the student's meaning.
"""
    else:
        base_prompt = f"""
Read the student's writing and gently improve it.

Text:
{text}

Provide a smoother version, explain the improvements softly,
and offer encouragement for next time.
"""

    guided_prompt = socratic_layer(base_prompt, text, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


# -------------------------------------------------------
# CREATIVE WRITING (with Socratic tutor)
# -------------------------------------------------------
def creative_writing(prompt_text: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    if is_christian_question(prompt_text):
        base_prompt = f"""
The student wants a creative story with a Christian perspective.

Prompt:
{prompt_text}

Explain gently how Christians often focus on themes like kindness,
hope, responsibility, and forgiveness in storytelling.

Then create a calm, gentle story appropriate for grade {grade_level}.
Avoid dramatic intensity.
"""
    else:
        base_prompt = f"""
Write a gentle creative story based on this prompt:

{prompt_text}

Keep the tone warm and understandable for grade {grade_level}.
Avoid intense emotion. Add subtle character personality if helpful.
"""

    guided_prompt = socratic_layer(base_prompt, prompt_text, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)

