from http import HTTPStatus

from tests.test_modulos import como, criar_aluno, criar_professor, criar_turma


def test_professor_registra_aviso_e_aluno_recebe_na_turma(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)

    resposta = client.post(
        f'/turmas/{turma.id}/avisos',
        json={
            'autor': 'Prof. Teste',
            'data': '2026-10-20',
            'titulo': 'Prova adiada',
            'mensagem': 'A prova foi para a próxima semana.',
        },
    )
    como(aluno.usuario_id)
    avisos_da_turma = client.get('/alunos/me/avisos').json()['avisos']

    assert resposta.status_code == HTTPStatus.CREATED
    assert resposta.json()['titulo'] == 'Prova adiada'
    assert [a['titulo'] for a in avisos_da_turma] == ['Prova adiada']


def test_aviso_sem_mensagem_e_rejeitado(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)

    resposta = client.post(
        f'/turmas/{turma.id}/avisos',
        json={'autor': 'Prof', 'data': '2026-10-20', 'titulo': 'X', 'mensagem': ''},
    )

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_aluno_nao_registra_aviso(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(aluno.usuario_id)

    resposta = client.post(
        f'/turmas/{turma.id}/avisos',
        json={'autor': 'Aluno', 'data': '2026-10-20', 'titulo': 'X', 'mensagem': 'Y'},
    )

    assert resposta.status_code == HTTPStatus.FORBIDDEN
