from datetime import time
from http import HTTPStatus
from uuid import UUID, uuid4

from turma.app import app
from turma.models import Aluno, DiaSemana, Horario, Professor, Turma
from turma.security import CurrentUser, get_current_user

CURSO_ID = '11111111-1111-1111-1111-111111111111'


def como(usuario_id):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=usuario_id, email='usuario@teste.com', e_admin=False
    )


def criar_aluno(session):
    aluno = Aluno(
        usuario_id=uuid4(),
        curso_id=CURSO_ID,
        ativo=True,
    )
    session.add(aluno)
    session.commit()
    session.refresh(aluno)
    return aluno


def criar_professor(session):
    professor = Professor(
        usuario_id=uuid4(), ativo=True
    )
    session.add(professor)
    session.commit()
    session.refresh(professor)
    return professor


def criar_turma(session, materia, professor, alunos, avisos):
    turma = Turma(
        nome=f'Turma {materia}',
        materia=materia,
        codigo=f'{materia[:3].upper()}{uuid4().hex[:4]}',
        curso_id=UUID(CURSO_ID),
        periodo_letivo='2026.2',
        capacidade=30,
        professor_id=professor.id,
        professor=professor,
        alunos=alunos,
        documentos=[],
        avisos=avisos,
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)
    session.add(
        Horario(
            turma_id=turma.id,
            professor_id=professor.id,
            dia_semana=DiaSemana.segunda,
            horario_inicio=time(8),
            horario_fim=time(10),
            local='Sala 101',
        )
    )
    session.commit()
    session.refresh(turma)
    return turma


def aviso(titulo, data):
    return {
        'id': str(uuid4()),
        'autor': 'Prof. Teste',
        'data': data,
        'titulo': titulo,
        'mensagem': f'Mensagem de {titulo}',
    }


def test_aluno_recebe_avisos_das_proprias_turmas_ordenados_por_data(
    client, session
):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    criar_turma(
        session,
        'Banco de Dados',
        professor,
        [aluno],
        [aviso('Antigo', '2026-09-01'), aviso('Recente', '2026-09-20')],
    )
    criar_turma(
        session, 'Redes', professor, [aluno], [aviso('Meio', '2026-09-10')]
    )
    como(aluno.usuario_id)

    resposta = client.get('/alunos/me/avisos')

    assert resposta.status_code == HTTPStatus.OK
    avisos = resposta.json()['avisos']
    assert [a['titulo'] for a in avisos] == ['Recente', 'Meio', 'Antigo']
    assert avisos[0]['disciplina'] == 'Banco de Dados'
    assert avisos[0]['autor'] == 'Prof. Teste'
    assert avisos[0]['data'] == '2026-09-20'
    assert set(avisos[0]) == {
        'id',
        'turma_id',
        'disciplina',
        'autor',
        'data',
        'titulo',
        'mensagem',
    }


def test_limite_restringe_quantidade_de_avisos(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    criar_turma(
        session,
        'Redes',
        professor,
        [aluno],
        [
            aviso('A', '2026-09-01'),
            aviso('B', '2026-09-02'),
            aviso('C', '2026-09-03'),
        ],
    )
    como(aluno.usuario_id)

    resposta = client.get('/alunos/me/avisos?limite=2')

    assert [a['titulo'] for a in resposta.json()['avisos']] == ['C', 'B']


def test_avisos_de_turma_alheia_nao_aparecem(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    outro = criar_aluno(session)
    criar_turma(
        session, 'Redes', professor, [outro], [aviso('Alheio', '2026-09-01')]
    )
    como(aluno.usuario_id)

    resposta = client.get('/alunos/me/avisos')

    assert resposta.json()['avisos'] == []


def test_usuario_sem_cadastro_de_aluno_recebe_lista_vazia(client, session):
    como(uuid4())

    resposta = client.get('/alunos/me/avisos')

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json() == {'avisos': []}
