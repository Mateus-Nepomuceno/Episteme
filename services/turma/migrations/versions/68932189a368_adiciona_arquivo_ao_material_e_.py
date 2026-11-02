from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '68932189a368'
down_revision: Union[str, Sequence[str], None] = '78410b816dad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('materiais', sa.Column('arquivo_nome', sa.String(), nullable=True))
    op.add_column('materiais', sa.Column('arquivo_caminho', sa.String(), nullable=True))
    op.add_column('turma_aluno', sa.Column('trancada_em', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('turma_aluno', 'trancada_em')
    op.drop_column('materiais', 'arquivo_caminho')
    op.drop_column('materiais', 'arquivo_nome')
