from functools import lru_cache
from pwdlib import PasswordHash


class PasswordService:

    def __init__(self):
        self.password_hash = PasswordHash.recommended()

    def hash_password(self, password: str) -> str:
        return self.password_hash.hash(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return self.password_hash.verify(password, hashed_password)


@lru_cache
def get_password_service() -> PasswordService:
    return PasswordService()
