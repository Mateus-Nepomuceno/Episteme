from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
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
from turma.security import (
    CurrentUser,
    exigir_admin,
    exigir_dono_ou_admin,
    get_current_user,
)
from turma.usuarios import matricula_do_usuario, usuario_id_por_matricula

router = APIRouter(prefix='/professores', tags=['professores'])


def _publico(
    session: Session, professor: Professor, matricula: str | None = None
) -> ProfessorPublic:
    return ProfessorPublic(
        id=professor.id,
        usuario_id=professor.usuario_id,
        matricula_id=matricula or matricula_do_usuario(session, professor.usuario_id),
        ativo=professor.ativo,
        nome=professor.nome,
    )


@router.post('/', status_code=HTTPStatus.CREATED, response_model=ProfessorPublic)
def create_professor(
    professor: ProfessorCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(exigir_admin)],
):
    usuario_id = usuario_id_por_matricula(professor.matricula_id)
    if usuario_id is None:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='Matrícula não encontrada no serviço de identidade',
        )

    db_professor = session.scalar(select(Professor).where(Professor.usuario_id == usuario_id))

    if db_professor:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Professor já cadastrado'
        )

    db_professor = Professor(
        usuario_id=usuario_id,
        ativo=professor.ativo,
        nome=professor.nome,
    )

    session.add(db_professor)
    session.commit()
    session.refresh(db_professor)

    return _publico(session, db_professor, professor.matricula_id)


@router.get('/', response_model=ProfessorList)
def read_professores(
    filter: Annotated[FiltroPaginacao, Depends()],
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(exigir_admin)],
):

    professores = session.scalars(select(Professor).offset(filter.offset).limit(filter.limit)).all()
    return {'professores': [_publico(session, p) for p in professores]}


@router.get('/{professor_id}', response_model=ProfessorPublic)
def read_professor(
    professor_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    professor = session.scalar(select(Professor).where(Professor.id == professor_id))

    if not professor:
        raise HTTPException(status_code=404, detail='Professor não encontrado')

    exigir_dono_ou_admin(current_user, professor.usuario_id)

    return _publico(session, professor)


@router.put('/{professor_id}', response_model=ProfessorPublic)
def update_professor(
    professor_id: UUID,
    professor: ProfessorCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(exigir_admin)],
):
    db_professor = session.scalar(select(Professor).where(Professor.id == professor_id))

    if not db_professor:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Professor não encontrado'
        )

    if usuario_id_por_matricula(professor.matricula_id) != db_professor.usuario_id:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='A matrícula não pode ser alterada',
        )

    db_professor.ativo = professor.ativo
    session.commit()
    session.refresh(db_professor)
    return _publico(session, db_professor)


@router.delete('/{professor_id}', response_model=Mensagem)
def delete_professor(
    professor_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(exigir_admin)],
):
    db_professor = session.scalar(select(Professor).where(Professor.id == professor_id))

    if not db_professor:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Professor não encontrado'
        )

    session.delete(db_professor)
    session.commit()

    return {'mensagem': 'Professor deletado'}
