from pydantic import BaseModel


class AssignSlackUserCommand(BaseModel):
    user_id: int
    slack_secret_id: int
    slack_user_id: int


class UnassignSlackUserCommand(BaseModel):
    user_id: int
    slack_user_id: int
