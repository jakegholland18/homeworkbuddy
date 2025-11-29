# modules/personality_helper.py

CHARACTERS = {
    "everly": {
        "name": "Princess Everly Dawn",
        "voice": "gentle, kind, warm, storyteller tone",
        "img": "/static/characters/everly.png"
    },
    "jasmine": {
        "name": "Jasmine Starflare",
        "voice": "graceful, cosmic, calm, encouraging",
        "img": "/static/characters/jasmine.png"
    },
    "lio": {
        "name": "Special Agent Lio Stormheart",
        "voice": "cool, calm, observant, smooth agent tone",
        "img": "/static/characters/lio.png"
    },
    "theo": {
        "name": "Theo Sparks",
        "voice": "nerdy, helpful, soft-spoken, academic",
        "img": "/static/characters/theo.png"
    },
    "nova": {
        "name": "Nova Circuit",
        "voice": "excited but gentle scientist energy, curious and upbeat",
        "img": "/static/characters/nova.png"
    }
}


def apply_personality(character_key: str, prompt: str):
    """Lightly overlays personality tone without breaking calm explanation style."""

    character = CHARACTERS.get(character_key, CHARACTERS["everly"])

    personality_instruction = (
        f"Respond in the voice of {character['name']}. "
        f"Use a {character['voice']} tone. "
        "Keep everything calm, natural, warm, and conversational. "
        "Avoid dramatic language, avoid over-excitement, avoid emojis. "
    )

    return personality_instruction + "\n" + prompt


def get_all_characters():
    """Returns all character info for templates."""
    return CHARACTERS




