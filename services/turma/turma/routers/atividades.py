from datetime import datetime
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import Aluno, Atividade, Entrega, Modulo, Turma
from turma.permissoes import (
    pode_acessar_turma,
    pode_gerenciar_turma,
)
from turma.schemas import (
    AtividadeCreate,
    AtividadeList,
    AtividadePublic,
    EntregaPublic,
)
from turma.security import CurrentUser, get_current_user

router = APIRouter(tags=['atividades'])


def _turma_ou_404(session: Session, turma_id: UUID) -> Turma:
    turma = session.get(Turma, turma_id)
    if turma is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Turma não encontrada'
        )
    return turma


def _permissao_negada() -> HTTPException:
    return HTTPException(
        status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
    )


def _aluno_do_usuario(session: Session, current_user: CurrentUser) -> Aluno | None:
    return session.scalar(select(Aluno).where(Aluno.usuario_id == current_user.id))


def _situacao(atividade: Atividade, entregue: bool, agora: datetime) -> str:
    if entregue:
        return 'concluida'
    if atividade.prazo < agora:
        return 'vencida'
    return 'pendente'


@router.get('/turmas/{turma_id}/atividades', response_model=AtividadeList)
def read_atividades(
    turma_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    turma = _turma_ou_404(session, turma_id)

    if not pode_acessar_turma(session, current_user, turma):
        raise _permissao_negada()

    gerencia = pode_gerenciar_turma(current_user, turma)
    consulta = select(Atividade).where(Atividade.turma_id == turma.id)
    if not gerencia:
        consulta = consulta.where(Atividade.publicada.is_(True))
    atividades = session.scalars(consulta.order_by(Atividade.prazo, Atividade.titulo)).all()

    if gerencia:
        return {
            'atividades': [
                AtividadePublic.model_validate(a).model_copy(update={'situacao': None})
                for a in atividades
            ]
        }

    aluno = _aluno_do_usuario(session, current_user)
    entregues = set()
    if aluno is not None:
        entregues = set(
            session.scalars(
                select(Entrega.atividade_id)
                .join(Atividade, Atividade.id == Entrega.atividade_id)
                .where(Atividade.turma_id == turma.id, Entrega.aluno_id == aluno.id)
            ).all()
        )

    agora = datetime.now()
    return {
        'atividades': [
            AtividadePublic.model_validate(a).model_copy(
                update={'situacao': _situacao(a, a.id in entregues, agora)}
            )
            for a in atividades
        ]
    }


@router.post(
    '/turmas/{turma_id}/atividades',
    status_code=HTTPStatus.CREATED,
    response_model=AtividadePublic,
)
def create_atividade(
    turma_id: UUID,
    atividade: AtividadeCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    turma = _turma_ou_404(session, turma_id)

    if not pode_gerenciar_turma(current_user, turma):
        raise _permissao_negada()

    if atividade.modulo_id is not None:
        modulo = session.get(Modulo, atividade.modulo_id)
        if modulo is None or modulo.turma_id != turma.id:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='Módulo não pertence a esta turma',
            )

    db_atividade = Atividade(
        turma_id=turma.id,
        titulo=atividade.titulo,
        tipo=atividade.tipo,
        categoria=atividade.categoria,
        prazo=atividade.prazo.replace(tzinfo=None),
        pontos=atividade.pontos,
        descricao=atividade.descricao,
        publicada=atividade.publicada,
        modulo_id=atividade.modulo_id,
    )
    session.add(db_atividade)
    session.commit()
    session.refresh(db_atividade)

    return AtividadePublic.model_validate(db_atividade).model_copy(
        update={'situacao': None}
    )


@router.post(
    '/atividades/{atividade_id}/entrega',
    response_model=EntregaPublic,
)
def registrar_entrega(
    atividade_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    atividade = session.get(Atividade, atividade_id)
    if atividade is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Atividade não encontrada'
        )

    turma = _turma_ou_404(session, atividade.turma_id)
    if not atividade.publicada or not pode_acessar_turma(session, current_user, turma):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Atividade não encontrada'
        )

    aluno = _aluno_do_usuario(session, current_user)
    if aluno is None:
        raise _permissao_negada()

    entrega = session.get(Entrega, (atividade.id, aluno.id))
    if entrega is None:
        entrega = Entrega(atividade_id=atividade.id, aluno_id=aluno.id)
        session.add(entrega)
        session.commit()
        session.refresh(entrega)

    return EntregaPublic(
        atividade_id=entrega.atividade_id,
        situacao='concluida',
        entregue_em=entrega.entregue_em,
    )
