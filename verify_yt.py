
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from icon_extractor import AppScanner

def test():
    print("Scanning apps...")
    scanner = AppScanner()
    apps = scanner.scan()
    
    target = "YouTube Music"
    found = next((a for a in apps if target.lower() in a['name'].lower()), None)
    
    if found:
        print(f"Found: {found['name']}")
        print(f"Path: {found['path']}")
    else:
        print("YouTube Music not found in scan.")

    # Also list all "YouTube" apps
    print("\nAll YouTube apps:")
    for app in apps:
        if "youtube" in app['name'].lower():
            print(f"- {app['name']}: {app['path']}")

if __name__ == "__main__":
    test()
