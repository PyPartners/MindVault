# features/two_factor_auth.py
import os
import base64
import qrcode
import pyotp
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QCheckBox, QScrollArea, QWidget, QApplication, QSizePolicy, QDialogButtonBox
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt


class TwoFactorSetupDialog(QDialog):
    def __init__(self, translator, app_name, username, existing_secret=None, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.app_name = app_name
        self.username_for_issuer = username 
        self.setWindowTitle(self.translator.tr("2fa_setup_title"))
        self.setMinimumWidth(450)

        self.secret_key = existing_secret or pyotp.random_base32()
        self.totp = pyotp.TOTP(self.secret_key)

        layout = QVBoxLayout(self)

        info_label = QLabel(self.translator.tr("2fa_setup_instructions"))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.generate_qr_code()
        layout.addWidget(self.qr_label)

        
        secret_key_layout = QHBoxLayout()
        secret_key_label = QLabel(self.translator.tr("2fa_secret_key_label"))
        self.secret_key_display = QLineEdit(self.secret_key)
        self.secret_key_display.setReadOnly(True)
        self.copy_secret_button = QPushButton(self.translator.tr("copy_button_action"))
        self.copy_secret_button.clicked.connect(self.copy_secret_key_to_clipboard)
        
        secret_key_layout.addWidget(secret_key_label)
        secret_key_layout.addWidget(self.secret_key_display, 1)
        secret_key_layout.addWidget(self.copy_secret_button)
        layout.addLayout(secret_key_layout)

        layout.addWidget(QLabel(self.translator.tr("2fa_enter_code_label")))
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("000000")
        self.code_edit.setMaxLength(6)
        layout.addWidget(self.code_edit)

        self.verify_button = QPushButton(self.translator.tr("2fa_verify_and_enable_button"))
        self.verify_button.clicked.connect(self.verify_and_accept)
        layout.addWidget(self.verify_button)

        self.cancel_button = QPushButton(self.translator.tr("cancel_button"))
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

    def generate_qr_code(self):
        provisioning_uri = self.totp.provisioning_uri(
            name=self.username_for_issuer, 
            issuer_name=self.app_name
        )
        img = qrcode.make(provisioning_uri)
        
        qr_img_path = "temp_qr.png" 
        img.save(qr_img_path)
        pixmap = QPixmap(qr_img_path)
        if os.path.exists(qr_img_path):
            os.remove(qr_img_path)

        self.qr_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))


    def copy_secret_key_to_clipboard(self):
        QApplication.clipboard().setText(self.secret_key)
        QMessageBox.information(self, self.translator.tr("info_title"),
                                self.translator.tr("2fa_secret_key_copied"))

    def verify_and_accept(self):
        entered_code = self.code_edit.text().strip()
        if not entered_code.isdigit() or len(entered_code) != 6:
            QMessageBox.warning(self, self.translator.tr("error_title"), self.translator.tr("2fa_invalid_code_format"))
            return

        if self.totp.verify(entered_code):
            QMessageBox.information(self, self.translator.tr("info_title"), self.translator.tr("2fa_enabled_success"))
            self.accept()
        else:
            QMessageBox.warning(self, self.translator.tr("error_title"), self.translator.tr("2fa_verification_failed"))

    def get_secret_key(self):
        return self.secret_key

class TwoFactorVerifyDialog(QDialog):
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setWindowTitle(self.translator.tr("2fa_verify_title"))
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.translator.tr("2fa_enter_code_prompt")))

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("000000")
        self.code_edit.setMaxLength(6)
        layout.addWidget(self.code_edit)
        self.code_edit.returnPressed.connect(self.accept)


        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.translator.tr("verify_button")) # Or "Login", "Unlock"
        self.button_box.button(QDialogButtonBox.Cancel).setText(self.translator.tr("cancel_button"))
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        self.code_edit.setFocus()


    def get_entered_code(self):
        return self.code_edit.text().strip()


def verify_totp_code(secret_key: str, code: str) -> bool:
    """Verifies a TOTP code against a secret key."""
    if not secret_key or not code:
        return False
    totp = pyotp.TOTP(secret_key)
    return totp.verify(code)


def store_2fa_secret_in_vault(vault_data: dict, secret: str | None):
    """Stores or removes the 2FA secret in the vault data structure."""
    if "config" not in vault_data:
        vault_data["config"] = {}
    if secret:
        vault_data["config"]["2fa_secret"] = secret
    elif "2fa_secret" in vault_data["config"]:
        del vault_data["config"]["2fa_secret"]

def get_2fa_secret_from_vault(vault_data: dict) -> str | None:
    """Retrieves the 2FA secret from the vault data structure."""
    return vault_data.get("config", {}).get("2fa_secret")

def is_2fa_enabled(vault_data: dict) -> bool:
    """Checks if 2FA is configured in the vault."""
    return bool(get_2fa_secret_from_vault(vault_data))