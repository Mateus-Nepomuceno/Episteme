from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from identidade.database import get_session
from identidade.models import Usuario
from identidade.schemas import (
    Mensagem,
    UsuarioCreate,
    UsuarioPublic,
)
from identidade.security import (
    get_current_user,
    get_password_hash,
)

router = APIRouter(prefix='/usuarios', tags=['usuarios'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=UsuarioPublic)
def create_usuario(
    usuario: UsuarioCreate, session: Annotated[Session, Depends(get_session)]
):
    db_user = session.scalar(
        select(Usuario).where(
            (Usuario.email == usuario.email) | (Usuario.cpf == usuario.cpf)
        )
    )

    if db_user:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Email ou CPF já cadastrado',
        )

    db_usuario = Usuario(
        nome=usuario.nome,
        email=usuario.email,
        cpf=usuario.cpf,
        telefone=usuario.telefone,
        senha=get_password_hash(usuario.senha),
        e_admin=usuario.e_admin,
    )

    session.add(db_usuario)
    session.commit()
    session.refresh(db_usuario)

    return db_usuario


@router.get('/{usuario_id}', response_model=UsuarioPublic)
def read_usuario(
    usuario_id: UUID, session: Annotated[Session, Depends(get_session)]
):
    usuario = session.scalar(select(Usuario).where(Usuario.id == usuario_id))

    if not usuario:
        raise HTTPException(status_code=404, detail='Usuário não encontrado')

    return usuario


@router.put('/{usuario_id}', response_model=UsuarioPublic)
def update_usuario(
    usuario_id: UUID,
    usuario: UsuarioCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    db_usuario = session.scalar(
        select(Usuario).where(Usuario.id == usuario_id)
    )

    if not db_usuario:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Usuário não encontrado'
        )

    if current_user.id != usuario_id and not current_user.e_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    db_usuario.nome = usuario.nome
    db_usuario.email = usuario.email
    db_usuario.cpf = usuario.cpf
    db_usuario.telefone = usuario.telefone
    db_usuario.senha = get_password_hash(usuario.senha)
    db_usuario.e_admin = usuario.e_admin

    try:
        session.commit()
        session.refresh(db_usuario)
        return db_usuario
    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Email ou CPF já cadastrados',
        )


@router.delete('/{usuario_id}', response_model=Mensagem)
def delete_usuario(
    usuario_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
):
    db_usuario = session.scalar(
        select(Usuario).where(Usuario.id == usuario_id)
    )

    if not db_usuario:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Usuário não encontrado'
        )

    if current_user.id != usuario_id and not current_user.e_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    session.delete(db_usuario)
    session.commit()

    return {'mensagem': 'Usuário deletado'}
