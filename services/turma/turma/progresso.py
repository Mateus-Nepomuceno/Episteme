from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from turma.models import AcessoMaterial, Atividade, Entrega, Material, Modulo

STATUS_CONCLUIDO = 'completed'
STATUS_EM_ANDAMENTO = 'in_progress'
STATUS_PENDENTE = 'pending'


def status_modulo(session: Session, modulo: Modulo, aluno_id: UUID) -> str:
    materiais = set(
        session.scalars(
            select(Material.id).where(Material.modulo_id == modulo.id)
        ).all()
    )
    atividades = set(
        session.scalars(
            select(Atividade.id).where(
                Atividade.modulo_id == modulo.id,
                Atividade.publicada.is_(True),
            )
        ).all()
    )

    if not materiais and not atividades:
        return STATUS_PENDENTE

    acessados = set(
        session.scalars(
            select(AcessoMaterial.material_id).where(
                AcessoMaterial.aluno_id == aluno_id,
                AcessoMaterial.material_id.in_(materiais),
            )
        ).all()
    ) if materiais else set()
    entregues = set(
        session.scalars(
            select(Entrega.atividade_id).where(
                Entrega.aluno_id == aluno_id,
                Entrega.atividade_id.in_(atividades),
            )
        ).all()
    ) if atividades else set()

    if materiais <= acessados and atividades <= entregues:
        return STATUS_CONCLUIDO
    if acessados or entregues:
        return STATUS_EM_ANDAMENTO
    return STATUS_PENDENTE


def progresso_turma(session: Session, turma_id: UUID, aluno_id: UUID) -> int | None:
    modulos = session.scalars(
        select(Modulo).where(Modulo.turma_id == turma_id, Modulo.publicado.is_(True))
    ).all()
    if not modulos:
        return None

    concluidos = sum(
        1
        for modulo in modulos
        if status_modulo(session, modulo, aluno_id) == STATUS_CONCLUIDO
    )
    return round(concluidos * 100 / len(modulos))
