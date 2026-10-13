from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import Professor
from turma.schemas import (
    FiltroPaginacao,
    Mensagem,
    ProfessorCreate,
    ProfessorList,
    ProfessorPublic,
)
from turma.security import CurrentUser, get_current_user

router = APIRouter(prefix='/professores', tags=['professores'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=ProfessorPublic)
def create_professor(professor: ProfessorCreate, session: Annotated[Session, Depends(get_session)]):
    db_professor = session.scalar(
        select(Professor).where(
            (Professor.matricula_id == professor.matricula_id)
            | (Professor.usuario_id == professor.usuario_id)
        )
    )

    if db_professor:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Professor já cadastrado'
        )

    db_professor = Professor(
        usuario_id=professor.usuario_id,
        matricula_id=professor.matricula_id,
        ativo=professor.ativo,
    )

    session.add(db_professor)
    session.commit()
    session.refresh(db_professor)

    return db_professor


@router.get('/', response_model=ProfessorList)
def read_professores(filter: Annotated[FiltroPaginacao, Depends()], session: Annotated[Session, Depends(get_session)]):
    professores = session.scalars(select(Professor).offset(filter.offset).limit(filter.limit)).all()
    return {'professores': professores}


@router.get('/{professor_id}', response_model=ProfessorPublic)
def read_professor(professor_id: UUID, session: Annotated[Session, Depends(get_session)]):
    professor = session.scalar(select(Professor).where(Professor.id == professor_id))

    if not professor:
        raise HTTPException(status_code=404, detail='Professor não encontrado')

    return professor


@router.put('/{professor_id}', response_model=ProfessorPublic)
def update_professor(
    professor_id: UUID,
    professor: ProfessorCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    db_professor = session.scalar(select(Professor).where(Professor.id == professor_id))

    if not db_professor:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Professor não encontrado'
        )

    if current_user.id != db_professor.usuario_id and not current_user.e_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    try:
        db_professor.usuario_id = professor.usuario_id
        db_professor.matricula_id = professor.matricula_id
        db_professor.ativo = professor.ativo
        session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Matrícula ou usuário já cadastrados'
        )
    else:
        session.refresh(db_professor)
        return db_professor


@router.delete('/{professor_id}', response_model=Mensagem)
def delete_professor(
    professor_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    db_professor = session.scalar(select(Professor).where(Professor.id == professor_id))

    if not db_professor:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Professor não encontrado'
        )

    if current_user.id != db_professor.usuario_id and not current_user.e_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    session.delete(db_professor)
    session.commit()

    return {'mensagem': 'Professor deletado'}
