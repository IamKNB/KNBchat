from typing import Any

import jwt
from pwdlib import PasswordHash

from core.config import get_settings

password_hasher = PasswordHash.recommended()
settings = get_settings()


class Password:
    @staticmethod
    def hash(password):
        return password_hasher.hash(password)

    @staticmethod
    def verify_hash(password: str, hashed_password: str) -> bool:
        return password_hasher.verify(password, hashed_password)


# todo:完成验证码部分

class JWT:
    @staticmethod
    def decode(jwt_token: str) -> dict[str, Any]: #todo:检查这个返回值Any,是否可以写作str
        return jwt.decode(jwt_token, settings.jwt_secret_key, algorithms=settings.jwt_algorithm,
                          options={"require": ["sub", "exp"]}, leeway=30, )

    @staticmethod
    def encode(to_encode: dict) -> str:
        return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
