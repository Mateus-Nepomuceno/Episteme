from http import HTTPStatus
from uuid import uuid4

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
