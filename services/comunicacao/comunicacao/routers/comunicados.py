from datetime import UTC, datetime
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from comunicacao.database import get_session
from comunicacao.models import Comunicado
from comunicacao.schemas import (
    ComunicadoCreate,
    ComunicadoList,
    ComunicadoPublic,
    ComunicadoUpdate,
    Mensagem,
)
from comunicacao.security import CurrentUser, exigir_admin, get_current_user

router = APIRouter(prefix='/comunicados', tags=['comunicados'])


def obter_agora_utc() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def despir_tz(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


@router.get('', response_model=ComunicadoList)
def read_comunicados(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    limite: Annotated[int, Query(ge=1, le=100)] = 50,
    situacao: Annotated[
        str | None,
        Query(
            description=(
                "Filtro administrativo de situação (apenas admin): "
                "'todos', 'publicados', 'programados', 'rascunhos', 'expirados'"
            )
        ),
    ] = None,
    incluir_rascunhos: Annotated[bool | None, Query()] = None,
    somente_vigentes: Annotated[bool, Query()] = False,
):
    agora = obter_agora_utc()

    # 1. Contexto Público:
    # Usuários comuns (Alunos e Professores) OU quando explicitamente solicitado somente_vigentes=True.
    # Sempre impõe filtragem estrita de publicação e vigência cronológica no servidor.
    if not current_user.e_admin or somente_vigentes:
        query = (
            select(Comunicado)
            .where(Comunicado.publicado.is_(True))
            .where(
                or_(
                    Comunicado.inicio_em.is_(None),
                    Comunicado.inicio_em <= agora,
                )
            )
            .where(
                or_(
                    Comunicado.expira_em.is_(None),
                    Comunicado.expira_em > agora,
                )
            )
        )
    else:
        # 2. Contexto Administrativo (Coordenação e Gestão de Notícias):
        # Por padrão (sem filtros), lista a totalidade dos comunicados (rascunhos, programados,
        # ativos e expirados), assegurando que o gerenciamento não perca nenhum registro.
        query = select(Comunicado)

        if situacao:
            sit = situacao.lower().strip()
            if sit in ('rascunho', 'rascunhos'):
                query = query.where(Comunicado.publicado.is_(False))
            elif sit in ('programado', 'programados'):
                query = query.where(Comunicado.publicado.is_(True)).where(
                    Comunicado.inicio_em.is_not(None),
                    Comunicado.inicio_em > agora,
                )
            elif sit in ('expirado', 'expirados'):
                query = query.where(Comunicado.publicado.is_(True)).where(
                    Comunicado.expira_em.is_not(None),
                    Comunicado.expira_em <= agora,
                )
            elif sit in ('publicado', 'publicados'):
                query = (
                    query.where(Comunicado.publicado.is_(True))
                    .where(
                        or_(
                            Comunicado.inicio_em.is_(None),
                            Comunicado.inicio_em <= agora,
                        )
                    )
                    .where(
                        or_(
                            Comunicado.expira_em.is_(None),
                            Comunicado.expira_em > agora,
                        )
                    )
                )
            elif sit in ('todos', 'tudo'):
                pass  # Todos os itens sem restrição de status
        elif incluir_rascunhos is False:
            query = query.where(Comunicado.publicado.is_(True))

    comunicados = session.scalars(
        query.order_by(Comunicado.publicado_em.desc()).limit(limite)
    ).all()

    return {'comunicados': comunicados}


@router.get('/{comunicado_id}', response_model=ComunicadoPublic)
def read_comunicado(
    comunicado_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    comunicado = session.get(Comunicado, comunicado_id)
    if not comunicado:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Comunicado não encontrado'
        )

    if not current_user.e_admin:
        agora = obter_agora_utc()
        if not comunicado.publicado:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='Comunicado não encontrado'
            )
        if comunicado.inicio_em and despir_tz(comunicado.inicio_em) > agora:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='Comunicado não encontrado'
            )
        if comunicado.expira_em and despir_tz(comunicado.expira_em) <= agora:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='Comunicado não encontrado'
            )

    return comunicado


@router.post(
    '',
    status_code=HTTPStatus.CREATED,
    response_model=ComunicadoPublic,
)
def create_comunicado(
    comunicado: ComunicadoCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(exigir_admin)],
):
    agora = obter_agora_utc()
    inicio = despir_tz(comunicado.inicio_em)
    expira = despir_tz(comunicado.expira_em)

    db_comunicado = Comunicado(
        titulo=comunicado.titulo,
        resumo=comunicado.resumo,
        corpo=comunicado.corpo,
        publicado=comunicado.publicado,
        inicio_em=inicio,
        expira_em=expira,
        versao=1,
    )
    db_comunicado.publicado_em = agora
    db_comunicado.atualizado_em = agora

    session.add(db_comunicado)
    session.commit()
    session.refresh(db_comunicado)

    return db_comunicado


@router.put(
    '/{comunicado_id}',
    response_model=ComunicadoPublic,
)
def update_comunicado(
    comunicado_id: UUID,
    comunicado: ComunicadoUpdate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(exigir_admin)],
):
    db_comunicado = session.get(Comunicado, comunicado_id)
    if not db_comunicado:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Comunicado não encontrado'
        )

    # 1. Controle de concorrência otimista
    if comunicado.versao is not None and comunicado.versao != db_comunicado.versao:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=(
                f'Conflito de concorrência: o comunicado foi modificado por outro administrador '
                f'(versão no servidor: {db_comunicado.versao}, versão enviada: {comunicado.versao}).'
            ),
        )

    # 2. Validação combinada de datas
    novo_inicio = (
        comunicado.inicio_em
        if 'inicio_em' in comunicado.model_fields_set
        else db_comunicado.inicio_em
    )
    novo_expira = (
        comunicado.expira_em
        if 'expira_em' in comunicado.model_fields_set
        else db_comunicado.expira_em
    )
    ni = despir_tz(novo_inicio)
    ne = despir_tz(novo_expira)
    if ni and ne and ne <= ni:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='A data de término deve ser posterior à data de início',
        )

    # 3. Atualização dos campos informados
    if comunicado.titulo is not None:
        db_comunicado.titulo = comunicado.titulo
    if comunicado.resumo is not None:
        db_comunicado.resumo = comunicado.resumo
    if comunicado.corpo is not None:
        db_comunicado.corpo = comunicado.corpo
    if comunicado.publicado is not None:
        # Se era rascunho e agora foi publicado, atualiza a data de publicação
        if comunicado.publicado and not db_comunicado.publicado:
            db_comunicado.publicado_em = obter_agora_utc()
        db_comunicado.publicado = comunicado.publicado
    if 'inicio_em' in comunicado.model_fields_set:
        db_comunicado.inicio_em = despir_tz(comunicado.inicio_em)
    if 'expira_em' in comunicado.model_fields_set:
        db_comunicado.expira_em = despir_tz(comunicado.expira_em)

    # 4. Incremento de versão e data de atualização
    db_comunicado.versao += 1
    db_comunicado.atualizado_em = obter_agora_utc()

    session.commit()
    session.refresh(db_comunicado)

    return db_comunicado


@router.delete(
    '/{comunicado_id}',
    response_model=Mensagem,
)
def delete_comunicado(
    comunicado_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(exigir_admin)],
):
    db_comunicado = session.get(Comunicado, comunicado_id)
    if not db_comunicado:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Comunicado não encontrado'
        )

    session.delete(db_comunicado)
    session.commit()

    return {'mensagem': 'Comunicado excluído com sucesso'}

