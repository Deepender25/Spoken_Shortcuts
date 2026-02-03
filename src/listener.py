import json
import queue
import sys
import sounddevice as sd
import vosk
import numpy as np
import time

class AudioListener:
    def __init__(self, config, launcher):
        self.config = config
        self.launcher = launcher
        self.running = False
        self.paused = False
        self.state = "IDLE"  # IDLE, ACTIVE (Listening for claps)
        
        self.model_path = "model"
        try:
            self.model = vosk.Model(self.model_path)
        except Exception as e:
            print(f"Failed to load model from {self.model_path}: {e}")
            sys.exit(1)
            
        self.rec = vosk.KaldiRecognizer(self.model, 16000)
        self.audio_queue = queue.Queue()
        
        self.wake_phrase = config.get("wake_phrase", "wake up").lower()
        self.trigger_phrase = config.get("trigger_phrase", "open").lower()
        self.active_timeout = 5.0 # Seconds to wait for command
        self.last_wake_time = 0

    def audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.audio_queue.put(bytes(indata))

    def run(self):
        self.running = True
        print("Listener started. Listening for 'Wake Up'...")
        
        with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype='int16',
                               channels=1, callback=self.audio_callback):
            while self.running:
                # Process Audio for Voice
                if not self.paused:
                    try:
                        data = self.audio_queue.get(timeout=0.1)
                        if self.rec.AcceptWaveform(data):
                            result = json.loads(self.rec.Result())
                            text = result.get("text", "")
                            
                            if text:
                                print(f"Heard: {text}")

                            if self.state == "IDLE":
                                if self.wake_phrase in text:
                                    print(f"Wake word '{self.wake_phrase}' detected! Waiting for command...")
                                    self.state = "ACTIVE"
                                    self.last_wake_time = time.time()
                            
                            elif self.state == "ACTIVE":
                                if self.trigger_phrase in text:
                                    print("Command 'open' detected! Launching apps...")
                                    self.launcher.launch_all()
                                    self.state = "IDLE"
                                    self.paused = True
                                    print("Paused. Enable via tray icon.")

                    except queue.Empty:
                        pass
                else:
                     try:
                        self.audio_queue.get(timeout=0.1)
                     except queue.Empty:
                        pass

                # Handle Timeout
                if self.state == "ACTIVE":
                    if time.time() - self.last_wake_time > self.active_timeout:
                        print("Timeout waiting for command. Returning to IDLE.")
                        self.state = "IDLE"

    def stop(self):
        self.running = False
