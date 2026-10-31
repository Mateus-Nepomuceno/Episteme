from http import HTTPStatus
from uuid import UUID

import httpx

from turma.settings import Settings

settings = Settings()
RESPOSTA_INVALIDA = 'Resposta inválida do serviço acadêmico'


class ServicoAcademicoIndisponivel(Exception):
    """O serviço acadêmico não respondeu ou não está configurado."""


def consultar_curso(curso_id: UUID) -> dict | None:
    """Busca o curso no serviço acadêmico.

    Retorna os dados do curso, ou None quando o curso não existe.
    """
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
