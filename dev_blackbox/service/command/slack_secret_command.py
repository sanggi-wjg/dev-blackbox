from pydantic import BaseModel


class CreateSlackSecretCommand(BaseModel):
    name: str
    bot_token: str
