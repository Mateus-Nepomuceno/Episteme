from datetime import time
from http import HTTPStatus
from uuid import UUID, uuid4

from turma.app import app
from turma.models import Aluno, DiaSemana, Horario, Professor, Turma
from turma.security import CurrentUser, get_current_user

CURSO_ID = '11111111-1111-1111-1111-111111111111'


def como(usuario_id, e_admin=False):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=usuario_id, email='usuario@teste.com', e_admin=e_admin
    )


def criar_aluno(session):
    aluno = Aluno(
        usuario_id=uuid4(),
        matricula_id=f'A{uuid4().hex[:6]}',
        curso_id=CURSO_ID,
        ativo=True,
    )
    session.add(aluno)
    session.commit()
    session.refresh(aluno)
    return aluno


def criar_turma(session, nome, professor, alunos):
    turma = Turma(
        nome=nome,
        materia='Matemática',
        codigo=f'MAT{uuid4().hex[:4]}',
        curso_id=UUID(CURSO_ID),
        periodo_letivo='2026.2',
        capacidade=30,
        professor_id=professor.id,
        professor=professor,
        alunos=alunos,
        documentos=[],
        avisos=[],
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


def criar_professor(session):
    professor = Professor(
        usuario_id=uuid4(), matricula_id=f'P{uuid4().hex[:6]}', ativo=True
    )
    session.add(professor)
    session.commit()
    session.refresh(professor)
    return professor


def test_dono_recebe_turmas_com_professor_e_horarios(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    criar_turma(session, 'Turma B', professor, [aluno])
    criar_turma(session, 'Turma A', professor, [aluno])
    como(aluno.usuario_id)

    resposta = client.get(f'/turmas/aluno/{aluno.id}')

    assert resposta.status_code == HTTPStatus.OK
    turmas = resposta.json()['turmas']
    assert [turma['nome'] for turma in turmas] == ['Turma A', 'Turma B']
    primeira = turmas[0]
    assert primeira['professor']['id'] == str(professor.id)
    assert primeira['professor']['matricula_id'] == professor.matricula_id
    assert primeira['horarios'] == [
        {
            'dia_semana': 'Segunda',
            'horario_inicio': '08:00:00',
            'horario_fim': '10:00:00',
            'local': 'Sala 101',
        }
    ]


def test_resposta_nao_expoe_lista_de_alunos(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    colega = criar_aluno(session)
    criar_turma(session, 'Turma', professor, [aluno, colega])
    como(aluno.usuario_id)

    resposta = client.get(f'/turmas/aluno/{aluno.id}')

    turma = resposta.json()['turmas'][0]
    assert 'alunos' not in turma
    assert str(colega.id) not in resposta.text


def test_outro_aluno_recebe_403(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    outro = criar_aluno(session)
    criar_turma(session, 'Turma', professor, [aluno])
    como(outro.usuario_id)

    resposta = client.get(f'/turmas/aluno/{aluno.id}')

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_administrador_recebe_turmas_de_qualquer_aluno(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    criar_turma(session, 'Turma', professor, [aluno])
    como(uuid4(), e_admin=True)

    resposta = client.get(f'/turmas/aluno/{aluno.id}')

    assert resposta.status_code == HTTPStatus.OK
    assert len(resposta.json()['turmas']) == 1


def test_aluno_sem_turma_recebe_lista_vazia(client, session):
    aluno = criar_aluno(session)
    como(aluno.usuario_id)

    resposta = client.get(f'/turmas/aluno/{aluno.id}')

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json() == {'turmas': []}


def test_aluno_inexistente_recebe_404(client, session):
    como(uuid4())

    resposta = client.get(f'/turmas/aluno/{uuid4()}')

    assert resposta.status_code == HTTPStatus.NOT_FOUND


def test_turmas_do_aluno_nao_aparecem_para_outro_aluno(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    outro = criar_aluno(session)
    criar_turma(session, 'Turma do outro', professor, [outro])
    como(aluno.usuario_id)

    resposta = client.get(f'/turmas/aluno/{aluno.id}')

    assert resposta.json() == {'turmas': []}
