from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '68f1c5bb7218'
down_revision: Union[str, Sequence[str], None] = '518bb0ab9ec7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('avaliacoes',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('turma_id', sa.Uuid(), nullable=False),
    sa.Column('nome', sa.String(), nullable=False),
    sa.Column('tipo', sa.String(), nullable=False),
    sa.Column('data', sa.Date(), nullable=False),
    sa.Column('peso', sa.Double(), nullable=False),
    sa.ForeignKeyConstraint(['turma_id'], ['turmas.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('notas',
    sa.Column('avaliacao_id', sa.Uuid(), nullable=False),
    sa.Column('aluno_id', sa.Uuid(), nullable=False),
    sa.Column('valor', sa.Double(), nullable=False),
    sa.Column('lancada_em', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['aluno_id'], ['alunos.id'], ),
    sa.ForeignKeyConstraint(['avaliacao_id'], ['avaliacoes.id'], ),
    sa.PrimaryKeyConstraint('avaliacao_id', 'aluno_id')
    )


def downgrade() -> None:
    op.drop_table('notas')
    op.drop_table('avaliacoes')
