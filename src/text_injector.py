"""
text_injector.py
Pastes text at the current cursor position using clipboard simulation.
"""

import time
import pyperclip
import pyautogui


class TextInjector:
    def inject(self, text: str):
        if not text:
            return
        try:
            previous = pyperclip.paste()
        except Exception:
            previous = ""

        pyperclip.copy(text)
        time.sleep(0.05)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.1)

        try:
            pyperclip.copy(previous)
        except Exception:
            pass