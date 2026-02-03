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
        self.title("Spoken_Shortcuts - Select Apps")
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
        
        self.btn_refresh = ctk.CTkButton(self.header, text="↻ Refresh", width=60, command=self.refresh_apps)
        self.btn_refresh.pack(side="right", padx=5)

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
        self.refresh_apps()

    def refresh_apps(self):
        # Clear UI
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        self.lbl_loading = ctk.CTkLabel(self.scroll_frame, text="Scanning apps... Please wait.")
        self.lbl_loading.pack(pady=20)
        
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
            # Extract icon using the LNK path if available, fall back to target path
            # This ensures we get the "PWA" icon or "Application" icon properly
            icon_source = app.get('lnk_path', app['path'])
            try:
                # If it's a Chrome App shim, sometimes the icon is weird, but usually LNK works best
                icon_img = self.scanner.extract_icon(icon_source)
            except:
                icon_img = None
                
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
            
            # Fallback icon if none
            if not ctk_img:
                # Create a simple colored placeholder or use a default asset?
                # For now just an empty space or a generic text symbol
                pass 

            self.apps_data.append({
                "name": app['name'],
                "path": app['path'],
                "icon": ctk_img,
                "selected": is_selected
            })
            
        self.after(0, lambda: self.populate_ui(final_list))

    def populate_ui(self, app_list):
        self.lbl_loading.destroy()
        self.apps_data = [] 
        
        for app in app_list:
            # Row Frame (Card Style)
            row = ctk.CTkFrame(self.scroll_frame, fg_color=("gray90", "gray20"), corner_radius=8)
            row.pack(fill="x", pady=4, padx=5)
            
            # Use columns to align nicely
            row.grid_columnconfigure(2, weight=1)

            # Checkbox
            var = ctk.BooleanVar(value=app['selected'])
            chk = ctk.CTkCheckBox(row, text="", variable=var, width=24, checkbox_width=20, checkbox_height=20)
            chk.grid(row=0, column=0, padx=(10, 5), pady=10)
            
            # Icon
            if app['icon']:
                lbl_icon = ctk.CTkLabel(row, text="", image=app['icon'])
                lbl_icon.grid(row=0, column=1, padx=5, pady=5)
            else:
                # Placeholder for missing icon
                lbl_icon = ctk.CTkLabel(row, text="App", width=24, text_color="gray")
                lbl_icon.grid(row=0, column=1, padx=5, pady=5)
            
            # Name
            lbl_name = ctk.CTkLabel(row, text=app['name'], font=("Segoe UI", 12), anchor="w")
            lbl_name.grid(row=0, column=2, sticky="ew", padx=10, pady=10)
            
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
