# modules/science_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -------------------------
# Detect Christian-related question
# -------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "Christian", "Christianity", "God", "Jesus", "Bible",
        "biblical", "creation", "faith",
        "Christian perspective",
        "from a Christian view",
        "how does this relate to Christianity",
        "how does this relate to God"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -------------------------
# Grade-Level Science Topics (guiding difficulty)
# -------------------------
SCIENCE_TOPICS = {
    "1": ["plants", "animals", "senses", "weather", "seasons"],
    "2": ["habitats", "life cycles", "basic forces", "energy", "earth materials"],
    "3": ["ecosystems", "adaptations", "simple machines", "solar system"],
    "4": ["energy transfer", "waves", "erosion", "motion"],
    "5": ["cells", "matter", "ecosystems", "earth systems"],
    "6": ["atoms", "molecules", "forces", "heat", "weather systems"],
    "7": ["genetics", "chemical reactions", "ecology", "body systems"],
    "8": ["forces and motion", "energy", "earth history", "chemistry basics"],
    "9": ["biology", "earth science", "physics basics"],
    "10": ["chemistry", "biology", "ecology", "geology"],
    "11": ["physics", "genetics", "cell biology"],
    "12": ["advanced physics", "advanced chemistry", "environmental science"]
}


# -------------------------------------------------------------
# EXPLAIN A SCIENCE TOPIC (FULL LESSON)
# -------------------------------------------------------------
def explain_science(topic: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    # If student wants Christian perspective
    if is_christian_question(topic):
        christian_prompt = f"""
The student asked how this science topic connects to Christianity.

Topic: {topic}

Offer a gentle explanation:
Explain that science studies the natural world and how it works.
Explain that many Christians appreciate science because they see the natural world as something created with order and purpose.
Avoid claiming that the Bible teaches modern scientific models or theories.
Keep it simple and appropriate for grade {grade_level}.

Do not teach the science lesson here. Only address the Christian connection.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    grade_topics = ", ".join(SCIENCE_TOPICS.get(str(grade_level), []))

    prompt = f"""
Teach the science topic: {topic}
Student grade level: {grade_level}

Use a gentle, calm, conversational tone. Avoid dramatic or energetic wording.
Be patient, clear, and friendly.

Include:
A simple overview
A step-by-step explanation of the idea
A couple worked examples or real-life applications
Key ideas to remember
Five practice questions
Then the answers

Write naturally, like you are sitting beside the student and helping them understand.

Grade level reference topics: {grade_topics}
Use this list to choose the right difficulty.
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


# -------------------------------------------------------------
# ANSWER GENERAL SCIENCE QUESTIONS
# -------------------------------------------------------------
def answer_science_question(question: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    # Christian worldview version
    if is_christian_question(question):
        christian_prompt = f"""
The student asked about this science question from a Christian perspective.

Question: {question}

Explain gently:
Science explains how the natural world works.
Christians see scientific order and patterns as signs of a world created with structure and purpose.
Do not claim that the Bible directly teaches modern scientific concepts.
Keep the tone soft and simple.

Do not answer the science question itself here, unless the student directly asks for both explanations.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    # Standard explanation
    prompt = f"""
Answer the following science question for a grade {grade_level} student in a calm, conversational way.

Question: {question}

Explain:
What the question is really asking
The answer in clear, simple reasoning
One short example or illustration
One helpful reminder for similar questions

Keep things warm, patient, and easy to follow.
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


# -------------------------------------------------------------
# GENERATE A SCIENCE QUIZ
# -------------------------------------------------------------
def generate_science_quiz(topic: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    # Christian worldview quiz
    if is_christian_question(topic):
        christian_prompt = f"""
The student asked for a Christian perspective on this science topic before a quiz.

Topic: {topic}

Begin with a short gentle explanation that many Christians appreciate the order of nature.
Then provide three simple science questions and an answer key.
Keep everything age-appropriate.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    prompt = f"""
Create a short science quiz for the topic: {topic}
Grade level: {grade_level}

Speak in a gentle, patient, conversational tone.
Include five questions and then an answer key.
Keep the difficulty appropriate for grade {grade_level}.
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


