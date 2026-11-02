from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '5574cb700012'
down_revision: Union[str, Sequence[str], None] = '543e3aa99691'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('turmas', sa.Column('encerrada_em', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('turmas', 'encerrada_em')
