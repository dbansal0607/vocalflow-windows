# =============================================================================
# VocalFlow for Windows — Configuration
# =============================================================================

import os
from dotenv import load_dotenv

load_dotenv()  # reads from .env file automatically

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
GROQ_API_KEY     = os.getenv("GROQ_API_KEY", "")

# Deepgram defaults
DEEPGRAM_DEFAULT_MODEL    = "nova-3-general"
DEEPGRAM_DEFAULT_LANGUAGE = "en-US"

# Groq default
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Audio settings
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS    = 1
AUDIO_CHUNK_SIZE  = 1024

# Hotkey options
# Default changed from Right Alt to Left Ctrl.
# Reason: Right Alt on many Windows keyboards acts as AltGr (maps to Ctrl+Alt
# internally), which caused ghost keypresses in apps like VS Code and Chrome.
HOTKEY_OPTIONS = {
    "Left Ctrl  (default)": "ctrl",
    "Right Ctrl"           : "right ctrl",
    "Right Alt"            : "right alt",
    "Left Alt"             : "alt",
    "Right Shift"          : "right shift",
}
DEFAULT_HOTKEY = "Left Ctrl  (default)"