from http import HTTPStatus
from uuid import UUID, uuid4

from turma.app import app
from turma.models import Aluno, Professor, Turma
from turma.security import CurrentUser, get_current_user

CURSO_ID = '11111111-1111-1111-1111-111111111111'
PERIODO = '2026.2'
CAPACIDADE = 30
CAPACIDADE_NOVA = 50
AVISO_ANTIGO = {
    'id': '7d0c2f0e-6a2b-4c55-9a53-1f1f1f1f1f01',
    'autor': 'Professor',
    'data': '2026-10-01',
    'titulo': 'Aviso antigo',
    'mensagem': 'aviso antigo',
}
AVISO_NOVO = {
    'autor': 'Professor',
    'data': '2026-10-05',
    'titulo': 'Aviso novo',
    'mensagem': 'aviso novo',
}


def como(usuario_id, e_admin=False):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=usuario_id, email='usuario@teste.com', e_admin=e_admin
    )


def cenario(session, com_aluno=True):
    professor = Professor(usuario_id=uuid4(), matricula_id=f'P{uuid4().hex[:6]}', ativo=True)
    aluno = Aluno(usuario_id=uuid4(), matricula_id=f'A{uuid4().hex[:6]}', curso_id=CURSO_ID, ativo=True)
    session.add_all([professor, aluno])
    session.commit()
    session.refresh(professor)
    session.refresh(aluno)

    turma = Turma(
        nome='Turma Base',
        materia='Matemática',
        codigo='MAT101',
        curso_id=UUID(CURSO_ID),
        periodo_letivo=PERIODO,
        capacidade=CAPACIDADE,
        professor_id=professor.id,
        professor=professor,
        alunos=[aluno] if com_aluno else [],
        avisos=[AVISO_ANTIGO],
        documentos=[],
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)
    return turma, professor, aluno


def corpo(turma, professor, **campos):
    base = {
        'nome': turma.nome,
        'codigo': turma.codigo,
        'materia': turma.materia,
        'curso_id': CURSO_ID,
        'periodo_letivo': PERIODO,
        'capacidade': turma.capacidade,
        'professor_id': str(professor.id),
        'documentos': [],
        'avisos': [],
    }
    base.update(campos)
    return base


def test_professor_responsavel_nao_cria_turma(client, session):
    _, professor, _ = cenario(session)
    como(professor.usuario_id)

    resposta = client.post(
        '/turmas/',
        json={
            'nome': 'Nova',
            'codigo': 'X1',
            'materia': 'X',
            'curso_id': CURSO_ID,
            'periodo_letivo': PERIODO,
            'capacidade': CAPACIDADE,
            'professor_id': str(professor.id),
        },
    )

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_professor_responsavel_nao_exclui_turma(client, session):
    turma, professor, _ = cenario(session)
    como(professor.usuario_id)

    resposta = client.delete(f'/turmas/{turma.id}')

    assert resposta.status_code == HTTPStatus.FORBIDDEN
    session.expire_all()
    assert session.get(Turma, turma.id) is not None


def test_professor_responsavel_edita_conteudo(client, session):
    turma, professor, _ = cenario(session)
    como(professor.usuario_id)

    resposta = client.put(
        f'/turmas/{turma.id}',
        json=corpo(turma, professor, nome='Novo nome', materia='Cálculo', avisos=[AVISO_NOVO], documentos=['./a.pdf']),
    )

    assert resposta.status_code == HTTPStatus.OK
    session.rollback()
    persistida = session.get(Turma, turma.id)
    assert persistida.nome == 'Novo nome'
    assert persistida.materia == 'Cálculo'
    assert [aviso['mensagem'] for aviso in persistida.avisos] == ['aviso novo']
    assert persistida.documentos == ['./a.pdf']


def test_professor_responsavel_nao_altera_capacidade(client, session):
    turma, professor, _ = cenario(session)
    como(professor.usuario_id)

    resposta = client.put(f'/turmas/{turma.id}', json=corpo(turma, professor, capacidade=99))

    assert resposta.status_code == HTTPStatus.FORBIDDEN
    session.rollback()
    assert session.get(Turma, turma.id).capacidade == CAPACIDADE


def test_professor_responsavel_nao_altera_codigo_nem_periodo(client, session):
    turma, professor, _ = cenario(session)
    como(professor.usuario_id)

    por_codigo = client.put(f'/turmas/{turma.id}', json=corpo(turma, professor, codigo='OUTRO'))
    por_periodo = client.put(f'/turmas/{turma.id}', json=corpo(turma, professor, periodo_letivo='2027.1'))

    assert por_codigo.status_code == HTTPStatus.FORBIDDEN
    assert por_periodo.status_code == HTTPStatus.FORBIDDEN


def test_professor_responsavel_nao_troca_alunos(client, session):
    turma, professor, _ = cenario(session)
    como(professor.usuario_id)

    resposta = client.put(f'/turmas/{turma.id}', json=corpo(turma, professor, aluno_ids=[]))

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_put_sem_aluno_ids_preserva_matriculas(client, session):
    turma, professor, aluno = cenario(session)
    como(uuid4(), e_admin=True)

    resposta = client.put(f'/turmas/{turma.id}', json=corpo(turma, professor, nome='Sem lista'))

    assert resposta.status_code == HTTPStatus.OK
    session.rollback()
    persistida = session.get(Turma, turma.id)
    assert [a.id for a in persistida.alunos] == [aluno.id]


def test_admin_substitui_alunos_quando_lista_e_enviada(client, session):
    turma, professor, aluno = cenario(session)
    como(uuid4(), e_admin=True)

    resposta = client.put(f'/turmas/{turma.id}', json=corpo(turma, professor, aluno_ids=[]))

    assert resposta.status_code == HTTPStatus.OK
    session.rollback()
    assert session.get(Turma, turma.id).alunos == []


def test_admin_altera_capacidade_e_codigo(client, session):
    turma, professor, _ = cenario(session)
    como(uuid4(), e_admin=True)

    resposta = client.put(f'/turmas/{turma.id}', json=corpo(turma, professor, capacidade=CAPACIDADE_NOVA, codigo='NOVO'))

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json()['capacidade'] == CAPACIDADE_NOVA
    assert resposta.json()['codigo'] == 'NOVO'


def test_ofertas_exige_token(client, session):
    app.dependency_overrides.pop(get_current_user, None)

    resposta = client.get('/turmas/ofertas', params={'curso_id': CURSO_ID, 'periodo_letivo': PERIODO})

    assert resposta.status_code == HTTPStatus.UNAUTHORIZED


def test_ofertas_aluno_comum_consulta(client, session):
    cenario(session)
    como(uuid4())

    resposta = client.get('/turmas/ofertas', params={'curso_id': CURSO_ID, 'periodo_letivo': PERIODO})

    assert resposta.status_code == HTTPStatus.OK
