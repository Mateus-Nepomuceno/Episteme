from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import (
    AcessoMaterial,
    Aluno,
    Atividade,
    Avaliacao,
    Entrega,
    Material,
    Modulo,
    Nota,
    Turma,
)
from turma.permissoes import pode_acessar_turma
from turma.routers.frequencia import calcular_frequencia
from turma.schemas import DesempenhoAluno
from turma.security import CurrentUser, get_current_user

router = APIRouter(tags=['desempenho'])


def _turma_ou_404(session: Session, turma_id: UUID) -> Turma:
    turma = session.get(Turma, turma_id)
    if turma is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Turma não encontrada'
        )
    return turma


def _calcular_media(session: Session, turma_id: UUID, aluno_id: UUID) -> float | None:
    avaliacoes = session.scalars(
        select(Avaliacao).where(Avaliacao.turma_id == turma_id)
    ).all()
    if not avaliacoes:
        return None

    valores = {
        nota.avaliacao_id: nota.valor
        for nota in session.scalars(
            select(Nota)
            .join(Avaliacao, Avaliacao.id == Nota.avaliacao_id)
            .where(Avaliacao.turma_id == turma_id, Nota.aluno_id == aluno_id)
        ).all()
    }
    total_pesos = sum(a.peso for a in avaliacoes)
    soma = sum(valores.get(a.id, 0.0) * a.peso for a in avaliacoes)

    return round(soma / total_pesos, 2)


def _calcular_progresso(session: Session, turma_id: UUID, aluno_id: UUID) -> int | None:
    modulos = session.scalars(
        select(Modulo).where(Modulo.turma_id == turma_id, Modulo.publicado.is_(True))
    ).all()
    if not modulos:
        return None

    materiais_acessados = set(
        session.scalars(
            select(AcessoMaterial.material_id).where(AcessoMaterial.aluno_id == aluno_id)
        ).all()
    )
    atividades_entregues = set(
        session.scalars(
            select(Entrega.atividade_id).where(Entrega.aluno_id == aluno_id)
        ).all()
    )

    concluidos = 0
    for modulo in modulos:
        materiais = session.scalars(
            select(Material.id).where(Material.modulo_id == modulo.id)
        ).all()
        atividades = session.scalars(
            select(Atividade.id).where(
                Atividade.modulo_id == modulo.id, Atividade.publicada.is_(True)
            )
        ).all()

        if not materiais and not atividades:
            continue

        materiais_ok = all(m in materiais_acessados for m in materiais)
        atividades_ok = all(a in atividades_entregues for a in atividades)
        if materiais_ok and atividades_ok:
            concluidos += 1

    return round(concluidos * 100 / len(modulos))


@router.get(
    '/alunos/me/turmas/{turma_id}/desempenho',
    response_model=DesempenhoAluno,
)
def read_desempenho_aluno(
    turma_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    turma = _turma_ou_404(session, turma_id)

    aluno = session.scalar(select(Aluno).where(Aluno.usuario_id == current_user.id))
    if aluno is None or not pode_acessar_turma(session, current_user, turma):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    return DesempenhoAluno(
        media=_calcular_media(session, turma.id, aluno.id),
        frequencia=calcular_frequencia(session, turma.id, aluno.id).percentual,
        progresso=_calcular_progresso(session, turma.id, aluno.id),
    )
