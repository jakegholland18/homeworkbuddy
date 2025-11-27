# modules/history_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -------------------------
# Detect Christian-oriented questions
# -------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "Christian", "Christianity", "God", "Jesus", "Bible",
        "biblical", "faith", "from a Christian perspective",
        "Christian worldview", "how does this relate to Christianity",
        "how does this relate to God"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -------------------------
# Grade-Level History Topics (for difficulty guidance)
# -------------------------
HISTORY_TOPICS = {
    "1": ["families", "communities", "holidays", "basic timelines"],
    "2": ["local history", "famous Americans", "geography basics"],
    "3": ["early American history", "Native cultures", "maps", "civics"],
    "4": ["state history", "colonial times", "revolutions"],
    "5": ["US history overview", "exploration", "founding documents"],
    "6": ["ancient civilizations", "world religions overview", "government basics"],
    "7": ["middle ages", "renaissance", "early world exploration"],
    "8": ["US Constitution", "American government", "civil war", "industrial era"],
    "9": ["world history", "ancient to medieval", "global empires"],
    "10": ["modern world history", "world wars", "global conflicts"],
    "11": ["US history in depth", "government systems", "civil rights"],
    "12": ["economics basics", "modern global issues", "advanced civics"]
}


# -------------------------------------------------------------
# FULL HISTORY LESSON
# -------------------------------------------------------------
def explain_history(topic: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    # Christian worldview requested
    if is_christian_question(topic):
        christian_prompt = f"""
The student asked for a Christian perspective related to this history topic.

Topic: {topic}

Provide a gentle explanation:
Explain that history describes what happened in different times and cultures.
Explain that many Christians view historical events through the belief that people have moral choices and that human history shows both good and harmful actions.
Keep it calm, balanced, and age-appropriate for grade {grade_level}.

Do not teach the full history lesson here. Only give the worldview connection.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    grade_topics = ", ".join(HISTORY_TOPICS.get(str(grade_level), []))

    prompt = f"""
Teach the history topic: {topic}
Grade level: {grade_level}

Speak gently and conversationally, as if sitting beside the student.
Do not use dramatic language or intense emotion.
Keep the explanation steady, clear, and calm.

Include:
A simple overview of the topic
A step-by-step explanation of the main ideas
A couple of real-world examples or events connected to the topic
Important ideas to remember
Five practice questions
Then the answers

Keep everything age-appropriate and easy to follow.

Grade-level guidance topics: {grade_topics}
Use these to choose the right difficulty.
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


# -------------------------------------------------------------
# ANSWER GENERAL HISTORY QUESTIONS
# -------------------------------------------------------------
def answer_history_question(question: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    if is_christian_question(question):
        christian_prompt = f"""
The student asked about this history question from a Christian viewpoint.

Question: {question}

Explain gently:
That history shows how people have made choices, built societies, and shaped cultures.
Christians see history as influenced by human responsibility, moral decisions, and long-term consequences.
Show how archaeology today confirms what the Bible teaches.
Keep the tone soft, balanced, and simple.

Do not answer the historical question itself unless the student directly requests both perspective and facts.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    prompt = f"""
Answer this history question for a grade {grade_level} student using calm,
simple, conversational teaching.

Question: {question}

Include:
A clear explanation of what the question is asking
A gentle, step-by-step answer
A short example or illustration
A helpful reminder for similar questions

Avoid excitement, dramatic stories, or intense descriptions.
Keep it peaceful and easy to understand.
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


# -------------------------------------------------------------
# GENERATE HISTORY QUIZ
# -------------------------------------------------------------
def generate_history_quiz(topic: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    if is_christian_question(topic):
        christian_prompt = f"""
The student asked about this history topic from a Christian perspective.

Topic: {topic}

Begin with a short explanation of how Christians view human events
as shaped by choices, responsibility, and long-term consequences.

Then provide three gentle history questions and an answer key.
Keep everything calm and age-appropriate.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    prompt = f"""
Create a short history quiz about: {topic}
Grade level: {grade_level}

Speak gently and conversationally.
Include five questions and then the answer key.
Keep the difficulty suitable for a grade {grade_level} student.
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)

