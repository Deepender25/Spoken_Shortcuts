import customtkinter as ctk
import json
import threading
from icon_extractor import AppScanner
from PIL import Image
import os

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, config_path, on_close_callback):
        super().__init__(parent)
        self.title("Wake Assistant - Select Apps")
        self.geometry("600x700")
        
        self.config_path = config_path
        self.on_close_callback = on_close_callback
        self.scanner = AppScanner()
        self.apps_data = [] # List of dicts {name, path, img, var}
        
        # Bring to front
        self.lift()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header = ctk.CTkFrame(self)
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.lbl_title = ctk.CTkLabel(self.header, text="Select Apps to Launch", font=("Arial", 18, "bold"))
        self.lbl_title.pack(side="left", padx=10)
        
        self.entry_search = ctk.CTkEntry(self.header, placeholder_text="Search...")
        self.entry_search.pack(side="right", padx=10)
        self.entry_search.bind("<KeyRelease>", self.filter_list)

        # Content Area (Scrollable)
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Installed Applications")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.scroll_frame.grid_columnconfigure(1, weight=1) # Name column expands

        # Loading Indicator
        self.lbl_loading = ctk.CTkLabel(self.scroll_frame, text="Scanning apps... Please wait.")
        self.lbl_loading.pack(pady=20)

        # Footer
        self.footer = ctk.CTkFrame(self)
        self.footer.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        self.btn_save = ctk.CTkButton(self.footer, text="Save & Close", command=self.save_and_close)
        self.btn_save.pack(side="right", padx=10)
        
        self.btn_cancel = ctk.CTkButton(self.footer, text="Cancel", fg_color="transparent", border_width=1, command=self.destroy_window)
        self.btn_cancel.pack(side="left", padx=10)

        # Load apps async
        threading.Thread(target=self.load_apps, daemon=True).start()

    def load_apps(self):
        # 1. Load Current Config
        current_apps = []
        try:
            with open(self.config_path, 'r') as f:
                conf = json.load(f)
                current_apps = [os.path.normpath(p).lower() for p in conf.get("apps", [])]
        except:
            pass

        # 2. Scan Apps
        scanned = self.scanner.scan()
        
        # 3. Prepare UI Items on Main Thread
        # Since we are in thread, we can't draw directly efficiently or safely sometimes
        # But we prepare data
        
        final_list = []
        for app in scanned:
            # Extract icon
            icon_img = self.scanner.extract_icon(app['path'])
            ctk_img = None
            if icon_img:
                ctk_img = ctk.CTkImage(light_image=icon_img, dark_image=icon_img, size=(24, 24))
            
            is_selected = os.path.normpath(app['path']).lower() in current_apps
            
            final_list.append({
                "name": app['name'],
                "path": app['path'],
                "icon": ctk_img,
                "selected": is_selected
            })
            
        self.after(0, lambda: self.populate_ui(final_list))

    def populate_ui(self, app_list):
        self.lbl_loading.destroy()
        self.apps_data = [] # Store widget refs
        
        for app in app_list:
            # Checkbox variable
            var = ctk.BooleanVar(value=app['selected'])
            
            # Row Frame
            row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            # Checkbox
            chk = ctk.CTkCheckBox(row, text="", variable=var, width=24)
            chk.pack(side="left", padx=5)
            
            # Icon
            if app['icon']:
                lbl_icon = ctk.CTkLabel(row, text="", image=app['icon'])
                lbl_icon.pack(side="left", padx=5)
            
            # Name
            lbl_name = ctk.CTkLabel(row, text=app['name'], anchor="w")
            lbl_name.pack(side="left", fill="x", expand=True, padx=5)
            
            self.apps_data.append({
                "frame": row,
                "name": app['name'].lower(),
                "path": app['path'],
                "var": var
            })

    def filter_list(self, event=None):
        query = self.entry_search.get().lower()
        for item in self.apps_data:
            if query in item["name"]:
                item["frame"].pack(fill="x", pady=2)
            else:
                item["frame"].pack_forget()

    def save_and_close(self):
        selected_paths = []
        for item in self.apps_data:
            if item["var"].get():
                selected_paths.append(item["path"])
        
        # Read existing to keep other settings
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
        except:
            data = {"wake_phrase": "wake up", "trigger_phrase": "open"}
            
        data["apps"] = selected_paths
        
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=4)
            
        if self.on_close_callback:
            self.on_close_callback()
            
        self.destroy()

    def destroy_window(self):
        self.destroy()
