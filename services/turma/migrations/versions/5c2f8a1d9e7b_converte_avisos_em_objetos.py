"""converte avisos de turmas em objetos estruturados

Revision ID: 5c2f8a1d9e7b
Revises: 3933ef2c8424
Create Date: 2026-11-01 10:00:00.000000

"""
from datetime import date, datetime
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c2f8a1d9e7b'
down_revision: Union[str, Sequence[str], None] = '3933ef2c8424'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

AUTOR_PADRAO = 'Não informado'
TITULO_PADRAO = 'Aviso'

turmas = sa.table(
    'turmas',
    sa.column('id', sa.Uuid()),
    sa.column('avisos', sa.JSON()),
    sa.column('criado_em', sa.DateTime()),
)


def _data_de_criacao(criado_em) -> str:
    if isinstance(criado_em, datetime):
        return criado_em.date().isoformat()
    return date.fromisoformat(str(criado_em)[:10]).isoformat()


def upgrade() -> None:
    conexao = op.get_bind()
    linhas = conexao.execute(
        sa.select(turmas.c.id, turmas.c.avisos, turmas.c.criado_em)
    ).all()

    for turma_id, avisos, criado_em in linhas:
        data = _data_de_criacao(criado_em)
        novos_avisos = [
            aviso
            if isinstance(aviso, dict)
            else {
                'id': str(uuid4()),
                'autor': AUTOR_PADRAO,
                'data': data,
                'titulo': TITULO_PADRAO,
                'mensagem': aviso,
            }
            for aviso in (avisos or [])
        ]
        conexao.execute(
            turmas.update()
            .where(turmas.c.id == turma_id)
            .values(avisos=novos_avisos)
        )


def downgrade() -> None:
    conexao = op.get_bind()
    linhas = conexao.execute(sa.select(turmas.c.id, turmas.c.avisos)).all()

    for turma_id, avisos in linhas:
        textos = [
            aviso['mensagem'] if isinstance(aviso, dict) else aviso
            for aviso in (avisos or [])
        ]
        conexao.execute(
            turmas.update().where(turmas.c.id == turma_id).values(avisos=textos)
        )
