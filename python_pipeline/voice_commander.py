"""
voice_commander.py — Keyword Detection Voice Command Module

Uses the SpeechRecognition library with Google Speech API for
basic keyword detection. Runs in a background thread, fires a
callback on recognised keyword.

Supported keywords:
  "night mode"   → activate night vision
  "normal mode"  → deactivate night vision
  "identify"     → force face identification pass
  "capture"      → save current frame
  "stop"         → shutdown pipeline

ROADMAP: Replace Google API with offline pocketsphinx or Whisper
         for helmet use without internet dependency.
"""

import speech_recognition as sr
import time


KEYWORDS = ["night mode", "normal mode", "identify", "capture", "stop"]


class VoiceCommander:
    def __init__(self, callback):
        """
        Args:
            callback : function(command: str) — called on keyword detection
        """
        self.recogniser   = sr.Recognizer()
        self.callback     = callback
        self.last_command = ""
        self.running      = True

        # Calibration settings
        self.recogniser.energy_threshold     = 300
        self.recogniser.dynamic_energy_threshold = True
        self.recogniser.pause_threshold      = 0.5

    def listen(self):
        """
        Continuous background listening loop.
        Runs on a daemon thread — call via threading.Thread(target=voice.listen).
        """
        print("[VOICE] Calibrating microphone — keep quiet for 2 seconds...")
        with sr.Microphone() as source:
            self.recogniser.adjust_for_ambient_noise(source, duration=2)
            print("[VOICE] Ready — listening for keywords")

            while self.running:
                try:
                    audio = self.recogniser.listen(source, timeout=5, phrase_time_limit=4)
                    text  = self.recogniser.recognize_google(audio).lower()
                    print(f"[VOICE] Heard: '{text}'")

                    for keyword in KEYWORDS:
                        if keyword in text:
                            self.last_command = keyword
                            self.callback(keyword)
                            break

                except sr.WaitTimeoutError:
                    pass  # No speech detected — continue listening
                except sr.UnknownValueError:
                    pass  # Could not parse audio — continue
                except sr.RequestError as e:
                    print(f"[VOICE] API error: {e} — retrying in 3s")
                    time.sleep(3)

    def stop(self):
        self.running = False
