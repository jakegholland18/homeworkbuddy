import re

def clean(text):
    if not text:
        return ""
    return text.strip()

def split_bullets(text):
    if not text:
        return []
    
    # Split into bullet-like chunks
    parts = re.split(r"[•\-–]\s*", text)
    parts = [p.strip() for p in parts if p.strip()]

    return parts[:8]   # limit for kid readability


def format_answer(ai_text: str):
    """
    Converts raw AI text into structured sections for subject.html
    """

    # SAFETY: ensure ai_text is a string
    if not isinstance(ai_text, str):
        ai_text = str(ai_text)

    # ----- DETECT sections in the AI text using simple anchors ------
    overview_match = re.search(r"(overview|summary|topic):?(.*?)(key facts|christian|agree|differ|practice|$)", ai_text, re.I | re.S)
    key_facts_match = re.search(r"(key facts|important points|facts):?(.*?)(christian|agree|differ|practice|$)", ai_text, re.I | re.S)
    christian_match = re.search(r"(christian|faith|biblical|worldview):?(.*?)(agree|differ|practice|$)", ai_text, re.I | re.S)
    agree_match = re.search(r"(agree|agreement|similar):?(.*?)(differ|difference|practice|$)", ai_text, re.I | re.S)
    differ_match = re.search(r"(differ|difference|contrast):?(.*?)(practice|$)", ai_text, re.I | re.S)
    practice_match = re.search(r"(practice|try|questions):?(.*)", ai_text, re.I | re.S)

    # ----- Extract sections -----
    overview = clean(overview_match.group(2) if overview_match else "")
    key_facts = split_bullets(key_facts_match.group(2) if key_facts_match else "")
    christian_view = clean(christian_match.group(2) if christian_match else "")
    agreement = split_bullets(agree_match.group(2) if agree_match else "")
    difference = split_bullets(differ_match.group(2) if differ_match else "")
    practice = split_bullets(practice_match.group(2) if practice_match else "")

    # ----- Return consistent structured object -----
    return {
        "overview": overview or "",
        "key_facts": key_facts or [],
        "christian_view": christian_view or "",
        "agreement": agreement or [],
        "difference": difference or [],
        "practice": practice or []
    }

