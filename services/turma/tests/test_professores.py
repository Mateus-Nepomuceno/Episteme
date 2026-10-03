from http import HTTPStatus
from uuid import uuid4

from turma.app import app
from turma.models import Professor
from turma.security import CurrentUser, get_current_user


def test_create_professor(client):
    uid = uuid4()
    response = client.post(
        '/professores/',
        json={'usuario_id': str(uid), 'matricula_id': '123', 'ativo': True},
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['matricula_id'] == '123'


def test_create_professor_conflict(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123', ativo=True)
    session.add(professor)
    session.commit()

    response = client.post(
        '/professores/',
        json={'usuario_id': str(uid), 'matricula_id': '123', 'ativo': True},
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_read_professores(client):
    response = client.get('/professores/')
    assert response.status_code == HTTPStatus.OK
    assert 'professores' in response.json()


def test_read_professor(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123', ativo=True)
    session.add(professor)
    session.commit()

    response = client.get(f'/professores/{professor.id}')
    assert response.status_code == HTTPStatus.OK
    assert response.json()['matricula_id'] == '123'


def test_read_professor_not_found(client):
    response = client.get(f'/professores/{uuid4()}')
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_professor(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123', ativo=True)
    session.add(professor)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uid, email='teste@teste.com', e_admin=False)

    new_uid = uuid4()
    response = client.put(
        f'/professores/{professor.id}',
        json={'usuario_id': str(new_uid), 'matricula_id': '1234', 'ativo': False},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['matricula_id'] == '1234'
    app.dependency_overrides.clear()


def test_update_professor_not_found(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)

    response = client.put(
        f'/professores/{uuid4()}',
        json={'usuario_id': str(uuid4()), 'matricula_id': '1234', 'ativo': False},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    app.dependency_overrides.clear()


def test_update_professor_forbidden(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123', ativo=True)
    session.add(professor)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='outro@teste.com', e_admin=False)

    response = client.put(
        f'/professores/{professor.id}',
        json={'usuario_id': str(uuid4()), 'matricula_id': '1234', 'ativo': False},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    app.dependency_overrides.clear()


def test_update_professor_conflict(client, session):
    uid1 = uuid4()
    uid2 = uuid4()
    professor1 = Professor(usuario_id=uid1, matricula_id='123', ativo=True)
    professor2 = Professor(usuario_id=uid2, matricula_id='124', ativo=True)
    session.add(professor1)
    session.add(professor2)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uid1, email='teste@teste.com', e_admin=True)

    response = client.put(
        f'/professores/{professor1.id}',
        json={'usuario_id': str(uid2), 'matricula_id': '124', 'ativo': False},
    )
    assert response.status_code == HTTPStatus.CONFLICT
    app.dependency_overrides.clear()


def test_delete_professor(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123', ativo=True)
    session.add(professor)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uid, email='teste@teste.com', e_admin=False)

    response = client.delete(f'/professores/{professor.id}')
    assert response.status_code == HTTPStatus.OK
    app.dependency_overrides.clear()


def test_delete_professor_not_found(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)

    response = client.delete(f'/professores/{uuid4()}')
    assert response.status_code == HTTPStatus.NOT_FOUND
    app.dependency_overrides.clear()


def test_delete_professor_forbidden(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123', ativo=True)
    session.add(professor)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)

    response = client.delete(f'/professores/{professor.id}')
    assert response.status_code == HTTPStatus.FORBIDDEN
    app.dependency_overrides.clear()
