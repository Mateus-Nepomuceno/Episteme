from http import HTTPStatus


def test_login_incorrect_email(client, user):
    response = client.post(
        '/auth/token',
        data={'username': 'errado@exemplo.com', 'password': 'senha_limpa'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_login_incorrect_password(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': 'senha_errada'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
