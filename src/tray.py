import pystray
from PIL import Image, ImageDraw
import sys
import os
from startup_manager import StartupManager


class TrayIcon:
    def __init__(self, listener):
        self.listener = listener
        self.icon = None
        self.startup_mgr = StartupManager()
        self.in_startup = False # Determine logic to check if in startup? 
        # Checking registry every time might be okay.

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

    def on_clicked(self, icon, item):
        txt = str(item)
        if txt == 'Exit':
            self.listener.stop()
            icon.stop()
            sys.exit()
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

    def run(self):
        image = self.create_image()
        menu = pystray.Menu(
            pystray.MenuItem('Enable', self.on_clicked, checked=lambda item: not self.listener.paused),
            pystray.MenuItem('Pause', self.on_clicked, checked=lambda item: self.listener.paused),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Add to Startup', self.on_clicked),
            pystray.MenuItem('Remove Startup', self.on_clicked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Exit', self.on_clicked)
        )
        
        self.icon = pystray.Icon("WakeApp", image, "Wake Assistant", menu)
        self.icon.run()

