import sys
import os
import json
import base64
import hashlib
# Import necessary modules from cryptography
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
# Import necessary modules from PyQt5
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QListWidget, QListWidgetItem,
    QDialog, QFormLayout, QMessageBox, QFileDialog, QFontDialog,
    QComboBox, QDialogButtonBox, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QSpacerItem, QSizePolicy, QAction,
    QMenuBar, QMenu, QToolBar, QStatusBar
)
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QClipboard
from PyQt5.QtCore import Qt, QSize, QSettings, QTranslator, QLocale, QLibraryInfo

# --- Constants ---
APP_NAME = "MindVault"
APP_VERSION = "1.0.0"
SETTINGS_FILE = "settings.json"
VAULT_DIR = "data"
VAULT_FILE = os.path.join(VAULT_DIR, "vault.enc")
LANG_DIR = "lang"
DEFAULT_LANG = "ar"
DEFAULT_THEME = "light"
DEFAULT_FONT_FAMILY = "Tahoma"
DEFAULT_FONT_SIZE = 10

# PBKDF2 constants
PBKDF2_ITERATIONS = 390000
SALT_SIZE = 16
AES_NONCE_SIZE = 12
AES_TAG_SIZE = 16

# --- Helper Functions ---

def ensure_dir(directory):
    """Creates a directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

# derive_key remains the same: takes password string, returns derived key bytes
def derive_key(password: str, salt: bytes) -> bytes:
    """Derives a 32-byte key from the password string and salt using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # AES-256 key size
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend()
    )
    # Encode the password string to bytes here before deriving
    return kdf.derive(password.encode('utf-8'))

# encrypt_data now takes the *derived key*
def encrypt_data(data: dict, derived_key: bytes) -> bytes | None:
    """Encrypts dictionary data using AES-GCM with a pre-derived key.
       Returns nonce + ciphertext + tag."""
    try:
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        aesgcm = AESGCM(derived_key) # Use the derived key directly
        nonce = os.urandom(AES_NONCE_SIZE)
        # Encrypt, returns ciphertext + tag
        encrypted_data = aesgcm.encrypt(nonce, json_data, None)
        # Return nonce + encrypted_data (ciphertext + tag)
        return nonce + encrypted_data
    except Exception as e:
        print(f"Encryption Error (AESGCM): {e}")
        return None

# decrypt_data now takes the *master password string*
def decrypt_data(encrypted_blob: bytes, master_password: str) -> dict | None:
    """Decrypts data encrypted with AES-GCM using the master password string."""
    try:
        # Extract salt, nonce, and ciphertext+tag
        salt = encrypted_blob[:SALT_SIZE]
        nonce = encrypted_blob[SALT_SIZE:SALT_SIZE + AES_NONCE_SIZE]
        ciphertext_with_tag = encrypted_blob[SALT_SIZE + AES_NONCE_SIZE:]

        if len(nonce) != AES_NONCE_SIZE or len(salt) != SALT_SIZE:
             print("Decryption Error: Invalid length for salt or nonce.")
             return None

        # Derive the key using the *provided master password string* and the extracted salt
        derived_key = derive_key(master_password, salt) # Use password string here

        aesgcm = AESGCM(derived_key)
        # Decrypt using nonce and ciphertext+tag
        decrypted_data = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
        return json.loads(decrypted_data.decode('utf-8'))
    except Exception as e: # Catches InvalidTag, ValueError, struct.error etc.
        # Important: InvalidTag means wrong password or data corruption
        print(f"Decryption Error: {e}")
        return None # Indicates decryption failure

# --- Wrapper functions for vault handling ---

def encrypt_vault(data: dict, master_password: str) -> bytes | None:
    """Derives key, encrypts data, and prepends salt and nonce."""
    try:
        salt = os.urandom(SALT_SIZE)
        # Derive key from the master password string
        derived_key = derive_key(master_password, salt)
        # Encrypt data using the derived key
        nonce_and_ciphertext = encrypt_data(data, derived_key)
        if nonce_and_ciphertext:
            # Prepend the salt used for key derivation
            # Result: salt + nonce + ciphertext + tag
            return salt + nonce_and_ciphertext
        else:
            print("Vault Encryption Error: encrypt_data failed.")
            return None # encrypt_data failed
    except Exception as e:
         print(f"Vault Encryption Wrapper Error: {e}")
         return None

# decrypt_data function already handles the full process, no separate wrapper needed

# --- Translation Handler ---
class TranslationHandler:
    def __init__(self, app, initial_lang='en'):
        self.app = app
        self.translator = QTranslator(self.app)
        self.locale = initial_lang
        self.translations = {}
        self.load_language(self.locale)

    def get_available_languages(self):
        langs = {}
        try:
            ensure_dir(LANG_DIR)
            for filename in os.listdir(LANG_DIR):
                if filename.endswith(".json"):
                    lang_code = filename[:-5] # Remove .json
                    try:
                        with open(os.path.join(LANG_DIR, filename), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Assume language name is stored with a key like "_lang_name_"
                            lang_name = data.get("_lang_name_", lang_code.upper())
                            langs[lang_code] = lang_name
                    except Exception as e:
                        print(f"Error loading lang file {filename}: {e}")
            # Add built-in Qt translations if available
            qt_translator = QTranslator()
            qt_locale = QLocale(self.locale)
            ts_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
            if qt_translator.load(qt_locale, "qt", "_", ts_path):
                 self.app.installTranslator(qt_translator)
                 # print(f"Loaded Qt base translations for {self.locale}") # Optional debug

            qt_base_translator = QTranslator()
            if qt_base_translator.load(qt_locale, "qtbase", "_", ts_path):
                self.app.installTranslator(qt_base_translator)
                # print(f"Loaded Qt base translations for {self.locale}") # Optional debug

        except FileNotFoundError:
            print(f"Language directory '{LANG_DIR}' not found.")
        except Exception as e:
            print(f"Error reading language directory: {e}")
        return langs


    def load_language(self, lang_code):
        lang_file = os.path.join(LANG_DIR, f"{lang_code}.json")
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            self.locale = lang_code
            # Install translator for custom strings
            # No need to install QTranslator here, we just use the dict lookup
            print(f"Loaded language: {lang_code}")
            # Set layout direction based on language
            if lang_code == 'ar':
                self.app.setLayoutDirection(Qt.RightToLeft)
            else:
                self.app.setLayoutDirection(Qt.LeftToRight)
            return True
        except FileNotFoundError:
            print(f"Translation file not found: {lang_file}")
            self.translations = {} # Clear translations if file not found
            self.app.setLayoutDirection(Qt.LeftToRight)
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
        """Translates a key using the loaded language file, supports basic formatting."""
        default_text = key # Use key as default if not found
        text = self.translations.get(key, default_text)
        try:
            # Basic positional formatting support
            if args:
                return text.format(*args)
            else:
                return text
        except (IndexError, KeyError, TypeError) as e:
             # Handle potential errors if formatting codes mismatch arguments
             print(f"Translation formatting error for key '{key}' with text '{text}' and args {args}: {e}")
             # Fallback to unformatted text or default
             return text if not args else default_text


# --- Settings Manager (remains the same) ---
class SettingsManager:
    def __init__(self, filename=SETTINGS_FILE):
        self.filename = filename
        self.settings = self.load_settings()

    def load_settings(self):
        defaults = {
            "language": DEFAULT_LANG,
            "theme": DEFAULT_THEME,
            "font_family": DEFAULT_FONT_FAMILY,
            "font_size": DEFAULT_FONT_SIZE,
            "first_run": True
        }
        if not os.path.exists(self.filename):
            self.save_settings(defaults)
            return defaults
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                # Ensure all keys exist, using defaults if missing
                for key, value in defaults.items():
                    loaded_settings.setdefault(key, value) # Use setdefault for cleaner merge

                # Basic validation (optional but good)
                if loaded_settings["theme"] not in ["light", "dark"]:
                    loaded_settings["theme"] = DEFAULT_THEME
                if not isinstance(loaded_settings["font_size"], int):
                    loaded_settings["font_size"] = DEFAULT_FONT_SIZE
                # Make sure first_run is boolean
                if not isinstance(loaded_settings["first_run"], bool):
                     loaded_settings["first_run"] = not os.path.exists(VAULT_FILE)


                return loaded_settings
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading settings file '{self.filename}': {e}. Using defaults.")
            # In case of error, save default settings to ensure a valid file exists
            self.save_settings(defaults)
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
        self.save_settings() # Save immediately on change

# --- UI Styles (remains the same) ---
STYLES = {
    "light": {
        "background": "#FAFAFA",
        "foreground": "#121212",
        "primary": "#2196F3", # Blue
        "primary_text": "#FFFFFF",
        "secondary": "#E0E0E0", # Light grey for borders/separators
        "list_selection": "#BBDEFB", # Lighter blue for selection
        "qss": """
            QMainWindow, QDialog {{
                background-color: {background};
                color: {foreground};
            }}
            QWidget {{ /* Catches most background widgets */
                 background-color: {background};
                 color: {foreground};
            }}
            QLabel {{
                color: {foreground};
                background-color: transparent; /* Ensure labels have transparent background */
            }}
            QLineEdit, QTextEdit {{
                background-color: #FFFFFF;
                color: {foreground};
                border: 1px solid {secondary};
                border-radius: 4px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {primary};
                color: {primary_text};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #1976D2; /* Darker blue */
            }}
            QPushButton:pressed {{
                background-color: #0D47A1; /* Even darker blue */
            }}
            QPushButton:disabled {{
                background-color: #BDBDBD; /* Grey out disabled buttons */
                color: #757575;
            }}
            QPushButton#copyButton {{ /* Specific style example */
                 background-color: #4CAF50; /* Green */
            }}
            QPushButton#copyButton:hover {{
                 background-color: #388E3C;
            }}
            QPushButton#copyButton:disabled {{
                background-color: #C8E6C9;
                color: #757575;
            }}
             QPushButton#deleteButton {{ /* Specific style example */
                 background-color: #f44336; /* Red */
            }}
            QPushButton#deleteButton:hover {{
                 background-color: #d32f2f;
            }}
            QPushButton#deleteButton:disabled {{
                background-color: #FFCDD2;
                color: #757575;
            }}
            QTableWidget {{
                background-color: #FFFFFF;
                color: {foreground};
                border: 1px solid {secondary};
                gridline-color: {secondary};
                border-radius: 4px;
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {list_selection};
                color: {foreground}; /* Keep text readable */
            }}
            QHeaderView::section {{
                background-color: {secondary};
                color: {foreground};
                padding: 4px;
                border: 1px solid {background}; /* Use main background for subtle border */
                font-weight: bold;
            }}
             QMenuBar {{
                background-color: {secondary};
                color: {foreground};
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 4px 8px;
            }}
            QMenuBar::item:selected {{
                background: {list_selection};
            }}
             QMenuBar::item:disabled {{
                color: #9E9E9E; /* Grey out disabled menu items */
            }}
            QMenu {{
                background-color: {background};
                border: 1px solid {secondary};
                color: {foreground};
            }}
            QMenu::item:selected {{
                background-color: {primary};
                color: {primary_text};
            }}
             QMenu::item:disabled {{
                color: #BDBDBD; /* Grey out disabled menu actions */
                background-color: transparent;
            }}
             QToolBar {{
                 background-color: {background};
                 border: none;
                 padding: 2px;
             }}
             QStatusBar {{
                 background-color: {secondary};
                 color: {foreground};
             }}
             QComboBox {{
                border: 1px solid {secondary};
                border-radius: 3px;
                padding: 1px 18px 1px 3px;
                min-width: 6em;
                background-color: white;
             }}
             QComboBox::drop-down {{
                 subcontrol-origin: padding;
                 subcontrol-position: top right;
                 width: 15px;
                 border-left-width: 1px;
                 border-left-color: {secondary};
                 border-left-style: solid;
                 border-top-right-radius: 3px;
                 border-bottom-right-radius: 3px;
             }}
            QComboBox QAbstractItemView {{
                border: 1px solid {secondary};
                selection-background-color: {primary};
                background-color: white;
                color: {foreground};
            }}
        """
    },
    "dark": {
        "background": "#121212",
        "foreground": "#E0E0E0", # Light grey text
        "primary": "#03DAC5", # Teal/Turquoise
        "primary_text": "#000000", # Black text on Teal
        "secondary": "#333333", # Dark grey for borders/surfaces
        "list_selection": "#03DAC5", # Use primary for selection
        "qss": """
            QMainWindow, QDialog {{
                background-color: {background};
                color: {foreground};
            }}
             QWidget {{ /* Catches most background widgets */
                 background-color: {background};
                 color: {foreground};
            }}
            QLabel {{
                color: {foreground};
                background-color: transparent;
            }}
            QLineEdit, QTextEdit {{
                background-color: {secondary};
                color: {foreground};
                border: 1px solid #555555; /* Slightly lighter border */
                border-radius: 4px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {primary};
                color: {primary_text}; /* Black text */
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                 min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #018786; /* Darker Teal */
            }}
            QPushButton:pressed {{
                background-color: #005F5F; /* Even darker Teal */
            }}
            QPushButton:disabled {{
                background-color: #424242; /* Darker grey for disabled */
                color: #757575;
            }}
             QPushButton#copyButton {{ /* Specific style example */
                 background-color: #81C784; /* Light Green */
                 color: #000000;
            }}
            QPushButton#copyButton:hover {{
                 background-color: #66BB6A;
            }}
             QPushButton#copyButton:disabled {{
                background-color: #4A7C4B;
                color: #9E9E9E;
            }}
             QPushButton#deleteButton {{ /* Specific style example */
                 background-color: #E57373; /* Light Red */
                 color: #000000;
            }}
            QPushButton#deleteButton:hover {{
                 background-color: #EF5350;
            }}
            QPushButton#deleteButton:disabled {{
                background-color: #8B4D4D;
                color: #9E9E9E;
            }}
            QTableWidget {{
                background-color: {secondary};
                color: {foreground};
                border: 1px solid #555555;
                gridline-color: #555555;
                border-radius: 4px;
            }}
             QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {list_selection};
                color: {primary_text}; /* Black text for contrast on Teal */
            }}
            QHeaderView::section {{
                background-color: #424242; /* Slightly lighter dark grey */
                color: {foreground};
                padding: 4px;
                border: 1px solid {background};
                font-weight: bold;
            }}
             QMenuBar {{
                background-color: {secondary};
                color: {foreground};
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 4px 8px;
            }}
            QMenuBar::item:selected {{
                background: #555555;
            }}
            QMenuBar::item:disabled {{
                color: #757575; /* Grey out disabled menu items */
            }}
            QMenu {{
                background-color: {secondary};
                border: 1px solid #555555;
                color: {foreground};
            }}
            QMenu::item:selected {{
                background-color: {primary};
                color: {primary_text};
            }}
            QMenu::item:disabled {{
                color: #757575; /* Grey out disabled menu actions */
                background-color: transparent;
            }}
             QToolBar {{
                 background-color: {background};
                 border: none;
                 padding: 2px;
             }}
             QStatusBar {{
                 background-color: {secondary};
                 color: {foreground};
             }}
             QComboBox {{
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 1px 18px 1px 3px;
                min-width: 6em;
                background-color: {secondary};
                color: {foreground};
             }}
              QComboBox::drop-down {{
                 subcontrol-origin: padding;
                 subcontrol-position: top right;
                 width: 15px;
                 border-left-width: 1px;
                 border-left-color: #555555;
                 border-left-style: solid;
                 border-top-right-radius: 3px;
                 border-bottom-right-radius: 3px;
             }}
            QComboBox QAbstractItemView {{ /* Style the dropdown list */
                border: 1px solid #555555;
                selection-background-color: {primary};
                selection-color: {primary_text};
                background-color: {secondary}; /* Background of the dropdown list */
                color: {foreground}; /* Text color in the dropdown list */
            }}
        """
    }
}

def apply_theme(app, theme_name):
    """Applies the selected theme's stylesheet."""
    if theme_name in STYLES:
        style_data = STYLES[theme_name]
        # Replace placeholders in QSS string
        qss = style_data["qss"].format(**style_data)
        app.setStyleSheet(qss)
        # Adjust palette for standard controls if needed (sometimes QSS isn't enough)
        palette = QPalette()
        text_color = QColor(style_data["foreground"])
        disabled_text_color = QColor("#808080") if theme_name == 'light' else QColor("#757575")
        base_color = QColor("#FFFFFF") if theme_name == 'light' else QColor(style_data["secondary"])
        button_color = QColor(style_data["primary"])
        button_text_color = QColor(style_data["primary_text"])
        highlight_color = QColor(style_data["list_selection"])
        highlighted_text_color = QColor(style_data.get("selected_text", style_data["foreground"]))
        if theme_name == 'dark' and highlight_color == QColor(style_data["primary"]):
            highlighted_text_color = QColor(style_data["primary_text"]) # Use primary text for dark theme highlight

        palette.setColor(QPalette.Window, QColor(style_data["background"]))
        palette.setColor(QPalette.WindowText, text_color)
        palette.setColor(QPalette.Base, base_color)
        palette.setColor(QPalette.AlternateBase, QColor(style_data["secondary"]))
        palette.setColor(QPalette.ToolTipBase, QColor(style_data["background"]))
        palette.setColor(QPalette.ToolTipText, text_color)
        palette.setColor(QPalette.Text, text_color)
        palette.setColor(QPalette.Button, button_color)
        palette.setColor(QPalette.ButtonText, button_text_color)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(style_data["primary"]))
        palette.setColor(QPalette.Highlight, highlight_color)
        palette.setColor(QPalette.HighlightedText, highlighted_text_color)

        # Set colors for disabled state more explicitly
        palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text_color)
        palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text_color)
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text_color)
        palette.setColor(QPalette.Disabled, QPalette.Base, QColor(style_data["secondary"]) if theme_name == 'light' else QColor("#222222"))
        palette.setColor(QPalette.Disabled, QPalette.Button, QColor("#BDBDBD") if theme_name == 'light' else QColor("#424242"))
        palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor("#D0D0D0") if theme_name == 'light' else QColor("#444444"))
        palette.setColor(QPalette.Disabled, QPalette.HighlightedText, disabled_text_color)

        app.setPalette(palette)

    else:
        print(f"Theme '{theme_name}' not found.")

# --- UI Components ---

# AccountDialog remains the same
class AccountDialog(QDialog):
    """Dialog for adding or editing an account."""
    def __init__(self, translator, account_data=None, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.account_data = account_data if account_data else {}

        self.setWindowTitle(self.translator.tr("add_edit_account_title"))
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        self.site_name_edit = QLineEdit(self.account_data.get("site", ""))
        self.username_edit = QLineEdit(self.account_data.get("username", ""))
        self.password_edit = QLineEdit(self.account_data.get("password", ""))
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.notes_edit = QLineEdit(self.account_data.get("notes", "")) # Changed to QLineEdit for simplicity

        self.show_password_button = QPushButton(self.translator.tr("show_password"))
        self.show_password_button.setCheckable(True)
        self.show_password_button.toggled.connect(self.toggle_password_visibility)

        # Password field layout
        password_layout = QHBoxLayout()
        password_layout.addWidget(self.password_edit)
        password_layout.addWidget(self.show_password_button)

        layout.addRow(self.translator.tr("site_name_label"), self.site_name_edit)
        layout.addRow(self.translator.tr("username_label"), self.username_edit)
        layout.addRow(self.translator.tr("password_label"), password_layout)
        layout.addRow(self.translator.tr("notes_label"), self.notes_edit)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        # Translate standard buttons
        self.button_box.button(QDialogButtonBox.Ok).setText(self.translator.tr("ok_button"))
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.translator.tr("cancel_button"))

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout.addRow(self.button_box)

        # Set initial state for show password button
        self.toggle_password_visibility(False)

    def toggle_password_visibility(self, checked):
        if checked:
            self.password_edit.setEchoMode(QLineEdit.Normal)
            self.show_password_button.setText(self.translator.tr("hide_password"))
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.show_password_button.setText(self.translator.tr("show_password"))

    def get_data(self):
        site = self.site_name_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text() # Don't strip password
        notes = self.notes_edit.text().strip()

        # Basic validation
        if not site or not username or not password:
            QMessageBox.warning(self, self.translator.tr("input_error_title"),
                                self.translator.tr("input_error_message"))
            return None

        return {
            "site": site,
            "username": username,
            "password": password,
            "notes": notes,
            # Use existing ID if editing, otherwise generate new unique ID
            "id": self.account_data.get("id", base64.urlsafe_b64encode(os.urandom(9)).decode('utf-8'))
        }

    @staticmethod
    def show_dialog(translator, account_data=None, parent=None):
        dialog = AccountDialog(translator, account_data, parent)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_data()
        return None

# SettingsDialog remains the same
class SettingsDialog(QDialog):
    """Dialog for changing application settings."""
    def __init__(self, translator, settings_manager, available_languages, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.settings_manager = settings_manager
        self.available_languages = available_languages # Dict: {'code': 'Name'}

        self.setWindowTitle(self.translator.tr("settings_title"))
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Language Selection
        self.lang_combo = QComboBox()
        current_lang_code = self.settings_manager.get("language")
        current_index = 0
        # Sort languages by name for display
        sorted_langs = sorted(self.available_languages.items(), key=lambda item: item[1])
        for i, (code, name) in enumerate(sorted_langs):
            self.lang_combo.addItem(f"{name} ({code})", code) # Display name, store code
            if code == current_lang_code:
                current_index = i
        self.lang_combo.setCurrentIndex(current_index)
        form_layout.addRow(self.translator.tr("language_label"), self.lang_combo)

        # Theme Selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItem(self.translator.tr("theme_light"), "light")
        self.theme_combo.addItem(self.translator.tr("theme_dark"), "dark")
        current_theme = self.settings_manager.get("theme")
        self.theme_combo.setCurrentIndex(0 if current_theme == "light" else 1)
        form_layout.addRow(self.translator.tr("theme_label"), self.theme_combo)

        # Font Selection
        font_layout = QHBoxLayout()
        current_font = QFont(self.settings_manager.get("font_family"), self.settings_manager.get("font_size"))
        self.font_label = QLabel(f"{current_font.family()}, {current_font.pointSize()}pt")
        self.font_label.setFont(current_font) # Apply font to label itself
        self.font_button = QPushButton(self.translator.tr("select_font_button"))
        self.font_button.clicked.connect(self.select_font)
        font_layout.addWidget(self.font_label, 1) # Stretch label
        font_layout.addWidget(self.font_button)
        form_layout.addRow(self.translator.tr("font_label"), font_layout)
        self.selected_font = current_font # Store the QFont object

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(
             QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
             Qt.Horizontal, self
        )
        self.button_box.button(QDialogButtonBox.Ok).setText(self.translator.tr("ok_button"))
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.translator.tr("cancel_button"))

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.language_changed = False
        self.theme_changed = False
        self.font_changed = False

    def select_font(self):
        """
        يفتح مربع حوار لاختيار الخط ويقوم بتحديث الخط المحدد والمعاينة.
        """
        print(f"[DEBUG] الخط الحالي قبل الفتح: {self.selected_font.family()}, {self.selected_font.pointSize()}pt")

        try:
            font, ok = QFontDialog.getFont(
                self.selected_font,          
                self,                        
                self.translator.tr("select_font_dialog_title") 
            )

            print(f"[DEBUG] QFontDialog.getFont returned: ok={ok}, font type={type(font)}")

            if ok:
                print(f"[DEBUG] تم اختيار الخط: {font.family()}, {font.pointSize()}pt")
                try:
                    self.selected_font = font  
                    display_text = f"{font.family()}, {font.pointSize()}pt"

                    self.font_label.setText(display_text) 
                    self.font_label.setFont(font)         
                    self.font_changed = True              
                    print("[DEBUG] تم تطبيق الخط بنجاح.")

                except Exception as ex:
                    QMessageBox.warning(self, self.translator.tr("error"),
                                        f"{self.translator.tr('error_applying_font')}:\n{ex}")
            else:
                print("[DEBUG] تم إلغاء اختيار الخط.")

        except Exception as e:
            print(f"[DEBUG] خطأ أثناء استدعاء QFontDialog.getFont: {e}")
            QMessageBox.critical(self, self.translator.tr("error"),
                                 f"{self.translator.tr('error_opening_font_dialog')}:\n{e}")

    def accept(self):
        # Check if settings changed
        new_lang = self.lang_combo.currentData()
        new_theme = self.theme_combo.currentData()
        new_font_family = self.selected_font.family()
        new_font_size = self.selected_font.pointSize()

        if new_lang != self.settings_manager.get("language"):
            self.language_changed = True
            self.settings_manager.set("language", new_lang)

        if new_theme != self.settings_manager.get("theme"):
            self.theme_changed = True
            self.settings_manager.set("theme", new_theme)

        # Check font changes more robustly
        font_family_changed = new_font_family != self.settings_manager.get("font_family")
        font_size_changed = new_font_size != self.settings_manager.get("font_size")

        if font_family_changed or font_size_changed:
            self.font_changed = True
            if font_family_changed:
                self.settings_manager.set("font_family", new_font_family)
            if font_size_changed:
                self.settings_manager.set("font_size", new_font_size)

        if self.language_changed:
             QMessageBox.information(self, self.translator.tr("info_title"),
                                     self.translator.tr("language_change_message"))

        super().accept() # Close dialog

    def get_changes(self):
        return {
            "language_changed": self.language_changed,
            "theme_changed": self.theme_changed,
            "font_changed": self.font_changed,
        }

# SetupWindow remains the same
class SetupWindow(QDialog):
    """Initial setup window to create the master password."""
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.master_password = None # Store the password string

        self.setWindowTitle(self.translator.tr("setup_title"))
        self.setMinimumWidth(400)
        self.setModal(True) # Block interaction with other windows

        layout = QVBoxLayout(self)

        welcome_label = QLabel(self.translator.tr("setup_welcome"))
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("font-size: 16pt; margin-bottom: 15px;")

        instruction_label = QLabel(self.translator.tr("setup_instruction"))
        instruction_label.setWordWrap(True)

        form_layout = QFormLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText(self.translator.tr("master_password_placeholder", 8)) # Min length hint
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setPlaceholderText(self.translator.tr("confirm_password_placeholder"))
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)

        form_layout.addRow(self.translator.tr("master_password_label"), self.password_edit)
        form_layout.addRow(self.translator.tr("confirm_password_label"), self.confirm_password_edit)

        # Password strength indicator (basic example)
        self.strength_label = QLabel(self.translator.tr("password_strength_weak"))
        self.password_edit.textChanged.connect(self.check_password_strength)
        form_layout.addRow(self.translator.tr("password_strength_label"), self.strength_label)

        layout.addWidget(welcome_label)
        layout.addWidget(instruction_label)
        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.translator.tr("create_button"))
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.translator.tr("cancel_button"))
        # Disable OK initially
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)


        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject) # Closes the dialog

        layout.addWidget(self.button_box)

        # Connect signals to validation
        self.password_edit.textChanged.connect(self.validate_inputs)
        self.confirm_password_edit.textChanged.connect(self.validate_inputs)


        # Initial strength check and validation
        self.check_password_strength("")
        self.validate_inputs()


    def check_password_strength(self, password):
        length = len(password)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(not c.isalnum() for c in password)
        score = 0
        if length >= 8: score += 1
        if length >= 12: score += 1
        if has_upper and has_lower: score += 1
        if has_digit: score += 1
        if has_symbol: score += 1

        if score >= 4:
            self.strength_label.setText(self.translator.tr("password_strength_strong"))
            self.strength_label.setStyleSheet("color: green;")
        elif score >= 3:
            self.strength_label.setText(self.translator.tr("password_strength_medium"))
            self.strength_label.setStyleSheet("color: orange;")
        else:
            self.strength_label.setText(self.translator.tr("password_strength_weak"))
            self.strength_label.setStyleSheet("color: red;")
        return score # Return score for validation


    def validate_inputs(self):
        """Enable OK button only if passwords match and meet minimum criteria."""
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        strength_score = self.check_password_strength(password)

        passwords_match = password == confirm_password
        # Minimum criteria: match and length >= 8
        is_valid = passwords_match and len(password) >= 8

        # Optional: Require minimum strength (e.g., medium)
        # is_valid = is_valid and strength_score >= 3

        self.button_box.button(QDialogButtonBox.Ok).setEnabled(is_valid)


    def validate_and_accept(self):
        # Re-check just in case (should be guaranteed by validate_inputs)
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        if not password or len(password) < 8:
            QMessageBox.warning(self, self.translator.tr("error_title"), self.translator.tr("error_password_short", 8))
            return

        if password != confirm_password:
            QMessageBox.warning(self, self.translator.tr("error_title"), self.translator.tr("error_password_mismatch"))
            return

        # Optional warning for weak passwords even if length is okay
        strength_score = self.check_password_strength(password)
        if strength_score < 3: # Less than medium
             reply = QMessageBox.question(self, self.translator.tr("warning_title"),
                                          self.translator.tr("warning_password_weak"),
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
             if reply == QMessageBox.No:
                 return


        self.master_password = password # Store the password string
        self.accept() # Close the dialog successfully

    def get_master_password(self):
        """Returns the master password string."""
        return self.master_password

# LoginWindow remains the same
class LoginWindow(QDialog):
    """Login window to enter the master password."""
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.master_password = None # Store the password string

        self.setWindowTitle(f"{APP_NAME} - {self.translator.tr('login_title')}")
        self.setMinimumWidth(350)
        self.setModal(True)

        layout = QVBoxLayout(self)

        icon_label = QLabel()
        # Placeholder icon (replace with QPixmap if you have an icon file)
        icon_label.setText("🔒")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48pt; margin-bottom: 15px;")


        prompt_label = QLabel(self.translator.tr("login_prompt"))
        prompt_label.setAlignment(Qt.AlignCenter)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText(self.translator.tr("master_password_label"))
        self.password_edit.setEchoMode(QLineEdit.Password)
        # Trigger accept on Enter key press
        self.password_edit.returnPressed.connect(self.validate_and_accept) # Connect directly


        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True) # Allow wrapping for longer errors
        self.error_label.hide() # Hidden initially


        layout.addWidget(icon_label)
        layout.addWidget(prompt_label)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.error_label)

        # Use standard buttons for OK/Cancel behavior
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.translator.tr("login_button"))
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.translator.tr("exit_button")) # Exit instead of Cancel
        # Disable OK initially until password entered
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.password_edit.textChanged.connect(lambda text: self.button_box.button(QDialogButtonBox.Ok).setEnabled(bool(text)))


        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject) # Rejection will close the app via main logic

        layout.addWidget(self.button_box)

        # Focus the password field on open
        self.password_edit.setFocus()


    def validate_and_accept(self):
        password = self.password_edit.text()
        if not password:
            # This shouldn't happen if OK button is disabled, but check anyway
            self.show_error(self.translator.tr("error_password_empty"))
            return

        self.master_password = password # Store password string
        self.error_label.hide() # Hide error on successful attempt before closing
        self.accept() # Signal successful attempt

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()
        self.password_edit.selectAll() # Select text for easy re-entry
        self.password_edit.setFocus()

    def get_master_password(self):
        """Returns the master password string."""
        return self.master_password


# MainWindow requires changes to use the new encryption/decryption flow
class MainWindow(QMainWindow):
    """Main application window."""
    def __init__(self, translator, settings_manager):
        super().__init__()
        self.translator = translator
        self.settings_manager = settings_manager
        self.master_key_string = None # Store the master password *string*
        self.vault_data = {"accounts": []} # In-memory decrypted data

        self.setWindowTitle(APP_NAME)
        self.resize(800, 600)

        # Central Widget and Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- Search Bar ---
        search_layout = QHBoxLayout()
        self.search_label = QLabel(self.translator.tr("search_label")) # Store label ref
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translator.tr("search_placeholder"))
        self.search_input.textChanged.connect(self.filter_accounts)
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # --- Accounts Table ---
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(3)
        # Set header labels later in retranslate_ui
        self.accounts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.accounts_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.accounts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.accounts_table.horizontalHeader().setStretchLastSection(True)
        self.accounts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.accounts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.accounts_table.verticalHeader().setVisible(False)
        self.accounts_table.itemSelectionChanged.connect(self.update_button_states)
        self.accounts_table.doubleClicked.connect(self.edit_selected_account)

        main_layout.addWidget(self.accounts_table)

        # --- Button Row ---
        button_layout = QHBoxLayout()
        self.add_button = QPushButton() # Text set in retranslate
        self.edit_button = QPushButton()
        self.delete_button = QPushButton()
        self.copy_button = QPushButton()

        self.delete_button.setObjectName("deleteButton")
        self.copy_button.setObjectName("copyButton")

        self.add_button.clicked.connect(self.add_account)
        self.edit_button.clicked.connect(self.edit_selected_account)
        self.delete_button.clicked.connect(self.delete_selected_account)
        self.copy_button.clicked.connect(self.copy_selected_password)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)) # Spacer
        button_layout.addWidget(self.copy_button)

        main_layout.addLayout(button_layout)

        # --- Actions, Menu, Toolbar, Status Bar ---
        self.create_actions()
        self.create_menus() # Store menu references
        self.create_toolbar()
        self.create_statusbar()

        # --- Initial State ---
        self.update_button_states() # Disable buttons initially
        self._clipboard = QApplication.clipboard() # Get clipboard instance
        self.retranslate_ui() # Apply initial translations

    def create_actions(self):
        # Define actions without text initially, text set in retranslate_ui
        self.add_act = QAction(QIcon.fromTheme("list-add", QIcon("icons/add.png")), "", self, triggered=self.add_account)
        self.edit_act = QAction(QIcon.fromTheme("document-edit", QIcon("icons/edit.png")), "", self, triggered=self.edit_selected_account)
        self.delete_act = QAction(QIcon.fromTheme("edit-delete", QIcon("icons/delete.png")), "", self, triggered=self.delete_selected_account)
        self.copy_act = QAction(QIcon.fromTheme("edit-copy", QIcon("icons/copy.png")), "", self, triggered=self.copy_selected_password)
        self.settings_act = QAction(QIcon.fromTheme("preferences-system", QIcon("icons/settings.png")), "", self, triggered=self.open_settings)
        self.lock_act = QAction(QIcon.fromTheme("system-lock-screen", QIcon("icons/lock.png")), "", self, triggered=self.lock_vault)
        self.exit_act = QAction(QIcon.fromTheme("application-exit", QIcon("icons/exit.png")), "", self, triggered=self.close)
        self.about_act = QAction("", self, triggered=self.show_about_dialog) # No icon for about usually

        # Set shortcuts
        self.add_act.setShortcut("Ctrl+N")
        self.edit_act.setShortcut("Ctrl+E")
        self.delete_act.setShortcut(Qt.Key_Delete) # Use Qt.Key enum
        self.copy_act.setShortcut("Ctrl+C")
        self.settings_act.setShortcut("Ctrl+,")
        self.lock_act.setShortcut("Ctrl+L")
        self.exit_act.setShortcut("Ctrl+Q")

    def create_menus(self):
        self.menu_bar = self.menuBar()
        # Create menus, text set in retranslate_ui
        self.file_menu = self.menu_bar.addMenu("")
        self.edit_menu = self.menu_bar.addMenu("")
        self.help_menu = self.menu_bar.addMenu("")

        # Add actions to menus
        self.file_menu.addAction(self.add_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.lock_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.settings_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_act)

        self.edit_menu.addAction(self.edit_act)
        self.edit_menu.addAction(self.delete_act)
        self.edit_menu.addSeparator()
        self.edit_menu.addAction(self.copy_act)

        self.help_menu.addAction(self.about_act)

    def create_toolbar(self):
        # Create toolbar, title set in retranslate_ui
        self.toolbar = self.addToolBar("")
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setMovable(False)

        self.toolbar.addAction(self.add_act)
        self.toolbar.addAction(self.edit_act)
        self.toolbar.addAction(self.delete_act)
        self.toolbar.addAction(self.copy_act)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.settings_act)
        self.toolbar.addAction(self.lock_act)

    def create_statusbar(self):
        self.status_bar = self.statusBar() # Store reference
        # Initial message set in retranslate_ui

    def load_vault(self, master_password_string):
        """Loads and decrypts the vault file using the master password string."""
        self.master_key_string = master_password_string # Store the string

        if not os.path.exists(VAULT_FILE):
            # This case is handled by the setup process, but good to check
            print("Vault file does not exist upon load request.")
            self.vault_data = {"accounts": []}
            # Don't save here, initial save happens during setup
            self.populate_accounts_table()
            return True # Treat as success (empty vault loaded)

        try:
            with open(VAULT_FILE, 'rb') as f:
                encrypted_blob = f.read()

            # Use the master password string to decrypt
            decrypted_data = decrypt_data(encrypted_blob, self.master_key_string)

            if decrypted_data is None:
                # Decryption failed (likely wrong password or corruption)
                return False # Signal failure

            # Decryption successful
            self.vault_data = decrypted_data
            if "accounts" not in self.vault_data or not isinstance(self.vault_data["accounts"], list):
                 print("Vault data malformed, resetting accounts list.")
                 self.vault_data["accounts"] = []
            self.populate_accounts_table()
            # Use translator for status message
            self.status_bar.showMessage(self.translator.tr("status_vault_loaded", len(self.vault_data["accounts"])), 5000)
            return True # Signal success

        except FileNotFoundError:
             print("Vault file disappeared unexpectedly during load.")
             self.vault_data = {"accounts": []}
             self.populate_accounts_table()
             return False # Indicate load failed
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr("error_title"),
                                 f"{self.translator.tr('error_load_vault')}\n{e}")
            self.vault_data = {"accounts": []}
            self.populate_accounts_table()
            return False # Indicate load failed

    def save_vault(self):
        """Encrypts and saves the current vault data using the master password string."""
        if not self.master_key_string:
            QMessageBox.critical(self, self.translator.tr("error_title"), self.translator.tr("error_save_nokey"))
            return False

        ensure_dir(VAULT_DIR)
        # Use the master password string to encrypt
        encrypted_blob = encrypt_vault(self.vault_data, self.master_key_string)

        if encrypted_blob:
            try:
                # Write atomically (optional but safer)
                temp_file = VAULT_FILE + ".tmp"
                with open(temp_file, 'wb') as f:
                    f.write(encrypted_blob)
                os.replace(temp_file, VAULT_FILE) # Atomic replace
                print("Vault saved successfully.")
                self.status_bar.showMessage(self.translator.tr("status_vault_saved"), 3000)
                return True
            except IOError as e:
                QMessageBox.critical(self, self.translator.tr("error_title"),
                                     f"{self.translator.tr('error_save_vault')}\n{e}")
                if os.path.exists(temp_file):
                    os.remove(temp_file) # Clean up temp file on error
                return False
            except Exception as e: # Catch other potential errors like os.replace issues
                 QMessageBox.critical(self, self.translator.tr("error_title"),
                                     f"{self.translator.tr('error_save_vault')}\n{e}")
                 if os.path.exists(temp_file):
                    os.remove(temp_file)
                 return False
        else:
             QMessageBox.critical(self, self.translator.tr("error_title"),
                                  self.translator.tr("error_encryption_failed"))
             return False

    # populate_accounts_table, filter_accounts, get_selected_account_id, get_account_by_id remain mostly the same
    def populate_accounts_table(self, filter_text=""):
        """Fills the table with account data, optionally filtering."""
        self.accounts_table.setSortingEnabled(False) # Disable sorting during population
        self.accounts_table.setRowCount(0) # Clear existing rows

        filter_text = filter_text.lower().strip()
        accounts_to_display = []

        # Ensure vault_data and accounts list exist
        if isinstance(self.vault_data, dict) and isinstance(self.vault_data.get("accounts"), list):
            current_accounts = self.vault_data["accounts"]
        else:
            current_accounts = []
            print("Warning: vault_data or accounts list is invalid during populate.")


        if filter_text:
            for account in current_accounts:
                # Check site, username, and notes for the filter text
                site_match = filter_text in account.get("site", "").lower()
                user_match = filter_text in account.get("username", "").lower()
                notes_match = filter_text in account.get("notes", "").lower()
                if site_match or user_match or notes_match:
                    accounts_to_display.append(account)
        else:
            accounts_to_display = current_accounts

        # Sort accounts by site name (case-insensitive) before displaying
        # Handle potential missing 'site' key gracefully
        accounts_to_display.sort(key=lambda x: x.get("site", "").lower())


        for account in accounts_to_display:
            row_position = self.accounts_table.rowCount()
            self.accounts_table.insertRow(row_position)

            # Handle potential missing keys when creating items
            site_item = QTableWidgetItem(account.get("site", ""))
            username_item = QTableWidgetItem(account.get("username", ""))
            notes_item = QTableWidgetItem(account.get("notes", ""))

            # Store the unique account ID in the first column's item data
            account_id = account.get("id")
            if account_id:
                 site_item.setData(Qt.UserRole, account_id)
            else:
                 # Fallback or warning if ID is missing (should not happen with new ID generation)
                 print(f"Warning: Account missing ID: {account.get('site')}")


            self.accounts_table.setItem(row_position, 0, site_item)
            self.accounts_table.setItem(row_position, 1, username_item)
            self.accounts_table.setItem(row_position, 2, notes_item)

        self.accounts_table.setSortingEnabled(True) # Re-enable sorting
        self.update_button_states() # Update buttons after populating

    def filter_accounts(self):
        """Filters the displayed accounts based on search input."""
        filter_text = self.search_input.text()
        self.populate_accounts_table(filter_text)

    def get_selected_account_id(self):
        """Returns the ID of the selected account, or None."""
        selected_rows = self.accounts_table.selectionModel().selectedRows()
        if selected_rows:
            # Get the item from the first column of the first selected row
            first_item = self.accounts_table.item(selected_rows[0].row(), 0)
            if first_item:
                # Retrieve the stored ID
                return first_item.data(Qt.UserRole)
        return None

    def get_account_by_id(self, account_id):
        """Finds an account dictionary in vault_data by its ID."""
        if not account_id or not isinstance(self.vault_data.get("accounts"), list):
             return None
        for account in self.vault_data["accounts"]:
            if account.get("id") == account_id:
                return account
        return None

    # update_button_states remains the same
    def update_button_states(self):
        """Enables/disables buttons and actions based on selection."""
        has_selection = bool(self.get_selected_account_id())
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.copy_button.setEnabled(has_selection)
        # Also update actions
        self.edit_act.setEnabled(has_selection)
        self.delete_act.setEnabled(has_selection)
        self.copy_act.setEnabled(has_selection)


    # add_account, edit_selected_account, delete_selected_account use save_vault() which now handles encryption correctly
    def add_account(self):
        """Opens the dialog to add a new account."""
        new_data = AccountDialog.show_dialog(self.translator, parent=self)
        if new_data:
            # Check for duplicates before adding
            exists = any(a.get('site', '').lower() == new_data['site'].lower() and \
                         a.get('username', '').lower() == new_data['username'].lower()
                         for a in self.vault_data.get("accounts", []))
            if exists:
                QMessageBox.warning(self, self.translator.tr("warning_title"),
                                    self.translator.tr("warning_account_exists"))
                return # Don't add duplicate

            # Ensure 'accounts' list exists and is a list
            if not isinstance(self.vault_data.get("accounts"), list):
                 self.vault_data["accounts"] = []

            self.vault_data["accounts"].append(new_data)
            if self.save_vault():
                # Find the newly added item and select it (optional)
                new_row_index = -1
                for row in range(self.accounts_table.rowCount()):
                    item = self.accounts_table.item(row, 0)
                    if item and item.data(Qt.UserRole) == new_data['id']:
                        new_row_index = row
                        break
                if new_row_index >= 0:
                    self.accounts_table.selectRow(new_row_index)

                # Repopulate with filter applied OR just add row if no filter?
                # Repopulating ensures sorting is correct after add.
                current_filter = self.search_input.text()
                self.populate_accounts_table(current_filter)
                 # Reselect if filter didn't hide it
                if new_row_index >= 0 and (not current_filter or new_data['id'] in [self.accounts_table.item(r,0).data(Qt.UserRole) for r in range(self.accounts_table.rowCount())]):
                     # Need to find row again after repopulation
                     for row in range(self.accounts_table.rowCount()):
                         item = self.accounts_table.item(row, 0)
                         if item and item.data(Qt.UserRole) == new_data['id']:
                             self.accounts_table.selectRow(row)
                             break
                self.status_bar.showMessage(self.translator.tr("status_account_added", new_data['site']), 3000)

            else:
                # Remove the added account if save failed
                self.vault_data["accounts"].pop() # Remove last added
                QMessageBox.critical(self, self.translator.tr("error_title"),
                                     self.translator.tr("error_add_failed"))

    def edit_selected_account(self):
        """Opens the dialog to edit the selected account."""
        selected_id = self.get_selected_account_id()
        if not selected_id:
            return

        account_to_edit = self.get_account_by_id(selected_id)
        if not account_to_edit:
             QMessageBox.warning(self, self.translator.tr("warning_title"), self.translator.tr("warning_account_notfound"))
             # Maybe refresh list if account disappeared?
             self.populate_accounts_table(self.search_input.text())
             return

        # Keep original data in case save fails
        original_account_copy = account_to_edit.copy()

        # Pass a copy to the dialog
        updated_data = AccountDialog.show_dialog(self.translator, account_data=account_to_edit.copy(), parent=self)

        if updated_data:
            # Find the index of the original account
            try:
                index_to_update = next(i for i, acc in enumerate(self.vault_data["accounts"]) if acc.get("id") == selected_id)

                # Update the account in the list
                self.vault_data["accounts"][index_to_update] = updated_data

                if self.save_vault():
                    # Repopulate table and try to maintain selection
                    current_filter = self.search_input.text()
                    self.populate_accounts_table(current_filter)
                    # Reselect based on ID
                    for row in range(self.accounts_table.rowCount()):
                         item = self.accounts_table.item(row, 0)
                         if item and item.data(Qt.UserRole) == selected_id:
                             self.accounts_table.selectRow(row)
                             break
                    self.status_bar.showMessage(self.translator.tr("status_account_updated", updated_data['site']), 3000)
                else:
                     # Revert change if save failed
                     print("Save failed after edit, reverting change in memory.")
                     self.vault_data["accounts"][index_to_update] = original_account_copy
                     # Maybe repopulate to show original state?
                     self.populate_accounts_table(self.search_input.text())
                     QMessageBox.critical(self, self.translator.tr("error_title"),
                                          self.translator.tr("error_update_failed"))
            except StopIteration:
                 # Account disappeared between selection and update?
                 QMessageBox.warning(self, self.translator.tr("warning_title"), self.translator.tr("warning_account_notfound"))
                 self.populate_accounts_table(self.search_input.text())


    def delete_selected_account(self):
        """Deletes the selected account after confirmation."""
        selected_id = self.get_selected_account_id()
        if not selected_id:
            return

        account_to_delete = self.get_account_by_id(selected_id)
        if not account_to_delete:
             # Should not happen if ID is valid and list hasn't changed async
             QMessageBox.warning(self, self.translator.tr("warning_title"), self.translator.tr("warning_account_notfound"))
             self.populate_accounts_table(self.search_input.text())
             return

        site_name = account_to_delete.get('site', self.translator.tr("unknown_site")) # Default name

        reply = QMessageBox.question(self, self.translator.tr("confirm_delete_title"),
                                     self.translator.tr("confirm_delete_message", site_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            original_accounts = list(self.vault_data["accounts"]) # Keep a copy for rollback
            # Filter out the account to delete
            self.vault_data["accounts"] = [acc for acc in self.vault_data["accounts"] if acc.get("id") != selected_id]

            if self.save_vault():
                self.populate_accounts_table(self.search_input.text()) # Repopulate table
                self.status_bar.showMessage(self.translator.tr("status_account_deleted", site_name), 3000)
            else:
                 # Revert if save failed
                 print("Save failed after delete, reverting change in memory.")
                 self.vault_data["accounts"] = original_accounts
                 self.populate_accounts_table(self.search_input.text()) # Show original state
                 QMessageBox.critical(self, self.translator.tr("error_title"),
                                      self.translator.tr("error_delete_failed"))

    # copy_selected_password remains the same
    def copy_selected_password(self):
        """Copies the password of the selected account to the clipboard."""
        selected_id = self.get_selected_account_id()
        if not selected_id:
            return

        account = self.get_account_by_id(selected_id)
        if account and "password" in account:
            password = account["password"]
            try:
                self._clipboard.setText(password)
                site_name = account.get('site', self.translator.tr("unknown_site"))
                self.status_bar.showMessage(self.translator.tr("status_password_copied", site_name), 3000)
                 # Optional: Clear clipboard after a delay (requires QTimer)
                # from PyQt5.QtCore import QTimer
                # QTimer.singleShot(30000, lambda pwd=password: self.clear_clipboard_if_matches(pwd))
            except Exception as e:
                 # Handle potential clipboard errors (e.g., on headless systems)
                 print(f"Clipboard Error: {e}")
                 QMessageBox.warning(self, self.translator.tr("error_title"), self.translator.tr("error_clipboard_copy"))

        else:
             QMessageBox.warning(self, self.translator.tr("warning_title"), self.translator.tr("warning_password_notfound"))

    # def clear_clipboard_if_matches(self, expected_password):
    #     """Clears the clipboard only if it still contains the copied password."""
    #     try:
    #         if self._clipboard.text() == expected_password:
    #             self._clipboard.clear()
    #             print("Clipboard cleared automatically.")
    #             self.status_bar.showMessage(self.translator.tr("status_clipboard_cleared"), 2000)
    #     except Exception as e:
    #         print(f"Clipboard clear error: {e}")


    # open_settings remains the same
    def open_settings(self):
        """Opens the settings dialog."""
        available_langs = self.translator.get_available_languages()
        settings_dialog = SettingsDialog(self.translator, self.settings_manager, available_langs, self)
        if settings_dialog.exec_() == QDialog.Accepted:
            changes = settings_dialog.get_changes()
            if changes["theme_changed"] or changes["font_changed"] or changes["language_changed"]:
                # Apply font and theme immediately
                if changes["theme_changed"] or changes["font_changed"]:
                     self.apply_app_settings()
                # Language change requires retranslating the UI
                if changes["language_changed"]:
                    current_lang = self.settings_manager.get("language", DEFAULT_LANG)
                    self.translator.load_language(current_lang)
                    self.retranslate_ui() # Update UI texts
                    # Apply layout direction change immediately
                    if current_lang == 'ar':
                        QApplication.instance().setLayoutDirection(Qt.RightToLeft)
                    else:
                         QApplication.instance().setLayoutDirection(Qt.LeftToRight)


                self.status_bar.showMessage(self.translator.tr("status_settings_applied"), 3000)

    # apply_app_settings remains the same
    def apply_app_settings(self):
        """Applies theme and font settings globally."""
        app = QApplication.instance()
        # Apply theme
        current_theme = self.settings_manager.get("theme", DEFAULT_THEME)
        apply_theme(app, current_theme)

        # Apply font
        font_family = self.settings_manager.get("font_family", DEFAULT_FONT_FAMILY)
        font_size = self.settings_manager.get("font_size", DEFAULT_FONT_SIZE)
        app.setFont(QFont(font_family, font_size))

        # Re-apply font to main window itself and children after global change
        self.setFont(app.font())
        # Force style update on existing widgets
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


    # retranslate_ui needs updates for menu items etc.
    def retranslate_ui(self):
        """Manually update texts of UI elements after language change."""
        self.setWindowTitle(APP_NAME)
        self.search_label.setText(self.translator.tr("search_label"))
        self.search_input.setPlaceholderText(self.translator.tr("search_placeholder"))
        self.accounts_table.setHorizontalHeaderLabels([
            self.translator.tr("header_site"),
            self.translator.tr("header_username"),
            self.translator.tr("header_notes")
        ])
        self.add_button.setText(self.translator.tr("add_button"))
        self.edit_button.setText(self.translator.tr("edit_button"))
        self.delete_button.setText(self.translator.tr("delete_button"))
        self.copy_button.setText(self.translator.tr("copy_password_button"))

        # Retranslate Actions (Tooltips, StatusTips, and Text)
        self.add_act.setText(self.translator.tr("add_action_tooltip"))
        self.add_act.setToolTip(self.translator.tr("add_action_tooltip"))
        self.add_act.setStatusTip(self.translator.tr("add_action_statustip"))

        self.edit_act.setText(self.translator.tr("edit_action_tooltip"))
        self.edit_act.setToolTip(self.translator.tr("edit_action_tooltip"))
        self.edit_act.setStatusTip(self.translator.tr("edit_action_statustip"))

        self.delete_act.setText(self.translator.tr("delete_action_tooltip"))
        self.delete_act.setToolTip(self.translator.tr("delete_action_tooltip"))
        self.delete_act.setStatusTip(self.translator.tr("delete_action_statustip"))

        self.copy_act.setText(self.translator.tr("copy_action_tooltip"))
        self.copy_act.setToolTip(self.translator.tr("copy_action_tooltip"))
        self.copy_act.setStatusTip(self.translator.tr("copy_action_statustip"))

        self.settings_act.setText(self.translator.tr("settings_action_tooltip"))
        self.settings_act.setToolTip(self.translator.tr("settings_action_tooltip"))
        self.settings_act.setStatusTip(self.translator.tr("settings_action_statustip"))

        self.lock_act.setText(self.translator.tr("lock_action_tooltip"))
        self.lock_act.setToolTip(self.translator.tr("lock_action_tooltip"))
        self.lock_act.setStatusTip(self.translator.tr("lock_action_statustip"))

        self.exit_act.setText(self.translator.tr("exit_action_tooltip"))
        self.exit_act.setToolTip(self.translator.tr("exit_action_tooltip"))
        self.exit_act.setStatusTip(self.translator.tr("exit_action_statustip"))

        self.about_act.setText(self.translator.tr("about_action_tooltip")) # Text for menu item
        self.about_act.setToolTip(self.translator.tr("about_action_tooltip"))
        self.about_act.setStatusTip(self.translator.tr("about_action_statustip"))

        # Retranslate Menus
        self.file_menu.setTitle(self.translator.tr("menu_file"))
        self.edit_menu.setTitle(self.translator.tr("menu_edit"))
        self.help_menu.setTitle(self.translator.tr("menu_help"))

        # Retranslate Toolbar Title
        self.toolbar.setWindowTitle(self.translator.tr("main_toolbar_title"))

        # Retranslate Status Bar initial message (if desired)
        self.status_bar.showMessage(self.translator.tr("status_ready"))

        # Update layout direction for the window and menubar specifically
        direction = Qt.RightToLeft if self.translator.locale == 'ar' else Qt.LeftToRight
        self.setLayoutDirection(direction)
        if hasattr(self, 'menu_bar'): # Ensure menubar exists
             self.menu_bar.setLayoutDirection(direction)


    # lock_vault remains the same
    def lock_vault(self):
        """Locks the vault, requiring re-login."""
        print("Locking vault...")
        self.master_key_string = None # Clear the stored master password string
        self.vault_data = {"accounts": []} # Clear decrypted data from memory
        self.populate_accounts_table() # Clear the table
        self.update_button_states()
        self.status_bar.showMessage(self.translator.tr("status_vault_locked"))
        self.hide() # Hide the main window

        # The main application loop in MindVaultApp will handle showing login again
        # We just need to close this window instance.
        self.close()


    # show_about_dialog remains the same
    def show_about_dialog(self):
        """Displays a simple About dialog."""
        QMessageBox.about(self,
                          self.translator.tr("about_title"),
                          f"<b>{APP_NAME}</b> v{APP_VERSION}<br><br>"
                          f"{self.translator.tr('about_text')}<br><br>"
                          f"Using Python & PyQt5<br>"
                          f"Cryptography via 'cryptography' library.")

    # closeEvent remains the same
    def closeEvent(self, event):
        """Handle window close event."""
        # Optional: Add confirmation before closing if needed
        # reply = QMessageBox.question(self, 'Confirm Exit', 'Are you sure you want to exit?',
        #                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        # if reply == QMessageBox.Yes:
        #     event.accept()
        # else:
        #     event.ignore()
        print("Closing MindVault.")
        # Vault is saved after every change, so no explicit save needed here.
        # Clear sensitive data just in case? (master_key_string is cleared on lock/close anyway)
        self.master_key_string = None
        self.vault_data = {}
        event.accept()


# --- Main Application Class (Controller) ---
# Needs updates for new encryption flow and language file creation
class MindVaultApp:
    def __init__(self, argv):
        self.app = QApplication(argv)
        # Set Application info for better integration (optional)
        self.app.setApplicationName(APP_NAME)
        self.app.setApplicationVersion(APP_VERSION)
        self.app.setOrganizationName("SARA") # Replace or remove

        self.settings_manager = SettingsManager(SETTINGS_FILE)
        
        icon_file_name = "app_icon.png"  # أو "app_icon.png"
        # يمكنك وضعه في مجلد icons أيضاً:
        # icon_path = os.path.join("icons", icon_file_name)
        icon_path = icon_file_name # إذا كان في المجلد الرئيسي

        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            self.app.setWindowIcon(app_icon)
            print(f"Application icon set from: {icon_path}") # رسالة تأكيد (اختياري)
        else:
            # رسالة تحذير إذا لم يتم العثور على الملف
            print(f"Warning: Application icon file not found at '{icon_path}'. Using default icon.")
        
        # --- Language Setup ---
        # Ensure language files exist *before* loading initial language
        self.create_default_lang_files()
        initial_lang = self.settings_manager.get("language", DEFAULT_LANG)
        self.translator = TranslationHandler(self.app, initial_lang)

        # --- Apply Initial Settings ---
        self.apply_initial_settings()

        self.main_window = None
        self.master_password_string = None # Store the password string

    def create_default_lang_files(self):
        """Creates default English and Arabic JSON files if they don't exist."""
        ensure_dir(LANG_DIR)
        lang_files_content = {
            "en.json": {
                # --- General ---
                "_lang_name_": "English",
                "ok_button": "OK",
                "cancel_button": "Cancel",
                "error_title": "Error",
                "warning_title": "Warning",
                "info_title": "Information",
                "unknown_site": "Unknown Site",
                "error_clipboard_copy": "Could not copy to clipboard.",
                 # --- Setup ---
                "setup_title": "MindVault Setup",
                "setup_welcome": "Welcome to MindVault!",
                "setup_instruction": "Please create a strong Master Password. This password encrypts your vault and is the ONLY way to access your stored passwords. FORGETTING IT MEANS LOSING ACCESS PERMANENTLY.",
                "master_password_label": "Master Password:",
                "confirm_password_label": "Confirm Password:",
                "master_password_placeholder": "Enter master password (min {0} chars)",
                "confirm_password_placeholder": "Enter password again",
                "password_strength_label": "Password Strength:",
                "password_strength_weak": "Weak",
                "password_strength_medium": "Medium",
                "password_strength_strong": "Strong",
                "create_button": "Create Vault",
                "error_password_empty": "Master Password cannot be empty.",
                "error_password_mismatch": "Passwords do not match.",
                "error_password_short": "Password must be at least {0} characters long.",
                "warning_password_weak": "Password strength is weak. Are you sure you want to use it?",
                 # --- Login ---
                "login_title": "Login",
                "login_prompt": "Enter your Master Password to unlock the vault:",
                "login_button": "Unlock",
                "exit_button": "Exit",
                "login_error_incorrect": "Incorrect Master Password or corrupted vault.",
                 # --- Main Window ---
                "search_placeholder": "Search Site, Username, or Notes...",
                "search_label": "Search:",
                "header_site": "Site / Service",
                "header_username": "Username",
                "header_notes": "Notes",
                "add_button": "Add New",
                "edit_button": "Edit",
                "delete_button": "Delete",
                "copy_password_button": "Copy Password",
                "status_ready": "Ready.",
                "status_vault_loaded": "Vault loaded successfully ({0} accounts).",
                "status_vault_saved": "Vault saved.",
                "status_account_added": "Account '{0}' added.",
                "status_account_updated": "Account '{0}' updated.",
                "status_account_deleted": "Account '{0}' deleted.",
                "status_password_copied": "Password for '{0}' copied to clipboard.",
                "status_clipboard_cleared": "Clipboard cleared.",
                "status_vault_locked": "Vault locked.",
                "status_settings_applied": "Settings applied.",
                "confirm_delete_title": "Confirm Deletion",
                "confirm_delete_message": "Are you sure you want to delete the account for '{0}'?",
                "error_load_vault": "Failed to load or decrypt the vault file.",
                "error_save_vault": "Failed to save the vault file.",
                "error_save_nokey": "Cannot save vault: Master key is not available.",
                "error_encryption_failed": "Encryption failed. Vault not saved.",
                "error_add_failed": "Failed to save after adding account.",
                "error_update_failed": "Failed to save after updating account.",
                "error_delete_failed": "Failed to save after deleting account.",
                "warning_account_exists": "An account with this Site and Username already exists.",
                "warning_account_notfound": "Selected account could not be found (it may have been deleted or modified).",
                "warning_password_notfound": "Password data not found for the selected account.",
                 # --- Account Dialog ---
                 "add_edit_account_title": "Account Details",
                 "site_name_label": "Site/Service Name:",
                 "username_label": "Username/Email:",
                 "password_label": "Password:",
                 "notes_label": "Notes (Optional):",
                 "show_password": "Show",
                 "hide_password": "Hide",
                 "input_error_title": "Input Error",
                 "input_error_message": "Site Name, Username, and Password cannot be empty.",
                 # --- Settings Dialog ---
                 "settings_title": "Settings",
                 "language_label": "Language:",
                 "theme_label": "Theme:",
                 "font_label": "Application Font:",
                 "select_font_button": "Choose Font...",
                 "select_font_dialog_title": "Select Application Font",
                 "theme_light": "Light",
                 "theme_dark": "Dark",
                 "language_change_message": "Some language changes may require an application restart to take full effect.", # Adjusted message
                 # --- Actions / Menus / Toolbar / Statusbar ---
                 "menu_file": "&File",
                 "menu_edit": "&Edit",
                 "menu_help": "&Help",
                 "add_action_tooltip": "Add New Account",
                 "add_action_statustip": "Create a new password entry",
                 "edit_action_tooltip": "Edit Selected Account",
                 "edit_action_statustip": "Modify the selected password entry",
                 "delete_action_tooltip": "Delete Selected Account",
                 "delete_action_statustip": "Remove the selected password entry",
                 "copy_action_tooltip": "Copy Password",
                 "copy_action_statustip": "Copy the selected account's password to the clipboard",
                 "settings_action_tooltip": "Settings",
                 "settings_action_statustip": "Change application settings (Language, Theme, Font)",
                 "lock_action_tooltip": "Lock Vault",
                 "lock_action_statustip": "Lock the vault and require password entry",
                 "exit_action_tooltip": "Exit",
                 "exit_action_statustip": "Exit the application",
                 "about_action_tooltip": "About MindVault",
                 "about_action_statustip": "Show information about the application",
                 "main_toolbar_title": "Main Toolbar",
                 "about_title": "About MindVault",
                 "about_text": "A secure, offline password manager."
            },
            "ar.json": {
                # --- General ---
                "_lang_name_": "العربية",
                "ok_button": "موافق",
                "cancel_button": "إلغاء",
                "error_title": "خطأ",
                "warning_title": "تحذير",
                "info_title": "معلومات",
                "unknown_site": "موقع غير معروف",
                "error_clipboard_copy": "لم نتمكن من النسخ إلى الحافظة.",
                 # --- Setup ---
                "setup_title": "إعداد MindVault",
                "setup_welcome": "مرحباً بك في MindVault!",
                "setup_instruction": "يرجى إنشاء كلمة مرور رئيسية قوية. هذه الكلمة تُستخدم لتشفير خزنتك وهي الطريقة الوحيدة للوصول لكلمات مرورك المحفوظة. نسيانها يعني فقدان الوصول نهائياً.",
                "master_password_label": "كلمة المرور الرئيسية:",
                "confirm_password_label": "تأكيد كلمة المرور:",
                "master_password_placeholder": "أدخل كلمة المرور (أقل شيء {0} حروف)",
                "confirm_password_placeholder": "أدخل كلمة المرور مرة أخرى",
                "password_strength_label": "قوة كلمة المرور:",
                "password_strength_weak": "ضعيفة",
                "password_strength_medium": "متوسطة",
                "password_strength_strong": "قوية",
                "create_button": "إنشاء الخزنة",
                "error_password_empty": "لا يمكن ترك كلمة المرور الرئيسية فارغة.",
                "error_password_mismatch": "كلمتا المرور غير متطابقتين.",
                "error_password_short": "يجب أن تتكون كلمة المرور من {0} أحرف على الأقل.",
                "warning_password_weak": "قوة كلمة المرور ضعيفة. هل أنت متأكد من استخدامها؟",
                 # --- Login ---
                "login_title": "تسجيل الدخول",
                "login_prompt": "أدخل كلمة المرور الرئيسية لفتح الخزنة:",
                "login_button": "فتح",
                "exit_button": "خروج",
                "login_error_incorrect": "كلمة المرور الرئيسية غير صحيحة أو الخزنة تالفة.",
                 # --- Main Window ---
                "search_placeholder": "ابحث عن موقع، اسم مستخدم، أو ملاحظات...",
                "search_label": "بحث:",
                "header_site": "الموقع / الخدمة",
                "header_username": "اسم المستخدم",
                "header_notes": "ملاحظات",
                "add_button": "إضافة جديد",
                "edit_button": "تعديل",
                "delete_button": "حذف",
                "copy_password_button": "نسخ كلمة المرور",
                "status_ready": "جاهز.",
                "status_vault_loaded": "تم تحميل الخزنة بنجاح ({0} حسابات).",
                "status_vault_saved": "تم حفظ الخزنة.",
                "status_account_added": "تمت إضافة الحساب '{0}'.",
                "status_account_updated": "تم تحديث الحساب '{0}'.",
                "status_account_deleted": "تم حذف الحساب '{0}'.",
                "status_password_copied": "تم نسخ كلمة مرور '{0}' إلى الحافظة.",
                "status_clipboard_cleared": "تم مسح الحافظة.",
                "status_vault_locked": "تم قفل الخزنة.",
                "status_settings_applied": "تم تطبيق الإعدادات.",
                "confirm_delete_title": "تأكيد الحذف",
                "confirm_delete_message": "هل أنت متأكد من حذف الحساب الخاص بـ '{0}'؟",
                "error_load_vault": "فشل تحميل أو فك تشفير ملف الخزنة.",
                "error_save_vault": "فشل حفظ ملف الخزنة.",
                "error_save_nokey": "لا يمكن حفظ الخزنة: المفتاح الرئيسي غير متوفر.",
                "error_encryption_failed": "فشل التشفير. لم يتم حفظ الخزنة.",
                "error_add_failed": "فشل الحفظ بعد إضافة الحساب.",
                "error_update_failed": "فشل الحفظ بعد تحديث الحساب.",
                "error_delete_failed": "فشل الحفظ بعد حذف الحساب.",
                "warning_account_exists": "يوجد حساب بنفس الموقع واسم المستخدم بالفعل.",
                "warning_account_notfound": "لم يتم العثور على الحساب المحدد (ربما تم حذفه أو تعديله).",
                "warning_password_notfound": "بيانات كلمة المرور غير موجودة للحساب المحدد.",
                 # --- Account Dialog ---
                 "add_edit_account_title": "تفاصيل الحساب",
                 "site_name_label": "اسم الموقع/الخدمة:",
                 "username_label": "اسم المستخدم/البريد:",
                 "password_label": "كلمة المرور:",
                 "notes_label": "ملاحظات (اختياري):",
                 "show_password": "إظهار",
                 "hide_password": "إخفاء",
                 "input_error_title": "خطأ إدخال",
                 "input_error_message": "اسم الموقع، اسم المستخدم، وكلمة المرور لا يمكن تركها فارغة.",
                 # --- Settings Dialog ---
                 "settings_title": "الإعدادات",
                 "language_label": "اللغة:",
                 "theme_label": "السمة (Theme):",
                 "font_label": "خط التطبيق:",
                 "select_font_button": "اختر الخط...",
                 "select_font_dialog_title": "اختر خط التطبيق",
                 "theme_light": "فاتح",
                 "theme_dark": "داكن",
                 "language_change_message": "قد تتطلب بعض تغييرات اللغة إعادة تشغيل التطبيق لتصبح فعالة بالكامل.", # رسالة معدلة
                 # --- Actions / Menus / Toolbar / Statusbar ---
                 "menu_file": "&ملف",
                 "menu_edit": "&تحرير",
                 "menu_help": "&مساعدة",
                 "add_action_tooltip": "إضافة حساب جديد",
                 "add_action_statustip": "إنشاء إدخال كلمة مرور جديدة",
                 "edit_action_tooltip": "تعديل الحساب المحدد",
                 "edit_action_statustip": "تعديل إدخال كلمة المرور المحددة",
                 "delete_action_tooltip": "حذف الحساب المحدد",
                 "delete_action_statustip": "إزالة إدخال كلمة المرور المحددة",
                 "copy_action_tooltip": "نسخ كلمة المرور",
                 "copy_action_statustip": "نسخ كلمة مرور الحساب المحدد إلى الحافظة",
                 "settings_action_tooltip": "الإعدادات",
                 "settings_action_statustip": "تغيير إعدادات التطبيق (اللغة، السمة، الخط)",
                 "lock_action_tooltip": "قفل الخزنة",
                 "lock_action_statustip": "قفل الخزنة وطلب كلمة المرور للدخول",
                 "exit_action_tooltip": "خروج",
                 "exit_action_statustip": "الخروج من التطبيق",
                 "about_action_tooltip": "حول MindVault",
                 "about_action_statustip": "إظهار معلومات حول التطبيق",
                 "main_toolbar_title": "شريط الأدوات الرئيسي",
                 "about_title": "حول MindVault",
                 "about_text": "مدير كلمات مرور آمن يعمل دون اتصال بالإنترنت."
            }
        }
        for filename, content in lang_files_content.items():
            filepath = os.path.join(LANG_DIR, filename)
            if not os.path.exists(filepath):
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(content, f, indent=4, ensure_ascii=False, sort_keys=True) # Sort keys for consistency
                    print(f"Created default language file: {filename}")
                except IOError as e:
                    print(f"Error creating language file {filename}: {e}")

    # apply_initial_settings remains the same
    def apply_initial_settings(self):
        """Applies theme and font from settings at startup."""
        current_theme = self.settings_manager.get("theme", DEFAULT_THEME)
        apply_theme(self.app, current_theme)

        font_family = self.settings_manager.get("font_family", DEFAULT_FONT_FAMILY)
        font_size = self.settings_manager.get("font_size", DEFAULT_FONT_SIZE)
        self.app.setFont(QFont(font_family, font_size))

        # Apply layout direction based on initial language setting
        initial_lang = self.settings_manager.get("language", DEFAULT_LANG)
        if initial_lang == 'ar':
            self.app.setLayoutDirection(Qt.RightToLeft)
        else:
            self.app.setLayoutDirection(Qt.LeftToRight)


    # run method needs updates for new encryption flow
    def run(self):
        """Main application execution flow."""
        while True: # Loop to allow re-login after locking
            self.master_password_string = None # Reset password string for each attempt/lock cycle
            vault_exists = os.path.exists(VAULT_FILE)
            # Determine first run based on setting AND vault existence
            first_run = self.settings_manager.get("first_run", True) or not vault_exists

            if first_run:
                # --- First Run / Setup ---
                print("First run or vault not found. Starting setup...")
                setup_win = SetupWindow(self.translator)
                if setup_win.exec_() == QDialog.Accepted:
                    self.master_password_string = setup_win.get_master_password() # Get the string
                    # Create initial empty vault using the password string
                    ensure_dir(VAULT_DIR)
                    empty_vault = {"accounts": []}
                    # Use encrypt_vault with the password string
                    encrypted_blob = encrypt_vault(empty_vault, self.master_password_string)
                    if encrypted_blob:
                         try:
                             # Use atomic write for initial creation too
                             temp_file = VAULT_FILE + ".tmp"
                             with open(temp_file, 'wb') as f:
                                 f.write(encrypted_blob)
                             os.replace(temp_file, VAULT_FILE)
                             self.settings_manager.set("first_run", False) # Mark setup complete *after* successful save
                             print("Initial vault created successfully.")
                             # Proceed to login/main window phase
                         except (IOError, OSError) as e:
                              QMessageBox.critical(None, self.translator.tr("error_title"),
                                                   f"{self.translator.tr('error_save_vault')}\n{e}")
                              if os.path.exists(temp_file): os.remove(temp_file)
                              sys.exit(1) # Exit if initial vault creation fails
                    else:
                         QMessageBox.critical(None, self.translator.tr("error_title"),
                                             self.translator.tr("error_encryption_failed") + "\nVault setup failed.")
                         sys.exit(1)

                else:
                    # User cancelled setup
                    print("Setup cancelled by user.")
                    sys.exit(0) # Exit gracefully

            # --- Normal Login ---
            # This part runs if it's not the first run OR if first run setup was successful
            if not self.master_password_string: # If setup was just done, we have the password, otherwise, show login
                login_win = LoginWindow(self.translator)
                login_successful = False
                while True: # Loop for login attempts
                    if login_win.exec_() == QDialog.Accepted:
                        potential_password = login_win.get_master_password() # Get string
                        # Attempt to decrypt the vault using the entered password string
                        try:
                             if not os.path.exists(VAULT_FILE):
                                 # Vault disappeared after startup? Highly unlikely but handle it.
                                 login_win.show_error(self.translator.tr("error_load_vault") + "\nVault file not found.")
                                 continue # Ask for password again? Or exit?

                             with open(VAULT_FILE, 'rb') as f:
                                 encrypted_blob_test = f.read()

                             # Use decrypt_data with the password string
                             if decrypt_data(encrypted_blob_test, potential_password) is not None:
                                 self.master_password_string = potential_password # Store correct string
                                 login_successful = True
                                 break # Correct password, exit login loop
                             else:
                                 # Decrypt failed - wrong password or corruption
                                 login_win.show_error(self.translator.tr("login_error_incorrect"))
                                 # Stay in the loop to allow another attempt

                        except Exception as e:
                             # Handle file read errors or other unexpected issues during test
                             login_win.show_error(f"{self.translator.tr('error_load_vault')}\n{e}")
                             # Stay in the loop or break? Let's stay for another attempt.
                    else:
                        # User cancelled the login dialog
                        print("Login cancelled by user.")
                        sys.exit(0) # Exit gracefully

                if not login_successful:
                     # Should not be reachable if cancel exits, but as safeguard
                     print("Login failed after multiple attempts.")
                     sys.exit(1)


            # --- Show Main Window ---
            if self.master_password_string:
                # Create and show the main window instance
                # Pass translator and settings manager
                self.main_window = MainWindow(self.translator, self.settings_manager)

                # Apply current settings (theme, font) to the new window instance
                self.main_window.apply_app_settings()
                # Retranslate UI elements in the new window instance
                self.main_window.retranslate_ui()

                # Load the vault using the confirmed master password string
                if self.main_window.load_vault(self.master_password_string):
                    self.main_window.show()
                    exit_code = self.app.exec_() # Start event loop

                    # Check if the window still exists after exec_() finishes
                    # If main_window is None or not visible, it means lock_vault was likely called,
                    # or the window was closed normally.
                    if self.main_window is None or not self.main_window.isVisible():
                        # If it was locked, the master_password_string is cleared,
                        # the while loop will restart and show the login window again.
                        # If closed normally, sys.exit() will be called below.
                        print("Main window closed or locked.")
                        # Check if we need to restart the loop (locked) or exit (closed)
                        # If master_password_string is None, it was likely locked.
                        if self.master_password_string is None:
                              print("Restarting login process...")
                              continue # Go back to the start of the while loop for login
                        else:
                              # Window closed normally, exit the loop and application
                              print("Exiting application.")
                              sys.exit(exit_code)

                else:
                    # Vault loading failed even after successful password test (corruption?)
                    QMessageBox.critical(None, self.translator.tr("error_title"),
                                         self.translator.tr("error_load_vault") + "\n" +
                                         self.translator.tr("login_error_incorrect"))
                    # Loop back to login after critical error? Or exit?
                    # Looping back might be confusing if the file is truly corrupt. Let's exit.
                    print("Exiting due to critical vault load failure.")
                    sys.exit(1)
            else:
                # Should not happen if logic above is correct, but as a safeguard
                print("Exiting due to missing master password after login/setup phase.")
                sys.exit(1)


if __name__ == '__main__':
    # Create dummy icon files if they don't exist (replace with real icons)
    ensure_dir("icons")
    icon_files = ["add.png", "edit.png", "delete.png", "copy.png", "settings.png", "lock.png", "exit.png"]
    for icon in icon_files:
        icon_path = os.path.join("icons", icon)
        if not os.path.exists(icon_path):
             try:
                 # Create an empty file as placeholder if icon doesn't exist
                 with open(icon_path, 'w') as f:
                     pass # Create empty file
                 print(f"Created placeholder icon: {icon_path}")
             except Exception as e:
                 print(f"Could not create placeholder icon {icon_path}: {e}")

    # Run the application
    mind_vault = MindVaultApp(sys.argv)
    mind_vault.run()