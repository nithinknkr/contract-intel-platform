"""add chunks content tsvector

Revision ID: c19cf09d49f7
Revises: ea105f85bd30
Create Date: 2026-07-29 07:50:00.496677

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c19cf09d49f7'
down_revision: Union[str, Sequence[str], None] = 'ea105f85bd30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # New generated column — chunk content is never edited in place once
    # written, so a STORED generated column (computed once, indexed like
    # a normal column) is correct here, same mechanism as documents.search_vector.
    # No drop-first needed (unlike ea105f85bd30) since this is a brand-new
    # column, not a fix to an existing expression.
    op.add_column(
        'chunks',
        sa.Column(
            'content_tsvector',
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('english', content)",
                persisted=True,
            ),
            nullable=True,
        ),
    )
    op.create_index(
        'ix_chunks_content_tsvector', 'chunks', ['content_tsvector'], unique=False, postgresql_using='gin'
    )


def downgrade() -> None:
    op.drop_index('ix_chunks_content_tsvector', table_name='chunks', postgresql_using='gin')
    op.drop_column('chunks', 'content_tsvector')