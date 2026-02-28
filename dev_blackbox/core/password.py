from functools import lru_cache

from pwdlib import PasswordHash


class PasswordService:

    def __init__(self):
        self.password_hash = PasswordHash.recommended()

    def hash(self, raw_password: str) -> str:
        return self.password_hash.hash(raw_password)

    def verify(self, raw_password: str, hashed_password: str) -> bool:
        return self.password_hash.verify(raw_password, hashed_password)


@lru_cache
def get_password_service() -> PasswordService:
    return PasswordService()
