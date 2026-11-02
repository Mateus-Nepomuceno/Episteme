from http import HTTPStatus

from tests.test_modulos import como, criar_aluno, criar_professor, criar_turma


def test_professor_encerra_turma_e_aluno_ve_data_de_encerramento(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)

    resposta = client.post(f'/turmas/{turma.id}/encerramento')
    como(aluno.usuario_id)
    turmas = client.get(f'/turmas/aluno/{aluno.id}').json()['turmas']

    assert resposta.status_code == HTTPStatus.OK
    assert turmas[0]['encerrada_em'] is not None


def test_encerramento_nao_altera_data_ja_registrada(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)

    primeira = client.post(f'/turmas/{turma.id}/encerramento').json()
    segunda = client.post(f'/turmas/{turma.id}/encerramento').json()

    assert segunda['encerrada_em'] == primeira['encerrada_em']


def test_aluno_nao_encerra_turma(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(aluno.usuario_id)

    resposta = client.post(f'/turmas/{turma.id}/encerramento')

    assert resposta.status_code == HTTPStatus.FORBIDDEN
