import base64
import os
from functools import lru_cache

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from dev_blackbox.core.config import get_settings

_SALT_LEN = 16
_NONCE_LEN = 12
_TAG_LEN = 16


class EncryptService:
    """
    AES-256-GCM
    key, pepper, salt 사용
    """

    def __init__(self, key: str, pepper: str):
        self._key = key.encode()
        self._pepper = pepper.encode()

    def encrypt(self, plaintext: str) -> str:
        salt = os.urandom(_SALT_LEN)
        derived_key = self._derive_key(salt)

        nonce = os.urandom(_NONCE_LEN)
        cipher = Cipher(algorithms.AES(derived_key), modes.GCM(nonce))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()

        # salt(16) + nonce(12) + tag(16) + ciphertext
        combined = salt + nonce + encryptor.tag + ciphertext
        return base64.urlsafe_b64encode(combined).decode()

    def decrypt(self, encrypted: str) -> str:
        combined = base64.urlsafe_b64decode(encrypted.encode())

        salt = combined[:_SALT_LEN]
        nonce = combined[_SALT_LEN : _SALT_LEN + _NONCE_LEN]
        tag = combined[_SALT_LEN + _NONCE_LEN : _SALT_LEN + _NONCE_LEN + _TAG_LEN]
        ciphertext = combined[_SALT_LEN + _NONCE_LEN + _TAG_LEN :]

        derived_key = self._derive_key(salt)

        cipher = Cipher(algorithms.AES(derived_key), modes.GCM(nonce, tag))
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode()

    def _derive_key(self, salt: bytes) -> bytes:
        kdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=self._pepper,
        )
        return kdf.derive(self._key)


@lru_cache
def get_encrypt_service() -> EncryptService:
    settings = get_settings()
    return EncryptService(
        key=settings.encryption.key,
        pepper=settings.encryption.pepper,
    )
