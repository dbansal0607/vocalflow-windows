"""
main.py — VocalFlow for Windows
=================================
Hold Right Alt → speak → release → text appears at your cursor.

Usage:
    python main.py

Note: Run as Administrator for global hotkeys to work in all apps.
"""

import sys
from config import DEEPGRAM_API_KEY, GROQ_API_KEY

from src.audio_engine     import AudioEngine
from src.deepgram_service import DeepgramService
from src.groq_service     import GroqService
from src.text_injector    import TextInjector
from src.hotkey_manager   import HotkeyManager
from src.tray_app         import TrayApp


def check_config():
    if not DEEPGRAM_API_KEY or "PASTE" in DEEPGRAM_API_KEY:
        print("\n[ERROR] Add your Deepgram API key to config.py first.\n"
              "Get a free key: https://console.deepgram.com/signup\n")
        sys.exit(1)
    if not GROQ_API_KEY or "PASTE" in GROQ_API_KEY:
        print("[WARNING] Groq key not set — post-processing disabled.\n"
              "Get a free key: https://console.groq.com\n")


def main():
    check_config()
    print("Starting VocalFlow for Windows…")
    print("Mic icon will appear in your system tray (bottom-right).")
    print("Hold Right Alt to record. Release to transcribe.\n")

    app_state = {
        "deepgram_api_key" : DEEPGRAM_API_KEY,
        "groq_api_key"     : GROQ_API_KEY,
        "hotkey"           : "Right Alt  (default)",
        "fix_spelling"     : False,
        "fix_grammar"      : False,
        "translate_enabled": False,
        "translate_to"     : "English",
    }

    tray = TrayApp(
        app_state,
        HotkeyManager(),
        AudioEngine(),
        DeepgramService(),
        GroqService(),
        TextInjector(),
    )
    tray.run()


if __name__ == "__main__":
    main()