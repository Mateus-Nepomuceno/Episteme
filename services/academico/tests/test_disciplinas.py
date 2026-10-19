from http import HTTPStatus
from uuid import uuid4

from academico.app import app
from academico.models import Disciplina
from academico.security import CurrentUser, get_current_user


def test_create_disciplina_conflict(client, session):
    disciplina = Disciplina(
        codigo='MAT101',
        nome='Calculo 1',
        carga_horaria=60,
        tipo='Obrigatória',
        departamento='MAT',
    )
    session.add(disciplina)
    session.commit()

    response = client.post(
        '/disciplinas/',
        json={
            'codigo': 'MAT101',
            'nome': 'Outro',
            'carga_horaria': 30,
            'tipo': 'Opcional',
            'departamento': 'MAT',
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_read_disciplina(client, session):
    disciplina = Disciplina(
        codigo='MAT102',
        nome='Calculo 2',
        carga_horaria=60,
        tipo='Obrigatória',
        departamento='MAT',
    )
    session.add(disciplina)
    session.commit()

    response = client.get(f'/disciplinas/{disciplina.id}')
    assert response.status_code == HTTPStatus.OK
    assert response.json()['codigo'] == 'MAT102'


def test_read_disciplina_not_found(client):
    response = client.get(f'/disciplinas/{uuid4()}')
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_disciplina(client, session):
    disciplina = Disciplina(
        codigo='MAT103',
        nome='Calculo 3',
        carga_horaria=60,
        tipo='Obrigatória',
        departamento='MAT',
    )
    session.add(disciplina)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='test@test.com', e_admin=True
    )

    response = client.put(
        f'/disciplinas/{disciplina.id}',
        json={
            'codigo': 'MAT103A',
            'nome': 'Calculo 3A',
            'carga_horaria': 60,
            'tipo': 'Obrigatória',
            'departamento': 'MAT',
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['codigo'] == 'MAT103A'
    app.dependency_overrides.clear()


def test_update_disciplina_not_found(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='test@test.com', e_admin=True
    )

    response = client.put(
        f'/disciplinas/{uuid4()}',
        json={
            'codigo': 'MAT103A',
            'nome': 'Calculo 3A',
            'carga_horaria': 60,
            'tipo': 'Obrigatória',
            'departamento': 'MAT',
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    app.dependency_overrides.clear()


def test_update_disciplina_forbidden(client, session):
    disciplina = Disciplina(
        codigo='MAT104',
        nome='Calculo 4',
        carga_horaria=60,
        tipo='Obrigatória',
        departamento='MAT',
    )
    session.add(disciplina)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='test@test.com', e_admin=False
    )

    response = client.put(
        f'/disciplinas/{disciplina.id}',
        json={
            'codigo': 'MAT104',
            'nome': 'Calculo 4A',
            'carga_horaria': 60,
            'tipo': 'Obrigatória',
            'departamento': 'MAT',
        },
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    app.dependency_overrides.clear()


def test_update_disciplina_conflict(client, session):
    d1 = Disciplina(
        codigo='MAT105',
        nome='Calculo 5',
        carga_horaria=60,
        tipo='Obrigatória',
        departamento='MAT',
    )
    d2 = Disciplina(
        codigo='MAT106',
        nome='Calculo 6',
        carga_horaria=60,
        tipo='Obrigatória',
        departamento='MAT',
    )
    session.add_all([d1, d2])
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='test@test.com', e_admin=True
    )

    response = client.put(
        f'/disciplinas/{d1.id}',
        json={
            'codigo': 'MAT106',
            'nome': 'Calculo 5A',
            'carga_horaria': 60,
            'tipo': 'Obrigatória',
            'departamento': 'MAT',
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    app.dependency_overrides.clear()


def test_delete_disciplina(client, session):
    disciplina = Disciplina(
        codigo='MAT107',
        nome='Calculo 7',
        carga_horaria=60,
        tipo='Obrigatória',
        departamento='MAT',
    )
    session.add(disciplina)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='test@test.com', e_admin=True
    )

    response = client.delete(f'/disciplinas/{disciplina.id}')
    assert response.status_code == HTTPStatus.OK
    app.dependency_overrides.clear()


def test_delete_disciplina_not_found(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='test@test.com', e_admin=True
    )

    response = client.delete(f'/disciplinas/{uuid4()}')
    assert response.status_code == HTTPStatus.NOT_FOUND
    app.dependency_overrides.clear()


def test_delete_disciplina_forbidden(client, session):
    disciplina = Disciplina(
        codigo='MAT108',
        nome='Calculo 8',
        carga_horaria=60,
        tipo='Obrigatória',
        departamento='MAT',
    )
    session.add(disciplina)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='test@test.com', e_admin=False
    )

    response = client.delete(f'/disciplinas/{disciplina.id}')
    assert response.status_code == HTTPStatus.FORBIDDEN
    app.dependency_overrides.clear()


def test_create_disciplina(client):
    response = client.post(
        '/disciplinas/',
        json={
            'codigo': 'MAT109',
            'nome': 'Calculo 9',
            'carga_horaria': 60,
            'tipo': 'Obrigatória',
            'departamento': 'MAT',
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['codigo'] == 'MAT109'


def test_read_disciplinas(client):
    response = client.get('/disciplinas/')
    assert response.status_code == HTTPStatus.OK
    assert 'disciplinas' in response.json()
