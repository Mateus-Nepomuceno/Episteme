"""adiciona validade e versao

Revision ID: 8f12a9c3d4e5
Revises: 687809e4ef91
Create Date: 2026-11-05 23:45:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '8f12a9c3d4e5'
down_revision: str | Sequence[str] | None = '687809e4ef91'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('comunicados', sa.Column('inicio_em', sa.DateTime(), nullable=True))
    op.add_column('comunicados', sa.Column('expira_em', sa.DateTime(), nullable=True))
    op.add_column('comunicados', sa.Column('versao', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('comunicados', sa.Column('atualizado_em', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('comunicados', 'atualizado_em')
    op.drop_column('comunicados', 'versao')
    op.drop_column('comunicados', 'expira_em')
    op.drop_column('comunicados', 'inicio_em')
