"""add_human_resolution

Revision ID: 3942b7d0c201
Revises: 
Create Date: 2026-05-03 08:33:11.821694+00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '3942b7d0c201'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tickets', sa.Column('human_resolution', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('tickets', 'human_resolution')
