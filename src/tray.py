import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw
import sys
import os
import threading
from startup_manager import StartupManager

class TrayIcon:
    def __init__(self, listener):
        self.listener = listener
        self.icon = None
        self.startup_mgr = StartupManager()
        self.root = None # Tkinter root

    def create_image(self):
        # Generate an image for the icon
        width = 64
        height = 64
        color1 = "black"
        color2 = "white"
        
        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.rectangle(
            (width // 2, 0, width, height // 2),
            fill=color2)
        dc.rectangle(
             (0, height // 2, width // 2, height),
            fill=color2)
            
        return image

    def run_settings(self):
        # We need to run UI in main thread usually, or careful with threads
        # Pystray run() blocks. We might need to run pystray in thread or 
        # run Settings in a way that respects the loop.
        
        # Simple hack: Initialize ctk root if needed
        # Initialize COM for the new thread (Required for pywin32 shortcuts)
        import pythoncom
        pythoncom.CoInitialize()

        # Ensure we have a fresh root for the new thread basically
        # Actually in Tkinter, creating a new root in a new thread is risky if another root existed.
        # But here we destroyed the old one (if we did).
        self.root = ctk.CTk()
        self.root.withdraw() # Hide the main root
        
        from gui import SettingsWindow
        
        def on_prop_close():
            # Reload config in listener?
            # Ideally listener reloads config every time it launches apps or we explicitly tell it
            # For now, let's assume it reads config fresh or we instruct it
            # The current listener implementation initiates 'config' in __init__.
            # We should probably reload it.
            self.reload_listener_config()
            
        SettingsWindow(self.root, "config.json", on_prop_close)
        self.root.mainloop()

        # Cleanup so we can recreate next time
        try:
            self.root.destroy()
        except:
            pass
        self.root = None

    def reload_listener_config(self):
        import json
        try:
            with open('config.json', 'r') as f:
                new_conf = json.load(f)
                self.listener.config = new_conf
                self.listener.wake_phrase = new_conf.get("wake_phrase", "wake up").lower()
                self.listener.trigger_phrase = new_conf.get("trigger_phrase", "open").lower()
                self.listener.launcher.apps = new_conf.get("apps", [])
                print("Config reloaded.")
        except Exception as e:
            print(f"Reload failed: {e}")

    def on_clicked(self, icon, item):
        txt = str(item)
        if txt == 'Exit':
            self.listener.stop()
            icon.stop()
            if self.root:
                self.root.quit()
            os._exit(0)
        elif txt == 'Enable':
            self.listener.paused = False
            print("Resumed via Tray.")
        elif txt == 'Pause':
            self.listener.paused = True
            print("Paused via Tray.")
        elif txt == 'Add to Startup':
            self.startup_mgr.add_to_startup()
        elif txt == 'Remove Startup':
            self.startup_mgr.remove_from_startup()
        elif txt == 'Configure Apps':
            pass 

    # We need to restructure Run to handle Tkinter


    def show_settings_safe(self, icon, item):
        t = threading.Thread(target=self.run_settings)
        t.start()

    def run(self):
        image = self.create_image()
        menu = pystray.Menu(
            pystray.MenuItem('Enable', self.on_clicked, checked=lambda item: not self.listener.paused),
            pystray.MenuItem('Pause', self.on_clicked, checked=lambda item: self.listener.paused),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Configure Apps', self.show_settings_safe),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Add to Startup', self.on_clicked),
            pystray.MenuItem('Remove Startup', self.on_clicked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Exit', self.on_clicked)
        )
        
        self.icon = pystray.Icon("WakeApp", image, "Wake Assistant", menu)
        self.icon.run()

