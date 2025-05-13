# MindVault 🔑

**MindVault** is a secure, local (offline) password manager with a graphical user interface, built using Python and PyQt5. It aims to provide a simple and secure way to store and manage your passwords.

<!-- <p align="center">
  <img src="https://i.ibb.co/1tpbx8Nq/app-icon.png" alt="MindVault Logo" width="200"/>
</p> -->

## ✨ Features

*   **Strong Encryption:** All your data is encrypted using AES-256 GCM. The encryption key is derived from your master password using PBKDF2HMAC (SHA256) with a high iteration count (`390000`) and a unique salt.
*   **Local Storage:** All your data is stored locally in an encrypted file (`data/vault.enc`). Nothing is sent over the internet.
*   **User-Friendly GUI:** Built with PyQt5, supporting light and dark themes.
*   **Account Management:**
    *   Add, edit, and delete accounts (site, username, password, notes).
    *   Show or hide the password in the input form.
*   **Quick Search:** Easily filter accounts based on site name, username, or notes.
*   **Password Copying:** Copy the selected password to the clipboard with a single click.
*   **Single Master Password:** One master password unlocks your entire password vault.
    *   Password strength indicator during creation.
*   **Vault Locking:** Ability to lock the vault, requiring re-entry of the master password.
*   **Multi-language Support:** Currently supports English and Arabic (with the possibility to add other languages via JSON files).
*   **Appearance Customization:**
    *   Themes (light/dark).
    *   Select application font and size.
*   **Portable Settings:** User settings (language, theme, font) are saved in `settings.json`.

## ⚙️ Requirements

*   Python 3.7 or newer.
*   The following libraries (can be installed via `pip`):
    *   `PyQt5`
    *   `cryptography`

## 🚀 Installation and Running

1.  **Clone the repository (or download the files):**
    ```bash
    git clone https://github.com/imsara-py/MindVault.git
    cd MindVault
    ```

2.  **(Optional but recommended) Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate    # On Windows
    ```

3.  **Install dependencies:**
    ```bash
    pip install PyQt5 cryptography
    ```

4.  **Run the program:**
    The program will create necessary directories (`data`, `lang`, `icons`) and files (default language files, initial settings file, dummy icons if they don't exist) on its first run.
    *   Ensure you have an `app_icon.png` file in the root directory or modify the path in the code if needed.
    *   If icons are not present in the `icons` folder, the program will create empty placeholder files. It's best to replace these with actual icons.

    ```bash
    python main.py
    ```

5.  **On first run:**
    *   You will be prompted to create a **Master Password**. This password is **extremely important**. If you forget it, you will not be able to access your stored data. **There is no way to recover it.**
    *   After creating the master password, the encrypted vault file will be created.

## 📁 File and Folder Structure

```
MindVault/
│
├── main.py     # Main program script
├── app_icon.png            # Main application icon
├── settings.json           # Application settings file (auto-generated)
│
├── data/
│   └── vault.enc           # Encrypted vault file (auto-generated)
│
├── lang/                     # Translation files directory (auto-generated)
│   ├── en.json             # English translation file (auto-generated)
│   └── ar.json             # Arabic translation file (auto-generated)
│
└── icons/                    # Directory for UI icons (auto-generated)
    ├── add.png
    ├── edit.png
    ├── delete.png
    ├── copy.png
    ├── settings.png
    ├── lock.png
    └── exit.png
```

## 🔐 Security Considerations

*   **Master Password:** It's the key to everything. Choose a strong, unique password and don't share it with anyone. Forgetting it means permanently losing access to all your data.
*   **Local Storage:** Your data never leaves your device. This means you are responsible for the security of your device and the vault file (`vault.enc`).
*   **Backups:** It is strongly recommended to regularly back up your `vault.enc` file and `settings.json` file to a secure location (e.g., an encrypted external drive).
*   **Cryptography Library:** The program relies on the well-tested and trusted `cryptography` library for handling encryption operations.

## 📝 To-Do List / Potential Future Features

*   [ ] Strong password generator.
*   [ ] Auto-lock vault after a period of inactivity.
*   [ ] Option to import/export data (in an encrypted format or protected CSV/JSON).
*   [ ] Support for more themes or full color customization.
*   [ ] More detailed password strength indicator when adding/editing an account.
*   [ ] Automatically clear clipboard after a certain time when a password is copied (the code has a starting point for this feature).

## 🤝 Contributing

Contributions are welcome! If you'd like to contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push your changes to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## 📜 License

This project is currently unlicensed.
