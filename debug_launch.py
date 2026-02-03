
import os
import time

def test_launch():
    # The AUMID from user's config
    app_id = "music.youtube.com-5929F88E_vezhnr0wkvrcy!App"
    
    print(f"Testing launch for: {app_id}")
    
    # Try with ! separator (Standard for AUMID launching via explorer)
    uri2 = f"shell:AppsFolder!{app_id}"
    print(f"URI2 (Bang): {uri2}")
    try:
        print("Attempting os.startfile(uri2)...")
        os.startfile(uri2)
        print("Success A?") 
    except Exception as e:
        print(f"Failed A: {e}")

    time.sleep(2)

    # Try with \ separator (Standard for Parsing names)
    uri = f"shell:AppsFolder\\{app_id}"
    print(f"URI (Backslash): {uri}")
    
    try:
        print("Attempting os.startfile(uri)...")
        os.startfile(uri)
        print("Success B?")
    except Exception as e:
        print(f"Failed B: {e}")

if __name__ == "__main__":
    test_launch()
