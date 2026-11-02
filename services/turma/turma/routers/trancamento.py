from datetime import datetime
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import Aluno, Turma, TurmaAluno
from turma.schemas import TrancamentoTurma
from turma.security import CurrentUser, get_current_user

router = APIRouter(tags=['trancamento'])


@router.post(
    '/turmas/{turma_id}/trancamento',
    response_model=TrancamentoTurma,
)
def trancar_turma(
    turma_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    turma = session.get(Turma, turma_id)
    if turma is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Turma não encontrada'
        )

    aluno = session.scalar(select(Aluno).where(Aluno.usuario_id == current_user.id))
    if aluno is None:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    vinculo = session.get(TurmaAluno, (turma.id, aluno.id))
    if vinculo is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Aluno não matriculado nesta turma',
        )

    if vinculo.trancada_em is None:
        vinculo.trancada_em = datetime.now()
        session.commit()
        session.refresh(vinculo)

    return TrancamentoTurma(turma_id=turma.id, trancada_em=vinculo.trancada_em)
