from http import HTTPStatus


def test_login_incorrect_matricula(client, user):
    response = client.post(
        '/auth/token',
        data={'username': 'nao-existe', 'password': 'senha_limpa'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_login_incorrect_password(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.matricula, 'password': 'senha_errada'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_login_com_email_e_recusado(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': 'senha_limpa'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
