from http import HTTPStatus
from uuid import uuid4

from tests.conftest import usuario_da

CURSO_A = '11111111-1111-1111-1111-111111111111'


def test_root(client):
    response = client.get('/')

    assert response.status_code == HTTPStatus.OK


def test_create_aluno(client):
    uid = str(uuid4())
    response = client.post(
        '/alunos/',
        json={
            'usuario_id': uid,
            'matricula_id': '123456',
            'curso_id': CURSO_A,
            'ativo': True
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['usuario_id'] == str(usuario_da('123456'))
    assert data['matricula_id'] == '123456'
    assert data['curso_id'] == CURSO_A


def test_read_alunos(client):
    response = client.get('/alunos/')
    assert response.status_code == HTTPStatus.OK
    assert 'alunos' in response.json()
