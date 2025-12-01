# modules/practice_helper.py

import json
from typing import Dict, Any
from modules.shared_ai import get_client, build_character_voice, grade_depth_instruction


# ------------------------------------------------------------
# Difficulty text
# ------------------------------------------------------------

def _difficulty_for_grade(grade_level: str) -> str:
    try:
        g = int(grade_level)
    except:
        return "medium difficulty"

    if g <= 3: return "very easy early-elementary difficulty"
    if g <= 6: return "easy to medium upper-elementary difficulty"
    if g <= 8: return "middle-school difficulty"
    if g <= 10: return "medium-hard early high-school difficulty"
    return "advanced high-school difficulty"


# ------------------------------------------------------------
# Subject flavor shaping
# ------------------------------------------------------------

def _subject_flavor(subject: str) -> str:
    mapping = {
        "num_forge": "math skills, word problems, equations, percentages, and reasoning.",
        "atom_sphere": "science concepts, experiments, cause-and-effect, and reasoning steps.",
        "faith_realm": "Bible knowledge, stories, verses, and application questions.",
        "chrono_core": "history timelines, events, causes, effects, and comparisons.",
        "ink_haven": "grammar, writing clarity, sentence improvement, and editing.",
        "truth_forge": "apologetics, reasoning, evidence, worldview logic.",
        "stock_star": "investing scenarios, percentages, returns, and decision-making.",
        "coin_quest": "money concepts: saving, spending, budgeting, interest, and value.",
        "terra_nova": "general knowledge, logic puzzles, problem solving.",
        "story_verse": "reading comprehension, inference, theme, characters.",
        "power_grid": "deep multi-step reasoning based on the topic.",
    }
    return mapping.get(subject, "general educational reasoning questions.")


# ------------------------------------------------------------
# MAIN PRACTICE GENERATOR
# ------------------------------------------------------------

def generate_practice_session(
    topic: str,
    subject: str,
    grade_level: str = "8",
    character: str = "everly",
) -> Dict[str, Any]:

    difficulty = _difficulty_for_grade(grade_level)
    flavor = _subject_flavor(subject)
    voice = build_character_voice(character)
    depth_rule = grade_depth_instruction(grade_level)

    if not topic:
        topic = "the last skill the student reviewed"

    # ------------------------------------------------------------
    # 🔥 NEW SYSTEM PROMPT — produces 10 mixed-question problems
    # ------------------------------------------------------------
    system_prompt = f"""
You are HOMEWORK BUDDY PRACTICE MODE.

GOAL:
Generate a *10-question* interactive practice mission:
• Some multiple-choice questions
• Some free-response questions
• Some word problems (if subject allows)
• ALL tied to: {topic}
• Subject flavor: {flavor}
• Difficulty: {difficulty}
• Tone & style use the tutor voice: {voice}
• Grade level rule: {depth_rule}

VERY IMPORTANT OUTPUT RULES:
Return ONLY VALID JSON in this exact format:

{{
  "steps": [
    {{
      "prompt": "string — what the tutor says for this problem",
      "type": "multiple_choice" OR "free",
      "choices": ["A. ...", "B. ...", "C. ...", "D. ..."],   (MC only)
      "expected": ["a"],            (MC: correct letter(s) only)
      "hint": "short helpful hint if wrong",
      "explanation": "step-by-step walkthrough for 3rd attempt"
    }}
  ],
  "final_message": "short encouraging completion message"
}}

STRICT RULES:
• Exactly 10 questions.
• NEVER omit "type". NEVER omit "choices" for MC questions.
• expected must be VERY short (e.g., ["a"] or ["4"]).
• Hints must be specific, not generic.
• Explanations must be short & step-by-step.
• Do NOT include markdown.
• Do NOT include commentary outside JSON.
"""

    user_prompt = """
Generate the full 10-question JSON practice session now.
REMEMBER: ONLY return the JSON object. No commentary.
"""

    client = get_client()
    response = client.responses.create(
        model="gpt-4.1-mini",
        max_output_tokens=1800,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.output_text.strip()

    # ------------------------------------------------------------
    # Attempt JSON parse
    # ------------------------------------------------------------
    try:
        data = json.loads(raw)
    except:
        # fallback
        return {
            "steps": [
                {
                    "prompt": f"Let's practice {topic}. What is one fact you remember?",
                    "type": "free",
                    "choices": [],
                    "expected": [""],
                    "hint": "Anything related to the topic works.",
                    "explanation": "You can share any detail you remember.",
                }
            ],
            "final_message": "Great work finishing the warm-up mission! 🚀",
            "topic": topic,
        }

    # ------------------------------------------------------------
    # Validation / Cleanup
    # ------------------------------------------------------------

    valid_steps = []
    for step in data.get("steps", []):
        prompt = str(step.get("prompt", "")).strip()

        qtype = step.get("type", "free")
        if qtype not in ["multiple_choice", "free"]:
            qtype = "free"

        choices = step.get("choices", []) if qtype == "multiple_choice" else []
        if choices and not isinstance(choices, list):
            choices = []

        expected_raw = step.get("expected", [])
        if not isinstance(expected_raw, list):
            expected_raw = [str(expected_raw)]

        expected = [str(x).lower().strip() for x in expected_raw if str(x).strip()]

        hint = str(step.get("hint", "Try thinking carefully about what the question is asking.")).strip()
        explanation = str(step.get("explanation", "Let's walk through how to solve it.")).strip()

        valid_steps.append({
            "prompt": prompt,
            "type": qtype,
            "choices": choices,
            "expected": expected or [""],
            "hint": hint,
            "explanation": explanation,
        })

    # Guarantee at least 1 step
    if not valid_steps:
        valid_steps = [
            {
                "prompt": f"Tell me one thing you know about {topic}.",
                "type": "free",
                "choices": [],
                "expected": [""],
                "hint": "Anything related works!",
                "explanation": "Just share what you remember.",
            }
        ]

    final_message = data.get("final_message", "You completed this practice mission! 🚀")

    return {
        "steps": valid_steps,
        "final_message": final_message,
        "topic": topic,
    }

