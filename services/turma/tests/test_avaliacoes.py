from http import HTTPStatus

SOMA_TOTAL = 100
PESO_AJUSTADO = 60
NOTA_LANCADA = 8.5

from tests.test_modulos import (
    como,
    criar_aluno,
    criar_professor,
    criar_turma,
)


def criar_avaliacao(client, turma_id, nome, peso, tipo='prova'):
    return client.post(
        f'/turmas/{turma_id}/avaliacoes',
        json={'nome': nome, 'tipo': tipo, 'data': '2026-09-16', 'peso': peso},
    )


def test_professor_cria_avaliacoes_e_soma_pesos(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)

    assert criar_avaliacao(client, turma.id, 'P1', 40).status_code == HTTPStatus.CREATED
    assert criar_avaliacao(client, turma.id, 'T1', 60, 'trabalho').status_code == (
        HTTPStatus.CREATED
    )
    resposta = client.get(f'/turmas/{turma.id}/avaliacoes')

    assert resposta.json()['soma_pesos'] == SOMA_TOTAL
    assert [a['nome'] for a in resposta.json()['avaliacoes']] == ['P1', 'T1']


def test_soma_de_pesos_acima_de_100_e_rejeitada(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)
    criar_avaliacao(client, turma.id, 'P1', 70)

    resposta = criar_avaliacao(client, turma.id, 'P2', 40)

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_atualizar_peso_respeita_limite_da_turma(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)
    p1 = criar_avaliacao(client, turma.id, 'P1', 40).json()
    criar_avaliacao(client, turma.id, 'T1', 40)

    estourado = client.patch(f'/avaliacoes/{p1["id"]}', json={'peso': 70})
    ajustado = client.patch(f'/avaliacoes/{p1["id"]}', json={'peso': 60})

    assert estourado.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert ajustado.status_code == HTTPStatus.OK
    assert ajustado.json()['peso'] == PESO_AJUSTADO


def test_professor_lanca_nota_e_aluno_ve_apenas_as_proprias(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    outro = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno, outro])
    como(professor.usuario_id)
    p1 = criar_avaliacao(client, turma.id, 'P1', 50).json()
    criar_avaliacao(client, turma.id, 'T1', 50, 'trabalho')

    lancamento = client.put(
        f'/avaliacoes/{p1["id"]}/notas/{aluno.id}', json={'valor': 8.5}
    )
    como(aluno.usuario_id)
    notas = client.get(f'/alunos/me/turmas/{turma.id}/notas').json()['notas']

    assert lancamento.status_code == HTTPStatus.OK
    assert lancamento.json()['valor'] == NOTA_LANCADA
    assert [n['valor'] for n in notas] == [NOTA_LANCADA, None]
    assert notas[0]['nome'] == 'P1'


def test_nota_fora_da_faixa_e_rejeitada(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)
    p1 = criar_avaliacao(client, turma.id, 'P1', 100).json()

    resposta = client.put(
        f'/avaliacoes/{p1["id"]}/notas/{aluno.id}', json={'valor': 11}
    )

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_nota_de_aluno_fora_da_turma_e_rejeitada(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    intruso = criar_aluno(session)
    como(professor.usuario_id)
    p1 = criar_avaliacao(client, turma.id, 'P1', 100).json()

    resposta = client.put(
        f'/avaliacoes/{p1["id"]}/notas/{intruso.id}', json={'valor': 9}
    )

    assert resposta.status_code == HTTPStatus.NOT_FOUND


def test_aluno_nao_lanca_nota(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)
    p1 = criar_avaliacao(client, turma.id, 'P1', 100).json()
    como(aluno.usuario_id)

    resposta = client.put(
        f'/avaliacoes/{p1["id"]}/notas/{aluno.id}', json={'valor': 10}
    )

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_aluno_fora_da_turma_nao_le_avaliacoes(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    intruso = criar_aluno(session)
    como(intruso.usuario_id)

    resposta = client.get(f'/turmas/{turma.id}/avaliacoes')

    assert resposta.status_code == HTTPStatus.FORBIDDEN
