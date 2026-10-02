from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from usuarios.database import get_session
from usuarios.models import Professor, Usuario
from usuarios.schemas import (
    FiltroPaginacao,
    Mensagem,
    ProfessorCreate,
    ProfessorList,
    ProfessorPublic,
)
from usuarios.security import (
    get_current_user,
    get_password_hash,
)

router = APIRouter(prefix='/professores', tags=['professores'])


@router.post(
    '/', status_code=HTTPStatus.CREATED, response_model=ProfessorPublic
)
def create_professor(professor: ProfessorCreate, session: Session = Depends(get_session)):
    db_user = session.scalar(
        select(Professor).where(
            (Professor.matricula_id == professor.matricula_id)
            | (Professor.email == professor.email)
        )
    )

    if db_user:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Usuário já cadastrado'
        )

    db_professor = Professor(
        nome=professor.nome,
        email=professor.email,
        cpf=professor.cpf,
        telefone=professor.telefone,
        senha=get_password_hash(professor.senha),
        matricula_id=professor.matricula_id,
        departamento_id=professor.departamento_id,
    )

    session.add(db_professor)
    session.commit()
    session.refresh(db_professor)

    return db_professor


@router.get('/', response_model=ProfessorList)
def read_professores(filter: FiltroPaginacao = Depends(), session: Session = Depends(get_session)):
    professores = session.scalars(select(Professor).offset(filter.offset).limit(filter.limit)).all()
    return {'professores': professores}


@router.get('/{professor_id}', response_model=ProfessorPublic)
def read_professor(professor_id: str, session: Session = Depends(get_session)):
    professor = session.scalar(select(Professor).where(Professor.id == professor_id))

    if not professor:
        raise HTTPException(status_code=404, detail='Professor não encontrado')

    return professor


@router.put('/{professor_id}', response_model=ProfessorPublic)
def update_professor(professor_id: str, professor: ProfessorCreate, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    db_professor = session.scalar(select(Professor).where(Professor.id == professor_id))

    if not db_professor:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Professor não encontrado'
        )

    if current_user.id != professor_id and current_user.tipo != 'ADMIN':
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    try:
        db_professor.nome = professor.nome
        db_professor.email = professor.email
        db_professor.cpf = professor.cpf
        db_professor.telefone = professor.telefone
        db_professor.senha = get_password_hash(professor.senha)
        db_professor.matricula_id = professor.matricula_id
        db_professor.departamento_id = professor.departamento_id
        db_professor.ativo = professor.ativo

        session.commit()
        session.refresh(db_professor)

        return db_professor

    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Matrícula ou email já cadastrados'
        )


@router.delete('/{professor_id}', response_model=Mensagem)
def delete_professor(professor_id: str, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user),):
    db_professor = session.scalar(select(Professor).where(Professor.id == professor_id))

    if not db_professor:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Professor não encontrado'
        )

    if current_user.id != professor_id and current_user.tipo != 'ADMIN':
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    session.delete(db_professor)
    session.commit()

    return {'mensagem': 'Professor deletado'}
