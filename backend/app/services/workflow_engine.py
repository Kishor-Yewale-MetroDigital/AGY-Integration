from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.rbac import verify_stage_permission
from app.config import settings
from app.models.entities import (
    ApprovalDelegation,
    ApprovalRecord,
    ApprovalRule,
    ApprovalStep,
    Budget,
    HiringRequest,
    User,
)
from app.schemas.domain import ApprovalDecisionRequest, ApprovalDelegationCreate
from app.services.audit_service import emit_notification, record_audit_event
from app.services.cost_service import FX_TO_INR, quantize_money

GRADE_RANK: dict[str, int] = {
    "L3": 3,
    "L4": 4,
    "L5": 5,
    "L6": 6,
    "L7": 7,
    "L8": 8,
    "EXEC": 9,
}

# Threshold above which Finance Review is required (INR 50,00,000 = 5,000,000.00)
DEFAULT_FINANCE_COST_THRESHOLD_INR = Decimal("5000000.00")


def evaluate_required_stages(db: Session, hiring_request: HiringRequest) -> tuple[list[tuple[str, str]], int]:
    """
    Evaluates active `ApprovalRule` records against the request's grade, total cost,
    hiring type, business unit, and country.
    Returns ordered list of (stage_name, required_role) and SLA hours.
    """
    rules = list(db.scalars(select(ApprovalRule).where(ApprovalRule.is_active.is_(True))).all())

    req_grade_rank = GRADE_RANK.get(hiring_request.job_grade, 3)
    fx = FX_TO_INR.get(hiring_request.currency, Decimal("1.00"))
    cost_in_inr = Decimal(hiring_request.total_annualized_forecast) * fx

    requires_manager = True
    requires_finance = False
    requires_committee = True
    sla_hours = settings.default_sla_hours

    # Built-in baseline enterprise policy: Senior grades (L6+) or high-cost (> 50L INR) require Finance Review
    if req_grade_rank >= GRADE_RANK["L6"] or cost_in_inr >= DEFAULT_FINANCE_COST_THRESHOLD_INR:
        requires_finance = True

    for rule in rules:
        matches = True
        if rule.min_grade and req_grade_rank < GRADE_RANK.get(rule.min_grade, 0):
            matches = False
        if rule.min_total_cost and cost_in_inr < Decimal(rule.min_total_cost):
            matches = False
        if rule.hiring_type and rule.hiring_type != hiring_request.hiring_type:
            matches = False
        if rule.business_unit and rule.business_unit != hiring_request.business_unit:
            matches = False
        if rule.location_country and rule.location_country != hiring_request.country:
            matches = False

        if matches:
            requires_manager = requires_manager or rule.requires_manager_review
            requires_finance = requires_finance or rule.requires_finance_review
            requires_committee = requires_committee or rule.requires_committee_review
            sla_hours = min(sla_hours, rule.sla_hours)

    stages: list[tuple[str, str]] = []
    if requires_manager:
        stages.append(("MANAGER_REVIEW", "HIRING_MANAGER"))
    if requires_finance:
        stages.append(("FINANCE_REVIEW", "FINANCE_REVIEWER"))
    if requires_committee:
        stages.append(("COMMITTEE_PENDING", "COMMITTEE_MEMBER"))

    return stages, sla_hours


def initialize_workflow_on_submit(
    db: Session,
    hiring_request: HiringRequest,
    actor: User,
) -> HiringRequest:
    if hiring_request.status not in {"DRAFT", "CLARIFICATION_REQUESTED"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit request from status '{hiring_request.status}'. Allowed: DRAFT, CLARIFICATION_REQUESTED.",
        )

    now = datetime.now(UTC)
    prev_status = hiring_request.status

    # Clear any prior pending/returned steps if resubmitting after clarification
    for existing_step in list(hiring_request.approval_steps):
        db.delete(existing_step)
    db.flush()

    stages, sla_hours = evaluate_required_stages(db, hiring_request)
    for idx, (stage_name, req_role) in enumerate(stages, start=1):
        is_first = idx == 1
        step = ApprovalStep(
            hiring_request_id=hiring_request.id,
            sequence_order=idx,
            stage_name=stage_name,
            required_role=req_role,
            step_status="ACTIVE" if is_first else "PENDING",
            due_at=(now + timedelta(hours=sla_hours)) if is_first else None,
        )
        db.add(step)

    first_stage = stages[0][0]
    hiring_request.status = first_stage
    hiring_request.submitted_at = now
    hiring_request.updated_at = now

    record_audit_event(
        db,
        entity_type="HiringRequest",
        entity_id=hiring_request.id,
        actor=actor,
        action="SUBMIT_REQUEST",
        previous_state={"status": prev_status},
        new_state={
            "status": hiring_request.status,
            "configured_stages": [s[0] for s in stages],
            "total_annualized_forecast": hiring_request.total_annualized_forecast,
        },
    )

    emit_notification(
        db,
        recipient_role=stages[0][1],
        hiring_request_id=hiring_request.id,
        event_type="REQUEST_SUBMITTED",
        message=f"Hiring request {hiring_request.request_code} ({hiring_request.job_title}) is awaiting {first_stage}.",
    )

    db.commit()
    db.refresh(hiring_request)
    return hiring_request


def process_approval_decision(
    db: Session,
    *,
    hiring_request: HiringRequest,
    decision_req: ApprovalDecisionRequest,
    actor: User,
    target_stage: str | None = None,
) -> HiringRequest:
    """
    Processes an approval, rejection, or clarification decision on the currently active workflow step.
    Strictly enforces stage order (cannot skip Finance Review), RBAC, Segregation of Duties,
    and duplicate action prevention.
    """
    active_step = next((s for s in hiring_request.approval_steps if s.step_status == "ACTIVE"), None)
    if not active_step:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Request '{hiring_request.request_code}' has no active approval step (current status: {hiring_request.status}). Duplicate or out-of-turn action prevented.",
        )

    if target_stage and target_stage != active_step.stage_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stage sequence violation: Cannot act on stage '{target_stage}' while request is in '{active_step.stage_name}'. Mandatory stages cannot be skipped.",
        )

    # Check if this actor already recorded a decision on this active step instance
    duplicate_record = db.scalar(
        select(ApprovalRecord).where(
            ApprovalRecord.approval_step_id == active_step.id,
            ApprovalRecord.approver_id == actor.id,
        )
    )
    if duplicate_record:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate approval action prevented: You have already acted on this approval step.",
        )

    delegated_from_id = verify_stage_permission(db, actor, hiring_request, active_step.stage_name)

    now = datetime.now(UTC)
    prev_status = hiring_request.status

    record = ApprovalRecord(
        hiring_request_id=hiring_request.id,
        approval_step_id=active_step.id,
        approver_id=actor.id,
        delegated_from_id=delegated_from_id,
        stage_name=active_step.stage_name,
        decision=decision_req.decision,
        comments=decision_req.comments.strip() or "Approved in accordance with workforce plan.",
        created_at=now,
    )
    db.add(record)

    active_step.completed_at = now

    if decision_req.decision == "APPROVE":
        active_step.step_status = "APPROVED"
        next_step = next(
            (
                s
                for s in hiring_request.approval_steps
                if s.sequence_order > active_step.sequence_order and s.step_status == "PENDING"
            ),
            None,
        )
        if next_step:
            next_step.step_status = "ACTIVE"
            next_step.due_at = now + timedelta(hours=settings.default_sla_hours)
            hiring_request.status = next_step.stage_name
            emit_notification(
                db,
                recipient_role=next_step.required_role,
                hiring_request_id=hiring_request.id,
                event_type="STAGE_ADVANCED",
                message=f"Request {hiring_request.request_code} advanced to {next_step.stage_name}.",
            )
        else:
            # Final People Committee approval achieved!
            hiring_request.status = "APPROVED"
            hiring_request.approved_at = now
            for pos in hiring_request.positions:
                pos.status = "APPROVED"

            # Commit budget allocation on department budget
            budget = db.scalar(
                select(Budget).where(Budget.department_id == hiring_request.department_id)
            )
            if budget:
                budget.committed_cost = quantize_money(
                    Decimal(budget.committed_cost) + Decimal(hiring_request.total_annualized_forecast)
                )

            emit_notification(
                db,
                recipient_role="REQUEST_CREATOR",
                recipient_user_id=hiring_request.request_owner_id,
                hiring_request_id=hiring_request.id,
                event_type="REQUEST_APPROVED",
                message=f"Hiring request {hiring_request.request_code} has been APPROVED by the People Committee.",
            )

    elif decision_req.decision == "REJECT":
        active_step.step_status = "REJECTED"
        hiring_request.status = "REJECTED"
        hiring_request.closed_at = now
        for pos in hiring_request.positions:
            pos.status = "CANCELLED"

        emit_notification(
            db,
            recipient_role="REQUEST_CREATOR",
            recipient_user_id=hiring_request.request_owner_id,
            hiring_request_id=hiring_request.id,
            event_type="REQUEST_REJECTED",
            message=f"Hiring request {hiring_request.request_code} was REJECTED at {active_step.stage_name}: {decision_req.comments}",
        )

    elif decision_req.decision == "REQUEST_CLARIFICATION":
        active_step.step_status = "RETURNED"
        hiring_request.status = "CLARIFICATION_REQUESTED"
        emit_notification(
            db,
            recipient_role="REQUEST_CREATOR",
            recipient_user_id=hiring_request.request_owner_id,
            hiring_request_id=hiring_request.id,
            event_type="CLARIFICATION_REQUESTED",
            message=f"Clarification requested on {hiring_request.request_code} at {active_step.stage_name}: {decision_req.comments}",
        )

    hiring_request.updated_at = now

    record_audit_event(
        db,
        entity_type="HiringRequest",
        entity_id=hiring_request.id,
        actor=actor,
        action=f"WORKFLOW_{decision_req.decision}",
        previous_state={"status": prev_status, "stage": active_step.stage_name},
        new_state={
            "status": hiring_request.status,
            "stage": active_step.stage_name,
            "decision": decision_req.decision,
            "comments": decision_req.comments,
            "delegated_from_id": delegated_from_id,
        },
    )

    db.commit()
    db.refresh(hiring_request)
    return hiring_request


def create_delegation(
    db: Session,
    *,
    payload: ApprovalDelegationCreate,
    actor: User,
) -> ApprovalDelegation:
    target_user = db.get(User, payload.to_user_id)
    if not target_user or not target_user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delegate target user not found.")

    delegation = ApprovalDelegation(
        from_user_id=actor.id,
        to_user_id=payload.to_user_id,
        stage_name=payload.stage_name,
        reason=payload.reason,
        is_active=True,
    )
    db.add(delegation)
    db.flush()
    record_audit_event(
        db,
        entity_type="ApprovalDelegation",
        entity_id=delegation.id,
        actor=actor,
        action="CREATE_DELEGATION",
        previous_state=None,
        new_state={
            "from_user_id": actor.id,
            "to_user_id": payload.to_user_id,
            "stage_name": payload.stage_name,
            "reason": payload.reason,
        },
    )
    db.commit()
    db.refresh(delegation)
    return delegation
