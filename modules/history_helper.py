# modules/history_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -------------------------------------------------------------
# Detect Christian-oriented history questions
# -------------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "christianity", "god", "jesus", "bible",
        "biblical", "faith", "from a christian perspective",
        "christian worldview", "how does this relate to christianity",
        "how does this relate to god"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -------------------------------------------------------------
# Grade-level guidance topics (difficulty shaping)
# -------------------------------------------------------------
HISTORY_TOPICS = {
    "1": ["families", "communities", "holidays", "basic timelines"],
    "2": ["local history", "famous americans", "geography basics"],
    "3": ["early american history", "native cultures", "maps", "civics"],
    "4": ["state history", "colonial times", "revolutions"],
    "5": ["us history overview", "exploration", "founding documents"],
    "6": ["ancient civilizations", "world religions overview", "government basics"],
    "7": ["middle ages", "renaissance", "early world exploration"],
    "8": ["us constitution", "american government", "civil war", "industrial era"],
    "9": ["world history", "ancient to medieval", "global empires"],
    "10": ["modern world history", "world wars", "global conflicts"],
    "11": ["us history in depth", "government systems", "civil rights"],
    "12": ["economics basics", "modern global issues", "advanced civics"]
}


# -------------------------------------------------------------
# SOCRATIC TUTOR LAYER (used for ALL history answers)
# -------------------------------------------------------------
def socratic_layer(base_explanation: str, question: str, grade_level: str):
    """
    Wraps the final explanation in a guided Socratic style
    before giving the full answer.
    """

    return f"""
A student asked: "{question}"

Begin by helping the student think for themselves without giving the full answer yet.

First, restate what the question is really asking in gentle, kid-friendly language.

Next, offer one helpful hint that nudges them toward the idea without revealing it.

Then, ask a guiding question that makes them think more deeply
about the historical situation, the people involved, or the causes/effects.

After that, give one more small nudge—still avoiding the full explanation.

Only after these steps, transition naturally into the full history explanation below.

Full Explanation:
{base_explanation}

End with a warm, simple summary that encourages a grade {grade_level} student
to keep asking thoughtful questions about history.
"""


# -------------------------------------------------------------
# FULL HISTORY LESSON
# -------------------------------------------------------------
def explain_history(topic: str, grade_level="8", character=None):

    if character is None:
        character = "valor_strike"

    # Christian worldview requested
    if is_christian_question(topic):
        base_prompt = f"""
The student requested a Christian perspective on this history topic:

{topic}

Explain gently how many Christians see history as the story of human choices,
responsibility, moral consequences, and God working through imperfect people.
Keep it calm and age-appropriate.
"""
        guided_prompt = socratic_layer(base_prompt, topic, grade_level)
        enriched_prompt = apply_personality(character, guided_prompt)
        return study_buddy_ai(enriched_prompt, grade_level, character)

    grade_topics = ", ".join(HISTORY_TOPICS.get(str(grade_level), []))

    base_prompt = f"""
Teach the history topic: {topic}
Grade level: {grade_level}

Explain the topic gently and conversationally:
Give a simple overview.
Guide the student through the main ideas step by step.
Use calm examples.
Never use dramatic or intense language.

Keep it suitable for grade {grade_level}.

Grade-level guidance topics: {grade_topics}
"""

    guided_prompt = socratic_layer(base_prompt, topic, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)
    return study_buddy_ai(enriched_prompt, grade_level, character)


# -------------------------------------------------------------
# ANSWER GENERAL HISTORY QUESTIONS
# -------------------------------------------------------------
def answer_history_question(question: str, grade_level="8", character=None):

    if character is None:
        character = "valor_strike"

    # Christian worldview perspective
    if is_christian_question(question):
        base_prompt = f"""
The student asked about this history question from a Christian perspective:

{question}

Explain gently how Christians see history as shaped by human choices,
responsibility, and long-term consequences.
You may mention that archaeology often supports biblical events,
but keep it soft, not argumentative.
"""
        guided_prompt = socratic_layer(base_prompt, question, grade_level)
        enriched_prompt = apply_personality(character, guided_prompt)
        return study_buddy_ai(enriched_prompt, grade_level, character)

    # Normal history question
    base_prompt = f"""
The student is asking a history question suitable for grade {grade_level}:

{question}

Give a calm, clear explanation.
Use gentle examples.
No dramatic or intense wording.
Keep it simple and supportive.
"""

    guided_prompt = socratic_layer(base_prompt, question, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)
    return study_buddy_ai(enriched_prompt, grade_level, character)


# -------------------------------------------------------------
# HISTORY QUIZ GENERATOR
# -------------------------------------------------------------
def generate_history_quiz(topic: str, grade_level="8", character=None):

    if character is None:
        character = "valor_strike"

    if is_christian_question(topic):
        base_prompt = f"""
The student wants a Christian perspective history quiz.

Topic: {topic}

Start with a short explanation of how Christians view human events
as shaped by moral choices and consequences.

Then create three gentle quiz questions plus answers.
Keep everything calm, simple, and age-appropriate.
"""
        guided_prompt = socratic_layer(base_prompt, topic, grade_level)
        enriched_prompt = apply_personality(character, guided_prompt)
        return study_buddy_ai(enriched_prompt, grade_level, character)

    base_prompt = f"""
Create a calm, age-appropriate history quiz about:

{topic}

Include five gentle questions and then the answer key.
Suit the difficulty for grade {grade_level}.
No dramatic language.
"""

    guided_prompt = socratic_layer(base_prompt, topic, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)
    return study_buddy_ai(enriched_prompt, grade_level, character)


