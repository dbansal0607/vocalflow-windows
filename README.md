# VocalFlow — Windows Port

This is a Windows port of [VocalFlow](https://github.com/Vocallabsai/vocalflow), a hold-to-record dictation tool that transcribes your speech and pastes it wherever your cursor is.

The original is a macOS app written in Swift (AppKit, SwiftUI, AVFoundation). None of that runs on Windows, so I rebuilt it from scratch in Python keeping the same core behavior.

---

## What it does

Hold a hotkey, speak, release — your words appear at the cursor. Works in any app: Notepad, browser, VS Code, whatever.

Under the hood:
- Mic audio is captured and streamed in real-time to Deepgram over WebSocket
- Deepgram returns a transcript (usually within a second of releasing the key)
- Optionally, the transcript goes through Groq for spelling/grammar correction or translation
- The final text is pasted at your cursor via clipboard + Ctrl+V

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.10 | Cross-platform, fast to iterate, strong audio/async ecosystem |
| Speech-to-Text | Deepgram WebSocket API | Real-time streaming, low latency, `nova-3-general` model |
| LLM post-processing | Groq API (llama-3.3-70b) | Fast inference for spelling/grammar correction and translation |
| Audio capture | `sounddevice` + `numpy` | Low-level mic access, outputs float32 → converted to int16 PCM |
| Hotkey detection | `keyboard` library | Global key hooks that work across all Windows apps |
| Text injection | `pyperclip` + `pyautogui` | Clipboard-based paste — most reliable method across all apps |
| System tray | `pystray` + `Pillow` | Native Windows tray icon with dynamic colour states |
| Settings UI | `tkinter` | Built-in, no extra dependencies, sufficient for a settings panel |
| Config / secrets | `python-dotenv` | Keys loaded from `.env`, never hardcoded or committed |

---

## Architecture

```
 Hotkey held down
      │
      ▼
 HotkeyManager  ──────────────────────────────────┐
      │                                            │
      │ on_press()                      on_release()
      ▼                                            │
 AudioEngine                                       │
 (sounddevice)                                     │
      │                                            │
      │ float32 PCM chunks                         │
      │ converted → int16                          ▼
      └──────────────► DeepgramService  ◄── stop_recording()
                       (WebSocket)             sends b"" flush
                            │
                            │ speech_final transcript
                            ▼
                       GroqService  (optional)
                       spell / grammar / translate
                            │
                            ▼
                       TextInjector
                       clipboard → Ctrl+V → active window
```

The hotkey press and release are the two trigger points. Everything between them — audio capture, streaming, transcription — runs in background daemon threads so the main thread stays free for the tray UI.

---

## Extra features added

**Deepgram balance** — right-click the tray icon → "Show Balance & Usage" to see your remaining Deepgram credit in USD. Calls `GET /v1/projects/{id}/balances`.

**Groq usage** — same popup shows your Groq rate-limit status (requests and tokens remaining, reset time). Groq doesn't have a balance endpoint so I'm reading their rate-limit response headers instead.

---

## Project structure

```
vocalflow-windows/
├── config.py              # all config lives here, keys loaded from .env
├── main.py                # entry point
├── requirements.txt
├── .env.example           # copy this to .env and add your keys
└── src/
    ├── audio_engine.py    # mic capture via sounddevice
    ├── deepgram_service.py
    ├── groq_service.py
    ├── hotkey_manager.py
    ├── text_injector.py   # clipboard paste
    ├── tray_app.py        # system tray icon + menu
    └── settings_gui.py    # tkinter settings window
```

---

## Setup

You need Python 3.10+ and a Deepgram API key (free tier gives $200 credit). Groq is optional.

```bash
git clone https://github.com/dbansal0607/vocalflow-windows
cd vocalflow-windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your keys:

```
DEEPGRAM_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

Run as Administrator (needed for global hotkey detection):

```bash
python main.py
```

You'll see a mic icon in the system tray. Hold **Left Ctrl**, speak, release.

---

## A few things I ran into

**Right Alt doesn't work reliably on Windows.** I initially used Right Alt as the hotkey since that's what felt natural coming from the macOS version. Turns out on Windows, Right Alt is treated as AltGr on most keyboards — internally it registers as Ctrl+Alt, which means it was firing unintended shortcuts in apps like VS Code while recording. Switched the default to Left Ctrl and made all options configurable in `config.py`.

**Deepgram needs an explicit close signal.** If you just close the WebSocket when the user releases the key, you lose the last sentence. Deepgram's protocol requires sending an empty binary frame (`b""`) to tell it you're done — it then flushes and sends a final `speech_final: true` response. Took a bit of digging through their docs to find this.

**Text injection.** The macOS version uses a low-level CGEvent API to simulate keypresses directly. On Windows, `SendInput` doesn't work reliably across all apps — especially anything running as Administrator or built on Electron. Clipboard + Ctrl+V is less elegant but works everywhere.

---

## Original vs this port

| | macOS original | This port |
|---|---|---|
| Language | Swift | Python 3.10 |
| Audio | AVAudioEngine | sounddevice |
| Hotkey | CGEvent tap | keyboard library |
| Text injection | CGEventCreateKeyboardEvent | clipboard + Ctrl+V |
| Tray | macOS menu bar | Windows system tray |

---

*Tested on Windows 11. Should work on Windows 10 as well.*
