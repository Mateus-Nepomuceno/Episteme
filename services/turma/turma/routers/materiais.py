from http import HTTPStatus
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import Material, Modulo, Turma
from turma.permissoes import pode_acessar_turma, pode_gerenciar_turma
from turma.schemas import MaterialPublic
from turma.security import CurrentUser, get_current_user
from turma.settings import Settings

router = APIRouter(tags=['materiais'])

TAMANHO_MAXIMO = 25 * 1024 * 1024


class MaterialArquivoForm(BaseModel):
    titulo: str = Field(min_length=1)
    ordem: int = Field(ge=0)
    descricao: str | None = None


def _dados_formulario(
    titulo: Annotated[str, Form(min_length=1)],
    ordem: Annotated[int, Form(ge=0)],
    descricao: Annotated[str | None, Form()] = None,
) -> MaterialArquivoForm:
    return MaterialArquivoForm(titulo=titulo, ordem=ordem, descricao=descricao)


@router.post(
    '/modulos/{modulo_id}/materiais/arquivo',
    status_code=HTTPStatus.CREATED,
    response_model=MaterialPublic,
)
def upload_material(
    modulo_id: UUID,
    dados: Annotated[MaterialArquivoForm, Depends(_dados_formulario)],
    arquivo: Annotated[UploadFile, File()],
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    modulo = session.get(Modulo, modulo_id)
    if modulo is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Módulo não encontrado'
        )

    turma = session.get(Turma, modulo.turma_id)
    if not pode_gerenciar_turma(current_user, turma):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    conteudo = arquivo.file.read(TAMANHO_MAXIMO + 1)
    if len(conteudo) > TAMANHO_MAXIMO:
        raise HTTPException(
            status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            detail='O arquivo excede o tamanho máximo permitido',
        )

    nome = Path(arquivo.filename or 'material').name
    pasta = Path(Settings().DIRETORIO_ARMAZENAMENTO) / str(uuid4())
    pasta.mkdir(parents=True)
    caminho = pasta / nome
    caminho.write_bytes(conteudo)

    db_material = Material(
        modulo_id=modulo.id,
        titulo=dados.titulo,
        descricao=dados.descricao,
        tipo='arquivo',
        ordem=dados.ordem,
        arquivo_nome=nome,
        arquivo_caminho=str(caminho),
    )
    session.add(db_material)
    session.commit()
    session.refresh(db_material)

    return MaterialPublic.model_validate(db_material)


@router.get('/materiais/{material_id}/arquivo')
def download_material(
    material_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    material = session.scalar(select(Material).where(Material.id == material_id))
    if material is None or material.arquivo_caminho is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Arquivo não encontrado'
        )

    modulo = session.get(Modulo, material.modulo_id)
    turma = session.get(Turma, modulo.turma_id)
    arquivo_visivel = pode_acessar_turma(session, current_user, turma) and (
        modulo.publicado or pode_gerenciar_turma(current_user, turma)
    )
    if not arquivo_visivel:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Arquivo não encontrado'
        )

    return FileResponse(
        material.arquivo_caminho,
        filename=material.arquivo_nome,
    )
