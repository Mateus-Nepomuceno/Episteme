from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '518bb0ab9ec7'
down_revision: Union[str, Sequence[str], None] = 'e16b2ebe9368'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('atividades',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('turma_id', sa.Uuid(), nullable=False),
    sa.Column('titulo', sa.String(), nullable=False),
    sa.Column('tipo', sa.String(), nullable=False),
    sa.Column('categoria', sa.String(), nullable=False),
    sa.Column('prazo', sa.DateTime(), nullable=False),
    sa.Column('pontos', sa.Double(), nullable=True),
    sa.Column('descricao', sa.String(), nullable=True),
    sa.Column('publicada', sa.Boolean(), nullable=False),
    sa.Column('modulo_id', sa.Uuid(), nullable=True),
    sa.ForeignKeyConstraint(['modulo_id'], ['modulos.id'], ),
    sa.ForeignKeyConstraint(['turma_id'], ['turmas.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('entregas',
    sa.Column('atividade_id', sa.Uuid(), nullable=False),
    sa.Column('aluno_id', sa.Uuid(), nullable=False),
    sa.Column('entregue_em', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['aluno_id'], ['alunos.id'], ),
    sa.ForeignKeyConstraint(['atividade_id'], ['atividades.id'], ),
    sa.PrimaryKeyConstraint('atividade_id', 'aluno_id')
    )


def downgrade() -> None:
    op.drop_table('entregas')
    op.drop_table('atividades')
