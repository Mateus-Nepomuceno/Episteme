from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from usuarios.database import get_session
from usuarios.models import Admin, Usuario
from usuarios.schemas import (
    AdminCreate,
    AdminList,
    AdminPublic,
    FiltroPaginacao,
    Mensagem,
)
from usuarios.security import (
    get_current_user,
    get_password_hash,
)

router = APIRouter(prefix='/admins', tags=['admins'])


@router.post(
    '/', status_code=HTTPStatus.CREATED, response_model=AdminPublic
)
def create_admin(admin: AdminCreate, session: Session = Depends(get_session)):
    db_user = session.scalar(
        select(Admin).where(
            (Admin.matricula_id == admin.matricula_id)
            | (Admin.email == admin.email)
        )
    )

    if db_user:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Usuário já cadastrado'
        )

    db_admin = Admin(
        nome=admin.nome,
        email=admin.email,
        cpf=admin.cpf,
        telefone=admin.telefone,
        senha=get_password_hash(admin.senha),
        matricula_id=admin.matricula_id,
        setor=admin.setor,
    )

    session.add(db_admin)
    session.commit()
    session.refresh(db_admin)

    return db_admin


@router.get('/', response_model=AdminList)
def read_admins(filter: FiltroPaginacao = Depends(), session: Session = Depends(get_session)):
    admins = session.scalars(select(Admin).offset(filter.offset).limit(filter.limit)).all()
    return {'admins': admins}


@router.get('/{admin_id}', response_model=AdminPublic)
def read_admin(admin_id: str, session: Session = Depends(get_session)):
    admin = session.scalar(select(Admin).where(Admin.id == admin_id))

    if not admin:
        raise HTTPException(status_code=404, detail='Admin não encontrado')

    return admin


@router.put('/{admin_id}', response_model=AdminPublic)
def update_admin(admin_id: str, admin: AdminCreate, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    db_admin = session.scalar(select(Admin).where(Admin.id == admin_id))

    if not db_admin:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Admin não encontrado'
        )

    if current_user.id != admin_id and current_user.tipo != 'ADMIN':
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    try:
        db_admin.nome = admin.nome
        db_admin.email = admin.email
        db_admin.cpf = admin.cpf
        db_admin.telefone = admin.telefone
        db_admin.senha = get_password_hash(admin.senha)
        db_admin.matricula_id = admin.matricula_id
        db_admin.setor = admin.setor
        db_admin.ativo = admin.ativo

        session.commit()
        session.refresh(db_admin)

        return db_admin

    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Matrícula ou email já cadastrados'
        )


@router.delete('/{admin_id}', response_model=Mensagem)
def delete_admin(admin_id: str, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user),):
    db_admin = session.scalar(select(Admin).where(Admin.id == admin_id))

    if not db_admin:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Admin não encontrado'
        )

    if current_user.id != admin_id and current_user.tipo != 'ADMIN':
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    session.delete(db_admin)
    session.commit()

    return {'mensagem': 'Admin deletado'}
