# modules/question_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import format_answer


# -------------------------------------------------------
# Detect whether the question is Christian-oriented
# -------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "christianity", "jesus", "god", "faith",
        "biblical", "bible",
        "how does this relate to god",
        "from a christian perspective",
        "christian worldview"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -------------------------------------------------------
# Six-section extractor (UNIFIED across all helpers)
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
# Build 6-section prompt (general)
# -------------------------------------------------------
def build_general_prompt(question: str, grade: str):
    return f"""
The student asked this question:

\"{question}\"

Answer using SIX gentle sections
(Overview, Key Facts, Christian View, Agreement, Difference, Practice).

Tone:
warm, simple, kid-friendly, slow, grade {grade} level.
"""


# -------------------------------------------------------
# Build 6-section prompt (Christian)
# -------------------------------------------------------
def build_christian_prompt(question: str, grade: str):
    return f"""
The student asked this question from a Christian perspective:

\"{question}\"

Answer using SIX gentle sections
(Overview, Key Facts, Christian View, Agreement, Difference, Practice).

Keep tone warm and respectful.
Use Scripture softly only if helpful.
"""


# -------------------------------------------------------
# MAIN PUBLIC FUNCTION
# -------------------------------------------------------
def answer_question(question: str, grade_level="8", character="everly"):

    if is_christian_question(question):
        prompt = build_christian_prompt(question, grade_level)
    else:
        prompt = build_general_prompt(question, grade_level)

    prompt = apply_personality(character, prompt)

    ai_text = study_buddy_ai(prompt, grade_level, character)

    sections = extract_sections(ai_text)

    return format_answer(
        overview=sections.get("overview", ""),
        key_facts=sections.get("key_facts", ""),
        christian_view=sections.get("christian_view", ""),
        agreement=sections.get("agreement", ""),
        difference=sections.get("difference", ""),
        practice=sections.get("practice", "")
    )
