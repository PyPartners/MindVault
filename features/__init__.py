# features/__init__.py
from .strength_indicator import check_password_strength_util
from .password_generator import PasswordGeneratorDialog
from .auto_lock import AutoLockManager
from .duplicate_checker import (
    DuplicateCheckerDialog,
    check_for_duplicate_password,
    find_all_duplicate_passwords
)
from .backup_restore import BackupRestoreHandler
from .two_factor_auth import ( 
    TwoFactorSetupDialog,
    TwoFactorVerifyDialog,
    verify_totp_code,
    store_2fa_secret_in_vault,
    get_2fa_secret_from_vault,
    is_2fa_enabled
)


__all__ = [
    "check_password_strength_util",
    "PasswordGeneratorDialog",
    "AutoLockManager",
    "DuplicateCheckerDialog",
    "check_for_duplicate_password",
    "find_all_duplicate_passwords",
    "BackupRestoreHandler",
    "TwoFactorSetupDialog", 
    "TwoFactorVerifyDialog", 
    "verify_totp_code",      
    "store_2fa_secret_in_vault", 
    "get_2fa_secret_from_vault", 
    "is_2fa_enabled"         
]