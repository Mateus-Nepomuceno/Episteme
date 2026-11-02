from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '26f509f2b338'
down_revision: Union[str, Sequence[str], None] = '5f0612ed9be3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('alunos', 'matricula_id')
    op.drop_column('professores', 'matricula_id')


def downgrade() -> None:
    op.add_column('professores', sa.Column('matricula_id', sa.VARCHAR(), nullable=True))
    op.add_column('alunos', sa.Column('matricula_id', sa.VARCHAR(), nullable=True))
