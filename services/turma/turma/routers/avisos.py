from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import Turma
from turma.permissoes import pode_gerenciar_turma
from turma.schemas import AvisoCreate, AvisoTurma
from turma.security import CurrentUser, get_current_user

router = APIRouter(tags=['avisos'])


@router.post(
    '/turmas/{turma_id}/avisos',
    status_code=HTTPStatus.CREATED,
    response_model=AvisoTurma,
)
def create_aviso(
    turma_id: UUID,
    aviso: AvisoCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    turma = session.get(Turma, turma_id)
    if turma is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Turma não encontrada'
        )

    if not pode_gerenciar_turma(current_user, turma):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    novo_aviso = AvisoTurma(**aviso.model_dump())
    turma.avisos = [
        *turma.avisos,
        novo_aviso.model_dump(mode='json'),
    ]
    session.commit()

    return novo_aviso
