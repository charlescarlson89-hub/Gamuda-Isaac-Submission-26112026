"""PostgreSQL tables based on the supplied user-based SoilSync schema.

Additional ownership, uniqueness and accounting columns enforce the frontend flows.
Passwords contain Argon2 hashes, never plaintext. All timestamps are UTC-aware.
"""

from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(40), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(80), nullable=False)
    points_balance: Mapped[int] = mapped_column(default=0, server_default="0")
    streak_days: Mapped[int] = mapped_column(default=0, server_default="0")
    tier: Mapped[str] = mapped_column(
        String(60), default="Tier 1: Beginner", server_default="Tier 1: Beginner"
    )
    terms_version: Mapped[str] = mapped_column(String(30), nullable=False)
    consented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    __table_args__ = (
        CheckConstraint("points_balance >= 0", name="users_nonnegative_points"),
        CheckConstraint("streak_days >= 0", name="users_nonnegative_streak"),
        Index("users_email_unique", func.lower(email), unique=True),
        Index("users_username_unique", func.lower(username), unique=True),
    )


class UserSettings(Base):
    __tablename__ = "user_settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    checkin_reminder: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    reward_received_notify: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    service_notices_notify: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    claim_reward_reminder: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    quiet_hours_start: Mapped[str] = mapped_column(
        String(5), default="22:00", server_default="22:00"
    )
    quiet_hours_end: Mapped[str] = mapped_column(String(5), default="07:00", server_default="07:00")


class GeminiCredential(Base):
    __tablename__ = "gemini_credentials"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    encrypted_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)


class DailyCheckin(Base):
    __tablename__ = "daily_checkins"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    checkin_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    points_awarded: Mapped[int] = mapped_column(default=10, server_default="10")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    __table_args__ = (
        UniqueConstraint("user_id", "checkin_date"),
        CheckConstraint("points_awarded = 10"),
    )


class WasteType(Base):
    __tablename__ = "waste_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    is_supported: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    rejection_reason: Mapped[str | None] = mapped_column(String(150))
    guide_recommendation: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    aliases: Mapped[list[str] | None] = mapped_column(JSON().with_variant(JSONB, "postgresql"))
    ingredient_role: Mapped[str | None] = mapped_column(String(20))
    reference_url: Mapped[str | None] = mapped_column(Text)


class ScanLog(Base):
    __tablename__ = "scan_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    waste_type_id: Mapped[int | None] = mapped_column(ForeignKey("waste_types.id"))
    points_earned: Mapped[int] = mapped_column(default=50, server_default="50")
    image_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), default="gemini")
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    result: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    __table_args__ = (
        UniqueConstraint("user_id", "image_sha256"),
        CheckConstraint("points_earned IN (0, 50)"),
    )


class FertilizerType(Base):
    __tablename__ = "fertilizer_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    est_days_to_finish: Mapped[int] = mapped_column(default=14, server_default="14")
    __table_args__ = (CheckConstraint("est_days_to_finish > 0"),)


class WasteFertilizerMatch(Base):
    __tablename__ = "waste_fertilizer_matches"
    id: Mapped[int] = mapped_column(primary_key=True)
    waste_type_id: Mapped[int] = mapped_column(
        ForeignKey("waste_types.id", ondelete="CASCADE"), nullable=False
    )
    fertilizer_type_id: Mapped[int] = mapped_column(
        ForeignKey("fertilizer_types.id", ondelete="CASCADE"), nullable=False
    )
    __table_args__ = (UniqueConstraint("waste_type_id", "fertilizer_type_id"),)


class Plant(Base):
    __tablename__ = "plants"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    plant_type: Mapped[str] = mapped_column(String(80), nullable=False)
    growth_stage: Mapped[str] = mapped_column(String(50), nullable=False)


class FertilizerSuitablePlant(Base):
    __tablename__ = "fertilizer_suitable_plants"
    id: Mapped[int] = mapped_column(primary_key=True)
    fertilizer_type_id: Mapped[int] = mapped_column(
        ForeignKey("fertilizer_types.id", ondelete="CASCADE"), nullable=False
    )
    plant_id: Mapped[int] = mapped_column(
        ForeignKey("plants.id", ondelete="CASCADE"), nullable=False
    )
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    notes: Mapped[str | None] = mapped_column(String(250))
    __table_args__ = (UniqueConstraint("fertilizer_type_id", "plant_id"),)


class FertilizerRecipeStep(Base):
    __tablename__ = "fertilizer_recipe_steps"
    id: Mapped[int] = mapped_column(primary_key=True)
    fertilizer_type_id: Mapped[int] = mapped_column(
        ForeignKey("fertilizer_types.id", ondelete="CASCADE"), nullable=False
    )
    step_number: Mapped[int] = mapped_column(nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        UniqueConstraint("fertilizer_type_id", "step_number"),
        CheckConstraint("step_number > 0"),
    )


class FertilizerMaintenanceGuide(Base):
    __tablename__ = "fertilizer_maintenance_guides"
    id: Mapped[int] = mapped_column(primary_key=True)
    fertilizer_type_id: Mapped[int] = mapped_column(
        ForeignKey("fertilizer_types.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    check_cadence: Mapped[str] = mapped_column(String(100), nullable=False)
    optimal_temp: Mapped[str] = mapped_column(String(150), nullable=False)
    moisture_range: Mapped[str] = mapped_column(String(150), nullable=False)


class Batch(Base):
    __tablename__ = "batches"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fertilizer_type_id: Mapped[int] = mapped_column(
        ForeignKey("fertilizer_types.id"), nullable=False
    )
    batch_number: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    client_request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="Active", server_default="Active")
    percentage_completed: Mapped[int] = mapped_column(default=0, server_default="0")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    est_completion_date: Mapped[datetime | None] = mapped_column(Date)
    __table_args__ = (
        UniqueConstraint("user_id", "client_request_id"),
        CheckConstraint("percentage_completed BETWEEN 0 AND 100"),
        CheckConstraint("status IN ('Active', 'Fermenting', 'Completed')"),
        CheckConstraint("(status = 'Completed') = (percentage_completed = 100)"),
    )


class WeeklyCheckinQuest(Base):
    __tablename__ = "weekly_checkin_quests"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_number: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(10), default="UPCOMING", server_default="UPCOMING")
    points_reward: Mapped[int] = mapped_column(default=100, server_default="100")
    available_on: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    image_proof_url: Mapped[str | None] = mapped_column(String(500))
    storage_key: Mapped[str | None] = mapped_column(String(300))
    photo_data: Mapped[bytes | None] = mapped_column(LargeBinary)
    image_sha256: Mapped[str | None] = mapped_column(String(64))
    verification: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB, "postgresql"))
    note: Mapped[str] = mapped_column(String(250), default="", server_default="")
    __table_args__ = (
        UniqueConstraint("batch_id", "week_number"),
        UniqueConstraint("batch_id", "image_sha256", name="uq_weekly_batch_image"),
        CheckConstraint("week_number BETWEEN 1 AND 105"),
        CheckConstraint("status IN ('UPCOMING', 'CURRENT', 'DONE')"),
        CheckConstraint("points_reward = 100"),
        CheckConstraint(
            "status <> 'DONE' OR (completed_at IS NOT NULL AND image_proof_url IS NOT NULL)"
        ),
    )


class Reward(Base):
    __tablename__ = "rewards"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    points_cost: Mapped[int] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    prototype_only: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    __table_args__ = (CheckConstraint("points_cost > 0"),)


class RewardClaim(Base):
    __tablename__ = "reward_claims"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reward_id: Mapped[int] = mapped_column(ForeignKey("rewards.id"), nullable=False)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    claim_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    points_spent: Mapped[int] = mapped_column(nullable=False)
    is_redeemed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    claimed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    __table_args__ = (
        UniqueConstraint("user_id", "reward_id"),
        UniqueConstraint("user_id", "request_id"),
        CheckConstraint("points_spent > 0"),
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )


class PointsLedger(Base):
    __tablename__ = "points_ledger"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    points: Mapped[int] = mapped_column(nullable=False)
    reason: Mapped[str] = mapped_column(String(150), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    __table_args__ = (CheckConstraint("points <> 0"),)
