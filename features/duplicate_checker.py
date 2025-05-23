# features/duplicate_checker.py
from collections import defaultdict
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
    QDialogButtonBox, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt

def find_all_duplicate_passwords(accounts_list: list) -> dict:
    """
    Finds all passwords used by more than one account.
    Returns: {password: [site_name1, site_name2, ...]}
    """
    password_map = defaultdict(list)
    for account in accounts_list:
        password = account.get("password")
        site_name = account.get("site", "Unknown")
        if password: # Only consider accounts with passwords
            password_map[password].append(site_name)

    duplicates = {
        password: sites for password, sites in password_map.items() if len(sites) > 1
    }
    return duplicates

def check_for_duplicate_password(new_password: str, current_account_id: str | None,
                                 all_accounts: list, translator) -> bool:
    """
    Checks if new_password is used by any *other* account.
    Returns True if it's a duplicate and user chose not to proceed, False otherwise.
    """
    if not new_password: # Empty password is not considered for duplication check here
        return False

    for account in all_accounts:
        if account.get("id") == current_account_id: # Skip self
            continue
        if account.get("password") == new_password:
            site_names = [acc.get("site", translator.tr("unknown_site")) for acc in all_accounts if acc.get("password") == new_password and acc.get("id") != current_account_id]

            reply = QMessageBox.question(
                None, # No parent needed for a simple warning
                translator.tr("warning_title"),
                translator.tr("duplicate_password_save_warning", new_password, "\n - ".join(site_names)),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No  # Default to No (don't save with duplicate)
            )
            return reply == QMessageBox.No # True means user chose "No", so stop saving
    return False # Not a duplicate or user chose "Yes"

class DuplicateCheckerDialog(QDialog):
    def __init__(self, translator, duplicate_data: dict, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setWindowTitle(self.translator.tr("duplicate_passwords_title"))
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        if not duplicate_data:
            label = QLabel(self.translator.tr("no_duplicate_passwords_found"))
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
        else:
            label = QLabel(self.translator.tr("duplicate_passwords_found_info"))
            layout.addWidget(label)

            self.list_widget = QListWidget()
            for password, sites in duplicate_data.items():
                # Mask part of the password for display
                masked_password = password[:3] + "****" + password[-2:] if len(password) > 5 else password
                item_text = self.translator.tr("password_display_mask", masked_password)
                item = QListWidgetItem(item_text)
                self.list_widget.addItem(item)
                
                sites_text = "\n".join([f"  - {site}" for site in sites])
                details_item = QListWidgetItem(sites_text)
                details_item.setFlags(details_item.flags() & ~Qt.ItemIsSelectable) # Not selectable
                self.list_widget.addItem(details_item)
                self.list_widget.addItem("") # Spacer

            layout.addWidget(self.list_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.button(QDialogButtonBox.Ok).setText(self.translator.tr("ok_button"))
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)