"""
hotkey_manager.py
Listens for a global modifier-key hold/release on Windows.
Requires running as Administrator to work inside all applications.
"""

import threading
import keyboard
from config import HOTKEY_OPTIONS, DEFAULT_HOTKEY


class HotkeyManager:
    def __init__(self):
        # Using Ctrl due to compatibility issues with Right Alt on Windows
        self._key     = "ctrl"
        self._pressed = False
        self._on_press   = None
        self._on_release = None

    def set_hotkey(self, display_name: str):
        self._key = HOTKEY_OPTIONS.get(display_name, self._key)

    def start(self, on_press, on_release):
        self._on_press   = on_press
        self._on_release = on_release
        keyboard.on_press_key(self._key,   self._handle_press,   suppress=False)
        keyboard.on_release_key(self._key, self._handle_release, suppress=False)

    def stop(self):
        keyboard.unhook_all()

    def _handle_press(self, _):
        if not self._pressed and self._on_press:
            self._pressed = True
            threading.Thread(target=self._on_press, daemon=True).start()

    def _handle_release(self, _):
        if self._pressed and self._on_release:
            self._pressed = False
            threading.Thread(target=self._on_release, daemon=True).start()