from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c775a07c90c9'
down_revision: Union[str, Sequence[str], None] = '07a99d6bc9cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.add_column(sa.Column('matricula', sa.String(), nullable=True))
        batch_op.create_unique_constraint('uq_usuarios_matricula', ['matricula'])


def downgrade() -> None:
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.drop_constraint('uq_usuarios_matricula', type_='unique')
        batch_op.drop_column('matricula')
