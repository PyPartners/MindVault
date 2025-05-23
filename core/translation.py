import os
import json
from PyQt5.QtCore import Qt, QTranslator, QLocale, QLibraryInfo
from .utils import ensure_dir # from mindvault.core.utils
# LANG_DIR will be passed or set based on where the main app runs.
# Let's make it so that this class uses a lang_dir passed to it.

class TranslationHandler:
    def __init__(self, app, initial_lang='en', lang_dir="lang"): # lang_dir relative to CWD
        self.app = app
        self.translator = QTranslator(self.app)
        self.locale = initial_lang
        self.translations = {}
        self.lang_dir = os.path.abspath(lang_dir) # Ensure it's an absolute path
        ensure_dir(self.lang_dir) # Ensure the lang directory exists
        self.load_language(self.locale)

    def get_available_languages(self):
        langs = {}
        try:
            # ensure_dir(self.lang_dir) # Already done in __init__
            for filename in os.listdir(self.lang_dir):
                if filename.endswith(".json"):
                    lang_code = filename[:-5]
                    try:
                        with open(os.path.join(self.lang_dir, filename), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            lang_name = data.get("_lang_name_", lang_code.upper())
                            langs[lang_code] = lang_name
                    except Exception as e:
                        print(f"Error loading lang file {filename}: {e}")
            
            # Load Qt's own translations
            qt_translator = QTranslator()
            qt_locale = QLocale(self.locale) # Use current app locale
            ts_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)

            if qt_translator.load(qt_locale, "qt", "_", ts_path):
                 self.app.installTranslator(qt_translator)
            else:
                print(f"Could not load Qt translations for {self.locale} from {ts_path}")

            qt_base_translator = QTranslator()
            if qt_base_translator.load(qt_locale, "qtbase", "_", ts_path):
                self.app.installTranslator(qt_base_translator)
            else:
                print(f"Could not load QtBase translations for {self.locale} from {ts_path}")

        except FileNotFoundError:
            print(f"Language directory '{self.lang_dir}' not found.")
        except Exception as e:
            print(f"Error reading language directory: {e}")
        return langs

    def load_language(self, lang_code):
        lang_file = os.path.join(self.lang_dir, f"{lang_code}.json")
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            self.locale = lang_code
            print(f"Loaded language: {lang_code}")
            if lang_code == 'ar':
                self.app.setLayoutDirection(Qt.RightToLeft)
            else:
                self.app.setLayoutDirection(Qt.LeftToRight)
            
            # Re-attempt to load Qt translations for the new language
            self.get_available_languages() # This will re-install Qt translators for the new locale
            return True
        except FileNotFoundError:
            print(f"Translation file not found: {lang_file}")
            self.translations = {} # Fallback to keys
            self.app.setLayoutDirection(Qt.LeftToRight) # Default LTR
            return False
        except json.JSONDecodeError:
            print(f"Error decoding JSON from: {lang_file}")
            self.translations = {}
            self.app.setLayoutDirection(Qt.LeftToRight)
            return False
        except Exception as e:
            print(f"Error loading language {lang_code}: {e}")
            self.translations = {}
            self.app.setLayoutDirection(Qt.LeftToRight)
            return False

    def tr(self, key, *args):
        default_text = key.replace("_", " ").title() # Basic default text from key
        text = self.translations.get(key, default_text)
        try:
            if args:
                return text.format(*args)
            else:
                return text
        except (IndexError, KeyError, TypeError) as e:
             print(f"Translation formatting error for key '{key}' with text '{text}' and args {args}: {e}")
             return text if not args else default_text # Return unformatted text or default if args were expected