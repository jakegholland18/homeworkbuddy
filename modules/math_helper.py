# modules/math_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -------------------------
# Detect Christian-related question
# -------------------------
def is_christian_question(text: str) -> bool:
    keywords = [
        "Christian", "Christianity", "God", "Jesus", "Bible",
        "biblical", "faith", "Christian perspective",
        "how does this relate to Christianity",
        "how does this relate to God"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -------------------------
# Math Curriculum (guides grade level pacing)
# -------------------------
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


# -------------------------------------------------------------
# EXPLAIN A MATH TOPIC (FULL LESSON)
# -------------------------------------------------------------
def explain_math(topic: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    # Christian worldview request
    if is_christian_question(topic):
        christian_prompt = f"""
The student asked how this math idea connects to Christianity.

Topic: {topic}

Explain gently and briefly:
- Math itself is academically neutral.
- Many Christians see math as reflecting order and consistency that God created.
- Avoid claiming the Bible teaches modern math topics.
- Keep the tone age-appropriate for grade {grade_level}.

Do not teach the math steps here. Only offer the Christian connection.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    # Standard academic explanation
    grade_topics = ", ".join(MATH_TOPICS.get(str(grade_level), []))

    prompt = f"""
Teach the math topic: {topic}
Student grade level: {grade_level}

Use a calm, conversational tone. Keep things simple and friendly.

Include:
- A short overview of the idea
- Step-by-step explanation
- A couple worked examples with explanations
- Key ideas to remember
- 5 practice problems
- Then the answers

Avoid lists with symbols like dashes or bullets. Just write in clear sentences and line breaks.

Grade {grade_level} normally studies topics such as: {grade_topics}
Use this to guide the difficulty.
"""

    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


# -------------------------------------------------------------
# SOLVE A MATH PROBLEM STEP BY STEP
# -------------------------------------------------------------
def solve_math_problem(problem: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    # Christian worldview request
    if is_christian_question(problem):
        christian_prompt = f"""
The student asked how this math question relates to Christianity.

Problem: {problem}

Explain gently that math is neutral academically, and some Christians see the order of math as reflecting the order in creation. Keep it short and do not solve the problem in this mode.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    prompt = f"""
Solve this math problem step by step in a calm, conversational way.

Problem: {problem}

Include:
- Restating what the problem is asking
- Step-by-step reasoning in plain language
- The final answer clearly stated
- One short tip for recognizing or solving similar problems in the future

Keep everything simple and friendly.
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


# -------------------------------------------------------------
# GENERATE A MATH QUIZ
# -------------------------------------------------------------
def generate_math_quiz(topic: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    # Christian worldview request
    if is_christian_question(topic):
        christian_prompt = f"""
The student asked how this math topic relates to Christianity.

Topic: {topic}

Start with a short reflection on how Christians sometimes see math as reflecting order and structure in the world. Then provide three simple practice questions and an answer key.
"""
        christian_prompt = apply_personality(character, christian_prompt)
        return study_buddy_ai(christian_prompt, grade_level, character)

    prompt = f"""
Create a short math quiz for the topic: {topic}
Grade level: {grade_level}

Include:
- Five practice questions
- Then the answer key

Write in a gentle, calm, conversational way as though you are verbally giving the questions to a student.
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)

