# modules/bible_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# ------------------------------------------------
# Detect if the student is asking for Christian content
# ------------------------------------------------
def is_christian_request(text: str) -> bool:
    keywords = [
        "bible", "jesus", "god", "christian", "faith", "scripture",
        "christianity", "biblical", "verse",
        "how does this relate to god", "what does this mean biblically"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# ------------------------------------------------
# SOCRATIC TUTOR WRAPPER
# ------------------------------------------------
def socratic_layer(base_explanation: str, question: str, grade_level: str):
    """
    Wraps the final explanation inside a step-by-step Socratic tutoring format.
    """

    return f"""
A student asked: "{question}"

Begin by helping the student think on their own without giving the full answer right away.

First, restate in gentle, kid-friendly language what the question is really about.

Next, offer one helpful hint that points them in the right direction.

Then, ask a guiding question that helps them think more deeply
about what the Bible teaches and how it might connect to their life.

After that, provide a small nudge—but still avoid giving away the final explanation.

Only after guiding them step-by-step should you transition into the full Bible explanation below.

Full Explanation:
{base_explanation}

End with a warm, simple summary appropriate for a grade {grade_level} student.
Reassure them that asking Bible questions is a wonderful way to grow.
"""


# ------------------------------------------------
# MAIN BIBLE LESSON FUNCTION
# ------------------------------------------------
def bible_lesson(topic: str, grade_level="8", character=None):

    if character is None:
        character = "valor_strike"

    if not is_christian_request(topic):
        topic = f"The student asked a Bible-related question: {topic}"

    base_prompt = f"""
The student is asking a Bible question at a grade {grade_level} level.

Topic:
{topic}

Explain the meaning in a warm, calm, conversational tone.
Avoid dramatic or heavy theological language.

Include:
A simple explanation of the topic.
A gentle description of how many Christians understand it.
A soft note about how this message might matter in daily life.

No preaching, judgment, or pressure—only kindness.
"""

    guided_prompt = socratic_layer(base_prompt, topic, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)
    return study_buddy_ai(enriched_prompt, grade_level, character)


# ------------------------------------------------
# EXPLAIN A VERSE
# ------------------------------------------------
def explain_verse(reference: str, text: str, grade_level="8", character=None):

    if character is None:
        character = "valor_strike"

    base_prompt = f"""
Explain this Bible verse in a calm, gentle tone for grade {grade_level}.

Reference: {reference}
Text: {text}

Keep it simple and clear.
Describe how many Christians understand its meaning.
Offer one soft, encouraging thought.
"""

    guided_prompt = socratic_layer(base_prompt, text, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)
    return study_buddy_ai(enriched_prompt, grade_level, character)


# ------------------------------------------------
# EXPLAIN A BIBLE STORY
# ------------------------------------------------
def explain_bible_story(story: str, grade_level="8", character=None):

    if character is None:
        character = "valor_strike"

    base_prompt = f"""
Tell the story of {story} in a calm, conversational way.
Then gently explain the message Christians often see in it.
Share how it may matter in daily life.
"""

    guided_prompt = socratic_layer(base_prompt, story, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)
    return study_buddy_ai(enriched_prompt, grade_level, character)


# ------------------------------------------------
# CHRISTIAN WORLDVIEW QUESTIONS
# ------------------------------------------------
def christian_worldview(question: str, grade_level="8", character=None):

    if character is None:
        character = "valor_strike"

    base_prompt = f"""
The student is asking a Christian worldview question:

{question}

Explain in a calm, patient tone.
Describe what Christians believe and why.
Be gentle, thoughtful, and supportive.
"""

    guided_prompt = socratic_layer(base_prompt, question, grade_level)
    enriched_prompt = apply_personality(character, guided_prompt)
    return study_buddy_ai(enriched_prompt, grade_level, character)



