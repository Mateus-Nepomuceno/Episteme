from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from identidade.database import get_session
from identidade.models import Usuario
from identidade.schemas import MatriculaInterna, UsuarioInterno
from identidade.security import exigir_servico

router = APIRouter(prefix='/internos', tags=['internos'])


@router.get('/usuarios/{usuario_id}', response_model=UsuarioInterno)
def read_usuario_interno(
    usuario_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    servico: Annotated[str, Depends(exigir_servico)],
):
    usuario = session.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Usuário não encontrado'
        )
    return usuario


@router.get(
    '/usuarios/por-matricula/{matricula}',
    response_model=UsuarioInterno,
)
def read_usuario_por_matricula(
    matricula: str,
    session: Annotated[Session, Depends(get_session)],
    servico: Annotated[str, Depends(exigir_servico)],
):
    usuario = session.scalar(
        select(Usuario).where(Usuario.matricula == matricula)
    )
    if usuario is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Usuário não encontrado'
        )
    return usuario


@router.put(
    '/usuarios/{usuario_id}/matricula',
    response_model=UsuarioInterno,
)
def definir_matricula_usuario(
    usuario_id: UUID,
    dados: MatriculaInterna,
    session: Annotated[Session, Depends(get_session)],
    servico: Annotated[str, Depends(exigir_servico)],
):
    if servico != 'turma':
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    usuario = session.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Usuário não encontrado'
        )

    usuario.matricula = dados.matricula
    session.commit()
    session.refresh(usuario)
    return usuario
