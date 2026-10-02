from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from usuarios.database import get_session
from usuarios.models import Usuario
from usuarios.schemas import Token
from usuarios.security import create_access_token, verify_password

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/token', response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)]
):
    usuario = session.scalar(select(Usuario).where(Usuario.email == form_data.username))

    if not usuario:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Senha ou email incorretos'
        )

    if not verify_password(form_data.password, usuario.senha):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Senha ou email incorretos'
        )

    access_token = create_access_token(data={'sub': usuario.email})

    return {'access_token': access_token, 'token_type': 'bearer'}
