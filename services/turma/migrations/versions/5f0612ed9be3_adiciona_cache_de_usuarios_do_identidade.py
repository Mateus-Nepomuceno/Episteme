from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '5f0612ed9be3'
down_revision: Union[str, Sequence[str], None] = '68932189a368'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('usuarios_cache',
    sa.Column('usuario_id', sa.Uuid(), nullable=False),
    sa.Column('nome', sa.String(), nullable=False),
    sa.Column('matricula', sa.String(), nullable=True),
    sa.Column('atualizado_em', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('usuario_id')
    )


def downgrade() -> None:
    op.drop_table('usuarios_cache')
