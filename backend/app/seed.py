from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.rbac import Role
from app.models.entities import (
    ApprovalRecord,
    ApprovalRule,
    ApprovalStep,
    AuditEvent,
    Budget,
    Department,
    HiringOutcome,
    HiringRequest,
    Position,
    User,
)
from app.services.cost_service import calculate_request_annualized_forecast


def seed_enterprise_data(db: Session) -> dict:
    """
    Seeds deterministic synthetic users (all 7 roles), departments, budgets,
    configurable approval rules, and initial hiring requests if the database is empty.
    """
    existing_user = db.scalar(select(User))
    if existing_user:
        return {"status": "already_seeded"}

    now = datetime(2026, 10, 15, 10, 0, tzinfo=timezone.utc)

    # 1. Departments
    dept_eng = Department(
        id="dept-eng",
        code="ENG-CORE",
        name="Platform & Cloud Engineering",
        business_unit="Digital & Technology",
        cost_center="CC-4100",
    )
    dept_data = Department(
        id="dept-data",
        code="DATA-AI",
        name="Enterprise Data & AI",
        business_unit="Digital & Technology",
        cost_center="CC-4200",
    )
    dept_ops = Department(
        id="dept-ops",
        code="OPS-SCM",
        name="Supply Chain & Store Operations",
        business_unit="Commercial Operations",
        cost_center="CC-5100",
    )
    db.add_all([dept_eng, dept_data, dept_ops])
    db.flush()

    # 2. Budgets (INR)
    db.add_all(
        [
            Budget(
                id="bud-eng-2026",
                department_id=dept_eng.id,
                fiscal_year=2026,
                currency="INR",
                allocated_budget=Decimal("35000000.00"),  # 3.5 Cr
                committed_cost=Decimal("9360000.00"),
                actual_spent=Decimal("3120000.00"),
            ),
            Budget(
                id="bud-data-2026",
                department_id=dept_data.id,
                fiscal_year=2026,
                currency="INR",
                allocated_budget=Decimal("25000000.00"),  # 2.5 Cr
                committed_cost=Decimal("6400000.00"),
                actual_spent=Decimal("0.00"),
            ),
            Budget(
                id="bud-ops-2026",
                department_id=dept_ops.id,
                fiscal_year=2026,
                currency="INR",
                allocated_budget=Decimal("24000000.00"),  # 2.4 Cr
                committed_cost=Decimal("0.00"),
                actual_spent=Decimal("0.00"),
            ),
        ]
    )

    # 3. Users across all 7 required roles
    users = [
        User(
            id="usr-creator",
            email="ananya.sharma@talentflow.example",
            full_name="Ananya Sharma (Request Creator)",
            role=Role.REQUEST_CREATOR,
            business_unit="Digital & Technology",
            department_id=dept_eng.id,
        ),
        User(
            id="usr-manager",
            email="vikram.desai@talentflow.example",
            full_name="Vikram Desai (Hiring Manager)",
            role=Role.HIRING_MANAGER,
            business_unit="Digital & Technology",
            department_id=dept_eng.id,
        ),
        User(
            id="usr-hrbp",
            email="meera.nair@talentflow.example",
            full_name="Meera Nair (HR Business Partner)",
            role=Role.HRBP,
            business_unit="Digital & Technology",
            department_id=dept_eng.id,
        ),
        User(
            id="usr-finance",
            email="rohan.kapoor@talentflow.example",
            full_name="Rohan Kapoor (Finance Reviewer)",
            role=Role.FINANCE_REVIEWER,
            business_unit="Corporate Finance",
            department_id=dept_eng.id,
        ),
        User(
            id="usr-committee",
            email="priya.menon@talentflow.example",
            full_name="Priya Menon (People Committee Chair)",
            role=Role.COMMITTEE_MEMBER,
            business_unit="Executive People Committee",
            department_id=dept_eng.id,
        ),
        User(
            id="usr-admin",
            email="admin@talentflow.example",
            full_name="Arjun Rao (Application Administrator)",
            role=Role.ADMIN,
            business_unit="Digital & Technology",
            department_id=dept_eng.id,
        ),
        User(
            id="usr-exec",
            email="cxo.observer@talentflow.example",
            full_name="Sanjay Verma (Executive Read-Only)",
            role=Role.EXEC_READONLY,
            business_unit="Executive Leadership",
            department_id=None,
        ),
    ]
    db.add_all(users)

    # 4. Configurable Approval Rules
    db.add_all(
        [
            ApprovalRule(
                id="rule-standard",
                rule_name="Standard Mid-Level Hiring Rule",
                min_grade="L3",
                min_total_cost=Decimal("0.00"),
                requires_manager_review=True,
                requires_finance_review=False,
                requires_committee_review=True,
                sla_hours=48,
            ),
            ApprovalRule(
                id="rule-senior-highcost",
                rule_name="Senior Grade (L6+) or High Cost (>50L INR) Finance Gate",
                min_grade="L6",
                min_total_cost=Decimal("5000000.00"),
                requires_manager_review=True,
                requires_finance_review=True,
                requires_committee_review=True,
                sla_hours=24,
            ),
        ]
    )
    db.flush()

    # 5. Seed Synthetic Requests
    # Request 1: Approved & Partially Filled (3 positions requested, 1 filled, 2 open recruiting)
    r1_forecast = calculate_request_annualized_forecast(
        est_annual_salary_per_pos=Decimal("2400000.00"),
        est_benefits_cost_per_pos=Decimal("480000.00"),
        est_recruitment_fee_per_pos=Decimal("160000.00"),
        est_onetime_cost_per_pos=Decimal("80000.00"),
        headcount_requested=3,
    )  # 3,120,000 * 3 = 9,360,000.00
    req1 = HiringRequest(
        id="req-seed-0001",
        request_code="REQ-2026-0001",
        job_title="Senior Cloud Platform Engineer",
        job_family="Software Engineering",
        department_id=dept_eng.id,
        business_unit="Digital & Technology",
        country="India",
        city="Pune",
        work_location="HYBRID",
        job_grade="L5",
        employment_type="FULL_TIME",
        hiring_manager_id="usr-manager",
        request_owner_id="usr-creator",
        hiring_type="NEW_HEADCOUNT",
        headcount_requested=3,
        justification="Expand Cloud Run and Kubernetes platform reliability squad for Q4 enterprise rollout.",
        expected_business_impact="Reduce deployment lead time by 40% and support 99.95% SLA.",
        requested_start_date=date(2026, 11, 15),
        target_hiring_date=date(2026, 11, 1),
        currency="INR",
        est_annual_salary_per_pos=Decimal("2400000.00"),
        est_benefits_cost_per_pos=Decimal("480000.00"),
        est_recruitment_fee_per_pos=Decimal("160000.00"),
        est_onetime_cost_per_pos=Decimal("80000.00"),
        total_annualized_forecast=r1_forecast,
        status="PARTIALLY_FILLED",
        submitted_at=now - timedelta(days=10),
        approved_at=now - timedelta(days=8),
        created_at=now - timedelta(days=12),
        updated_at=now - timedelta(days=2),
    )
    db.add(req1)
    db.flush()

    pos1_1 = Position(
        id="pos-0001-1",
        hiring_request_id=req1.id,
        position_index=1,
        position_code="REQ-2026-0001-P01",
        status="FILLED",
        target_hire_date=date(2026, 11, 1),
    )
    pos1_2 = Position(
        id="pos-0001-2",
        hiring_request_id=req1.id,
        position_index=2,
        position_code="REQ-2026-0001-P02",
        status="OPEN_RECRUITING",
        target_hire_date=date(2026, 11, 1),
    )
    pos1_3 = Position(
        id="pos-0001-3",
        hiring_request_id=req1.id,
        position_index=3,
        position_code="REQ-2026-0001-P03",
        status="OPEN_RECRUITING",
        target_hire_date=date(2026, 11, 1),
    )
    db.add_all([pos1_1, pos1_2, pos1_3])
    db.flush()

    db.add(
        HiringOutcome(
            id="out-0001-1",
            position_id=pos1_1.id,
            candidate_ref="CAND-SYN-101",
            actual_hire_date=date(2026, 10, 25),
            actual_annual_base_salary=Decimal("2350000.00"),
            actual_benefits_cost=Decimal("470000.00"),
            actual_recruitment_fee=Decimal("150000.00"),
            actual_onetime_cost=Decimal("80000.00"),
            closure_status="HIRED",
            closure_reason="Offer accepted and onboarding completed.",
        )
    )

    step1_mgr = ApprovalStep(
        id="stp-0001-1",
        hiring_request_id=req1.id,
        sequence_order=1,
        stage_name="MANAGER_REVIEW",
        required_role=Role.HIRING_MANAGER,
        step_status="APPROVED",
        completed_at=now - timedelta(days=9),
    )
    step1_fin = ApprovalStep(
        id="stp-0001-2",
        hiring_request_id=req1.id,
        sequence_order=2,
        stage_name="FINANCE_REVIEW",
        required_role=Role.FINANCE_REVIEWER,
        step_status="APPROVED",
        completed_at=now - timedelta(days=8, hours=12),
    )
    step1_com = ApprovalStep(
        id="stp-0001-3",
        hiring_request_id=req1.id,
        sequence_order=3,
        stage_name="COMMITTEE_PENDING",
        required_role=Role.COMMITTEE_MEMBER,
        step_status="APPROVED",
        completed_at=now - timedelta(days=8),
    )
    db.add_all([step1_mgr, step1_fin, step1_com])
    db.flush()

    db.add_all(
        [
            ApprovalRecord(
                id="rec-0001-1",
                hiring_request_id=req1.id,
                approval_step_id=step1_mgr.id,
                approver_id="usr-manager",
                stage_name="MANAGER_REVIEW",
                decision="APPROVE",
                comments="Validated headcount and platform squad roadmap alignment.",
                created_at=now - timedelta(days=9),
            ),
            ApprovalRecord(
                id="rec-0001-2",
                hiring_request_id=req1.id,
                approval_step_id=step1_fin.id,
                approver_id="usr-finance",
                stage_name="FINANCE_REVIEW",
                decision="APPROVE",
                comments="Budget verified within CC-4100 Q4 envelope.",
                created_at=now - timedelta(days=8, hours=12),
            ),
            ApprovalRecord(
                id="rec-0001-3",
                hiring_request_id=req1.id,
                approval_step_id=step1_com.id,
                approver_id="usr-committee",
                stage_name="COMMITTEE_PENDING",
                decision="APPROVE",
                comments="Approved by People Committee for immediate recruitment.",
                created_at=now - timedelta(days=8),
            ),
        ]
    )

    # Request 2: Pending People Committee (Overdue SLA indicator demonstration)
    r2_forecast = calculate_request_annualized_forecast(
        est_annual_salary_per_pos=Decimal("3800000.00"),
        est_benefits_cost_per_pos=Decimal("760000.00"),
        est_recruitment_fee_per_pos=Decimal("240000.00"),
        est_onetime_cost_per_pos=Decimal("100000.00"),
        headcount_requested=2,
    )  # 4,900,000 * 2 = 9,800,000.00
    req2 = HiringRequest(
        id="req-seed-0002",
        request_code="REQ-2026-0002",
        job_title="Principal Data & BigQuery Architect",
        job_family="Data & Analytics",
        department_id=dept_data.id,
        business_unit="Digital & Technology",
        country="India",
        city="Bengaluru",
        work_location="HYBRID",
        job_grade="L6",
        employment_type="FULL_TIME",
        hiring_manager_id="usr-manager",
        request_owner_id="usr-creator",
        hiring_type="NEW_HEADCOUNT",
        headcount_requested=2,
        justification="Lead enterprise BigQuery data mesh and real-time analytics governance.",
        expected_business_impact="Unify 14 country data marts and reduce query slot spend by 28%.",
        requested_start_date=date(2026, 12, 1),
        target_hiring_date=date(2026, 11, 20),
        currency="INR",
        est_annual_salary_per_pos=Decimal("3800000.00"),
        est_benefits_cost_per_pos=Decimal("760000.00"),
        est_recruitment_fee_per_pos=Decimal("240000.00"),
        est_onetime_cost_per_pos=Decimal("100000.00"),
        total_annualized_forecast=r2_forecast,
        status="COMMITTEE_PENDING",
        submitted_at=now - timedelta(days=5),
        created_at=now - timedelta(days=6),
        updated_at=now - timedelta(days=3),
    )
    db.add(req2)
    db.flush()

    db.add_all(
        [
            Position(
                id="pos-0002-1",
                hiring_request_id=req2.id,
                position_index=1,
                position_code="REQ-2026-0002-P01",
                status="REQUESTED",
                target_hire_date=date(2026, 11, 20),
            ),
            Position(
                id="pos-0002-2",
                hiring_request_id=req2.id,
                position_index=2,
                position_code="REQ-2026-0002-P02",
                status="REQUESTED",
                target_hire_date=date(2026, 11, 20),
            ),
            ApprovalStep(
                id="stp-0002-1",
                hiring_request_id=req2.id,
                sequence_order=1,
                stage_name="MANAGER_REVIEW",
                required_role=Role.HIRING_MANAGER,
                step_status="APPROVED",
                completed_at=now - timedelta(days=4),
            ),
            ApprovalStep(
                id="stp-0002-2",
                hiring_request_id=req2.id,
                sequence_order=2,
                stage_name="FINANCE_REVIEW",
                required_role=Role.FINANCE_REVIEWER,
                step_status="APPROVED",
                completed_at=now - timedelta(days=3),
            ),
            ApprovalStep(
                id="stp-0002-3",
                hiring_request_id=req2.id,
                sequence_order=3,
                stage_name="COMMITTEE_PENDING",
                required_role=Role.COMMITTEE_MEMBER,
                step_status="ACTIVE",
                due_at=now - timedelta(days=1),  # Overdue SLA!
            ),
        ]
    )

    # Request 3: Approved Replacement Role
    r3_forecast = calculate_request_annualized_forecast(
        est_annual_salary_per_pos=Decimal("2600000.00"),
        est_benefits_cost_per_pos=Decimal("420000.00"),
        est_recruitment_fee_per_pos=Decimal("120000.00"),
        est_onetime_cost_per_pos=Decimal("60000.00"),
        headcount_requested=2,
    )  # 3,200,000 * 2 = 6,400,000.00
    req3 = HiringRequest(
        id="req-seed-0003",
        request_code="REQ-2026-0003",
        job_title="Analytics Engineer",
        job_family="Data & Analytics",
        department_id=dept_data.id,
        business_unit="Digital & Technology",
        country="India",
        city="Pune",
        work_location="HYBRID",
        job_grade="L4",
        employment_type="FULL_TIME",
        hiring_manager_id="usr-manager",
        request_owner_id="usr-creator",
        hiring_type="REPLACEMENT",
        headcount_requested=2,
        justification="Backfill two critical analytics engineers for financial reporting pipelines.",
        expected_business_impact="Maintain SLA on executive KPI marts.",
        requested_start_date=date(2026, 11, 25),
        target_hiring_date=date(2026, 11, 10),
        currency="INR",
        est_annual_salary_per_pos=Decimal("2600000.00"),
        est_benefits_cost_per_pos=Decimal("420000.00"),
        est_recruitment_fee_per_pos=Decimal("120000.00"),
        est_onetime_cost_per_pos=Decimal("60000.00"),
        total_annualized_forecast=r3_forecast,
        status="APPROVED",
        submitted_at=now - timedelta(days=20),
        approved_at=now - timedelta(days=18),
        created_at=now - timedelta(days=21),
        updated_at=now - timedelta(days=18),
    )
    db.add(req3)
    db.flush()

    db.add_all(
        [
            Position(
                id="pos-0003-1",
                hiring_request_id=req3.id,
                position_index=1,
                position_code="REQ-2026-0003-P01",
                status="APPROVED",
                target_hire_date=date(2026, 11, 10),
            ),
            Position(
                id="pos-0003-2",
                hiring_request_id=req3.id,
                position_index=2,
                position_code="REQ-2026-0003-P02",
                status="APPROVED",
                target_hire_date=date(2026, 11, 10),
            ),
        ]
    )

    db.add(
        AuditEvent(
            id="aud-seed-0001",
            entity_type="System",
            entity_id="seed-init",
            actor_id="usr-admin",
            actor_role=Role.ADMIN,
            action="SEED_SYNTHETIC_DATA",
            previous_state=None,
            new_state={"seeded_requests": 3, "seeded_users": 7},
            occurred_at=now,
        )
    )

    db.commit()
    return {"status": "seeded", "users": 7, "departments": 3, "requests": 3}
