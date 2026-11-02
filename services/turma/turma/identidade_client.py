from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from jwt import encode

from turma.settings import Settings

TEMPO_LIMITE_SEGUNDOS = 5
STATUS_OK = 200
DURACAO_TOKEN_MINUTOS = 5
NOME_SERVICO = 'turma'


def criar_token_servico() -> str:
    settings = Settings()
    expira_em = datetime.now(tz=UTC) + timedelta(minutes=DURACAO_TOKEN_MINUTOS)
    return encode(
        {
            'sub': f'servico:{NOME_SERVICO}',
            'servico': NOME_SERVICO,
            'exp': expira_em,
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def buscar_usuario(usuario_id: UUID) -> dict | None:
    return _consultar(f'/internos/usuarios/{usuario_id}')


def buscar_usuario_por_matricula(matricula: str) -> dict | None:
    return _consultar(f'/internos/usuarios/por-matricula/{matricula}')


def _consultar(caminho: str) -> dict | None:
    settings = Settings()
    try:
        resposta = httpx.get(
            f'{settings.IDENTIDADE_API_URL}{caminho}',
            headers={'Authorization': f'Bearer {criar_token_servico()}'},
            timeout=TEMPO_LIMITE_SEGUNDOS,
        )
    except httpx.RequestError:
        return None

    if resposta.status_code != STATUS_OK:
        return None
    return resposta.json()


def definir_matricula(usuario_id: UUID, matricula: str) -> bool:
    settings = Settings()
    try:
        resposta = httpx.put(
            f'{settings.IDENTIDADE_API_URL}/internos/usuarios/{usuario_id}/matricula',
            json={'matricula': matricula},
            headers={'Authorization': f'Bearer {criar_token_servico()}'},
            timeout=TEMPO_LIMITE_SEGUNDOS,
        )
    except httpx.RequestError:
        return False
    return resposta.status_code == STATUS_OK
