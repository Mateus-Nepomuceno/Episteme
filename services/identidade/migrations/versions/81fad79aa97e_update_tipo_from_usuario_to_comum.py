"""update tipo from USUARIO to COMUM

Revision ID: 81fad79aa97e
Revises: b4decd5fc102
Create Date: 2026-10-02 18:05:41.373890

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81fad79aa97e'
down_revision: Union[str, Sequence[str], None] = 'b4decd5fc102'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("UPDATE usuarios SET tipo = 'COMUM' WHERE tipo = 'USUARIO'")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE usuarios SET tipo = 'USUARIO' WHERE tipo = 'COMUM'")
