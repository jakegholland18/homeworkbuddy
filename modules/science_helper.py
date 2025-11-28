# modules/science_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -------------------------------------------------------
# Detect Christian-related science questions
# -------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "christian", "christianity", "god", "jesus", "bible",
        "biblical", "creation", "faith",
        "christian perspective",
        "from a christian view",
        "how does this relate to christianity",
        "how does this relate to god"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -------------------------------------------------------
# Socratic Tutor Layer (used on all explanations)
# -------------------------------------------------------
def socratic_layer(base_explanation: str, question: str, grade_level: str):
    """
    Wraps any explanation inside Socratic guidance:
    restate → hint → guiding question → small nudge → full explanation.
    """

    return f"""
A student asked: "{question}"

Before teaching the full explanation, help the student think on their own.

Start by restating the question in simple, kid-friendly language so they feel understood.

Then offer a small hint that gently points them in the right direction.

Next, ask a guiding question that gets them thinking about what they already know
about nature, science, or the world around them.

After that, give a soft nudge that helps them move closer to the idea
without revealing the whole explanation too early.

Once you have guided their thinking step-by-step,
transition naturally into the full explanation below.

Full Explanation:
{base_explanation}

End with a warm, encouraging summary written at a grade {grade_level} level
that reassures them it is wonderful to be curious about how the world works.
"""


# -------------------------------------------------------
# Grade-Level Science Topics
# -------------------------------------------------------
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
# EXPLAIN A SCIENCE TOPIC (FULL LESSON w/ Socratic tutoring)
# -------------------------------------------------------------
def explain_science(topic: str, grade_level="8", character=None):

    if character is None:
        character = "valor_strike"

    # Christian worldview requested
    if is_christian_question(topic):
        christian_base = f"""
The student asked how this science topic relates to Christianity.

Topic: {topic}

Explain gently that science studies the natural world and helps us understand
how things work by observing patterns, gathering evidence, and testing ideas.

Explain that many Christians appreciate science because they see the natural world
as something created with order and purpose, but avoid claiming that the Bible
teaches modern scientific theories.

Keep the tone warm, simple, and respectful.
"""
        prompt = socratic_layer(christian_base, topic, grade_level)
        prompt = apply_personality(character, prompt)
        return study_buddy_ai(prompt, grade_level, character)

    # Standard science explanation
    grade_topics = ", ".join(SCIENCE_TOPICS.get(str(grade_level), []))

    base_prompt = f"""
Teach the science topic: {topic}
Grade level: {grade_level}

Use a calm, patient, conversational voice.
Avoid energetic or dramatic language.

Include a simple overview, gentle step-by-step thinking,
and real-world examples that help the idea make sense.
Explain key ideas in plain language, then guide the student 
through a few practice questions and answers in a natural,
spoken tone without lists or headings.

Grade-level reference topics include: {grade_topics}
Use this to match the difficulty.
"""

    guided_prompt = socratic_layer(base_prompt, topic, grade_level)
    guided_prompt = apply_personality(character, guided_prompt)
    return study_buddy_ai(guided_prompt, grade_level, character)


# -------------------------------------------------------------
# ANSWER A SCIENCE QUESTION (Socratic + Personality)
# -------------------------------------------------------------
def answer_science_question(question: str, grade_level="8", character=None):

    if character is None:
        character = "valor_strike"

    # Christian worldview version
    if is_christian_question(question):
        christian_base = f"""
The student asked about this science question from a Christian perspective.

Question: {question}

Explain gently:
Science describes how the natural world works.
Many Christians see scientific patterns and order as signs of a world created with consistency.
Avoid claiming that Scripture directly teaches modern scientific theories.

Speak in a warm, calm tone for a grade {grade_level} student.
"""
        guided_prompt = socratic_layer(christian_base, question, grade_level)
        guided_prompt = apply_personality(character, guided_prompt)
        return study_buddy_ai(guided_prompt, grade_level, character)

    # Standard explanation
    base_prompt = f"""
Answer this science question for a grade {grade_level} student
using a slow, friendly, conversational tone:

{question}

Explain what the question is asking,
walk through the idea step by step in natural language,
give a gentle example, and offer one small reminder.
"""
    guided_prompt = socratic_layer(base_prompt, question, grade_level)
    guided_prompt = apply_personality(character, guided_prompt)
    return study_buddy_ai(guided_prompt, grade_level, character)


# -------------------------------------------------------------
# GENERATE A SCIENCE QUIZ (Socratic + Personality)
# -------------------------------------------------------------
def generate_science_quiz(topic: str, grade_level="8", character=None):

    if character is None:
        character = "valor_strike"

    # Christian worldview quiz
    if is_christian_question(topic):
        christian_base = f"""
The student wants a Christian perspective before a small science quiz.

Topic: {topic}

Explain gently that many Christians appreciate the order in nature.
Then offer several gentle practice questions and a conversational answer key.
"""
        guided_prompt = socratic_layer(christian_base, topic, grade_level)
        guided_prompt = apply_personality(character, guided_prompt)
        return study_buddy_ai(guided_prompt, grade_level, character)

    # Standard quiz
    base_prompt = f"""
Create a soft, conversational science quiz for the topic: {topic}
Grade level: {grade_level}

Ask five gentle practice questions in spoken, natural language.
Then offer an answer key in the same tone.
"""
    guided_prompt = socratic_layer(base_prompt, topic, grade_level)
    guided_prompt = apply_personality(character, guided_prompt)
    return study_buddy_ai(guided_prompt, grade_level, character)



