"""
tray_app.py
Windows system tray application — the main controller.
"""

import threading
from PIL import Image, ImageDraw
import pystray
from config import HOTKEY_OPTIONS


class TrayApp:
    _COLORS = {
        "idle"        : (90,  90,  90),
        "recording"   : (210, 50,  50),
        "transcribing": (50,  120, 210),
    }

    def __init__(self, state, hk_mgr, audio, dg_svc, groq_svc, injector):
        self.state    = state
        self.hk       = hk_mgr
        self.audio    = audio
        self.dg       = dg_svc
        self.groq     = groq_svc
        self.injector = injector
        self.icon     = None

    def run(self):
        self.hk.start(on_press=self._on_press, on_release=self._on_release)

        menu = pystray.Menu(
            pystray.MenuItem("VocalFlow for Windows", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Settings",            self._open_settings),
            pystray.MenuItem("Show Balance & Usage",self._show_balance),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )
        self.icon = pystray.Icon(
            "VocalFlow", self._make_icon("idle"),
            "VocalFlow — Hold Alt to dictate", menu,
        )
        self.icon.run()

    # ── Recording lifecycle ───────────────────────────────────────────────

    def _on_press(self):
        self._set_status("recording")
        queue = self.audio.start_recording()
        self.dg.stream(queue, self._on_transcript)

    def _on_release(self):
        self._set_status("transcribing")
        self.audio.stop_recording()

    def _on_transcript(self, text):
        self._set_status("idle")
        if not text:
            return
        s = self.state
        text = self.groq.process(
            text,
            fix_spelling =s.get("fix_spelling", False),
            fix_grammar  =s.get("fix_grammar",  False),
            translate_to =s.get("translate_to") if s.get("translate_enabled") else None,
        )
        self.injector.inject(text)

    # ── Menu actions ──────────────────────────────────────────────────────

    def _open_settings(self, icon, item):
        from src.settings_gui import SettingsWindow
        threading.Thread(
            target=lambda: SettingsWindow(self.state, self.dg, self.groq).run(),
            daemon=True,
        ).start()

    def _show_balance(self, icon, item):
        def fetch():
            import tkinter as tk
            from tkinter import messagebox
            from src.deepgram_service import get_deepgram_balance
            from src.groq_service     import get_groq_usage

            dg = get_deepgram_balance()
            gq = get_groq_usage()

            dg_line = f"Balance : {dg['balance']}"
            if dg.get("error"):
                dg_line += f"  ({dg['error']})"

            msg = (
                "── Deepgram ──────────────────────\n"
                + dg_line + "\n\n"
                + "── Groq ──────────────────────────\n"
                + f"Status             : {gq.get('status', 'N/A')}\n"
                + f"Requests remaining : {gq.get('req_remaining','N/A')} / {gq.get('req_limit','N/A')}\n"
                + f"Tokens remaining   : {gq.get('tok_remaining','N/A')} / {gq.get('tok_limit','N/A')}\n"
                + f"Quota resets at    : {gq.get('reset_at','N/A')}"
            )

            root = tk.Tk(); root.withdraw()
            messagebox.showinfo("VocalFlow — Balance & Usage", msg)
            root.destroy()

        threading.Thread(target=fetch, daemon=True).start()

    def _quit(self, icon, item):
        self.hk.stop()
        icon.stop()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _set_status(self, state):
        if self.icon:
            self.icon.icon  = self._make_icon(state)
            self.icon.title = {
                "idle"        : "VocalFlow — Hold Alt to dictate",
                "recording"   : "VocalFlow — Recording…",
                "transcribing": "VocalFlow — Transcribing…",
            }.get(state, "VocalFlow")

    @staticmethod
    def _make_icon(state):
        c   = TrayApp._COLORS.get(state, (90, 90, 90))
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d   = ImageDraw.Draw(img)
        d.rounded_rectangle([20, 4, 44, 36], radius=10, fill=c)
        d.arc([12, 24, 52, 52], start=0, end=180, fill=c, width=4)
        d.rectangle([29, 50, 35, 58], fill=c)
        d.rectangle([20, 57, 44, 62], fill=c)
        return img