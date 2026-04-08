"""
groq_service.py
Two responsibilities:
  1. LLM post-processing (spelling, grammar, translation) via Groq
  2. Fetching API usage / rate-limit info  ← EXTRA FEATURE
"""

import requests
from config import GROQ_API_KEY, GROQ_DEFAULT_MODEL

_BASE = "https://api.groq.com/openai/v1"


def get_groq_usage():
    """
    Groq doesn't expose a credit-balance endpoint, but every API response
    includes rate-limit headers that show remaining quota.
    Returns a dict with status, req_remaining, tok_remaining, etc.
    """
    if not GROQ_API_KEY or GROQ_API_KEY == "PASTE_YOUR_GROQ_KEY_HERE":
        return {"status": "API key not configured"}

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    try:
        r = requests.get(f"{_BASE}/models", headers=headers, timeout=10)
        if r.status_code == 401:
            return {"status": "Invalid API key ✗"}
        if r.status_code != 200:
            return {"status": f"HTTP {r.status_code}"}

        h = r.headers
        return {
            "status"        : "Connected ✓",
            "req_limit"     : h.get("x-ratelimit-limit-requests",     "N/A"),
            "req_remaining" : h.get("x-ratelimit-remaining-requests", "N/A"),
            "tok_limit"     : h.get("x-ratelimit-limit-tokens",       "N/A"),
            "tok_remaining" : h.get("x-ratelimit-remaining-tokens",   "N/A"),
            "reset_at"      : h.get("x-ratelimit-reset-requests",     "N/A"),
        }
    except Exception as e:
        return {"status": f"Connection error: {e}"}


def get_groq_models():
    """Return list of available Groq model IDs."""
    if not GROQ_API_KEY or GROQ_API_KEY == "PASTE_YOUR_GROQ_KEY_HERE":
        return []
    try:
        r = requests.get(
            f"{_BASE}/models",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            timeout=10,
        )
        r.raise_for_status()
        return sorted(m["id"] for m in r.json().get("data", []) if m.get("object") == "model")
    except Exception:
        return []


class GroqService:
    """Applies optional LLM corrections to a transcript."""

    def process(self, text, *, fix_spelling=False, fix_grammar=False,
                translate_to=None, model=GROQ_DEFAULT_MODEL):
        if not GROQ_API_KEY or GROQ_API_KEY == "PASTE_YOUR_GROQ_KEY_HERE":
            return text
        if not (fix_spelling or fix_grammar or translate_to):
            return text

        steps, n = [], 1
        if fix_spelling:
            steps.append(f"{n}. Fix spelling mistakes. Do not change meaning."); n += 1
        if fix_grammar:
            steps.append(f"{n}. Fix grammar mistakes. Do not add content."); n += 1
        if translate_to:
            steps.append(f"{n}. Translate entirely to {translate_to}.")

        system = (
            "Apply these steps in order:\n" + "\n".join(steps)
            + "\nReturn ONLY the result — no explanation."
        )
        try:
            r = requests.post(
                f"{_BASE}/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user",   "content": text},
                    ],
                    "temperature": 0,
                },
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip() or text
        except Exception:
            return text