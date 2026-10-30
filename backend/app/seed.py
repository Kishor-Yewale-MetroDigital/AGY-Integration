from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, select
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

    now = datetime(2026, 10, 15, 10, 0, tzinfo=UTC)

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
                actual_spent=Decimal("3050000.00"),
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


def populate_interactive_approval_queue(db: Session) -> dict:
    """
    Ensures the local/demo environment has active requests across all approval stages
    (COMMITTEE_PENDING, FINANCE_REVIEW, MANAGER_REVIEW, DRAFT) so reviewers can test
    Approve, Request Clarification, Reject, Resubmit, and Position Outcomes repeatedly.
    """
    now = datetime.now(UTC)
    restored_or_added = []

    # 1. Restore REQ-2026-0002 to COMMITTEE_PENDING if it was already decided
    req2 = db.get(HiringRequest, "req-seed-0002")
    if req2 and req2.status != "COMMITTEE_PENDING":
        req2.status = "COMMITTEE_PENDING"
        req2.approved_at = None
        req2.closed_at = None
        req2.updated_at = now
        for p in req2.positions:
            p.status = "REQUESTED"
        for s in req2.approval_steps:
            if s.stage_name == "COMMITTEE_PENDING":
                s.step_status = "ACTIVE"
                s.completed_at = None
                db.execute(delete(ApprovalRecord).where(ApprovalRecord.approval_step_id == s.id))
            else:
                s.step_status = "APPROVED"
        restored_or_added.append("REQ-2026-0002 (restored to COMMITTEE_PENDING)")

    # 2. Add REQ-2026-0004 in COMMITTEE_PENDING if not present
    if not db.get(HiringRequest, "req-seed-0004"):
        r4_forecast = calculate_request_annualized_forecast(
            est_annual_salary_per_pos=Decimal("2900000.00"),
            est_benefits_cost_per_pos=Decimal("450000.00"),
            est_recruitment_fee_per_pos=Decimal("150000.00"),
            est_onetime_cost_per_pos=Decimal("750000.00") if False else Decimal("75000.00"),
            headcount_requested=2,
        )
        req4 = HiringRequest(
            id="req-seed-0004",
            request_code="REQ-2026-0004",
            job_title="Lead Site Reliability Engineer (Cloud Run)",
            job_family="Software Engineering",
            department_id="dept-eng",
            business_unit="Digital & Technology",
            country="India",
            city="Pune",
            work_location="HYBRID",
            job_grade="L5",
            employment_type="FULL_TIME",
            hiring_manager_id="usr-manager",
            request_owner_id="usr-creator",
            hiring_type="NEW_HEADCOUNT",
            headcount_requested=2,
            justification="Strengthen production observability and zero-downtime deployment automation.",
            expected_business_impact="Cut P1 incident MTTR from 45m to under 12m across 24 microservices.",
            requested_start_date=date(2026, 12, 10),
            target_hiring_date=date(2026, 11, 25),
            currency="INR",
            est_annual_salary_per_pos=Decimal("2900000.00"),
            est_benefits_cost_per_pos=Decimal("450000.00"),
            est_recruitment_fee_per_pos=Decimal("150000.00"),
            est_onetime_cost_per_pos=Decimal("75000.00"),
            total_annualized_forecast=r4_forecast,
            status="COMMITTEE_PENDING",
            submitted_at=now - timedelta(days=2),
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(hours=6),
        )
        db.add(req4)
        db.flush()
        db.add_all(
            [
                Position(
                    id="pos-0004-1",
                    hiring_request_id=req4.id,
                    position_index=1,
                    position_code="REQ-2026-0004-P01",
                    status="REQUESTED",
                    target_hire_date=date(2026, 11, 25),
                ),
                Position(
                    id="pos-0004-2",
                    hiring_request_id=req4.id,
                    position_index=2,
                    position_code="REQ-2026-0004-P02",
                    status="REQUESTED",
                    target_hire_date=date(2026, 11, 25),
                ),
                ApprovalStep(
                    id="stp-0004-1",
                    hiring_request_id=req4.id,
                    sequence_order=1,
                    stage_name="MANAGER_REVIEW",
                    required_role=Role.HIRING_MANAGER,
                    step_status="APPROVED",
                    completed_at=now - timedelta(days=1, hours=12),
                ),
                ApprovalStep(
                    id="stp-0004-2",
                    hiring_request_id=req4.id,
                    sequence_order=2,
                    stage_name="FINANCE_REVIEW",
                    required_role=Role.FINANCE_REVIEWER,
                    step_status="APPROVED",
                    completed_at=now - timedelta(hours=12),
                ),
                ApprovalStep(
                    id="stp-0004-3",
                    hiring_request_id=req4.id,
                    sequence_order=3,
                    stage_name="COMMITTEE_PENDING",
                    required_role=Role.COMMITTEE_MEMBER,
                    step_status="ACTIVE",
                    due_at=now + timedelta(hours=36),
                ),
            ]
        )
        restored_or_added.append("REQ-2026-0004 (COMMITTEE_PENDING)")
    else:
        req4 = db.get(HiringRequest, "req-seed-0004")
        if req4 and req4.status != "COMMITTEE_PENDING":
            req4.status = "COMMITTEE_PENDING"
            req4.approved_at = None
            req4.closed_at = None
            req4.updated_at = now
            for p in req4.positions:
                p.status = "REQUESTED"
            for s in req4.approval_steps:
                s.step_status = "ACTIVE" if s.stage_name == "COMMITTEE_PENDING" else "APPROVED"
                if s.stage_name == "COMMITTEE_PENDING":
                    s.completed_at = None
                    db.execute(delete(ApprovalRecord).where(ApprovalRecord.approval_step_id == s.id))
            restored_or_added.append("REQ-2026-0004 (restored to COMMITTEE_PENDING)")

    # 3. Add REQ-2026-0005 in FINANCE_REVIEW if not present
    if not db.get(HiringRequest, "req-seed-0005"):
        r5_forecast = calculate_request_annualized_forecast(
            est_annual_salary_per_pos=Decimal("3400000.00"),
            est_benefits_cost_per_pos=Decimal("520000.00"),
            est_recruitment_fee_per_pos=Decimal("180000.00"),
            est_onetime_cost_per_pos=Decimal("90000.00"),
            headcount_requested=2,
        )
        req5 = HiringRequest(
            id="req-seed-0005",
            request_code="REQ-2026-0005",
            job_title="Staff Supply Chain ML Scientist",
            job_family="Data & Analytics",
            department_id="dept-ops",
            business_unit="Commercial Operations",
            country="India",
            city="Bengaluru",
            work_location="HYBRID",
            job_grade="L6",
            employment_type="FULL_TIME",
            hiring_manager_id="usr-manager",
            request_owner_id="usr-creator",
            hiring_type="NEW_HEADCOUNT",
            headcount_requested=2,
            justification="Build demand-forecasting models for perishable inventory across 32 wholesale depots.",
            expected_business_impact="Reduce perishable spoilage by 11% (~4.2 Cr INR annual savings).",
            requested_start_date=date(2026, 12, 15),
            target_hiring_date=date(2026, 11, 30),
            currency="INR",
            est_annual_salary_per_pos=Decimal("3400000.00"),
            est_benefits_cost_per_pos=Decimal("520000.00"),
            est_recruitment_fee_per_pos=Decimal("180000.00"),
            est_onetime_cost_per_pos=Decimal("90000.00"),
            total_annualized_forecast=r5_forecast,
            status="FINANCE_REVIEW",
            submitted_at=now - timedelta(days=1),
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(hours=4),
        )
        db.add(req5)
        db.flush()
        db.add_all(
            [
                Position(
                    id="pos-0005-1",
                    hiring_request_id=req5.id,
                    position_index=1,
                    position_code="REQ-2026-0005-P01",
                    status="REQUESTED",
                    target_hire_date=date(2026, 11, 30),
                ),
                Position(
                    id="pos-0005-2",
                    hiring_request_id=req5.id,
                    position_index=2,
                    position_code="REQ-2026-0005-P02",
                    status="REQUESTED",
                    target_hire_date=date(2026, 11, 30),
                ),
                ApprovalStep(
                    id="stp-0005-1",
                    hiring_request_id=req5.id,
                    sequence_order=1,
                    stage_name="MANAGER_REVIEW",
                    required_role=Role.HIRING_MANAGER,
                    step_status="APPROVED",
                    completed_at=now - timedelta(hours=10),
                ),
                ApprovalStep(
                    id="stp-0005-2",
                    hiring_request_id=req5.id,
                    sequence_order=2,
                    stage_name="FINANCE_REVIEW",
                    required_role=Role.FINANCE_REVIEWER,
                    step_status="ACTIVE",
                    due_at=now + timedelta(hours=24),
                ),
                ApprovalStep(
                    id="stp-0005-3",
                    hiring_request_id=req5.id,
                    sequence_order=3,
                    stage_name="COMMITTEE_PENDING",
                    required_role=Role.COMMITTEE_MEMBER,
                    step_status="PENDING",
                    due_at=now + timedelta(hours=48),
                ),
            ]
        )
        restored_or_added.append("REQ-2026-0005 (FINANCE_REVIEW)")
    else:
        req5 = db.get(HiringRequest, "req-seed-0005")
        if req5 and req5.status != "FINANCE_REVIEW":
            req5.status = "FINANCE_REVIEW"
            req5.approved_at = None
            req5.closed_at = None
            req5.updated_at = now
            for p in req5.positions:
                p.status = "REQUESTED"
            for s in req5.approval_steps:
                if s.stage_name == "MANAGER_REVIEW":
                    s.step_status = "APPROVED"
                elif s.stage_name == "FINANCE_REVIEW":
                    s.step_status = "ACTIVE"
                    s.completed_at = None
                    db.execute(delete(ApprovalRecord).where(ApprovalRecord.approval_step_id == s.id))
                else:
                    s.step_status = "PENDING"
                    s.completed_at = None
                    db.execute(delete(ApprovalRecord).where(ApprovalRecord.approval_step_id == s.id))
            restored_or_added.append("REQ-2026-0005 (restored to FINANCE_REVIEW)")

    # 4. Add REQ-2026-0006 in MANAGER_REVIEW if not present
    if not db.get(HiringRequest, "req-seed-0006"):
        r6_forecast = calculate_request_annualized_forecast(
            est_annual_salary_per_pos=Decimal("1900000.00"),
            est_benefits_cost_per_pos=Decimal("300000.00"),
            est_recruitment_fee_per_pos=Decimal("100000.00"),
            est_onetime_cost_per_pos=Decimal("50000.00"),
            headcount_requested=1,
        )
        req6 = HiringRequest(
            id="req-seed-0006",
            request_code="REQ-2026-0006",
            job_title="Fulfillment Operations Systems Specialist",
            job_family="Operations Engineering",
            department_id="dept-ops",
            business_unit="Commercial Operations",
            country="India",
            city="Mumbai",
            work_location="ONSITE",
            job_grade="L4",
            employment_type="FULL_TIME",
            hiring_manager_id="usr-manager",
            request_owner_id="usr-creator",
            hiring_type="REPLACEMENT",
            headcount_requested=1,
            justification="Backfill critical warehouse management system specialist for Mumbai distribution hub.",
            expected_business_impact="Maintain 99.4% on-time dispatch across West India B2B orders.",
            requested_start_date=date(2026, 12, 5),
            target_hiring_date=date(2026, 11, 18),
            currency="INR",
            est_annual_salary_per_pos=Decimal("1900000.00"),
            est_benefits_cost_per_pos=Decimal("300000.00"),
            est_recruitment_fee_per_pos=Decimal("100000.00"),
            est_onetime_cost_per_pos=Decimal("50000.00"),
            total_annualized_forecast=r6_forecast,
            status="MANAGER_REVIEW",
            submitted_at=now - timedelta(hours=6),
            created_at=now - timedelta(hours=8),
            updated_at=now - timedelta(hours=6),
        )
        db.add(req6)
        db.flush()
        db.add_all(
            [
                Position(
                    id="pos-0006-1",
                    hiring_request_id=req6.id,
                    position_index=1,
                    position_code="REQ-2026-0006-P01",
                    status="REQUESTED",
                    target_hire_date=date(2026, 11, 18),
                ),
                ApprovalStep(
                    id="stp-0006-1",
                    hiring_request_id=req6.id,
                    sequence_order=1,
                    stage_name="MANAGER_REVIEW",
                    required_role=Role.HIRING_MANAGER,
                    step_status="ACTIVE",
                    due_at=now + timedelta(hours=42),
                ),
                ApprovalStep(
                    id="stp-0006-2",
                    hiring_request_id=req6.id,
                    sequence_order=2,
                    stage_name="COMMITTEE_PENDING",
                    required_role=Role.COMMITTEE_MEMBER,
                    step_status="PENDING",
                    due_at=now + timedelta(hours=90),
                ),
            ]
        )
        restored_or_added.append("REQ-2026-0006 (MANAGER_REVIEW)")
    else:
        req6 = db.get(HiringRequest, "req-seed-0006")
        if req6 and req6.status != "MANAGER_REVIEW":
            req6.status = "MANAGER_REVIEW"
            req6.approved_at = None
            req6.closed_at = None
            req6.updated_at = now
            for p in req6.positions:
                p.status = "REQUESTED"
            for s in req6.approval_steps:
                if s.stage_name == "MANAGER_REVIEW":
                    s.step_status = "ACTIVE"
                    s.completed_at = None
                    db.execute(delete(ApprovalRecord).where(ApprovalRecord.approval_step_id == s.id))
                else:
                    s.step_status = "PENDING"
                    s.completed_at = None
                    db.execute(delete(ApprovalRecord).where(ApprovalRecord.approval_step_id == s.id))
            restored_or_added.append("REQ-2026-0006 (restored to MANAGER_REVIEW)")

    db.flush()

    approved_statuses = {"APPROVED", "RECRUITING", "PARTIALLY_FILLED", "FILLED", "CLOSED"}
    all_reqs = list(db.scalars(select(HiringRequest)).unique().all())
    for b in db.scalars(select(Budget)).all():
        dept_committed = sum(
            (Decimal(r.total_annualized_forecast) for r in all_reqs if r.department_id == b.department_id and r.status in approved_statuses),
            Decimal("0.00"),
        )
        dept_actual = Decimal("0.00")
        for r in all_reqs:
            if r.department_id == b.department_id and r.status in approved_statuses:
                for p in r.positions:
                    if p.status == "FILLED" and p.outcome and p.outcome.closure_status == "HIRED":
                        dept_actual += (
                            Decimal(p.outcome.actual_annual_base_salary)
                            + Decimal(p.outcome.actual_benefits_cost)
                            + Decimal(p.outcome.actual_recruitment_fee)
                            + Decimal(p.outcome.actual_onetime_cost)
                        )
        b.committed_cost = dept_committed
        b.actual_spent = dept_actual

    db.commit()
    return {"status": "queue_populated", "items": restored_or_added}
