from http import HTTPStatus
from uuid import uuid4

from tests.test_modulos import como, criar_aluno, criar_turma
from turma.models import Professor


def test_turma_devolve_nome_do_professor_para_o_aluno(client, session):
    professor = Professor(
        usuario_id=uuid4(),
        matricula_id='P000111',
        ativo=True,
        nome='Rafael Oliveira',
    )
    session.add(professor)
    session.commit()
    session.refresh(professor)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(aluno.usuario_id)

    resposta = client.get(f'/turmas/{turma.id}')
    turmas_do_aluno = client.get(f'/turmas/aluno/{aluno.id}').json()['turmas']

    assert resposta.json()['professor']['nome'] == 'Rafael Oliveira'
    assert turmas_do_aluno[0]['professor']['nome'] == 'Rafael Oliveira'


def test_professor_sem_nome_devolve_nulo(client, session):
    professor = Professor(usuario_id=uuid4(), matricula_id='P000222', ativo=True)
    session.add(professor)
    session.commit()
    session.refresh(professor)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(aluno.usuario_id)

    resposta = client.get(f'/turmas/{turma.id}')

    assert resposta.json()['professor']['nome'] is None


def test_admin_cadastra_professor_com_nome(client, session):
    como(uuid4(), e_admin=True)

    resposta = client.post(
        '/professores/',
        json={
            'usuario_id': str(uuid4()),
            'matricula_id': 'P000333',
            'ativo': True,
            'nome': 'Helena Silva',
        },
    )

    assert resposta.status_code == HTTPStatus.CREATED
    assert resposta.json()['nome'] == 'Helena Silva'
