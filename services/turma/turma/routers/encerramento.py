from datetime import datetime
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import Avaliacao, Turma, TurmaAluno
from turma.permissoes import pode_gerenciar_turma
from turma.routers.desempenho import calcular_media
from turma.routers.frequencia import calcular_frequencia
from turma.schemas import EncerramentoTurma
from turma.security import CurrentUser, get_current_user

router = APIRouter(tags=['encerramento'])

PESO_TOTAL = 100.0
TOLERANCIA = 1e-9
NOTA_MINIMA = 7.0


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
        soma_pesos = session.scalar(
            select(func.coalesce(func.sum(Avaliacao.peso), 0)).where(
                Avaliacao.turma_id == turma.id
            )
        )
        if abs(soma_pesos - PESO_TOTAL) > TOLERANCIA:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='A soma dos pesos precisa ser 100 para encerrar a turma',
            )

        turma.encerrada_em = datetime.now()
        for vinculo in session.scalars(
            select(TurmaAluno).where(TurmaAluno.turma_id == turma.id)
        ).all():
            media = calcular_media(session, turma.id, vinculo.aluno_id)
            vinculo.nota_final = media
            vinculo.frequencia_final = calcular_frequencia(
                session, turma.id, vinculo.aluno_id
            ).percentual
            if vinculo.trancada_em is not None:
                vinculo.situacao = 'trancado'
            elif media is not None and media >= NOTA_MINIMA:
                vinculo.situacao = 'aprovado'
            else:
                vinculo.situacao = 'reprovado'
        session.commit()
        session.refresh(turma)

    return EncerramentoTurma(id=turma.id, encerrada_em=turma.encerrada_em)
