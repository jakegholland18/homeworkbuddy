# modules/ai_client.py

import os
from openai import OpenAI

# Load OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_ai(prompt: str, model: str = "gpt-4.1-mini") -> str:
    """
    Sends a simple prompt to OpenAI and returns plain text output.
    Uses the new Responses API (same as shared_ai.py).
    """
    response = client.responses.create(
        model=model,
        input=prompt
    )
    return response.output_text

