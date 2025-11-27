# modules/bible_helper.py

from modules.shared_ai import study_buddy_ai
from modules.personality_helper import apply_personality


# -----------------------------
# Detect when student wants Christian content
# -----------------------------
def is_christian_request(text: str) -> bool:
    keywords = [
        "Bible", "Jesus", "God", "Christian", "faith",
        "Christianity", "Scripture", "biblical", "verse",
        "how does this relate to God", "what does this mean biblically"
    ]
    return any(k.lower() in text.lower() for k in keywords)


# -----------------------------
# MAIN BIBLE LESSON FUNCTION
# -----------------------------
def bible_lesson(topic: str, grade_level="8", character=None):
    """
    A gentle, conversational Bible explanation.
    No hype, no drama, no lists unless necessary,
    and subtle personality from the selected character.
    """

    if character is None:
        character = "valor_strike"

    if not is_christian_request(topic):
        # If the student asks a Bible question,
        # we always allow Christian perspective.
        # If they ask a non-Bible question, this helper shouldn't be used.
        topic = f"The student asked a Bible-related question: {topic}"

    prompt = f"""
The student is asking a Bible question at a grade {grade_level} level.

Topic or passage:
{topic}

Explain the meaning in a warm, gentle, conversational tone. 
Avoid big dramatic language, avoid overly formal theological terms,
and keep it understandable for the student's age.

Include:
A simple explanation of the passage or topic.
A calm description of how many Christians understand it.
A short, friendly note about how this idea might matter in daily life.

Do not preach, pressure, or judge. 
Be respectful, kind, and thoughtful.
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


# -----------------------------
# EXPLAIN A VERSE
# -----------------------------
def explain_verse(reference: str, text: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    prompt = f"""
Explain this Bible verse in a gentle, clear, conversational way
for a grade {grade_level} student.

Reference: {reference}
Text: {text}

Describe the meaning of the verse in simple terms.
Mention how many Christians understand its message.
Offer one calm thought about how it might encourage or guide someone.

Avoid dramatic imagery or forceful language.
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


# -----------------------------
# EXPLAIN A BIBLE STORY
# -----------------------------
def explain_bible_story(story: str, grade_level="8", character=None):
    if character is None:
        character = "valor_strike"

    prompt = f"""
Tell the story of {story} from the Bible in a calm, warm, conversational tone.
Make the summary clear and age-appropriate for grade {grade_level}.

Then gently explain the main message that many Christians see in this story.
Offer one thought about how this lesson might be meaningful in everyday life.

Keep the explanation quiet, natural, and thoughtful.
No dramatic storytelling.
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)


# -----------------------------
# CHRISTIAN WORLDVIEW QUESTIONS
# -----------------------------
def christian_worldview(question: str, grade_level="8", character=None):
    """
    For questions like:
    - Why do Christians believe ___?
    - How does Christianity explain ___?
    """

    if character is None:
        character = "valor_strike"

    prompt = f"""
The student is asking a Christian worldview question:

{question}

Answer in a patient, conversational tone suitable for grade {grade_level}.
Explain what many Christians believe and why, using calm and gentle language.

Avoid arguments, debates, or harsh comparisons to other beliefs.
Focus on clarity, kindness, and understanding.

Offer a short, thoughtful reflection that helps the student feel supported.
"""
    prompt = apply_personality(character, prompt)
    return study_buddy_ai(prompt, grade_level, character)

