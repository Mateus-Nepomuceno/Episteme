from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import Aluno, Professor, Turma
from turma.schemas import (
    FiltroPaginacao,
    Mensagem,
    TurmaCreate,
    TurmaList,
    TurmaPublic,
)
from turma.security import CurrentUser, get_current_user

router = APIRouter(prefix='/turmas', tags=['turmas'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=TurmaPublic)
def create_turma(turma: TurmaCreate, session: Annotated[Session, Depends(get_session)]):
    db_turma = session.scalar(
        select(Turma).where(
            (Turma.nome == turma.nome) and
            (Turma.professor_id == turma.professor_id)
        )
    )

    if db_turma:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Turma já existe'
        )

    professor = session.get(Professor, turma.professor_id)

    if not professor:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Professor não existe'
        )

    alunos: list[Aluno] = list(
        session.scalars(
            select(Aluno).where(Aluno.id.in_(turma.aluno_ids))
        ).all()
    )

    if len(alunos) != len(turma.aluno_ids):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Um ou mais alunos não foram encontrados'
        )

    db_turma = Turma(
        nome=turma.nome,
        professor_id=turma.professor_id,
        materia=turma.materia,
        documentos=turma.documentos,
        avisos=turma.avisos,
        professor=professor,
        alunos=alunos
    )

    session.add(db_turma)
    session.commit()
    session.refresh(db_turma)

    return db_turma


@router.get('/', response_model=TurmaList)
def read_turmas(filter: Annotated[FiltroPaginacao, Depends()], session: Annotated[Session, Depends(get_session)]):
    turmas = session.scalars(select(Turma).offset(filter.offset).limit(filter.limit)).all()
    return {'turmas': turmas}


@router.get('/{turma_id}', response_model=TurmaPublic)
def read_turma(turma_id: UUID, session: Annotated[Session, Depends(get_session)]):
    turma = session.scalar(select(Turma).where(Turma.id == turma_id))

    if not turma:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Turma não encontrada')

    return turma


@router.put('/{turma_id}', response_model=TurmaPublic)
def update_turma(
    turma_id: UUID,
    turma: TurmaCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    db_turma = session.scalar(select(Turma).where(Turma.id == turma_id))

    if not db_turma:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Turma não encontrada'
        )

    professor = session.get(Professor, db_turma.professor_id)
    # Se a turma existe, tem professor
    assert professor is not None

    if current_user.id != professor.usuario_id and not current_user.e_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    alunos: list[Aluno] = list(
        session.scalars(
            select(Aluno).where(Aluno.id.in_(turma.aluno_ids))
        ).all()
    )

    if len(alunos) != len(turma.aluno_ids):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Um ou mais alunos não foram encontrados'
        )

    db_turma.nome = turma.nome
    db_turma.professor_id = turma.professor_id
    db_turma.professor = professor
    db_turma.materia = turma.materia
    db_turma.documentos = turma.documentos
    db_turma.avisos = turma.avisos
    db_turma.alunos = alunos
    session.refresh(db_turma)
    return db_turma


@router.delete('/{turma_id}', response_model=Mensagem)
def delete_turma(
    turma_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    db_turma = session.scalar(select(Turma).where(Turma.id == turma_id))

    if not db_turma:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Turma não encontrada'
        )

    professor = session.get(Professor, db_turma.professor_id)
    # Se a turma existe, tem professor
    assert professor is not None

    if current_user.id != professor.usuario_id and not current_user.e_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    session.delete(db_turma)
    session.commit()

    return {'mensagem': 'Turma deletada'}
