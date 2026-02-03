import os
import sys
import win32gui
import win32ui
import win32con
import win32api
import pythoncom
from PIL import Image
from win32com.client import Dispatch
from win32com.shell import shell, shellcon

class AppScanner:
    def __init__(self):
        self.apps = []
        try:
            pythoncom.CoInitialize()
        except:
            pass
        self.wscript = Dispatch("WScript.Shell")

    def get_start_menu_paths(self):
        # Common locations for apps and shortcuts
        user_profile = os.environ['USERPROFILE']
        prog_data = os.environ.get('ProgramData', r'C:\ProgramData')
        app_data = os.environ.get('APPDATA', os.path.join(user_profile, r'AppData\Roaming'))
        
        paths = [
            os.path.join(prog_data, r'Microsoft\Windows\Start Menu\Programs'),
            os.path.join(app_data, r'Microsoft\Windows\Start Menu\Programs'),
            os.path.join(user_profile, r'Desktop')
        ]
        return paths

    def resolve_shortcut(self, path):
        try:
            if path.lower().endswith('.lnk'):
                shortcut = self.wscript.CreateShortcut(path)
                return shortcut.TargetPath
        except:
            pass
        return path

    def scan_filesystem(self):
        """Scans filesystem for .lnk files"""
        fs_apps = {} # Name -> Path
        
        for root_path in self.get_start_menu_paths():
            if not os.path.exists(root_path):
                continue
                
            for root, dirs, files in os.walk(root_path):
                for file in files:
                    # Look for .lnk to catch Browser Apps
                    if file.lower().endswith('.lnk'):
                        try:
                            name = os.path.splitext(file)[0]
                            full_path = os.path.join(root, file)
                            
                            # Filter
                            lower_name = name.lower()
                            if "uninstall" in lower_name or "documentation" in lower_name or "readme" in lower_name:
                                continue
                                
                            fs_apps[name] = full_path
                        except:
                            pass
        return fs_apps

    def scan(self):
        """
        Hybrid scan: Shell Discovery + Filesystem LNK matching
        """
        self.apps = []
        seen_names = set()
        
        # 1. Shell Scan
        shell_items = []
        try:
            shell_app = Dispatch('Shell.Application')
            apps_folder = shell_app.NameSpace("shell:AppsFolder")
            if apps_folder:
                for item in apps_folder.Items():
                    shell_items.append(item)
        except Exception as e:
            print(f"Shell scan error: {e}")

        # 2. Filesystem Scan
        lnk_map = self.scan_filesystem()
        
        # 3. Process Shell Items
        for item in shell_items:
            try:
                name = item.Name
                path = item.Path 
                
                if not name or not path:
                    continue
                
                if name.lower() in seen_names:
                    continue

                if "uninstall" in name.lower():
                    continue

                # Prefer LNK path if available (for better icon extraction)
                final_path = path
                if name in lnk_map:
                     final_path = lnk_map[name]
                
                self.apps.append({
                    "name": name,
                    "path": final_path
                })
                seen_names.add(name.lower())
                
            except:
                continue
                
        # 4. Add leftover LNKs
        for name, path in lnk_map.items():
            if name.lower() not in seen_names:
                self.apps.append({
                    "name": name,
                    "path": path
                })
                seen_names.add(name.lower())

        self.apps.sort(key=lambda x: x['name'].lower())
        return self.apps

    def extract_icon(self, path, size=32):
        """
        Extracts icon. Robust strategy:
        1. SHGetFileInfo (Standard)
        2. SHGetFileInfo (PIDL) (For UWP)
        3. ExtractIconEx (For stubborn .exe/.lnk)
        """
        hIcon = 0
        try:
            flags = shellcon.SHGFI_ICON | (shellcon.SHGFI_LARGEICON if size > 16 else shellcon.SHGFI_SMALLICON)
            
            # Strategy A: Standard File Path
            try:
                ret = win32gui.SHGetFileInfo(path, 0, flags)
                if ret and ret[0] > 0:
                    hIcon = ret[0]
            except:
                pass

            # Strategy B: PIDL (if A failed and path is not a file, e.g. AUMID)
            if hIcon == 0:
                try:
                    parsing_name = f"shell:AppsFolder\\{path}"
                    pidl, _ = shell.SHParseDisplayName(parsing_name, 0)
                    ret = shell.SHGetFileInfo(pidl, 0, flags | shellcon.SHGFI_PIDL)
                    if ret and ret[0] > 0:
                        hIcon = ret[0]
                except:
                    pass

            # Strategy C: ExtractIconEx (Fallback for files/shortcuts)
            if hIcon == 0 and os.path.exists(path):
                try:
                    # Resolve if LNK
                    target = self.resolve_shortcut(path)
                    if os.path.exists(target):
                        # Extract from executable
                        large, small = win32gui.ExtractIconEx(target, 0, 1)
                        if large:
                            hIcon = large[0]
                except:
                    pass

            if hIcon == 0:
                return None

            # Create Bitmap Context
            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            hbmp = win32ui.CreateBitmap()
            ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
            ico_y = win32api.GetSystemMetrics(win32con.SM_CYICON)
            mem_dc = hdc.CreateCompatibleDC()
            hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
            mem_dc.SelectObject(hbmp)
            
            # Draw
            try:
                # Try win32ui method first
                mem_dc.DrawIcon((0, 0), hIcon)
            except:
                try:
                    # Fallback to win32gui
                    win32gui.DrawIconEx(mem_dc.GetSafeHdc(), 0, 0, hIcon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
                except:
                    # If drawing fails, we can't do anything
                    # Don't return None yet, maybe we can try cleanup?
                    pass

            # Convert to PIL
            try:
                bmpinfo = hbmp.GetInfo()
                bmpstr = hbmp.GetBitmapBits(True)
                img = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1)
            except:
                img = None

            # Cleanup
            try:
                win32gui.DestroyIcon(hIcon)
            except:
                pass
            
            win32gui.DeleteObject(hbmp.GetHandle())
            mem_dc.DeleteDC()
            
            return img
            
        except Exception as e:
            return None
