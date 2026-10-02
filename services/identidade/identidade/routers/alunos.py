from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from identidade.database import get_session
from identidade.models import Aluno, Usuario
from identidade.schemas import (
    AlunoCreate,
    AlunoList,
    AlunoPublic,
    FiltroPaginacao,
    Mensagem,
)
from identidade.security import (
    get_current_user,
    get_password_hash,
)

router = APIRouter(prefix='/alunos', tags=['alunos'])


@router.post(
    '/', status_code=HTTPStatus.CREATED, response_model=AlunoPublic
)
def create_aluno(aluno: AlunoCreate, session: Session = Depends(get_session)):
    db_user = session.scalar(
        select(Aluno).where(
            (Aluno.matricula_id == aluno.matricula_id)
            | (Aluno.email == aluno.email)
        )
    )

    if db_user:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Usuário já cadastrado'
        )

    db_aluno = Aluno(
        nome=aluno.nome,
        email=aluno.email,
        cpf=aluno.cpf,
        telefone=aluno.telefone,
        senha=get_password_hash(aluno.senha),
        matricula_id=aluno.matricula_id,
        curso_id=aluno.curso_id,
    )

    session.add(db_aluno)
    session.commit()
    session.refresh(db_aluno)

    return db_aluno


@router.get('/', response_model=AlunoList)
def read_alunos(filter: FiltroPaginacao = Depends(), session: Session = Depends(get_session)):
    alunos = session.scalars(select(Aluno).offset(filter.offset).limit(filter.limit)).all()
    return {'alunos': alunos}


@router.get('/{aluno_id}', response_model=AlunoPublic)
def read_aluno(aluno_id: str, session: Session = Depends(get_session)):
    aluno = session.scalar(select(Aluno).where(Aluno.id == aluno_id))

    if not aluno:
        raise HTTPException(status_code=404, detail='Aluno não encontrado')

    return aluno


@router.put('/{aluno_id}', response_model=AlunoPublic)
def update_aluno(aluno_id: str, aluno: AlunoCreate, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    db_aluno = session.scalar(select(Aluno).where(Aluno.id == aluno_id))

    if not db_aluno:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Aluno não encontrado'
        )

    if current_user.id != aluno_id and current_user.tipo != 'ADMIN':
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    try:
        db_aluno.nome = aluno.nome
        db_aluno.email = aluno.email
        db_aluno.cpf = aluno.cpf
        db_aluno.telefone = aluno.telefone
        db_aluno.senha = get_password_hash(aluno.senha)
        db_aluno.matricula_id = aluno.matricula_id
        db_aluno.curso_id = aluno.curso_id
        db_aluno.ativo = aluno.ativo

        session.commit()
        session.refresh(db_aluno)

        return db_aluno

    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Matrícula ou email já cadastrados'
        )


@router.delete('/{aluno_id}', response_model=Mensagem)
def delete_aluno(aluno_id: str, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user),):
    db_aluno = session.scalar(select(Aluno).where(Aluno.id == aluno_id))

    if not db_aluno:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Aluno não encontrado'
        )

    if current_user.id != aluno_id and current_user.tipo != 'ADMIN':
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    session.delete(db_aluno)
    session.commit()

    return {'mensagem': 'Aluno deletado'}
