import sys
import os
import json
import shutil # For creating placeholder icons

from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt # For Qt.RightToLeft etc.

# Application specific imports
# Assuming these modules are in the same directory or in PYTHONPATH
# For a structured project, they would be like: from .constants import ...
from constants import (
    APP_NAME, APP_VERSION, SETTINGS_FILE, VAULT_FILE, VAULT_DIR,
    LANG_DIR_NAME, DEFAULT_LANG, DEFAULT_THEME, DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE, ICONS_DIR, APP_ICON_PATH
)
from core.settings import SettingsManager
from core.translation import TranslationHandler
from core.crypto import encrypt_vault, decrypt_data # For setup and login
from core.utils import ensure_dir
from ui.main_window import MainWindow
from ui.dialogs import SetupWindow, LoginWindow # For setup and login
from ui.styles import apply_theme

# Feature imports for 2FA login flow
from features import (
    TwoFactorVerifyDialog,
    verify_totp_code,
    get_2fa_secret_from_vault # Used in login flow
)

# Define language files content (for create_default_lang_files)
DEFAULT_LANG_FILES_CONTENT = {
    "en.json": {
        "_lang_name_": "English",
        "app_title": APP_NAME,
        "ok_button": "OK",
        "cancel_button": "Cancel",
        "yes_button": "Yes",
        "no_button": "No",
        "add_button": "Add",
        "edit_button": "Edit",
        "delete_button": "Delete",
        "create_button": "Create",
        "login_button": "Login",
        "exit_button": "Exit",
        "settings_title": "Settings",
        "language_label": "Language:",
        "theme_label": "Theme:",
        "font_label": "Font:",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "select_font_button": "Select Font",
        "select_font_dialog_title": "Select Font",
        "auto_lock_settings_label": "Auto-lock vault after:",
        "auto_lock_disabled": "Disabled",
        "auto_lock_minutes_suffix": "{0} minutes",
        "status_ready": "Ready.",
        "status_vault_loaded": "Vault loaded. {0} accounts.",
        "status_vault_saved": "Vault saved.",
        "status_vault_locked": "Vault locked.",
        "status_settings_applied": "Settings applied.",
        "status_account_added": "Account '{0}' added.",
        "status_account_updated": "Account '{0}' updated.",
        "status_account_deleted": "Account '{0}' deleted.",
        "status_password_copied": "Password for '{0}' copied to clipboard.",
        "status_vault_restored_relogin": "Vault restored. Please log in again.",
        "search_label": "Search:",
        "search_placeholder": "Type to filter accounts...",
        "header_site": "Site/Service",
        "header_username": "Username/Email",
        "header_notes": "Notes",
        "copy_password_button": "Copy Password",
        "menu_file": "&File",
        "menu_edit": "&Edit",
        "menu_tools": "&Tools",
        "menu_help": "&Help",
        "add_action_tooltip": "Add new account",
        "edit_action_tooltip": "Edit selected account",
        "delete_action_tooltip": "Delete selected account",
        "copy_action_tooltip": "Copy password of selected account",
        "settings_action_tooltip": "Open settings",
        "lock_action_tooltip": "Lock vault",
        "exit_action_tooltip": "Exit application",
        "about_action_tooltip": "About " + APP_NAME,
        "backup_vault_menu": "Backup Vault...",
        "backup_vault_tooltip": "Backup the current vault",
        "restore_vault_menu": "Restore Vault...",
        "restore_vault_tooltip": "Restore vault from a backup",
        "check_duplicates_menu": "Check for Duplicate Passwords...",
        "check_duplicates_tooltip": "Find accounts using the same password",
        "main_toolbar_title": "Main Toolbar",
        "about_title": "About " + APP_NAME,
        "about_text": "A simple and secure password manager.",
        "error_title": "Error",
        "warning_title": "Warning",
        "info_title": "Information",
        "input_error_title": "Input Error",
        "input_error_message": "Site, username, and password cannot be empty.",
        "error_password_short": "Master password must be at least {0} characters long.",
        "error_password_mismatch": "Passwords do not match.",
        "warning_password_weak": "The chosen password is weak. Are you sure you want to use it?",
        "error_password_empty": "Password cannot be empty.",
        "login_title": "Login",
        "login_prompt": "Enter your master password to unlock the vault:",
        "master_password_label": "Master Password",
        "login_error_incorrect": "Incorrect master password or vault corrupted.",
        "setup_title": "MindVault Setup",
        "setup_welcome": "Welcome to MindVault!",
        "setup_instruction": "Please create a strong master password to secure your vault. This password will be required to access your stored accounts. Remember it well, as it cannot be recovered if lost.",
        "master_password_placeholder": "Minimum {0} characters",
        "confirm_password_placeholder": "Confirm master password",
        "confirm_password_label": "Confirm Master Password:",
        "password_strength_label": "Password Strength:",
        "password_strength_very_weak": "Very Weak",
        "password_strength_weak": "Weak",
        "password_strength_medium": "Medium",
        "password_strength_strong": "Strong",
        "password_strength_very_strong": "Very Strong",
        "error_load_vault": "Could not load vault.",
        "vault_file_not_found_detail": "Vault file not found. Please ensure it exists or setup the application again.",
        "error_save_vault": "Could not save vault.",
        "error_save_nokey": "Cannot save vault: Master key not set.",
        "error_encryption_failed": "Encryption failed. Vault not saved.",
        "error_encryption_failed_save": "Encryption failed during save. Vault not saved.",
        "error_decrypt_failed_critical": "Failed to decrypt vault. Data may be corrupted or password incorrect.",
        "unlock_vault_first": "Please unlock the vault first to use this feature.",
        "warning_account_notfound": "Selected account not found. It might have been deleted.",
        "warning_account_notfound_during_update": "Account to update not found. Refreshing list.",
        "error_add_failed": "Failed to add account. Vault not saved.",
        "error_update_failed": "Failed to update account. Vault not saved.",
        "error_delete_failed": "Failed to delete account. Vault not saved.",
        "confirm_delete_title": "Confirm Delete",
        "confirm_delete_message": "Are you sure you want to delete the account for '{0}'?",
        "unknown_site": "Unknown Site",
        "warning_password_notfound": "Password not found for this account.",
        "error_clipboard_copy": "Could not copy to clipboard.",
        "error_clipboard_unavailable": "Clipboard service is not available.",
        "language_change_message": "Language settings will apply after restarting the application or reopening settings.",
        "add_edit_account_title": "Add/Edit Account",
        "site_name_label": "Site/Service Name:",
        "username_label": "Username/Email:",
        "password_label": "Password:",
        "notes_label": "Notes (optional):",
        "show_password": "Show",
        "hide_password": "Hide",
        "generate_button": "Generate",
        "duplicate_password_title": "Duplicate Password Warning",
        "duplicate_password_message": "This password is already used for other accounts:\n{0}\nUsing unique passwords improves security. Do you want to use this password anyway?",
        "duplicate_password_message_no_accounts": "This password is a duplicate of one or more other accounts. Using unique passwords improves security. Do you want to use this password anyway?",
        "view_duplicates_button": "View Duplicates",
        "backup_title": "Backup Vault",
        "backup_success_message": "Vault backed up successfully to:\n{0}",
        "backup_error_message": "Vault backup failed: {0}",
        "restore_title": "Restore Vault",
        "restore_confirm_message": "Restoring will overwrite your current vault. Are you sure you want to proceed? The application will require a new login.",
        "restore_select_file_title": "Select Backup File to Restore",
        "restore_success_message": "Vault restored successfully from:\n{0}",
        "restore_error_message": "Vault restore failed: {0}",
        "restore_error_not_vault_file": "The selected file does not appear to be a valid vault backup.",
        "duplicate_checker_title": "Duplicate Password Checker",
        "duplicate_checker_intro": "The following passwords are used for multiple accounts. Consider changing them to unique, strong passwords:",
        "duplicate_checker_no_duplicates": "No duplicate passwords found! Good job!",
        "password_column_label": "Password",
        "accounts_column_label": "Accounts Using This Password",
        "autolock_notification_title": "Vault Locked",
        "autolock_notification_message": "MindVault has been automatically locked due to inactivity.",
        # 2FA Keys
        "enable_2fa_checkbox_label": "Enable Two-Factor Authentication (Recommended)",
        "2fa_setup_title": "Setup Two-Factor Authentication",
        "2fa_setup_instructions": "Scan the QR code with your authenticator app (e.g., Google Authenticator, Authy). If you cannot scan the QR code, you can manually enter the secret key.",
        "2fa_secret_key_label": "Secret Key:",
        "2fa_secret_key_copied": "Secret key copied to clipboard!",
        "2fa_enter_code_label": "Enter the 6-digit code from your authenticator app to verify:",
        "2fa_verify_and_enable_button": "Verify & Enable 2FA",
        "2fa_invalid_code_format": "Invalid code format. Please enter a 6-digit code.",
        "2fa_enabled_success": "Two-Factor Authentication has been successfully enabled!",
        "2fa_verification_failed": "Verification failed. The code is incorrect or has expired.",
        "2fa_verify_title": "Two-Factor Authentication",
        "2fa_enter_code_prompt": "Enter the 6-digit code from your authenticator app:",
        "verify_button": "Verify",
        "disable_2fa_confirm_title": "Disable 2FA",
        "disable_2fa_confirm_message": "Are you sure you want to disable Two-Factor Authentication? This will reduce the security of your vault.",
    },
    "ar.json": {
        "_lang_name_": "العربية",
        "app_title": APP_NAME,
        "ok_button": "موافق",
        "cancel_button": "إلغاء",
        "yes_button": "نعم",
        "no_button": "لا",
        "add_button": "إضافة",
        "edit_button": "تعديل",
        "delete_button": "حذف",
        "create_button": "إنشاء",
        "login_button": "تسجيل الدخول",
        "exit_button": "خروج",
        "settings_title": "الإعدادات",
        "language_label": "اللغة:",
        "theme_label": "السمة:",
        "font_label": "الخط:",
        "theme_light": "فاتح",
        "theme_dark": "داكن",
        "select_font_button": "اختر الخط",
        "select_font_dialog_title": "اختر الخط",
        "auto_lock_settings_label": "قفل الخزنة تلقائيًا بعد:",
        "auto_lock_disabled": "معطل",
        "auto_lock_minutes_suffix": "{0} دقائق",
        "status_ready": "جاهز.",
        "status_vault_loaded": "تم تحميل الخزنة. {0} حسابات.",
        "status_vault_saved": "تم حفظ الخزنة.",
        "status_vault_locked": "الخزنة مقفلة.",
        "status_settings_applied": "تم تطبيق الإعدادات.",
        "status_account_added": "تمت إضافة الحساب '{0}'.",
        "status_account_updated": "تم تحديث الحساب '{0}'.",
        "status_account_deleted": "تم حذف الحساب '{0}'.",
        "status_password_copied": "تم نسخ كلمة المرور لـ '{0}' إلى الحافظة.",
        "status_vault_restored_relogin": "تم استعادة الخزنة. يرجى تسجيل الدخول مرة أخرى.",
        "search_label": "بحث:",
        "search_placeholder": "اكتب لتصفية الحسابات...",
        "header_site": "الموقع/الخدمة",
        "header_username": "اسم المستخدم/البريد",
        "header_notes": "ملاحظات",
        "copy_password_button": "نسخ كلمة المرور",
        "menu_file": "ملف",
        "menu_edit": "تحرير",
        "menu_tools": "أدوات",
        "menu_help": "مساعدة",
        "add_action_tooltip": "إضافة حساب جديد",
        "edit_action_tooltip": "تعديل الحساب المحدد",
        "delete_action_tooltip": "حذف الحساب المحدد",
        "copy_action_tooltip": "نسخ كلمة مرور الحساب المحدد",
        "settings_action_tooltip": "فتح الإعدادات",
        "lock_action_tooltip": "قفل الخزنة",
        "exit_action_tooltip": "الخروج من التطبيق",
        "about_action_tooltip": "حول " + APP_NAME,
        "backup_vault_menu": "نسخ احتياطي للخزنة...",
        "backup_vault_tooltip": "عمل نسخة احتياطية للخزنة الحالية",
        "restore_vault_menu": "استعادة الخزنة...",
        "restore_vault_tooltip": "استعادة الخزنة من نسخة احتياطية",
        "check_duplicates_menu": "التحقق من كلمات المرور المكررة...",
        "check_duplicates_tooltip": "البحث عن حسابات تستخدم نفس كلمة المرور",
        "main_toolbar_title": "شريط الأدوات الرئيسي",
        "about_title": "حول " + APP_NAME,
        "about_text": "مدير كلمات مرور بسيط وآمن.",
        "error_title": "خطأ",
        "warning_title": "تحذير",
        "info_title": "معلومات",
        "input_error_title": "خطأ في الإدخال",
        "input_error_message": "لا يمكن ترك حقول الموقع واسم المستخدم وكلمة المرور فارغة.",
        "error_password_short": "يجب أن تتكون كلمة المرور الرئيسية من {0} أحرف على الأقل.",
        "error_password_mismatch": "كلمتا المرور غير متطابقتين.",
        "warning_password_weak": "كلمة المرور المختارة ضعيفة. هل أنت متأكد من رغبتك في استخدامها؟",
        "error_password_empty": "لا يمكن ترك كلمة المرور فارغة.",
        "login_title": "تسجيل الدخول",
        "login_prompt": "أدخل كلمة المرور الرئيسية لفتح الخزنة:",
        "master_password_label": "كلمة المرور الرئيسية",
        "login_error_incorrect": "كلمة المرور الرئيسية غير صحيحة أو الخزنة تالفة.",
        "setup_title": "إعداد MindVault",
        "setup_welcome": "أهلاً بك في MindVault!",
        "setup_instruction": "يرجى إنشاء كلمة مرور رئيسية قوية لتأمين خزنتك. ستكون هذه الكلمة مطلوبة للوصول إلى حساباتك المخزنة. تذكرها جيدًا، حيث لا يمكن استعادتها في حال فقدانها.",
        "master_password_placeholder": "الحد الأدنى {0} أحرف",
        "confirm_password_placeholder": "تأكيد كلمة المرور الرئيسية",
        "confirm_password_label": "تأكيد كلمة المرور الرئيسية:",
        "password_strength_label": "قوة كلمة المرور:",
        "password_strength_very_weak": "ضعيفة جدا",
        "password_strength_weak": "ضعيفة",
        "password_strength_medium": "متوسطة",
        "password_strength_strong": "قوية",
        "password_strength_very_strong": "قوية جدا",
        "error_load_vault": "لم يتم تحميل الخزنة.",
        "vault_file_not_found_detail": "ملف الخزنة غير موجود. يرجى التأكد من وجوده أو إعداد التطبيق مرة أخرى.",
        "error_save_vault": "لم يتم حفظ الخزنة.",
        "error_save_nokey": "لا يمكن حفظ الخزنة: المفتاح الرئيسي غير معين.",
        "error_encryption_failed": "فشل التشفير. لم يتم حفظ الخزنة.",
        "error_encryption_failed_save": "فشل التشفير أثناء الحفظ. لم يتم حفظ الخزنة.",
        "error_decrypt_failed_critical": "فشل فك تشفير الخزنة. قد تكون البيانات تالفة أو كلمة المرور غير صحيحة.",
        "unlock_vault_first": "يرجى فتح الخزنة أولاً لاستخدام هذه الميزة.",
        "warning_account_notfound": "الحساب المحدد غير موجود. ربما تم حذفه.",
        "warning_account_notfound_during_update": "الحساب المراد تحديثه غير موجود. يتم تحديث القائمة.",
        "error_add_failed": "فشل إضافة الحساب. لم يتم حفظ الخزنة.",
        "error_update_failed": "فشل تحديث الحساب. لم يتم حفظ الخزنة.",
        "error_delete_failed": "فشل حذف الحساب. لم يتم حفظ الخزنة.",
        "confirm_delete_title": "تأكيد الحذف",
        "confirm_delete_message": "هل أنت متأكد من رغبتك في حذف الحساب الخاص بـ '{0}'؟",
        "unknown_site": "موقع غير معروف",
        "warning_password_notfound": "كلمة المرور غير موجودة لهذا الحساب.",
        "error_clipboard_copy": "لم يتم النسخ إلى الحافظة.",
        "error_clipboard_unavailable": "خدمة الحافظة غير متوفرة.",
        "language_change_message": "سيتم تطبيق إعدادات اللغة بعد إعادة تشغيل التطبيق أو إعادة فتح الإعدادات.",
        "add_edit_account_title": "إضافة/تعديل حساب",
        "site_name_label": "اسم الموقع/الخدمة:",
        "username_label": "اسم المستخدم/البريد الإلكتروني:",
        "password_label": "كلمة المرور:",
        "notes_label": "ملاحظات (اختياري):",
        "show_password": "إظهار",
        "hide_password": "إخفاء",
        "generate_button": "إنشاء",
        "duplicate_password_title": "تحذير كلمة مرور مكررة",
        "duplicate_password_message": "كلمة المرور هذه مستخدمة بالفعل لحسابات أخرى:\n{0}\nاستخدام كلمات مرور فريدة يحسن الأمان. هل تريد استخدام كلمة المرور هذه على أي حال؟",
        "duplicate_password_message_no_accounts": "كلمة المرور هذه مكررة لواحدة أو أكثر من الحسابات الأخرى. استخدام كلمات مرور فريدة يحسن الأمان. هل تريد استخدام كلمة المرور هذه على أي حال؟",
        "view_duplicates_button": "عرض المكررات",
        "backup_title": "نسخ احتياطي للخزنة",
        "backup_success_message": "تم النسخ الاحتياطي للخزنة بنجاح إلى:\n{0}",
        "backup_error_message": "فشل النسخ الاحتياطي للخزنة: {0}",
        "restore_title": "استعادة الخزنة",
        "restore_confirm_message": "الاستعادة ستؤدي إلى الكتابة فوق خزنتك الحالية. هل أنت متأكد من رغبتك في المتابعة؟ سيتطلب التطبيق تسجيل دخول جديد.",
        "restore_select_file_title": "اختر ملف النسخ الاحتياطي للاستعادة",
        "restore_success_message": "تم استعادة الخزنة بنجاح من:\n{0}",
        "restore_error_message": "فشل استعادة الخزنة: {0}",
        "restore_error_not_vault_file": "الملف المحدد لا يبدو أنه نسخة احتياطية صالحة للخزنة.",
        "duplicate_checker_title": "مدقق كلمات المرور المكررة",
        "duplicate_checker_intro": "كلمات المرور التالية مستخدمة لعدة حسابات. ضع في اعتبارك تغييرها إلى كلمات مرور قوية وفريدة:",
        "duplicate_checker_no_duplicates": "لم يتم العثور على كلمات مرور مكررة! عمل جيد!",
        "password_column_label": "كلمة المرور",
        "accounts_column_label": "الحسابات التي تستخدم كلمة المرور هذه",
        "autolock_notification_title": "الخزنة مقفلة",
        "autolock_notification_message": "تم قفل MindVault تلقائيًا بسبب عدم النشاط.",
        # 2FA Keys - Arabic
        "enable_2fa_checkbox_label": "تمكين المصادقة الثنائية (موصى به)",
        "2fa_setup_title": "إعداد المصادقة الثنائية",
        "2fa_setup_instructions": "امسح رمز الاستجابة السريعة (QR) باستخدام تطبيق المصادقة الخاص بك (مثل Google Authenticator, Authy). إذا لم تتمكن من مسح الرمز، يمكنك إدخال المفتاح السري يدويًا.",
        "2fa_secret_key_label": "المفتاح السري:",
        "2fa_secret_key_copied": "تم نسخ المفتاح السري إلى الحافظة!",
        "2fa_enter_code_label": "أدخل الرمز المكون من 6 أرقام من تطبيق المصادقة للتحقق:",
        "2fa_verify_and_enable_button": "تحقق ومكّن المصادقة الثنائية",
        "2fa_invalid_code_format": "تنسيق الرمز غير صالح. يرجى إدخال رمز مكون من 6 أرقام.",
        "2fa_enabled_success": "تم تمكين المصادقة الثنائية بنجاح!",
        "2fa_verification_failed": "فشل التحقق. الرمز غير صحيح أو انتهت صلاحيته.",
        "2fa_verify_title": "المصادقة الثنائية",
        "2fa_enter_code_prompt": "أدخل الرمز المكون من 6 أرقام من تطبيق المصادقة:",
        "verify_button": "تحقق",
        "disable_2fa_confirm_title": "تعطيل المصادقة الثنائية",
        "disable_2fa_confirm_message": "هل أنت متأكد من رغبتك في تعطيل المصادقة الثنائية؟ سيؤدي هذا إلى تقليل أمان خزنتك.",
    }
}


class MindVaultApp:
    def __init__(self, argv):
        self.app = QApplication.instance() # Try to get existing instance
        if self.app is None: # Create it if it doesn't exist
            self.app = QApplication(argv)
        
        self.app.setApplicationName(APP_NAME)
        self.app.setApplicationVersion(APP_VERSION)
        self.app.setOrganizationName("PyPartners")

        self.settings_manager = SettingsManager(filename=SETTINGS_FILE)

        self.project_root = os.path.dirname(os.path.abspath(sys.argv[0])) 
        self.icons_dir_path = os.path.join(self.project_root, ICONS_DIR)
        self.lang_dir_path = os.path.join(self.project_root, LANG_DIR_NAME)

        ensure_dir(self.icons_dir_path)
        ensure_dir(self.lang_dir_path)

        app_icon_full_path = os.path.join(self.project_root, APP_ICON_PATH)
        if not os.path.exists(app_icon_full_path):
            app_icon_full_path = os.path.join(self.icons_dir_path, APP_ICON_PATH)

        if os.path.exists(app_icon_full_path):
            self.app.setWindowIcon(QIcon(app_icon_full_path))
        else:
            print(f"Warning: App icon '{APP_ICON_PATH}' not found at root or in '{ICONS_DIR}/'.")

        self.create_default_lang_files()

        initial_lang = self.settings_manager.get("language", DEFAULT_LANG)
        self.translator = TranslationHandler(self.app, initial_lang, lang_dir=self.lang_dir_path)
        
        self.apply_initial_settings()

        self.main_window = None
        self.master_password_string = None
        self.decrypted_vault_cache = None
        self.app_is_running = False # Flag to control the main application loop

    def create_default_lang_files(self):
        ensure_dir(self.lang_dir_path)
        for filename, content in DEFAULT_LANG_FILES_CONTENT.items():
            filepath = os.path.join(self.lang_dir_path, filename)
            if not os.path.exists(filepath):
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(content, f, indent=4, ensure_ascii=False, sort_keys=True)
                    print(f"Created default language file: {filepath}")
                except IOError as e:
                    print(f"Error creating language file {filepath}: {e}")

    def apply_initial_settings(self):
        current_theme = self.settings_manager.get("theme", DEFAULT_THEME)
        apply_theme(self.app, current_theme)

        font_family = self.settings_manager.get("font_family", DEFAULT_FONT_FAMILY)
        font_size = self.settings_manager.get("font_size", DEFAULT_FONT_SIZE)
        self.app.setFont(QFont(font_family, font_size))

        initial_lang = self.settings_manager.get("language", DEFAULT_LANG)
        if initial_lang == 'ar':
            self.app.setLayoutDirection(Qt.RightToLeft)
        else:
            self.app.setLayoutDirection(Qt.LeftToRight)

    def run(self):
        self.app_is_running = True
        exit_code = 0 # Default exit code

        while self.app_is_running:
            self.master_password_string = None
            self.decrypted_vault_cache = None

            first_run = self.settings_manager.get("first_run", True) or not os.path.exists(VAULT_FILE)

            if first_run:
                print("First run or vault not found. Starting setup...")
                setup_win = SetupWindow(self.translator)
                if setup_win.exec_() == QDialog.Accepted:
                    potential_master_password = setup_win.get_master_password()
                    ensure_dir(VAULT_DIR)
                    empty_vault = {"accounts": [], "config": {}}
                    encrypted_blob = encrypt_vault(empty_vault, potential_master_password)
                    if encrypted_blob:
                        try:
                            temp_vault_file = VAULT_FILE + ".tmp"
                            with open(temp_vault_file, 'wb') as f: f.write(encrypted_blob)
                            os.replace(temp_vault_file, VAULT_FILE)
                            self.settings_manager.set("first_run", False)
                            print("Initial vault created successfully.")
                            self.master_password_string = potential_master_password
                            self.decrypted_vault_cache = empty_vault
                        except Exception as e:
                            QMessageBox.critical(None, self.translator.tr("error_title"),
                                                 f"{self.translator.tr('error_save_vault')}\n{e}")
                            if os.path.exists(temp_vault_file): os.remove(temp_vault_file)
                            self.app_is_running = False # Critical error, stop
                            break # Exit while loop
                    else:
                        QMessageBox.critical(None, self.translator.tr("error_title"),
                                             self.translator.tr("error_encryption_failed") + "\nVault setup failed.")
                        self.app_is_running = False
                        break # Exit while loop
                else: # User cancelled setup
                    print("Setup cancelled by user.")
                    self.app_is_running = False
                    break # Exit while loop

            if not self.app_is_running: continue # Check flag after potential exit from setup

            # --- Normal Login Attempt ---
            if not self.master_password_string:
                login_win = LoginWindow(self.translator)
                master_password_ok = False
                potential_password_for_session = None

                while not master_password_ok:
                    if login_win.exec_() == QDialog.Accepted:
                        current_potential_password = login_win.get_master_password()
                        if not os.path.exists(VAULT_FILE):
                            login_win.show_error(self.translator.tr("error_load_vault") + "\n" +
                                                 self.translator.tr("vault_file_not_found_detail", VAULT_FILE))
                            continue
                        try:
                            with open(VAULT_FILE, 'rb') as f: encrypted_blob_test = f.read()
                            temp_decrypted_vault = decrypt_data(encrypted_blob_test, current_potential_password)
                            if temp_decrypted_vault is not None:
                                master_password_ok = True
                                potential_password_for_session = current_potential_password
                                self.decrypted_vault_cache = temp_decrypted_vault
                                print("Master password verified.")
                            else:
                                login_win.show_error(self.translator.tr("login_error_incorrect"))
                                self.decrypted_vault_cache = None
                        except Exception as e:
                            login_win.show_error(f"{self.translator.tr('error_load_vault')}\n{e}")
                            self.decrypted_vault_cache = None
                    else: # User cancelled login dialog
                        print("Login (master password) cancelled by user.")
                        self.app_is_running = False # Signal to exit main loop
                        break # Exit password attempt loop
                
                if not self.app_is_running: continue # Check flag after login cancel

                if not master_password_ok: # If login failed (e.g. multiple wrong attempts lead to cancel)
                    print("Master password not verified, restarting login or exiting.")
                    continue # Restart main while loop (will re-prompt login or exit if app_is_running false)


                # --- Stage 2: 2FA Check ---
                if self.decrypted_vault_cache:
                    two_fa_secret_key = get_2fa_secret_from_vault(self.decrypted_vault_cache)
                    if two_fa_secret_key:
                        print("2FA is enabled, prompting for code.")
                        two_fa_verify_dialog = TwoFactorVerifyDialog(self.translator)
                        if two_fa_verify_dialog.exec_() == QDialog.Accepted:
                            entered_code = two_fa_verify_dialog.get_entered_code()
                            if verify_totp_code(two_fa_secret_key, entered_code):
                                self.master_password_string = potential_password_for_session
                                print("2FA verification successful.")
                            else:
                                QMessageBox.warning(None, self.translator.tr("error_title"),
                                                    self.translator.tr("2fa_verification_failed"))
                                self.decrypted_vault_cache = None
                                continue # Restart main while loop for new login
                        else: # User cancelled 2FA dialog
                            print("2FA verification cancelled by user.")
                            self.decrypted_vault_cache = None
                            # If main_window was never shown, cancelling 2FA should exit.
                            if self.main_window is None:
                                self.app_is_running = False
                            continue # Restart main while loop (or exit if flag changed)
                    else: # 2FA not enabled
                        self.master_password_string = potential_password_for_session
                        print("2FA not enabled. Login successful with master password.")
                else: # Should not happen if master_password_ok was true
                    print("Error: Decrypted vault cache is None after master password success.")
                    continue # Restart main while loop

            if not self.app_is_running: continue # Check flag again

            # --- Show Main Window ---
            if self.master_password_string and self.decrypted_vault_cache is not None:
                if self.main_window is None: # Create main window only if it doesn't exist or was destroyed
                    self.main_window = MainWindow(self.translator, self.settings_manager)
                    self.main_window.request_relogin.connect(self.handle_relogin_request)
                
                self.main_window.vault_data = self.decrypted_vault_cache
                self.main_window.master_key_string = self.master_password_string
                
                if "config" not in self.main_window.vault_data:
                    self.main_window.vault_data["config"] = {}

                self.main_window.populate_accounts_table()
                self.main_window.status_bar.showMessage(
                    self.translator.tr("status_vault_loaded", len(self.main_window.vault_data.get("accounts", []))), 5000)
                
                if self.main_window.master_key_string:
                    self.main_window.auto_lock_manager.start()

                self.main_window.apply_app_settings()
                self.main_window.retranslate_ui()
                self.main_window.update_button_states()
                self.main_window.show()
                
                self.decrypted_vault_cache = None # Clear app-level cache

                current_exit_code = self.app.exec_() # This blocks until app.quit() or last window closed
                exit_code = current_exit_code # Store the exit code from Qt

                # After app.exec_() returns:
                if self.master_password_string is None and self.app_is_running:
                    # Relogin was requested (master_password_string cleared by handle_relogin_request)
                    # and app should continue running.
                    print("Main event loop finished, relogin requested. Continuing main app loop.")
                    # self.main_window is already None or closed due to handle_relogin_request
                    continue # Go to the start of the while self.app_is_running loop
                else:
                    # Normal exit or app_is_running became false
                    print("Application exec_() finished. Exiting main app loop.")
                    self.app_is_running = False # Ensure loop terminates
                    break # Exit the while self.app_is_running loop
            else:
                # Login failed or setup incomplete, and app_is_running might still be true
                if not self.app_is_running: # If already signaled to stop
                    print("Application run loop signaled to stop during login/setup phase.")
                    break
                
                print("Login failed or setup incomplete. Restarting login loop.")
                self.master_password_string = None
                self.decrypted_vault_cache = None
                continue # Go back to start of while self.app_is_running loop
        
        print(f"MindVaultApp.run() finished with exit code {exit_code}.")
        # sys.exit(exit_code) # Removed to allow control by the caller of run() if any, or let script end.

    def handle_relogin_request(self):
        print("Relogin request received by MindVaultApp.")
        self.master_password_string = None # Indicate that a new login is required
        
        if self.main_window:
            if self.main_window.isVisible():
                self.main_window.close() # This will trigger its closeEvent
            self.main_window = None # Discard the instance
        
        # If the Qt event loop is running, we need to quit it so the Python `while` loop can continue.
        # Check if QApplication instance exists and is running its event loop.
        # A more direct check might be needed if QCoreApplication.quit() is not sufficient
        # or if there are nested event loops.
        app_instance = QApplication.instance()
        if app_instance:
            # This is a common way to check if the event loop is active.
            # However, `QApplication.quit()` is the standard way to signal the event loop to terminate.
            # The `exec_()` call in `run()` will then return.
            print("Signaling Qt event loop to quit for relogin.")
            app_instance.quit()
        # The `continue` in the `run()` method's loop will handle restarting the login process.

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Create placeholder icons if they don't exist
    ensure_dir(ICONS_DIR) # ICONS_DIR is "icons"
    icon_files_to_check = [
        "add.png", "edit.png", "delete.png", "copy.png", "settings.png", 
        "lock.png", "exit.png", "backup.png", "restore.png", "duplicates.png",
        "check.png", "check_dark.png", APP_ICON_PATH # e.g., "app_icon.png"
    ]
    for icon_name in icon_files_to_check:
        icon_path_file = os.path.join(ICONS_DIR, icon_name) # icons/add.png etc.
        if not os.path.exists(icon_path_file):
            try:
                with open(icon_path_file, 'w') as f: pass
            except Exception as e:
                print(f"Could not create placeholder icon {icon_path_file}: {e}")
    
    root_app_icon = APP_ICON_PATH # e.g. "app_icon.png" at root
    icons_dir_app_icon = os.path.join(ICONS_DIR, APP_ICON_PATH) # icons/app_icon.png
    if not os.path.exists(root_app_icon) and os.path.exists(icons_dir_app_icon):
        try:
            shutil.copy2(icons_dir_app_icon, root_app_icon)
            print(f"Copied {icons_dir_app_icon} to {root_app_icon}")
        except Exception as e:
            print(f"Could not copy app icon from {ICONS_DIR}/ to root: {e}")

    mind_vault_app = MindVaultApp(sys.argv)
    final_exit_code = mind_vault_app.run() 

    sys.exit(final_exit_code) 


if __name__ == '__main__':
    main()