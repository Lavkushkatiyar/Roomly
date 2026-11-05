"""create roomly conversations table

Revision ID: b17f3c9a2d41
Revises: 8d67f7a1642b
Create Date: 2026-11-05 04:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b17f3c9a2d41"
down_revision: str | Sequence[str] | None = "8d67f7a1642b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roomly_conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column(
            "guest_language",
            sa.Enum(
                "ENGLISH",
                "Hindi",
                "HINGLISH",
                "TAMIL",
                "TELUGU",
                "KANNADA",
                "MALAYALAM",
                "MARATHI",
                "BENGALI",
                "GUJARATI",
                "PUNJABI",
                name="roomly_guest_language",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "ENDED", name="roomly_conversation_status"),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["room_id"], ["hotel_rooms.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_roomly_conversations_room_id"),
        "roomly_conversations",
        ["room_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_roomly_conversations_room_id"),
        table_name="roomly_conversations",
    )
    op.drop_table("roomly_conversations")

    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE roomly_conversation_status")
        op.execute("DROP TYPE roomly_guest_language")
