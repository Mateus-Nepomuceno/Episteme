from http import HTTPStatus
from urllib.parse import quote
from uuid import UUID

import httpx
from fastapi import HTTPException

from academico.settings import Settings

settings = Settings()

TIMEOUT_SEGUNDOS = 5.0
TAMANHO_PAGINA = 100

MSG_TIMEOUT = 'O serviço de turma demorou para responder'
MSG_INDISPONIVEL = 'Não foi possível acessar o serviço de turma'
MSG_ERRO = 'O serviço de turma retornou um erro'
MSG_RESPOSTA_INVALIDA = 'O serviço de turma retornou uma resposta inválida'
MSG_ALUNO_NAO_ENCONTRADO = 'Cadastro de aluno não encontrado'
MSG_LISTAGEM_INVALIDA = 'A listagem de turmas retornada é inválida'
MSG_PERMISSAO_NEGADA = 'Permissão negada'


def _requisitar(caminho, token, params=None):
    url = f'{settings.TURMA_API_URL.rstrip("/")}{caminho}'

    try:
        return httpx.get(
            url,
            params=params,
            headers={'Authorization': f'Bearer {token}'},
            timeout=TIMEOUT_SEGUNDOS,
        )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=HTTPStatus.GATEWAY_TIMEOUT, detail=MSG_TIMEOUT
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail=MSG_INDISPONIVEL,
        ) from exc


def _buscar_aluno(caminho, token):
    resposta = _requisitar(caminho, token)

    if resposta.status_code == HTTPStatus.NOT_FOUND:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail=MSG_ALUNO_NAO_ENCONTRADO
        )

    if resposta.status_code == HTTPStatus.FORBIDDEN:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail=MSG_PERMISSAO_NEGADA
        )

    if resposta.is_error:
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY, detail=MSG_ERRO
        )

    try:
        return resposta.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY, detail=MSG_RESPOSTA_INVALIDA
        ) from exc


def buscar_aluno_por_usuario(usuario_id: UUID, token: str):
    return _buscar_aluno(f'/alunos/usuario_id/{usuario_id}', token)


def buscar_aluno_por_matricula(matricula: str, token: str):
    matricula_codificada = quote(matricula, safe='')
    return _buscar_aluno(f'/alunos/matricula_id/{matricula_codificada}', token)


def listar_ofertas(filtros: dict, token: str) -> list:
    turmas = []
    offset = 0

    while True:
        resposta = _requisitar(
            '/turmas/ofertas',
            token,
            params={**filtros, 'offset': offset, 'limit': TAMANHO_PAGINA},
        )

        if resposta.status_code == HTTPStatus.FORBIDDEN:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, detail=MSG_PERMISSAO_NEGADA
            )

        if resposta.is_error:
            raise HTTPException(
                status_code=HTTPStatus.BAD_GATEWAY, detail=MSG_ERRO
            )

        try:
            pagina = resposta.json()['turmas']
        except (ValueError, KeyError, TypeError) as exc:
            raise HTTPException(
                status_code=HTTPStatus.BAD_GATEWAY,
                detail=MSG_RESPOSTA_INVALIDA,
            ) from exc

        if not isinstance(pagina, list):
            raise HTTPException(
                status_code=HTTPStatus.BAD_GATEWAY, detail=MSG_LISTAGEM_INVALIDA
            )

        turmas.extend(pagina)

        if len(pagina) < TAMANHO_PAGINA:
            return turmas

        offset += TAMANHO_PAGINA


def listar_turmas_do_aluno(aluno_id, token: str) -> list:
    resposta = _requisitar(f'/turmas/aluno/{aluno_id}', token)

    if resposta.status_code == HTTPStatus.FORBIDDEN:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail=MSG_PERMISSAO_NEGADA
        )

    if resposta.is_error:
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY, detail=MSG_ERRO
        )

    try:
        turmas = resposta.json()['turmas']
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail=MSG_RESPOSTA_INVALIDA,
        ) from exc

    if not isinstance(turmas, list):
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY, detail=MSG_LISTAGEM_INVALIDA
        )

    return turmas
