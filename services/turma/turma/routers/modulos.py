from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import AcessoMaterial, Aluno, Material, Modulo, Turma
from turma.permissoes import (
    pode_acessar_turma,
    pode_gerenciar_turma,
)
from turma.progresso import status_modulo
from turma.schemas import (
    AcessoMaterialPublic,
    MaterialCreate,
    MaterialPublic,
    ModuloCreate,
    ModuloList,
    ModuloPublic,
)
from turma.security import CurrentUser, get_current_user

router = APIRouter(tags=['modulos'])


def _turma_ou_404(session: Session, turma_id: UUID) -> Turma:
    turma = session.get(Turma, turma_id)
    if turma is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Turma não encontrada'
        )
    return turma


def _modulo_ou_404(session: Session, modulo_id: UUID) -> Modulo:
    modulo = session.get(Modulo, modulo_id)
    if modulo is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Módulo não encontrado'
        )
    return modulo


def _permissao_negada() -> HTTPException:
    return HTTPException(
        status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
    )


def _modulo_publico(
    session: Session, modulo: Modulo, status: str | None = None
) -> ModuloPublic:
    materiais = session.scalars(
        select(Material)
        .where(Material.modulo_id == modulo.id)
        .order_by(Material.ordem, Material.titulo)
    ).all()
    return ModuloPublic(
        id=modulo.id,
        titulo=modulo.titulo,
        ordem=modulo.ordem,
        publicado=modulo.publicado,
        status=status,
        materiais=[MaterialPublic.model_validate(m) for m in materiais],
    )


@router.get('/turmas/{turma_id}/modulos', response_model=ModuloList)
def read_modulos(
    turma_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    turma = _turma_ou_404(session, turma_id)

    if not pode_acessar_turma(session, current_user, turma):
        raise _permissao_negada()

    gerencia = pode_gerenciar_turma(current_user, turma)
    consulta = select(Modulo).where(Modulo.turma_id == turma.id)
    if not gerencia:
        consulta = consulta.where(Modulo.publicado.is_(True))

    modulos = session.scalars(consulta.order_by(Modulo.ordem, Modulo.titulo)).all()

    if gerencia:
        return {'modulos': [_modulo_publico(session, m) for m in modulos]}

    aluno = session.scalar(select(Aluno).where(Aluno.usuario_id == current_user.id))
    return {
        'modulos': [
            _modulo_publico(session, m, status_modulo(session, m, aluno.id))
            for m in modulos
        ]
    }


@router.post(
    '/turmas/{turma_id}/modulos',
    status_code=HTTPStatus.CREATED,
    response_model=ModuloPublic,
)
def create_modulo(
    turma_id: UUID,
    modulo: ModuloCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    turma = _turma_ou_404(session, turma_id)

    if not pode_gerenciar_turma(current_user, turma):
        raise _permissao_negada()

    db_modulo = Modulo(
        turma_id=turma.id,
        titulo=modulo.titulo,
        ordem=modulo.ordem,
        publicado=modulo.publicado,
    )
    session.add(db_modulo)
    session.commit()
    session.refresh(db_modulo)

    return _modulo_publico(session, db_modulo)


@router.post(
    '/modulos/{modulo_id}/materiais',
    status_code=HTTPStatus.CREATED,
    response_model=MaterialPublic,
)
def create_material(
    modulo_id: UUID,
    material: MaterialCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    modulo = _modulo_ou_404(session, modulo_id)
    turma = _turma_ou_404(session, modulo.turma_id)

    if not pode_gerenciar_turma(current_user, turma):
        raise _permissao_negada()

    db_material = Material(
        modulo_id=modulo.id,
        titulo=material.titulo,
        descricao=material.descricao,
        tipo=material.tipo,
        ordem=material.ordem,
    )
    session.add(db_material)
    session.commit()
    session.refresh(db_material)

    return MaterialPublic.model_validate(db_material)


@router.post(
    '/materiais/{material_id}/acesso',
    response_model=AcessoMaterialPublic,
)
def registrar_acesso_material(
    material_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    material = session.get(Material, material_id)
    if material is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Material não encontrado'
        )

    modulo = _modulo_ou_404(session, material.modulo_id)
    turma = _turma_ou_404(session, modulo.turma_id)

    if not modulo.publicado or not pode_acessar_turma(session, current_user, turma):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Material não encontrado'
        )

    aluno = session.scalar(select(Aluno).where(Aluno.usuario_id == current_user.id))
    if aluno is None:
        raise _permissao_negada()

    acesso = session.get(AcessoMaterial, (material.id, aluno.id))
    if acesso is None:
        acesso = AcessoMaterial(material_id=material.id, aluno_id=aluno.id)
        session.add(acesso)
        session.commit()
        session.refresh(acesso)

    return AcessoMaterialPublic.model_validate(acesso)
