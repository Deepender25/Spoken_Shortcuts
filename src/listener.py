import json
import queue
import sys
import sounddevice as sd
import vosk
import numpy as np
import time
import logging

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
            logging.info(f"Loading Vosk model from {self.model_path}...")
            self.model = vosk.Model(self.model_path)
            logging.info("Model loaded successfully.")
        except Exception as e:
            logging.critical(f"Failed to load model from {self.model_path}: {e}")
            print(f"Failed to load model from {self.model_path}: {e}")
            sys.exit(1)
            
        self.wake_phrase = config.get("wake_phrase", "wake up").lower()
        self.trigger_phrase = config.get("trigger_phrase", "open").lower()
        self.active_timeout = 5.0 # Seconds to wait for command
        self.last_wake_time = 0

        # Construct Grammar to filter noise
        # Note: Vocabulary must be in the model. If user uses custom words not in model, they warn.
        # But standard small models usually have common words.
        # Grammar format: list of strings.
        # We allow wake phrase, trigger phrase, and [unk] for unknown.
        # If phrases have multiple words, we should include individual words? 
        # Vosk grammar expects a JSON list of strings as the string representation.
        # Example: '["wake up", "open", "[unk]"]'
        
        grammar = [self.wake_phrase, self.trigger_phrase, "[unk]"]
        grammar_str = json.dumps(grammar)
        logging.info(f"Vosk Grammar set to: {grammar_str}")
        
        try:
            self.rec = vosk.KaldiRecognizer(self.model, 16000, grammar_str)
        except Exception as e:
            logging.warning(f"Failed to set grammar ({e}). Falling back to full vocabulary.")
            self.rec = vosk.KaldiRecognizer(self.model, 16000)

        self.audio_queue = queue.Queue()

    def set_paused(self, paused):
        self.paused = paused
        if self.on_state_change:
            self.on_state_change(self.paused)

    def audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            logging.warning(f"Audio status: {status}")
            print(status, file=sys.stderr)
        self.audio_queue.put(bytes(indata))

    def run(self):
        self.running = True
        logging.info("Listener started.")
        print("Listener started.")
        
        while self.running:
            if not self.paused:
                logging.info("Microphone Active. Listening...")
                print("Microphone Active. Listening...")
                try:
                    # Check devices strictly before opening stream
                    # devices = sd.query_devices() # Detailed check could go here
                    
                    with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype='int16',
                                           channels=1, callback=self.audio_callback):
                        while self.running and not self.paused:
                            try:
                                data = self.audio_queue.get(timeout=1.0) # Increased timeout slightly to reduce busy loops
                                if self.rec.AcceptWaveform(data):
                                    result = json.loads(self.rec.Result())
                                    text = result.get("text", "")
                                    
                                    if text and text != "[unk]":
                                        logging.info(f"Heard: {text}")
                                        print(f"Heard: {text}")

                                    if self.state == "IDLE":
                                        if self.wake_phrase in text:
                                            logging.info(f"Wake word '{self.wake_phrase}' detected!")
                                            print(f"Wake word '{self.wake_phrase}' detected! Waiting for command...")
                                            self.state = "ACTIVE"
                                            self.last_wake_time = time.time()
                                    
                                    elif self.state == "ACTIVE":
                                        if self.trigger_phrase in text:
                                            logging.info("Command 'open' detected!")
                                            print("Command 'open' detected! Launching apps...")
                                            self.launcher.launch_all()
                                            self.state = "IDLE"
                                            self.set_paused(True) # Pause and release resources
                                            print("Paused. Enable via tray icon.")
                                
                                # Handle Timeout
                                if self.state == "ACTIVE":
                                    if time.time() - self.last_wake_time > self.active_timeout:
                                        msg = "Timeout waiting for command. Returning to IDLE."
                                        logging.info(msg)
                                        print(msg)
                                        self.state = "IDLE"

                            except queue.Empty:
                                pass
                except Exception as e:
                    logging.error(f"Audio stream error: {e}")
                    print(f"Audio stream error: {e}")
                    time.sleep(2) # Wait a bit before retrying if stream fails
            else:
                # Paused state - Minimal resource usage
                time.sleep(0.5)

    def stop(self):
        self.running = False
