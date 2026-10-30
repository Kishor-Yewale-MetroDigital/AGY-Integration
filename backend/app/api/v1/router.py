from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.rbac import Role, get_current_user, require_roles
from app.database import get_db
from app.models.entities import (
    ApprovalDelegation,
    ApprovalRule,
    AuditEvent,
    Budget,
    Department,
    HiringRequest,
    Notification,
    User,
)
from app.schemas.domain import (
    ApprovalDecisionRequest,
    ApprovalDelegationCreate,
    ApprovalRuleCreate,
    HiringOutcomeCreate,
    HiringRequestCreate,
    HiringRequestResponse,
    HiringRequestUpdate,
)
from app.seed import populate_interactive_approval_queue
from app.services.audit_service import record_audit_event
from app.services.bigquery_service import bq_warehouse
from app.services.cost_service import (
    calculate_cost_of_delayed_hiring,
    compute_workforce_and_cost_summary,
)
from app.services.request_service import (
    create_hiring_request,
    record_position_outcome,
    serialize_hiring_request,
    update_hiring_request,
)
from app.services.workflow_engine import (
    create_delegation,
    initialize_workflow_on_submit,
    process_approval_decision,
)

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = list(db.scalars(select(User).order_by(User.full_name)).all())
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "business_unit": u.business_unit,
            "department_id": u.department_id,
        }
        for u in users
    ]


@api_router.get("/departments")
def list_departments(db: Session = Depends(get_db)):
    depts = list(db.scalars(select(Department).order_by(Department.code)).all())
    budgets = {b.department_id: b for b in db.scalars(select(Budget)).all()}
    result = []
    for d in depts:
        b = budgets.get(d.id)
        result.append(
            {
                "id": d.id,
                "code": d.code,
                "name": d.name,
                "business_unit": d.business_unit,
                "cost_center": d.cost_center,
                "allocated_budget": str(b.allocated_budget) if b else "0.00",
                "committed_cost": str(b.committed_cost) if b else "0.00",
                "actual_spent": str(b.actual_spent) if b else "0.00",
                "currency": b.currency if b else "INR",
            }
        )
    return result


@api_router.get("/requests", response_model=list[HiringRequestResponse])
def list_hiring_requests(
    status_filter: str | None = Query(default=None, alias="status"),
    department_id: str | None = None,
    business_unit: str | None = None,
    country: str | None = None,
    work_location: str | None = None,
    job_grade: str | None = None,
    hiring_type: str | None = None,
    search: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(HiringRequest).order_by(HiringRequest.created_at.desc())
    if status_filter:
        stmt = stmt.where(HiringRequest.status == status_filter)
    if department_id:
        stmt = stmt.where(HiringRequest.department_id == department_id)
    if business_unit:
        stmt = stmt.where(HiringRequest.business_unit == business_unit)
    if country:
        stmt = stmt.where(HiringRequest.country == country)
    if work_location:
        stmt = stmt.where(HiringRequest.work_location == work_location)
    if job_grade:
        stmt = stmt.where(HiringRequest.job_grade == job_grade)
    if hiring_type:
        stmt = stmt.where(HiringRequest.hiring_type == hiring_type)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            HiringRequest.job_title.ilike(pattern) | HiringRequest.request_code.ilike(pattern)
        )

    requests = list(db.scalars(stmt.offset(offset).limit(limit)).unique().all())
    return [serialize_hiring_request(r) for r in requests]


@api_router.get("/requests/{request_id}", response_model=HiringRequestResponse)
def get_hiring_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = db.get(HiringRequest, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hiring request not found.")
    return serialize_hiring_request(req)


@api_router.post(
    "/requests",
    response_model=HiringRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_request_endpoint(
    payload: HiringRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            Role.REQUEST_CREATOR,
            Role.HIRING_MANAGER,
            Role.HRBP,
            Role.FINANCE_REVIEWER,
            Role.COMMITTEE_MEMBER,
            Role.ADMIN,
        )
    ),
):
    req = create_hiring_request(db, payload=payload, actor=current_user)
    return serialize_hiring_request(req)


@api_router.patch("/requests/{request_id}", response_model=HiringRequestResponse)
def update_request_endpoint(
    request_id: str,
    payload: HiringRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            Role.REQUEST_CREATOR,
            Role.HIRING_MANAGER,
            Role.HRBP,
            Role.FINANCE_REVIEWER,
            Role.COMMITTEE_MEMBER,
            Role.ADMIN,
        )
    ),
):
    req = db.get(HiringRequest, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hiring request not found.")
    updated = update_hiring_request(db, hiring_request=req, payload=payload, actor=current_user)
    return serialize_hiring_request(updated)


@api_router.post("/requests/{request_id}/submit", response_model=HiringRequestResponse)
def submit_request_endpoint(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            Role.REQUEST_CREATOR,
            Role.HIRING_MANAGER,
            Role.HRBP,
            Role.FINANCE_REVIEWER,
            Role.COMMITTEE_MEMBER,
            Role.ADMIN,
        )
    ),
):
    req = db.get(HiringRequest, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hiring request not found.")
    submitted = initialize_workflow_on_submit(db, req, current_user)
    return serialize_hiring_request(submitted)


@api_router.post("/requests/{request_id}/decisions", response_model=HiringRequestResponse)
def submit_approval_decision_endpoint(
    request_id: str,
    payload: ApprovalDecisionRequest,
    target_stage: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = db.get(HiringRequest, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hiring request not found.")
    updated = process_approval_decision(
        db,
        hiring_request=req,
        decision_req=payload,
        actor=current_user,
        target_stage=target_stage,
    )
    return serialize_hiring_request(updated)


@api_router.post(
    "/requests/{request_id}/positions/{position_id}/outcome",
    response_model=HiringRequestResponse,
)
def record_outcome_endpoint(
    request_id: str,
    position_id: str,
    payload: HiringOutcomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            Role.REQUEST_CREATOR,
            Role.HRBP,
            Role.HIRING_MANAGER,
            Role.FINANCE_REVIEWER,
            Role.COMMITTEE_MEMBER,
            Role.ADMIN,
        )
    ),
):
    req = db.get(HiringRequest, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hiring request not found.")
    updated = record_position_outcome(
        db,
        hiring_request=req,
        position_id=position_id,
        payload=payload,
        actor=current_user,
    )
    return serialize_hiring_request(updated)


@api_router.get("/approvals/delegations")
def list_delegations_endpoint(db: Session = Depends(get_db)):
    delegations = list(db.scalars(select(ApprovalDelegation)).all())
    return [
        {
            "id": d.id,
            "from_user_id": d.from_user_id,
            "to_user_id": d.to_user_id,
            "stage_name": d.stage_name,
            "reason": d.reason,
            "is_active": d.is_active,
        }
        for d in delegations
    ]


@api_router.post("/demo/populate-queue")
def populate_demo_queue_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = populate_interactive_approval_queue(db)
    bq_warehouse.run_incremental_merge_sync(db)
    return result


@api_router.post("/approvals/delegations", status_code=status.HTTP_201_CREATED)
def create_delegation_endpoint(
    payload: ApprovalDelegationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(Role.HIRING_MANAGER, Role.HRBP, Role.FINANCE_REVIEWER, Role.COMMITTEE_MEMBER, Role.ADMIN)
    ),
):
    delegation = create_delegation(db, payload=payload, actor=current_user)
    return {
        "id": delegation.id,
        "from_user_id": delegation.from_user_id,
        "to_user_id": delegation.to_user_id,
        "stage_name": delegation.stage_name,
        "reason": delegation.reason,
        "is_active": delegation.is_active,
    }


@api_router.get("/approvals/rules")
def list_approval_rules(db: Session = Depends(get_db)):
    rules = list(db.scalars(select(ApprovalRule)).all())
    return [
        {
            "id": r.id,
            "rule_name": r.rule_name,
            "min_grade": r.min_grade,
            "min_total_cost": str(r.min_total_cost),
            "hiring_type": r.hiring_type,
            "business_unit": r.business_unit,
            "location_country": r.location_country,
            "requires_manager_review": r.requires_manager_review,
            "requires_finance_review": r.requires_finance_review,
            "requires_committee_review": r.requires_committee_review,
            "sla_hours": r.sla_hours,
        }
        for r in rules
    ]


@api_router.post("/approvals/rules", status_code=status.HTTP_201_CREATED)
def create_approval_rule(
    payload: ApprovalRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(Role.ADMIN, Role.COMMITTEE_MEMBER, Role.FINANCE_REVIEWER, Role.HRBP)
    ),
):
    rule = ApprovalRule(**payload.model_dump())
    db.add(rule)
    db.flush()
    record_audit_event(
        db,
        entity_type="ApprovalRule",
        entity_id=rule.id,
        actor=current_user,
        action="CREATE_APPROVAL_RULE",
        previous_state=None,
        new_state=payload.model_dump(),
    )
    db.commit()
    db.refresh(rule)
    return {"id": rule.id, "rule_name": rule.rule_name}


@api_router.get("/workforce/summary")
def get_workforce_cost_summary(
    department_id: str | None = None,
    business_unit: str | None = None,
    job_grade: str | None = None,
    country: str | None = None,
    hiring_type: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    delay_days: int = Query(default=30, ge=0, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    summary = compute_workforce_and_cost_summary(
        db,
        department_id=department_id,
        business_unit=business_unit,
        job_grade=job_grade,
        country=country,
        hiring_type=hiring_type,
        status=status_filter,
    )
    delay_impact = calculate_cost_of_delayed_hiring(
        est_annual_salary_per_pos=Decimal("2800000.00"),
        open_positions_count=summary["open_approved_positions"],
        delay_days=delay_days,
    )
    return {
        **{k: str(v) if isinstance(v, Decimal) else v for k, v in summary.items()},
        "delay_cost_projection": {k: str(v) for k, v in delay_impact.items()},
    }


@api_router.get("/dashboard/overview")
def get_executive_dashboard(
    business_unit: str | None = None,
    department_id: str | None = None,
    country: str | None = None,
    job_grade: str | None = None,
    hiring_type: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns both Live Operational Metrics (from Cloud SQL PostgreSQL) and
    Curated Historical Analytics (from `talentflow_analytics` BigQuery warehouse)
    with SLA overdue escalation counts.
    """
    bq_warehouse.run_incremental_merge_sync(db)
    bq_analytics = bq_warehouse.query_curated_analytics(
        db,
        business_unit=business_unit,
        department_id=department_id,
        country=country,
        job_grade=job_grade,
        hiring_type=hiring_type,
        status=status_filter,
    )
    workforce = compute_workforce_and_cost_summary(
        db,
        department_id=department_id,
        business_unit=business_unit,
        job_grade=job_grade,
        country=country,
        hiring_type=hiring_type,
        status=status_filter,
    )

    # Calculate overdue SLA requests in live operational DB
    now = datetime.now(UTC)
    all_reqs = list(db.scalars(select(HiringRequest)).unique().all())
    overdue_sla_count = 0
    for r in all_reqs:
        for s in r.approval_steps:
            due = s.due_at
            if due and due.tzinfo is None:
                due = due.replace(tzinfo=UTC)
            if s.step_status == "ACTIVE" and due and now > due:
                overdue_sla_count += 1

    return {
        "live_operational_metrics": {
            "source": "Cloud SQL for PostgreSQL (Transactional SoT)",
            "overdue_sla_requests": overdue_sla_count,
            "workforce_and_cost": {
                k: str(v) if isinstance(v, Decimal) else v for k, v in workforce.items()
            },
        },
        "bigquery_historical_analytics": bq_analytics,
    }


@api_router.post("/analytics/sync")
def trigger_bigquery_sync(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return bq_warehouse.run_incremental_merge_sync(db)


@api_router.get("/analytics/bigquery")
def get_bigquery_analytics(
    business_unit: str | None = None,
    department_id: str | None = None,
    country: str | None = None,
    job_grade: str | None = None,
    hiring_type: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bq_warehouse.run_incremental_merge_sync(db)
    return bq_warehouse.query_curated_analytics(
        db,
        business_unit=business_unit,
        department_id=department_id,
        country=country,
        job_grade=job_grade,
        hiring_type=hiring_type,
        status=status_filter,
    )


@api_router.get("/audit-events")
def list_audit_events(
    entity_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(AuditEvent).order_by(AuditEvent.occurred_at.desc()).limit(limit)
    if entity_id:
        stmt = stmt.where(AuditEvent.entity_id == entity_id)
    events = list(db.scalars(stmt).all())
    return [
        {
            "id": e.id,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "actor_id": e.actor_id,
            "actor_role": e.actor_role,
            "action": e.action,
            "previous_state": e.previous_state,
            "new_state": e.new_state,
            "occurred_at": e.occurred_at,
        }
        for e in events
    ]


@api_router.get("/notifications")
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Notification)
        .where(
            (Notification.recipient_role == current_user.role)
            | (Notification.recipient_user_id == current_user.id)
        )
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    notifs = list(db.scalars(stmt).all())
    return [
        {
            "id": n.id,
            "recipient_role": n.recipient_role,
            "hiring_request_id": n.hiring_request_id,
            "event_type": n.event_type,
            "message": n.message,
            "created_at": n.created_at,
        }
        for n in notifs
    ]
