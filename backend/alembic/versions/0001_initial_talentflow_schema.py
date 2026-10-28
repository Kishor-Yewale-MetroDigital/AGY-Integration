"""Initial TalentFlow schema with immutable audit protection

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-28 19:00:00
"""
from typing import Sequence, Union
from alembic import op

from app.database import Base
import app.models.entities  # noqa: F401

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

    if bind.dialect.name == "postgresql":
        op.execute(
            """
            CREATE OR REPLACE FUNCTION prevent_audit_event_mutation()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'Audit events are immutable and cannot be modified or deleted.';
            END;
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS trg_prevent_audit_mutation ON audit_events;
            CREATE TRIGGER trg_prevent_audit_mutation
            BEFORE UPDATE OR DELETE ON audit_events
            FOR EACH ROW EXECUTE FUNCTION prevent_audit_event_mutation();
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_prevent_audit_mutation ON audit_events;")
        op.execute("DROP FUNCTION IF EXISTS prevent_audit_event_mutation();")
    Base.metadata.drop_all(bind=bind)
