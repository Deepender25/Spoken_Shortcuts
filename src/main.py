import sys
import os
import threading
import json
import time
import logging

# Ensure we run from the project root (parent of 'src')
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
os.chdir(project_root)

# Set up logging
log_file = os.path.join(project_root, 'wake.log')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add src to path if needed (though running this file usually puts it in path)
if 'src' not in sys.path:
    sys.path.append('src')

from listener import AudioListener
from launcher import AppLauncher
from tray import TrayIcon

def main():
    logging.info("----------------------------------------------------------------")
    logging.info("Starting Spoken_Shortcuts Application...")
    print("Starting Spoken_Shortcuts...")

    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logging.warning("Config not found, creating default.")
        print("Config not found, creating default.")
        config = {"apps": ["calc.exe"], "clap_threshold": 3000, "wake_phrase": "wake up"}
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        config = {"apps": ["calc.exe"], "clap_threshold": 3000, "wake_phrase": "wake up"}

    # Startup Delay (to allow system audio/tray to initialize)
    startup_delay = config.get("startup_delay", 0)
    if startup_delay > 0:
        logging.info(f"Waiting for {startup_delay} seconds startup delay...")
        time.sleep(startup_delay)

    try:
        launcher = AppLauncher(config['apps'])
        listener = AudioListener(config, launcher)
        tray = TrayIcon(listener)

        # Start listener in a separate thread
        listener_thread = threading.Thread(target=listener.run)
        listener_thread.daemon = True
        listener_thread.start()
        logging.info("Listener thread started.")

        # Run Tray icon (blocking)
        logging.info("Starting Tray Icon...")
        tray.run()
    except Exception as e:
        logging.critical(f"Critical Error in main execution: {e}", exc_info=True)
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Fallback logging if main crashes
        with open("crash.log", "a") as f:
            f.write(f"CRASH: {e}\n")

