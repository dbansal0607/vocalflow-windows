"""
settings_gui.py
Tkinter settings window — three tabs:
  • API Keys    → manage keys at runtime
  • Balance     → Deepgram credit balance + Groq rate-limit usage  ← EXTRA FEATURE
  • Settings    → hotkey, post-processing toggles
"""

import threading
import tkinter as tk
from tkinter import messagebox, ttk
from config import HOTKEY_OPTIONS


class SettingsWindow:
    def __init__(self, app_state, deepgram_svc, groq_svc):
        self.state = app_state
        self.dg    = deepgram_svc
        self.groq  = groq_svc

    def run(self):
        root = tk.Tk()
        root.title("VocalFlow — Settings")
        root.geometry("520x500")
        root.resizable(False, False)

        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=12, pady=10)

        self._api_tab(nb)
        self._balance_tab(nb)
        self._settings_tab(nb)
        root.mainloop()

    # ── API Keys ──────────────────────────────────────────────────────────

    def _api_tab(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="  API Keys  ")

        for i, (label, key) in enumerate([
            ("Deepgram API Key:", "deepgram_api_key"),
            ("Groq API Key:",     "groq_api_key"),
        ]):
            row = i * 4
            ttk.Label(f, text=label, font=("Segoe UI", 9, "bold")).grid(
                row=row, column=0, sticky="w", padx=14, pady=(20, 2))
            var = tk.StringVar(value=self.state.get(key, ""))
            entry = ttk.Entry(f, textvariable=var, show="•", width=52)
            entry.grid(row=row+1, column=0, padx=14)

            ttk.Button(f, text="Show/Hide",
                       command=lambda e=entry: e.config(show="" if e.cget("show") == "•" else "•"),
                       width=10).grid(row=row+1, column=1, padx=4)

            def save(k=key, v=var):
                self.state[k] = v.get()
                messagebox.showinfo("Saved", "Key saved ✓")
            ttk.Button(f, text="Save", command=save, width=8).grid(
                row=row+2, column=0, sticky="w", padx=14, pady=(4, 0))

        ttk.Label(f, text="Get free keys: console.deepgram.com  |  console.groq.com",
                  foreground="gray", font=("Segoe UI", 8)).grid(
            row=9, column=0, padx=14, pady=(30, 0), sticky="w")

    # ── Balance & Usage ───────────────────────────────────────────────────

    def _balance_tab(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="  Balance & Usage  ")

        # Deepgram
        ttk.Label(f, text="Deepgram Credit Balance",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(18, 4))
        dg_frame = ttk.LabelFrame(f, text="Deepgram", padding=10)
        dg_frame.pack(fill="x", padx=16, pady=(0, 12))

        dg_bal_var = tk.StringVar(value="— click Refresh —")
        dg_err_var = tk.StringVar(value="")
        ttk.Label(dg_frame, text="Balance:").grid(row=0, column=0, sticky="w")
        ttk.Label(dg_frame, textvariable=dg_bal_var,
                  font=("Segoe UI", 11, "bold"), foreground="#1a7f4b").grid(
            row=0, column=1, sticky="w", padx=12)
        ttk.Label(dg_frame, textvariable=dg_err_var,
                  foreground="red", font=("Segoe UI", 8)).grid(row=1, column=0, columnspan=2, sticky="w")

        # Groq
        ttk.Label(f, text="Groq API Usage",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(4, 4))
        groq_frame = ttk.LabelFrame(f, text="Groq", padding=10)
        groq_frame.pack(fill="x", padx=16, pady=(0, 12))

        gq_vars = {k: tk.StringVar(value="—") for k in
                   ("status", "req_remaining", "req_limit", "tok_remaining", "tok_limit", "reset_at")}

        for i, (lbl, key) in enumerate([
            ("Status",               "status"),
            ("Requests remaining",   "req_remaining"),
            ("Requests limit",       "req_limit"),
            ("Tokens remaining",     "tok_remaining"),
            ("Tokens limit",         "tok_limit"),
            ("Quota resets at",      "reset_at"),
        ]):
            ttk.Label(groq_frame, text=f"{lbl}:").grid(row=i, column=0, sticky="w", pady=1)
            ttk.Label(groq_frame, textvariable=gq_vars[key],
                      foreground="#1a7f4b" if key == "status" else "black").grid(
                row=i, column=1, sticky="w", padx=12)

        # Refresh button
        btn = ttk.Button(f, text="⟳  Refresh", width=16)
        btn.pack(pady=6)

        def refresh():
            btn.config(state="disabled", text="Fetching…")
            def _fetch():
                from src.deepgram_service import get_deepgram_balance
                from src.groq_service     import get_groq_usage
                dg = get_deepgram_balance()
                dg_bal_var.set(dg["balance"])
                dg_err_var.set(dg.get("error") or "")
                gq = get_groq_usage()
                for k, v in gq_vars.items():
                    v.set(gq.get(k, "N/A"))
                btn.config(state="normal", text="⟳  Refresh")
            threading.Thread(target=_fetch, daemon=True).start()

        btn.config(command=refresh)

    # ── Settings ──────────────────────────────────────────────────────────

    def _settings_tab(self, nb):
        f = ttk.Frame(nb)
        nb.add(f, text="  Settings  ")

        ttk.Label(f, text="Hotkey (hold to record):",
                  font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=14, pady=(18, 2))
        hk_var = tk.StringVar(value=self.state.get("hotkey", list(HOTKEY_OPTIONS.keys())[0]))
        ttk.Combobox(f, textvariable=hk_var, values=list(HOTKEY_OPTIONS.keys()),
                     state="readonly", width=36).grid(row=1, column=0, padx=14, sticky="w")

        ttk.Label(f, text="Post-processing (requires Groq key):",
                  font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", padx=14, pady=(20, 4))

        spell_var   = tk.BooleanVar(value=self.state.get("fix_spelling", False))
        grammar_var = tk.BooleanVar(value=self.state.get("fix_grammar",  False))
        ttk.Checkbutton(f, text="Spelling correction", variable=spell_var).grid(
            row=3, column=0, sticky="w", padx=28)
        ttk.Checkbutton(f, text="Grammar correction",  variable=grammar_var).grid(
            row=4, column=0, sticky="w", padx=28)

        trans_var = tk.BooleanVar(value=self.state.get("translate_enabled", False))
        ttk.Checkbutton(f, text="Translate output to:", variable=trans_var).grid(
            row=5, column=0, sticky="w", padx=28, pady=(12, 0))

        lang_var = tk.StringVar(value=self.state.get("translate_to", "English"))
        ttk.Combobox(f, textvariable=lang_var, state="readonly", width=28,
                     values=["English","Hindi","Spanish","French","German",
                             "Japanese","Korean","Arabic","Bengali","Tamil"]).grid(
            row=6, column=0, padx=44, sticky="w")

        def save():
            self.state.update({
                "hotkey"           : hk_var.get(),
                "fix_spelling"     : spell_var.get(),
                "fix_grammar"      : grammar_var.get(),
                "translate_enabled": trans_var.get(),
                "translate_to"     : lang_var.get(),
            })
            messagebox.showinfo("Saved", "Settings saved ✓\nRestart app to apply hotkey changes.")

        ttk.Button(f, text="Save Settings", command=save).grid(
            row=7, column=0, sticky="w", padx=14, pady=20)