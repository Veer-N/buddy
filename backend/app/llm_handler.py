# llm_handler.py
import requests
from typing import List, Tuple
from .fillers import get_random_response  # fallback filler responses


def summarize_memories(memories, concise=True):
    """Summarize relevant memories for Buddy reply."""
    if not memories:
        return ""
    if concise:
        for msg, _ in reversed(memories):
            if msg['speaker'] == 'user':
                return msg['text']
        return ""
    else:
        return "\n".join([f"{m['speaker']}: {m['text']}" for m, _ in memories])


def _call_ollama(prompt: str) -> str:
    """Internal helper to call Ollama locally with fallback."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "gemma3:4b", "prompt": prompt, "stream": False},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        reply = data.get("response", "").strip()

        # Fallback if Ollama returns empty
        if not reply:
            reply = get_random_response()

        return reply

    except Exception as e:
        # Return a random filler from fallback responses on error
        print(f"[LLM_HANDLER] ❌ Ollama error: {e}")
        return get_random_response()


def generate_reply(user_text: str, memories_summary: str) -> str:
    """Generate Buddy reply using Ollama or fallback fillers."""
    prompt = f"""You are Buddy, an empathetic AI companion.
User said: {user_text}
Context: {memories_summary}
Reply naturally, with emotion and understanding."""

    return _call_ollama(prompt)
