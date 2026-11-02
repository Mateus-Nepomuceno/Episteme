from datetime import datetime, timedelta
from http import HTTPStatus

from tests.test_modulos import (
    como,
    criar_aluno,
    criar_modulo,
    criar_professor,
    criar_turma,
)

PRAZO_FUTURO = (datetime.now() + timedelta(days=30)).isoformat()
PRAZO_PASSADO = (datetime.now() - timedelta(days=30)).isoformat()


def criar_atividade(client, turma_id, prazo=PRAZO_FUTURO, **extra):
    corpo = {
        'titulo': 'Lista 01',
        'tipo': 'exercicio',
        'categoria': 'Lista de Exercícios',
        'pontos': 2.5,
        'prazo': prazo,
    }
    corpo.update(extra)
    resposta = client.post(f'/turmas/{turma_id}/atividades', json=corpo)
    assert resposta.status_code == HTTPStatus.CREATED
    return resposta.json()


def test_professor_cria_atividade_e_lista_sem_situacao(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)

    atividade = criar_atividade(client, turma.id)
    resposta = client.get(f'/turmas/{turma.id}/atividades')

    assert atividade['situacao'] is None
    assert resposta.json()['atividades'][0]['titulo'] == 'Lista 01'
    assert resposta.json()['atividades'][0]['situacao'] is None


def test_aluno_ve_situacao_pendente_e_vencida(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)
    criar_atividade(client, turma.id, titulo='No prazo', prazo=PRAZO_FUTURO)
    criar_atividade(client, turma.id, titulo='Encerrada', prazo=PRAZO_PASSADO)
    como(aluno.usuario_id)

    resposta = client.get(f'/turmas/{turma.id}/atividades')

    situacoes = {a['titulo']: a['situacao'] for a in resposta.json()['atividades']}
    assert situacoes == {'No prazo': 'pendente', 'Encerrada': 'vencida'}


def test_entrega_marca_atividade_como_concluida_uma_vez(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)
    atividade = criar_atividade(client, turma.id, prazo=PRAZO_PASSADO)
    como(aluno.usuario_id)

    primeira = client.post(f'/atividades/{atividade["id"]}/entrega')
    segunda = client.post(f'/atividades/{atividade["id"]}/entrega')
    lista = client.get(f'/turmas/{turma.id}/atividades')

    assert primeira.status_code == HTTPStatus.OK
    assert primeira.json()['situacao'] == 'concluida'
    assert segunda.json()['entregue_em'] == primeira.json()['entregue_em']
    assert lista.json()['atividades'][0]['situacao'] == 'concluida'


def test_atividade_nao_publicada_nao_aparece_para_aluno(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)
    criar_atividade(client, turma.id, publicada=False)
    como(aluno.usuario_id)

    resposta = client.get(f'/turmas/{turma.id}/atividades')

    assert resposta.json()['atividades'] == []


def test_aluno_fora_da_turma_nao_le_nem_entrega(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)
    atividade = criar_atividade(client, turma.id)
    intruso = criar_aluno(session)
    como(intruso.usuario_id)

    leitura = client.get(f'/turmas/{turma.id}/atividades')
    entrega = client.post(f'/atividades/{atividade["id"]}/entrega')

    assert leitura.status_code == HTTPStatus.FORBIDDEN
    assert entrega.status_code == HTTPStatus.NOT_FOUND


def test_atividade_com_modulo_de_outra_turma_e_rejeitada(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    outra = criar_turma(session, professor, [])
    como(professor.usuario_id)
    modulo_alheio = criar_modulo(client, outra.id, 'Alheio', 1)

    resposta = client.post(
        f'/turmas/{turma.id}/atividades',
        json={
            'titulo': 'X',
            'tipo': 'leitura',
            'categoria': 'Leitura',
            'prazo': PRAZO_FUTURO,
            'modulo_id': modulo_alheio['id'],
        },
    )

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_outro_professor_nao_cria_atividade(client, session):
    professor = criar_professor(session)
    outro = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(outro.usuario_id)

    resposta = client.post(
        f'/turmas/{turma.id}/atividades',
        json={
            'titulo': 'X',
            'tipo': 'leitura',
            'categoria': 'Leitura',
            'prazo': PRAZO_FUTURO,
        },
    )

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_tipo_de_atividade_invalido_e_rejeitado(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)

    resposta = client.post(
        f'/turmas/{turma.id}/atividades',
        json={
            'titulo': 'X',
            'tipo': 'prova',
            'categoria': 'Leitura',
            'prazo': PRAZO_FUTURO,
        },
    )

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
