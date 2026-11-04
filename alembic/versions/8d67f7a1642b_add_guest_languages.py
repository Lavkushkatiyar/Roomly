"""add supported guest languages

Revision ID: 8d67f7a1642b
Revises: 7aa4b5d0555f
Create Date: 2026-11-04 19:50:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "8d67f7a1642b"
down_revision: str | Sequence[str] | None = "530e770b59c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


LANGUAGE_ENUM_NAMES = (
    "HINGLISH",
    "TAMIL",
    "TELUGU",
    "KANNADA",
    "MALAYALAM",
    "MARATHI",
    "BENGALI",
    "GUJARATI",
    "PUNJABI",
)


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for language in LANGUAGE_ENUM_NAMES:
            op.execute(
                f"ALTER TYPE guest_language ADD VALUE IF NOT EXISTS '{language}'"
            )


def downgrade() -> None:
    # PostgreSQL enum labels are intentionally retained on downgrade because
    # removing them requires rebuilding the type and can invalidate stored rows.
    pass
