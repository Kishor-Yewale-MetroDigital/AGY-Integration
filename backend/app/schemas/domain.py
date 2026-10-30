from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class HiringRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_title: str = Field(..., min_length=3, max_length=128)
    job_family: str = Field(..., min_length=2, max_length=64)
    department_id: str = Field(..., min_length=1)
    business_unit: str = Field(..., min_length=2, max_length=64)
    country: str = Field(..., min_length=2, max_length=64)
    city: str = Field(..., min_length=2, max_length=64)
    work_location: Literal["ONSITE", "HYBRID", "REMOTE"]
    job_grade: Literal["L3", "L4", "L5", "L6", "L7", "L8", "EXEC"]
    employment_type: Literal["FULL_TIME", "CONTRACT", "PART_TIME"]
    hiring_manager_id: str = Field(..., min_length=1)
    request_owner_id: str | None = Field(default=None, min_length=1)
    hiring_type: Literal["NEW_HEADCOUNT", "REPLACEMENT"]
    headcount_requested: int = Field(..., ge=1, le=50)
    justification: str = Field(..., min_length=15)
    expected_business_impact: str = Field(..., min_length=10)
    requested_start_date: date
    target_hiring_date: date
    currency: Literal["INR", "EUR", "USD"] = "INR"
    est_annual_salary_per_pos: Decimal = Field(..., gt=Decimal("0"))
    est_benefits_cost_per_pos: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    est_recruitment_fee_per_pos: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    est_onetime_cost_per_pos: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))

    @model_validator(mode="after")
    def validate_dates(self) -> "HiringRequestCreate":
        if self.requested_start_date < self.target_hiring_date:
            raise ValueError("requested_start_date must be on or after target_hiring_date")
        return self


class HiringRequestUpdate(BaseModel):
    """
    Explicitly forbids `status` modification to prevent bypassing the People Committee workflow.
    """

    model_config = ConfigDict(extra="forbid")

    job_title: str | None = Field(default=None, min_length=3, max_length=128)
    job_family: str | None = Field(default=None, min_length=2, max_length=64)
    country: str | None = Field(default=None, min_length=2, max_length=64)
    city: str | None = Field(default=None, min_length=2, max_length=64)
    work_location: Literal["ONSITE", "HYBRID", "REMOTE"] | None = None
    job_grade: Literal["L3", "L4", "L5", "L6", "L7", "L8", "EXEC"] | None = None
    employment_type: Literal["FULL_TIME", "CONTRACT", "PART_TIME"] | None = None
    hiring_type: Literal["NEW_HEADCOUNT", "REPLACEMENT"] | None = None
    headcount_requested: int | None = Field(default=None, ge=1, le=50)
    justification: str | None = Field(default=None, min_length=15)
    expected_business_impact: str | None = Field(default=None, min_length=10)
    requested_start_date: date | None = None
    target_hiring_date: date | None = None
    est_annual_salary_per_pos: Decimal | None = Field(default=None, gt=Decimal("0"))
    est_benefits_cost_per_pos: Decimal | None = Field(default=None, ge=Decimal("0"))
    est_recruitment_fee_per_pos: Decimal | None = Field(default=None, ge=Decimal("0"))
    est_onetime_cost_per_pos: Decimal | None = Field(default=None, ge=Decimal("0"))


class ApprovalDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["APPROVE", "REJECT", "REQUEST_CLARIFICATION"]
    comments: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def require_comments_for_negative_decisions(self) -> "ApprovalDecisionRequest":
        if self.decision in {"REJECT", "REQUEST_CLARIFICATION"} and len(self.comments.strip()) < 5:
            raise ValueError(
                f"A detailed reason/comment (minimum 5 characters) is mandatory when decision is {self.decision}."
            )
        return self


class ApprovalDelegationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    to_user_id: str = Field(..., min_length=1)
    stage_name: Literal["MANAGER_REVIEW", "FINANCE_REVIEW", "COMMITTEE_PENDING"]
    reason: str = Field(..., min_length=5, max_length=500)


class ApprovalRuleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_name: str = Field(..., min_length=3, max_length=128)
    min_grade: Literal["L3", "L4", "L5", "L6", "L7", "L8", "EXEC"] | None = None
    min_total_cost: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    hiring_type: Literal["NEW_HEADCOUNT", "REPLACEMENT"] | None = None
    business_unit: str | None = None
    location_country: str | None = None
    requires_manager_review: bool = True
    requires_finance_review: bool = False
    requires_committee_review: bool = True
    sla_hours: int = Field(default=48, ge=1, le=720)


class HiringOutcomeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_ref: str = Field(..., min_length=3, max_length=64, description="Synthetic candidate ID only")
    actual_hire_date: date
    actual_annual_base_salary: Decimal = Field(..., ge=Decimal("0"))
    actual_benefits_cost: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    actual_recruitment_fee: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    actual_onetime_cost: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    closure_status: Literal["HIRED", "OFFER_DECLINED", "CANCELLED"]
    closure_reason: str = Field(..., min_length=5)

    @field_validator("candidate_ref")
    @classmethod
    def enforce_synthetic_candidate_ref(cls, v: str) -> str:
        if "@" in v or " " in v.strip():
            raise ValueError("candidate_ref must be a synthetic reference code (e.g. CAND-SYN-001), not personal PII.")
        return v.strip()


class PositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    position_index: int
    position_code: str
    status: str
    target_hire_date: date
    outcome: dict | None = None


class ApprovalStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sequence_order: int
    stage_name: str
    required_role: str
    step_status: str
    due_at: datetime | None
    completed_at: datetime | None
    is_overdue: bool = False


class ApprovalRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    approval_step_id: str
    approver_id: str
    delegated_from_id: str | None
    stage_name: str
    decision: str
    comments: str
    created_at: datetime


class HiringRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    request_code: str
    job_title: str
    job_family: str
    department_id: str
    business_unit: str
    country: str
    city: str
    work_location: str
    job_grade: str
    employment_type: str
    hiring_manager_id: str
    request_owner_id: str
    hiring_type: str
    headcount_requested: int
    justification: str
    expected_business_impact: str
    requested_start_date: date
    target_hiring_date: date
    currency: str
    est_annual_salary_per_pos: Decimal
    est_benefits_cost_per_pos: Decimal
    est_recruitment_fee_per_pos: Decimal
    est_onetime_cost_per_pos: Decimal
    total_annualized_forecast: Decimal
    in_period_projected_cost: Decimal
    status: str
    submitted_at: datetime | None
    approved_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    positions: list[PositionResponse] = []
    approval_steps: list[ApprovalStepResponse] = []
    approval_records: list[ApprovalRecordResponse] = []
