from typing import Annotated

from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from pydantic import ValidationError
from starlette import status

from dev_blackbox.core.database import get_db_session
from dev_blackbox.core.jwt_handler import get_jwt_service
from dev_blackbox.service.model.user_model import UserModel
from dev_blackbox.service.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
)
AuthToken = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(
    # security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
):
    authenticate_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )
    jwt_service = get_jwt_service()

    try:
        payload = jwt_service.decode_token(token)
    except InvalidTokenError, ValidationError:
        raise authenticate_exception

    user_email = payload.get("sub")
    if user_email is None:
        raise authenticate_exception

    with get_db_session() as db:
        service = UserService(db)
        user = service.get_user_by_email_or_none(user_email)
        if user is None:
            raise authenticate_exception
        return UserModel.model_validate(user)


async def get_current_admin_user(
    current_user: UserModel = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )
    return current_user


CurrentUser = Annotated[UserModel, Depends(get_current_user)]
CurrentAdminUser = Annotated[UserModel, Depends(get_current_admin_user)]
