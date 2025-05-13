import os
import json
from config import DEFAULT_KEY_BINDINGS, THEMES

class Settings:
    def __init__(self):
        self.settings_file = "settings.json"
        self.key_bindings = DEFAULT_KEY_BINDINGS.copy()
        self.theme = "Classic"
        self.load_settings()

    def load_settings(self):
        #Load settings from settings.json
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r") as f:
                    data = json.load(f)
                    loaded_bindings = data.get("key_bindings", {})
                    for key in DEFAULT_KEY_BINDINGS:
                        if key in loaded_bindings:
                            self.key_bindings[key] = loaded_bindings[key]
                    self.theme = data.get("theme", "Classic") if data.get("theme") in THEMES else "Classic"
        except Exception as e:
            print(f"Failed to load settings: {e}")

    def save_key_bindings(self, key_bindings):
        #Save key bindings
        self.key_bindings = key_bindings
        self.save_settings()

    def save_theme(self, theme):
        #Save theme
        self.theme = theme
        self.save_settings()

    def save_settings(self):
        #Save settings to settings.json
        try:
            with open(self.settings_file, "w") as f:
                json.dump({"key_bindings": self.key_bindings, "theme": self.theme}, f)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def get_key_bindings(self):
        #Get current key bindings
        return self.key_bindings
 
    def get_theme(self):
        #Get current theme
        return self.theme