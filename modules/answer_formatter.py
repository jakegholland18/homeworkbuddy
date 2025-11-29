# modules/answer_formatter.py
"""
This module standardizes all AI answers into a clean, structured dictionary
so every subject page displays consistently.

It prevents KeyErrors and ensures subject.html always receives the sections:
overview, key_facts, christian_view, agreement, difference, practice.
"""

def format_answer(
    overview=None,
    key_facts=None,
    christian_view=None,
    agreement=None,
    difference=None,
    practice=None,
    raw_text=None
):
    """
    Safely formats and normalizes structured AI output
    to match what subject.html expects.
    """

    # Ensure lists are always lists and strings are always strings
    return {
        "overview": overview or "",
        
        "key_facts": key_facts if isinstance(key_facts, list) else [],

        "christian_view": christian_view or "",

        "agreement": agreement if isinstance(agreement, list) else [],

        "difference": difference if isinstance(difference, list) else [],

        "practice": practice if isinstance(practice, list) else [],

        # Optional: keep original AI text for debugging or future features
        "raw_text": raw_text or ""
    }


