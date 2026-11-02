from datetime import datetime
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import Turma
from turma.permissoes import pode_gerenciar_turma
from turma.schemas import EncerramentoTurma
from turma.security import CurrentUser, get_current_user

router = APIRouter(tags=['encerramento'])


@router.post(
    '/turmas/{turma_id}/encerramento',
    response_model=EncerramentoTurma,
)
def encerrar_turma(
    turma_id: UUID,
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

    if turma.encerrada_em is None:
        turma.encerrada_em = datetime.now()
        session.commit()
        session.refresh(turma)

    return EncerramentoTurma(id=turma.id, encerrada_em=turma.encerrada_em)
