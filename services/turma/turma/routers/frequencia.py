from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import Aluno, Chamada, Presenca, Turma, TurmaAluno
from turma.permissoes import pode_acessar_turma, pode_gerenciar_turma
from turma.schemas import (
    ChamadaCreate,
    ChamadaPublic,
    FrequenciaAluno,
)
from turma.security import CurrentUser, get_current_user

router = APIRouter(tags=['frequencia'])


def _turma_ou_404(session: Session, turma_id: UUID) -> Turma:
    turma = session.get(Turma, turma_id)
    if turma is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Turma não encontrada'
        )
    return turma


def _permissao_negada() -> HTTPException:
    return HTTPException(
        status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
    )


def calcular_frequencia(
    session: Session, turma_id: UUID, aluno_id: UUID
) -> FrequenciaAluno:
    aulas = session.scalar(
        select(func.count()).select_from(Chamada).where(Chamada.turma_id == turma_id)
    )
    presencas = session.scalar(
        select(func.count())
        .select_from(Presenca)
        .join(Chamada, Chamada.id == Presenca.chamada_id)
        .where(
            Chamada.turma_id == turma_id,
            Presenca.aluno_id == aluno_id,
            Presenca.presente.is_(True),
        )
    )
    percentual = round(presencas * 100 / aulas) if aulas else None
    return FrequenciaAluno(aulas=aulas, presencas=presencas, percentual=percentual)


def _matriculados(session: Session, turma_id: UUID) -> set[UUID]:
    return set(
        session.scalars(
            select(TurmaAluno.aluno_id).where(TurmaAluno.turma_id == turma_id)
        ).all()
    )


@router.post(
    '/turmas/{turma_id}/chamadas',
    status_code=HTTPStatus.CREATED,
    response_model=ChamadaPublic,
)
def create_chamada(
    turma_id: UUID,
    chamada: ChamadaCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    turma = _turma_ou_404(session, turma_id)

    if not pode_gerenciar_turma(current_user, turma):
        raise _permissao_negada()

    matriculados = _matriculados(session, turma.id)
    informados = {item.aluno_id for item in chamada.presencas}
    if not informados <= matriculados:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='Há alunos que não estão matriculados nesta turma',
        )

    if session.scalar(
        select(Chamada).where(Chamada.turma_id == turma.id, Chamada.data == chamada.data)
    ):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Já existe chamada registrada para esta data',
        )

    presentes = {item.aluno_id for item in chamada.presencas if item.presente}

    db_chamada = Chamada(turma_id=turma.id, data=chamada.data)
    session.add(db_chamada)
    session.flush()
    for aluno_id in matriculados:
        session.add(
            Presenca(
                chamada_id=db_chamada.id,
                aluno_id=aluno_id,
                presente=aluno_id in presentes,
            )
        )
    session.commit()

    return ChamadaPublic(
        id=db_chamada.id,
        turma_id=turma.id,
        data=db_chamada.data,
        presentes=len(presentes),
        matriculados=len(matriculados),
    )


@router.get(
    '/alunos/me/turmas/{turma_id}/frequencia',
    response_model=FrequenciaAluno,
)
def read_frequencia_aluno(
    turma_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    turma = _turma_ou_404(session, turma_id)

    aluno = session.scalar(select(Aluno).where(Aluno.usuario_id == current_user.id))
    if aluno is None or not pode_acessar_turma(session, current_user, turma):
        raise _permissao_negada()

    return calcular_frequencia(session, turma.id, aluno.id)
