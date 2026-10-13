from datetime import time
from http import HTTPStatus
from uuid import uuid4

from turma.app import app
from turma.models import Aluno, DiaSemana, Horario, Professor, Turma
from turma.security import CurrentUser, get_current_user


def test_create_horario_forbidden(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123')
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[]
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)
    response = client.post(
        '/horarios/',
        json={
            'turma_id': str(turma.id),
            'professor_id': str(professor.id),
            'dia_semana': DiaSemana.segunda.value,
            'horario_inicio': time(7).isoformat(),
            'horario_fim': time(9).isoformat(),
            'local': 'Sala 1',
        }
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    app.dependency_overrides.clear()


def test_create_horario_conflict_horario(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123')
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[]
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=True)
    response = client.post(
        '/horarios/',
        json={
            'turma_id': str(turma.id),
            'professor_id': str(professor.id),
            'dia_semana': DiaSemana.segunda.value,
            'horario_inicio': time(9).isoformat(),
            'horario_fim': time(5).isoformat(),
            'local': 'Sala 1',
        }
    )
    assert response.status_code == HTTPStatus.CONFLICT
    app.dependency_overrides.clear()


def test_create_horario_conflict_turma(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123')
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[]
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    horario = Horario(
        turma_id=turma.id,
        professor_id=uid,
        dia_semana=DiaSemana.segunda,
        horario_inicio=time(7),
        horario_fim=time(9),
        local='Sala 2',
    )
    session.add(horario)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=True)
    response = client.post(
        '/horarios/',
        json={
            'turma_id': str(turma.id),
            'professor_id': str(professor.id),
            'dia_semana': DiaSemana.segunda.value,
            'horario_inicio': time(8).isoformat(),
            'horario_fim': time(10).isoformat(),
            'local': 'Sala 1',
        }
    )
    assert response.status_code == HTTPStatus.CONFLICT
    app.dependency_overrides.clear()


def test_create_horario_conflict_professor(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123')
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma1 = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[]
    )
    turma2 = Turma(
        nome='Turma 2',
        materia='Mat 2',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[]
    )
    session.add(turma1)
    session.add(turma2)
    session.commit()
    session.refresh(turma1)
    session.refresh(turma2)

    horario = Horario(
        turma_id=turma1.id,
        professor_id=professor.id,
        dia_semana=DiaSemana.segunda,
        horario_inicio=time(7),
        horario_fim=time(9),
        local='Sala 2',
    )
    session.add(horario)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=True)
    response = client.post(
        '/horarios/',
        json={
            'turma_id': str(turma2.id),
            'professor_id': str(professor.id),
            'dia_semana': DiaSemana.segunda.value,
            'horario_inicio': time(8).isoformat(),
            'horario_fim': time(10).isoformat(),
            'local': 'Sala 1',
        }
    )
    assert response.status_code == HTTPStatus.CONFLICT
    app.dependency_overrides.clear()


def test_create_horario_conflict_local(client, session):
    uid1 = uuid4()
    uid2 = uuid4()
    professor1 = Professor(usuario_id=uid1, matricula_id='123')
    professor2 = Professor(usuario_id=uid2, matricula_id='456')
    session.add(professor1)
    session.add(professor2)
    session.commit()
    session.refresh(professor1)
    session.refresh(professor2)

    turma1 = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor1.id,
        professor=professor1,
        avisos=[],
        documentos=[]
    )
    turma2 = Turma(
        nome='Turma 2',
        materia='Mat 2',
        professor_id=professor2.id,
        professor=professor2,
        avisos=[],
        documentos=[]
    )
    session.add(turma1)
    session.add(turma2)
    session.commit()
    session.refresh(turma1)
    session.refresh(turma2)

    horario = Horario(
        turma_id=turma1.id,
        professor_id=professor1.id,
        dia_semana=DiaSemana.segunda,
        horario_inicio=time(7),
        horario_fim=time(9),
        local='Sala 1',
    )
    session.add(horario)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=True)
    response = client.post(
        '/horarios/',
        json={
            'turma_id': str(turma2.id),
            'professor_id': str(professor2.id),
            'dia_semana': DiaSemana.segunda.value,
            'horario_inicio': time(8).isoformat(),
            'horario_fim': time(12).isoformat(),
            'local': 'Sala 1',
        }
    )
    assert response.status_code == HTTPStatus.CONFLICT
    app.dependency_overrides.clear()


def test_create_horario(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='123')
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[]
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=True)
    response = client.post(
        '/horarios/',
        json={
            'turma_id': str(turma.id),
            'professor_id': str(professor.id),
            'dia_semana': DiaSemana.segunda.value,
            'horario_inicio': time(8).isoformat(),
            'horario_fim': time(12).isoformat(),
            'local': 'Sala 1',
        }
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['local'] == 'Sala 1'
    app.dependency_overrides.clear()


def test_read_horarios_aluno_not_found(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=True)
    response = client.get(f'/horarios/aluno/{uuid4()}')
    assert response.status_code == HTTPStatus.NOT_FOUND
    app.dependency_overrides.clear()


def test_read_horarios_aluno_forbidden(client, session):
    aluno = Aluno(usuario_id=uuid4(), matricula_id='1', curso_id='1', ativo=True)
    professor = Professor(usuario_id=uuid4(), matricula_id='123')
    session.add(aluno)
    session.add(professor)
    session.commit()
    session.refresh(aluno)
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[],
        alunos=[aluno],
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    horario = Horario(
        turma_id=turma.id,
        professor_id=professor.id,
        dia_semana=DiaSemana.segunda,
        horario_inicio=time(7),
        horario_fim=time(9),
        local='Sala 1',
    )
    session.add(horario)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)
    response = client.get(f'/horarios/aluno/{aluno.id}')
    assert response.status_code == HTTPStatus.FORBIDDEN
    app.dependency_overrides.clear()


def test_read_horarios_aluno(client, session):
    aluno = Aluno(usuario_id=uuid4(), matricula_id='1', curso_id='1', ativo=True)
    professor = Professor(usuario_id=uuid4(), matricula_id='123')
    session.add(aluno)
    session.add(professor)
    session.commit()
    session.refresh(aluno)
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[],
        alunos=[aluno],
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    horario = Horario(
        turma_id=turma.id,
        professor_id=professor.id,
        dia_semana=DiaSemana.segunda,
        horario_inicio=time(7),
        horario_fim=time(9),
        local='Sala 1',
    )
    session.add(horario)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=aluno.usuario_id, email='teste@teste.com', e_admin=False)
    response = client.get(f'/horarios/aluno/{aluno.id}')
    assert response.status_code == HTTPStatus.OK
    app.dependency_overrides.clear()


def test_read_horarios_professor_not_found(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=True)
    response = client.get(f'/horarios/professor/{uuid4()}')
    assert response.status_code == HTTPStatus.NOT_FOUND
    app.dependency_overrides.clear()


def test_read_horarios_professor_forbidden(client, session):
    professor = Professor(usuario_id=uuid4(), matricula_id='123')
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

    horario = Horario(
        turma_id=turma.id,
        professor_id=professor.id,
        dia_semana=DiaSemana.segunda,
        horario_inicio=time(7),
        horario_fim=time(9),
        local='Sala 1',
    )
    session.add(horario)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)
    response = client.get(f'/horarios/professor/{professor.id}')
    assert response.status_code == HTTPStatus.FORBIDDEN
    app.dependency_overrides.clear()


def test_read_horarios_professor(client, session):
    professor = Professor(usuario_id=uuid4(), matricula_id='123')
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

    horario = Horario(
        turma_id=turma.id,
        professor_id=professor.id,
        dia_semana=DiaSemana.segunda,
        horario_inicio=time(7),
        horario_fim=time(9),
        local='Sala 1',
    )
    session.add(horario)
    session.commit()

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=professor.usuario_id, email='teste@teste.com', e_admin=False)
    response = client.get(f'/horarios/professor/{professor.id}')
    assert response.status_code == HTTPStatus.OK
    app.dependency_overrides.clear()


def test_update_horario_not_found(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)
    response = client.put(
        f'/horarios/{uuid4()}',
        json={
            'turma_id': str(uuid4()),
            'professor_id': str(uuid4()),
            'dia_semana': DiaSemana.segunda.value,
            'horario_inicio': time(5).isoformat(),
            'horario_fim': time(8).isoformat(),
            'local': 'Sala 1',
        }
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    app.dependency_overrides.clear()


def test_update_horario_forbidden(client, session):
    professor = Professor(usuario_id=uuid4(), matricula_id='123')
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[]
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    horario = Horario(
        turma_id=turma.id,
        professor_id=professor.id,
        dia_semana=DiaSemana.quinta,
        horario_inicio=time(7),
        horario_fim=time(9),
        local='Sala 1',
    )
    session.add(horario)
    session.commit()
    session.refresh(horario)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)
    response = client.put(
        f'/horarios/{horario.id}',
        json={
            'turma_id': str(turma.id),
            'professor_id': str(professor.id),
            'dia_semana': DiaSemana.segunda.value,
            'horario_inicio': time(5).isoformat(),
            'horario_fim': time(8).isoformat(),
            'local': 'Sala 1',
        }
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    app.dependency_overrides.clear()


def test_update_horario_conflict_horario(client, session):
    professor = Professor(usuario_id=uuid4(), matricula_id='123')
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[]
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    horario = Horario(
        turma_id=turma.id,
        professor_id=professor.id,
        dia_semana=DiaSemana.quinta,
        horario_inicio=time(7),
        horario_fim=time(9),
        local='Sala 1',
    )
    session.add(horario)
    session.commit()
    session.refresh(horario)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=True)
    response = client.put(
        f'/horarios/{horario.id}',
        json={
            'turma_id': str(turma.id),
            'professor_id': str(professor.id),
            'dia_semana': DiaSemana.segunda.value,
            'horario_inicio': time(8).isoformat(),
            'horario_fim': time(5).isoformat(),
            'local': 'Sala 1',
        }
    )
    assert response.status_code == HTTPStatus.CONFLICT
    app.dependency_overrides.clear()


def test_update_horario_conflict_turma(client, session):
    professor = Professor(usuario_id=uuid4(), matricula_id='123')
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[]
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    horario_ok = Horario(
        turma_id=turma.id,
        professor_id=professor.id,
        dia_semana=DiaSemana.quinta,
        horario_inicio=time(7),
        horario_fim=time(9),
        local='Sala 1',
    )
    session.add(horario_ok)
    session.commit()
    session.refresh(horario_ok)

    horario = Horario(
        turma_id=turma.id,
        professor_id=professor.id,
        dia_semana=DiaSemana.quinta,
        horario_inicio=time(10),
        horario_fim=time(12),
        local='Sala 2',
    )
    session.add(horario)
    session.commit()
    session.refresh(horario)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=True)
    response = client.put(
        f'/horarios/{horario.id}',
        json={
            'turma_id': str(turma.id),
            'professor_id': str(professor.id),
            'dia_semana': DiaSemana.quinta.value,
            'horario_inicio': time(8).isoformat(),
            'horario_fim': time(10).isoformat(),
            'local': 'Sala 2',
        }
    )
    assert response.status_code == HTTPStatus.CONFLICT
    app.dependency_overrides.clear()


def test_update_horario_conflict_professor(client, session):
    professor = Professor(usuario_id=uuid4(), matricula_id='123')
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma1 = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[]
    )
    turma2 = Turma(
        nome='Turma 2',
        materia='Mat 2',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[]
    )
    session.add(turma1)
    session.add(turma2)
    session.commit()
    session.refresh(turma1)
    session.refresh(turma2)

    horario_ok = Horario(
        turma_id=turma1.id,
        professor_id=professor.id,
        dia_semana=DiaSemana.quinta,
        horario_inicio=time(7),
        horario_fim=time(9),
        local='Sala 1',
    )
    session.add(horario_ok)
    session.commit()
    session.refresh(horario_ok)

    horario = Horario(
        turma_id=turma2.id,
        professor_id=professor.id,
        dia_semana=DiaSemana.quinta,
        horario_inicio=time(10),
        horario_fim=time(12),
        local='Sala 2',
    )
    session.add(horario)
    session.commit()
    session.refresh(horario)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=True)
    response = client.put(
        f'/horarios/{horario.id}',
        json={
            'turma_id': str(turma2.id),
            'professor_id': str(professor.id),
            'dia_semana': DiaSemana.quinta.value,
            'horario_inicio': time(8).isoformat(),
            'horario_fim': time(10).isoformat(),
            'local': 'Sala 2',
        }
    )
    assert response.status_code == HTTPStatus.CONFLICT
    app.dependency_overrides.clear()


def test_update_horario_conflict_local(client, session):
    professor1 = Professor(usuario_id=uuid4(), matricula_id='123')
    professor2 = Professor(usuario_id=uuid4(), matricula_id='456')
    session.add(professor1)
    session.add(professor2)
    session.commit()
    session.refresh(professor1)
    session.refresh(professor2)

    turma1 = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor1.id,
        professor=professor1,
        avisos=[],
        documentos=[]
    )
    turma2 = Turma(
        nome='Turma 2',
        materia='Mat 2',
        professor_id=professor2.id,
        professor=professor2,
        avisos=[],
        documentos=[]
    )
    session.add(turma1)
    session.add(turma2)
    session.commit()
    session.refresh(turma1)
    session.refresh(turma2)

    horario_ok = Horario(
        turma_id=turma1.id,
        professor_id=professor1.id,
        dia_semana=DiaSemana.quinta,
        horario_inicio=time(7),
        horario_fim=time(9),
        local='Sala 1',
    )
    session.add(horario_ok)
    session.commit()
    session.refresh(horario_ok)

    horario = Horario(
        turma_id=turma2.id,
        professor_id=professor2.id,
        dia_semana=DiaSemana.quinta,
        horario_inicio=time(10),
        horario_fim=time(12),
        local='Sala 2',
    )
    session.add(horario)
    session.commit()
    session.refresh(horario)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=True)
    response = client.put(
        f'/horarios/{horario.id}',
        json={
            'turma_id': str(turma2.id),
            'professor_id': str(professor2.id),
            'dia_semana': DiaSemana.quinta.value,
            'horario_inicio': time(10).isoformat(),
            'horario_fim': time(12).isoformat(),
            'local': 'Sala 1',
        }
    )
    assert response.status_code == HTTPStatus.CONFLICT
    app.dependency_overrides.clear()


def test_update_horario(client, session):
    professor = Professor(usuario_id=uuid4(), matricula_id='123')
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[]
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    horario = Horario(
        turma_id=turma.id,
        professor_id=professor.id,
        dia_semana=DiaSemana.quinta,
        horario_inicio=time(7),
        horario_fim=time(9),
        local='Sala 1',
    )
    session.add(horario)
    session.commit()
    session.refresh(horario)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=True)
    response = client.put(
        f'/horarios/{horario.id}',
        json={
            'turma_id': str(turma.id),
            'professor_id': str(professor.id),
            'dia_semana': DiaSemana.terca.value,
            'horario_inicio': time(8).isoformat(),
            'horario_fim': time(12).isoformat(),
            'local': 'Sala 2',
        }
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['local'] == 'Sala 2'
    app.dependency_overrides.clear()


def test_delete_horario_not_found(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=True)
    response = client.delete(f'/horarios/{uuid4()}')
    assert response.status_code == HTTPStatus.NOT_FOUND
    app.dependency_overrides.clear()


def test_delete_horario_forbidden(client, session):
    professor = Professor(usuario_id=uuid4(), matricula_id='123')
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[]
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    horario = Horario(
        turma_id=turma.id,
        professor_id=professor.id,
        dia_semana=DiaSemana.quinta,
        horario_inicio=time(7),
        horario_fim=time(9),
        local='Sala 1',
    )
    session.add(horario)
    session.commit()
    session.refresh(horario)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)
    response = client.delete(f'/horarios/{horario.id}')
    assert response.status_code == HTTPStatus.FORBIDDEN
    app.dependency_overrides.clear()


def test_delete_horario(client, session):
    professor = Professor(usuario_id=uuid4(), matricula_id='123')
    session.add(professor)
    session.commit()
    session.refresh(professor)

    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        professor_id=professor.id,
        professor=professor,
        avisos=[],
        documentos=[]
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    horario = Horario(
        turma_id=turma.id,
        professor_id=professor.id,
        dia_semana=DiaSemana.quinta,
        horario_inicio=time(7),
        horario_fim=time(9),
        local='Sala 1',
    )
    session.add(horario)
    session.commit()
    session.refresh(horario)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=True)
    response = client.delete(f'/horarios/{horario.id}')
    assert response.status_code == HTTPStatus.OK
    app.dependency_overrides.clear()
