from http import HTTPStatus
from uuid import uuid4

from turma.app import app
from turma.models import Aluno
from turma.security import CurrentUser, get_current_user


def test_create_aluno_conflict(client, session):
    uid = uuid4()
    aluno = Aluno(usuario_id=uid, matricula_id='123', curso_id='1', ativo=True)
    session.add(aluno)
    session.commit()

    response = client.post(
        '/alunos/',
        json={'usuario_id': str(uid), 'matricula_id': '123', 'curso_id': '1', 'ativo': True},
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_read_aluno(client, session):
    uid = uuid4()
    aluno = Aluno(usuario_id=uid, matricula_id='123', curso_id='1', ativo=True)
    session.add(aluno)
    session.commit()

    response = client.get(f'/alunos/{aluno.id}')
    assert response.status_code == HTTPStatus.OK
    assert response.json()['matricula_id'] == '123'


def test_read_aluno_not_found(client):
    response = client.get(f'/alunos/{uuid4()}')
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_read_aluno_usuario_id(client, session):
    uid = uuid4()
    aluno = Aluno(usuario_id=uid, matricula_id='123', curso_id='1', ativo=True)
    session.add(aluno)
    session.commit()

    response = client.get(f'/alunos/usuario_id/{aluno.usuario_id}')
    assert response.status_code == HTTPStatus.OK
    assert response.json()['matricula_id'] == '123'


def test_read_aluno_usuario_id_not_found(client):
    response = client.get(f'/alunos/usuario_id/{uuid4()}')
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_aluno(client, session):
    uid = uuid4()
    aluno = Aluno(usuario_id=uid, matricula_id='123', curso_id='1', ativo=True)
    session.add(aluno)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uid, email='teste@teste.com', e_admin=False)

    new_uid = uuid4()
    response = client.put(
        f'/alunos/{aluno.id}',
        json={'usuario_id': str(new_uid), 'matricula_id': '1234', 'curso_id': '2', 'ativo': False},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['matricula_id'] == '1234'
    assert response.json()['curso_id'] == '2'
    app.dependency_overrides.clear()


def test_update_aluno_not_found(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)

    response = client.put(
        f'/alunos/{uuid4()}',
        json={'usuario_id': str(uuid4()), 'matricula_id': '1234', 'curso_id': '2', 'ativo': False},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    app.dependency_overrides.clear()


def test_update_aluno_forbidden(client, session):
    uid = uuid4()
    aluno = Aluno(usuario_id=uid, matricula_id='123', curso_id='1', ativo=True)
    session.add(aluno)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)

    response = client.put(
        f'/alunos/{aluno.id}',
        json={'usuario_id': str(uuid4()), 'matricula_id': '1234', 'curso_id': '2', 'ativo': False},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    app.dependency_overrides.clear()


def test_update_aluno_conflict(client, session):
    uid1 = uuid4()
    uid2 = uuid4()
    aluno1 = Aluno(usuario_id=uid1, matricula_id='123', curso_id='1', ativo=True)
    aluno2 = Aluno(usuario_id=uid2, matricula_id='124', curso_id='2', ativo=True)
    session.add(aluno1)
    session.add(aluno2)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uid1, email='teste@teste.com', e_admin=True)

    response = client.put(
        f'/alunos/{aluno1.id}',
        json={'usuario_id': str(uid2), 'matricula_id': '124', 'curso_id': '2', 'ativo': False},
    )
    assert response.status_code == HTTPStatus.CONFLICT
    app.dependency_overrides.clear()


def test_delete_aluno(client, session):
    uid = uuid4()
    aluno = Aluno(usuario_id=uid, matricula_id='123', curso_id='1', ativo=True)
    session.add(aluno)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uid, email='teste@teste.com', e_admin=False)

    response = client.delete(f'/alunos/{aluno.id}')
    assert response.status_code == HTTPStatus.OK
    app.dependency_overrides.clear()


def test_delete_aluno_not_found(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)

    response = client.delete(f'/alunos/{uuid4()}')
    assert response.status_code == HTTPStatus.NOT_FOUND
    app.dependency_overrides.clear()


def test_delete_aluno_forbidden(client, session):
    uid = uuid4()
    aluno = Aluno(usuario_id=uid, matricula_id='123', curso_id='1', ativo=True)
    session.add(aluno)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)

    response = client.delete(f'/alunos/{aluno.id}')
    assert response.status_code == HTTPStatus.FORBIDDEN
    app.dependency_overrides.clear()
