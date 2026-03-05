from datetime import datetime, timezone

from auth.user import User
from core.security import JWT
from .schemas import Token, AccessToken

__all__ = [
    "TokenUtils",
]


class TokenUtils:
    @staticmethod
    def encode_access_token(access_token: AccessToken) -> str:
        to_encode = access_token.to_payload()
        encoded_jwt = JWT.encode(to_encode)
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> AccessToken:
        payload = JWT.decode(token)
        return AccessToken(**payload)

    @staticmethod
    def create_token(user: User) -> Token:  # todo:后续添加预加载,对链式查询进行加速
        token_expires_delta = user.access_token_expires_timedelta
        scopes_set: set[str] = set()
        for permission_group in user.permission_groups:
            for scope in permission_group.scopes:
                scopes_set.add(scope.content)
        access_token = AccessToken(
            sub=user.id,
            exp=datetime.now(timezone.utc) + token_expires_delta,
            scope=" ".join(sorted(scopes_set)),
        )
        token = TokenUtils.encode_access_token(access_token)
        return Token(access_token=token, token_type='bearer')
