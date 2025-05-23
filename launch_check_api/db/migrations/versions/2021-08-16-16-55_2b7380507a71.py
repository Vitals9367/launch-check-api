"""Created Dummy Model.

Revision ID: 2b7380507a71
Revises: 819cbf6e030b
Create Date: 2021-08-16 16:55:25.157309

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2b7380507a71"
down_revision = "819cbf6e030b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Run the upgrade migrations."""
    op.create_table(
        "dummy_model",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Run the downgrade migrations."""
    op.drop_table("dummy_model")
    # ### end Alembic commands ###
