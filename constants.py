import os

APP_NAME = "MindVault"
APP_VERSION = "2.0"
SETTINGS_FILE = "settings.json" # This will be at the root, relative to where main.py is run
VAULT_DIR_NAME = "data" # Directory name, not full path
VAULT_DIR = os.path.abspath(VAULT_DIR_NAME) # Store absolute path for robustness
VAULT_FILE_NAME = "vault.enc"
VAULT_FILE = os.path.join(VAULT_DIR, VAULT_FILE_NAME)

LANG_DIR_NAME = "lang" # Directory name for languages inside the package
# LANG_DIR will be calculated in translation.py relative to its own path
# or passed as an absolute path from main.py if needed.
# For simplicity in generate_structure.py, we'll assume it's managed by TranslationHandler
# and it might be better if TranslationHandler expects a path relative to the main script
# or an absolute path. Let's assume LANG_DIR will be in the root for now, as in original.
# If LANG_DIR is inside the package, paths will need adjustment.
# The original code implies LANG_DIR is at the root (where generate_structure.py runs)
# Let's make it relative to the package root for better packaging.
# No, the original code's `create_default_lang_files` expects LANG_DIR at CWD.
# Let's assume `lang` folder is at the project root, created by `main.py`.

DEFAULT_LANG = "ar"
DEFAULT_THEME = "light"
DEFAULT_FONT_FAMILY = "Tahoma"
DEFAULT_FONT_SIZE = 10
DEFAULT_AUTO_LOCK_TIMEOUT = 0

# PBKDF2 constants
PBKDF2_ITERATIONS = 390000
SALT_SIZE = 16
AES_NONCE_SIZE = 12
AES_TAG_SIZE = 16

# Path for icons, assuming "icons" folder is at the project root
# or relative to where the main script is executed.
# This can be tricky. If icons are part of the package, paths should be relative to package.
# For now, stick to original behavior (root-level "icons" folder).
ICONS_DIR = "icons" # Relative to execution directory
APP_ICON_PATH = "app_icon.png" # Relative to execution directory