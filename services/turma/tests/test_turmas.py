from http import HTTPStatus
from uuid import uuid4

from turma.app import app
from turma.models import Aluno, Professor, Turma
from turma.security import CurrentUser, get_current_user

CURSO_ID = str(uuid4())
CAPACIDADE_TURMA = 30
CAPACIDADE_NOVA = 45


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
            'materia': 'Física', 'codigo': 'FIS101', 'curso_id': CURSO_ID, 'periodo_letivo': '2026.2', 'capacidade': CAPACIDADE_TURMA,
            'aluno_ids': [str(aluno1.id), str(aluno2.id)],
            'documentos': ['./documento.pdf'],
            'aviso': ['Aviso 1', 'Aviso 2'],
        }
    )
    assert response.status_code == HTTPStatus.CREATED


def test_create_turma_sem_prof(client, session):
    response = client.post(
        '/turmas/',
        json={'nome': 'Turma 1', 'professor_id': str(uuid4()), 'materia': 'Física', 'codigo': 'FIS101', 'curso_id': CURSO_ID, 'periodo_letivo': '2026.2', 'capacidade': CAPACIDADE_TURMA}
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
            'materia': 'Física', 'codigo': 'FIS101', 'curso_id': CURSO_ID, 'periodo_letivo': '2026.2', 'capacidade': CAPACIDADE_TURMA,
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
        json={'nome': 'Turma 1', 'professor_id': str(professor.id), 'materia': 'Física', 'codigo': 'FIS101', 'curso_id': CURSO_ID, 'periodo_letivo': '2026.2', 'capacidade': CAPACIDADE_TURMA}
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
        json={'nome': 'Turma abcd', 'professor_id': str(professor.id), 'materia': 'Física', 'codigo': 'FIS101', 'curso_id': CURSO_ID, 'periodo_letivo': '2026.2', 'capacidade': CAPACIDADE_TURMA}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['nome'] == 'Turma abcd'
    assert response.json()['materia'] == 'Física'
    app.dependency_overrides.clear()


def test_update_turma_not_found(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(id=uuid4(), email='teste@teste.com', e_admin=False)

    response = client.put(
        f'/turmas/{uuid4()}',
        json={'nome': 'Turma abcd', 'professor_id': str(uuid4()), 'materia': 'Física', 'codigo': 'FIS101', 'curso_id': CURSO_ID, 'periodo_letivo': '2026.2', 'capacidade': CAPACIDADE_TURMA}
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
        json={'nome': 'Turma abcd', 'professor_id': str(professor.id), 'materia': 'Física', 'codigo': 'FIS101', 'curso_id': CURSO_ID, 'periodo_letivo': '2026.2', 'capacidade': CAPACIDADE_TURMA}
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
        json={'nome': 'Turma abcd', 'professor_id': str(professor.id), 'materia': 'Física', 'codigo': 'FIS101', 'curso_id': CURSO_ID, 'periodo_letivo': '2026.2', 'capacidade': CAPACIDADE_TURMA, 'aluno_ids': [str(uuid4())]}
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


def _payload_turma(**campos):
    payload = {
        'nome': 'Turma X',
        'codigo': 'FIS101',
        'materia': 'Física',
        'curso_id': CURSO_ID,
        'periodo_letivo': '2026.2',
        'capacidade': CAPACIDADE_TURMA,
    }
    payload.update(campos)
    return payload


def test_create_turma_sem_professor_alocado(client, session):
    response = client.post('/turmas/', json=_payload_turma())

    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['professor'] is None
    assert response.json()['capacidade'] == CAPACIDADE_TURMA
    assert response.json()['curso_id'] == CURSO_ID
    assert response.json()['periodo_letivo'] == '2026.2'
    assert response.json()['codigo'] == 'FIS101'


def test_create_turma_exige_capacidade_positiva(client, session):
    sem_capacidade = _payload_turma()
    del sem_capacidade['capacidade']

    assert (
        client.post('/turmas/', json=sem_capacidade).status_code
        == HTTPStatus.UNPROCESSABLE_ENTITY
    )
    assert (
        client.post('/turmas/', json=_payload_turma(capacidade=0)).status_code
        == HTTPStatus.UNPROCESSABLE_ENTITY
    )


def test_create_turma_exige_codigo_curso_e_periodo(client, session):
    for campo in ('codigo', 'curso_id', 'periodo_letivo'):
        payload = _payload_turma()
        del payload[campo]
        response = client.post('/turmas/', json=payload)
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, campo


def test_create_turma_periodo_letivo_com_formato_invalido(client, session):
    response = client.post(
        '/turmas/', json=_payload_turma(periodo_letivo='2026-2')
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_turmas_do_mesmo_professor_com_nomes_diferentes(
    client, session
):
    professor = Professor(usuario_id=uuid4(), matricula_id='777', ativo=True)
    session.add(professor)
    session.commit()
    session.refresh(professor)

    primeira = client.post(
        '/turmas/',
        json=_payload_turma(nome='Turma 1', professor_id=str(professor.id)),
    )
    segunda = client.post(
        '/turmas/',
        json=_payload_turma(nome='Turma 2', professor_id=str(professor.id)),
    )

    assert primeira.status_code == HTTPStatus.CREATED
    assert segunda.status_code == HTTPStatus.CREATED


def test_read_turma_expoe_professor_horarios_e_oferta(client, session):
    professor = Professor(usuario_id=uuid4(), matricula_id='888', ativo=True)
    session.add(professor)
    session.commit()
    session.refresh(professor)

    response = client.post(
        '/turmas/',
        json=_payload_turma(professor_id=str(professor.id)),
    )
    turma_id = response.json()['id']

    response = client.get(f'/turmas/{turma_id}')

    assert response.status_code == HTTPStatus.OK
    dados = response.json()
    assert dados['professor']['matricula_id'] == '888'
    assert dados['horarios'] == []
    assert dados['codigo'] == 'FIS101'
    assert dados['capacidade'] == CAPACIDADE_TURMA


def test_update_turma_persiste_novos_campos_de_oferta(client, session):
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

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uid, email='teste@teste.com', e_admin=False
    )

    response = client.put(
        f'/turmas/{turma.id}',
        json=_payload_turma(
            nome='Turma nova',
            codigo='MAT999',
            capacidade=CAPACIDADE_NOVA,
            professor_id=str(professor.id),
        ),
    )
    app.dependency_overrides.clear()

    assert response.status_code == HTTPStatus.OK
    session.rollback()
    persistida = session.get(Turma, turma.id)
    assert persistida.nome == 'Turma nova'
    assert persistida.codigo == 'MAT999'
    assert persistida.capacidade == CAPACIDADE_NOVA
    assert persistida.curso_id is not None


def test_update_turma_sem_professor_so_admin_pode(client, session):
    turma = Turma(
        nome='Turma 1',
        materia='Mat 1',
        avisos=[],
        documentos=[],
        codigo='MAT1',
        curso_id=uuid4(),
        periodo_letivo='2026.2',
        capacidade=10,
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='aluno@teste.com', e_admin=False
    )
    response = client.put(f'/turmas/{turma.id}', json=_payload_turma())
    assert response.status_code == HTTPStatus.FORBIDDEN

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='admin@teste.com', e_admin=True
    )
    response = client.put(f'/turmas/{turma.id}', json=_payload_turma())
    app.dependency_overrides.clear()
    assert response.status_code == HTTPStatus.OK


def _usuario_como(usuario_id, e_admin=False):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=usuario_id, email='usuario@teste.com', e_admin=e_admin
    )


def test_create_turma_pelo_professor_responsavel(client, session):
    uid = uuid4()
    professor = Professor(usuario_id=uid, matricula_id='555', ativo=True)
    session.add(professor)
    session.commit()
    session.refresh(professor)

    _usuario_como(uid)
    response = client.post(
        '/turmas/',
        json=_payload_turma(professor_id=str(professor.id)),
    )
    app.dependency_overrides.clear()

    assert response.status_code == HTTPStatus.CREATED


def test_create_turma_por_outro_professor_e_negado(client, session):
    professor = Professor(usuario_id=uuid4(), matricula_id='556', ativo=True)
    session.add(professor)
    session.commit()
    session.refresh(professor)

    _usuario_como(uuid4())
    response = client.post(
        '/turmas/',
        json=_payload_turma(professor_id=str(professor.id)),
    )
    app.dependency_overrides.clear()

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_create_turma_sem_professor_so_admin(client, session):
    _usuario_como(uuid4())
    response = client.post('/turmas/', json=_payload_turma())
    app.dependency_overrides.clear()

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_create_turma_sem_autenticacao(client, session):
    app.dependency_overrides.pop(get_current_user, None)
    response = client.post('/turmas/', json=_payload_turma())

    assert response.status_code == HTTPStatus.UNAUTHORIZED
