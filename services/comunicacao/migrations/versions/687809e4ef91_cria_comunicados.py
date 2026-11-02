from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '687809e4ef91'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('comunicados',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('titulo', sa.String(), nullable=False),
    sa.Column('resumo', sa.String(), nullable=False),
    sa.Column('corpo', sa.String(), nullable=False),
    sa.Column('publicado', sa.Boolean(), nullable=False),
    sa.Column('publicado_em', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('comunicados')
