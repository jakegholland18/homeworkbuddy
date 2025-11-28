# modules/math_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -----------------------------------------------------------
# Detect Christian-related question
# -----------------------------------------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "Christian", "Christianity", "God", "Jesus", "Bible",
        "biblical", "faith", "Christian perspective",
        "how does this relate to Christianity",
        "how does this relate to God"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -----------------------------------------------------------
# Math curriculum difficulty guide
# -----------------------------------------------------------
MATH_TOPICS = {
    "1": ["counting", "addition", "subtraction", "shapes", "time"],
    "2": ["addition", "subtraction", "money", "graphs", "arrays"],
    "3": ["multiplication", "division", "fractions basics", "area"],
    "4": ["long division", "fractions", "decimals"],
    "5": ["fractions operations", "volume", "decimals"],
    "6": ["ratio", "rates", "percent", "equations"],
    "7": ["proportions", "rational numbers", "probability"],
    "8": ["linear equations", "functions", "exponents"],
    "9": ["algebra", "quadratics", "polynomials"],
    "10": ["geometry", "similarity", "trigonometry basics"],
    "11": ["algebra II", "logarithms", "rational functions"],
    "12": ["precalculus", "calculus intro", "limits"]
}


# -----------------------------------------------------------
# SOCRATIC TUTOR LAYER
# -----------------------------------------------------------
def socratic_layer(base_explanation: str, question: str, grade_level: str):
    """
    Helps the student think first, then learn:
    restate → hint → guiding question → gentle nudge → full explanation.
    """

    return f"""
A student asked a math question: "{question}"

Begin by helping the student think before giving the full answer.

First, restate the problem or topic in gentle, kid-friendly language.

Next, offer a helpful hint that points them in the right direction
without solving anything yet.

Then ask a guiding question that helps them think about the structure
of the problem or how numbers relate to each other.

After that, give a small nudge—just enough to help them make progress
if they are stuck, but still not giving away the final explanation.

Only after these steps should you transition into the full math explanation below.

Full Explanation:
{base_explanation}

End with a soft, encouraging summary written for a grade {grade_level} student,
reassuring them that learning math is a step-by-step process and they are doing well.
"""


# -----------------------------------------------------------
# EXPLAIN A MATH TOPIC — SOCIATIC + PERSONALITY
# -----------------------------------------------------------
def explain_math(topic: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    # Christian worldview request
    if is_christian_question(topic):
        christian_prompt = f"""
The student asked how this math idea connects to Christianity.

Topic: {topic}

Explain gently and briefly.
Say that math itself is academically neutral,
and some Christians see its order and reliability
as reflecting structure in creation.
Avoid claiming that the Bible teaches modern math topics.
Use a warm, simple tone suitable for grade {grade_level}.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    grade_topics = ", ".join(MATH_TOPICS.get(str(grade_level), []))

    base_prompt = f"""
Teach the math topic: {topic}
Grade level: {grade_level}

Speak in a calm, conversational tone.

Include:
A short overview of the idea.
A step-by-step explanation in simple language.
A couple of worked examples explained clearly.
A gentle reminder of key ideas.
Five practice problems.
Then the answers.

Avoid symbols like bullet points or dashes. Use soft line breaks instead.

Grade {grade_level} typically learns: {grade_topics}
Use this for difficulty guidance.
"""

    # Wrap in Socratic method
    guided_prompt = socratic_layer(base_prompt, topic, grade_level)

    # Character personality
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


# -----------------------------------------------------------
# SOLVE A MATH PROBLEM (Socratic)
# -----------------------------------------------------------
def solve_math_problem(problem: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    # Christian worldview check
    if is_christian_question(problem):
        christian_prompt = f"""
The student asked how this math problem relates to Christianity.

Problem: {problem}

Explain gently that math is neutral as a school subject,
and Christians often see the order and consistency in math
as reflecting order in creation.

Keep it short and do not solve the math steps in this mode.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    base_prompt = f"""
Solve this math problem step by step in a calm, conversational voice.

Problem: {problem}

Include:
A gentle restatement of what the problem is asking.
Step-by-step reasoning using simple language.
The final answer clearly stated.
One short tip for similar problems.
"""

    guided_prompt = socratic_layer(base_prompt, problem, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


# -----------------------------------------------------------
# GENERATE A MATH QUIZ (Socratic)
# -----------------------------------------------------------
def generate_math_quiz(topic: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    # Christian worldview request
    if is_christian_question(topic):
        christian_prompt = f"""
The student asked how this math topic relates to Christianity.

Topic: {topic}

Gently explain how Christians sometimes see math as reflecting
order and structure in the world.

Then provide three simple practice questions and a short answer key.
Keep the tone warm and calm.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    base_prompt = f"""
Create a short math quiz about: {topic}

Write in a gentle, spoken tone.
Give five practice questions.
After a short pause, provide the answers.

Grade level: {grade_level}
"""

    guided_prompt = socratic_layer(base_prompt, topic, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)

    return study_buddy_ai(enriched_prompt, grade_level, character)


