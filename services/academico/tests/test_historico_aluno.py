from http import HTTPStatus
from unittest.mock import patch
from uuid import uuid4

import httpx

from academico.app import app
from academico.security import CurrentUser, get_current_user

ALUNO_ID = str(uuid4())
MEDIA_APROVADO = 8.5
FREQUENCIA_APROVADO = 95
TURMA_APROVADA = str(uuid4())
TURMA_REPROVADA = str(uuid4())
TURMA_EM_ANDAMENTO = str(uuid4())


def _turmas():
    return {
        'turmas': [
            {
                'id': TURMA_APROVADA,
                'materia': 'Banco de Dados I',
                'periodo_letivo': '2025.1',
                'encerrada_em': '2025-07-01T10:00:00',
            },
            {
                'id': TURMA_REPROVADA,
                'materia': 'Redes',
                'periodo_letivo': '2024.2',
                'encerrada_em': '2024-12-15T10:00:00',
            },
            {
                'id': TURMA_EM_ANDAMENTO,
                'materia': 'Engenharia',
                'periodo_letivo': '2026.2',
                'encerrada_em': None,
            },
        ]
    }


DESEMPENHOS = {
    TURMA_APROVADA: {
        'media': MEDIA_APROVADO,
        'frequencia': FREQUENCIA_APROVADO,
        'progresso': 100,
        'nota_final': MEDIA_APROVADO,
        'frequencia_final': FREQUENCIA_APROVADO,
        'situacao': 'aprovado',
    },
    TURMA_REPROVADA: {
        'media': 5.0,
        'frequencia': 70,
        'progresso': 100,
        'nota_final': 5.0,
        'frequencia_final': 70,
        'situacao': 'reprovado',
    },
}


def _fake_get(url, params=None, headers=None, timeout=None):
    if '/alunos/usuario_id/' in url:
        return httpx.Response(HTTPStatus.OK, json={'id': ALUNO_ID})
    if url.endswith(f'/turmas/aluno/{ALUNO_ID}'):
        return httpx.Response(HTTPStatus.OK, json=_turmas())
    for turma_id, desempenho in DESEMPENHOS.items():
        if url.endswith(f'/alunos/me/turmas/{turma_id}/desempenho'):
            return httpx.Response(HTTPStatus.OK, json=desempenho)
    return httpx.Response(HTTPStatus.NOT_FOUND)


def test_historico_traz_apenas_turmas_encerradas_com_situacao(client, session):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='aluno@teste.com', e_admin=False, token='token-aluno'
    )

    with patch('academico.turma_client.httpx.get', side_effect=_fake_get):
        resposta = client.get('/alunos/me/historico')

    app.dependency_overrides.pop(get_current_user, None)
    disciplinas = resposta.json()['disciplinas']
    assert resposta.status_code == HTTPStatus.OK
    assert [d['disciplina'] for d in disciplinas] == ['Redes', 'Banco de Dados I']
    assert [d['situacao'] for d in disciplinas] == ['reprovado', 'aprovado']
    assert disciplinas[1]['nota_final'] == MEDIA_APROVADO
    assert disciplinas[1]['frequencia_final'] == FREQUENCIA_APROVADO
