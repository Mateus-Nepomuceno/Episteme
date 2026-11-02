from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '06cf6e1969d5'
down_revision: Union[str, Sequence[str], None] = '5574cb700012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('professores', sa.Column('nome', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('professores', 'nome')
