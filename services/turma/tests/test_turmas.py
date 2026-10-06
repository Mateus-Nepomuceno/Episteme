from http import HTTPStatus
from uuid import uuid4

from turma.app import app
from turma.models import Aluno, Professor, Turma
from turma.security import CurrentUser, get_current_user


def test_create_turma(client, session):
    uid_prof = uuid4()
    uid_aluno1 = uuid4()
    uid_aluno2 = uuid4()

    professor = Professor(usuario_id=uid_prof, matricula_id='123', ativo=True)
    aluno1 = Aluno(usuario_id=uid_aluno1, matricula_id='456', curso_id='1', ativo=True)
    aluno2 = Aluno(usuario_id=uid_aluno2, matricula_id='789', curso_id='1', ativo=True)
    session.add(professor)
    session.add(aluno1)
    session.add(aluno2)
    session.commit()
    session.refresh(professor)
    session.refresh(aluno1)
    session.refresh(aluno2)

    response = client.post(
        '/turmas/',
        json={
            'nome': 'Turma 1',
            'professor_id': str(professor.id),
            'materia': 'Física',
            'aluno_ids': [str(aluno1.id), str(aluno2.id)],
            'documentos': ['./documento.pdf'],
            'aviso': ['Aviso 1', 'Aviso 2'],
        }
    )
    assert response.status_code == HTTPStatus.CREATED


def test_create_turma_sem_prof(client, session):
    response = client.post(
        '/turmas/',
        json={'nome': 'Turma 1', 'professor_id': str(uuid4()), 'materia': 'Física'}
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_turma_erro_alunos(client, session):
    uid_prof = uuid4()

    professor = Professor(usuario_id=uid_prof, matricula_id='123', ativo=True)
    session.add(professor)
    session.commit()
    session.refresh(professor)

    response = client.post(
        '/turmas/',
        json={
            'nome': 'Turma 1',
            'professor_id': str(professor.id),
            'materia': 'Física',
            'aluno_ids': [str(uuid4())],
        }
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_turma_conflict(client, session):
    uid = uuid4()

    professor = Professor(usuario_id=uid, matricula_id='123', ativo=True)
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[],
    )
    session.add(turma)
    session.commit()

    response = client.post(
        '/turmas/',
        json={'nome': 'Turma 1', 'professor_id': str(professor.id), 'materia': 'Física'}
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_read_turmas(client):
    response = client.get('/turmas/')
    assert response.status_code == HTTPStatus.OK
    assert 'turmas' in response.json()


def test_read_turma(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123', ativo=True)
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[],
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    response = client.get(f'/turmas/{turma.id}')
    assert response.status_code == HTTPStatus.OK
    assert response.json()['nome'] == 'Turma 1'


def test_read_turma_not_found(client):
    response = client.get(f'/turmas/{uuid4()}')
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_turma(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123', ativo=True)
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[],
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uid, email='teste@teste.com', e_admin=False)

    response = client.put(
        f'/turmas/{turma.id}',
        json={'nome': 'Turma abcd', 'professor_id': str(professor.id), 'materia': 'Física'}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['nome'] == 'Turma abcd'
    assert response.json()['materia'] == 'Física'
    app.dependency_overrides.clear()


def test_update_turma_not_found(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)

    response = client.put(
        f'/turmas/{uuid4()}',
        json={'nome': 'Turma abcd', 'professor_id': str(uuid4()), 'materia': 'Física'}
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    app.dependency_overrides.clear()


def test_update_turma_forbidden(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123', ativo=True)
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[],
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)

    response = client.put(
        f'/turmas/{turma.id}',
        json={'nome': 'Turma abcd', 'professor_id': str(professor.id), 'materia': 'Física'}
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    app.dependency_overrides.clear()


def test_update_turma_erro_alunos(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123', ativo=True)
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[],
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uid, email='teste@teste.com', e_admin=False)

    response = client.put(
        f'/turmas/{turma.id}',
        json={'nome': 'Turma abcd', 'professor_id': str(professor.id), 'materia': 'Física', 'aluno_ids': [str(uuid4())]}
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    app.dependency_overrides.clear()


def test_delete_turma(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123', ativo=True)
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[],
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uid, email='teste@teste.com', e_admin=False)

    response = client.delete(f'/turmas/{turma.id}')
    assert response.status_code == HTTPStatus.OK
    app.dependency_overrides.clear()


def test_delete_turma_not_found(client):
    uid = uuid4()
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uid, email='teste@teste.com', e_admin=False)

    response = client.delete(f'/turmas/{uuid4()}')
    assert response.status_code == HTTPStatus.NOT_FOUND
    app.dependency_overrides.clear()


def test_delete_forbidden(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123', ativo=True)
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[],
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)

    response = client.delete(f'/turmas/{turma.id}')
    assert response.status_code == HTTPStatus.FORBIDDEN
    app.dependency_overrides.clear()
