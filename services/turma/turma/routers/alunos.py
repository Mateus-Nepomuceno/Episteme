from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import Aluno
from turma.schemas import (
    AlunoCreate,
    AlunoList,
    AlunoPublic,
    FiltroPaginacao,
    Mensagem,
)
from turma.security import CurrentUser, get_current_user

router = APIRouter(prefix='/alunos', tags=['alunos'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=AlunoPublic)
def create_aluno(aluno: AlunoCreate, session: Annotated[Session, Depends(get_session)]):
    db_aluno = session.scalar(
        select(Aluno).where(
            (Aluno.matricula_id == aluno.matricula_id)
            | (Aluno.usuario_id == aluno.usuario_id)
        )
    )

    if db_aluno:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Aluno já cadastrado'
        )

    db_aluno = Aluno(
        usuario_id=aluno.usuario_id,
        matricula_id=aluno.matricula_id,
        curso_id=aluno.curso_id,
        ativo=aluno.ativo,
    )

    session.add(db_aluno)
    session.commit()
    session.refresh(db_aluno)

    return db_aluno


@router.get('/', response_model=AlunoList)
def read_alunos(filter: Annotated[FiltroPaginacao, Depends()], session: Annotated[Session, Depends(get_session)]):
    alunos = session.scalars(select(Aluno).offset(filter.offset).limit(filter.limit)).all()
    return {'alunos': alunos}


@router.get('/{aluno_id}', response_model=AlunoPublic)
def read_aluno(aluno_id: UUID, session: Annotated[Session, Depends(get_session)]):
    aluno = session.scalar(select(Aluno).where(Aluno.id == aluno_id))

    if not aluno:
        raise HTTPException(status_code=404, detail='Aluno não encontrado')

    return aluno


@router.get('/usuario_id/{aluno_usuario_id}', response_model=AlunoPublic)
def read_aluno_usuario_id(aluno_usuario_id: UUID, session: Annotated[Session, Depends(get_session)]):
    aluno = session.scalar(select(Aluno).where(Aluno.usuario_id == aluno_usuario_id))

    if not aluno:
        raise HTTPException(status_code=404, detail='Aluno não encontrado')

    return aluno


@router.put('/{aluno_id}', response_model=AlunoPublic)
def update_aluno(
    aluno_id: UUID,
    aluno: AlunoCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    db_aluno = session.scalar(select(Aluno).where(Aluno.id == aluno_id))

    if not db_aluno:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Aluno não encontrado'
        )

    if current_user.id != db_aluno.usuario_id and not current_user.e_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    try:
        db_aluno.usuario_id = aluno.usuario_id
        db_aluno.matricula_id = aluno.matricula_id
        db_aluno.curso_id = aluno.curso_id
        db_aluno.ativo = aluno.ativo
        session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Matrícula ou usuário já cadastrados'
        )
    else:
        session.refresh(db_aluno)
        return db_aluno


@router.delete('/{aluno_id}', response_model=Mensagem)
def delete_aluno(
    aluno_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    db_aluno = session.scalar(select(Aluno).where(Aluno.id == aluno_id))

    if not db_aluno:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Aluno não encontrado'
        )

    if current_user.id != db_aluno.usuario_id and not current_user.e_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    session.delete(db_aluno)
    session.commit()

    return {'mensagem': 'Aluno deletado'}
