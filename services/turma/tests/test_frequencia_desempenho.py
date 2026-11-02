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
PRESENCAS_ESPERADAS = 2
MEDIA_ESPERADA = 6.0
PROGRESSO_METADE = 50


def registrar_chamada(client, turma_id, data, presentes, matriculados):
    presencas = [
        {'aluno_id': str(aluno.id), 'presente': aluno in presentes}
        for aluno in matriculados
    ]
    return client.post(
        f'/turmas/{turma_id}/chamadas',
        json={'data': data, 'presencas': presencas},
    )


def test_chamada_registra_presencas_e_calcula_frequencia(client, session):
    professor = criar_professor(session)
    ana = criar_aluno(session)
    bia = criar_aluno(session)
    turma = criar_turma(session, professor, [ana, bia])
    como(professor.usuario_id)

    primeira = registrar_chamada(client, turma.id, '2026-09-01', [ana, bia], [ana, bia])
    registrar_chamada(client, turma.id, '2026-09-03', [ana], [ana, bia])
    como(bia.usuario_id)
    frequencia = client.get(f'/alunos/me/turmas/{turma.id}/frequencia').json()

    assert primeira.status_code == HTTPStatus.CREATED
    assert primeira.json()['presentes'] == PRESENCAS_ESPERADAS
    assert frequencia == {'aulas': 2, 'presencas': 1, 'percentual': PROGRESSO_METADE}


def test_chamada_repetida_na_mesma_data_e_rejeitada(client, session):
    professor = criar_professor(session)
    ana = criar_aluno(session)
    turma = criar_turma(session, professor, [ana])
    como(professor.usuario_id)
    registrar_chamada(client, turma.id, '2026-09-01', [ana], [ana])

    resposta = registrar_chamada(client, turma.id, '2026-09-01', [], [ana])

    assert resposta.status_code == HTTPStatus.CONFLICT


def test_chamada_com_aluno_nao_matriculado_e_rejeitada(client, session):
    professor = criar_professor(session)
    ana = criar_aluno(session)
    intruso = criar_aluno(session)
    turma = criar_turma(session, professor, [ana])
    como(professor.usuario_id)

    resposta = client.post(
        f'/turmas/{turma.id}/chamadas',
        json={
            'data': '2026-09-01',
            'presencas': [{'aluno_id': str(intruso.id), 'presente': True}],
        },
    )

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_frequencia_sem_chamadas_e_nula(client, session):
    professor = criar_professor(session)
    ana = criar_aluno(session)
    turma = criar_turma(session, professor, [ana])
    como(ana.usuario_id)

    frequencia = client.get(f'/alunos/me/turmas/{turma.id}/frequencia').json()

    assert frequencia == {'aulas': 0, 'presencas': 0, 'percentual': None}


def test_media_considera_nota_ausente_como_zero(client, session):
    professor = criar_professor(session)
    ana = criar_aluno(session)
    turma = criar_turma(session, professor, [ana])
    como(professor.usuario_id)
    prova = client.post(
        f'/turmas/{turma.id}/avaliacoes',
        json={'nome': 'P1', 'tipo': 'prova', 'data': '2026-09-16', 'peso': 60},
    ).json()
    client.post(
        f'/turmas/{turma.id}/avaliacoes',
        json={'nome': 'T1', 'tipo': 'trabalho', 'data': '2026-10-01', 'peso': 40},
    )
    client.put(f'/avaliacoes/{prova["id"]}/notas/{ana.id}', json={'valor': 10})
    como(ana.usuario_id)

    desempenho = client.get(f'/alunos/me/turmas/{turma.id}/desempenho').json()

    assert desempenho['media'] == MEDIA_ESPERADA
    assert desempenho['frequencia'] is None
    assert desempenho['progresso'] is None


def test_progresso_conta_modulos_com_materiais_acessados_e_atividades_entregues(
    client, session
):
    professor = criar_professor(session)
    ana = criar_aluno(session)
    turma = criar_turma(session, professor, [ana])
    como(professor.usuario_id)
    modulo_um = criar_modulo(client, turma.id, 'Módulo 1', 1)
    criar_modulo(client, turma.id, 'Módulo 2', 2)
    material = client.post(
        f'/modulos/{modulo_um["id"]}/materiais',
        json={'titulo': 'Slides', 'tipo': 'arquivo', 'ordem': 1},
    ).json()
    atividade = client.post(
        f'/turmas/{turma.id}/atividades',
        json={
            'titulo': 'Lista',
            'tipo': 'exercicio',
            'categoria': 'Lista',
            'prazo': PRAZO_FUTURO,
            'modulo_id': modulo_um['id'],
        },
    ).json()
    como(ana.usuario_id)
    client.post(f'/materiais/{material["id"]}/acesso')
    assert client.get(f'/alunos/me/turmas/{turma.id}/desempenho').json()['progresso'] == 0

    client.post(f'/atividades/{atividade["id"]}/entrega')
    progresso = client.get(f'/alunos/me/turmas/{turma.id}/desempenho').json()['progresso']

    assert progresso == PROGRESSO_METADE


def test_usuario_sem_cadastro_de_aluno_nao_le_desempenho(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)

    resposta = client.get(f'/alunos/me/turmas/{turma.id}/desempenho')

    assert resposta.status_code == HTTPStatus.FORBIDDEN
