from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from turma.academico_client import (
    ServicoAcademicoIndisponivel,
    consultar_curso,
)
from turma.database import get_session
from turma.models import Aluno
from turma.schemas import (
    AlunoCreate,
    AlunoList,
    AlunoPublic,
    FiltroPaginacao,
    Mensagem,
)
from turma.security import (
    CurrentUser,
    exigir_admin,
    exigir_dono_ou_admin,
    get_current_user,
)

router = APIRouter(prefix='/alunos', tags=['alunos'])


def _exigir_curso_valido(curso_id: str) -> None:
    try:
        curso = consultar_curso(UUID(curso_id))
    except ServicoAcademicoIndisponivel as exc:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail='Não foi possível verificar o curso no serviço acadêmico',
        ) from exc

    if curso is None:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='Curso não encontrado no serviço acadêmico',
        )

    if not curso.get('ativo', False):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='Curso inativo não pode ser associado a alunos',
        )


@router.post('/', status_code=HTTPStatus.CREATED, response_model=AlunoPublic)
def create_aluno(
    aluno: AlunoCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(exigir_admin)],
):

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

    _exigir_curso_valido(aluno.curso_id)

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
def read_alunos(
    filter: Annotated[FiltroPaginacao, Depends()],
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(exigir_admin)],
):

    alunos = session.scalars(select(Aluno).offset(filter.offset).limit(filter.limit)).all()
    return {'alunos': alunos}


@router.get('/{aluno_id}', response_model=AlunoPublic)
def read_aluno(
    aluno_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    aluno = session.scalar(select(Aluno).where(Aluno.id == aluno_id))

    if not aluno:
        raise HTTPException(status_code=404, detail='Aluno não encontrado')

    exigir_dono_ou_admin(current_user, aluno.usuario_id)

    return aluno


@router.get('/usuario_id/{aluno_usuario_id}', response_model=AlunoPublic)
def read_aluno_usuario_id(
    aluno_usuario_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    exigir_dono_ou_admin(current_user, aluno_usuario_id)

    aluno = session.scalar(select(Aluno).where(Aluno.usuario_id == aluno_usuario_id))

    if not aluno:
        raise HTTPException(status_code=404, detail='Aluno não encontrado')

    return aluno


@router.get('/matricula_id/{aluno_matricula_id}', response_model=AlunoPublic)
def read_aluno_matricula_id(
    aluno_matricula_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    aluno = session.scalar(select(Aluno).where(Aluno.matricula_id == aluno_matricula_id))

    if not aluno:
        raise HTTPException(status_code=404, detail='Aluno não encontrado')

    exigir_dono_ou_admin(current_user, aluno.usuario_id)

    return aluno


@router.put('/{aluno_id}', response_model=AlunoPublic)
def update_aluno(
    aluno_id: UUID,
    aluno: AlunoCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(exigir_admin)],
):
    db_aluno = session.scalar(select(Aluno).where(Aluno.id == aluno_id))

    if not db_aluno:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Aluno não encontrado'
        )

    _exigir_curso_valido(aluno.curso_id)

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
    current_user: Annotated[CurrentUser, Depends(exigir_admin)],
):
    db_aluno = session.scalar(select(Aluno).where(Aluno.id == aluno_id))

    if not db_aluno:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Aluno não encontrado'
        )

    session.delete(db_aluno)
    session.commit()

    return {'mensagem': 'Aluno deletado'}
