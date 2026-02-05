import customtkinter
import json
import subprocess
import threading
import atexit
import tkinter
from tkinter import filedialog
import os
import webbrowser
import sys
from PIL import Image, ImageDraw
import pystray

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Leaks Tweaker")
        self.geometry("500x550")
        self.protocol("WM_DELETE_WINDOW", self.quit_app)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_profile_ui()

        self.tab_view = customtkinter.CTkTabview(self)
        self.tab_view.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.proxy_tab = self.tab_view.add("Proxy")
        self.gemini_tab = self.tab_view.add("Gemini")
        self.copilot_tab = self.tab_view.add("Copilot")
        self.google_labs_tab = self.tab_view.add("Google Labs")
        self.grok_tab = self.tab_view.add("Grok")
        self.settings_tab = self.tab_view.add("Settings")

        # --- Proxy Tab ---
        self.proxy_tab.grid_columnconfigure(0, weight=1)
        self.proxy_tab.grid_rowconfigure(3, weight=1)

        self.settings_frame = customtkinter.CTkFrame(self.proxy_tab)
        self.settings_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.settings_frame.grid_columnconfigure(1, weight=1)

        self.command_label = customtkinter.CTkLabel(self.settings_frame, text="Start Command:")
        self.command_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.command_entry = customtkinter.CTkEntry(self.settings_frame)
        self.command_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        self.proxy_control_button = customtkinter.CTkButton(self.proxy_tab, text="Start Proxy", command=self.toggle_proxy)
        self.proxy_control_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.mitm_cert_button = customtkinter.CTkButton(self.proxy_tab, text="Open mitm.it to Get CA Certificate", command=self.open_mitm_it)
        self.mitm_cert_button.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")

        self.log_frame = customtkinter.CTkFrame(self.proxy_tab)
        self.log_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(2, weight=1)

        self.log_label = customtkinter.CTkLabel(self.log_frame, text="Logs")
        self.log_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.log_textbox = customtkinter.CTkTextbox(self.log_frame)
        self.log_textbox.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        self.log_textbox.configure(state="disabled")

        # --- Gemini Tab ---
        self.gemini_tab.grid_columnconfigure(0, weight=1)
        self.gemini_tab.grid_rowconfigure(1, weight=1)

        self.gemini_modification_switch = customtkinter.CTkSwitch(self.gemini_tab, text="Enable Gemini Modifications", command=self.toggle_gemini_modification)
        self.gemini_modification_switch.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.gemini_tab_view = customtkinter.CTkTabview(self.gemini_tab)
        self.gemini_tab_view.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")

        self.gemini_flags_tab = self.gemini_tab_view.add("Flags")

        # --- Gemini Flags Tab ---
        self.gemini_flags_tab.grid_columnconfigure(0, weight=1)
        self.gemini_flags_tab.grid_rowconfigure(1, weight=1)

        self.gemini_search_entry = customtkinter.CTkEntry(self.gemini_flags_tab, placeholder_text="Search Gemini flags...")
        self.gemini_search_entry.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.gemini_search_entry.bind("<KeyRelease>", self.filter_gemini_flags)

        self.gemini_flags_list_frame = customtkinter.CTkScrollableFrame(self.gemini_flags_tab)
        self.gemini_flags_list_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        self.gemini_add_flag_textbox = customtkinter.CTkTextbox(self.gemini_flags_tab, height=60)
        self.gemini_add_flag_textbox.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        self.gemini_add_flag_button = customtkinter.CTkButton(self.gemini_flags_tab, text="Add Flag(s)", command=self.add_gemini_flag)
        self.gemini_add_flag_button.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        self.gemini_add_range_frame = customtkinter.CTkFrame(self.gemini_flags_tab)
        self.gemini_add_range_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        self.gemini_add_range_frame.grid_columnconfigure(0, weight=1)
        self.gemini_add_range_frame.grid_columnconfigure(1, weight=1)

        self.gemini_start_range_entry = customtkinter.CTkEntry(self.gemini_add_range_frame, placeholder_text="Start of range")
        self.gemini_start_range_entry.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="ew")

        self.gemini_end_range_entry = customtkinter.CTkEntry(self.gemini_add_range_frame, placeholder_text="End of range")
        self.gemini_end_range_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.gemini_add_range_button = customtkinter.CTkButton(self.gemini_add_range_frame, text="Add Range", command=self.add_gemini_range)
        self.gemini_add_range_button.grid(row=0, column=2, padx=(5, 0), pady=5)

        self.gemini_binary_search_button = customtkinter.CTkButton(self.gemini_flags_tab, text="Binary Search for Flag", command=self.open_binary_search_window)
        self.gemini_binary_search_button.grid(row=5, column=0, padx=10, pady=5, sticky="ew")

        self.gemini_save_changes_button = customtkinter.CTkButton(self.gemini_flags_tab, text="Save Gemini Changes", command=self.save_gemini_changes)
        self.gemini_save_changes_button.grid(row=6, column=0, padx=10, pady=5, sticky="ew")


        # --- Copilot Tab ---
        self.copilot_tab.grid_columnconfigure(0, weight=1)
        self.copilot_tab.grid_rowconfigure(2, weight=1)

        self.copilot_modification_switch = customtkinter.CTkSwitch(self.copilot_tab, text="Enable Copilot Modifications", command=self.toggle_copilot_modification)
        self.copilot_modification_switch.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.copilot_beta_switch = customtkinter.CTkSwitch(self.copilot_tab, text="Enable Beta", command=self.toggle_copilot_beta_and_save)
        self.copilot_beta_switch.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.copilot_flags_list_frame = customtkinter.CTkScrollableFrame(self.copilot_tab)
        self.copilot_flags_list_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

        self.copilot_add_flag_entry = customtkinter.CTkEntry(self.copilot_tab, placeholder_text="Enter flag name to add")
        self.copilot_add_flag_entry.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        self.copilot_add_flag_button = customtkinter.CTkButton(self.copilot_tab, text="Add Flag", command=self.add_copilot_flag)
        self.copilot_add_flag_button.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        self.copilot_save_changes_button = customtkinter.CTkButton(self.copilot_tab, text="Save Copilot Changes", command=self.save_copilot_changes)
        self.copilot_save_changes_button.grid(row=5, column=0, padx=10, pady=5, sticky="ew")

        # --- Google Labs Tab ---
        self.google_labs_tab.grid_columnconfigure(0, weight=1)

        self.google_labs_modification_switch = customtkinter.CTkSwitch(self.google_labs_tab, text="Enable Google Labs Modifications", command=self.toggle_google_labs_modification)
        self.google_labs_modification_switch.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.music_fx_replace_label = customtkinter.CTkLabel(self.google_labs_tab, text="Replace MusicFX Homepage Link:")
        self.music_fx_replace_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.music_fx_replace_entry = customtkinter.CTkEntry(self.google_labs_tab, placeholder_text="e.g., debug or notebook")
        self.music_fx_replace_entry.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        self.music_fx_replace_desc = customtkinter.CTkLabel(self.google_labs_tab, text="Replaces the '/tools/music-fx' link with your own path (e.g., /debug).", text_color="gray", font=("", 11))
        self.music_fx_replace_desc.grid(row=3, column=0, padx=10, pady=(0,5), sticky="w")

        self.bypass_not_found_switch = customtkinter.CTkSwitch(self.google_labs_tab, text="Bypass 'notFound' errors")
        self.bypass_not_found_switch.grid(row=4, column=0, padx=10, pady=10, sticky="w")

        self.google_labs_save_button = customtkinter.CTkButton(self.google_labs_tab, text="Save Google Labs Changes", command=self.save_google_labs_changes)
        self.google_labs_save_button.grid(row=5, column=0, padx=10, pady=10, sticky="ew")

        # --- Grok Tab ---
        self.grok_tab.grid_columnconfigure(0, weight=1)
        self.grok_tab.grid_rowconfigure(3, weight=1)

        self.grok_modification_switch = customtkinter.CTkSwitch(self.grok_tab, text="Enable Grok Modifications", command=self.toggle_grok_modification)
        self.grok_modification_switch.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.grok_spoof_subscription_switch = customtkinter.CTkSwitch(self.grok_tab, text="Spoof Subscription (Pro/Super)", command=self.save_grok_changes)
        self.grok_spoof_subscription_switch.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        self.grok_actions_frame = customtkinter.CTkFrame(self.grok_tab)
        self.grok_actions_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.grok_actions_frame.grid_columnconfigure(0, weight=1)
        self.grok_actions_frame.grid_columnconfigure(1, weight=1)

        self.grok_load_default_button = customtkinter.CTkButton(self.grok_actions_frame, text="Load Extracted Config", command=self.load_grok_default_config)
        self.grok_load_default_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.grok_format_button = customtkinter.CTkButton(self.grok_actions_frame, text="Format & Validate JSON", command=self.format_grok_json)
        self.grok_format_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.grok_search_frame = customtkinter.CTkFrame(self.grok_tab)
        self.grok_search_frame.grid(row=2, column=0, padx=10, pady=(5,0), sticky="ew")
        self.grok_search_frame.grid_columnconfigure(0, weight=1)

        self.grok_search_entry = customtkinter.CTkEntry(self.grok_search_frame, placeholder_text="Search JSON...")
        self.grok_search_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.grok_search_entry.bind("<Return>", self.grok_find_next)

        self.grok_find_prev_button = customtkinter.CTkButton(self.grok_search_frame, text="<", width=30, command=self.grok_find_prev)
        self.grok_find_prev_button.grid(row=0, column=1, padx=2, pady=5)

        self.grok_find_next_button = customtkinter.CTkButton(self.grok_search_frame, text=">", width=30, command=self.grok_find_next)
        self.grok_find_next_button.grid(row=0, column=2, padx=2, pady=5)
        
        self.grok_toggle_bool_button = customtkinter.CTkButton(self.grok_search_frame, text="Toggle Boolean", width=100, command=self.grok_toggle_boolean)
        self.grok_toggle_bool_button.grid(row=0, column=3, padx=5, pady=5)

        self.grok_json_textbox = customtkinter.CTkTextbox(self.grok_tab)
        self.grok_json_textbox.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        
        # Bind double click for easy toggling
        self.grok_json_textbox._textbox.bind("<Double-Button-1>", self.grok_toggle_boolean)

        self.grok_save_button = customtkinter.CTkButton(self.grok_tab, text="Save Grok Changes", command=self.save_grok_changes)
        self.grok_save_button.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

        # --- Settings Tab ---
        self.settings_tab.grid_columnconfigure(0, weight=1)

        self.minimize_to_tray_switch = customtkinter.CTkSwitch(self.settings_tab, text="Minimize to tray", command=self.toggle_minimize_to_tray)
        self.minimize_to_tray_switch.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.start_on_startup_switch = customtkinter.CTkSwitch(self.settings_tab, text="Start with OS", command=self.toggle_start_on_startup)
        self.start_on_startup_switch.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        # --- Load Data ---
        self.log_listeners = []
        self.proxy_process = None
        self.gemini_flag_widgets = {}
        self.copilot_flag_widgets = {}
        self.load_profiles()
        self.update_profile_dropdown()
        self.setup_startup()
        self.load_active_profile_data_into_ui()
        self.generate_rules_json()
        self.start_proxy()

    def create_profile_ui(self):
        profile_frame = customtkinter.CTkFrame(self)
        profile_frame.grid(row=0, column=0, padx=10, pady=(10,0), sticky="ew")
        profile_frame.grid_columnconfigure(2, weight=1)
        label = customtkinter.CTkLabel(profile_frame, text="Profile:")
        label.grid(row=0, column=0, padx=5, pady=5)
        self.profile_menu = customtkinter.CTkOptionMenu(profile_frame, command=self.switch_profile)
        self.profile_menu.grid(row=0, column=1, padx=5, pady=5)
        profile_actions_frame = customtkinter.CTkFrame(profile_frame)
        profile_actions_frame.grid(row=0, column=2, padx=5, pady=5, sticky="e")
        new_button = customtkinter.CTkButton(profile_actions_frame, text="New", width=50, command=self.new_profile)
        new_button.pack(side="left", padx=5)
        rename_button = customtkinter.CTkButton(profile_actions_frame, text="Rename", width=70, command=self.rename_profile)
        rename_button.pack(side="left", padx=5)
        delete_button = customtkinter.CTkButton(profile_actions_frame, text="Delete", width=60, command=self.delete_profile)
        delete_button.pack(side="left", padx=5)
        import_button = customtkinter.CTkButton(profile_actions_frame, text="Import", width=60, command=self.import_profile)
        import_button.pack(side="left", padx=5)
        export_button = customtkinter.CTkButton(profile_actions_frame, text="Export", width=60, command=self.export_profile)
        export_button.pack(side="left", padx=5)

    def load_profiles(self):
        try:
            with open("profiles.json", "r") as f:
                self.profiles_data = json.load(f)
                if "profiles" not in self.profiles_data or "active_profile" not in self.profiles_data:
                    raise ValueError("Invalid profiles.json structure")
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            self.profiles_data = {
                "active_profile": "default",
                "profiles": {
                    "default": {
                        "proxy_command": "mitmdump -s proxy.py -p 8000",
                        "apps": {
                            "gemini": {"enabled": True, "flag_configs": {}},
                            "copilot": {"enabled": True, "flags": [], "allow_beta": False},
                            "google_labs": {"enabled": True, "music_fx_replace": "None", "bypass_not_found": False},
                            "grok": {"enabled": True, "config_json": "{}", "spoof_subscription": False}
                        }
                    }
                }
            }

        self.app_settings = self.profiles_data.get("app_settings", {
            "minimize_to_tray": False,
            "start_on_startup": False
        })

        self.active_profile_name = self.profiles_data.get("active_profile", "default")
        if self.active_profile_name not in self.profiles_data.get("profiles", {}):
            self.active_profile_name = list(self.profiles_data["profiles"].keys())[0] if self.profiles_data["profiles"] else "default"

        migrated = False
        for profile_name, profile_data in self.profiles_data.get("profiles", {}).items():
            if "flag_configs" in profile_data and "apps" not in profile_data:
                print(f"Migrating profile '{profile_name}' to new app-based structure...")
                profile_data["apps"] = {
                    "gemini": {
                        "enabled": profile_data.pop("modification_enabled", True),
                        "flag_configs": profile_data.pop("flag_configs")
                    }
                }
                migrated = True
        
        if migrated:
            self.save_profiles()
        
        self.active_profile = self.profiles_data["profiles"][self.active_profile_name]

    def save_profiles(self):
        self.profiles_data["active_profile"] = self.active_profile_name
        with open("profiles.json", "w") as f:
            json.dump(self.profiles_data, f, indent=4)

    def update_profile_dropdown(self):
        profile_names = list(self.profiles_data["profiles"].keys())
        self.profile_menu.configure(values=profile_names)
        self.profile_menu.set(self.active_profile_name)

    def load_active_profile_data_into_ui(self):
        self.command_entry.delete(0, "end")
        self.command_entry.insert(0, self.active_profile.get("proxy_command", "mitmdump -s proxy.py -p 8000"))
        gemini_app_config = self.active_profile.setdefault("apps", {}).setdefault("gemini", {})
        if gemini_app_config.get("enabled", True):
            self.gemini_modification_switch.select()
        else:
            self.gemini_modification_switch.deselect()
        copilot_app_config = self.active_profile.setdefault("apps", {}).setdefault("copilot", {})
        if copilot_app_config.get("enabled", True):
            self.copilot_modification_switch.select()
        else:
            self.copilot_modification_switch.deselect()
        if copilot_app_config.get("allow_beta", False):
            self.copilot_beta_switch.select()
        else:
            self.copilot_beta_switch.deselect()

        google_labs_app_config = self.active_profile.setdefault("apps", {}).setdefault("google_labs", {})
        if google_labs_app_config.get("enabled", True):
            self.google_labs_modification_switch.select()
        else:
            self.google_labs_modification_switch.deselect()
        self.music_fx_replace_entry.delete(0, "end")
        self.music_fx_replace_entry.insert(0, google_labs_app_config.get("music_fx_replace", "None"))
        if google_labs_app_config.get("bypass_not_found", False):
            self.bypass_not_found_switch.select()
        else:
            self.bypass_not_found_switch.deselect()

        grok_app_config = self.active_profile.setdefault("apps", {}).setdefault("grok", {})
        if grok_app_config.get("enabled", True):
            self.grok_modification_switch.select()
        else:
            self.grok_modification_switch.deselect()

        if grok_app_config.get("spoof_subscription", False):
            self.grok_spoof_subscription_switch.select()
        else:
            self.grok_spoof_subscription_switch.deselect()
        
        self.grok_json_textbox.delete("1.0", "end")
        grok_json_str = grok_app_config.get("config_json", "{}")
        if not grok_json_str or grok_json_str == "{}":
             # Try to load from default file if empty
             try:
                 if os.path.exists("grok_config.json"):
                     with open("grok_config.json", "r", encoding="utf-8") as f:
                         grok_json_str = f.read()
             except:
                 pass
        
        # Pretty print if possible
        try:
            parsed = json.loads(grok_json_str)
            self.grok_json_textbox.insert("1.0", json.dumps(parsed, indent=4))
        except:
            self.grok_json_textbox.insert("1.0", grok_json_str)

        if self.app_settings.get("minimize_to_tray", False):
            self.minimize_to_tray_switch.select()
        else:
            self.minimize_to_tray_switch.deselect()

        if self.app_settings.get("start_on_startup", False):
            self.start_on_startup_switch.select()
        else:
            self.start_on_startup_switch.deselect()
            
        self.load_gemini_flags()
        self.load_copilot_flags()

    def switch_profile(self, profile_name):
        self.active_profile_name = profile_name
        self.active_profile = self.profiles_data["profiles"][profile_name]
        self.save_profiles()
        self.load_active_profile_data_into_ui()
        self.generate_rules_json()
        self.log_message(f"Switched to profile: {profile_name}\n")

    def new_profile(self):
        dialog = customtkinter.CTkInputDialog(text="Enter new profile name:", title="New Profile")
        new_name = dialog.get_input()
        if new_name and new_name not in self.profiles_data["profiles"]:
            self.profiles_data["profiles"][new_name] = {
                "proxy_command": "mitmdump -s proxy.py -p 8000",
                "apps": {
                    "gemini": {"enabled": True, "flag_configs": {}},
                    "copilot": {"enabled": True, "flags": [], "allow_beta": False},
                    "google_labs": {"enabled": True, "music_fx_replace": "None", "bypass_not_found": False},
                    "grok": {"enabled": True, "config_json": "{}", "spoof_subscription": False}
                }
            }
            self.switch_profile(new_name)
            self.update_profile_dropdown()
        elif new_name:
            self.log_message(f"Error: Profile '{new_name}' already exists.\n")

    def rename_profile(self):
        dialog = customtkinter.CTkInputDialog(text=f"Enter new name for '{self.active_profile_name}':", title="Rename Profile")
        new_name = dialog.get_input()
        if new_name and new_name not in self.profiles_data["profiles"]:
            self.profiles_data["profiles"][new_name] = self.profiles_data["profiles"].pop(self.active_profile_name)
            self.active_profile_name = new_name
            self.save_profiles()
            self.update_profile_dropdown()
        elif new_name:
            self.log_message(f"Error: Profile '{new_name}' already exists.\n")

    def delete_profile(self):
        if len(self.profiles_data["profiles"]) <= 1:
            self.log_message("Error: Cannot delete the last profile.\n")
            return
        del self.profiles_data["profiles"][self.active_profile_name]
        new_active_profile = list(self.profiles_data["profiles"].keys())[0]
        self.switch_profile(new_active_profile)
        self.update_profile_dropdown()

    def import_profile(self):
        file_path = filedialog.askopenfilename(title="Import Profile", filetypes=[("JSON files", "*.json"), ("All files", "*.*")] )
        if not file_path: return
        try:
            with open(file_path, "r") as f: imported_data = json.load(f)
            profile_name = os.path.splitext(os.path.basename(file_path))[0]
            if profile_name in self.profiles_data["profiles"]:
                dialog = customtkinter.CTkInputDialog(text=f"Profile '{profile_name}' exists. Enter a new name:", title="Import Profile")
                profile_name = dialog.get_input()
            if profile_name and profile_name not in self.profiles_data["profiles"]:
                self.profiles_data["profiles"][profile_name] = imported_data
                self.save_profiles()
                self.update_profile_dropdown()
                self.log_message(f"Profile '{profile_name}' imported.\n")
            elif profile_name: self.log_message(f"Error: Profile '{profile_name}' already exists.\n")
        except (json.JSONDecodeError, IOError) as e: self.log_message(f"Error importing profile: {e}\n")

    def export_profile(self):
        file_path = filedialog.asksaveasfilename(title="Export Profile",defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")], initialfile=f"{self.active_profile_name}.json")
        if not file_path: return
        try:
            with open(file_path, "w") as f: json.dump(self.active_profile, f, indent=4)
            self.log_message(f"Profile '{self.active_profile_name}' exported to {file_path}\n")
        except IOError as e: self.log_message(f"Error exporting profile: {e}\n")

    def open_mitm_it(self):
        url = "http://mitm.it"
        self.log_message(f"Opening {url} in your browser to download the CA certificate...\n")
        webbrowser.open(url, new=2)

    def generate_rules_json(self):
        apps_for_backend = {}
        if "apps" in self.active_profile:
            if "gemini" in self.active_profile["apps"]:
                gemini_config = self.active_profile["apps"]["gemini"]

                def sort_key(item):
                    key_part = item.split('-')[0]
                    return int(key_part)

                enabled_flags_configs = {k: v for k, v in gemini_config.get("flag_configs", {}).items() if v.get("enabled", True)}
                
                enabled_flags = []
                for id in sorted(enabled_flags_configs.keys(), key=sort_key):
                    if '-' in id:
                        enabled_flags.append(id)
                    else:
                        enabled_flags.append(int(id))

                apps_for_backend["gemini"] = {
                    "enabled": gemini_config.get("enabled", True), 
                    "flags": enabled_flags
                }
            if "copilot" in self.active_profile["apps"]:
                copilot_config = self.active_profile["apps"]["copilot"]
                enabled_flags = [f["name"] for f in copilot_config.get("flags", []) if f.get("enabled", True)]
                apps_for_backend["copilot"] = {
                    "enabled": copilot_config.get("enabled", True),
                    "flags": sorted(enabled_flags),
                    "allow_beta": copilot_config.get("allow_beta", False)
                }
            if "google_labs" in self.active_profile["apps"]:
                apps_for_backend["google_labs"] = self.active_profile["apps"]["google_labs"]
            if "grok" in self.active_profile["apps"]:
                apps_for_backend["grok"] = self.active_profile["apps"]["grok"]

        with open("rules.json", "w") as f: json.dump({"apps": apps_for_backend}, f, indent=4)
        self.restart_proxy_if_running()

    def quit_app(self):
        if hasattr(self, 'tray_icon') and self.tray_icon.visible:
            self.tray_icon.stop()
        if self.proxy_process and self.proxy_process.poll() is None:
            self.proxy_process.terminate()
        self.destroy()

    # --- Gemini Methods ---
    def load_gemini_flags(self):
        for widget in self.gemini_flags_list_frame.winfo_children():
            widget.destroy()
        self.gemini_flag_widgets = {}
        gemini_app_config = self.active_profile.setdefault("apps", {}).setdefault("gemini", {})
        flag_configs = gemini_app_config.setdefault("flag_configs", {})
        self.log_message(f"Loading flags: {flag_configs}\n")

        def sort_key(item):
            key_part = item[0].split('-')[0]
            return int(key_part)

        for flag_id_str, config in sorted(flag_configs.items(), key=sort_key):
            note, enabled = config.get("note", ""), config.get("enabled", True)
            flag_frame = customtkinter.CTkFrame(self.gemini_flags_list_frame)
            flag_frame.pack(fill="x", padx=5, pady=2)
            switch = customtkinter.CTkSwitch(flag_frame, text="", width=0)
            switch.pack(side="left", padx=5)
            if enabled:
                switch.select()
            else:
                switch.deselect()
            flag_label = customtkinter.CTkLabel(flag_frame, text=flag_id_str)
            flag_label.pack(side="left", padx=5)
            note_entry = customtkinter.CTkEntry(flag_frame, placeholder_text="Note...")
            note_entry.insert(0, note)
            note_entry.pack(side="left", padx=5, fill="x", expand=True)
            delete_button = customtkinter.CTkButton(flag_frame, text="X", width=30, command=lambda f=flag_id_str: self.remove_gemini_flag(f))
            delete_button.pack(side="right", padx=5)
            self.gemini_flag_widgets[flag_id_str] = {"note_entry": note_entry, "switch": switch, "frame": flag_frame}
        self.filter_gemini_flags()

    def add_gemini_range(self):
        start_range = self.gemini_start_range_entry.get()
        end_range = self.gemini_end_range_entry.get()

        if not start_range or not end_range:
            self.log_message("Error: Start and end of range cannot be empty.\n")
            return

        if not start_range.isdigit() or not end_range.isdigit():
            self.log_message("Error: Range start and end must be numbers.\n")
            return
        
        if int(start_range) >= int(end_range):
            self.log_message("Error: Start of range must be less than end of range.\n")
            return

        flag_to_add = f"{start_range}-{end_range}"

        gemini_app_config = self.active_profile.setdefault("apps", {}).setdefault("gemini", {})
        flag_configs = gemini_app_config.setdefault("flag_configs", {})
        
        if flag_to_add not in flag_configs:
            flag_configs[flag_to_add] = {"note": "", "enabled": True}
            self.save_profiles()
            self.generate_rules_json()
            self.load_gemini_flags()
            self.gemini_start_range_entry.delete(0, "end")
            self.gemini_end_range_entry.delete(0, "end")
            self.log_message(f"Gemini Flag Range '{flag_to_add}' added.\n")
        else:
            self.log_message(f"Error: Flag '{flag_to_add}' already exists.\n")

    def add_gemini_flag(self):
        input_text = self.gemini_add_flag_textbox.get("1.0", "end-1c")
        if not input_text:
            return

        # Split by newlines to handle multi-line paste
        lines = input_text.strip().split('\n')
        
        gemini_app_config = self.active_profile.setdefault("apps", {}).setdefault("gemini", {})
        flag_configs = gemini_app_config.setdefault("flag_configs", {})
        
        added_flags = []
        invalid_flags = []
        duplicate_flags = []
        
        for line in lines:
            flag_to_add = line.strip()
            if not flag_to_add:
                continue
            
            # Validate the input
            is_valid_range = False
            if '-' in flag_to_add:
                parts = flag_to_add.split('-')
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit() and int(parts[0]) < int(parts[1]):
                    is_valid_range = True
            
            if not is_valid_range and not flag_to_add.isdigit():
                invalid_flags.append(flag_to_add)
                continue
            
            if flag_to_add in flag_configs:
                duplicate_flags.append(flag_to_add)
                continue
            
            flag_configs[flag_to_add] = {"note": "", "enabled": True}
            added_flags.append(flag_to_add)
        
        # Save and reload if any flags were added
        if added_flags:
            self.save_profiles()
            self.generate_rules_json()
            self.load_gemini_flags()
            self.gemini_add_flag_textbox.delete("1.0", "end")
            
            if len(added_flags) == 1:
                self.log_message(f"Gemini Flag '{added_flags[0]}' added.\n")
            else:
                self.log_message(f"Added {len(added_flags)} Gemini flags: {', '.join(added_flags)}\n")
        
        # Report any issues
        if invalid_flags:
            self.log_message(f"Error: Invalid flags skipped: {', '.join(invalid_flags)}\n")
        if duplicate_flags:
            self.log_message(f"Warning: Duplicate flags skipped: {', '.join(duplicate_flags)}\n")
        
        if not added_flags and not invalid_flags and not duplicate_flags:
            self.log_message("Error: No valid flags to add.\n")

    def remove_gemini_flag(self, flag_to_remove):
        gemini_app_config = self.active_profile.setdefault("apps", {}).setdefault("gemini", {})
        flag_configs = gemini_app_config.setdefault("flag_configs", {})
        if flag_to_remove in flag_configs:
            del flag_configs[flag_to_remove]
            self.save_profiles()
            self.generate_rules_json()
            self.load_gemini_flags()
            self.log_message(f"Gemini Flag '{flag_to_remove}' removed.\n")

    def save_gemini_changes(self):
        gemini_app_config = self.active_profile.setdefault("apps", {}).setdefault("gemini", {})
        gemini_app_config["enabled"] = self.gemini_modification_switch.get() == 1
        flag_configs = gemini_app_config.setdefault("flag_configs", {})
        for flag_id, widgets in self.gemini_flag_widgets.items():
            flag_configs[str(flag_id)] = {"note": widgets["note_entry"].get(), "enabled": widgets["switch"].get() == 1}
        self.save_profiles()
        self.generate_rules_json()
        self.log_message(f"Gemini changes saved to profile: '{self.active_profile_name}'\n")

    def filter_gemini_flags(self, event=None):
        search_term = self.gemini_search_entry.get().lower()
        for flag_id, widgets in self.gemini_flag_widgets.items():
            note = widgets["note_entry"].get().lower()
            if search_term in str(flag_id) or search_term in note:
                widgets["frame"].pack(fill="x", padx=5, pady=2)
            else:
                widgets["frame"].pack_forget()

    def toggle_gemini_modification(self):
        gemini_app_config = self.active_profile.setdefault("apps", {}).setdefault("gemini", {})
        gemini_app_config["enabled"] = self.gemini_modification_switch.get() == 1
        self.save_profiles()
        self.generate_rules_json()
        self.log_message(f"Gemini modification {'enabled' if gemini_app_config['enabled'] else 'disabled'}.\n")



    # --- Copilot Methods ---
    def load_copilot_flags(self):
        for widget in self.copilot_flags_list_frame.winfo_children():
            widget.destroy()
        self.copilot_flag_widgets = {}
        copilot_app_config = self.active_profile.setdefault("apps", {}).setdefault("copilot", {})
        flags = copilot_app_config.setdefault("flags", [])
        for i, flag_obj in enumerate(flags):
            name, enabled = flag_obj.get("name", ""), flag_obj.get("enabled", True)
            flag_frame = customtkinter.CTkFrame(self.copilot_flags_list_frame)
            flag_frame.pack(fill="x", padx=5, pady=2)
            switch = customtkinter.CTkSwitch(flag_frame, text="", width=0)
            switch.pack(side="left", padx=5)
            if enabled:
                switch.select()
            else:
                switch.deselect()
            flag_label = customtkinter.CTkLabel(flag_frame, text=name)
            flag_label.pack(side="left", padx=5, fill="x", expand=True)
            delete_button = customtkinter.CTkButton(flag_frame, text="X", width=30, command=lambda index=i: self.remove_copilot_flag(index))
            delete_button.pack(side="right", padx=5)
            self.copilot_flag_widgets[i] = {"switch": switch, "label": flag_label, "frame": flag_frame}

    def add_copilot_flag(self):
        flag_name = self.copilot_add_flag_entry.get()
        if flag_name:
            copilot_app_config = self.active_profile.setdefault("apps", {}).setdefault("copilot", {})
            flags = copilot_app_config.setdefault("flags", [])
            if not any(f["name"] == flag_name for f in flags):
                flags.append({"name": flag_name, "enabled": True})
                self.save_profiles()
                self.generate_rules_json()
                self.load_copilot_flags()
                self.copilot_add_flag_entry.delete(0, "end")
                self.log_message(f"Copilot Flag '{flag_name}' added.\n")

    def remove_copilot_flag(self, index):
        copilot_app_config = self.active_profile.setdefault("apps", {}).setdefault("copilot", {})
        flags = copilot_app_config.setdefault("flags", [])
        if 0 <= index < len(flags):
            removed_flag = flags.pop(index)
            self.save_profiles()
            self.generate_rules_json()
            self.load_copilot_flags()
            self.log_message(f'''Copilot Flag '{removed_flag['name']}' removed.\n''')

    def save_copilot_changes(self):
        copilot_app_config = self.active_profile.setdefault("apps", {}).setdefault("copilot", {})
        copilot_app_config["enabled"] = self.copilot_modification_switch.get() == 1
        copilot_app_config["allow_beta"] = self.copilot_beta_switch.get() == 1
        new_flags = []
        for i in sorted(self.copilot_flag_widgets.keys()):
            widgets = self.copilot_flag_widgets[i]
            new_flags.append({"name": widgets["label"].cget("text"), "enabled": widgets["switch"].get() == 1})
        copilot_app_config["flags"] = new_flags
        self.save_profiles()
        self.generate_rules_json()
        self.log_message(f"Copilot changes saved to profile: '{self.active_profile_name}'\n")

    def toggle_copilot_modification(self):
        copilot_app_config = self.active_profile.setdefault("apps", {}).setdefault("copilot", {})
        copilot_app_config["enabled"] = self.copilot_modification_switch.get() == 1
        self.save_profiles()
        self.generate_rules_json()
        self.log_message(f"Copilot modification {'enabled' if copilot_app_config['enabled'] else 'disabled'}.\n")

    def toggle_copilot_beta_and_save(self):
        is_beta_enabled = self.copilot_beta_switch.get() == 1
        copilot_app_config = self.active_profile.setdefault("apps", {}).setdefault("copilot", {})
        copilot_app_config["allow_beta"] = is_beta_enabled
        self.save_profiles()
        self.generate_rules_json()
        self.log_message(f"Copilot 'allowBeta' set to {is_beta_enabled}.\n")

    # --- Google Labs Methods ---
    def toggle_google_labs_modification(self):
        google_labs_app_config = self.active_profile.setdefault("apps", {}).setdefault("google_labs", {})
        google_labs_app_config["enabled"] = self.google_labs_modification_switch.get() == 1
        self.save_profiles()
        self.generate_rules_json()
        self.log_message(f"Google Labs modification {'enabled' if google_labs_app_config['enabled'] else 'disabled'}.\n")

    def save_google_labs_changes(self):
        google_labs_app_config = self.active_profile.setdefault("apps", {}).setdefault("google_labs", {})
        google_labs_app_config["enabled"] = self.google_labs_modification_switch.get() == 1
        google_labs_app_config["music_fx_replace"] = self.music_fx_replace_entry.get().lstrip('/')
        google_labs_app_config["bypass_not_found"] = self.bypass_not_found_switch.get() == 1
        self.save_profiles()
        self.generate_rules_json()
        self.log_message(f"Google Labs changes saved to profile: '{self.active_profile_name}'\n")

    # --- Grok Methods ---
    def toggle_grok_modification(self):
        grok_app_config = self.active_profile.setdefault("apps", {}).setdefault("grok", {})
        grok_app_config["enabled"] = self.grok_modification_switch.get() == 1
        self.save_profiles()
        self.generate_rules_json()
        self.log_message(f"Grok modification {'enabled' if grok_app_config['enabled'] else 'disabled'}.\n")

    def load_grok_default_config(self):
        try:
            if os.path.exists("grok_config.json"):
                with open("grok_config.json", "r", encoding="utf-8") as f:
                    content = f.read()
                    parsed = json.loads(content)
                    self.grok_json_textbox.delete("1.0", "end")
                    self.grok_json_textbox.insert("1.0", json.dumps(parsed, indent=4))
                    self.log_message("Loaded extracted Grok configuration.\n")
            else:
                self.log_message("Error: grok_config.json not found. Run the extractor first or browse.\n")
        except Exception as e:
            self.log_message(f"Error loading Grok config: {e}\n")

    def format_grok_json(self):
        content = self.grok_json_textbox.get("1.0", "end-1c")
        try:
            parsed = json.loads(content)
            formatted = json.dumps(parsed, indent=4)
            self.grok_json_textbox.delete("1.0", "end")
            self.grok_json_textbox.insert("1.0", formatted)
            self.log_message("JSON is valid and formatted.\n")
            return True
        except json.JSONDecodeError as e:
            self.log_message(f"Invalid JSON: {e}\n")
            return False

    def grok_find_next(self, event=None):
        self._grok_search("next")

    def grok_find_prev(self):
        self._grok_search("prev")

    def _grok_search(self, direction):
        search_str = self.grok_search_entry.get()
        if not search_str:
            return

        text_widget = self.grok_json_textbox._textbox
        text_widget.tag_remove("found", "1.0", "end")
        
        start_index = "insert"
        
        if direction == "next":
            pos = text_widget.search(search_str, start_index, stopindex="end", nocase=True)
            # Loop around if not found
            if not pos:
                pos = text_widget.search(search_str, "1.0", stopindex=start_index, nocase=True)
        else:
            pos = text_widget.search(search_str, start_index, stopindex="1.0", backwards=True, nocase=True)
            if not pos:
                pos = text_widget.search(search_str, "end", stopindex=start_index, backwards=True, nocase=True)

        if pos:
            # Highlight and scroll
            end_pos = f"{pos}+{len(search_str)}c"
            text_widget.tag_add("found", pos, end_pos)
            text_widget.tag_config("found", background="yellow", foreground="black")
            text_widget.mark_set("insert", end_pos if direction == "next" else pos)
            text_widget.see(pos)
            text_widget.focus_set()

    def grok_toggle_boolean(self, event=None):
        text_widget = self.grok_json_textbox._textbox
        
        # If triggered by event (double click), use the mouse position
        if event:
            try:
                index = text_widget.index(f"@{event.x},{event.y}")
                text_widget.mark_set("insert", index)
            except:
                pass
        
        # Get word at cursor
        try:
            # Expand selection to word boundaries
            word_start = text_widget.search(r'\W', "insert", backwards=True, regexp=True, stopindex="insert linestart")
            if not word_start: word_start = "insert linestart"
            else: word_start = f"{word_start}+1c"
            
            word_end = text_widget.search(r'\W', "insert", regexp=True, stopindex="insert lineend")
            if not word_end: word_end = "insert lineend"
            
            # Extract word
            current_word = text_widget.get(word_start, word_end).strip()
            
            # Check if boolean
            new_word = None
            if current_word == "true":
                new_word = "false"
            elif current_word == "false":
                new_word = "true"
            
            if new_word:
                text_widget.delete(word_start, word_end)
                text_widget.insert(word_start, new_word)
                self.log_message(f"Toggled boolean: {current_word} -> {new_word}\n")
                # Highlight change briefly
                text_widget.tag_add("changed", word_start, f"{word_start}+{len(new_word)}c")
                text_widget.tag_config("changed", background="lightgreen", foreground="black")
                self.after(500, lambda: text_widget.tag_remove("changed", "1.0", "end"))
                return "break" # Prevent default double-click selection if we handled it
        except Exception as e:
            self.log_message(f"Error toggling boolean: {e}\n")

    def save_grok_changes(self):
        if not self.format_grok_json():
            return
        
        grok_app_config = self.active_profile.setdefault("apps", {}).setdefault("grok", {})
        grok_app_config["enabled"] = self.grok_modification_switch.get() == 1
        grok_app_config["spoof_subscription"] = self.grok_spoof_subscription_switch.get() == 1
        grok_app_config["config_json"] = self.grok_json_textbox.get("1.0", "end-1c")
        
        self.save_profiles()
        self.generate_rules_json()
        self.log_message(f"Grok changes saved to profile: '{self.active_profile_name}'\n")

    # --- Settings Methods ---
    def toggle_minimize_to_tray(self):
        self.app_settings["minimize_to_tray"] = self.minimize_to_tray_switch.get() == 1
        self.profiles_data["app_settings"] = self.app_settings
        self.save_profiles()
        if self.app_settings["minimize_to_tray"]:
            self.log_message("Minimize to tray enabled.\n")
            self.setup_tray_icon()
            self.protocol("WM_DELETE_WINDOW", self.hide_window)
        else:
            self.log_message("Minimize to tray disabled.\n")
            if hasattr(self, 'tray_icon') and self.tray_icon.visible:
                self.tray_icon.stop()
            self.protocol("WM_DELETE_WINDOW", self.quit_app)

    def setup_tray_icon(self):
        if hasattr(self, 'tray_icon') and self.tray_icon.visible:
            return
        
        width = 64
        height = 64
        color1 = (0, 0, 0) 
        color2 = (255, 255, 255)
        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.rectangle(
            (width // 2, 0, width, height // 2),
            fill=color2)
        dc.rectangle(
            (0, height // 2, width // 2, height),
            fill=color2)
            
        menu = (pystray.MenuItem('Show', self.show_window, default=True), pystray.MenuItem('Quit', self.quit_app))
        self.tray_icon = pystray.Icon("AI Leaks Tweaker", image, "AI Leaks Tweaker", menu)
        
        def run_tray_icon():
            self.tray_icon.run()

        tray_thread = threading.Thread(target=run_tray_icon)
        tray_thread.daemon = True
        tray_thread.start()

    def hide_window(self):
        self.withdraw()

    def show_window(self, icon, item):
        self.deiconify()

    def toggle_start_on_startup(self):
        self.app_settings["start_on_startup"] = self.start_on_startup_switch.get() == 1
        self.profiles_data["app_settings"] = self.app_settings
        self.save_profiles()
        self.setup_startup()

    def setup_startup(self):
        if sys.platform == "win32":
            self._setup_windows_startup()
        elif sys.platform == "darwin":
            self._setup_macos_startup()
        elif sys.platform.startswith("linux"):
            self._setup_linux_startup()

    def _setup_windows_startup(self):
        try:
            import winreg
            app_name = "AITweaker"
            key = winreg.HKEY_CURRENT_USER
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_ALL_ACCESS) as registry_key:
                if self.app_settings.get("start_on_startup", False):
                    script_path = os.path.abspath("run.bat")
                    winreg.SetValueEx(registry_key, app_name, 0, winreg.REG_SZ, script_path)
                    self.log_message("App set to start with Windows.\n")
                else:
                    try:
                        winreg.DeleteValue(registry_key, app_name)
                        self.log_message("App removed from Windows startup.\n")
                    except FileNotFoundError:
                        self.log_message("App not in startup, nothing to remove.\n")
        except Exception as e:
            self.log_message(f"Error setting up Windows startup: {e}\n")

    def _setup_macos_startup(self):
        try:
            script_path = os.path.abspath("run.sh")
            plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tweaker.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>'''
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.tweaker.app.plist")

            if self.app_settings.get("start_on_startup", False):
                with open(plist_path, "w") as f:
                    f.write(plist_content)
                self.log_message("App set to start with macOS.\n")
            else:
                if os.path.exists(plist_path):
                    os.remove(plist_path)
                    self.log_message("App removed from macOS startup.\n")
        except Exception as e:
            self.log_message(f"Error setting up macOS startup: {e}\n")

    def _setup_linux_startup(self):
        try:
            script_path = os.path.abspath("run.sh")
            desktop_entry = f'''[Desktop Entry]
Type=Application
Name=AI Tweaker
Exec={script_path}
StartupNotify=true
Terminal=false'''
            autostart_dir = os.path.expanduser("~/.config/autostart")
            if not os.path.exists(autostart_dir):
                os.makedirs(autostart_dir)
            desktop_file_path = os.path.join(autostart_dir, "tweaker.desktop")

            if self.app_settings.get("start_on_startup", False):
                with open(desktop_file_path, "w") as f:
                    f.write(desktop_entry)
                self.log_message("App set to start with Linux.\n")
            else:
                if os.path.exists(desktop_file_path):
                    os.remove(desktop_file_path)
                    self.log_message("App removed from Linux startup.\n")
        except Exception as e:
            self.log_message(f"Error setting up Linux startup: {e}\n")

    # --- Generic Methods ---
    def toggle_proxy(self):
        if self.proxy_process and self.proxy_process.poll() is None: self.stop_proxy() 
        else: self.start_proxy()

    def start_proxy(self):
        command = self.command_entry.get()
        if not command: self.log_message("Start command cannot be empty.\n"); return
        if command != self.active_profile.get("proxy_command"): self.active_profile["proxy_command"] = command; self.save_profiles()
        self.proxy_control_button.configure(text="Stop Proxy"); self.log_textbox.configure(state="normal"); self.log_textbox.delete("1.0", "end"); self.log_message(f"Starting proxy with command: {command}\n")
        def stream_reader(stream):
            for line in iter(stream.readline, ''):
                if line.startswith("[TERMINAL_LOG]"):
                    # Print to terminal without the prefix and with a newline
                    content = line[len("[TERMINAL_LOG]"):].strip()
                    print(content)
                    sys.stdout.flush()
                    self.log_message(content + "\n")
                else:
                    # Send to GUI log
                    self.log_message(line)
        def run_proxy():
            try:
                self.proxy_process = subprocess.Popen(command.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
                stdout_thread = threading.Thread(target=stream_reader, args=(self.proxy_process.stdout,)); stdout_thread.daemon = True; stdout_thread.start()
                stderr_thread = threading.Thread(target=stream_reader, args=(self.proxy_process.stderr,)); stderr_thread.daemon = True; stderr_thread.start()
                self.proxy_process.wait()
            except Exception as e: self.log_message(f"Failed to start proxy: {e}\n")
            finally: self.after(0, self.proxy_stopped)
        self.proxy_thread = threading.Thread(target=run_proxy); self.proxy_thread.daemon = True; self.proxy_thread.start()

    def stop_proxy(self):
        if self.proxy_process: self.proxy_process.terminate(); self.proxy_process = None; self.log_message("Proxy process terminated.\n")
        self.proxy_control_button.configure(text="Start Proxy")

    def proxy_stopped(self):
        self.proxy_control_button.configure(text="Start Proxy"); self.log_message("Proxy process stopped.\n")

    def restart_proxy_if_running(self):
        if self.proxy_process and self.proxy_process.poll() is None:
            self.log_message("Restarting proxy to apply configuration changes...\n"); self.stop_proxy(); self.after(200, self.start_proxy)

    def log_message(self, message):
        def _log():
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", message)
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
            for listener in self.log_listeners:
                listener(message)
        self.after(0, _log)

    def open_binary_search_window(self):
        if not hasattr(self, "binary_search_window") or not self.binary_search_window.winfo_exists():
            self.binary_search_window = BinarySearchWindow(self)
            self.binary_search_window.focus()
        else:
            self.binary_search_window.focus()

    def set_gemini_flags(self, flags_list):
        gemini_app_config = self.active_profile.setdefault("apps", {}).setdefault("gemini", {})
        flag_configs = {}
        for flag in flags_list:
            flag_configs[str(flag)] = {"note": "Binary Search", "enabled": True}
        gemini_app_config["flag_configs"] = flag_configs
        self.save_profiles()
        self.generate_rules_json()
        self.load_gemini_flags()

class BinarySearchWindow(customtkinter.CTkToplevel):
    def __init__(self, master_app):
        super().__init__(master_app)
        self.app = master_app
        self.title("Gemini Flag Binary Search")
        self.geometry("450x400")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.attributes("-topmost", True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Search range
        self.range_frame = customtkinter.CTkFrame(self)
        self.range_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.range_frame.grid_columnconfigure(0, weight=1)
        self.range_frame.grid_columnconfigure(1, weight=1)
        self.min_entry = customtkinter.CTkEntry(self.range_frame, placeholder_text="Min Flag ID")
        self.min_entry.insert(0, "45428766")
        self.min_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.max_entry = customtkinter.CTkEntry(self.range_frame, placeholder_text="Max Flag ID")
        self.max_entry.insert(0, "45999999")
        self.max_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.keep_flags_checkbox = customtkinter.CTkCheckBox(self.range_frame, text="Keep current flags enabled")
        self.keep_flags_checkbox.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        self.start_button = customtkinter.CTkButton(self.range_frame, text="Start Search", command=self.start_search)
        self.start_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Search status
        self.status_label = customtkinter.CTkLabel(self, text="Enter a range and start the search.", wraplength=400)
        self.status_label.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

        # User feedback
        self.feedback_frame = customtkinter.CTkFrame(self)
        self.feedback_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.feedback_frame.grid_columnconfigure(0, weight=1)
        self.feedback_frame.grid_columnconfigure(1, weight=1)
        self.question_label = customtkinter.CTkLabel(self.feedback_frame, text="Is the feature present?")
        self.question_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        self.yes_button = customtkinter.CTkButton(self.feedback_frame, text="Yes", command=self.found_feature, state="disabled")
        self.yes_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.no_button = customtkinter.CTkButton(self.feedback_frame, text="No", command=self.not_found_feature, state="disabled")
        self.no_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Instructions & Result
        self.info_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.info_frame.grid_columnconfigure(0, weight=1)

        self.cache_label = customtkinter.CTkLabel(self.info_frame, text="Remember to do a hard refresh (Ctrl+Shift+R) after each step.", wraplength=400)
        self.cache_label.grid(row=0, column=0, columnspan=2, padx=10, pady=5)

        self.copy_button = customtkinter.CTkButton(self.info_frame, text="Copy Flag ID", command=self.copy_flag)
        
        self.low = 0
        self.high = 0
        self.mid = 0
        self.original_flags = {}
        self.searching = False
        self.search_phase = "idle" # idle, initial_check, binary_search, verifying

    def copy_flag(self):
        self.clipboard_clear()
        self.clipboard_append(str(self.low))
        self.status_label.configure(text=f"Flag {self.low} copied to clipboard.")

    def _apply_test_range(self, test_range):
        flags_to_set = [test_range]
        if self.keep_flags_checkbox.get() == 1:
            enabled_original_flags = [flag for flag, config in self.original_flags.items() if config.get("enabled")]
            flags_to_set.extend(enabled_original_flags)
        self.app.set_gemini_flags(flags_to_set)

    def start_search(self):
        min_val = self.min_entry.get()
        max_val = self.max_entry.get()
        if not min_val.isdigit() or not max_val.isdigit() or int(min_val) >= int(max_val):
            self.status_label.configure(text="Invalid range. Please enter valid numbers with min < max.")
            return
        
        self.copy_button.grid_forget()
        self.low = int(min_val)
        self.high = int(max_val)
        self.original_flags = self.app.active_profile.get("apps", {}).get("gemini", {}).get("flag_configs", {}).copy()
        
        self.app.log_listeners.append(self.on_log_message)
        self.searching = True
        self.search_phase = "initial_check"
        self.start_button.configure(state="disabled")
        
        self._apply_test_range(f"{self.low}-{self.high}")
        self.status_label.configure(text=f"Testing initial range: {self.low}-{self.high}\nWaiting for Gemini script load...")
        self.yes_button.configure(state="disabled")
        self.no_button.configure(state="disabled")

    def next_step(self):
        if self.low > self.high:
            self.status_label.configure(text=f"Search failed. Range is empty. Last tested range was {self.low}-{self.high}")
            self.stop_search()
            return

        if self.low == self.high:
            self.search_phase = "verifying"
            self._apply_test_range(str(self.low))
            self.status_label.configure(text=f"Verifying final flag: {self.low}\nWaiting for script...")
            self.yes_button.configure(state="disabled")
            self.no_button.configure(state="disabled")
            return

        self.mid = (self.low + self.high) // 2
        self._apply_test_range(f"{self.low}-{self.mid}")
        
        self.status_label.configure(text=f"Testing range: {self.low}-{self.mid}\nWaiting for Gemini script load...")
        self.yes_button.configure(state="disabled")
        self.no_button.configure(state="disabled")

    def on_log_message(self, message):
        if self.searching and "Modified Gemini script" in message:
            if self.search_phase == "initial_check":
                self.status_label.configure(text=f"Script loaded with full range {self.low}-{self.high}\nIs the feature present?")
            elif self.search_phase == "binary_search":
                self.status_label.configure(text=f"Script loaded with range {self.low}-{self.mid}\nIs the feature present?")
            elif self.search_phase == "verifying":
                self.status_label.configure(text=f"Script loaded with final flag {self.low}\nIs the feature present?")
            self.yes_button.configure(state="normal")
            self.no_button.configure(state="normal")

    def found_feature(self): # Yes
        if self.search_phase == "initial_check":
            self.search_phase = "binary_search"
            self.next_step()
        elif self.search_phase == "binary_search":
            self.high = self.mid
            self.next_step()
        elif self.search_phase == "verifying":
            self.status_label.configure(text=f"Flag confirmed: {self.low}")
            self.yes_button.configure(state="disabled")
            self.no_button.configure(state="disabled")
            self.copy_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
            self.start_button.configure(text="Reset Search", command=self.stop_search, state="normal")
            if self.on_log_message in self.app.log_listeners:
                self.app.log_listeners.remove(self.on_log_message)
            self.searching = False

    def not_found_feature(self): # No
        if self.search_phase == "initial_check":
            self.status_label.configure(text="Feature not present in the selected range. Aborting search.")
            self.stop_search()
        elif self.search_phase == "binary_search":
            self.low = self.mid + 1
            self.next_step()
        elif self.search_phase == "verifying":
            self.status_label.configure(text=f"Verification failed for flag {self.low}. The feature was not present with only this flag enabled. Restarting search.")
            self.stop_search()

    def stop_search(self): # This is now the "Reset" method
        # Restore original flags if a search was ever started
        if self.original_flags:
            if self.on_log_message in self.app.log_listeners:
                self.app.log_listeners.remove(self.on_log_message)
            
            gemini_app_config = self.app.active_profile.setdefault("apps", {}).setdefault("gemini", {})
            gemini_app_config["flag_configs"] = self.original_flags
            self.app.save_profiles()
            self.app.generate_rules_json()
            self.app.load_gemini_flags()
            self.original_flags = {} # Clear after use

        # Always reset state and UI
        self.searching = False
        self.search_phase = "idle"
        
        self.status_label.configure(text="Enter a range and start the search.")
        self.start_button.configure(text="Start Search", command=self.start_search, state="normal")
        self.yes_button.configure(state="disabled")
        self.no_button.configure(state="disabled")
        self.copy_button.grid_forget()

    def on_close(self):
        self.stop_search()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
