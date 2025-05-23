# features/auto_lock.py
from PyQt5.QtCore import QObject, QTimer, QEvent, QCoreApplication
from PyQt5.QtWidgets import QApplication

class AutoLockManager(QObject):
    def __init__(self, main_window, settings_manager, translator, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.settings_manager = settings_manager
        self.translator = translator
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._handle_timeout)
        self.is_active = False
        self.timeout_minutes = 0
        self._load_settings()

    def _load_settings(self):
        self.timeout_minutes = self.settings_manager.get("auto_lock_timeout", 0) # 0 for disabled
        if self.timeout_minutes > 0:
            self.timer.setInterval(self.timeout_minutes * 60 * 1000) # ms
        else:
            self.timer.stop()

    def start(self):
        self._load_settings()
        if self.timeout_minutes > 0:
            self.is_active = True
            self.timer.start()
            QApplication.instance().installEventFilter(self)
            print(f"Auto-lock started: {self.timeout_minutes} minutes.")

    def stop(self):
        self.is_active = False
        self.timer.stop()
        try:
            QApplication.instance().removeEventFilter(self)
        except RuntimeError: # Can happen if app is closing
            pass
        print("Auto-lock stopped.")

    def reset_timer(self):
        if self.is_active and self.timeout_minutes > 0:
            self.timer.start() # Restart with the same interval

    def update_settings(self):
        was_active = self.is_active
        if was_active:
            self.stop()
        self._load_settings()
        if self.timeout_minutes > 0 or (was_active and self.timeout_minutes == 0) : # Re-start if it was active or became active
             if self.main_window and self.main_window.master_key_string: # Only start if vault is unlocked
                self.start()


    def _handle_timeout(self):
        if self.is_active and self.main_window:
            print("Auto-lock timeout. Locking vault.")
            self.main_window.status_bar.showMessage(self.translator.tr("status_auto_locked"), 5000)
            self.main_window.lock_vault() # This will also stop the autolock manager via main_window logic

    def eventFilter(self, obj, event):
        # Reset timer on user activity
        # Check event types that indicate user activity
        if event.type() in [
            QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.MouseButtonRelease,
            QEvent.KeyPress, QEvent.KeyRelease, QEvent.Wheel
        ]:
            self.reset_timer()
        return super().eventFilter(obj, event)