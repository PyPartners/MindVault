# features/password_generator.py
import string
import secrets
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QCheckBox,
    QPushButton, QHBoxLayout, QLabel, QSpinBox, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt

class PasswordGeneratorDialog(QDialog):
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.generated_password = ""

        self.setWindowTitle(self.translator.tr("generate_password_title"))
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.length_spinbox = QSpinBox()
        self.length_spinbox.setRange(8, 128)
        self.length_spinbox.setValue(16)
        form_layout.addRow(self.translator.tr("length_label"), self.length_spinbox)

        self.uppercase_checkbox = QCheckBox(self.translator.tr("use_uppercase_label"))
        self.uppercase_checkbox.setChecked(True)
        form_layout.addRow(self.uppercase_checkbox)

        self.lowercase_checkbox = QCheckBox(self.translator.tr("use_lowercase_label"))
        self.lowercase_checkbox.setChecked(True)
        form_layout.addRow(self.lowercase_checkbox)

        self.digits_checkbox = QCheckBox(self.translator.tr("use_digits_label"))
        self.digits_checkbox.setChecked(True)
        form_layout.addRow(self.digits_checkbox)

        self.symbols_checkbox = QCheckBox(self.translator.tr("use_symbols_label"))
        self.symbols_checkbox.setChecked(True)
        form_layout.addRow(self.symbols_checkbox)

        layout.addLayout(form_layout)

        self.password_display_edit = QLineEdit()
        self.password_display_edit.setReadOnly(True)
        self.password_display_edit.setPlaceholderText(self.translator.tr("generated_password_placeholder"))
        layout.addWidget(QLabel(self.translator.tr("generated_password_label")))
        layout.addWidget(self.password_display_edit)

        button_layout = QHBoxLayout()
        self.generate_button = QPushButton(self.translator.tr("generate_button_action"))
        self.copy_button = QPushButton(self.translator.tr("copy_button_action"))
        self.use_button = QPushButton(self.translator.tr("use_password_button"))
        self.cancel_button = QPushButton(self.translator.tr("cancel_button"))

        self.generate_button.clicked.connect(self.generate_and_display_password)
        self.copy_button.clicked.connect(self.copy_password)
        self.use_button.clicked.connect(self.accept) # accept will pass generated_password
        self.cancel_button.clicked.connect(self.reject)

        self.copy_button.setEnabled(False)
        self.use_button.setEnabled(False)

        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.copy_button)
        layout.addLayout(button_layout)

        dialog_buttons_layout = QHBoxLayout()
        dialog_buttons_layout.addStretch()
        dialog_buttons_layout.addWidget(self.use_button)
        dialog_buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(dialog_buttons_layout)

        self.generate_and_display_password() # Generate one on open

    def generate_and_display_password(self):
        length = self.length_spinbox.value()
        use_uppercase = self.uppercase_checkbox.isChecked()
        use_lowercase = self.lowercase_checkbox.isChecked()
        use_digits = self.digits_checkbox.isChecked()
        use_symbols = self.symbols_checkbox.isChecked()

        character_set = ""
        if use_uppercase:
            character_set += string.ascii_uppercase
        if use_lowercase:
            character_set += string.ascii_lowercase
        if use_digits:
            character_set += string.digits
        if use_symbols:
            character_set += string.punctuation

        if not character_set:
            QMessageBox.warning(self, self.translator.tr("error_title"),
                                self.translator.tr("generator_no_charset_selected"))
            self.generated_password = ""
            self.password_display_edit.setText("")
            self.copy_button.setEnabled(False)
            self.use_button.setEnabled(False)
            return

        # Ensure password meets criteria if possible (at least one of each selected type)
        # This is a bit more complex for truly random, but a good practice
        password_list = []
        if use_uppercase: password_list.append(secrets.choice(string.ascii_uppercase))
        if use_lowercase: password_list.append(secrets.choice(string.ascii_lowercase))
        if use_digits: password_list.append(secrets.choice(string.digits))
        if use_symbols: password_list.append(secrets.choice(string.punctuation))
        
        remaining_length = length - len(password_list)
        if remaining_length < 0: # If length is too small for selected criteria
             QMessageBox.warning(self, self.translator.tr("error_title"),
                                 self.translator.tr("generator_length_too_short_for_criteria"))
             self.generated_password = ""
             self.password_display_edit.setText("")
             self.copy_button.setEnabled(False)
             self.use_button.setEnabled(False)
             return


        for _ in range(remaining_length):
            password_list.append(secrets.choice(character_set))

        secrets.SystemRandom().shuffle(password_list) # Shuffle to make it random
        self.generated_password = "".join(password_list)
        self.password_display_edit.setText(self.generated_password)
        self.copy_button.setEnabled(True)
        self.use_button.setEnabled(True)


    def copy_password(self):
        if self.generated_password:
            QApplication.clipboard().setText(self.generated_password)
            QMessageBox.information(self, self.translator.tr("info_title"),
                                    self.translator.tr("password_copied_to_clipboard"))

    def get_generated_password(self):
        return self.generated_password

    @staticmethod
    def generate_password(translator, parent=None):
        dialog = PasswordGeneratorDialog(translator, parent)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_generated_password()
        return None