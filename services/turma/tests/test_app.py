from http import HTTPStatus
from uuid import uuid4


def test_root(client):
    response = client.get('/')

    assert response.status_code == HTTPStatus.OK


def test_create_aluno(client, current_user_override):
    uid = str(uuid4())
    response = client.post(
        '/alunos/',
        json={
            'usuario_id': uid,
            'matricula_id': '123456',
            'curso_id': '1',
            'ativo': True
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['usuario_id'] == uid
    assert data['matricula_id'] == '123456'
    assert data['curso_id'] == '1'


def test_read_alunos(client):
    response = client.get('/alunos/')
    assert response.status_code == HTTPStatus.OK
    assert 'alunos' in response.json()
