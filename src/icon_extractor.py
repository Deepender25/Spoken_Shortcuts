import os
import sys
import win32gui
import win32ui
import win32con
import win32api
import shutil
from PIL import Image
import ctypes
from win32com.client import Dispatch

class AppScanner:
    def __init__(self):
        self.apps = []
        self.shell = Dispatch('WScript.Shell')

    def get_start_menu_paths(self):
        paths = [
            os.path.join(os.environ['ProgramData'], r'Microsoft\Windows\Start Menu\Programs'),
            os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs')
        ]
        return paths

    def scan(self):
        """Scans start menu for .lnk files"""
        self.apps = []
        for root_path in self.get_start_menu_paths():
            if not os.path.exists(root_path):
                continue
                
            for root, dirs, files in os.walk(root_path):
                for file in files:
                    if file.lower().endswith('.lnk'):
                        full_path = os.path.join(root, file)
                        try:
                            # Resolve shortcut
                            shortcut = self.shell.CreateShortCut(full_path)
                            target_path = shortcut.Targetpath
                            
                            # Filter out uninstallers, help files, etc if needed
                            # For now we verify target exists
                            if os.path.exists(target_path) or os.path.exists(target_path + ".exe"):
                                name = os.path.splitext(file)[0]
                                self.apps.append({
                                    "name": name,
                                    "path": target_path,
                                    "lnk_path": full_path # Icon source
                                })
                        except Exception as e:
                            pass # Skip unreadable shortcuts
                            
        # Sort by name
        self.apps.sort(key=lambda x: x['name'].lower())
        return self.apps

    def extract_icon(self, path, size=32):
        """
        Extracts icon from exe or lnk and returns PIL Image.
        Returns generic icon if fails.
        """
        try:
            # win32gui.ExtractIconEx returns large and small icons
            # We treat path as potential source. 
            # If it's a .lnk, we might want to ask Windows for the icon
            # But ExtractIconEx works well on .exe and .dll
            
            # Simple approach: Use ExtractIconEx on the target path if possible
            # But getting the right icon index is hard without IShellLink.
            
            # Better approach for Tkinter/PIL on Windows:
            # Use SHGetFileInfo
            
            file_flags = win32con.FILE_ATTRIBUTE_NORMAL
            flags = win32con.SHGFI_ICON | win32con.SHGFI_USEFILEATTRIBUTES
            
            if size > 16:
                 flags |= win32con.SHGFI_LARGEICON
            else:
                 flags |= win32con.SHGFI_SMALLICON
            
            # If it's an existing file, don't use USEFILEATTRIBUTES to obtain the actual file icon
            if os.path.exists(path):
                flags = win32con.SHGFI_ICON | (win32con.SHGFI_LARGEICON if size > 16 else win32con.SHGFI_SMALLICON)
                
            h_icon_info = win32gui.SHGetFileInfo(path, 0, flags)
            hIcon = h_icon_info[0]

            if hIcon == 0:
                return None

            # Create a PyCBitmap from the icon handle
            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            hbmp = win32ui.CreateBitmap()
            
            # We need to draw the icon into a bitmap
            # This is complex in pure python pywin32 without memory leaks
            # Let's try a safer way using only handles if possible or 
            # standard drawing.
            
            # Actually, standard approach:
            ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
            ico_y = win32api.GetSystemMetrics(win32con.SM_CYICON)
            
            mem_dc = hdc.CreateCompatibleDC()
            hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
            mem_dc.SelectObject(hbmp)
            
            # Draw
            win32gui.DrawIconEx(mem_dc.GetSafeHdc(), 0, 0, hIcon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
            
            # Convert to PIL
            bmpinfo = hbmp.GetInfo()
            bmpstr = hbmp.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)
                
            # Cleanup
            win32gui.DestroyIcon(hIcon)
            win32gui.DeleteObject(hbmp.GetHandle())
            mem_dc.DeleteDC()
            
            return img
            
        except Exception as e:
            # print(f"Icon extract fail: {e}")
            return None
