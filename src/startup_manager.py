import winreg
import sys
import os

class StartupManager:
    def __init__(self, app_name="Spoken_Shortcuts"):
        self.app_name = app_name
        self.key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def add_to_startup(self):
        """Adds the current script execution command to Windows Startup registry."""
        # Get the python executable from the venv
        python_exe = sys.executable
        # Get the main.py path. We assume this script is running from the src or root via main
        # Ideally we pass the path to the entry script (src/main.py in root context)
        # Let's verify where we are. 
        # If this is run from main.py, the script path is valid.
        
        # We need the absolute path to main.py
        # This file is in src/, so main.py is in the same directory.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, "main.py")
        
        # Command: "path/to/venv/pythonw.exe" "path/to/src/main.py"
        # Use pythonw.exe to avoid console window if possible, but for now python.exe is safer for debugging.
        # Ideally we use pythonw in production for background tasks.
        pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
        if not os.path.exists(pythonw_exe):
            pythonw_exe = python_exe

        command = f'"{pythonw_exe}" "{script_path}"'
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, command)
            winreg.CloseKey(key)
            print(f"Successfully added to startup: {command}")
            return True
        except Exception as e:
            print(f"Failed to add to startup: {e}")
            return False

    def remove_from_startup(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, self.app_name)
            winreg.CloseKey(key)
            print("Successfully removed from startup.")
            return True
        except FileNotFoundError:
            print("Not in startup.")
            return True
        except Exception as e:
            print(f"Failed to remove from startup: {e}")
            return False
