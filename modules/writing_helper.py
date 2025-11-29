# modules/writing_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


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
# SOCratic Tutor Layer
# -------------------------------------------------------
def socratic_layer(question: str, grade_level: str):
    """
    Returns a block of Socratic tutoring instructions
    that the AI will prepend before delivering the 6-section format.
    """
    return f"""
A student asked: "{question}"

Before giving the full structured answer, guide them Socratically:

1. Restate what the question is really asking in very simple, kid-friendly words.
2. Offer one gentle hint that points their thinking in the right direction.
3. Ask a guiding question that makes the student think more deeply.
4. Give a tiny nudge—but do NOT reveal the full answer.

After these 4 steps, begin the 6-section Homework Buddy format.
Make everything appropriate for a grade {grade_level} student.

Now continue with the structured answer below.
"""


# -------------------------------------------------------
# BASE PROMPTS (all generate 6-section answers)
# -------------------------------------------------------
def build_writing_skill_prompt(topic: str, grade_level: str):
    return f"""
Teach the writing skill "{topic}" using the 6 Homework Buddy sections:
Overview, Key Facts, Christian View, Agreement, Difference, Practice.

Make examples very small and simple.
Use friendly, clear explanations for grade {grade_level}.
"""


def build_writing_task_prompt(task: str, grade_level: str):
    return f"""
Help the student complete this writing task:

{task}

Explain it using the 6 Homework Buddy sections:
Overview, Key Facts, Christian View, Agreement, Difference, Practice.

Keep ideas practical and easy for grade {grade_level}.
"""


def build_editing_prompt(text: str, grade_level: str):
    return f"""
Improve this student writing:

{text}

Explain improvements using the 6 sections:
Overview, Key Facts, Christian View, Agreement, Difference, Practice.

Be encouraging and gentle for grade {grade_level}.
"""


def build_creative_prompt(prompt_text: str, grade_level: str):
    return f"""
Write a gentle creative story based on:

{prompt_text}

After the story, explain it using the 6-section Homework Buddy structure.
Make it calm, warm, and friendly for grade {grade_level}.
"""


# -------------------------------------------------------
# PUBLIC FUNCTIONS — with SOCratic + STRUCTURED formatting
# -------------------------------------------------------

def explain_writing(topic: str, grade_level="8", character=None):

    if character is None:
        character = "theo"

    # Christian vs general prompt
    if is_christian_question(topic):
        base_prompt = f"""
Explain the writing topic "{topic}" with a gentle Christian viewpoint.

Use the 6 Homework Buddy sections.
"""
    else:
        base_prompt = build_writing_skill_prompt(topic, grade_level)

    # 🎯 Add the Socratic intro BEFORE the structured prompt
    full_prompt = socratic_layer(topic, grade_level) + "\n" + base_prompt

    enriched = apply_personality(character, full_prompt)
    ai_text = study_buddy_ai(enriched, grade_level, character)

    sections = parse_into_sections(ai_text)
    return format_answer(**sections)



def help_write(task: str, grade_level="8", character=None):

    if character is None:
        character = "theo"

    if is_christian_question(task):
        base_prompt = f"""
Help the student with this writing task from a gentle Christian viewpoint:

{task}

Use the 6 Homework Buddy sections.
"""
    else:
        base_prompt = build_writing_task_prompt(task, grade_level)

    full_prompt = socratic_layer(task, grade_level) + "\n" + base_prompt
    enriched = apply_personality(character, full_prompt)
    ai_text = study_buddy_ai(enriched, grade_level, character)

    sections = parse_into_sections(ai_text)
    return format_answer(**sections)



def edit_writing(text: str, grade_level="8", character=None):

    if character is None:
        character = "theo"

    if is_christian_question(text):
        base_prompt = f"""
Edit this writing with a gentle Christian viewpoint:

{text}

Use the 6 Homework Buddy sections.
"""
    else:
        base_prompt = build_editing_prompt(text, grade_level)

    full_prompt = socratic_layer(text, grade_level) + "\n" + base_prompt
    enriched = apply_personality(character, full_prompt)
    ai_text = study_buddy_ai(enriched, grade_level, character)

    sections = parse_into_sections(ai_text)
    return format_answer(**sections)



def creative_writing(prompt_text: str, grade_level="8", character=None):

    if character is None:
        character = "theo"

    if is_christian_question(prompt_text):
        base_prompt = f"""
Write a creative story with a gentle Christian viewpoint:

{prompt_text}

Explain it using the 6 sections.
"""
    else:
        base_prompt = build_creative_prompt(prompt_text, grade_level)

    full_prompt = socratic_layer(prompt_text, grade_level) + "\n" + base_prompt
    enriched = apply_personality(character, full_prompt)
    ai_text = study_buddy_ai(enriched, grade_level, character)

    sections = parse_into_sections(ai_text)
    return format_answer(**sections)



