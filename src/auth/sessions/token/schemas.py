from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AccessToken(BaseModel):
    sub: UUID
    exp: datetime
    scope: str

    @property
    def scopes(self) -> list[str]:
        return self.scope.split()

    def to_payload(self) -> dict[str, str | datetime]:
        d = self.model_dump()
        d["sub"] = str(self.sub)
        return d


class Token(BaseModel):
    access_token: str
    token_type: str

