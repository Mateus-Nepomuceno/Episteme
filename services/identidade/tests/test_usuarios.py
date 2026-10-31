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
            'cpf': '111.444.777-35',
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
            'cpf': '987.654.321-00',
            'telefone': '(11) 77777-7777',
            'senha': 'nova_senha',
            'e_admin': False,
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_read_usuario(client, user, user_token):
    response = client.get(
        f'/usuarios/{user.id}',
        headers={'Authorization': f'Bearer {user_token}'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['email'] == user.email


def test_read_usuario_sem_autenticacao(client, user):
    response = client.get(f'/usuarios/{user.id}')
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_read_usuario_de_outro_usuario_e_negado(
    client, admin, user_token
):
    response = client.get(
        f'/usuarios/{admin.id}',
        headers={'Authorization': f'Bearer {user_token}'},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_read_usuario_admin_consulta_qualquer_usuario(
    client, user, admin_token
):
    response = client.get(
        f'/usuarios/{user.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )
    assert response.status_code == HTTPStatus.OK


def test_read_usuario_not_found(client, admin_token):
    response = client.get(
        f'/usuarios/{uuid4()}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )
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
            'cpf': '000.000.001-91',
            'telefone': '(11) 95555-5555',
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
            'cpf': '111.444.777-35',
            'telefone': '(11) 90000-0000',
            'senha': 'senha_limpa',
            'e_admin': False,
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_usuario_proprio_usuario_e_negado(client, user, user_token):
    response = client.delete(
        f'/usuarios/{user.id}',
        headers={'Authorization': f'Bearer {user_token}'},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_delete_usuario_por_administrador(client, user, admin_token):
    response = client.delete(
        f'/usuarios/{user.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )
    assert response.status_code == HTTPStatus.OK


def test_delete_usuario_not_found(client, admin_token):
    response = client.delete(
        f'/usuarios/{uuid4()}',
        headers={'Authorization': f'Bearer {admin_token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_usuario_conflict(client, user, user_token):
    client.post(
        '/usuarios/',
        json={
            'nome': 'malicioso2',
            'email': 'malicioso2@exemplo.com',
            'cpf': '529.982.247-25',
            'telefone': '(11) 94444-4444',
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


def test_create_usuario_normaliza_cpf_e_telefone(client, session):
    response = client.post(
        '/usuarios/',
        json=_payload_usuario(
            email='normalizado@exemplo.com',
            cpf='111 444 777 35',
            telefone='(11) 97777-7777',
        ),
    )
    assert response.status_code == HTTPStatus.CREATED

    usuario = session.scalar(
        select(Usuario).where(Usuario.email == 'normalizado@exemplo.com')
    )
    assert usuario.cpf == '111.444.777-35'
    assert usuario.telefone == '+5511977777777'


def test_create_usuario_aceita_telefone_com_codigo_do_pais(client, session):
    response = client.post(
        '/usuarios/',
        json=_payload_usuario(
            email='pais@exemplo.com', telefone='+5511999998888'
        ),
    )
    assert response.status_code == HTTPStatus.CREATED

    usuario = session.scalar(
        select(Usuario).where(Usuario.email == 'pais@exemplo.com')
    )
    assert usuario.telefone == '+5511999998888'


def test_create_usuario_cpf_com_digito_verificador_invalido(client):
    response = client.post(
        '/usuarios/', json=_payload_usuario(cpf='111.444.777-36')
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_usuario_cpf_com_todos_digitos_iguais(client):
    response = client.post(
        '/usuarios/', json=_payload_usuario(cpf='111.111.111-11')
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_usuario_cpf_com_tamanho_errado(client):
    response = client.post('/usuarios/', json=_payload_usuario(cpf='1114447'))
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_usuario_telefone_com_tamanho_invalido(client):
    response = client.post(
        '/usuarios/', json=_payload_usuario(telefone='+55 11 9999')
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_usuario_telefone_com_letras(client):
    response = client.post(
        '/usuarios/', json=_payload_usuario(telefone='11 9999-ABCD')
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_update_usuario_cpf_invalido_e_recusado(client, user, user_token):
    response = client.put(
        f'/usuarios/{user.id}',
        headers={'Authorization': f'Bearer {user_token}'},
        json=_payload_usuario(
            email=user.email,
            cpf='000.000.000-00',
            telefone=user.telefone,
            senha='senha_limpa',
        ),
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_usuario_nao_cria_administrador(client, session):
    response = client.post(
        '/usuarios/',
        json=_payload_usuario(email='novo@exemplo.com', e_admin=True),
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['e_admin'] is False


def test_update_usuario_comum_nao_se_promove(client, user, user_token):
    response = client.put(
        f'/usuarios/{user.id}',
        headers={'Authorization': f'Bearer {user_token}'},
        json=_payload_usuario(
            email=user.email,
            cpf=user.cpf,
            telefone=user.telefone,
            senha='senha_limpa',
            e_admin=True,
        ),
    )

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_update_usuario_admin_pode_promover(client, user, admin_token):
    response = client.put(
        f'/usuarios/{user.id}',
        headers={'Authorization': f'Bearer {admin_token}'},
        json=_payload_usuario(
            email=user.email,
            cpf=user.cpf,
            telefone=user.telefone,
            senha='senha_limpa',
            e_admin=True,
        ),
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['e_admin'] is True
