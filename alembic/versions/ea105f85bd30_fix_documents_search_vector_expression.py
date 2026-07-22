"""fix documents.search_vector expression

Revision ID: ea105f85bd30
Revises: 206378bf403d
Create Date: 2026-07-22 09:08:13.278212

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ea105f85bd30'
down_revision: Union[str, Sequence[str], None] = '206378bf403d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Generated columns can't be ALTERed in place — Postgres requires
    # drop + recreate to change the expression. Index depends on the
    # column, so it has to go first; then rebuild both in reverse order.
    op.drop_index('ix_documents_search_vector', table_name='documents', postgresql_using='gin')
    op.drop_column('documents', 'search_vector')
    op.add_column(
        'documents',
        sa.Column(
            'search_vector',
            postgresql.TSVECTOR(),
            sa.Computed(
                r"to_tsvector('english', regexp_replace(regexp_replace(filename, "
                r"'\.[^.]+$', ''), '[_-]', ' ', 'g'))",
                persisted=True,
            ),
            nullable=True,
        ),
    )
    op.create_index(
        'ix_documents_search_vector', 'documents', ['search_vector'], unique=False, postgresql_using='gin'
    )


def downgrade() -> None:
    op.drop_index('ix_documents_search_vector', table_name='documents', postgresql_using='gin')
    op.drop_column('documents', 'search_vector')
    op.add_column(
        'documents',
        sa.Column(
            'search_vector',
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', filename)", persisted=True),
            nullable=True,
        ),
    )
    op.create_index(
        'ix_documents_search_vector', 'documents', ['search_vector'], unique=False, postgresql_using='gin'
    )