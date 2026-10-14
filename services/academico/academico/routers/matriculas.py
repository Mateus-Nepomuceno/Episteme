
from http import HTTPStatus
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException

from academico.schemas import CadastroAcademicoResponse
from academico.security import CurrentUser, get_current_user
from academico.settings import Settings

settings = Settings()

router = APIRouter(prefix='/matricula', tags=['matricula'])


@router.post('/solicitar', response_model=CadastroAcademicoResponse, )
def solicitar_matricula(
    current_user: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
    ):
    url = (
        f'{settings.TURMA_API_URL.rstrip("/")}'
        f'/alunos/usuario_id/{current_user.id}'
    )

    try:
        response = httpx.get(url, timeout=5.0)
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=HTTPStatus.GATEWAY_TIMEOUT,
            detail='O serviço de turma demorou para responder',
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail='Não foi possível acessar o serviço de turma',
        )

    if response.status_code == HTTPStatus.NOT_FOUND:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Cadastro de aluno não encontrado',
        )

    if response.is_error:
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail='O serviço de turma retornou um erro',
        )

    aluno = response.json()

    return {
        'mensagem': 'cadastro acadêmico encontrado',
        'usuario_id': current_user.id,
        'aluno_id': aluno['id'],
        'curso_id': aluno['curso_id'],
    }