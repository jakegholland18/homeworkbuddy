"""
Centralized Subject Configuration
All subject metadata in one place for easy management and scaling.
"""

# Subject Registry - Single source of truth for all subjects
SUBJECTS = {
    "num_forge": {
        "key": "num_forge",
        "name": "NumForge",
        "label": "NumForge (Math)",
        "description": "Master math concepts from arithmetic to advanced algebra",
        "subtitle": "Math",
        "icon": "num_forge.png",
        "category": "core",
        "min_grade": 1,
        "max_grade": 12,
        "handler_module": "math_helper",
        "handler_function": "explain_math",
        "features": ["practice", "deep_study", "arcade", "chat"],
        "order": 2,
    },
    "atom_sphere": {
        "key": "atom_sphere",
        "name": "AtomSphere",
        "label": "AtomSphere (Science)",
        "description": "Explore the wonders of biology, chemistry, physics, and more",
        "subtitle": "Science",
        "icon": "atom_sphere.png",
        "category": "core",
        "min_grade": 1,
        "max_grade": 12,
        "handler_module": "science_helper",
        "handler_function": "explain_science",
        "features": ["practice", "deep_study", "chat"],
        "order": 3,
    },
    "ink_haven": {
        "key": "ink_haven",
        "name": "InkHaven",
        "label": "InkHaven (Writing)",
        "description": "Craft compelling narratives and master writing skills",
        "subtitle": "Writing",
        "icon": "ink_haven.png",
        "category": "core",
        "min_grade": 1,
        "max_grade": 12,
        "handler_module": "writing_helper",
        "handler_function": "help_write",
        "features": ["practice", "chat"],
        "order": 5,
    },
    "faith_realm": {
        "key": "faith_realm",
        "name": "FaithRealm",
        "label": "FaithRealm (Bible)",
        "description": "Discover biblical wisdom and spiritual understanding",
        "subtitle": "Bible",
        "icon": "faith_realm.png",
        "category": "enrichment",
        "min_grade": 1,
        "max_grade": 12,
        "handler_module": "bible_helper",
        "handler_function": "bible_lesson",
        "features": ["practice", "chat"],
        "order": 6,
    },
    "chrono_core": {
        "key": "chrono_core",
        "name": "ChronoCore",
        "label": "ChronoCore (History)",
        "description": "Journey through time and explore world history",
        "subtitle": "History",
        "icon": "chrono_core.png",
        "category": "core",
        "min_grade": 1,
        "max_grade": 12,
        "handler_module": "history_helper",
        "handler_function": "explain_history",
        "features": ["practice", "deep_study", "chat"],
        "order": 1,
    },
    "story_verse": {
        "key": "story_verse",
        "name": "StoryVerse",
        "label": "StoryVerse (Reading)",
        "description": "Analyze literature and improve reading comprehension",
        "subtitle": "Reading",
        "icon": "story_verse.png",
        "category": "core",
        "min_grade": 1,
        "max_grade": 12,
        "handler_module": "text_helper",
        "handler_function": "explain_text",
        "features": ["practice", "chat"],
        "order": 4,
    },
    "coin_quest": {
        "key": "coin_quest",
        "name": "CoinQuest",
        "label": "CoinQuest (Money)",
        "description": "Learn essential money management and financial literacy",
        "subtitle": "Money",
        "icon": "coin_quest.png",
        "category": "life_skills",
        "min_grade": 3,
        "max_grade": 12,
        "handler_module": "money_helper",
        "handler_function": "explain_money",
        "features": ["practice", "chat"],
        "order": 7,
    },
    "stock_star": {
        "key": "stock_star",
        "name": "StockStar",
        "label": "StockStar (Investing)",
        "description": "Understand investing, markets, and building wealth",
        "subtitle": "Investing",
        "icon": "stock_star.png",
        "category": "life_skills",
        "min_grade": 6,
        "max_grade": 12,
        "handler_module": "investment_helper",
        "handler_function": "explain_investing",
        "features": ["practice", "chat"],
        "order": 8,
    },
    "truth_forge": {
        "key": "truth_forge",
        "name": "TruthForge",
        "label": "TruthForge (Apologetics)",
        "description": "Develop critical thinking and defend your faith",
        "subtitle": "Apologetics",
        "icon": "truth_forge.png",
        "category": "enrichment",
        "min_grade": 6,
        "max_grade": 12,
        "handler_module": "apologetics_helper",
        "handler_function": "apologetics_answer",
        "features": ["chat"],
        "order": 11,
    },
    "terra_nova": {
        "key": "terra_nova",
        "name": "TerraNova",
        "label": "TerraNova (General)",
        "description": "Ask anything and explore all topics",
        "subtitle": "General Knowledge",
        "icon": "terra_nova.png",
        "category": "general",
        "min_grade": 1,
        "max_grade": 12,
        "handler_module": "question_helper",
        "handler_function": "answer_question",
        "features": ["chat"],
        "order": 9,
    },
    "power_grid": {
        "key": "power_grid",
        "name": "PowerGrid",
        "label": "PowerGrid (Deep Study)",
        "description": "Upload materials for deep study and comprehensive learning",
        "subtitle": "Deep Study",
        "icon": "power_grid.png",
        "category": "advanced",
        "min_grade": 6,
        "max_grade": 12,
        "handler_module": None,  # Special handling
        "handler_function": None,
        "features": ["file_upload", "deep_study"],
        "order": 10,
    },
}


def get_subject(subject_key: str) -> dict:
    """Get subject configuration by key. Returns None if not found."""
    return SUBJECTS.get(subject_key)


def get_all_subjects(sorted_by_order=True) -> list:
    """Get all subjects as list. Optionally sorted by display order."""
    subjects_list = list(SUBJECTS.values())
    if sorted_by_order:
        subjects_list.sort(key=lambda x: x.get("order", 999))
    return subjects_list


def get_subject_handler(subject_key: str):
    """
    Get the handler function for a subject.
    Returns tuple: (module_name, function_name) or (None, None) if special handling needed.
    """
    subject = get_subject(subject_key)
    if not subject:
        return None, None
    return subject.get("handler_module"), subject.get("handler_function")


def validate_subject(subject_key: str) -> bool:
    """Check if subject key is valid."""
    return subject_key in SUBJECTS


def validate_grade(grade_value) -> int:
    """
    Validate and normalize grade value.
    Returns valid grade (1-12) or default grade 8.
    """
    try:
        grade = int(grade_value)
        if 1 <= grade <= 12:
            return grade
    except (ValueError, TypeError):
        pass
    return 8  # Default grade


def validate_grade_for_subject(subject_key: str, grade_value) -> bool:
    """Check if grade is valid for specific subject."""
    subject = get_subject(subject_key)
    if not subject:
        return False

    grade = validate_grade(grade_value)
    min_grade = subject.get("min_grade", 1)
    max_grade = subject.get("max_grade", 12)

    return min_grade <= grade <= max_grade


def get_subjects_for_display() -> list:
    """
    Get subjects formatted for display on /subjects page.
    Returns list of tuples: (key, icon, name, subtitle)
    """
    subjects = get_all_subjects(sorted_by_order=True)
    return [
        (s["key"], s["icon"], s["name"], s["subtitle"])
        for s in subjects
    ]


def get_subject_labels() -> dict:
    """Get dict of subject keys to display labels for dropdowns."""
    return {s["key"]: s["label"] for s in SUBJECTS.values()}


def get_subject_map():
    """
    Get dict mapping subject keys to handler functions.
    Used for backward compatibility with existing code.
    Returns dict with None for subjects requiring special handling.
    """
    subject_map = {}

    # Import handlers dynamically
    from modules import (
        math_helper,
        science_helper,
        bible_helper,
        history_helper,
        writing_helper,
        apologetics_helper,
        investment_helper,
        money_helper,
        question_helper,
        text_helper,
    )

    handler_modules = {
        "math_helper": math_helper,
        "science_helper": science_helper,
        "bible_helper": bible_helper,
        "history_helper": history_helper,
        "writing_helper": writing_helper,
        "apologetics_helper": apologetics_helper,
        "investment_helper": investment_helper,
        "money_helper": money_helper,
        "question_helper": question_helper,
        "text_helper": text_helper,
    }

    for key, config in SUBJECTS.items():
        module_name = config.get("handler_module")
        func_name = config.get("handler_function")

        if module_name and func_name and module_name in handler_modules:
            module = handler_modules[module_name]
            subject_map[key] = getattr(module, func_name)
        else:
            subject_map[key] = None  # Special handling needed

    return subject_map


# Category descriptions
CATEGORIES = {
    "core": "Core academic subjects for comprehensive learning",
    "enrichment": "Spiritual and personal development",
    "life_skills": "Practical skills for real-world success",
    "general": "Broad knowledge and curiosity exploration",
    "advanced": "Deep dive tools for intensive study",
}


def get_subjects_by_category() -> dict:
    """Group subjects by category."""
    by_category = {}
    for subject in SUBJECTS.values():
        category = subject.get("category", "general")
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(subject)

    # Sort each category by order
    for category in by_category:
        by_category[category].sort(key=lambda x: x.get("order", 999))

    return by_category
