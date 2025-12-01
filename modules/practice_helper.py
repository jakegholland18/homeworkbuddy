# modules/practice_helper.py

import json
from typing import Dict, Any

from modules.shared_ai import get_client, build_character_voice, grade_depth_instruction


def _difficulty_for_grade(grade_level: str) -> str:
    """
    Map grade to difficulty description.
    D = auto-match to grade (your choice).
    """
    try:
        g = int(grade_level)
    except Exception:
        return "medium difficulty"

    if g <= 3:
        return "very easy, gentle, early elementary difficulty"
    if g <= 6:
        return "easy to medium difficulty for upper elementary"
    if g <= 8:
        return "medium difficulty for middle school"
    if g <= 10:
        return "medium-hard difficulty for early high school"
    return "advanced difficulty for high school and beyond"


def _subject_flavor(subject: str) -> str:
    """
    Short hint for how to shape the practice based on subject code.
    """
    mapping = {
        "num_forge": "math word problems and step-by-step equation solving.",
        "atom_sphere": "science processes, cause-and-effect, and experiments explained in steps.",
        "faith_realm": "Bible stories, verses, and application questions in small steps.",
        "chrono_core": "history timelines, causes and effects, and event comparisons.",
        "ink_haven": "writing skills like grammar fixes, sentence rewrites, and structure.",
        "truth_forge": "apologetics questions, reasoning steps, and evidence-based thinking.",
        "stock_star": "investing scenarios, risk vs reward, and math with percentages.",
        "coin_quest": "money skills: budgeting, saving, spending, and simple interest.",
        "terra_nova": "general knowledge, logic puzzles, and concept breakdowns.",
        "story_verse": "reading comprehension with short passages and questions.",
        "power_grid": "deeper multi-step reasoning practice based on the topic.",
    }
    return mapping.get(subject, "general step-by-step practice questions.")


def generate_practice_session(
    topic: str,
    subject: str,
    grade_level: str = "8",
    character: str = "everly",
) -> Dict[str, Any]:
    """
    Generate a structured, multi-step interactive practice session.

    Returns a dict shaped like:
    {
        "steps": [
            {
                "prompt": "Tutor message to student (what to ask them to do for this step)",
                "expected": ["acceptable answer 1", "acceptable answer 2"],
                "hint": "short hint if they get it wrong"
            },
            ...
        ],
        "final_message": "Encouraging wrap-up message."
    }
    """

    difficulty = _difficulty_for_grade(grade_level)
    subject_hint = _subject_flavor(subject)
    voice = build_character_voice(character)
    depth_rule = grade_depth_instruction(grade_level)

    if not topic:
        topic = "the last thing the student asked about"

    system_prompt = f"""
You are HOMEWORK BUDDY PRACTICE MODE — an interactive tutor.

GOAL:
Create a SHORT, FUN, STEP-BY-STEP practice session that the student
will complete one message at a time in a chat.

IMPORTANT:
• The practice is ONLY about this topic: {topic}
• Subject flavor: {subject_hint}
• Difficulty: {difficulty}
• Grade level rule: {depth_rule}
• Tutor voice: {voice}

OUTPUT FORMAT (VERY IMPORTANT):
Return ONLY valid JSON with this exact structure:

{{
  "steps": [
    {{
      "prompt": "string — what the tutor says to the student for this step",
      "expected": ["short acceptable answer 1", "answer 2"],
      "hint": "short helpful hint if the student gets it wrong"
    }}
  ],
  "final_message": "short encouraging completion message"
}}

RULES:
• 3 to 5 steps only.
• Each prompt should be short, fun, and clearly ask the student to do ONE thing.
• expected answers must be SHORT, lower-case words or phrases, no punctuation.
• Hints should be friendly and specific, not generic.
• Make it feel like a mission or challenge, but not cringey.
• DO NOT include any extra keys besides "steps" and "final_message".
• DO NOT include any explanation outside the JSON.
• DO NOT use markdown, bullet markers, or line prefixes.
"""

    user_prompt = """
Create the JSON practice session now.
Remember: ONLY return the JSON object, nothing else.
"""

    client = get_client()

    response = client.responses.create(
        model="gpt-4.1-mini",
        max_output_tokens=800,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.output_text.strip()

    # Try to parse JSON from the model
    try:
        practice_data = json.loads(raw)
    except Exception:
        # Fallback: simple 1-step practice if parsing fails
        return {
            "steps": [
                {
                    "prompt": f"Let's practice {topic}. First, tell me one important thing you remember about it.",
                    "expected": [""],  # accept anything
                    "hint": "There isn’t one right answer; just share any key idea you remember.",
                }
            ],
            "final_message": "Nice work! You finished this quick practice mission 🚀",
        }

    # Basic validation + safety
    if not isinstance(practice_data, dict):
        return {
            "steps": [
                {
                    "prompt": f"Let's practice {topic}. First, tell me one important thing you remember about it.",
                    "expected": [""],
                    "hint": "There isn’t one right answer; just share any key idea you remember.",
                }
            ],
            "final_message": "Nice work! You finished this quick practice mission 🚀",
        }

    steps = practice_data.get("steps") or []
    if not isinstance(steps, list) or len(steps) == 0:
        practice_data["steps"] = [
            {
                "prompt": f"Let's practice {topic}. First, tell me one important thing you remember about it.",
                "expected": [""],
                "hint": "There isn’t one right answer; just share any key idea you remember.",
            }
        ]

    # Normalize expected lists to always be list of strings
    normalized_steps = []
    for step in practice_data["steps"]:
        prompt = str(step.get("prompt", "")).strip()
        expected = step.get("expected", [])
        hint = str(step.get("hint", "")).strip() or "Try thinking about the main idea again."

        if not isinstance(expected, list):
            expected = [str(expected)]

        expected_clean = [str(a).lower().strip() for a in expected if str(a).strip()]

        normalized_steps.append(
            {
                "prompt": prompt or "What is the next thing you would do?",
                "expected": expected_clean or [""],
                "hint": hint,
            }
        )

    practice_data["steps"] = normalized_steps
    practice_data["final_message"] = practice_data.get(
        "final_message",
        "Great job! You completed this practice mission 🚀",
    )

    return practice_data
