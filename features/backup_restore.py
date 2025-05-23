# features/backup_restore.py
import os
import shutil
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from datetime import datetime


class BackupRestoreHandler:
    def __init__(self, vault_file_path: str, translator, parent_widget=None):
        self.vault_file_path = vault_file_path
        self.translator = translator
        self.parent_widget = parent_widget # For dialog modality

    def backup_vault(self):
        if not os.path.exists(self.vault_file_path):
            QMessageBox.warning(
                self.parent_widget,
                self.translator.tr("warning_title"),
                self.translator.tr("backup_no_vault_to_backup")
            )
            return False

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_backup_name = f"mindvault_backup_{timestamp}.enc"
        
        # Suggest a directory for backups (e.g., user's Documents)
        # For simplicity, start with current dir or let user choose freely
        backup_dir = os.path.dirname(self.vault_file_path) # Suggest same dir as vault initially
        
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent_widget,
            self.translator.tr("backup_dialog_title"),
            os.path.join(backup_dir, default_backup_name),
            self.translator.tr("backup_file_filter") + " (*.enc)"
        )

        if file_path:
            try:
                shutil.copy2(self.vault_file_path, file_path) # copy2 preserves metadata
                QMessageBox.information(
                    self.parent_widget,
                    self.translator.tr("info_title"),
                    self.translator.tr("backup_success_message", file_path)
                )
                return True
            except Exception as e:
                QMessageBox.critical(
                    self.parent_widget,
                    self.translator.tr("error_title"),
                    self.translator.tr("backup_fail_message", str(e))
                )
        return False

    def restore_vault(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent_widget,
            self.translator.tr("restore_dialog_title"),
            os.path.dirname(self.vault_file_path), # Suggest same dir
            self.translator.tr("backup_file_filter") + " (*.enc);;" + self.translator.tr("all_files_filter") + " (*)"
        )

        if file_path:
            reply = QMessageBox.warning(
                self.parent_widget,
                self.translator.tr("warning_title"),
                self.translator.tr("restore_warning_overwrite"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                try:
                    # Ensure vault directory exists (should, but good check)
                    vault_dir = os.path.dirname(self.vault_file_path)
                    if not os.path.exists(vault_dir):
                        os.makedirs(vault_dir)
                        
                    shutil.copy2(file_path, self.vault_file_path)
                    QMessageBox.information(
                        self.parent_widget,
                        self.translator.tr("info_title"),
                        self.translator.tr("restore_success_message") + "\n" +
                        self.translator.tr("restore_requires_relogin_message")
                    )
                    return True # Indicates success, main app should handle re-lock
                except Exception as e:
                    QMessageBox.critical(
                        self.parent_widget,
                        self.translator.tr("error_title"),
                        self.translator.tr("restore_fail_message", str(e))
                    )
        return False