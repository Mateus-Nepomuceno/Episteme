from http import HTTPStatus
from uuid import uuid4

import pytest
from fastapi import HTTPException
from jwt import encode

from academico.security import get_current_user
from academico.settings import Settings


def test_get_current_user_valid():
    settings = Settings()
    uid = str(uuid4())
    payload = {'sub': 'teste@teste.com', 'id': uid, 'e_admin': True}
    token = encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    user = get_current_user(token)
    assert str(user.id) == uid
    assert user.email == 'teste@teste.com'
    assert user.e_admin is True


def test_get_current_user_invalid_token():
    with pytest.raises(HTTPException) as excinfo:
        get_current_user('token_invalido')
    assert excinfo.value.status_code == HTTPStatus.UNAUTHORIZED


def test_get_current_user_missing_fields():
    settings = Settings()
    payload = {'sub': 'teste@teste.com'}
    token = encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    with pytest.raises(HTTPException) as excinfo:
        get_current_user(token)
    assert excinfo.value.status_code == HTTPStatus.UNAUTHORIZED
