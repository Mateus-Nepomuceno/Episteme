from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import Aluno, Avaliacao, Nota, Turma, TurmaAluno
from turma.permissoes import pode_acessar_turma, pode_gerenciar_turma
from turma.schemas import (
    AvaliacaoCreate,
    AvaliacaoList,
    AvaliacaoPublic,
    AvaliacaoUpdate,
    NotaAluno,
    NotaCreate,
    NotaPublic,
    NotasAlunoList,
)
from turma.security import CurrentUser, get_current_user

router = APIRouter(tags=['avaliacoes'])

LIMITE_PESOS = 100.0
TOLERANCIA = 1e-9


def _turma_ou_404(session: Session, turma_id: UUID) -> Turma:
    turma = session.get(Turma, turma_id)
    if turma is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Turma não encontrada'
        )
    return turma


def _avaliacao_ou_404(session: Session, avaliacao_id: UUID) -> Avaliacao:
    avaliacao = session.get(Avaliacao, avaliacao_id)
    if avaliacao is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Avaliação não encontrada'
        )
    return avaliacao


def _permissao_negada() -> HTTPException:
    return HTTPException(
        status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
    )


def _soma_pesos(session: Session, turma_id: UUID, excluir: UUID | None = None) -> float:
    pesos = session.scalars(
        select(Avaliacao.peso).where(
            Avaliacao.turma_id == turma_id,
            Avaliacao.id != excluir if excluir else True,
        )
    ).all()
    return float(sum(pesos))


def _garantir_limite_pesos(soma: float) -> None:
    if soma > LIMITE_PESOS + TOLERANCIA:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='A soma dos pesos da turma não pode ultrapassar 100',
        )


@router.get('/turmas/{turma_id}/avaliacoes', response_model=AvaliacaoList)
def read_avaliacoes(
    turma_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    turma = _turma_ou_404(session, turma_id)

    if not pode_acessar_turma(session, current_user, turma):
        raise _permissao_negada()

    avaliacoes = session.scalars(
        select(Avaliacao)
        .where(Avaliacao.turma_id == turma.id)
        .order_by(Avaliacao.data, Avaliacao.nome)
    ).all()

    return {
        'avaliacoes': [AvaliacaoPublic.model_validate(a) for a in avaliacoes],
        'soma_pesos': _soma_pesos(session, turma.id),
    }


@router.post(
    '/turmas/{turma_id}/avaliacoes',
    status_code=HTTPStatus.CREATED,
    response_model=AvaliacaoPublic,
)
def create_avaliacao(
    turma_id: UUID,
    avaliacao: AvaliacaoCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    turma = _turma_ou_404(session, turma_id)

    if not pode_gerenciar_turma(current_user, turma):
        raise _permissao_negada()

    _garantir_limite_pesos(_soma_pesos(session, turma.id) + avaliacao.peso)

    db_avaliacao = Avaliacao(
        turma_id=turma.id,
        nome=avaliacao.nome,
        tipo=avaliacao.tipo,
        data=avaliacao.data,
        peso=avaliacao.peso,
    )
    session.add(db_avaliacao)
    session.commit()
    session.refresh(db_avaliacao)

    return AvaliacaoPublic.model_validate(db_avaliacao)


@router.patch('/avaliacoes/{avaliacao_id}', response_model=AvaliacaoPublic)
def update_avaliacao(
    avaliacao_id: UUID,
    alteracao: AvaliacaoUpdate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    db_avaliacao = _avaliacao_ou_404(session, avaliacao_id)
    turma = _turma_ou_404(session, db_avaliacao.turma_id)

    if not pode_gerenciar_turma(current_user, turma):
        raise _permissao_negada()

    dados = alteracao.model_dump(exclude_unset=True)
    if 'peso' in dados:
        _garantir_limite_pesos(
            _soma_pesos(session, turma.id, excluir=db_avaliacao.id) + dados['peso']
        )

    for campo, valor in dados.items():
        setattr(db_avaliacao, campo, valor)
    session.commit()
    session.refresh(db_avaliacao)

    return AvaliacaoPublic.model_validate(db_avaliacao)


@router.put(
    '/avaliacoes/{avaliacao_id}/notas/{aluno_id}',
    response_model=NotaPublic,
)
def lancar_nota(
    avaliacao_id: UUID,
    aluno_id: UUID,
    nota: NotaCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    avaliacao = _avaliacao_ou_404(session, avaliacao_id)
    turma = _turma_ou_404(session, avaliacao.turma_id)

    if not pode_gerenciar_turma(current_user, turma):
        raise _permissao_negada()

    matriculado = session.scalar(
        select(TurmaAluno).where(
            TurmaAluno.turma_id == turma.id, TurmaAluno.aluno_id == aluno_id
        )
    )
    if matriculado is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Aluno não matriculado nesta turma',
        )

    db_nota = session.get(Nota, (avaliacao.id, aluno_id))
    if db_nota is None:
        db_nota = Nota(avaliacao_id=avaliacao.id, aluno_id=aluno_id, valor=nota.valor)
        session.add(db_nota)
    else:
        db_nota.valor = nota.valor
    session.commit()
    session.refresh(db_nota)

    return NotaPublic.model_validate(db_nota)


@router.get(
    '/alunos/me/turmas/{turma_id}/notas',
    response_model=NotasAlunoList,
)
def read_notas_aluno(
    turma_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    turma = _turma_ou_404(session, turma_id)

    aluno = session.scalar(select(Aluno).where(Aluno.usuario_id == current_user.id))
    if aluno is None or not pode_acessar_turma(session, current_user, turma):
        raise _permissao_negada()

    avaliacoes = session.scalars(
        select(Avaliacao)
        .where(Avaliacao.turma_id == turma.id)
        .order_by(Avaliacao.data, Avaliacao.nome)
    ).all()

    valores = {
        nota.avaliacao_id: nota.valor
        for nota in session.scalars(
            select(Nota)
            .join(Avaliacao, Avaliacao.id == Nota.avaliacao_id)
            .where(Avaliacao.turma_id == turma.id, Nota.aluno_id == aluno.id)
        ).all()
    }

    return {
        'notas': [
            NotaAluno(
                avaliacao_id=a.id,
                nome=a.nome,
                tipo=a.tipo,
                data=a.data,
                peso=a.peso,
                valor=valores.get(a.id),
            )
            for a in avaliacoes
        ]
    }
