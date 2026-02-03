import subprocess
import os
import shutil

class AppLauncher:
    def __init__(self, apps):
        self.apps = apps # List of app paths (AUMID or file path)

    def launch_all(self):
        print(f"Launching {len(self.apps)} apps...")
        for app in self.apps:
            self.launch_app(app)

    def launch_app(self, path):
        """Launches a single app by path or AUMID"""
        print(f"Launching: {path}")
        try:
            # 1. Try standard file execution (works for .exe, .lnk, .url, etc.)
            if os.path.exists(path):
                # os.startfile is the Windows equivalent of "double clicking"
                os.startfile(path)
                return

            # 2. Assume AUMID/Shell Path
            # Use os.startfile with shell:AppsFolder\{AUMID}
            # Experiments showed that '\' works better than '!' for os.startfile
            try:
                uri = f"shell:AppsFolder\\{path}"
                os.startfile(uri)
                return
            except Exception as e:
                # Fallback to explorer method if os.startfile fails
               pass

            # 3. Fallback: Explorer with '!' separator (sometimes works where startfile fails?)
            # But usually 'start shell:AppsFolder!{path}' is what CMD does.
            cmd = f'explorer.exe shell:AppsFolder!{path}'
            subprocess.Popen(cmd, shell=True)
            
        except Exception as e:
            print(f"Failed to launch {path}: {e}")
