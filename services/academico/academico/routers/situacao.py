from http import HTTPStatus
from typing import Annotated
from uuid import UUID

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
from academico.turma_client import buscar_aluno_por_matricula

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
    aluno = buscar_aluno_por_matricula(matricula_aluno, current_user.token)

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
