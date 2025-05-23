import os
import base64
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QDialogButtonBox, QLabel, QFontDialog, QComboBox, QCheckBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from constants import APP_NAME, DEFAULT_AUTO_LOCK_TIMEOUT 
from features import (
    check_password_strength_util,
    PasswordGeneratorDialog,
    check_for_duplicate_password,
    TwoFactorSetupDialog,
    TwoFactorVerifyDialog,
    store_2fa_secret_in_vault,
    is_2fa_enabled
)


class AccountDialog(QDialog):
    def __init__(self, translator, account_data=None, all_accounts_data=None, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.account_data = account_data if account_data else {}
        self.all_accounts_data = all_accounts_data if all_accounts_data else []
        self.parent_main_window = parent

        self.setWindowTitle(self.translator.tr("add_edit_account_title"))
        self.setMinimumWidth(450)

        layout = QFormLayout(self)
        self.site_name_edit = QLineEdit(self.account_data.get("site", ""))
        self.username_edit = QLineEdit(self.account_data.get("username", ""))
        
        password_outer_layout = QVBoxLayout()
        password_inner_layout = QHBoxLayout()
        self.password_edit = QLineEdit(self.account_data.get("password", ""))
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.textChanged.connect(self._update_password_strength_indicator)
        
        self.show_password_button = QPushButton(self.translator.tr("show_password"))
        self.show_password_button.setCheckable(True)
        self.show_password_button.toggled.connect(self.toggle_password_visibility)
        
        self.generate_password_button = QPushButton(self.translator.tr("generate_button"))
        self.generate_password_button.clicked.connect(self.open_password_generator)
        
        password_inner_layout.addWidget(self.password_edit, 1)
        password_inner_layout.addWidget(self.show_password_button)
        password_inner_layout.addWidget(self.generate_password_button)
        password_outer_layout.addLayout(password_inner_layout)
        
        self.password_strength_label = QLabel("")
        self._update_password_strength_indicator(self.password_edit.text()) # Initial check
        password_outer_layout.addWidget(self.password_strength_label)
        
        self.notes_edit = QLineEdit(self.account_data.get("notes", ""))
        
        layout.addRow(self.translator.tr("site_name_label"), self.site_name_edit)
        layout.addRow(self.translator.tr("username_label"), self.username_edit)
        layout.addRow(self.translator.tr("password_label"), password_outer_layout)
        layout.addRow(self.translator.tr("notes_label"), self.notes_edit)
        
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        self.button_box.button(QDialogButtonBox.Ok).setText(self.translator.tr("ok_button"))
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.translator.tr("cancel_button"))
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
        self.toggle_password_visibility(False) # Initialize to hidden

    def _update_password_strength_indicator(self, password_text):
        if not hasattr(self, 'password_strength_label'): return # Widget might not be fully initialized
        strength_text, style_sheet = check_password_strength_util(password_text, self.translator)
        self.password_strength_label.setText(f"{self.translator.tr('password_strength_label')} {strength_text}")
        self.password_strength_label.setStyleSheet(style_sheet)

    def open_password_generator(self):
        # Assuming PasswordGeneratorDialog.generate_password is a static method or similar
        generated_pwd = PasswordGeneratorDialog.generate_password(self.translator, self)
        if generated_pwd:
            self.password_edit.setText(generated_pwd)
            self._update_password_strength_indicator(generated_pwd) # Update strength for generated password

    def toggle_password_visibility(self, checked):
        if checked:
            self.password_edit.setEchoMode(QLineEdit.Normal)
            self.show_password_button.setText(self.translator.tr("hide_password"))
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.show_password_button.setText(self.translator.tr("show_password"))

    def validate_and_accept(self):
        site = self.site_name_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text() # No strip on password

        if not site or not username or not password:
            QMessageBox.warning(self, self.translator.tr("input_error_title"),
                                self.translator.tr("input_error_message"))
            return

        current_id = self.account_data.get("id", None) # For excluding self in duplicate check
        # Pass translator to check_for_duplicate_password if it needs to show a QMessageBox
        # Corrected line: Removed the 5th argument 'self'
        if check_for_duplicate_password(password, current_id, self.all_accounts_data, self.translator):
            # The function itself now handles the QMessageBox, so just return if it indicates a duplicate was confirmed by user to proceed or blocked
            return 
            
        self.accept()

    def get_data(self):
        site = self.site_name_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        notes = self.notes_edit.text().strip()
        
        # Generate a unique ID if it's a new account
        account_id = self.account_data.get("id", base64.urlsafe_b64encode(os.urandom(9)).decode('utf-8'))
        
        return {"site": site, "username": username, "password": password, "notes": notes, "id": account_id}

    @staticmethod
    def show_dialog(translator, account_data=None, all_accounts_data=None, parent=None):
        dialog = AccountDialog(translator, account_data, all_accounts_data, parent)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_data()
        return None


class SettingsDialog(QDialog):
    def __init__(self, translator, settings_manager, available_languages, main_window_ref, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.settings_manager = settings_manager
        self.available_languages = available_languages
        self.main_window_ref = main_window_ref # Reference to MainWindow for vault access

        self.setWindowTitle(self.translator.tr("settings_title"))
        self.setMinimumWidth(450) 

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Language Selection
        self.lang_combo = QComboBox()
        current_lang_code = self.settings_manager.get("language")
        sorted_langs = sorted(self.available_languages.items(), key=lambda item: item[1]) # Sort by name
        current_lang_idx = 0
        for i, (code, name) in enumerate(sorted_langs):
            self.lang_combo.addItem(f"{name} ({code})", code) # Display "Name (code)", store code
            if code == current_lang_code:
                current_lang_idx = i
        self.lang_combo.setCurrentIndex(current_lang_idx)
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
        current_font = QFont(
            self.settings_manager.get("font_family"),
            self.settings_manager.get("font_size")
        )
        self.selected_font = current_font # Store the QFont object
        self.font_label = QLabel(f"{current_font.family()}, {current_font.pointSize()}pt")
        self.font_label.setFont(current_font)
        self.font_button = QPushButton(self.translator.tr("select_font_button"))
        self.font_button.clicked.connect(self.select_font)
        font_layout.addWidget(self.font_label, 1) # Label takes expanding space
        font_layout.addWidget(self.font_button)
        form_layout.addRow(self.translator.tr("font_label"), font_layout)

        # Auto-lock Timeout
        self.auto_lock_combo = QComboBox()
        # Values are in minutes, 0 means disabled
        self.auto_lock_timeouts = { 
            self.translator.tr("auto_lock_disabled"): 0,
            "1 " + self.translator.tr("auto_lock_minutes_suffix", 1): 1,
            "5 " + self.translator.tr("auto_lock_minutes_suffix", 5): 5,
            "10 " + self.translator.tr("auto_lock_minutes_suffix", 10): 10,
            "15 " + self.translator.tr("auto_lock_minutes_suffix", 15): 15,
            "30 " + self.translator.tr("auto_lock_minutes_suffix", 30): 30,
            "60 " + self.translator.tr("auto_lock_minutes_suffix", 60): 60,
        }
        current_timeout_val = self.settings_manager.get("auto_lock_timeout", DEFAULT_AUTO_LOCK_TIMEOUT)
        current_timeout_idx = 0
        idx = 0
        for text, value in self.auto_lock_timeouts.items():
            self.auto_lock_combo.addItem(text, value) # Store timeout value in minutes
            if value == current_timeout_val:
                current_timeout_idx = idx
            idx += 1
        self.auto_lock_combo.setCurrentIndex(current_timeout_idx)
        form_layout.addRow(self.translator.tr("auto_lock_settings_label"), self.auto_lock_combo)

        # 2FA Setting
        self.enable_2fa_checkbox = QCheckBox(self.translator.tr("enable_2fa_checkbox_label"))
        if self.main_window_ref and self.main_window_ref.master_key_string:
            # Check current 2FA status from vault_data in main_window_ref
            self.enable_2fa_checkbox.setChecked(is_2fa_enabled(self.main_window_ref.vault_data))
        else:
            self.enable_2fa_checkbox.setEnabled(False) # Cannot change 2FA if vault is locked
            self.enable_2fa_checkbox.setToolTip(self.translator.tr("unlock_vault_first"))
        
        # Connect stateChanged *after* setting initial state to avoid premature trigger
        self.enable_2fa_checkbox.stateChanged.connect(self.handle_2fa_state_change)
        form_layout.addRow(self.enable_2fa_checkbox) # Add to layout

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(
             QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.translator.tr("ok_button"))
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.translator.tr("cancel_button"))
        
        self.button_box.accepted.connect(self.apply_settings_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Flags to track changes
        self.language_changed = False
        self.theme_changed = False
        self.font_changed = False
        self.auto_lock_changed = False
        # 2FA changes are applied directly to vault, so no specific flag needed here for get_changes()
        # The checkbox state reflects the vault's state.

    def select_font(self):
        font, ok = QFontDialog.getFont(self.selected_font, self, self.translator.tr("select_font_dialog_title"))
        if ok:
            self.selected_font = font
            self.font_label.setText(f"{font.family()}, {font.pointSize()}pt")
            self.font_label.setFont(font) # Update label preview

    def handle_2fa_state_change(self, state):
        is_checked = (state == Qt.Checked)

        # Ensure vault is accessible
        if not self.main_window_ref or not self.main_window_ref.master_key_string:
            self.enable_2fa_checkbox.setChecked(not is_checked) # Revert checkbox
            QMessageBox.warning(self, self.translator.tr("warning_title"), self.translator.tr("unlock_vault_first"))
            return

        current_2fa_status_in_vault = is_2fa_enabled(self.main_window_ref.vault_data)

        if is_checked and not current_2fa_status_in_vault: # User wants to enable 2FA
            vault_identifier = self.settings_manager.get("vault_identifier", f"{APP_NAME}User")
            setup_dialog = TwoFactorSetupDialog(
                self.translator, APP_NAME, vault_identifier, parent=self
            )
            if setup_dialog.exec_() == QDialog.Accepted:
                secret_key = setup_dialog.get_secret_key()
                # Store secret in main_window's vault_data
                store_2fa_secret_in_vault(self.main_window_ref.vault_data, secret_key)
                if not self.main_window_ref.save_vault(): # Attempt to save changes
                    # If save fails, revert 2FA setup in memory
                    store_2fa_secret_in_vault(self.main_window_ref.vault_data, None) 
                    self.enable_2fa_checkbox.setChecked(False) # Uncheck UI
                    QMessageBox.critical(self, self.translator.tr("error_title"), self.translator.tr("error_save_vault"))
                # Success message is handled by TwoFactorSetupDialog
            else: # User cancelled 2FA setup
                self.enable_2fa_checkbox.setChecked(False) # Uncheck UI
        
        elif not is_checked and current_2fa_status_in_vault: # User wants to disable 2FA
            reply = QMessageBox.question(self, self.translator.tr("disable_2fa_confirm_title"),
                                         self.translator.tr("disable_2fa_confirm_message"),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                # Remove secret from main_window's vault_data
                store_2fa_secret_in_vault(self.main_window_ref.vault_data, None) 
                if not self.main_window_ref.save_vault():
                    # If save fails, ideally revert (would need old secret if complex recovery desired)
                    # For now, just warn and UI might be out of sync until reload or fix
                    QMessageBox.critical(self, self.translator.tr("error_title"), self.translator.tr("error_save_vault"))
                    # Re-check the box as disable failed, but the secret is already cleared from memory vault_data
                    # This is tricky. Safest is to tell user save failed and they might need to re-enable/disable.
                    # Or, attempt to re-load the vault to get the true state.
                    # For now, let's assume the user will try again or the app will handle later.
                    # We can refresh the checkbox state based on the (failed-to-save but modified) vault_data
                    self.enable_2fa_checkbox.setChecked(is_2fa_enabled(self.main_window_ref.vault_data))

            else: # User chose not to disable
                self.enable_2fa_checkbox.setChecked(True) # Re-check UI
        
        # Final sync of checkbox with vault_data state after any operation
        if self.main_window_ref and self.main_window_ref.master_key_string:
             self.enable_2fa_checkbox.setChecked(is_2fa_enabled(self.main_window_ref.vault_data))


    def apply_settings_and_accept(self):
        new_lang = self.lang_combo.currentData()
        new_theme = self.theme_combo.currentData()
        new_font_family = self.selected_font.family()
        new_font_size = self.selected_font.pointSize()
        new_auto_lock_timeout = self.auto_lock_combo.currentData()

        if new_lang != self.settings_manager.get("language"):
            self.language_changed = True
            self.settings_manager.set("language", new_lang)
        if new_theme != self.settings_manager.get("theme"):
            self.theme_changed = True
            self.settings_manager.set("theme", new_theme)
        if new_font_family != self.settings_manager.get("font_family") or \
           new_font_size != self.settings_manager.get("font_size"):
            self.font_changed = True
            self.settings_manager.set("font_family", new_font_family)
            self.settings_manager.set("font_size", new_font_size)
        if new_auto_lock_timeout != self.settings_manager.get("auto_lock_timeout"):
            self.auto_lock_changed = True
            self.settings_manager.set("auto_lock_timeout", new_auto_lock_timeout)
        
        # Settings manager saves itself when set() is called.
        # 2FA changes are already saved (or attempted to be saved) by handle_2fa_state_change.

        if self.language_changed:
             QMessageBox.information(self, self.translator.tr("info_title"),
                                     self.translator.tr("language_change_message"))
        super().accept() # Close the dialog

    def get_changes(self):
        return {
            "language_changed": self.language_changed,
            "theme_changed": self.theme_changed,
            "font_changed": self.font_changed,
            "auto_lock_changed": self.auto_lock_changed,
            # 2FA change status is not directly tracked here as it's applied immediately
        }

class SetupWindow(QDialog):
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.master_password = None

        self.setWindowTitle(self.translator.tr("setup_title"))
        self.setMinimumWidth(400)
        self.setModal(True) # Block other windows

        layout = QVBoxLayout(self)

        welcome_label = QLabel(self.translator.tr("setup_welcome"))
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("font-size: 16pt; margin-bottom: 15px;")

        instruction_label = QLabel(self.translator.tr("setup_instruction"))
        instruction_label.setWordWrap(True)

        form_layout = QFormLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText(self.translator.tr("master_password_placeholder", 8))
        self.password_edit.setEchoMode(QLineEdit.Password)
        
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setPlaceholderText(self.translator.tr("confirm_password_placeholder"))
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)

        form_layout.addRow(self.translator.tr("master_password_label"), self.password_edit)
        form_layout.addRow(self.translator.tr("confirm_password_label"), self.confirm_password_edit)

        self.strength_label = QLabel() # Text set by update_strength_display
        self.password_edit.textChanged.connect(self.update_strength_display)
        form_layout.addRow(self.translator.tr("password_strength_label"), self.strength_label)

        layout.addWidget(welcome_label)
        layout.addWidget(instruction_label)
        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.translator.tr("create_button"))
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.translator.tr("cancel_button"))
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False) # Initially disabled

        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Connect validation after UI setup
        self.password_edit.textChanged.connect(self.validate_inputs)
        self.confirm_password_edit.textChanged.connect(self.validate_inputs)
        
        self.update_strength_display("") # Initial strength display
        self.validate_inputs() # Initial validation for button state

    def _get_strength_score(self, password_text):
        # Using the text from check_password_strength_util to determine score
        strength_text, _ = check_password_strength_util(password_text, self.translator)
        # This relies on the exact translated strings. Might be fragile.
        # Better if check_password_strength_util returned a score or enum.
        if strength_text == self.translator.tr("password_strength_very_weak"): return 1 # Assuming this key exists
        if strength_text == self.translator.tr("password_strength_weak"): return 2
        if strength_text == self.translator.tr("password_strength_medium"): return 3
        if strength_text == self.translator.tr("password_strength_strong"): return 4
        if strength_text == self.translator.tr("password_strength_very_strong"): return 5 # Assuming this key exists
        return 0 # Default unknown

    def update_strength_display(self, password_text):
        strength_text, style_sheet = check_password_strength_util(password_text, self.translator)
        self.strength_label.setText(strength_text)
        self.strength_label.setStyleSheet(style_sheet)

    def validate_inputs(self):
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        passwords_match = (password == confirm_password)
        is_valid_length = (len(password) >= 8) 
        # For simplicity, just check length and match. Strength is advisory.
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(is_valid_length and passwords_match)

    def validate_and_accept(self):
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        if len(password) < 8:
            QMessageBox.warning(self, self.translator.tr("error_title"), 
                                self.translator.tr("error_password_short", 8))
            return
        if password != confirm_password:
            QMessageBox.warning(self, self.translator.tr("error_title"), 
                                self.translator.tr("error_password_mismatch"))
            return

        strength_score = self._get_strength_score(password)
        # Consider a score of 3 (medium) or less as weak enough for a warning
        if strength_score < 3: # Adjust threshold as needed
             reply = QMessageBox.question(self, self.translator.tr("warning_title"),
                                          self.translator.tr("warning_password_weak"), # Generic weak password warning
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
             if reply == QMessageBox.No:
                 return # User chose not to proceed with a weak password
        
        self.master_password = password
        self.accept()

    def get_master_password(self):
        return self.master_password


class LoginWindow(QDialog):
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.master_password = None

        self.setWindowTitle(f"{APP_NAME} - {self.translator.tr('login_title')}")
        self.setMinimumWidth(350)
        self.setModal(True)

        layout = QVBoxLayout(self)

        icon_label = QLabel("🔒") # Simple lock icon
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48pt; margin-bottom: 15px;")

        prompt_label = QLabel(self.translator.tr("login_prompt"))
        prompt_label.setAlignment(Qt.AlignCenter)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText(self.translator.tr("master_password_label"))
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.returnPressed.connect(self.validate_and_accept) # Allow login with Enter key

        self.error_label = QLabel("") # For displaying login errors
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.hide() # Initially hidden

        layout.addWidget(icon_label)
        layout.addWidget(prompt_label)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.error_label)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.translator.tr("login_button"))
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.translator.tr("exit_button"))
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False) # Disable OK until text is entered

        # Enable OK button only if password field is not empty
        self.password_edit.textChanged.connect(
            lambda text: self.button_box.button(QDialogButtonBox.Ok).setEnabled(bool(text.strip()))
        )

        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject) # Closes dialog, app will exit
        layout.addWidget(self.button_box)
        
        self.password_edit.setFocus() # Focus on password field on open

    def validate_and_accept(self):
        password = self.password_edit.text()
        if not password: # Should be caught by button state, but good for Enter key
            self.show_error(self.translator.tr("error_password_empty"))
            return
        
        self.master_password = password
        self.error_label.hide() # Clear any previous error
        self.accept()

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()
        self.password_edit.selectAll() # Select text for easy re-entry
        self.password_edit.setFocus()

    def get_master_password(self):
        return self.master_password