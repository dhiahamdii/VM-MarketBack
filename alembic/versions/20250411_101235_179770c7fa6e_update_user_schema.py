"""update_user_schema

Revision ID: 179770c7fa6e
Revises: 1ad1f5513043
Create Date: 2025-04-11 10:12:35.874265+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '179770c7fa6e'
down_revision: Union[str, None] = '1ad1f5513043'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
