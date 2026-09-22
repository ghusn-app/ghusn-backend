"""update diagnosis and consultation workflow

Revision ID: ae8b891e5c66
Revises: a99a03443f7c
Create Date: 2026-09-22 13:01:09.767752
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# =========================================================
# Alembic identifiers
# =========================================================

revision: str = "ae8b891e5c66"
down_revision: Union[str, Sequence[str], None] = "a99a03443f7c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# =========================================================
# ENUM definitions
# =========================================================

diagnosis_source_enum = postgresql.ENUM(
    "AI",
    "EXPERT",
    name="diagnosissource",
    create_type=False,
)

diagnosis_status_enum = postgresql.ENUM(
    "PENDING",
    "CONFIRMED",
    "UNCERTAIN",
    name="diagnosisstatus",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""

    # =====================================================
    # 1. Update ConsultationStatus ENUM
    # =====================================================

    op.execute(
        """
        ALTER TYPE consultationstatus
        ADD VALUE IF NOT EXISTS 'PENDING_EXPERT'
        """
    )

    op.execute(
        """
        ALTER TYPE consultationstatus
        ADD VALUE IF NOT EXISTS 'REJECTED'
        """
    )

    # =====================================================
    # 2. Update consultations table
    # =====================================================

    # AI diagnosis linked to the consultation
    op.add_column(
        "consultations",
        sa.Column(
            "ai_diagnosis_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    # Final diagnosis created by the expert
    op.add_column(
        "consultations",
        sa.Column(
            "expert_diagnosis_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    # Remove the FK for the old diagnosis_id column
    op.drop_constraint(
        op.f("consultations_diagnosis_id_fkey"),
        "consultations",
        type_="foreignkey",
    )

    # Create FK for AI diagnosis
    op.create_foreign_key(
        "consultations_ai_diagnosis_id_fkey",
        "consultations",
        "diagnoses",
        ["ai_diagnosis_id"],
        ["diagnosis_id"],
    )

    # Create FK for expert diagnosis
    op.create_foreign_key(
        "consultations_expert_diagnosis_id_fkey",
        "consultations",
        "diagnoses",
        ["expert_diagnosis_id"],
        ["diagnosis_id"],
    )

    # Remove the old diagnosis_id column
    op.drop_column(
        "consultations",
        "diagnosis_id",
    )

    # =====================================================
    # 3. Add disease_name_by_expert
    # =====================================================

    op.add_column(
        "diagnoses",
        sa.Column(
            "disease_name_by_expert",
            sa.String(),
            nullable=True,
        ),
    )

    # =====================================================
    # 4. Create Diagnosis ENUM types
    # =====================================================

    diagnosis_source_enum.create(
        op.get_bind(),
        checkfirst=True,
    )

    diagnosis_status_enum.create(
        op.get_bind(),
        checkfirst=True,
    )

    # =====================================================
    # 5. Add source/status as NULLABLE first
    # =====================================================
    #
    # Important:
    # Existing diagnosis rows do not have values for these
    # columns yet. Therefore we cannot add them as NOT NULL
    # immediately.
    # =====================================================

    op.add_column(
        "diagnoses",
        sa.Column(
            "source",
            diagnosis_source_enum,
            nullable=True,
        ),
    )

    op.add_column(
        "diagnoses",
        sa.Column(
            "status",
            diagnosis_status_enum,
            nullable=True,
        ),
    )

    # =====================================================
    # 6. Backfill existing diagnoses
    # =====================================================
    #
    # Diagnoses created before the expert workflow were
    # produced by the AI.
    # =====================================================

    op.execute(
        """
        UPDATE diagnoses
        SET source = 'AI'
        WHERE source IS NULL
        """
    )

    op.execute(
        """
        UPDATE diagnoses
        SET status = 'CONFIRMED'
        WHERE status IS NULL
        """
    )

    # =====================================================
    # 7. Enforce NOT NULL
    # =====================================================

    op.alter_column(
        "diagnoses",
        "source",
        existing_type=diagnosis_source_enum,
        nullable=False,
    )

    op.alter_column(
        "diagnoses",
        "status",
        existing_type=diagnosis_status_enum,
        nullable=False,
    )

    # =====================================================
    # 8. Make diagnosis fields nullable where needed
    # =====================================================

    # Expert may enter a disease that does not exist
    # in the diseases dictionary.
    op.alter_column(
        "diagnoses",
        "disease_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    # Expert diagnosis does not necessarily need its
    # own image.
    op.alter_column(
        "diagnoses",
        "image_url",
        existing_type=sa.Text(),
        nullable=True,
    )

    # Expert diagnosis does not have an AI confidence score.
    op.alter_column(
        "diagnoses",
        "confidence_score",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""

    # =====================================================
    # 1. Restore diagnoses constraints
    # =====================================================
    #
    # Note:
    # If expert diagnoses have already been inserted with
    # NULL disease_id/image_url/confidence_score, downgrade
    # would require handling those rows first.
    # =====================================================

    op.alter_column(
        "diagnoses",
        "confidence_score",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        nullable=False,
    )

    op.alter_column(
        "diagnoses",
        "image_url",
        existing_type=sa.Text(),
        nullable=False,
    )

    op.alter_column(
        "diagnoses",
        "disease_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # =====================================================
    # 2. Remove new diagnosis columns
    # =====================================================

    op.drop_column(
        "diagnoses",
        "status",
    )

    op.drop_column(
        "diagnoses",
        "source",
    )

    op.drop_column(
        "diagnoses",
        "disease_name_by_expert",
    )

    # =====================================================
    # 3. Remove Diagnosis ENUM types
    # =====================================================

    diagnosis_status_enum.drop(
        op.get_bind(),
        checkfirst=True,
    )

    diagnosis_source_enum.drop(
        op.get_bind(),
        checkfirst=True,
    )

    # =====================================================
    # 4. Restore old consultation diagnosis_id
    # =====================================================

    op.add_column(
        "consultations",
        sa.Column(
            "diagnosis_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    # Remove new foreign keys
    op.drop_constraint(
        "consultations_expert_diagnosis_id_fkey",
        "consultations",
        type_="foreignkey",
    )

    op.drop_constraint(
        "consultations_ai_diagnosis_id_fkey",
        "consultations",
        type_="foreignkey",
    )

    # Restore old diagnosis FK
    op.create_foreign_key(
        "consultations_diagnosis_id_fkey",
        "consultations",
        "diagnoses",
        ["diagnosis_id"],
        ["diagnosis_id"],
    )

    # Remove new consultation columns
    op.drop_column(
        "consultations",
        "expert_diagnosis_id",
    )

    op.drop_column(
        "consultations",
        "ai_diagnosis_id",
    )

    # -----------------------------------------------------
    # PENDING_EXPERT and REJECTED are intentionally kept
    # inside consultationstatus.
    #
    # PostgreSQL does not support a simple:
    #
    # ALTER TYPE consultationstatus DROP VALUE ...
    # -----------------------------------------------------