# text_to_speech.py
import threading
import queue
import time

class TextToSpeech:
    """
    Singleton TTS manager. Initializes pyttsx3 INSIDE the background thread to avoid
    thread-affinity issues and keeps the engine alive for the app lifetime.

    Usage:
        tts = TextToSpeech()
        tts.speak("Hello")
        ...
        tts.stop()  # only when shutting down the entire app
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()
        return cls._instance

    def _init(self):
        self._q = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        # small guard so thread has time to init engine if needed
        time.sleep(0.05)

    def _worker(self):
        """
        Worker thread: initializes pyttsx3 here and processes the queue.
        This avoids issues where the engine was created in one thread and used in another.
        """
        try:
            import pyttsx3
        except Exception as e:
            # If pyttsx3 is missing, print and exit worker
            print("TextToSpeech worker: pyttsx3 import failed:", e)
            return

        try:
            # Initialize engine inside this worker thread
            # Use sapi5 on Windows for best results
            try:
                self.engine = pyttsx3.init("sapi5")
            except Exception:
                self.engine = pyttsx3.init()

            # Set default voice properties
            self.engine.setProperty("rate", 160)
            self.engine.setProperty("volume", 1.0)
            voices = self.engine.getProperty("voices")
            if voices:
                # Keep default voice (voices[0]) or choose another index
                self.engine.setProperty("voice", voices[0].id)
        except Exception as e:
            # If engine init fails, print and stop worker
            print("TextToSpeech worker: engine init failed:", e)
            return

        while not self._stop_event.is_set():
            try:
                text = self._q.get(timeout=0.2)
            except queue.Empty:
                continue

            if text is None:
                # shutdown signal
                break

            try:
                # speak synchronously inside this thread
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as ex:
                # don't crash the thread; print and continue
                print("TextToSpeech engine error:", ex)
            finally:
                # small pause to avoid overwhelming the engine
                time.sleep(0.05)

        # cleanup if engine supports stop
        try:
            if hasattr(self, "engine"):
                try:
                    self.engine.stop()
                except Exception:
                    pass
        except Exception:
            pass

    def speak(self, text: str):
        """Queue text for speaking (non-blocking)."""
        if not text:
            return
        # Only put plain strings; keep queue small by discarding empty
        self._q.put(text)

    def stop(self, wait: bool = False, timeout: float = 2.0):
        """
        Shutdown the TTS thread. Call this only when app is exiting.
        wait: whether to join the thread
        """
        self._q.put(None)
        self._stop_event.set()
        if wait:
            try:
                self._thread.join(timeout=timeout)
            except Exception:
                pass
