from datetime import time
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import Horario
from turma.schemas import (
    HorarioCreate,
    HorarioPublic,
)

router = APIRouter(prefix='/horarios', tags=['professores'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=HorarioPublic)
def create_horario(horario: HorarioCreate, session: Annotated[Session, Depends(get_session)]):
    horario_inicio = time.fromisoformat(horario.horario_inicio)
    horario_fim = time.fromisoformat(horario.horario_fim)

    if horario_inicio > horario_fim:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Horário de início e fim incorretos'
        )

    db_horario_conflito_turma = session.scalar(
        select(Horario)
        .join(Horario.turma)
        .where(
            Horario.dia_semana == horario.dia_semana,
            Horario.turma_id == horario.turma_id,
            Horario.horario_inicio < horario_fim,
            Horario.horario_fim > horario_inicio,
        )
    )
    if db_horario_conflito_turma:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Horário possui sobreposição de horários para mesma turma'
        )

    db_horario_conflito_professor = session.scalar(
        select(Horario)
        .join(Horario.turma)
        .where(
            Horario.dia_semana == horario.dia_semana,
            Horario.professor_id == horario.professor_id,
            Horario.horario_inicio < horario_fim,
            Horario.horario_fim > horario_inicio,
        )
    )
    if db_horario_conflito_professor:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Horário possui sobreposição de horários para mesmo professor'
        )

    db_horario_conflito_local = session.scalar(
        select(Horario)
        .join(Horario.turma)
        .where(
            Horario.dia_semana == horario.dia_semana,
            Horario.local == horario.local,
            Horario.horario_inicio < horario_fim,
            Horario.horario_fim > horario_inicio,
        )
    )
    if db_horario_conflito_local:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Horário possui sobreposição de horários para mesmo local'
        )

    db_horario = Horario(
        turma_id=horario.turma_id,
        professor_id=horario.professor_id,
        dia_semana=horario.dia_semana,
        horario_inicio=horario_inicio,
        horario_fim=horario_fim,
        local=horario.local
    )

    session.add(db_horario)
    session.commit()
    session.refresh(db_horario)

    return db_horario
