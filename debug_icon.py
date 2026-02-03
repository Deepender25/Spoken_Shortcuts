
import win32gui
import win32ui
import win32con
import win32api
from win32com.shell import shell, shellcon
from win32com.client import Dispatch

def debug():
    print("Debug: Testing Icon Location...")
    
    try:
        sh = Dispatch("Shell.Application")
        apps = sh.NameSpace("shell:AppsFolder")
        
        found_item = None
        for item in apps.Items():
            if "Calculator" in item.Name:
                found_item = item
                break
                
        if found_item:
            print(f"Found: {found_item.Name}")
            path = found_item.Path
            parsing_name = f"shell:AppsFolder\\{path}"
            
            pidl, _ = shell.SHParseDisplayName(parsing_name, 0)
            
            # Test SHGFI_ICONLOCATION
            print("Trying SHGFI_ICONLOCATION...")
            flags = shellcon.SHGFI_PIDL | shellcon.SHGFI_ICONLOCATION
            ret = shell.SHGetFileInfo(pidl, 0, flags)
            # ret = (hIcon, iIcon, dwAttributes, DisplayName, TypeName)
            # When SHGFI_ICONLOCATION is set, DisplayName is the path, iIcon is the index?
            # Actually, pywin32 docs are scarce. 
            # In C++, szDisplayName gets the path, iIcon gets the icon index.
            
            print(f"Ret: {ret}")
            icon_path = ret[3]
            icon_index = ret[1]
            print(f"Path: {icon_path}, Index: {icon_index}")
            
            if icon_path and icon_path != "":
                # Try ExtractIconEx with this path
                print(f"Extracting from: {icon_path} index {icon_index}")
                try:
                    # win32gui.ExtractIconEx returns (large_icons, small_icons) list of handles
                    large, small = win32gui.ExtractIconEx(icon_path, icon_index, 1)
                    print(f"Extracted: Large={large}, Small={small}")
                    
                    if large:
                        hIcon = large[0]
                        print(f"Got hIcon: {hIcon}")
                        win32gui.DestroyIcon(hIcon)
                        print("DestroyIcon success on extracted icon")
                except Exception as e:
                    print(f"ExtractIconEx failed: {e}")
            else:
                print("No icon path returned.")

    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    debug()
