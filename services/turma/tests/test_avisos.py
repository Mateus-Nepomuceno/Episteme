from http import HTTPStatus
from uuid import UUID, uuid4

from turma.app import app
from turma.models import Aluno, Professor, Turma
from turma.security import CurrentUser, get_current_user

CURSO_ID = '11111111-1111-1111-1111-111111111111'
PERIODO = '2026.2'


def como(usuario_id, e_admin=False):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=usuario_id, email='usuario@teste.com', e_admin=e_admin
    )


def criar_professor(session):
    professor = Professor(
        usuario_id=uuid4(), matricula_id=f'P{uuid4().hex[:6]}', ativo=True
    )
    session.add(professor)
    session.commit()
    session.refresh(professor)
    return professor


def criar_turma(session, professor):
    turma = Turma(
        nome='Turma',
        materia='Matemática',
        codigo=f'MAT{uuid4().hex[:4]}',
        curso_id=UUID(CURSO_ID),
        periodo_letivo=PERIODO,
        capacidade=30,
        professor_id=professor.id,
        professor=professor,
        alunos=[],
        documentos=[],
        avisos=[],
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)
    return turma


def corpo_turma(turma, professor, avisos):
    return {
        'nome': turma.nome,
        'codigo': turma.codigo,
        'materia': turma.materia,
        'curso_id': CURSO_ID,
        'periodo_letivo': PERIODO,
        'capacidade': turma.capacidade,
        'professor_id': str(professor.id),
        'documentos': [],
        'avisos': avisos,
    }


AVISO = {
    'autor': 'Prof. Ricardo',
    'data': '2026-10-05',
    'titulo': 'Prova adiada',
    'mensagem': 'A prova passa para sexta-feira.',
}


def test_professor_responsavel_grava_aviso_estruturado(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor)
    como(professor.usuario_id)

    resposta = client.put(
        f'/turmas/{turma.id}',
        json=corpo_turma(turma, professor, [AVISO]),
    )

    assert resposta.status_code == HTTPStatus.OK
    aviso = resposta.json()['avisos'][0]
    assert UUID(aviso['id'])
    assert aviso['autor'] == 'Prof. Ricardo'
    assert aviso['data'] == '2026-10-05'
    assert aviso['titulo'] == 'Prova adiada'
    assert aviso['mensagem'] == 'A prova passa para sexta-feira.'


def test_get_devolve_os_campos_do_aviso(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor)
    como(professor.usuario_id)
    client.put(
        f'/turmas/{turma.id}', json=corpo_turma(turma, professor, [AVISO])
    )

    resposta = client.get(f'/turmas/{turma.id}')

    avisos = resposta.json()['avisos']
    assert len(avisos) == 1
    assert set(avisos[0]) == {'id', 'autor', 'data', 'titulo', 'mensagem'}
    assert avisos[0]['titulo'] == 'Prova adiada'


def test_aviso_como_texto_simples_e_recusado(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor)
    como(professor.usuario_id)

    resposta = client.put(
        f'/turmas/{turma.id}',
        json=corpo_turma(turma, professor, ['texto solto']),
    )

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_aviso_sem_titulo_ou_data_e_recusado(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor)
    como(professor.usuario_id)
    sem_titulo = {k: v for k, v in AVISO.items() if k != 'titulo'}
    sem_data = {k: v for k, v in AVISO.items() if k != 'data'}

    resposta = client.put(
        f'/turmas/{turma.id}',
        json=corpo_turma(turma, professor, [sem_titulo, sem_data]),
    )

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_outro_professor_nao_grava_avisos(client, session):
    professor = criar_professor(session)
    outro = criar_professor(session)
    turma = criar_turma(session, professor)
    como(outro.usuario_id)

    resposta = client.put(
        f'/turmas/{turma.id}',
        json=corpo_turma(turma, professor, [AVISO]),
    )

    assert resposta.status_code == HTTPStatus.FORBIDDEN
    session.rollback()
    assert session.get(Turma, turma.id).avisos == []


def test_aluno_nao_grava_avisos(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor)
    aluno = Aluno(
        usuario_id=uuid4(),
        matricula_id='A000001',
        curso_id=CURSO_ID,
        ativo=True,
    )
    session.add(aluno)
    session.commit()
    como(aluno.usuario_id)

    resposta = client.put(
        f'/turmas/{turma.id}',
        json=corpo_turma(turma, professor, [AVISO]),
    )

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_administrador_grava_avisos_de_qualquer_turma(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor)
    como(uuid4(), e_admin=True)

    resposta = client.put(
        f'/turmas/{turma.id}',
        json=corpo_turma(turma, professor, [AVISO]),
    )

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json()['avisos'][0]['titulo'] == 'Prova adiada'


def test_criacao_de_turma_grava_avisos_estruturados(client, session):
    professor = criar_professor(session)
    como(uuid4(), e_admin=True)

    resposta = client.post(
        '/turmas/',
        json={
            'nome': 'Nova',
            'codigo': 'NOV1',
            'materia': 'Física',
            'curso_id': CURSO_ID,
            'periodo_letivo': PERIODO,
            'capacidade': 20,
            'professor_id': str(professor.id),
            'avisos': [AVISO],
        },
    )

    assert resposta.status_code == HTTPStatus.CREATED
    assert resposta.json()['avisos'][0]['autor'] == 'Prof. Ricardo'
