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
        self.on_state_change = None # Callback for state changes
        
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

    def set_paused(self, paused):
        self.paused = paused
        if self.on_state_change:
            self.on_state_change(self.paused)

    def audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.audio_queue.put(bytes(indata))

    def run(self):
        self.running = True
        print("Listener started.")
        
        while self.running:
            if not self.paused:
                print("Microphone Active. Listening...")
                try:
                    with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype='int16',
                                           channels=1, callback=self.audio_callback):
                        while self.running and not self.paused:
                            try:
                                data = self.audio_queue.get(timeout=0.5)
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
                                            self.set_paused(True) # Pause and release resources
                                            print("Paused. Enable via tray icon.")
                                
                                # Handle Timeout
                                if self.state == "ACTIVE":
                                    if time.time() - self.last_wake_time > self.active_timeout:
                                        print("Timeout waiting for command. Returning to IDLE.")
                                        self.state = "IDLE"

                            except queue.Empty:
                                pass
                except Exception as e:
                    print(f"Audio stream error: {e}")
                    time.sleep(1) # Wait a bit before retrying if stream fails
            else:
                # Paused state - Minimal resource usage
                time.sleep(0.5)

    def stop(self):
        self.running = False
