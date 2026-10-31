"""rename is_admin to e_admin

Revision ID: 07a99d6bc9cc
Revises: a958bdfe4a9f
Create Date: 2026-10-02 18:25:22.433201

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07a99d6bc9cc'
down_revision: Union[str, Sequence[str], None] = 'a958bdfe4a9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.alter_column('is_admin', new_column_name='e_admin')

def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.alter_column('e_admin', new_column_name='is_admin')

    # ### end Alembic commands ###
