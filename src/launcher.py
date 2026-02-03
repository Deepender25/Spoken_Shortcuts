import subprocess
import os
import shutil

class AppLauncher:
    def __init__(self, apps):
        self.apps = apps # List of app names or paths

    def launch_all(self):
        print(f"Launching {len(self.apps)} apps...")
        for app in self.apps:
            try:
                # If it's a full path, use it. If it's just a name (calc.exe), try to find it.
                if os.path.exists(app):
                    subprocess.Popen(app)
                    print(f"Launched: {app}")
                else:
                    # Try to resolve via shutil.which or just run it shell=True
                    # shell=True allows running "start calc" etc, but subprocess.Popen("calc.exe") usually works if in PATH
                    path = shutil.which(app)
                    if path:
                        subprocess.Popen(path)
                        print(f"Launched: {app}")
                    else:
                        # Fallback: try invoking blindly
                        subprocess.Popen(app, shell=True)
                        print(f"Launched (shell): {app}")
            except Exception as e:
                print(f"Failed to launch {app}: {e}")
