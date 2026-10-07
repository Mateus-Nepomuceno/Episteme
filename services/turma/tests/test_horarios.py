from datetime import time
from http import HTTPStatus
from uuid import uuid4

from turma.models import DiaSemana, Horario, Professor, Turma


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
