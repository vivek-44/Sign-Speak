# sequence_processor.py
from text_to_speech import TextToSpeech
import time
from collections import deque

class SequenceProcessor:
    def __init__(self):
        # store tokens
        self.sequence = []
        self.max_sequence_length = 30

        # singleton TTS manager
        self.tts = TextToSpeech()

        # speaking control: prevent speaking same token repeatedly
        self._last_spoken = None
        self._last_speak_time = 0.0
        self.speak_cooldown = 0.5  # seconds between speaking the same token

        # Optional de-duplication window as additional protection
        self.recent = deque(maxlen=5)

    def add_to_sequence(self, text: str):
        """Add token (avoid consecutive duplicates) and speak it once."""
        if not text:
            return

        if self.sequence and self.sequence[-1] == text:
            return

        if len(self.sequence) >= self.max_sequence_length:
            self.sequence.pop(0)

        self.sequence.append(text)

        # optional minor recent duplicate check
        if len(self.recent) and self.recent[-1] == text:
            # if it was very recent, skip speaking
            self.recent.append(text)
            return

        self.recent.append(text)

        # speak with a cooldown to avoid beating the engine
        now = time.time()
        if text != self._last_spoken or (now - self._last_speak_time) >= self.speak_cooldown:
            self._last_spoken = text
            self._last_speak_time = now
            self.tts.speak(text)

    def get_sequence(self) -> str:
        return " ".join(self.sequence)

    def clear_sequence(self):
        self.sequence.clear()
        self.recent.clear()
        self._last_spoken = None

    def speak_full_sequence(self):
        s = self.get_sequence()
        if s:
            self.tts.speak(s)

    def shutdown_tts(self, wait: bool = False):
        """Call at application exit to stop TTS thread cleanly."""
        self.tts.stop(wait=wait)
