from http import HTTPStatus
from uuid import UUID

import httpx

from turma.settings import Settings

settings = Settings()
RESPOSTA_INVALIDA = 'Resposta inválida do serviço acadêmico'


class ServicoAcademicoIndisponivel(Exception):
    pass


def consultar_curso(curso_id: UUID) -> dict | None:
    if not settings.ACADEMICO_API_URL:
        mensagem = 'ACADEMICO_API_URL não configurada'
        raise ServicoAcademicoIndisponivel(mensagem)

    url = f'{settings.ACADEMICO_API_URL.rstrip("/")}/cursos/{curso_id}'

    try:
        resposta = httpx.get(url, timeout=5.0)
    except httpx.RequestError as exc:
        raise ServicoAcademicoIndisponivel(str(exc)) from exc

    if resposta.status_code == HTTPStatus.NOT_FOUND:
        return None

    if resposta.is_error:
        mensagem = f'Status inesperado: {resposta.status_code}'
        raise ServicoAcademicoIndisponivel(mensagem)

    try:
        dados = resposta.json()
    except ValueError as exc:
        raise ServicoAcademicoIndisponivel(RESPOSTA_INVALIDA) from exc

    if not isinstance(dados, dict):
        raise ServicoAcademicoIndisponivel(RESPOSTA_INVALIDA)

    return dados
