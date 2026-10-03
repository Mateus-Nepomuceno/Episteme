from http import HTTPStatus
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import DecodeError, decode
from pydantic import BaseModel

from academico.settings import Settings

settings = Settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')


class CurrentUser(BaseModel):
    id: UUID
    email: str
    e_admin: bool


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Não foi possível validar as credenciais de autenticação',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except DecodeError:
        raise credentials_exception
    else:
        email = payload.get('sub')
        user_id = payload.get('id')
        e_admin = payload.get('e_admin')
        if not email or not user_id or e_admin is None:
            raise credentials_exception
        return CurrentUser(id=user_id, email=email, e_admin=e_admin)
