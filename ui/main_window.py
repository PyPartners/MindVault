import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QSpacerItem,
    QSizePolicy, QAction, QMenuBar, QMenu, QToolBar, QStatusBar, QMessageBox, QDialog, QApplication
)
from PyQt5.QtGui import QIcon, QFont, QClipboard
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer

from constants import (
    APP_NAME, APP_VERSION, VAULT_FILE, VAULT_DIR, ICONS_DIR,
    DEFAULT_THEME, DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE # For apply_app_settings
)
from core.crypto import decrypt_data, encrypt_vault
from core.utils import ensure_dir
from .dialogs import AccountDialog, SettingsDialog # Relative import
from .styles import apply_theme # Relative import

# Feature imports
from features import (
    AutoLockManager,
    BackupRestoreHandler,
    DuplicateCheckerDialog,
    find_all_duplicate_passwords
)

DEFAULT_LANG = "en"

class MainWindow(QMainWindow):
    request_relogin = pyqtSignal() # Signal to controller to handle relogin

    def __init__(self, translator, settings_manager):
        super().__init__()
        self.translator = translator
        self.settings_manager = settings_manager
        self.master_key_string = None
        self.vault_data = {"accounts": [], "config": {}} # Ensure config exists
        self._clipboard = QApplication.clipboard() if QApplication.instance() else None # Handle no app instance during tests

        # Initialize AutoLockManager (from features)
        self.auto_lock_manager = AutoLockManager(
            self, # QWidget parent for timer
            self.settings_manager, 
            self.translator,
            self # Pass self as main_window_ref for lock_vault callback
        )
        # Initialize BackupRestoreHandler (from features)
        self.backup_restore_handler = BackupRestoreHandler(VAULT_FILE, self.translator, self)

        self.setWindowTitle(APP_NAME)
        self.resize(800, 600)
        self.setWindowIcon(QIcon(os.path.join(ICONS_DIR, "app_icon.png")))


        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_label = QLabel() # Text set by retranslate_ui
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_accounts)
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # Accounts table
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(3) # Site, Username, Notes
        self.accounts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.accounts_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.accounts_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Non-editable cells
        self.accounts_table.horizontalHeader().setStretchLastSection(True)
        self.accounts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # Site name stretches
        self.accounts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # Username to contents
        self.accounts_table.verticalHeader().setVisible(False) # Hide row numbers
        self.accounts_table.itemSelectionChanged.connect(self.update_button_states)
        self.accounts_table.doubleClicked.connect(self.edit_selected_account) # Double-click to edit
        main_layout.addWidget(self.accounts_table)

        # Action buttons
        button_layout = QHBoxLayout()
        self.add_button = QPushButton()
        self.edit_button = QPushButton()
        self.delete_button = QPushButton()
        self.copy_button = QPushButton()
        
        # Set object names for styling if needed (e.g., deleteButton, copyButton)
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

        self.create_actions()
        self.create_menus()
        self.create_toolbar()
        self.create_statusbar()

        self.update_button_states() # Initial button state
        self.retranslate_ui() # Set initial text for all UI elements

    def _icon(self, name):
        # Helper to load icons, trying theme first, then from ICONS_DIR
        themed_icon = QIcon.fromTheme(name)
        if not themed_icon.isNull():
            return themed_icon
        
        # Fallback to file system icon if ICONS_DIR is defined and file exists
        # Standard names for themed icons often don't have .png
        # Map common action names to typical file names if necessary
        icon_map = {
            "list-add": "add.png", "document-edit": "edit.png", "edit-delete": "delete.png",
            "edit-copy": "copy.png", "preferences-system": "settings.png",
            "system-lock-screen": "lock.png", "application-exit": "exit.png",
            "document-save-as": "backup.png", "document-open": "restore.png",
            "tools-check-spelling": "duplicates.png"
        }
        file_name = icon_map.get(name, name + ".png") # Default to name.png if not in map
        
        path = os.path.join(ICONS_DIR, file_name)
        if os.path.exists(path):
            return QIcon(path)
        return QIcon() # Return empty icon if not found

    def create_actions(self):
        self.add_act = QAction(self._icon("list-add"), "", self, triggered=self.add_account)
        self.edit_act = QAction(self._icon("document-edit"), "", self, triggered=self.edit_selected_account)
        self.delete_act = QAction(self._icon("edit-delete"), "", self, triggered=self.delete_selected_account)
        self.copy_act = QAction(self._icon("edit-copy"), "", self, triggered=self.copy_selected_password)
        self.settings_act = QAction(self._icon("preferences-system"), "", self, triggered=self.open_settings)
        self.lock_act = QAction(self._icon("system-lock-screen"), "", self, triggered=self.lock_vault)
        self.exit_act = QAction(self._icon("application-exit"), "", self, triggered=self.close)
        
        self.about_act = QAction("", self, triggered=self.show_about_dialog) # No icon for About usually
        
        self.backup_act = QAction(self._icon("document-save-as"), "", self, triggered=self.perform_backup)
        self.restore_act = QAction(self._icon("document-open"), "", self, triggered=self.perform_restore)
        self.check_duplicates_act = QAction(self._icon("tools-check-spelling"), "", self, triggered=self.show_duplicate_password_checker)

        # Shortcuts
        self.add_act.setShortcut("Ctrl+N")
        self.edit_act.setShortcut("Ctrl+E")
        self.delete_act.setShortcut(Qt.Key_Delete) # Standard delete key
        self.copy_act.setShortcut("Ctrl+C")
        self.settings_act.setShortcut("Ctrl+,") # Common shortcut for settings
        self.lock_act.setShortcut("Ctrl+L")
        self.exit_act.setShortcut("Ctrl+Q")
        self.check_duplicates_act.setShortcut("Ctrl+D") # Example shortcut for duplicates

    def create_menus(self):
        self.menu_bar = self.menuBar() # Get the main window's menu bar
        
        # File Menu
        self.file_menu = self.menu_bar.addMenu("") # Text set by retranslate_ui
        self.file_menu.addAction(self.add_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.backup_act)
        self.file_menu.addAction(self.restore_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.lock_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.settings_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_act)
        
        # Edit Menu
        self.edit_menu = self.menu_bar.addMenu("")
        self.edit_menu.addAction(self.edit_act)
        self.edit_menu.addAction(self.delete_act)
        self.edit_menu.addSeparator()
        self.edit_menu.addAction(self.copy_act)
        
        # Tools Menu
        self.tools_menu = self.menu_bar.addMenu("")
        self.tools_menu.addAction(self.check_duplicates_act)
        
        # Help Menu
        self.help_menu = self.menu_bar.addMenu("")
        self.help_menu.addAction(self.about_act)

    def create_toolbar(self):
        self.toolbar = self.addToolBar("") # Title set by retranslate_ui
        self.toolbar.setIconSize(QSize(24, 24)) # Standard icon size
        self.toolbar.setMovable(False) # Prevent user from moving toolbar

        self.toolbar.addAction(self.add_act)
        self.toolbar.addAction(self.edit_act)
        self.toolbar.addAction(self.delete_act)
        self.toolbar.addAction(self.copy_act)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.check_duplicates_act)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.settings_act)
        self.toolbar.addAction(self.lock_act)

    def create_statusbar(self):
        self.status_bar = self.statusBar() # Get main window's status bar
        # Initial message set by retranslate_ui

    def load_vault(self, master_password_string): # Called by controller after successful login
        self.master_key_string = master_password_string
        
        if not os.path.exists(VAULT_FILE):
            self.vault_data = {"accounts": [], "config": {}} # Fresh vault structure
            self.populate_accounts_table()
            if self.master_key_string: self.auto_lock_manager.start()
            return True # New vault, effectively "loaded"

        try:
            with open(VAULT_FILE, 'rb') as f:
                encrypted_blob = f.read()
            
            decrypted_data = decrypt_data(encrypted_blob, self.master_key_string)
            if decrypted_data is None:
                # This case should ideally be handled by the login screen itself.
                # If it occurs here, it implies an issue post-login or a corrupted vault.
                QMessageBox.critical(self, self.translator.tr("error_title"), self.translator.tr("error_decrypt_failed_critical"))
                self.lock_vault() # Force relogin or exit
                return False

            self.vault_data = decrypted_data
            # Ensure essential keys exist
            if "accounts" not in self.vault_data or not isinstance(self.vault_data["accounts"], list):
                 self.vault_data["accounts"] = []
            if "config" not in self.vault_data: # For 2FA and future global configs
                 self.vault_data["config"] = {}
            
            self.populate_accounts_table()
            self.status_bar.showMessage(self.translator.tr("status_vault_loaded", len(self.vault_data["accounts"])), 5000)
            if self.master_key_string: self.auto_lock_manager.start() # Start auto-lock timer
            return True
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr("error_title"), f"{self.translator.tr('error_load_vault')}\n{e}")
            self.vault_data = {"accounts": [], "config": {}} # Reset to empty on error
            self.populate_accounts_table()
            self.lock_vault() # Force relogin or exit
            return False

    def save_vault(self):
        if not self.master_key_string:
            QMessageBox.critical(self, self.translator.tr("error_title"), self.translator.tr("error_save_nokey"))
            return False
        
        ensure_dir(VAULT_DIR) # Ensure data directory exists
        
        # Ensure 'config' key exists, crucial for 2FA logic that expects it
        if "config" not in self.vault_data:
            self.vault_data["config"] = {}
            
        encrypted_blob = encrypt_vault(self.vault_data, self.master_key_string)
        if encrypted_blob:
            try:
                # Atomic save: write to temp file then replace original
                temp_file = VAULT_FILE + ".tmp"
                with open(temp_file, 'wb') as f:
                    f.write(encrypted_blob)
                os.replace(temp_file, VAULT_FILE) # Atomic on most OS
                print("Vault saved successfully.")
                self.status_bar.showMessage(self.translator.tr("status_vault_saved"), 3000)
                return True
            except Exception as e:
                QMessageBox.critical(self, self.translator.tr("error_title"), f"{self.translator.tr('error_save_vault')}\n{e}")
                if os.path.exists(temp_file): # Cleanup temp file on error
                    try: os.remove(temp_file)
                    except OSError: pass
                return False
        else:
             QMessageBox.critical(self, self.translator.tr("error_title"), self.translator.tr("error_encryption_failed_save"))
             return False

    def populate_accounts_table(self, filter_text=""):
        self.accounts_table.setSortingEnabled(False) # Disable sorting during population
        self.accounts_table.setRowCount(0) # Clear existing rows
        
        filter_text = filter_text.lower().strip()
        current_accounts = self.vault_data.get("accounts", [])
        
        accounts_to_display = []
        if filter_text:
            for account in current_accounts:
                site_match = filter_text in account.get("site", "").lower()
                user_match = filter_text in account.get("username", "").lower()
                notes_match = filter_text in account.get("notes", "").lower()
                if site_match or user_match or notes_match:
                    accounts_to_display.append(account)
        else:
            accounts_to_display = current_accounts
            
        # Sort accounts by site name (case-insensitive) before displaying
        accounts_to_display.sort(key=lambda x: x.get("site", "").lower())
            
        for account in accounts_to_display:
            row_position = self.accounts_table.rowCount()
            self.accounts_table.insertRow(row_position)
            
            site_item = QTableWidgetItem(account.get("site", ""))
            username_item = QTableWidgetItem(account.get("username", ""))
            notes_item = QTableWidgetItem(account.get("notes", ""))
            
            # Store the unique account ID in the first item's UserRole data
            account_id = account.get("id")
            if account_id:
                site_item.setData(Qt.UserRole, account_id)
            
            self.accounts_table.setItem(row_position, 0, site_item)
            self.accounts_table.setItem(row_position, 1, username_item)
            self.accounts_table.setItem(row_position, 2, notes_item)
            
        self.accounts_table.setSortingEnabled(True) # Re-enable sorting
        self.update_button_states()

    def filter_accounts(self):
        self.populate_accounts_table(self.search_input.text())

    def get_selected_account_id(self):
        selected_rows = self.accounts_table.selectionModel().selectedRows()
        if selected_rows:
            # Assuming ID is stored in the first column's item
            first_item = self.accounts_table.item(selected_rows[0].row(), 0) 
            if first_item:
                return first_item.data(Qt.UserRole) # Retrieve stored ID
        return None

    def get_account_by_id(self, account_id):
        if not account_id or not isinstance(self.vault_data.get("accounts"), list):
            return None
        for account in self.vault_data["accounts"]:
            if account.get("id") == account_id:
                return account
        return None

    def update_button_states(self):
        has_selection = bool(self.get_selected_account_id())
        # Main window buttons
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.copy_button.setEnabled(has_selection)
        # Corresponding actions in menu/toolbar
        self.edit_act.setEnabled(has_selection)
        self.delete_act.setEnabled(has_selection)
        self.copy_act.setEnabled(has_selection)
        
        # Lock action should always be enabled if vault is open
        is_locked = not bool(self.master_key_string)
        self.lock_act.setEnabled(not is_locked)

        # Some actions might depend on whether the vault is locked
        can_operate_on_vault = not is_locked
        self.add_act.setEnabled(can_operate_on_vault)
        self.add_button.setEnabled(can_operate_on_vault)
        self.backup_act.setEnabled(can_operate_on_vault)
        # Restore can be enabled even if locked, as it forces a re-login.
        # self.restore_act.setEnabled(True) # Or based on some other logic
        self.check_duplicates_act.setEnabled(can_operate_on_vault)


    def add_account(self):
        if not self.master_key_string: # Should be disabled by update_button_states, but as safeguard
            QMessageBox.warning(self, self.translator.tr("warning_title"), self.translator.tr("unlock_vault_first"))
            return

        new_data = AccountDialog.show_dialog(
            self.translator,
            all_accounts_data=self.vault_data.get("accounts", []), # Pass all accounts for duplicate check
            parent=self
        )
        if new_data:
            if not isinstance(self.vault_data.get("accounts"), list): # Should not happen if vault_data is initialized well
                self.vault_data["accounts"] = []
            self.vault_data["accounts"].append(new_data)
            if self.save_vault():
                current_filter = self.search_input.text()
                self.populate_accounts_table(current_filter) # Refresh table
                # Try to select the newly added item
                for row in range(self.accounts_table.rowCount()):
                     item = self.accounts_table.item(row, 0)
                     if item and item.data(Qt.UserRole) == new_data['id']:
                         self.accounts_table.selectRow(row)
                         break
                self.status_bar.showMessage(self.translator.tr("status_account_added", new_data['site']), 3000)
            else:
                # If save failed, revert the addition from memory
                self.vault_data["accounts"].pop() 
                QMessageBox.critical(self, self.translator.tr("error_title"), self.translator.tr("error_add_failed"))

    def edit_selected_account(self):
        selected_id = self.get_selected_account_id()
        if not selected_id: return

        account_to_edit = self.get_account_by_id(selected_id)
        if not account_to_edit:
             QMessageBox.warning(self, self.translator.tr("warning_title"), self.translator.tr("warning_account_notfound"))
             self.populate_accounts_table(self.search_input.text()) # Refresh table in case
             return

        original_account_copy = account_to_edit.copy() # For rollback on save failure
        
        updated_data = AccountDialog.show_dialog(
            self.translator,
            account_data=original_account_copy, # Pass a copy to dialog
            all_accounts_data=self.vault_data.get("accounts", []),
            parent=self
        )
        
        if updated_data:
            try:
                # Find index of the account to update
                index_to_update = next(i for i, acc in enumerate(self.vault_data["accounts"]) if acc.get("id") == selected_id)
                self.vault_data["accounts"][index_to_update] = updated_data
                
                if self.save_vault():
                    current_filter = self.search_input.text()
                    self.populate_accounts_table(current_filter)
                    # Try to re-select the edited item
                    for row in range(self.accounts_table.rowCount()):
                         item = self.accounts_table.item(row, 0)
                         if item and item.data(Qt.UserRole) == selected_id:
                             self.accounts_table.selectRow(row)
                             break
                    self.status_bar.showMessage(self.translator.tr("status_account_updated", updated_data['site']), 3000)
                else:
                     # Rollback if save failed
                     self.vault_data["accounts"][index_to_update] = original_account_copy
                     self.populate_accounts_table(self.search_input.text()) # Refresh with original
                     QMessageBox.critical(self, self.translator.tr("error_title"), self.translator.tr("error_update_failed"))
            except StopIteration:
                 # Account ID was not found in the list, something is wrong
                 QMessageBox.warning(self, self.translator.tr("warning_title"), self.translator.tr("warning_account_notfound_during_update"))
                 self.populate_accounts_table(self.search_input.text())


    def delete_selected_account(self):
        selected_id = self.get_selected_account_id()
        if not selected_id: return

        account_to_delete = self.get_account_by_id(selected_id)
        if not account_to_delete:
             QMessageBox.warning(self, self.translator.tr("warning_title"), self.translator.tr("warning_account_notfound"))
             self.populate_accounts_table(self.search_input.text())
             return

        site_name = account_to_delete.get('site', self.translator.tr("unknown_site"))
        reply = QMessageBox.question(self, self.translator.tr("confirm_delete_title"),
                                     self.translator.tr("confirm_delete_message", site_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            original_accounts = list(self.vault_data["accounts"]) # Copy for rollback
            self.vault_data["accounts"] = [acc for acc in self.vault_data["accounts"] if acc.get("id") != selected_id]
            
            if self.save_vault():
                self.populate_accounts_table(self.search_input.text()) # Refresh table
                self.status_bar.showMessage(self.translator.tr("status_account_deleted", site_name), 3000)
            else:
                 # Rollback if save failed
                 self.vault_data["accounts"] = original_accounts
                 self.populate_accounts_table(self.search_input.text())
                 QMessageBox.critical(self, self.translator.tr("error_title"), self.translator.tr("error_delete_failed"))

    def copy_selected_password(self):
        selected_id = self.get_selected_account_id()
        if not selected_id: return

        account = self.get_account_by_id(selected_id)
        if account and "password" in account:
            if self._clipboard:
                try:
                    self._clipboard.setText(account["password"])
                    self.status_bar.showMessage(
                        self.translator.tr("status_password_copied", account.get('site', self.translator.tr("unknown_site"))),
                        3000
                    )
                    # Optional: Clear clipboard after a delay
                    QTimer.singleShot(15000, lambda: self._clipboard.clear() if self._clipboard.text() == account["password"] else None)
                except Exception as e:
                     QMessageBox.warning(self, self.translator.tr("error_title"), 
                                         f"{self.translator.tr('error_clipboard_copy')}\n{e}")
            else:
                QMessageBox.warning(self, self.translator.tr("error_title"), self.translator.tr("error_clipboard_unavailable"))
        else:
             QMessageBox.warning(self, self.translator.tr("warning_title"), self.translator.tr("warning_password_notfound"))

    def open_settings(self):
        # Pass `self` (MainWindow instance) to SettingsDialog for 2FA operations
        # that need to access/modify vault_data and call save_vault()
        available_langs = self.translator.get_available_languages()
        settings_dialog = SettingsDialog(
            self.translator, 
            self.settings_manager, 
            available_langs, 
            main_window_ref=self, # Pass reference to self
            parent=self
        )
        
        if settings_dialog.exec_() == QDialog.Accepted:
            changes = settings_dialog.get_changes()
            
            if changes["theme_changed"] or changes["font_changed"]:
                 self.apply_app_settings() # Apply theme and font to the whole app
            
            if changes["language_changed"]:
                current_lang = self.settings_manager.get("language", DEFAULT_LANG)
                # Reload translations and update UI direction in TranslationHandler
                self.translator.load_language(current_lang) 
                self.retranslate_ui() # Retranslate all text in MainWindow
                # Application-level layout direction is set by TranslationHandler
                # QTimer.singleShot(0, lambda: QApplication.instance().setLayoutDirection(
                #     Qt.RightToLeft if current_lang == 'ar' else Qt.LeftToRight
                # ))


            if changes["auto_lock_changed"]:
                self.auto_lock_manager.update_settings() # Restart timer with new timeout
            
            self.status_bar.showMessage(self.translator.tr("status_settings_applied"), 3000)
            # Note: 2FA changes are handled and saved directly within SettingsDialog logic

    def apply_app_settings(self): # Applies theme and font globally
        app = QApplication.instance()
        if not app: return

        current_theme = self.settings_manager.get("theme", DEFAULT_THEME)
        apply_theme(app, current_theme) # From ui.styles

        font_family = self.settings_manager.get("font_family", DEFAULT_FONT_FAMILY)
        font_size = self.settings_manager.get("font_size", DEFAULT_FONT_SIZE)
        app_font = QFont(font_family, font_size)
        app.setFont(app_font)
        
        # Also apply font to this window instance if it's already created
        self.setFont(app_font) 
        
        # Force Qt to re-evaluate styles for the new theme/font
        # This can help with widgets that don't update immediately.
        self.style().unpolish(self)
        self.style().polish(self)
        self.update() # Request a repaint

    def retranslate_ui(self):
        self.setWindowTitle(APP_NAME) # App name is not translated by default
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
        
        # Actions (Tooltips and Menu Text)
        self.add_act.setText(self.translator.tr("add_action_tooltip"))
        self.add_act.setToolTip(self.translator.tr("add_action_tooltip"))
        self.edit_act.setText(self.translator.tr("edit_action_tooltip"))
        self.edit_act.setToolTip(self.translator.tr("edit_action_tooltip"))
        self.delete_act.setText(self.translator.tr("delete_action_tooltip"))
        self.delete_act.setToolTip(self.translator.tr("delete_action_tooltip"))
        self.copy_act.setText(self.translator.tr("copy_action_tooltip"))
        self.copy_act.setToolTip(self.translator.tr("copy_action_tooltip"))
        self.settings_act.setText(self.translator.tr("settings_action_tooltip"))
        self.settings_act.setToolTip(self.translator.tr("settings_action_tooltip"))
        self.lock_act.setText(self.translator.tr("lock_action_tooltip"))
        self.lock_act.setToolTip(self.translator.tr("lock_action_tooltip"))
        self.exit_act.setText(self.translator.tr("exit_action_tooltip"))
        self.exit_act.setToolTip(self.translator.tr("exit_action_tooltip"))
        self.about_act.setText(self.translator.tr("about_action_tooltip")) # About typically only text
        self.backup_act.setText(self.translator.tr("backup_vault_menu"))
        self.backup_act.setToolTip(self.translator.tr("backup_vault_tooltip"))
        self.restore_act.setText(self.translator.tr("restore_vault_menu"))
        self.restore_act.setToolTip(self.translator.tr("restore_vault_tooltip"))
        self.check_duplicates_act.setText(self.translator.tr("check_duplicates_menu"))
        self.check_duplicates_act.setToolTip(self.translator.tr("check_duplicates_tooltip"))
        
        # Menus
        self.file_menu.setTitle(self.translator.tr("menu_file"))
        self.edit_menu.setTitle(self.translator.tr("menu_edit"))
        self.tools_menu.setTitle(self.translator.tr("menu_tools"))
        self.help_menu.setTitle(self.translator.tr("menu_help"))
        
        self.toolbar.setWindowTitle(self.translator.tr("main_toolbar_title"))
        self.status_bar.showMessage(self.translator.tr("status_ready")) # Default status

        # Update layout direction for the main window itself
        direction = Qt.RightToLeft if self.translator.locale == 'ar' else Qt.LeftToRight
        self.setLayoutDirection(direction)
        if hasattr(self, 'menu_bar'): # MenuBar might need explicit direction
             self.menu_bar.setLayoutDirection(direction)
        # Search layout might need explicit re-alignment depending on complexity
        # Table headers also respect layoutDirection set on QApplication or self.accounts_table

    def lock_vault(self):
        print("Locking vault...")
        self.auto_lock_manager.stop() # Stop auto-lock timer
        self.master_key_string = None
        self.vault_data = {"accounts": [], "config": {}} # Clear sensitive data
        self.populate_accounts_table() # Clear table display
        self.update_button_states() # Disable most buttons
        self.status_bar.showMessage(self.translator.tr("status_vault_locked"))
        
        self.hide() # Hide main window
        self.request_relogin.emit() # Signal to controller
        # Controller will typically close this window instance and show login
        # self.close() # Can also be called here if controller doesn't manage closure

    def show_about_dialog(self):
        QMessageBox.about(self, self.translator.tr("about_title"),
                          f"<b>{APP_NAME}</b> v{APP_VERSION}<br><br>"
                          f"{self.translator.tr('about_text')}<br><br>"
                          f"Using Python & PyQt5<br>"
                          f"Cryptography via 'cryptography' library.")

    def closeEvent(self, event): # Standard Qt event handler
        print("Closing MindVault main window.")
        self.auto_lock_manager.stop() # Ensure timer is stopped
        # Clearing sensitive data is good practice, though app is exiting
        self.master_key_string = None 
        self.vault_data = {}
        # The request_relogin signal is not appropriate here as it's a full close
        event.accept() # Allow window to close

    def show_duplicate_password_checker(self):
        if not self.master_key_string:
            QMessageBox.information(self, self.translator.tr("info_title"), self.translator.tr("unlock_vault_first"))
            return
        
        duplicates = find_all_duplicate_passwords(self.vault_data.get("accounts", []))
        # DuplicateCheckerDialog is from features, assumed to be a QDialog
        dialog = DuplicateCheckerDialog(self.translator, duplicates, self) 
        dialog.exec_()

    def perform_backup(self):
        if not self.master_key_string:
            QMessageBox.information(self, self.translator.tr("info_title"), self.translator.tr("unlock_vault_first"))
            return
        self.backup_restore_handler.backup_vault()

    def perform_restore(self):
        # Restore can be initiated even if locked, as it will force a re-login.
        if self.backup_restore_handler.restore_vault(): # This shows its own messages
            self.status_bar.showMessage(self.translator.tr("status_vault_restored_relogin"), 5000)
            self.lock_vault() # Force re-login with potentially new/restored vault
            # The lock_vault method will emit request_relogin