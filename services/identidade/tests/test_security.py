from datetime import datetime, timedelta
from http import HTTPStatus
from uuid import uuid4
from zoneinfo import ZoneInfo

from jwt import decode, encode

from identidade.security import create_access_token
from identidade.settings import Settings


def test_jwt():
    data = {'teste': 'teste'}
    token = create_access_token(data)

    decoded = decode(token, Settings().SECRET_KEY, algorithms=['HS256'])

    assert decoded['teste'] == data['teste']
    assert 'exp' in decoded


def test_get_current_user_invalid_token(client):
    response = client.delete(
        f'/usuarios/{uuid4()}',
        headers={'Authorization': 'Bearer tokeninvalido'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_current_user_no_sub(client):
    token = encode(
        {'teste': 'teste'}, Settings().SECRET_KEY, algorithm='HS256'
    )
    response = client.delete(
        f'/usuarios/{uuid4()}', headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_current_user_user_not_found(client):
    token = encode(
        {'sub': 'naoencontrado@teste.com'},
        Settings().SECRET_KEY,
        algorithm='HS256',
    )
    response = client.delete(
        f'/usuarios/{uuid4()}', headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_current_user_token_expirado(client, user):
    settings = Settings()
    expirado = encode(
        {
            'sub': user.email,
            'exp': datetime.now(tz=ZoneInfo('UTC')) - timedelta(minutes=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.put(
        f'/usuarios/{user.id}',
        headers={'Authorization': f'Bearer {expirado}'},
        json={
            'nome': 'joana',
            'email': user.email,
            'cpf': user.cpf,
            'telefone': user.telefone,
            'senha': 'senha_limpa',
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
