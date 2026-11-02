from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '543e3aa99691'
down_revision: Union[str, Sequence[str], None] = '68f1c5bb7218'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('chamadas',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('turma_id', sa.Uuid(), nullable=False),
    sa.Column('data', sa.Date(), nullable=False),
    sa.ForeignKeyConstraint(['turma_id'], ['turmas.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('turma_id', 'data')
    )
    op.create_table('presencas',
    sa.Column('chamada_id', sa.Uuid(), nullable=False),
    sa.Column('aluno_id', sa.Uuid(), nullable=False),
    sa.Column('presente', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['aluno_id'], ['alunos.id'], ),
    sa.ForeignKeyConstraint(['chamada_id'], ['chamadas.id'], ),
    sa.PrimaryKeyConstraint('chamada_id', 'aluno_id')
    )


def downgrade() -> None:
    op.drop_table('presencas')
    op.drop_table('chamadas')
