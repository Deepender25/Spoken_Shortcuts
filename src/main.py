import sys
import os
import threading
import json
import time

# Ensure we run from the project root (parent of 'src')
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
os.chdir(project_root)

# Add src to path if needed (though running this file usually puts it in path)
if 'src' not in sys.path:
    sys.path.append('src')

from listener import AudioListener
from launcher import AppLauncher
from tray import TrayIcon

def main():
    print("Starting Spoken_Shortcuts...")
    
    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Config not found, creating default.")
        config = {"apps": ["calc.exe"], "clap_threshold": 3000, "wake_phrase": "wake up"}

    launcher = AppLauncher(config['apps'])
    listener = AudioListener(config, launcher)
    tray = TrayIcon(listener)

    # Start listener in a separate thread
    listener_thread = threading.Thread(target=listener.run)
    listener_thread.daemon = True
    listener_thread.start()

    # Run Tray icon (blocking)
    tray.run()

if __name__ == "__main__":
    main()
