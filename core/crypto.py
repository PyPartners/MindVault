import os
import json
import base64
import hashlib
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

# Import constants
from constants import (
    PBKDF2_ITERATIONS,
    SALT_SIZE,
    AES_NONCE_SIZE,
    AES_TAG_SIZE
)
from .utils import ensure_dir # from mindvault.core.utils

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend()
    )
    return kdf.derive(password.encode('utf-8'))

def encrypt_data(data: dict, derived_key: bytes) -> bytes | None:
    try:
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        aesgcm = AESGCM(derived_key)
        nonce = os.urandom(AES_NONCE_SIZE)
        encrypted_data = aesgcm.encrypt(nonce, json_data, None)
        return nonce + encrypted_data
    except Exception as e:
        print(f"Encryption Error (AESGCM): {e}")
        return None

def decrypt_data(encrypted_blob: bytes, master_password: str) -> dict | None:
    try:
        salt = encrypted_blob[:SALT_SIZE]
        nonce = encrypted_blob[SALT_SIZE:SALT_SIZE + AES_NONCE_SIZE]
        ciphertext_with_tag = encrypted_blob[SALT_SIZE + AES_NONCE_SIZE:]
        if len(nonce) != AES_NONCE_SIZE or len(salt) != SALT_SIZE:
             print("Decryption Error: Invalid length for salt or nonce.")
             return None
        derived_key = derive_key(master_password, salt)
        aesgcm = AESGCM(derived_key)
        decrypted_data = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
        return json.loads(decrypted_data.decode('utf-8'))
    except Exception: # Catch more general exceptions for decryption failure (like InvalidTag)
        # print(f"Decryption Error: {e}") # Avoid printing specific crypto errors to user
        return None

def encrypt_vault(data: dict, master_password: str) -> bytes | None:
    # ensure_dir is called by MainWindow.save_vault directly on VAULT_DIR
    try:
        salt = os.urandom(SALT_SIZE)
        derived_key = derive_key(master_password, salt)
        nonce_and_ciphertext = encrypt_data(data, derived_key)
        if nonce_and_ciphertext:
            return salt + nonce_and_ciphertext
        else:
            print("Vault Encryption Error: encrypt_data failed.")
            return None
    except Exception as e:
         print(f"Vault Encryption Wrapper Error: {e}")
         return None