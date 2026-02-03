
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from icon_extractor import AppScanner

def test():
    print("Initializing scanner...")
    scanner = AppScanner()
    print("Scanning apps...")
    apps = scanner.scan()
    print(f"Found {len(apps)} apps.")
    
    # Print first 20 apps
    for i, app in enumerate(apps[:20]):
        print(f"{i+1}. {app['name']} -> {app['path']}")

    # Try to find specific apps we care about
    targets = ["Calculator", "Microsoft Edge", "Snipping Tool", "Clock"]
    for target in targets:
        found = next((a for a in apps if target.lower() in a['name'].lower()), None)
        if found:
            print(f"\nFound target: {found['name']}")
            print(f"Path/AUMID: {found['path']}")
            
            # Test icon extraction
            icon = scanner.extract_icon(found['path'])
            if icon:
                print(f"✅ Icon extracted successfully for {found['name']}")
            else:
                print(f"❌ Failed to extract icon for {found['name']}")
        else:
            print(f"\n⚠️ Could not find target app: {target}")

if __name__ == "__main__":
    test()
