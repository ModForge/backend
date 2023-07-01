from pydantic import BaseModel
from typing import Union


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Union[str, None] = None
    user: Union[dict, None] = None
    discord_access_token: Union[str, None] = None
    discord: Union[dict, None] = None
