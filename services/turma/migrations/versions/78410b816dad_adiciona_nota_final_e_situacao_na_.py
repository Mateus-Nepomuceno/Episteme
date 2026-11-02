from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '78410b816dad'
down_revision: Union[str, Sequence[str], None] = '06cf6e1969d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('turma_aluno', sa.Column('nota_final', sa.Double(), nullable=True))
    op.add_column('turma_aluno', sa.Column('frequencia_final', sa.Integer(), nullable=True))
    op.add_column('turma_aluno', sa.Column('situacao', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('turma_aluno', 'situacao')
    op.drop_column('turma_aluno', 'frequencia_final')
    op.drop_column('turma_aluno', 'nota_final')
