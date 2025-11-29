# modules/money_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import format_answer


# ------------------------------------------------------------
# Detect Christian-oriented money questions
# ------------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "christianity", "bible", "jesus", "god",
        "biblical", "stewardship", "christian perspective",
        "christian worldview", "what does the bible say",
        "how does this relate to god"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# ------------------------------------------------------------
# Build 6-section prompt for general money topics
# ------------------------------------------------------------
def build_money_prompt(topic: str, grade: str):
    return f"""
You are a gentle money teacher for a grade {grade} student.

The student asked about:
"{topic}"

Answer using SIX calm and kid-friendly sections.

SECTION 1 — OVERVIEW
Explain the money idea in a few slow and simple sentences.

SECTION 2 — KEY FACTS
Explain the important everyday ideas like earning, saving,
budgeting, spending, and choosing between needs and wants.
Use small calm sentences, not lists.

SECTION 3 — CHRISTIAN VIEW
Explain softly how many Christians see money as something to manage
wisely with responsibility, generosity, and gratitude.

SECTION 4 — AGREEMENT
Explain what people of any worldview agree about, such as planning,
saving, avoiding debt problems, and being responsible.

SECTION 5 — DIFFERENCE
Explain gently how Christian stewardship adds a different sense of
purpose or motivation for using money wisely.

SECTION 6 — PRACTICE
Ask two or three tiny reflection questions and give very short
example answers.

Keep everything slow, warm, and simple.
"""


# ------------------------------------------------------------
# Build 6-section prompt for Christian-directed questions
# ------------------------------------------------------------
def build_christian_money_prompt(topic: str, grade: str):
    return f"""
The student asked this money question from a Christian perspective:

"{topic}"

Answer using SIX calm, gentle sections.

SECTION 1 — OVERVIEW
Explain the question in slow, everyday words.

SECTION 2 — KEY FACTS
Explain the important ideas involved in the topic such as saving,
spending, planning, and responsibility.

SECTION 3 — CHRISTIAN VIEW
Explain softly how many Christians understand money as stewardship.
You may mention ideas like honesty, generosity, and wisdom.

SECTION 4 — AGREEMENT
Explain what all people agree on regarding money regardless
of worldview.

SECTION 5 — DIFFERENCE
Explain gently how Christian motivations may differ from a
purely secular view of money.

SECTION 6 — PRACTICE
Ask 2–3 tiny reflection questions with simple example answers.

Keep the tone warm, slow, and safe for a young student.
"""


# ------------------------------------------------------------
# Extract helper — consistent with all other helpers
# ------------------------------------------------------------
def _extract_section(raw: str, label: str) -> str:
    return raw.split(label)[-1].strip() if label in raw else "No information provided."


# ------------------------------------------------------------
# Main Money Explanation
# ------------------------------------------------------------
def explain_money(topic: str, grade_level="8", character="everly"):
    christian = is_christian_question(topic)

    if christian:
        prompt = build_christian_money_prompt(topic, grade_level)
    else:
        prompt = build_money_prompt(topic, grade_level)

    # Add character personality
    prompt = apply_personality(character, prompt)

    # Ask AI
    raw = study_buddy_ai(prompt, grade_level, character)

    # Extract six sections
    overview       = _extract_section(raw, "SECTION 1")
    key_facts      = _extract_section(raw, "SECTION 2")
    christian_view = _extract_section(raw, "SECTION 3")
    agreement      = _extract_section(raw, "SECTION 4")
    difference     = _extract_section(raw, "SECTION 5")
    practice       = _extract_section(raw, "SECTION 6")

    # Format for HTML
    return format_answer(
        overview=overview,
        key_facts=key_facts,
        christian_view=christian_view,
        agreement=agreement,
        difference=difference,
        practice=practice
    )


# ------------------------------------------------------------
# Solve Accounting Problem — 6-section format
# ------------------------------------------------------------
def solve_accounting_problem(problem: str, grade_level="8", character="everly"):

    prompt = f"""
You are a gentle accounting tutor for a grade {grade_level} student.

The student asked:
"{problem}"

Use SIX warm, simple sections.

SECTION 1 — OVERVIEW
Rephrase the problem in slow, everyday words.

SECTION 2 — KEY FACTS
Explain the basic accounting ideas the problem uses such as
assets, expenses, revenues, liabilities, or debits and credits.

SECTION 3 — CHRISTIAN VIEW
Softly explain how Christians view honesty, stewardship,
and responsibility in managing money.

SECTION 4 — AGREEMENT
Explain what all worldviews agree about in accounting such as keeping
track of money, being responsible, and avoiding mistakes.

SECTION 5 — DIFFERENCE
Explain gently how Christian stewardship can add deeper meaning
to responsible financial decision-making.

SECTION 6 — PRACTICE
Walk through the solution in slow steps and then give 2 tiny
practice problems with example answers.

Keep everything calm and very simple.
"""

    # Apply personality
    prompt = apply_personality(character, prompt)

    # Call AI
    raw = study_buddy_ai(prompt, grade_level, character)

    # Extract
    overview       = _extract_section(raw, "SECTION 1")
    key_facts      = _extract_section(raw, "SECTION 2")
    christian_view = _extract_section(raw, "SECTION 3")
    agreement      = _extract_section(raw, "SECTION 4")
    difference     = _extract_section(raw, "SECTION 5")
    practice       = _extract_section(raw, "SECTION 6")

    return format_answer(
        overview=overview,
        key_facts=key_facts,
        christian_view=christian_view,
        agreement=agreement,
        difference=difference,
        practice=practice
    )


# ------------------------------------------------------------
# Accounting Quiz — 6-section format
# ------------------------------------------------------------
def accounting_quiz(topic: str, grade_level="8", character="everly"):

    prompt = f"""
Create a warm, calm money quiz for grade {grade_level}.

Topic:
"{topic}"

Use SIX SECTIONS.

SECTION 1 — OVERVIEW
Short gentle explanation of the topic.

SECTION 2 — KEY FACTS
Simple core ideas the student should understand.

SECTION 3 — CHRISTIAN VIEW
Soft explanation of stewardship and responsibility.

SECTION 4 — AGREEMENT
What all worldviews agree about money.

SECTION 5 — DIFFERENCE
How Christian motivations may differ from secular motivations.

SECTION 6 — PRACTICE
Write a few tiny quiz questions followed by short example answers
in natural kid-friendly language.

Tone must stay warm, slow, and child-friendly.
"""

    prompt = apply_personality(character, prompt)
    raw = study_buddy_ai(prompt, grade_level, character)

    overview       = _extract_section(raw, "SECTION 1")
    key_facts      = _extract_section(raw, "SECTION 2")
    christian_view = _extract_section(raw, "SECTION 3")
    agreement      = _extract_section(raw, "SECTION 4")
    difference     = _extract_section(raw, "SECTION 5")
    practice       = _extract_section(raw, "SECTION 6")

    return format_answer(
        overview=overview,
        key_facts=key_facts,
        christian_view=christian_view,
        agreement=agreement,
        difference=difference,
        practice=practice
    )





