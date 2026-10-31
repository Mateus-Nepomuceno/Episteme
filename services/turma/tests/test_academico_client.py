from http import HTTPStatus
from unittest.mock import Mock, patch
from uuid import UUID

import httpx
import pytest

from turma import academico_client
from turma.academico_client import (
    ServicoAcademicoIndisponivel,
    consultar_curso,
)

CURSO = UUID('11111111-1111-1111-1111-111111111111')
URL_BASE = 'http://academico.test'
TIMEOUT = 5.0


@pytest.fixture
def com_url_academico(monkeypatch):
    monkeypatch.setattr(academico_client.settings, 'ACADEMICO_API_URL', URL_BASE)


def _resposta(status_code, json_payload=None):
    resposta = Mock()
    resposta.status_code = status_code
    resposta.is_error = status_code >= HTTPStatus.BAD_REQUEST
    resposta.json.return_value = json_payload
    return resposta


def test_consultar_curso_retorna_dados_do_curso(com_url_academico):
    dados = {'id': str(CURSO), 'ativo': True}
    with patch(
        'turma.academico_client.httpx.get',
        return_value=_resposta(200, dados),
    ) as requisicao:
        assert consultar_curso(CURSO) == dados

    requisicao.assert_called_once_with(
        f'{URL_BASE}/cursos/{CURSO}', timeout=TIMEOUT
    )


def test_consultar_curso_retorna_none_quando_nao_existe(com_url_academico):
    with patch(
        'turma.academico_client.httpx.get',
        return_value=_resposta(404),
    ):
        assert consultar_curso(CURSO) is None


def test_consultar_curso_erro_do_servico_vira_indisponivel(com_url_academico):
    with patch(
        'turma.academico_client.httpx.get',
        return_value=_resposta(500),
    ), pytest.raises(ServicoAcademicoIndisponivel):
        consultar_curso(CURSO)


def test_consultar_curso_falha_de_conexao_vira_indisponivel(com_url_academico):
    with patch(
        'turma.academico_client.httpx.get',
        side_effect=httpx.ConnectError('recusado'),
    ), pytest.raises(ServicoAcademicoIndisponivel):
        consultar_curso(CURSO)


def test_consultar_curso_sem_url_configurada(monkeypatch):
    monkeypatch.setattr(academico_client.settings, 'ACADEMICO_API_URL', None)

    with patch('turma.academico_client.httpx.get') as requisicao, pytest.raises(
        ServicoAcademicoIndisponivel
    ):
        consultar_curso(CURSO)

    requisicao.assert_not_called()
