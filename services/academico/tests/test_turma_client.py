from http import HTTPStatus
from unittest.mock import Mock, patch
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException

from academico.turma_client import (
    buscar_aluno_por_matricula,
    buscar_aluno_por_usuario,
    listar_ofertas,
)


def resposta(status_code=HTTPStatus.OK, payload=None):
    retorno = Mock()
    retorno.status_code = status_code
    retorno.is_error = status_code >= HTTPStatus.BAD_REQUEST
    retorno.json.return_value = payload
    return retorno


def test_buscar_aluno_por_usuario_encaminha_o_token():
    usuario_id = uuid4()

    with patch(
        'academico.turma_client.httpx.get',
        return_value=resposta(payload={'id': str(uuid4())}),
    ) as requisicao:
        buscar_aluno_por_usuario(usuario_id, 'token-do-usuario')

    cabecalhos = requisicao.call_args.kwargs['headers']
    assert cabecalhos == {'Authorization': 'Bearer token-do-usuario'}
    assert requisicao.call_args.args[0].endswith(
        f'/alunos/usuario_id/{usuario_id}'
    )


def test_listar_ofertas_encaminha_o_token_em_cada_pagina():
    with patch(
        'academico.turma_client.httpx.get',
        return_value=resposta(payload={'turmas': []}),
    ) as requisicao:
        listar_ofertas({'curso_id': 'x'}, 'token-do-usuario')

    assert requisicao.call_args.kwargs['headers'] == {
        'Authorization': 'Bearer token-do-usuario'
    }


def test_buscar_aluno_por_matricula_escapa_o_valor():
    with patch(
        'academico.turma_client.httpx.get',
        return_value=resposta(payload={}),
    ) as requisicao:
        buscar_aluno_por_matricula('2026/1?x', 'token')

    assert requisicao.call_args.args[0].endswith(
        '/alunos/matricula_id/2026%2F1%3Fx'
    )


def test_timeout_vira_504():
    with patch(
        'academico.turma_client.httpx.get',
        side_effect=httpx.TimeoutException('lento'),
    ), pytest.raises(HTTPException) as excinfo:
        buscar_aluno_por_usuario(uuid4(), 'token')

    assert excinfo.value.status_code == HTTPStatus.GATEWAY_TIMEOUT


def test_falha_de_conexao_vira_503():
    with patch(
        'academico.turma_client.httpx.get',
        side_effect=httpx.ConnectError('recusado'),
    ), pytest.raises(HTTPException) as excinfo:
        buscar_aluno_por_usuario(uuid4(), 'token')

    assert excinfo.value.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_aluno_inexistente_vira_404():
    with patch(
        'academico.turma_client.httpx.get',
        return_value=resposta(status_code=HTTPStatus.NOT_FOUND),
    ), pytest.raises(HTTPException) as excinfo:
        buscar_aluno_por_usuario(uuid4(), 'token')

    assert excinfo.value.status_code == HTTPStatus.NOT_FOUND


TAMANHO_PAGINA_TESTE = 100


def test_listar_ofertas_pagina_ate_o_fim():
    primeira = [{'id': str(uuid4())} for _ in range(TAMANHO_PAGINA_TESTE)]
    segunda = [{'id': str(uuid4())}]

    with patch(
        'academico.turma_client.httpx.get',
        side_effect=[
            resposta(payload={'turmas': primeira}),
            resposta(payload={'turmas': segunda}),
        ],
    ) as requisicao:
        turmas = listar_ofertas({'curso_id': 'x'}, 'token')

    assert len(turmas) == TAMANHO_PAGINA_TESTE + 1
    assert requisicao.call_count == 2 * 1


def test_permissao_negada_no_turma_vira_403():
    with patch(
        'academico.turma_client.httpx.get',
        return_value=resposta(status_code=HTTPStatus.FORBIDDEN),
    ), pytest.raises(HTTPException) as excinfo:
        buscar_aluno_por_matricula('2026001', 'token')

    assert excinfo.value.status_code == HTTPStatus.FORBIDDEN
