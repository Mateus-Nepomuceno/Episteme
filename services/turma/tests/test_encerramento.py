from http import HTTPStatus

from tests.test_modulos import como, criar_aluno, criar_professor, criar_turma

PESO_TOTAL = 100
NOTA_APROVACAO = 8
NOTA_REPROVACAO = 5


def criar_avaliacao_total(client, turma_id, peso=PESO_TOTAL):
    resposta = client.post(
        f'/turmas/{turma_id}/avaliacoes',
        json={'nome': 'P1', 'tipo': 'prova', 'data': '2026-09-16', 'peso': peso},
    )
    assert resposta.status_code == HTTPStatus.CREATED
    return resposta.json()


def test_professor_encerra_turma_e_aluno_ve_data_de_encerramento(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)
    criar_avaliacao_total(client, turma.id)

    resposta = client.post(f'/turmas/{turma.id}/encerramento')
    como(aluno.usuario_id)
    turmas = client.get(f'/turmas/aluno/{aluno.id}').json()['turmas']

    assert resposta.status_code == HTTPStatus.OK
    assert turmas[0]['encerrada_em'] is not None


def test_encerramento_nao_altera_data_ja_registrada(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)
    criar_avaliacao_total(client, turma.id)

    primeira = client.post(f'/turmas/{turma.id}/encerramento').json()
    segunda = client.post(f'/turmas/{turma.id}/encerramento').json()

    assert segunda['encerrada_em'] == primeira['encerrada_em']


def test_encerramento_exige_soma_de_pesos_igual_a_100(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)
    criar_avaliacao_total(client, turma.id, peso=60)

    resposta = client.post(f'/turmas/{turma.id}/encerramento')

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_encerramento_grava_nota_frequencia_e_situacao_na_matricula(
    client, session
):
    professor = criar_professor(session)
    aprovado = criar_aluno(session)
    reprovado = criar_aluno(session)
    turma = criar_turma(session, professor, [aprovado, reprovado])
    como(professor.usuario_id)
    avaliacao = criar_avaliacao_total(client, turma.id)
    client.put(
        f'/avaliacoes/{avaliacao["id"]}/notas/{aprovado.id}',
        json={'valor': NOTA_APROVACAO},
    )
    client.put(
        f'/avaliacoes/{avaliacao["id"]}/notas/{reprovado.id}',
        json={'valor': NOTA_REPROVACAO},
    )
    client.post(f'/turmas/{turma.id}/encerramento')

    como(aprovado.usuario_id)
    desempenho = client.get(f'/alunos/me/turmas/{turma.id}/desempenho').json()
    como(reprovado.usuario_id)
    desempenho_reprovado = client.get(
        f'/alunos/me/turmas/{turma.id}/desempenho'
    ).json()

    assert desempenho['nota_final'] == NOTA_APROVACAO
    assert desempenho['situacao'] == 'aprovado'
    assert desempenho_reprovado['nota_final'] == NOTA_REPROVACAO
    assert desempenho_reprovado['situacao'] == 'reprovado'


def test_aluno_nao_encerra_turma(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(aluno.usuario_id)

    resposta = client.post(f'/turmas/{turma.id}/encerramento')

    assert resposta.status_code == HTTPStatus.FORBIDDEN
