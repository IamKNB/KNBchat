from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import SecurityScopes
from jwt import InvalidTokenError
from pydantic import ValidationError

from auth.user import User
from db import SessionDep
from .jwt import TokenUtils
from .oauth2 import oauth2_schema


def get_user(session: SessionDep, security_scopes: SecurityScopes,
             token: Annotated[str, Depends(oauth2_schema)]) -> User:
    """
    本函数是Depend函数
    权限不够,token失效,user不存在等错误 都会直接rise HTTPException
    """
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail="Could not validate credentials",
                                          headers={"WWW-Authenticate": authenticate_value}, )

    try:
        access_token = TokenUtils.decode_access_token(token)
    except (InvalidTokenError, ValidationError):
        raise credentials_exception
    user: User | None = session.get(User, access_token.sub)
    if not user:
        raise credentials_exception

    for scope in security_scopes.scopes:
        if scope not in access_token.scopes:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not enough permissions",
                                headers={"WWW-Authenticate": authenticate_value}, )
    return user
