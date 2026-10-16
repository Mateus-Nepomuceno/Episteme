from http import HTTPStatus
from uuid import uuid4

from academico.app import app
from academico.models import Curso
from academico.security import CurrentUser, get_current_user


def test_create_curso_conflict(client, session):
    curso = Curso(
        codigo='ENG01',
        nome='Engenharia',
        tipo_formacao='Graduação',
        modalidade='Presencial',
        nivel_academico='Superior',
        carga_horaria_total=3600,
        campus='Sede',
    )
    session.add(curso)
    session.commit()

    response = client.post(
        '/cursos/',
        json={
            'codigo': 'ENG01',
            'nome': 'Engenharia',
            'tipo_formacao': 'Graduação',
            'modalidade': 'Presencial',
            'nivel_academico': 'Superior',
            'carga_horaria_total': 3600,
            'campus': 'Sede',
            'ativo': True,
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_read_curso(client, session):
    curso = Curso(
        codigo='ENG02',
        nome='Engenharia',
        tipo_formacao='Graduação',
        modalidade='Presencial',
        nivel_academico='Superior',
        carga_horaria_total=3600,
        campus='Sede',
    )
    session.add(curso)
    session.commit()

    response = client.get(f'/cursos/{curso.id}')
    assert response.status_code == HTTPStatus.OK
    assert response.json()['codigo'] == 'ENG02'


def test_read_curso_not_found(client):
    response = client.get(f'/cursos/{uuid4()}')
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_curso(client, session):
    curso = Curso(
        codigo='ENG03',
        nome='Engenharia',
        tipo_formacao='Graduação',
        modalidade='Presencial',
        nivel_academico='Superior',
        carga_horaria_total=3600,
        campus='Sede',
    )
    session.add(curso)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='test@test.com', e_admin=True
    )

    response = client.put(
        f'/cursos/{curso.id}',
        json={
            'codigo': 'ENG03A',
            'nome': 'Engenharia',
            'tipo_formacao': 'Graduação',
            'modalidade': 'Presencial',
            'nivel_academico': 'Superior',
            'carga_horaria_total': 3600,
            'campus': 'Sede',
            'ativo': True,
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['codigo'] == 'ENG03A'
    app.dependency_overrides.clear()


def test_update_curso_not_found(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='test@test.com', e_admin=True
    )

    response = client.put(
        f'/cursos/{uuid4()}',
        json={
            'codigo': 'ENG03A',
            'nome': 'Engenharia',
            'tipo_formacao': 'Graduação',
            'modalidade': 'Presencial',
            'nivel_academico': 'Superior',
            'carga_horaria_total': 3600,
            'campus': 'Sede',
            'ativo': True,
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    app.dependency_overrides.clear()


def test_update_curso_forbidden(client, session):
    curso = Curso(
        codigo='ENG04',
        nome='Engenharia',
        tipo_formacao='Graduação',
        modalidade='Presencial',
        nivel_academico='Superior',
        carga_horaria_total=3600,
        campus='Sede',
    )
    session.add(curso)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='test@test.com', e_admin=False
    )

    response = client.put(
        f'/cursos/{curso.id}',
        json={
            'codigo': 'ENG04A',
            'nome': 'Engenharia',
            'tipo_formacao': 'Graduação',
            'modalidade': 'Presencial',
            'nivel_academico': 'Superior',
            'carga_horaria_total': 3600,
            'campus': 'Sede',
            'ativo': True,
        },
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    app.dependency_overrides.clear()


def test_update_curso_conflict(client, session):
    c1 = Curso(
        codigo='ENG05',
        nome='C1',
        tipo_formacao='G',
        modalidade='P',
        nivel_academico='S',
        carga_horaria_total=1,
        campus='S',
    )
    c2 = Curso(
        codigo='ENG06',
        nome='C2',
        tipo_formacao='G',
        modalidade='P',
        nivel_academico='S',
        carga_horaria_total=1,
        campus='S',
    )
    session.add_all([c1, c2])
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='test@test.com', e_admin=True
    )

    response = client.put(
        f'/cursos/{c1.id}',
        json={
            'codigo': 'ENG06',
            'nome': 'C1',
            'tipo_formacao': 'G',
            'modalidade': 'P',
            'nivel_academico': 'S',
            'carga_horaria_total': 1,
            'campus': 'S',
            'ativo': True,
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    app.dependency_overrides.clear()


def test_delete_curso(client, session):
    curso = Curso(
        codigo='ENG07',
        nome='C1',
        tipo_formacao='G',
        modalidade='P',
        nivel_academico='S',
        carga_horaria_total=1,
        campus='S',
    )
    session.add(curso)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='test@test.com', e_admin=True
    )

    response = client.delete(f'/cursos/{curso.id}')
    assert response.status_code == HTTPStatus.OK
    app.dependency_overrides.clear()


def test_delete_curso_not_found(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='test@test.com', e_admin=True
    )

    response = client.delete(f'/cursos/{uuid4()}')
    assert response.status_code == HTTPStatus.NOT_FOUND
    app.dependency_overrides.clear()


def test_delete_curso_forbidden(client, session):
    curso = Curso(
        codigo='ENG08',
        nome='C1',
        tipo_formacao='G',
        modalidade='P',
        nivel_academico='S',
        carga_horaria_total=1,
        campus='S',
    )
    session.add(curso)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='test@test.com', e_admin=False
    )

    response = client.delete(f'/cursos/{curso.id}')
    assert response.status_code == HTTPStatus.FORBIDDEN
    app.dependency_overrides.clear()


def test_create_curso(client):
    response = client.post(
        '/cursos/',
        json={
            'codigo': 'ENG09',
            'nome': 'C1',
            'tipo_formacao': 'G',
            'modalidade': 'P',
            'nivel_academico': 'S',
            'carga_horaria_total': 1,
            'campus': 'S',
            'ativo': True,
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['codigo'] == 'ENG09'


def test_read_cursos(client):
    response = client.get('/cursos/')
    assert response.status_code == HTTPStatus.OK
    assert 'cursos' in response.json()
