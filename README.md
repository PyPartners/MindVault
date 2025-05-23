# MindVault 🔑

**MindVault** is a secure, offline-first password manager with a graphical user interface built using Python and PyQt5. It aims to provide a clean, modern, and safe way to store and manage your passwords locally—without any internet dependencies.

<p align="center">
  <img src="https://i.ibb.co/1tpbx8Nq/app-icon.png" alt="MindVault Logo" width="200"/>
</p>

---

## ✨ Features

- 🔐 **Strong Encryption:** Uses AES-256 GCM for encryption. The encryption key is derived from your master password using PBKDF2HMAC with SHA256 and 390,000 iterations.
- 💾 **Local Storage:** Your encrypted data is stored in `data/vault.enc`. Nothing leaves your device.
- 🖼️ **User-Friendly GUI:** Clean and intuitive interface powered by PyQt5 with support for light and dark modes.
- 📁 **Account Management:**
  - Add, edit, and delete entries (site, username, password, notes).
  - Toggle visibility of the password field.
- 🔍 **Quick Search:** Instantly filter accounts by website, username, or notes.
- 📋 **Clipboard Copy:** One-click copy of password fields.
- 🔑 **Master Password:** One strong password unlocks the entire vault.
  - Password strength indicator included during creation.
- 🔒 **Auto Lock:** Vault automatically locks after inactivity.
- ⚠️ **Duplicate Detection:** Notifies you if you're reusing the same password.
- 🔐 **Password Generator:** Built-in generator for strong, customizable passwords.
- 📈 **Strength Indicator:** Dynamic password strength meter.
- 📦 **Backup & Restore:** Easily create and restore backups of your vault.
- 🔐 **2FA (TOTP) Support:** Add a second layer of authentication with time-based one-time passwords.
- 🌍 **Multi-language:** Supports English and Arabic. Additional languages can be added via JSON files.
- 🎨 **Appearance Settings:** Choose from light/dark themes, select font and size.
- ⚙️ **Portable Settings:** Stored in `settings.json`.

---

## ⚙️ Requirements

- Python 3.7 or newer
- Install dependencies with:

```bash
pip install PyQt5 cryptography pyotp qrcode
````

---

## 🚀 Installation and Running

1. **Clone the repository:**

```bash
git clone https://github.com/PyPartners/MindVault.git
cd MindVault
```

2. **(Optional) Create a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate    # On Linux/macOS
# venv\Scripts\activate     # On Windows
```

3. **Run the application:**

```bash
python main.py
```

4. **On first launch:**

   * You'll be prompted to create a **master password**.
   * The program will generate required folders (`data/`, `lang/`, `icons/`) and default files if missing.

---

## 📁 Project Structure

```
MindVault/
│
├── main.py                # Entry point
├── app_icon.png           # Application icon
├── constants.py
├── settings.json          # User preferences (auto-generated)
├── THANKS.txt
├── requirements.txt
├── __init__.py
│
├── core/                  # Core logic and utilities
│   ├── crypto.py
│   ├── settings.py
│   ├── translation.py
│   └── utils.py
│
├── features/              # Optional functionality
│   ├── auto_lock.py
│   ├── backup_restore.py
│   ├── duplicate_checker.py
│   ├── password_generator.py
│   ├── strength_indicator.py
│   └── two_factor_auth.py
│
├── icons/                 # UI Icons
│   ├── add.png
│   ├── edit.png
│   ├── delete.png
│   ├── copy.png
│   ├── settings.png
│   ├── lock.png
│   ├── exit.png
│   ├── app_icon.png
│   ├── backup.png
│   ├── restore.png
│   ├── check.png
│   └── check_dark.png
│
├── lang/                  # Language JSON files
│   ├── en.json
│   └── ar.json
│
├── ui/                    # GUI code
│   ├── main_window.py
│   ├── dialogs.py
│   └── styles.py
│
└── project_map/           # Documentation and architecture
    ├── MindVault.md
    ├── mindvault_architecture.png
    └── mindvault_architecture_english.png
```

---

## 🔐 Security Considerations

* **Master Password:** It is *never* stored. It's used to derive the encryption key. Losing it = losing access forever.
* **Vault File:** Always stored locally, encrypted. You control your data.
* **Backups:** Create secure, encrypted backups of `vault.enc` and `settings.json`.
* **Clipboard:** Passwords copied to clipboard are not auto-cleared *yet* (feature in progress).

---

## 📌 To-Do / Planned Features

* [x] Strong password generator
* [x] Auto-lock on inactivity
* [x] Duplicate password warnings
* [x] Password strength meter
* [x] Vault backup and restore
* [x] 2FA (TOTP) authentication

---

## 🤝 Contributing

1. Fork the repository
2. Create a branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'Add AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Submit a Pull Request

---

## 📜 License

This project is currently **unlicensed**.
