from http import HTTPStatus


def test_root(client):
    response = client.get('/')

    assert response.status_code == HTTPStatus.OK


def test_get_token(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': 'senha_limpa'},
    )
    token = response.json()

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in token
    assert 'token_type' in token


def test_create_usuario(client):
    response = client.post(
        '/usuarios/',
        json={
            'nome': 'carlos',
            'email': 'carlos@exemplo.com',
            'cpf': '000.000.000-00',
            'telefone': '(11) 77777-7777',
            'senha': 'nova_senha',
            'e_admin': False,
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['nome'] == 'carlos'
    assert data['email'] == 'carlos@exemplo.com'
