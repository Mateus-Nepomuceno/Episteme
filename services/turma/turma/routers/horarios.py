from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import Aluno, Horario, Professor, Turma
from turma.schemas import (
    HorarioCreate,
    HorarioList,
    HorarioPublic,
    Mensagem,
)
from turma.security import (
    CurrentUser,
    exigir_admin,
    exigir_dono_ou_admin,
    get_current_user,
)

router = APIRouter(prefix='/horarios', tags=['professores'])


def check_horario_tem_conflito(
    horario: HorarioCreate,
    session: Session,
    horario_id: UUID | None = None,
):
    if horario.horario_inicio > horario.horario_fim:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Horário de início e fim incorretos'
        )

    outro_horario = [Horario.id != horario_id] if horario_id else []

    db_horario_conflito_turma = session.scalar(
        select(Horario)
        .join(Horario.turma)
        .where(
            Horario.dia_semana == horario.dia_semana,
            Horario.turma_id == horario.turma_id,
            Horario.horario_inicio < horario.horario_fim,
            Horario.horario_fim > horario.horario_inicio,
            *outro_horario,
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
            Horario.horario_inicio < horario.horario_fim,
            Horario.horario_fim > horario.horario_inicio,
            *outro_horario,
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
            Horario.horario_inicio < horario.horario_fim,
            Horario.horario_fim > horario.horario_inicio,
            *outro_horario,
        )
    )
    if db_horario_conflito_local:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Horário possui sobreposição de horários para mesmo local'
        )


@router.post('/', status_code=HTTPStatus.CREATED, response_model=HorarioPublic)
def create_horario(
    horario: HorarioCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(exigir_admin)]
):
    check_horario_tem_conflito(horario, session)

    db_horario = Horario(
        turma_id=horario.turma_id,
        professor_id=horario.professor_id,
        dia_semana=horario.dia_semana,
        horario_inicio=horario.horario_inicio,
        horario_fim=horario.horario_fim,
        local=horario.local
    )

    session.add(db_horario)
    session.commit()
    session.refresh(db_horario)

    return db_horario


@router.get('/aluno/{aluno_id}', response_model=HorarioList)
def read_horarios_aluno(
    aluno_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    db_aluno = session.scalar(select(Aluno).where(Aluno.id == aluno_id))

    if not db_aluno:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Aluno não encontrado'
        )

    exigir_dono_ou_admin(current_user, db_aluno.usuario_id)

    db_horarios = session.scalars(
        select(Horario)
        .where(
            Horario.turma.has(
                Turma.alunos.any(Aluno.id == aluno_id)
            )
        )
    ).all()

    return {'horarios': db_horarios}


@router.get('/professor/{professor_id}', response_model=HorarioList)
def read_horarios_professor(
    professor_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    db_professor = session.scalar(select(Professor).where(Professor.id == professor_id))

    if not db_professor:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Professor não encontrado'
        )

    exigir_dono_ou_admin(current_user, db_professor.usuario_id)

    db_horarios = session.scalars(
        select(Horario)
        .where(Horario.professor_id == professor_id)
    ).all()

    return {'horarios': db_horarios}


@router.put('/{horario_id}', response_model=HorarioPublic)
def update_horario(
    horario_id: UUID,
    horario: HorarioCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(exigir_admin)]
):
    db_horario = session.scalar(select(Horario).where(Horario.id == horario_id))

    if not db_horario:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Horário não encontrado'
        )

    check_horario_tem_conflito(horario, session, horario_id)

    db_horario.dia_semana = horario.dia_semana
    db_horario.horario_inicio = horario.horario_inicio
    db_horario.horario_fim = horario.horario_fim
    db_horario.local = horario.local
    db_horario.turma_id = horario.turma_id
    db_horario.professor_id = horario.professor_id

    session.commit()
    session.refresh(db_horario)

    return db_horario


@router.delete('/{horario_id}', response_model=Mensagem)
def delete_horario(
    horario_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(exigir_admin)]
):
    db_horario = session.scalar(select(Horario).where(Horario.id == horario_id))

    if not db_horario:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Horário não encontrado'
        )

    session.delete(db_horario)
    session.commit()

    return {'mensagem': 'Horário deletado'}
