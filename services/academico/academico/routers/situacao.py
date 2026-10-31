from http import HTTPStatus
from typing import Annotated
from urllib.parse import quote
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from academico.database import get_session
from academico.models import (
    Curso,
)
from academico.schemas import (
    SituacaoAcademicaAlunoPublic,
)
from academico.security import CurrentUser, get_current_user
from academico.settings import Settings

settings = Settings()

router = APIRouter(prefix='/matricula', tags=['matricula'])


@router.get(
    '/situacao/{matricula_aluno}',
    response_model=SituacaoAcademicaAlunoPublic,
)
def consultar_situacao_academica_aluno(
    matricula_aluno: str,
    current_user: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
    session: Annotated[Session, Depends(get_session)],
):
    url = (
        f'{settings.TURMA_API_URL.rstrip("/")}'
        f'/alunos/matricula_id/{quote(matricula_aluno, safe="")}'
    )

    try:
        response = httpx.get(url, timeout=5.0)
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=HTTPStatus.GATEWAY_TIMEOUT,
            detail='O serviço de turma demorou para responser'
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail='Não foi possível acessar o serviço de turma'
        ) from exc

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

    try:
        aluno = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail='O serviço de turma retornou uma resposta inválida',
        ) from exc

    try:
        usuario_id = UUID(str(aluno['usuario_id']))
        curso_id = UUID(str(aluno['curso_id']))
        ativo = bool(aluno['ativo'])
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail='O serviço de turma retornou identificadores inválidos',
        ) from exc

    if current_user.id != usuario_id and not current_user.e_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    curso = session.get(Curso, curso_id)
    if curso is None:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='O curso do aluno não está cadastrado no serviço acadêmico'
        )

    return {
        'aluno_usuario_id': usuario_id,
        'matricula': matricula_aluno,
        'curso': curso,
        'ativo': ativo,
    }
