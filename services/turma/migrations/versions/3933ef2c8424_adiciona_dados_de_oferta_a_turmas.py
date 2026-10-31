"""adiciona dados de oferta a turmas

Revision ID: 3933ef2c8424
Revises: 208bb74e499a
Create Date: 2026-10-31 17:05:37.212947

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3933ef2c8424'
down_revision: Union[str, Sequence[str], None] = '208bb74e499a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('turmas', schema=None) as batch_op:
        batch_op.add_column(sa.Column('codigo', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('curso_id', sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column('periodo_letivo', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('capacidade', sa.Integer(), nullable=True))
        batch_op.alter_column(
            'professor_id', existing_type=sa.Uuid(), nullable=True
        )


def downgrade() -> None:
    with op.batch_alter_table('turmas', schema=None) as batch_op:
        batch_op.alter_column(
            'professor_id', existing_type=sa.Uuid(), nullable=False
        )
        batch_op.drop_column('capacidade')
        batch_op.drop_column('periodo_letivo')
        batch_op.drop_column('curso_id')
        batch_op.drop_column('codigo')
