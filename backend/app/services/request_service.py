from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Budget, Department, HiringOutcome, HiringRequest, Position, User
from app.schemas.domain import HiringOutcomeCreate, HiringRequestCreate, HiringRequestUpdate
from app.services.audit_service import record_audit_event
from app.services.cost_service import (
    calculate_in_period_expenditure,
    calculate_request_annualized_forecast,
    quantize_money,
)


def _next_request_code(db: Session) -> str:
    codes = list(db.scalars(select(HiringRequest.request_code)).all())
    max_num = len(codes)
    for code in codes:
        if code and "-" in code:
            suffix = code.rsplit("-", 1)[-1]
            if suffix.isdigit():
                max_num = max(max_num, int(suffix))
    return f"REQ-2026-{max_num + 1:04d}"


def create_hiring_request(
    db: Session,
    *,
    payload: HiringRequestCreate,
    actor: User,
) -> HiringRequest:
    dept = db.get(Department, payload.department_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")

    total_forecast = calculate_request_annualized_forecast(
        est_annual_salary_per_pos=payload.est_annual_salary_per_pos,
        est_benefits_cost_per_pos=payload.est_benefits_cost_per_pos,
        est_recruitment_fee_per_pos=payload.est_recruitment_fee_per_pos,
        est_onetime_cost_per_pos=payload.est_onetime_cost_per_pos,
        headcount_requested=payload.headcount_requested,
    )

    req_code = _next_request_code(db)
    req = HiringRequest(
        request_code=req_code,
        job_title=payload.job_title,
        job_family=payload.job_family,
        department_id=payload.department_id,
        business_unit=payload.business_unit,
        country=payload.country,
        city=payload.city,
        work_location=payload.work_location,
        job_grade=payload.job_grade,
        employment_type=payload.employment_type,
        hiring_manager_id=payload.hiring_manager_id,
        request_owner_id=payload.request_owner_id or actor.id,
        hiring_type=payload.hiring_type,
        headcount_requested=payload.headcount_requested,
        justification=payload.justification,
        expected_business_impact=payload.expected_business_impact,
        requested_start_date=payload.requested_start_date,
        target_hiring_date=payload.target_hiring_date,
        currency=payload.currency,
        est_annual_salary_per_pos=payload.est_annual_salary_per_pos,
        est_benefits_cost_per_pos=payload.est_benefits_cost_per_pos,
        est_recruitment_fee_per_pos=payload.est_recruitment_fee_per_pos,
        est_onetime_cost_per_pos=payload.est_onetime_cost_per_pos,
        total_annualized_forecast=total_forecast,
        status="DRAFT",
    )
    db.add(req)
    db.flush()

    for idx in range(1, payload.headcount_requested + 1):
        pos = Position(
            hiring_request_id=req.id,
            position_index=idx,
            position_code=f"{req_code}-P{idx:02d}",
            status="REQUESTED",
            target_hire_date=payload.target_hiring_date,
        )
        db.add(pos)

    record_audit_event(
        db,
        entity_type="HiringRequest",
        entity_id=req.id,
        actor=actor,
        action="CREATE_REQUEST",
        previous_state=None,
        new_state={
            "request_code": req.request_code,
            "job_title": req.job_title,
            "headcount_requested": req.headcount_requested,
            "total_annualized_forecast": req.total_annualized_forecast,
            "status": req.status,
        },
    )

    db.commit()
    db.refresh(req)
    return req


def update_hiring_request(
    db: Session,
    *,
    hiring_request: HiringRequest,
    payload: HiringRequestUpdate,
    actor: User,
) -> HiringRequest:
    if hiring_request.status not in {"DRAFT", "CLARIFICATION_REQUESTED"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot edit request in status '{hiring_request.status}'. Only DRAFT or CLARIFICATION_REQUESTED requests can be edited.",
        )

    updates = payload.model_dump(exclude_unset=True)
    prev_snapshot = {k: getattr(hiring_request, k) for k in updates}

    for field, value in updates.items():
        setattr(hiring_request, field, value)

    if hiring_request.requested_start_date < hiring_request.target_hiring_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="requested_start_date must be on or after target_hiring_date.",
        )

    hiring_request.total_annualized_forecast = calculate_request_annualized_forecast(
        est_annual_salary_per_pos=hiring_request.est_annual_salary_per_pos,
        est_benefits_cost_per_pos=hiring_request.est_benefits_cost_per_pos,
        est_recruitment_fee_per_pos=hiring_request.est_recruitment_fee_per_pos,
        est_onetime_cost_per_pos=hiring_request.est_onetime_cost_per_pos,
        headcount_requested=hiring_request.headcount_requested,
    )

    # Reconcile positions if headcount_requested changed
    current_count = len(hiring_request.positions)
    if hiring_request.headcount_requested > current_count:
        for idx in range(current_count + 1, hiring_request.headcount_requested + 1):
            db.add(
                Position(
                    hiring_request_id=hiring_request.id,
                    position_index=idx,
                    position_code=f"{hiring_request.request_code}-P{idx:02d}",
                    status="REQUESTED",
                    target_hire_date=hiring_request.target_hiring_date,
                )
            )
    elif hiring_request.headcount_requested < current_count:
        for pos in sorted(hiring_request.positions, key=lambda p: p.position_index, reverse=True)[
            : current_count - hiring_request.headcount_requested
        ]:
            db.delete(pos)

    hiring_request.updated_at = datetime.now(UTC)

    record_audit_event(
        db,
        entity_type="HiringRequest",
        entity_id=hiring_request.id,
        actor=actor,
        action="UPDATE_REQUEST",
        previous_state=prev_snapshot,
        new_state={
            **updates,
            "total_annualized_forecast": hiring_request.total_annualized_forecast,
        },
    )

    db.commit()
    db.refresh(hiring_request)
    return hiring_request


def record_position_outcome(
    db: Session,
    *,
    hiring_request: HiringRequest,
    position_id: str,
    payload: HiringOutcomeCreate,
    actor: User,
) -> HiringRequest:
    if hiring_request.status not in {"APPROVED", "RECRUITING", "PARTIALLY_FILLED"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot record hiring outcomes when request status is '{hiring_request.status}'. Request must be APPROVED first.",
        )

    pos = next((p for p in hiring_request.positions if p.id == position_id), None)
    if not pos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found on request.")
    if pos.outcome is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Outcome already recorded for this position.")

    actual_benefits = (
        Decimal(payload.actual_benefits_cost)
        if Decimal(payload.actual_benefits_cost) > Decimal("0.00") or payload.closure_status != "HIRED"
        else Decimal(hiring_request.est_benefits_cost_per_pos)
    )
    actual_fee = (
        Decimal(payload.actual_recruitment_fee)
        if Decimal(payload.actual_recruitment_fee) > Decimal("0.00") or payload.closure_status != "HIRED"
        else Decimal(hiring_request.est_recruitment_fee_per_pos)
    )
    actual_onetime = (
        Decimal(payload.actual_onetime_cost)
        if Decimal(payload.actual_onetime_cost) > Decimal("0.00") or payload.closure_status != "HIRED"
        else Decimal(hiring_request.est_onetime_cost_per_pos)
    )

    outcome = HiringOutcome(
        position_id=pos.id,
        candidate_ref=payload.candidate_ref,
        actual_hire_date=payload.actual_hire_date,
        actual_annual_base_salary=payload.actual_annual_base_salary,
        actual_benefits_cost=actual_benefits,
        actual_recruitment_fee=actual_fee,
        actual_onetime_cost=actual_onetime,
        closure_status=payload.closure_status,
        closure_reason=payload.closure_reason,
    )
    db.add(outcome)

    if payload.closure_status == "HIRED":
        pos.status = "FILLED"
        budget = db.scalar(select(Budget).where(Budget.department_id == hiring_request.department_id))
        if budget:
            actual_cost = (
                Decimal(payload.actual_annual_base_salary)
                + actual_benefits
                + actual_fee
                + actual_onetime
            )
            budget.actual_spent = quantize_money(Decimal(budget.actual_spent) + actual_cost)
    else:
        pos.status = "CANCELLED"

    db.flush()

    filled_count = sum(1 for p in hiring_request.positions if p.status == "FILLED")
    open_count = sum(1 for p in hiring_request.positions if p.status in {"APPROVED", "OPEN_RECRUITING"})

    prev_status = hiring_request.status
    if open_count == 0 and filled_count > 0:
        hiring_request.status = "FILLED"
        hiring_request.closed_at = datetime.now(UTC)
    elif filled_count > 0:
        hiring_request.status = "PARTIALLY_FILLED"
    elif open_count == 0:
        hiring_request.status = "CANCELLED"
        hiring_request.closed_at = datetime.now(UTC)
    else:
        hiring_request.status = "RECRUITING"

    record_audit_event(
        db,
        entity_type="HiringRequest",
        entity_id=hiring_request.id,
        actor=actor,
        action="RECORD_POSITION_OUTCOME",
        previous_state={"status": prev_status, "position_id": pos.id},
        new_state={
            "status": hiring_request.status,
            "position_id": pos.id,
            "closure_status": payload.closure_status,
            "actual_annual_base_salary": payload.actual_annual_base_salary,
        },
    )

    db.commit()
    db.refresh(hiring_request)
    return hiring_request


def serialize_hiring_request(req: HiringRequest) -> dict:
    now = datetime.now(UTC)
    in_period = calculate_in_period_expenditure(
        est_annual_salary_per_pos=req.est_annual_salary_per_pos,
        est_benefits_cost_per_pos=req.est_benefits_cost_per_pos,
        est_recruitment_fee_per_pos=req.est_recruitment_fee_per_pos,
        est_onetime_cost_per_pos=req.est_onetime_cost_per_pos,
        headcount_requested=req.headcount_requested,
        start_date=req.requested_start_date,
    )

    steps = []
    for s in req.approval_steps:
        due = s.due_at
        if due and due.tzinfo is None:
            due = due.replace(tzinfo=UTC)
        is_overdue = bool(s.step_status == "ACTIVE" and due and now > due)
        steps.append(
            {
                "id": s.id,
                "sequence_order": s.sequence_order,
                "stage_name": s.stage_name,
                "required_role": s.required_role,
                "step_status": s.step_status,
                "due_at": s.due_at,
                "completed_at": s.completed_at,
                "is_overdue": is_overdue,
            }
        )

    positions = []
    for p in req.positions:
        outcome_dict = None
        if p.outcome:
            outcome_dict = {
                "id": p.outcome.id,
                "candidate_ref": p.outcome.candidate_ref,
                "actual_hire_date": p.outcome.actual_hire_date.isoformat(),
                "actual_annual_base_salary": str(p.outcome.actual_annual_base_salary),
                "actual_benefits_cost": str(p.outcome.actual_benefits_cost),
                "actual_recruitment_fee": str(p.outcome.actual_recruitment_fee),
                "actual_onetime_cost": str(p.outcome.actual_onetime_cost),
                "closure_status": p.outcome.closure_status,
                "closure_reason": p.outcome.closure_reason,
            }
        positions.append(
            {
                "id": p.id,
                "position_index": p.position_index,
                "position_code": p.position_code,
                "status": p.status,
                "target_hire_date": p.target_hire_date,
                "outcome": outcome_dict,
            }
        )

    return {
        "id": req.id,
        "request_code": req.request_code,
        "job_title": req.job_title,
        "job_family": req.job_family,
        "department_id": req.department_id,
        "business_unit": req.business_unit,
        "country": req.country,
        "city": req.city,
        "work_location": req.work_location,
        "job_grade": req.job_grade,
        "employment_type": req.employment_type,
        "hiring_manager_id": req.hiring_manager_id,
        "request_owner_id": req.request_owner_id,
        "hiring_type": req.hiring_type,
        "headcount_requested": req.headcount_requested,
        "justification": req.justification,
        "expected_business_impact": req.expected_business_impact,
        "requested_start_date": req.requested_start_date,
        "target_hiring_date": req.target_hiring_date,
        "currency": req.currency,
        "est_annual_salary_per_pos": req.est_annual_salary_per_pos,
        "est_benefits_cost_per_pos": req.est_benefits_cost_per_pos,
        "est_recruitment_fee_per_pos": req.est_recruitment_fee_per_pos,
        "est_onetime_cost_per_pos": req.est_onetime_cost_per_pos,
        "total_annualized_forecast": req.total_annualized_forecast,
        "in_period_projected_cost": in_period,
        "status": req.status,
        "submitted_at": req.submitted_at,
        "approved_at": req.approved_at,
        "closed_at": req.closed_at,
        "created_at": req.created_at,
        "updated_at": req.updated_at,
        "positions": positions,
        "approval_steps": steps,
        "approval_records": [
            {
                "id": r.id,
                "approval_step_id": r.approval_step_id,
                "approver_id": r.approver_id,
                "delegated_from_id": r.delegated_from_id,
                "stage_name": r.stage_name,
                "decision": r.decision,
                "comments": r.comments,
                "created_at": r.created_at,
            }
            for r in req.approval_records
        ],
    }
