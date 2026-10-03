from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from academico.database import get_session
from academico.models import Curso
from academico.schemas import (
    CursoCreate,
    CursoList,
    CursoPublic,
    FiltroPaginacao,
    Mensagem,
)
from academico.security import CurrentUser, get_current_user

router = APIRouter(prefix='/cursos', tags=['cursos'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=CursoPublic)
def create_curso(
    curso: CursoCreate, session: Annotated[Session, Depends(get_session)]
):
    db_curso = session.scalar(
        select(Curso).where(Curso.codigo == curso.codigo)
    )

    if db_curso:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Curso já cadastrado'
        )

    db_curso = Curso(
        codigo=curso.codigo,
        nome=curso.nome,
        tipo_formacao=curso.tipo_formacao,
        modalidade=curso.modalidade,
        nivel_academico=curso.nivel_academico,
        carga_horaria_total=curso.carga_horaria_total,
        campus=curso.campus,
        duracao=curso.duracao,
        documentacao=curso.documentacao,
        ativo=curso.ativo,
    )

    session.add(db_curso)
    session.commit()
    session.refresh(db_curso)

    return db_curso


@router.get('/', response_model=CursoList)
def read_cursos(
    filter: Annotated[FiltroPaginacao, Depends()],
    session: Annotated[Session, Depends(get_session)],
):
    cursos = session.scalars(
        select(Curso).offset(filter.offset).limit(filter.limit)
    ).all()
    return {'cursos': cursos}


@router.get('/{curso_id}', response_model=CursoPublic)
def read_curso(
    curso_id: UUID, session: Annotated[Session, Depends(get_session)]
):
    curso = session.scalar(select(Curso).where(Curso.id == curso_id))

    if not curso:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Curso não encontrado'
        )

    return curso


@router.put('/{curso_id}', response_model=CursoPublic)
def update_curso(
    curso_id: UUID,
    curso: CursoCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    db_curso = session.scalar(select(Curso).where(Curso.id == curso_id))

    if not db_curso:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Curso não encontrado'
        )

    if not current_user.e_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    db_curso.codigo = curso.codigo
    db_curso.nome = curso.nome
    db_curso.tipo_formacao = curso.tipo_formacao
    db_curso.modalidade = curso.modalidade
    db_curso.nivel_academico = curso.nivel_academico
    db_curso.carga_horaria_total = curso.carga_horaria_total
    db_curso.campus = curso.campus
    db_curso.duracao = curso.duracao
    db_curso.documentacao = curso.documentacao
    db_curso.ativo = curso.ativo
    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Código já cadastrado'
        )
    else:
        session.refresh(db_curso)
        return db_curso


@router.delete('/{curso_id}', response_model=Mensagem)
def delete_curso(
    curso_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    db_curso = session.scalar(select(Curso).where(Curso.id == curso_id))

    if not db_curso:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Curso não encontrado'
        )

    if not current_user.e_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    session.delete(db_curso)
    session.commit()

    return {'mensagem': 'Curso deletado'}
