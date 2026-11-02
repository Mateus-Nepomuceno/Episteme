from http import HTTPStatus

import pytest

from tests.test_modulos import (
    como,
    criar_aluno,
    criar_modulo,
    criar_professor,
    criar_turma,
)
from turma.routers import materiais

NOTA_TRANCADA = 9


@pytest.fixture
def diretorio(monkeypatch, tmp_path):
    monkeypatch.setenv('DIRETORIO_ARMAZENAMENTO', str(tmp_path))
    return tmp_path


def enviar_arquivo(client, modulo_id, conteudo=b'conteudo da aula'):
    return client.post(
        f'/modulos/{modulo_id}/materiais/arquivo',
        data={'titulo': 'Aula 1', 'ordem': '1'},
        files={'arquivo': ('aula 1.pdf', conteudo, 'application/pdf')},
    )


def test_professor_envia_arquivo_e_aluno_baixa(client, session, diretorio):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)
    modulo = criar_modulo(client, turma.id, 'Módulo 1', 1)

    envio = enviar_arquivo(client, modulo['id'])
    como(aluno.usuario_id)
    download = client.get(f'/materiais/{envio.json()["id"]}/arquivo')

    assert envio.status_code == HTTPStatus.CREATED
    assert envio.json()['tipo'] == 'arquivo'
    assert download.status_code == HTTPStatus.OK
    assert download.content == b'conteudo da aula'
    assert 'aula%201.pdf' in download.headers['content-disposition']


def test_aluno_nao_envia_arquivo(client, session, diretorio):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)
    modulo = criar_modulo(client, turma.id, 'Módulo 1', 1)
    como(aluno.usuario_id)

    resposta = enviar_arquivo(client, modulo['id'])

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_aluno_fora_da_turma_nao_baixa_arquivo(client, session, diretorio):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)
    modulo = criar_modulo(client, turma.id, 'Módulo 1', 1)
    envio = enviar_arquivo(client, modulo['id'])
    intruso = criar_aluno(session)
    como(intruso.usuario_id)

    resposta = client.get(f'/materiais/{envio.json()["id"]}/arquivo')

    assert resposta.status_code == HTTPStatus.NOT_FOUND


def test_aluno_nao_baixa_arquivo_de_modulo_nao_publicado(client, session, diretorio):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)
    modulo = criar_modulo(client, turma.id, 'Rascunho', 1, publicado=False)
    envio = enviar_arquivo(client, modulo['id'])
    como(aluno.usuario_id)

    resposta = client.get(f'/materiais/{envio.json()["id"]}/arquivo')

    assert resposta.status_code == HTTPStatus.NOT_FOUND


def test_arquivo_acima_do_limite_e_rejeitado(client, session, diretorio, monkeypatch):
    monkeypatch.setattr(materiais, 'TAMANHO_MAXIMO', 4)
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)
    modulo = criar_modulo(client, turma.id, 'Módulo 1', 1)

    resposta = enviar_arquivo(client, modulo['id'], conteudo=b'muito grande')

    assert resposta.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE


def test_aluno_tranca_turma_e_historico_mostra_trancado(client, session, diretorio):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)
    avaliacao = client.post(
        f'/turmas/{turma.id}/avaliacoes',
        json={'nome': 'P1', 'tipo': 'prova', 'data': '2026-09-16', 'peso': 100},
    ).json()
    client.put(f'/avaliacoes/{avaliacao["id"]}/notas/{aluno.id}', json={'valor': NOTA_TRANCADA})
    como(aluno.usuario_id)
    trancamento = client.post(f'/turmas/{turma.id}/trancamento')
    como(professor.usuario_id)
    client.post(f'/turmas/{turma.id}/encerramento')
    como(aluno.usuario_id)
    desempenho = client.get(f'/alunos/me/turmas/{turma.id}/desempenho').json()

    assert trancamento.status_code == HTTPStatus.OK
    assert desempenho['situacao'] == 'trancado'
    assert desempenho['nota_final'] == NOTA_TRANCADA


def test_professor_nao_tranca_turma_como_aluno(client, session, diretorio):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)

    resposta = client.post(f'/turmas/{turma.id}/trancamento')

    assert resposta.status_code == HTTPStatus.FORBIDDEN
