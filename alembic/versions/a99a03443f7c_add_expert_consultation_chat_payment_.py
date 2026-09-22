"""add expert consultation chat payment notifications

Revision ID: a99a03443f7c
Revises: d7e566bbdf7e
Create Date: 2026-09-20 13:51:17.479824
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a99a03443f7c"
down_revision: Union[str, Sequence[str], None] = "d7e566bbdf7e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # =========================================================
    # 1. Add EXPERT role
    # =========================================================

    op.execute(
        "ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'expert'"
    )

    # =========================================================
    # 2. Experts
    # =========================================================

    op.create_table("experts",sa.Column("expert_id",sa.Integer(),nullable=False),
    sa.Column("user_id",sa.Integer(),nullable=False),
    sa.Column("specialization",sa.String(),nullable=False),
    sa.Column("bio",sa.Text(),nullable=True),
    sa.Column("experience_years",sa.Integer(),nullable=False),
    sa.Column("consultation_price",sa.Numeric(precision=10, scale=2),nullable=False),
    sa.Column("is_available",sa.Boolean(),nullable=False),
    sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=True),
    sa.ForeignKeyConstraint( ["user_id"],["users.user_id"]),
    sa.PrimaryKeyConstraint("expert_id"),
    sa.UniqueConstraint("user_id")
    )

    op.create_index(op.f("ix_experts_expert_id"),"experts",["expert_id"],unique=False)

    # =========================================================
    # 3. Consultations
    # =========================================================

    op.create_table("consultations",
    sa.Column("consultation_id",sa.Integer(),nullable=False),
    sa.Column("farmer_id",sa.Integer(),nullable=False),
    sa.Column("expert_id",sa.Integer(),nullable=False),
    sa.Column("diagnosis_id",sa.Integer(),nullable=True),
    sa.Column("status",sa.Enum("PENDING_PAYMENT","OPEN","WAITING_EXPERT","WAITING_FARMER","CLOSED",name="consultationstatus"),nullable=False),
    sa.Column("questions_used",sa.Integer(),nullable=False),
    sa.Column("max_questions",sa.Integer(),nullable=False),
    sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=True),
    sa.Column("closed_at",sa.DateTime(timezone=True),nullable=True),
    sa.ForeignKeyConstraint( ["diagnosis_id"], ["diagnoses.diagnosis_id"]),
    sa.ForeignKeyConstraint(["expert_id"],["experts.expert_id"]),
    sa.ForeignKeyConstraint(["farmer_id"],["farmers.farmer_id"]),
    sa.PrimaryKeyConstraint("consultation_id"))

    op.create_index(
        op.f("ix_consultations_consultation_id"),
        "consultations",
        ["consultation_id"],
        unique=False
    )

    # =========================================================
    # 4. Consultation Messages
    # =========================================================

    op.create_table(
        "consultation_messages",

        sa.Column(
            "message_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "consultation_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "sender_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "message",
            sa.Text(),
            nullable=True
        ),

        sa.Column(
            "image_url",
            sa.String(),
            nullable=True
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True
        ),

        sa.ForeignKeyConstraint(
            ["consultation_id"],
            ["consultations.consultation_id"]
        ),

        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["users.user_id"]
        ),

        sa.PrimaryKeyConstraint("message_id")
    )

    op.create_index(
        op.f("ix_consultation_messages_message_id"),
        "consultation_messages",
        ["message_id"],
        unique=False
    )

    # =========================================================
    # 5. Notifications
    # =========================================================

    op.create_table(
        "notifications",

        sa.Column(
            "notification_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "consultation_id",
            sa.Integer(),
            nullable=True
        ),

        sa.Column(
            "type",
            sa.Enum(
                "NEW_CONSULTATION",
                "NEW_FARMER_MESSAGE",
                "EXPERT_REPLY",
                "CONSULTATION_CLOSED",
                name="notificationtype"
            ),
            nullable=False
        ),

        sa.Column(
            "title",
            sa.String(),
            nullable=False
        ),

        sa.Column(
            "message",
            sa.Text(),
            nullable=False
        ),

        sa.Column(
            "is_read",
            sa.Boolean(),
            nullable=False
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True
        ),

        sa.ForeignKeyConstraint(
            ["consultation_id"],
            ["consultations.consultation_id"]
        ),

        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"]
        ),

        sa.PrimaryKeyConstraint("notification_id")
    )

    op.create_index(
        op.f("ix_notifications_notification_id"),
        "notifications",
        ["notification_id"],
        unique=False
    )

    # =========================================================
    # 6. Replace old payments table
    # =========================================================

    # Old payments table is empty, so we replace it completely.
    op.drop_table("payments")

    # Remove the old PostgreSQL paymentstatus enum.
    old_payment_status = postgresql.ENUM(
        "pending",
        "approved",
        "rejected",
        name="paymentstatus"
    )

    old_payment_status.drop(
        op.get_bind(),
        checkfirst=True
    )

    # =========================================================
    # 7. Create new payments table
    # =========================================================

    op.create_table(
        "payments",

        sa.Column(
            "payment_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "consultation_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "farmer_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "amount",
            sa.Numeric(precision=10, scale=2),
            nullable=False
        ),

        sa.Column(
            "currency",
            sa.String(length=10),
            nullable=False
        ),

        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "PAID",
                "FAILED",
                "CANCELLED",
                name="paymentstatus"
            ),
            nullable=False
        ),

        sa.Column(
            "payment_method",
            sa.String(),
            nullable=True
        ),

        sa.Column(
            "transaction_id",
            sa.String(),
            nullable=True
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True
        ),

        sa.Column(
            "paid_at",
            sa.DateTime(timezone=True),
            nullable=True
        ),

        sa.ForeignKeyConstraint(
            ["consultation_id"],
            ["consultations.consultation_id"]
        ),

        sa.ForeignKeyConstraint(
            ["farmer_id"],
            ["farmers.farmer_id"]
        ),

        sa.PrimaryKeyConstraint("payment_id"),

        sa.UniqueConstraint("transaction_id")
    )

    op.create_index(
        op.f("ix_payments_payment_id"),
        "payments",
        ["payment_id"],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    # =========================================================
    # 1. Remove new payments table
    # =========================================================

    op.drop_index(
        op.f("ix_payments_payment_id"),
        table_name="payments"
    )

    op.drop_table("payments")

    # Remove new paymentstatus enum.
    new_payment_status = postgresql.ENUM(
        "PENDING",
        "PAID",
        "FAILED",
        "CANCELLED",
        name="paymentstatus"
    )

    new_payment_status.drop(
        op.get_bind(),
        checkfirst=True
    )

    # =========================================================
    # 2. Recreate old paymentstatus enum
    # =========================================================

    old_payment_status = postgresql.ENUM(
        "pending",
        "approved",
        "rejected",
        name="paymentstatus"
    )

    old_payment_status.create(
        op.get_bind(),
        checkfirst=True
    )

    # =========================================================
    # 3. Recreate old payments table
    # =========================================================

    op.create_table(
        "payments",

        sa.Column(
            "payment_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "farmer_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "diagnosis_id",
            sa.Integer(),
            nullable=False
        ),

        sa.Column(
            "admin_id",
            sa.Integer(),
            nullable=True
        ),

        sa.Column(
            "amount",
            sa.Numeric(precision=10, scale=2),
            nullable=False
        ),

        sa.Column(
            "currency",
            sa.String(length=50),
            nullable=False
        ),

        sa.Column(
            "provider",
            sa.String(length=50),
            nullable=False
        ),

        sa.Column(
            "payment_status",
            old_payment_status,
            nullable=False
        ),

        sa.Column(
            "transaction_ref",
            sa.String(length=100),
            nullable=True
        ),

        sa.Column(
            "payment_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True
        ),

        sa.ForeignKeyConstraint(
            ["farmer_id"],
            ["farmers.farmer_id"],
            ondelete="CASCADE"
        ),

        sa.ForeignKeyConstraint(
            ["diagnosis_id"],
            ["diagnoses.diagnosis_id"]
        ),

        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["admins.admin_id"]
        ),

        sa.PrimaryKeyConstraint("payment_id"),

        sa.UniqueConstraint(
            "diagnosis_id",
            name="payments_diagnosis_id_key"
        )
    )

    # =========================================================
    # 4. Remove notifications
    # =========================================================

    op.drop_index(
        op.f("ix_notifications_notification_id"),
        table_name="notifications"
    )

    op.drop_table("notifications")

    # =========================================================
    # 5. Remove consultation messages
    # =========================================================

    op.drop_index(
        op.f("ix_consultation_messages_message_id"),
        table_name="consultation_messages"
    )

    op.drop_table("consultation_messages")

    # =========================================================
    # 6. Remove consultations
    # =========================================================

    op.drop_index(
        op.f("ix_consultations_consultation_id"),
        table_name="consultations"
    )

    op.drop_table("consultations")

    # =========================================================
    # 7. Remove experts
    # =========================================================

    op.drop_index(
        op.f("ix_experts_expert_id"),
        table_name="experts"
    )

    op.drop_table("experts")

    # NOTE:
    # We intentionally do not remove 'expert' from userrole.
    # PostgreSQL does not support ALTER TYPE ... DROP VALUE directly.