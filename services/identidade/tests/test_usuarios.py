from http import HTTPStatus
from uuid import uuid4

from sqlalchemy import select

from identidade.models import Usuario
from identidade.security import verify_password


def test_create_usuario(client):
    response = client.post(
        '/usuarios/',
        json={
            'nome': 'roberto',
            'email': 'roberto@exemplo.com',
            'cpf': '000.000.000-00',
            'telefone': '(11) 77777-7777',
            'senha': 'nova_senha',
            'e_admin': False,
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['nome'] == 'roberto'
    assert data['email'] == 'roberto@exemplo.com'


def test_create_usuario_conflict(client, user):
    response = client.post(
        '/usuarios/',
        json={
            'nome': 'joana clone',
            'email': user.email,
            'cpf': '111.111.111-11',
            'telefone': '(11) 77777-7777',
            'senha': 'nova_senha',
            'e_admin': False,
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_read_usuario(client, user):
    response = client.get(f'/usuarios/{user.id}')
    assert response.status_code == HTTPStatus.OK
    assert response.json()['email'] == user.email


def test_read_usuario_not_found(client):
    response = client.get(f'/usuarios/{uuid4()}')
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_usuario_success(client, user, user_token):
    response = client.put(
        f'/usuarios/{user.id}',
        headers={'Authorization': f'Bearer {user_token}'},
        json={
            'nome': 'joana atualizada',
            'email': user.email,
            'cpf': user.cpf,
            'telefone': user.telefone,
            'senha': 'senha_limpa',
            'e_admin': False,
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['nome'] == 'joana atualizada'


def test_update_usuario_forbidden(client, user, admin_token):
    pass


def test_update_usuario_forbidden_real(client, user):
    response_create = client.post(
        '/usuarios/',
        json={
            'nome': 'malicioso',
            'email': 'malicioso@exemplo.com',
            'cpf': '555.555.555-55',
            'telefone': '555',
            'senha': 'senha_limpa',
            'e_admin': False,
        },
    )
    mallory = response_create.json()
    mallory_token = client.post(
        '/auth/token',
        data={'username': mallory['email'], 'password': 'senha_limpa'},
    ).json()['access_token']

    response = client.put(
        f'/usuarios/{user.id}',
        headers={'Authorization': f'Bearer {mallory_token}'},
        json={
            'nome': 'hackeado',
            'email': user.email,
            'cpf': user.cpf,
            'telefone': user.telefone,
            'senha': 'senha_limpa',
            'e_admin': False,
        },
    )
    assert response.status_code == HTTPStatus.FORBIDDEN

    response = client.delete(
        f'/usuarios/{user.id}',
        headers={'Authorization': f'Bearer {mallory_token}'},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_update_usuario_not_found(client, user_token):
    response = client.put(
        f'/usuarios/{uuid4()}',
        headers={'Authorization': f'Bearer {user_token}'},
        json={
            'nome': 'joana atualizada',
            'email': 'algum@email.com',
            'cpf': '000',
            'telefone': '000',
            'senha': 'senha_limpa',
            'e_admin': False,
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_usuario(client, user, user_token):
    response = client.delete(
        f'/usuarios/{user.id}',
        headers={'Authorization': f'Bearer {user_token}'},
    )
    assert response.status_code == HTTPStatus.OK


def test_delete_usuario_not_found(client, user_token):
    response = client.delete(
        f'/usuarios/{uuid4()}',
        headers={'Authorization': f'Bearer {user_token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_usuario_conflict(client, user, user_token):
    client.post(
        '/usuarios/',
        json={
            'nome': 'malicioso2',
            'email': 'malicioso2@exemplo.com',
            'cpf': '444.444.444-44',
            'telefone': '444',
            'senha': 'senha_limpa',
            'e_admin': False,
        },
    )

    response = client.put(
        f'/usuarios/{user.id}',
        headers={'Authorization': f'Bearer {user_token}'},
        json={
            'nome': 'joana atualizada',
            'email': 'malicioso2@exemplo.com',
            'cpf': user.cpf,
            'telefone': user.telefone,
            'senha': 'senha_limpa',
            'e_admin': False,
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT


def _payload_usuario(**campos):
    payload = {
        'nome': 'carlos',
        'email': 'carlos@exemplo.com',
        'cpf': '111.444.777-35',
        'telefone': '(11) 97777-7777',
        'senha': 'senha_valida',
        'e_admin': False,
    }
    payload.update(campos)
    return payload


def test_create_usuario_sem_senha_e_recusado(client, session):
    response = client.post('/usuarios/', json=_payload_usuario(senha=''))
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_usuario_sem_campo_senha_e_recusado(client, session):
    payload = _payload_usuario()
    del payload['senha']
    response = client.post('/usuarios/', json=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_usuario_senha_curta_e_recusada(client, session):
    response = client.post(
        '/usuarios/', json=_payload_usuario(senha='a' * 7)
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_usuario_senha_minima_e_aceita(client, session):
    response = client.post(
        '/usuarios/', json=_payload_usuario(senha='a' * 8)
    )
    assert response.status_code == HTTPStatus.CREATED


def test_create_usuario_armazena_senha_com_hash(client, session):
    response = client.post(
        '/usuarios/', json=_payload_usuario(senha='senha_secreta')
    )
    assert response.status_code == HTTPStatus.CREATED

    usuario = session.scalar(
        select(Usuario).where(Usuario.email == 'carlos@exemplo.com')
    )
    assert usuario is not None
    assert usuario.senha != 'senha_secreta'
    assert verify_password('senha_secreta', usuario.senha)


def test_update_usuario_sem_senha_e_recusado(client, user, user_token):
    response = client.put(
        f'/usuarios/{user.id}',
        headers={'Authorization': f'Bearer {user_token}'},
        json=_payload_usuario(
            email=user.email, cpf=user.cpf, telefone=user.telefone, senha=''
        ),
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
