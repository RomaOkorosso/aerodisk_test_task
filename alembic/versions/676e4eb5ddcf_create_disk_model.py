"""create disk model

Revision ID: 676e4eb5ddcf
Revises: cb860ee888c1
Create Date: 2023-04-11 21:16:27.241488

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "676e4eb5ddcf"
down_revision = "cb860ee888c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "disks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.Column("filesystem", sa.String(), nullable=True),
        sa.Column("mountpoint", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_disks_id"), "disks", ["id"], unique=False)
    op.create_index(op.f("ix_disks_name"), "disks", ["name"], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_disks_name"), table_name="disks")
    op.drop_index(op.f("ix_disks_id"), table_name="disks")
    op.drop_table("disks")
    # ### end Alembic commands ###
