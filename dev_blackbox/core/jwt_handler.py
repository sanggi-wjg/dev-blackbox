from datetime import timedelta
from functools import lru_cache

import jwt

from dev_blackbox.core.config import get_settings
from dev_blackbox.util.datetime_util import get_datetime_utc_now


class JwtService:

    def __init__(self, secret_key: str, algorithm: str, expiration_minutes: int):
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._expiration_minutes = expiration_minutes

    def create_token(self, data: dict) -> str:
        to_encode = data.copy()
        to_encode.update(
            {
                "exp": get_datetime_utc_now() + timedelta(minutes=self._expiration_minutes),
            }
        )
        return jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)

    def decode_token(self, token: str) -> dict:
        return jwt.decode(token, self._secret_key, algorithms=[self._algorithm])


@lru_cache
def get_jwt_service() -> "JwtService":
    auth_secrets = get_settings().auth
    return JwtService(
        secret_key=auth_secrets.secret_key,
        algorithm=auth_secrets.algorithm,
        expiration_minutes=auth_secrets.access_token_expire_minutes,
    )
