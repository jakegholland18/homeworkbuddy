# modules/text_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import format_answer


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
def socratic_layer(question: str, grade_level: str):
    return f"""
A student asked about this reading question or passage:

\"{question}\"

Before giving the full structured answer, guide them Socratically:

1. Restate what they are asking in very simple words.
2. Give one gentle hint that helps them think.
3. Ask one small guiding question.
4. Provide one tiny nudge, without giving the full answer.

After these 4 steps, begin the 6-section Homework Buddy format.
Everything must be clear and friendly for grade {grade_level}.
"""


# -------------------------------------------------------
# Build summary prompt using 6-section format
# -------------------------------------------------------
def build_summary_prompt(text: str, grade_level: str):
    return f"""
Summarize and explain this reading passage using the 6 sections:
Overview, Key Facts, Christian View, Agreement, Difference, Practice.

Passage:
{text}

Make OVERVIEW very short.
Make KEY FACTS simple.
In PRACTICE, include 2–3 small questions the student can try.
"""


# -------------------------------------------------------
# Reading comprehension question prompt
# -------------------------------------------------------
def build_comprehension_prompt(question: str, passage: str, grade_level: str):
    return f"""
Help the student understand this reading question.

Passage:
{passage}

Question:
{question}

Explain the answer using the 6 Homework Buddy sections.
Keep everything extremely simple and kid-friendly.
In PRACTICE, include one small comprehension question they can try.
"""


# -------------------------------------------------------
# Main idea prompt
# -------------------------------------------------------
def build_main_idea_prompt(passage: str, grade_level: str):
    return f"""
Help the student find the main idea of this passage:

{passage}

Explain it using the 6 sections.
Keep OVERVIEW and KEY FACTS short and simple.
In PRACTICE, include 1–2 tiny questions the student can answer.
"""


# -------------------------------------------------------
# General reading task prompt
# -------------------------------------------------------
def build_task_prompt(task: str, grade_level: str):
    return f"""
Help the student with this reading task:

{task}

Use the 6-section Homework Buddy structure.
Keep everything gentle, simple, and easy for a grade {grade_level} student.
Include a short PRACTICE section.
"""


# -------------------------------------------------------
# Helper for extracting SECTION text
# -------------------------------------------------------
def extract_section(raw: str, label: str) -> str:
    if label not in raw:
        return "Not available."
    return raw.split(label)[-1].strip()


# -------------------------------------------------------
# PUBLIC FUNCTIONS — SOCratic + STRUCTURED FORMAT
# -------------------------------------------------------

def summarize_text(text: str, grade_level="8", character=None):

    if character is None:
        character = "theo"

    # Christian worldview
    if is_christian_question(text):
        base_prompt = f"""
The student wants a Christian-friendly explanation of this passage:

{text}

Explain using the 6 structured sections.
Keep everything gentle and clear.
"""
    else:
        base_prompt = build_summary_prompt(text, grade_level)

    full_prompt = socratic_layer(text, grade_level) + "\n" + base_prompt
    enriched = apply_personality(character, full_prompt)

    raw = study_buddy_ai(enriched, grade_level, character)

    return format_answer(
        overview=extract_section(raw, "SECTION 1"),
        key_facts=extract_section(raw, "SECTION 2"),
        christian_view=extract_section(raw, "SECTION 3"),
        agreement=extract_section(raw, "SECTION 4"),
        difference=extract_section(raw, "SECTION 5"),
        practice=extract_section(raw, "SECTION 6")
    )


def reading_help(question: str, passage: str, grade_level="8", character=None):

    if character is None:
        character = "theo"

    if is_christian_question(question + " " + passage):
        base_prompt = f"""
The student wants reading help with a Christian perspective.

Passage:
{passage}

Question:
{question}

Explain using the 6-section Homework Buddy format.
"""
    else:
        base_prompt = build_comprehension_prompt(question, passage, grade_level)

    full_prompt = socratic_layer(question, grade_level) + "\n" + base_prompt
    enriched = apply_personality(character, full_prompt)

    raw = study_buddy_ai(enriched, grade_level, character)

    return format_answer(
        overview=extract_section(raw, "SECTION 1"),
        key_facts=extract_section(raw, "SECTION 2"),
        christian_view=extract_section(raw, "SECTION 3"),
        agreement=extract_section(raw, "SECTION 4"),
        difference=extract_section(raw, "SECTION 5"),
        practice=extract_section(raw, "SECTION 6")
    )


def find_main_idea(passage: str, grade_level="8", character=None):

    if character is None:
        character = "theo"

    if is_christian_question(passage):
        base_prompt = f"""
Help the student find the main idea and include a gentle Christian viewpoint.

Passage:
{passage}

Use the 6 structured sections.
"""
    else:
        base_prompt = build_main_idea_prompt(passage, grade_level)

    full_prompt = socratic_layer(passage, grade_level) + "\n" + base_prompt
    enriched = apply_personality(character, full_prompt)

    raw = study_buddy_ai(enriched, grade_level, character)

    return format_answer(
        overview=extract_section(raw, "SECTION 1"),
        key_facts=extract_section(raw, "SECTION 2"),
        christian_view=extract_section(raw, "SECTION 3"),
        agreement=extract_section(raw, "SECTION 4"),
        difference=extract_section(raw, "SECTION 5"),
        practice=extract_section(raw, "SECTION 6")
    )


def help_with_reading_task(task: str, grade_level="8", character=None):

    if character is None:
        character = "theo"

    if is_christian_question(task):
        base_prompt = f"""
The student wants this reading task explained with a Christian-friendly tone:

{task}

Use the 6 Homework Buddy structured sections.
"""
    else:
        base_prompt = build_task_prompt(task, grade_level)

    full_prompt = socratic_layer(task, grade_level) + "\n" + base_prompt
    enriched = apply_personality(character, full_prompt)

    raw = study_buddy_ai(enriched, grade_level, character)

    return format_answer(
        overview=extract_section(raw, "SECTION 1"),
        key_facts=extract_section(raw, "SECTION 2"),
        christian_view=extract_section(raw, "SECTION 3"),
        agreement=extract_section(raw, "SECTION 4"),
        difference=extract_section(raw, "SECTION 5"),
        practice=extract_section(raw, "SECTION 6")
    )
