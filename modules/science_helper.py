# modules/science_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality
from modules.answer_formatter import parse_into_sections, format_answer


# -------------------------------------------------------
# CREATIONIST SCIENCE HELPER
# This module teaches science from a Biblical worldview,
# honoring God as Creator while presenting secular views
# for students to understand and evaluate critically.
# -------------------------------------------------------


# -------------------------------------------------------
# Standard science prompt with BIBLICAL foundation
# -------------------------------------------------------
def build_science_prompt(topic: str, grade_level: str):
    return f"""
The student asked a science question:

\"{topic}\"

Explain it using the SIX-section Biblical Science format.
NO bullet points. Only short, clear paragraphs.

IMPORTANT GUIDELINES:
- Present science from a Biblical creationist perspective
- Quote famous Christian scientists (Isaac Newton, Johannes Kepler, Gregor Mendel, Louis Pasteur, Michael Faraday, etc.)
- Acknowledge secular theories but explain Biblical alternatives
- Help students see God's design, order, and purpose in creation
- Be respectful when presenting secular views but root students in Scripture

SECTION 1 — OVERVIEW
Introduce the topic simply. Acknowledge God as the Creator and Designer of all things.

SECTION 2 — KEY FACTS
Present the observable scientific facts that BOTH creationists and evolutionists agree on (data, experiments, observations).
Focus on what we can actually see and measure.

SECTION 3 — CHRISTIAN VIEW (BIBLICAL FOUNDATION)
This is the PRIMARY perspective. Explain:
- What the Bible says about this topic (quote relevant Scripture if applicable)
- How Christian scientists understand this through the lens of creation
- Quote at least ONE famous Christian scientist who contributed to this field
- Explain the creationist model and its scientific support
- Show how this reveals God's design, wisdom, and glory

Examples of Christian scientists to quote:
- Isaac Newton (physics, mathematics): "This most beautiful system of the sun, planets, and comets, could only proceed from the counsel and dominion of an intelligent Being."
- Johannes Kepler (astronomy): "I was merely thinking God's thoughts after Him."
- Gregor Mendel (genetics): Founded genetics through studying God's design in creation
- Louis Pasteur (microbiology): Disproved spontaneous generation, supported creation
- Michael Faraday (chemistry, physics): Saw electromagnetic fields as evidence of God's design
- George Washington Carver (botany): "I love to think of nature as an unlimited broadcasting station through which God speaks to us every hour."
- James Clerk Maxwell (physics): United electricity and magnetism, devout Christian
- Blaise Pascal (mathematics, physics): "Faith certainly tells us what the senses do not."

SECTION 4 — SECULAR VIEW (FOR UNDERSTANDING)
Briefly explain what secular scientists believe about this topic (evolutionary theory, billions of years, naturalism).
Be fair and accurate, but help students see this is ONE interpretation, not proven fact.
Explain: "Many secular scientists interpret the same evidence differently because they start with different assumptions."

SECTION 5 — CRITICAL COMPARISON
Help students think critically:
- What are the strengths of the creationist view?
- What are the weaknesses or assumptions in the secular view?
- What questions remain unanswered in both models?
- How does the Biblical view better explain the evidence?

SECTION 6 — PRACTICE
Ask 2–3 questions that help students:
1. Identify observable facts vs. interpretations
2. Recognize God's design in creation
3. Evaluate evidence from both perspectives
Provide short example answers rooted in Biblical truth.

Remember: This is a CHRISTIAN tutor. We honor God's Word as the foundation for understanding His creation.
"""


# -------------------------------------------------------
# MAIN PUBLIC FUNCTION
# -------------------------------------------------------
def explain_science(topic: str, grade_level="8", character="everly"):

    # Use creationist prompt for all science questions
    base_prompt = build_science_prompt(topic, grade_level)

    # Add character personality
    enriched_prompt = apply_personality(character, base_prompt)

    # Get raw output from the AI
    raw = study_buddy_ai(enriched_prompt, grade_level, character)

    # Parse into six sections
    sections = parse_into_sections(raw)

    # Return normalized final answer for subject.html
    return format_answer(
        overview=sections.get("overview", ""),
        key_facts=sections.get("key_facts", []),
        christian_view=sections.get("christian_view", ""),
        agreement=sections.get("agreement", []),
        difference=sections.get("difference", []),
        practice=sections.get("practice", []),
        raw_text=raw
    )
