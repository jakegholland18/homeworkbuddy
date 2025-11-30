# modules/science_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import format_answer


# -------------------------------------------------------
# Detect Christian-oriented science questions
# -------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "christianity", "god", "jesus", "bible",
        "biblical", "creation", "faith",
        "christian perspective", "christian view",
        "how does this relate to christianity",
        "how does this relate to god"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -------------------------------------------------------
# SECTION EXTRACTOR — Unified across all helpers
# -------------------------------------------------------
def extract_sections(ai_text: str):
    def extract(label):
        if label not in ai_text:
            return "Not available."

        start = ai_text.find(label) + len(label)
        end = len(ai_text)

        # Stop at next section header
        for nxt in ["SECTION 1", "SECTION 2", "SECTION 3",
                    "SECTION 4", "SECTION 5", "SECTION 6"]:
            pos = ai_text.find(nxt, start)
            if pos != -1 and pos < end:
                end = pos

        return ai_text[start:end].strip()

    return {
        "overview": extract("SECTION 1"),
        "key_facts": extract("SECTION 2"),
        "christian_view": extract("SECTION 3"),
        "agreement": extract("SECTION 4"),
        "difference": extract("SECTION 5"),
        "practice": extract("SECTION 6"),
    }


# -------------------------------------------------------
# Build science prompt (standard)
# -------------------------------------------------------
def build_science_prompt(topic: str, grade_level: str):
    return f"""
The student asked a science question:

\"{topic}\"

Explain it using SIX gentle sections:
Overview, Key Facts, Christian View, Agreement, Difference, Practice.

Tone:
calm, slow, warm, kid-friendly, grade {grade_level}.
"""


# -------------------------------------------------------
# Build Christian-directed science prompt
# -------------------------------------------------------
def build_christian_science_prompt(topic: str, grade_level: str):
    return f"""
The student asked this science question from a Christian perspective:

\"{topic}\"

Use SIX warm, gentle sections:
Overview, Key Facts, Christian View, Agreement, Difference, Practice.

Keep Scripture soft and only if natural.
"""


# -------------------------------------------------------
# MAIN PUBLIC FUNCTION — FIXED FOR NEW 6-SECTION SYSTEM
# -------------------------------------------------------
def explain_science(topic: str, grade_level="8", character="everly"):

    # Choose prompt style
    if is_christian_question(topic):
        prompt = build_christian_science_prompt(topic, grade_level)
    else:
        prompt = build_science_prompt(topic, grade_level)

    # Add personality
    prompt = apply_personality(character, prompt)

    # Get AI output (already structured text)
    ai_text = study_buddy_ai(prompt, grade_level, character)

    # Extract unified sections
    sections = extract_sections(ai_text)

    # Format for HTML template
    return format_answer(
        overview=sections.get("overview", ""),
        key_facts=sections.get("key_facts", ""),
        christian_view=sections.get("christian_view", ""),
        agreement=sections.get("agreement", ""),
        difference=sections.get("difference", ""),
        practice=sections.get("practice", "")
    )

