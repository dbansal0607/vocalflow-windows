"""
audio_engine.py
Captures microphone audio on Windows using sounddevice.
Delivers 16-bit PCM chunks to a queue consumed by DeepgramService.
"""

import queue
import numpy as np
import sounddevice as sd
from config import AUDIO_SAMPLE_RATE, AUDIO_CHANNELS, AUDIO_CHUNK_SIZE


class AudioEngine:
    def __init__(self):
        self._stream = None
        self._queue  = queue.Queue()
        self._recording = False

    def start_recording(self):
        """Open mic stream; return queue that receives PCM chunks."""
        self._queue     = queue.Queue()
        self._recording = True

        self._stream = sd.InputStream(
            samplerate=AUDIO_SAMPLE_RATE,
            channels=AUDIO_CHANNELS,
            dtype=np.float32,
            blocksize=AUDIO_CHUNK_SIZE,
            callback=self._callback,
        )
        self._stream.start()
        return self._queue

    def stop_recording(self):
        """Stop capture and push sentinel None so Deepgram knows stream ended."""
        self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._queue.put(None)
        return self._queue

    def _callback(self, indata, frames, time, status):
        if self._recording:
            # float32 [-1, 1] → int16 for Deepgram linear16
            pcm = (indata * 32767).astype(np.int16)
            self._queue.put(pcm.tobytes())