"""
deepgram_service.py
Two responsibilities:
  1. Real-time streaming STT via Deepgram WebSocket API
  2. Fetching account credit balance  ← EXTRA FEATURE
"""

import asyncio
import json
import queue
import threading
import requests
import websockets

from config import (
    DEEPGRAM_API_KEY,
    DEEPGRAM_DEFAULT_MODEL,
    DEEPGRAM_DEFAULT_LANGUAGE,
    AUDIO_SAMPLE_RATE,
)


def get_deepgram_balance():
    """
    Fetch Deepgram account credit balance.
    Returns: { "balance": "$12.34", "raw": 12.34, "error": None }
    """
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
    try:
        r = requests.get("https://api.deepgram.com/v1/projects", headers=headers, timeout=10)
        r.raise_for_status()
        projects = r.json().get("projects", [])
        if not projects:
            return {"balance": "N/A", "raw": None, "error": "No projects found"}

        project_id = projects[0]["project_id"]
        r = requests.get(
            f"https://api.deepgram.com/v1/projects/{project_id}/balances",
            headers=headers, timeout=10,
        )
        r.raise_for_status()
        balances = r.json().get("balances", [])
        if not balances:
            return {"balance": "$0.00", "raw": 0.0, "error": None}

        amount = balances[0].get("amount", 0.0)
        return {"balance": f"${amount:.4f}", "raw": amount, "error": None}

    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            return {"balance": "N/A", "raw": None, "error": "Invalid API key"}
        return {"balance": "N/A", "raw": None, "error": str(e)}
    except Exception as e:
        return {"balance": "N/A", "raw": None, "error": str(e)}


class DeepgramService:
    """Streams audio to Deepgram and returns the final transcript."""

    def __init__(self):
        self._thread = None

    def stream(self, audio_queue, on_transcript,
               model=DEEPGRAM_DEFAULT_MODEL, language=DEEPGRAM_DEFAULT_LANGUAGE):
        """Launch background thread to handle WebSocket streaming."""
        self._thread = threading.Thread(
            target=self._run,
            args=(audio_queue, on_transcript, model, language),
            daemon=True,
        )
        self._thread.start()

    def _run(self, audio_queue, on_transcript, model, language):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._connect(audio_queue, on_transcript, model, language))
        finally:
            loop.close()

    async def _connect(self, audio_queue, on_transcript, model, language):
        url = (
            f"wss://api.deepgram.com/v1/listen"
            f"?encoding=linear16&sample_rate={AUDIO_SAMPLE_RATE}&channels=1"
            f"&model={model}&language={language}&punctuate=true&interim_results=true"
        )
        headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
        parts = []

        try:
            async with websockets.connect(url, additional_headers=headers) as ws:
                await asyncio.gather(
                    self._send_audio(ws, audio_queue),
                    self._receive(ws, parts),
                )
        except Exception:
            pass

        on_transcript(" ".join(p for p in parts if p))

    @staticmethod
    async def _send_audio(ws, audio_queue):
        loop = asyncio.get_event_loop()
        while True:
            chunk = await loop.run_in_executor(None, audio_queue.get)
            if chunk is None:
                await ws.send(b"")   # flush signal
                break
            await ws.send(chunk)

    @staticmethod
    async def _receive(ws, parts):
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if msg.get("is_final"):
                alts = msg.get("channel", {}).get("alternatives", [])
                if alts:
                    text = alts[0].get("transcript", "").strip()
                    if text:
                        parts.append(text)