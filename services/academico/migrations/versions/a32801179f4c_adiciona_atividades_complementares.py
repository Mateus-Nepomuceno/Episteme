from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a32801179f4c'
down_revision: Union[str, Sequence[str], None] = 'ac0bda1b0023'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('atividades_complementares',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('aluno_id', sa.Uuid(), nullable=False),
    sa.Column('descricao', sa.String(), nullable=False),
    sa.Column('horas', sa.Integer(), nullable=False),
    sa.Column('situacao', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('atividades_complementares')
