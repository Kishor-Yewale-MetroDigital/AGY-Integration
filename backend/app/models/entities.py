import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_uuid() -> str:
    return str(uuid.uuid4())


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    business_unit: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    cost_center: Mapped[str] = mapped_column(String(32), nullable=False)

    budgets: Mapped[list["Budget"]] = relationship(back_populates="department", cascade="all, delete-orphan")
    requests: Mapped[list["HiringRequest"]] = relationship(back_populates="department")


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    department_id: Mapped[str] = mapped_column(ForeignKey("departments.id"), nullable=False, index=True)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False, default=2026)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    allocated_budget: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    committed_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    actual_spent: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))

    department: Mapped["Department"] = relationship(back_populates="budgets")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    business_unit: Mapped[str] = mapped_column(String(64), nullable=False)
    department_id: Mapped[str | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class HiringRequest(Base):
    __tablename__ = "hiring_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    request_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    job_title: Mapped[str] = mapped_column(String(128), nullable=False)
    job_family: Mapped[str] = mapped_column(String(64), nullable=False)
    department_id: Mapped[str] = mapped_column(ForeignKey("departments.id"), nullable=False, index=True)
    business_unit: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(64), nullable=False)
    work_location: Mapped[str] = mapped_column(String(32), nullable=False)  # ONSITE | HYBRID | REMOTE
    job_grade: Mapped[str] = mapped_column(String(16), nullable=False, index=True)  # L3..L8, EXEC
    employment_type: Mapped[str] = mapped_column(String(32), nullable=False)  # FULL_TIME | CONTRACT | PART_TIME
    hiring_manager_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    request_owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    hiring_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # NEW_HEADCOUNT | REPLACEMENT
    headcount_requested: Mapped[int] = mapped_column(Integer, nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    expected_business_impact: Mapped[str] = mapped_column(Text, nullable=False)
    requested_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_hiring_date: Mapped[date] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    est_annual_salary_per_pos: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    est_benefits_cost_per_pos: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    est_recruitment_fee_per_pos: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    est_onetime_cost_per_pos: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_annualized_forecast: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT", index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    department: Mapped["Department"] = relationship(back_populates="requests")
    positions: Mapped[list["Position"]] = relationship(
        back_populates="hiring_request", cascade="all, delete-orphan", order_by="Position.position_index"
    )
    approval_steps: Mapped[list["ApprovalStep"]] = relationship(
        back_populates="hiring_request", cascade="all, delete-orphan", order_by="ApprovalStep.sequence_order"
    )
    approval_records: Mapped[list["ApprovalRecord"]] = relationship(
        back_populates="hiring_request", cascade="all, delete-orphan", order_by="ApprovalRecord.created_at"
    )


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    hiring_request_id: Mapped[str] = mapped_column(ForeignKey("hiring_requests.id"), nullable=False, index=True)
    position_index: Mapped[int] = mapped_column(Integer, nullable=False)
    position_code: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="REQUESTED"
    )  # REQUESTED | APPROVED | OPEN_RECRUITING | FILLED | CANCELLED
    target_hire_date: Mapped[date] = mapped_column(Date, nullable=False)

    hiring_request: Mapped["HiringRequest"] = relationship(back_populates="positions")
    outcome: Mapped["HiringOutcome | None"] = relationship(
        back_populates="position", uselist=False, cascade="all, delete-orphan"
    )


class HiringOutcome(Base):
    __tablename__ = "hiring_outcomes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    position_id: Mapped[str] = mapped_column(ForeignKey("positions.id"), unique=True, nullable=False)
    candidate_ref: Mapped[str] = mapped_column(String(64), nullable=False)  # Synthetic ID only
    actual_hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_annual_base_salary: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    actual_benefits_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    actual_recruitment_fee: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    actual_onetime_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    closure_status: Mapped[str] = mapped_column(String(32), nullable=False)  # HIRED | OFFER_DECLINED | CANCELLED
    closure_reason: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    position: Mapped["Position"] = relationship(back_populates="outcome")


class ApprovalRule(Base):
    __tablename__ = "approval_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    rule_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    min_grade: Mapped[str | None] = mapped_column(String(16), nullable=True)
    min_total_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    hiring_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    business_unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    location_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    requires_manager_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_finance_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_committee_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sla_hours: Mapped[int] = mapped_column(Integer, default=48, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    hiring_request_id: Mapped[str] = mapped_column(ForeignKey("hiring_requests.id"), nullable=False, index=True)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_name: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # MANAGER_REVIEW | FINANCE_REVIEW | COMMITTEE_PENDING
    required_role: Mapped[str] = mapped_column(String(32), nullable=False)
    assigned_approver_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    step_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING"
    )  # PENDING | ACTIVE | APPROVED | REJECTED | RETURNED
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    hiring_request: Mapped["HiringRequest"] = relationship(back_populates="approval_steps")


class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    hiring_request_id: Mapped[str] = mapped_column(ForeignKey("hiring_requests.id"), nullable=False, index=True)
    approval_step_id: Mapped[str] = mapped_column(ForeignKey("approval_steps.id"), nullable=False)
    approver_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    delegated_from_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    stage_name: Mapped[str] = mapped_column(String(32), nullable=False)
    decision: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # APPROVE | REJECT | REQUEST_CLARIFICATION | DELEGATE
    comments: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    hiring_request: Mapped["HiringRequest"] = relationship(back_populates="approval_records")


class ApprovalDelegation(Base):
    __tablename__ = "approval_delegations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    from_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    to_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    stage_name: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    recipient_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    recipient_role: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    hiring_request_id: Mapped[str] = mapped_column(ForeignKey("hiring_requests.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    previous_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


@event.listens_for(AuditEvent, "before_update")
def _block_audit_update(mapper, connection, target):
    raise PermissionError("Audit events are immutable and cannot be updated.")


@event.listens_for(AuditEvent, "before_delete")
def _block_audit_delete(mapper, connection, target):
    raise PermissionError("Audit events are immutable and cannot be deleted.")
