import os
import json
from constants import (
    SETTINGS_FILE, VAULT_FILE, APP_NAME,
    DEFAULT_LANG, DEFAULT_THEME, DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE,
    DEFAULT_AUTO_LOCK_TIMEOUT
)
# SETTINGS_FILE is expected at the root where the app is run.
# This class will use it as is.

class SettingsManager:
    def __init__(self, filename=None):
        self.filename = filename if filename else SETTINGS_FILE
        self.filename = os.path.abspath(self.filename) # Use absolute path
        self.settings = self.load_settings()

    def load_settings(self):
        defaults = {
            "language": DEFAULT_LANG,
            "theme": DEFAULT_THEME,
            "font_family": DEFAULT_FONT_FAMILY,
            "font_size": DEFAULT_FONT_SIZE,
            "first_run": True, # Default to true, logic will check vault existence
            "auto_lock_timeout": DEFAULT_AUTO_LOCK_TIMEOUT,
            "vault_identifier": f"{APP_NAME}Vault"
        }
        if not os.path.exists(self.filename):
            # Determine first_run based on vault existence if settings file is new
            defaults["first_run"] = not os.path.exists(VAULT_FILE)
            self.save_settings(defaults)
            return defaults
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                # Ensure all default keys exist
                for key, value in defaults.items():
                    loaded_settings.setdefault(key, value)
                
                # Validate specific settings
                if loaded_settings.get("theme") not in ["light", "dark"]:
                    loaded_settings["theme"] = DEFAULT_THEME
                if not isinstance(loaded_settings.get("font_size"), int):
                    loaded_settings["font_size"] = DEFAULT_FONT_SIZE
                if not isinstance(loaded_settings.get("first_run"), bool):
                     # If first_run is corrupted, check vault existence
                     loaded_settings["first_run"] = not os.path.exists(VAULT_FILE)
                if not isinstance(loaded_settings.get("auto_lock_timeout"), int):
                    loaded_settings["auto_lock_timeout"] = DEFAULT_AUTO_LOCK_TIMEOUT
                return loaded_settings
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading settings file '{self.filename}': {e}. Using defaults.")
            # Re-determine first_run if settings are corrupted
            defaults["first_run"] = not os.path.exists(VAULT_FILE)
            self.save_settings(defaults) # Save a clean default file
            return defaults

    def save_settings(self, settings_data=None):
        if settings_data is None:
            settings_data = self.settings
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4, ensure_ascii=False)
            self.settings = settings_data # Update internal state
        except IOError as e:
            print(f"Error saving settings file '{self.filename}': {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()