from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e16b2ebe9368'
down_revision: Union[str, Sequence[str], None] = '5c2f8a1d9e7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('modulos',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('turma_id', sa.Uuid(), nullable=False),
    sa.Column('titulo', sa.String(), nullable=False),
    sa.Column('ordem', sa.Integer(), nullable=False),
    sa.Column('publicado', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['turma_id'], ['turmas.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('materiais',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('modulo_id', sa.Uuid(), nullable=False),
    sa.Column('titulo', sa.String(), nullable=False),
    sa.Column('tipo', sa.String(), nullable=False),
    sa.Column('ordem', sa.Integer(), nullable=False),
    sa.Column('descricao', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['modulo_id'], ['modulos.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('acessos_material',
    sa.Column('material_id', sa.Uuid(), nullable=False),
    sa.Column('aluno_id', sa.Uuid(), nullable=False),
    sa.Column('aberto_em', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['aluno_id'], ['alunos.id'], ),
    sa.ForeignKeyConstraint(['material_id'], ['materiais.id'], ),
    sa.PrimaryKeyConstraint('material_id', 'aluno_id')
    )


def downgrade() -> None:
    op.drop_table('acessos_material')
    op.drop_table('materiais')
    op.drop_table('modulos')
