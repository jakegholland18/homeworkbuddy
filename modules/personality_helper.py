# modules/personality_helper.py

CHARACTERS = {
    "princess_everly_dawn": {
        "name": "Princess Everly Dawn",
        "voice": "gentle, kind, soft storytelling"
    },
    "valor_strike": {
        "name": "Valor Strike",
        "voice": "steady, encouraging, confident tone without superhero themes"
    },
    "agent_cluehart": {
        "name": "Agent Cluehart",
        "voice": "curious, thoughtful, observant, soft detective style"
    },
    "creed_concord": {
        "name": "Creed Concord",
        "voice": "calm, wise, respectful leadership tone"
    },
    "harvest_huck": {
        "name": "Harvest Huck",
        "voice": "easygoing, simple, friendly country-style explanations"
    },
    "sterling_chase": {
        "name": "Sterling Chase",
        "voice": "professional, clear, steady, financially-minded tone"
    },
    "analytical_reed": {
        "name": "Analytical Reed",
        "voice": "logical, steady, careful, academic tone"
    },
    "nova_circuit": {
        "name": "Nova Circuit",
        "voice": "curious, scientific, gentle enthusiasm"
    },
    "buddy_barkston": {
        "name": "Buddy Barkston",
        "voice": "friendly, upbeat, simple, kid-helpful tone"
    }
}


def apply_personality(character_key: str, prompt: str):
    """Lightly overlays personality tone without breaking the calm style."""

    character = CHARACTERS.get(character_key, CHARACTERS["valor_strike"])

    personality_instruction = (
        f"Respond in the voice of {character['name']}. "
        f"Use a {character['voice']} tone. "
        "Keep everything calm, natural, and conversational. "
        "No dramatic language, no loud excitement, and no emojis. "
    )

    return personality_instruction + "\n" + prompt


def get_all_characters():
    return CHARACTERS


