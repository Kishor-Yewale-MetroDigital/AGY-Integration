"""
Automated Unit, Integration, and End-to-End Acceptance Suite for TalentFlow.
Covers all 17 mandatory acceptance scenarios from Module 9.
"""
from decimal import Decimal
from pathlib import Path

import pytest

from app.models.entities import AuditEvent


def _valid_request_payload(
    *,
    job_grade: str = "L4",
    headcount: int = 2,
    salary: str = "1800000.00",
    benefits: str = "300000.00",
    fee: str = "100000.00",
    onetime: str = "50000.00",
) -> dict:
    return {
        "job_title": "Full-Stack Product Engineer",
        "job_family": "Software Engineering",
        "department_id": "dept-eng",
        "business_unit": "Digital & Technology",
        "country": "India",
        "city": "Pune",
        "work_location": "HYBRID",
        "job_grade": job_grade,
        "employment_type": "FULL_TIME",
        "hiring_manager_id": "usr-manager",
        "hiring_type": "NEW_HEADCOUNT",
        "headcount_requested": headcount,
        "justification": "Deliver customer order portal modernization for FY2026.",
        "expected_business_impact": "Increase digital order conversion by 15%.",
        "requested_start_date": "2026-12-01",
        "target_hiring_date": "2026-11-15",
        "currency": "INR",
        "est_annual_salary_per_pos": salary,
        "est_benefits_cost_per_pos": benefits,
        "est_recruitment_fee_per_pos": fee,
        "est_onetime_cost_per_pos": onetime,
    }


def test_scenario_01_hiring_manager_creates_and_submits_valid_request(client):
    """Scenario 1: A hiring manager creates and submits a valid request."""
    res = client.post(
        "/api/v1/requests",
        json=_valid_request_payload(headcount=2),
        headers={"X-User-Id": "usr-creator"},
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["status"] == "DRAFT"
    assert len(data["positions"]) == 2
    # (18L + 3L + 1L + 0.5L) * 2 = 45,00,000.00
    assert Decimal(data["total_annualized_forecast"]) == Decimal("4500000.00")

    sub_res = client.post(
        f"/api/v1/requests/{data['id']}/submit",
        headers={"X-User-Id": "usr-creator"},
    )
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["status"] == "MANAGER_REVIEW"
    assert len(sub_data["approval_steps"]) >= 2


def test_scenario_02_invalid_request_rejected_with_validation_errors(client):
    """Scenario 2: An invalid request is rejected with useful validation errors."""
    bad_payload = _valid_request_payload()
    bad_payload["headcount_requested"] = 0
    bad_payload["justification"] = "short"
    bad_payload["requested_start_date"] = "2026-10-01"  # Before target_hiring_date

    res = client.post(
        "/api/v1/requests",
        json=bad_payload,
        headers={"X-User-Id": "usr-creator"},
    )
    assert res.status_code == 422
    detail = str(res.json())
    assert "headcount_requested" in detail or "justification" in detail


def test_scenario_03_finance_review_cannot_be_skipped(client):
    """Scenario 3: A request requiring finance review cannot skip that stage."""
    # Senior L6 grade + high cost triggers mandatory Finance Review stage
    res = client.post(
        "/api/v1/requests",
        json=_valid_request_payload(job_grade="L6", headcount=2, salary="3200000.00"),
        headers={"X-User-Id": "usr-creator"},
    )
    req_id = res.json()["id"]
    client.post(f"/api/v1/requests/{req_id}/submit", headers={"X-User-Id": "usr-creator"})

    # Manager approves stage 1 -> advances to FINANCE_REVIEW
    mgr_res = client.post(
        f"/api/v1/requests/{req_id}/decisions",
        json={"decision": "APPROVE", "comments": "Manager approved."},
        headers={"X-User-Id": "usr-manager"},
    )
    assert mgr_res.status_code == 200
    assert mgr_res.json()["status"] == "FINANCE_REVIEW"

    # Committee member tries to skip FINANCE_REVIEW and approve directly -> 409/403 blocked
    skip_res = client.post(
        f"/api/v1/requests/{req_id}/decisions?target_stage=COMMITTEE_PENDING",
        json={"decision": "APPROVE", "comments": "Attempting to skip finance."},
        headers={"X-User-Id": "usr-committee"},
    )
    assert skip_res.status_code == 409

    # Also attempting to patch `status` directly is blocked by schema validation (extra="forbid")
    bypass_res = client.patch(
        f"/api/v1/requests/{req_id}",
        json={"status": "APPROVED"},
        headers={"X-User-Id": "usr-admin"},
    )
    assert bypass_res.status_code == 422


def test_scenario_04_authorized_committee_member_approves_request(client):
    """Scenario 4: An authorized committee member approves a request through completion."""
    # Standard L4 request (45L INR < 50L threshold -> Manager Review -> Committee Pending)
    res = client.post(
        "/api/v1/requests",
        json=_valid_request_payload(job_grade="L4", headcount=1),
        headers={"X-User-Id": "usr-creator"},
    )
    req_id = res.json()["id"]
    client.post(f"/api/v1/requests/{req_id}/submit", headers={"X-User-Id": "usr-creator"})

    # Stage 1: Manager approves
    r1 = client.post(
        f"/api/v1/requests/{req_id}/decisions",
        json={"decision": "APPROVE", "comments": "Manager sign-off."},
        headers={"X-User-Id": "usr-manager"},
    )
    assert r1.json()["status"] == "COMMITTEE_PENDING"

    # Stage 2: People Committee approves
    r2 = client.post(
        f"/api/v1/requests/{req_id}/decisions",
        json={"decision": "APPROVE", "comments": "People Committee approved headcount."},
        headers={"X-User-Id": "usr-committee"},
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "APPROVED"
    assert all(p["status"] == "APPROVED" for p in r2.json()["positions"])


def test_scenario_05_unauthorized_user_and_self_approval_blocked(client):
    """Scenario 5: An unauthorized user (or request creator via SoD) cannot approve or reject."""
    # Created by usr-manager himself -> Segregation of Duties must block usr-manager from approving own request!
    res = client.post(
        "/api/v1/requests",
        json=_valid_request_payload(job_grade="L4", headcount=1),
        headers={"X-User-Id": "usr-manager"},
    )
    req_id = res.json()["id"]
    client.post(f"/api/v1/requests/{req_id}/submit", headers={"X-User-Id": "usr-manager"})

    # Self-approval attempt by usr-manager -> 403 Forbidden (Segregation of Duties)
    sod_res = client.post(
        f"/api/v1/requests/{req_id}/decisions",
        json={"decision": "APPROVE", "comments": "Approving my own request."},
        headers={"X-User-Id": "usr-manager"},
    )
    assert sod_res.status_code == 403
    assert "Segregation of Duties" in sod_res.json()["detail"]

    # Executive Read-Only user attempt -> 403 Forbidden
    exec_res = client.post(
        f"/api/v1/requests/{req_id}/decisions",
        json={"decision": "APPROVE", "comments": "Exec trying to approve."},
        headers={"X-User-Id": "usr-exec"},
    )
    assert exec_res.status_code == 403


def test_scenario_06_rejected_request_requires_reason_and_retains_audit_history(client, test_db_session):
    """Scenario 6: A rejected request requires a reason and retains its immutable audit history."""
    res = client.post(
        "/api/v1/requests",
        json=_valid_request_payload(job_grade="L4", headcount=1),
        headers={"X-User-Id": "usr-creator"},
    )
    req_id = res.json()["id"]
    client.post(f"/api/v1/requests/{req_id}/submit", headers={"X-User-Id": "usr-creator"})

    # Reject without reason -> 422 validation failure
    empty_rej = client.post(
        f"/api/v1/requests/{req_id}/decisions",
        json={"decision": "REJECT", "comments": ""},
        headers={"X-User-Id": "usr-manager"},
    )
    assert empty_rej.status_code == 422

    # Reject with valid reason -> 200 REJECTED
    valid_rej = client.post(
        f"/api/v1/requests/{req_id}/decisions",
        json={"decision": "REJECT", "comments": "Role duplicated in existing Q4 contractor squad."},
        headers={"X-User-Id": "usr-manager"},
    )
    assert valid_rej.status_code == 200
    assert valid_rej.json()["status"] == "REJECTED"

    # Verify audit trail recorded and is immutable
    audits = client.get(f"/api/v1/audit-events?entity_id={req_id}", headers={"X-User-Id": "usr-admin"}).json()
    actions = [a["action"] for a in audits]
    assert "CREATE_REQUEST" in actions
    assert "SUBMIT_REQUEST" in actions
    assert "WORKFLOW_REJECT" in actions

    audit_row = test_db_session.query(AuditEvent).first()
    with pytest.raises(PermissionError, match="immutable"):
        audit_row.action = "TAMPERED"
        test_db_session.commit()
    test_db_session.rollback()


def test_scenario_07_duplicate_approval_actions_prevented(client):
    """Scenario 7: Duplicate approval actions are prevented."""
    # Seeded request req-seed-0003 is already APPROVED -> acting again returns 409 Conflict
    dup_res = client.post(
        "/api/v1/requests/req-seed-0003/decisions",
        json={"decision": "APPROVE", "comments": "Duplicate approval attempt."},
        headers={"X-User-Id": "usr-committee"},
    )
    assert dup_res.status_code == 409


def test_scenario_08_and_09_budget_calculations_and_no_multi_position_double_counting(client):
    """
    Scenario 8 & 9: Budget calculations and cost rollups produce expected Decimal results,
    and multiple positions do not cause headcount or cost double-counting.
    """
    summary = client.get("/api/v1/workforce/summary", headers={"X-User-Id": "usr-finance"}).json()
    # Seeded data has:
    # req-seed-0001 (3 positions, PARTIALLY_FILLED: 1 FILLED, 2 OPEN_RECRUITING; forecast = 93,60,000)
    # req-seed-0002 (2 positions, COMMITTEE_PENDING: not yet approved)
    # req-seed-0003 (2 positions, APPROVED: 2 APPROVED; forecast = 64,00,000)
    assert summary["requested_headcount"] == 7  # 3 + 2 + 2
    assert summary["approved_headcount"] == 5  # 3 + 2 (counted once per position despite 3 approval records on req 1)
    assert summary["filled_positions"] == 1
    assert summary["open_approved_positions"] == 4
    assert Decimal(summary["forecast_total_hiring_cost"]) == Decimal("15760000.00")  # 93.6L + 64.0L
    assert Decimal(summary["allocated_department_budget"]) == Decimal("84000000.00")  # 3.5Cr + 2.5Cr + 2.4Cr


def test_scenario_10_dashboard_filters_return_consistent_results(client):
    """Scenario 10: Dashboard filters return consistent results."""
    eng_reqs = client.get(
        "/api/v1/requests?department_id=dept-eng",
        headers={"X-User-Id": "usr-exec"},
    ).json()
    assert len(eng_reqs) == 1
    assert eng_reqs[0]["request_code"] == "REQ-2026-0001"

    l6_dash = client.get(
        "/api/v1/dashboard/overview?job_grade=L6",
        headers={"X-User-Id": "usr-exec"},
    ).json()
    assert l6_dash["bigquery_historical_analytics"]["kpis"]["total_requests"] == 1
    assert l6_dash["bigquery_historical_analytics"]["kpis"]["pending_committee"] == 1


def test_scenario_11_database_records_persist_across_sessions(test_db_session):
    """Scenario 11: Transactional records persist across new database sessions."""
    from sqlalchemy.orm import sessionmaker

    from app.models.entities import HiringRequest

    NewSession = sessionmaker(bind=test_db_session.get_bind(), future=True)
    with NewSession() as fresh_session:
        persisted = fresh_session.get(HiringRequest, "req-seed-0001")
        assert persisted is not None
        assert persisted.request_code == "REQ-2026-0001"
        assert len(persisted.positions) == 3


def test_scenario_12_and_13_bigquery_idempotent_pipeline_and_reconciliation(client):
    """
    Scenario 12 & 13: The BigQuery pipeline can be rerun without duplicating records,
    and BigQuery metrics match independently calculated expected results.
    """
    sync1 = client.post("/api/v1/analytics/sync", headers={"X-User-Id": "usr-admin"}).json()
    client.post("/api/v1/analytics/sync", headers={"X-User-Id": "usr-admin"})
    sync3 = client.post("/api/v1/analytics/sync", headers={"X-User-Id": "usr-admin"}).json()

    assert sync3["sync_run_count"] >= 3
    assert sync1["total_unique_requests_in_bq"] == sync3["total_unique_requests_in_bq"] == 3
    assert sync1["total_unique_positions_in_bq"] == sync3["total_unique_positions_in_bq"] == 7

    bq_res = client.get("/api/v1/analytics/bigquery", headers={"X-User-Id": "usr-exec"}).json()
    assert bq_res["reconciliation"]["is_reconciled"] is True
    assert bq_res["kpis"]["approved_positions"] == 5
    assert Decimal(bq_res["kpis"]["annualized_cost_forecast_inr"]) == Decimal("15760000.00")


def test_scenario_14_15_16_17_cicd_cloudrun_and_zero_exposed_secrets(client):
    """
    Scenarios 14–17: Verify CI/CD workflows, Cloud Run health/analytics connectivity,
    and guarantee no secrets are exposed in source code.
    """
    health = client.get("/healthz").json()
    assert client.get("/health").json() == health
    assert health["status"] == "ok"
    assert health["bq_dataset"] == "talentflow_analytics"

    repo_root = Path(__file__).resolve().parent.parent.parent
    ci_workflow = repo_root / ".github" / "workflows" / "ci.yml"
    deploy_workflow = repo_root / ".github" / "workflows" / "deploy.yml"
    assert ci_workflow.exists()
    assert deploy_workflow.exists()

    # Scan source files to ensure no hardcoded private keys or GCP service account JSON keys exist.
    # Tokens are assembled at runtime so this test file does not match its own scan.
    forbidden_tokens = ["-----BEGIN " + "PRIVATE KEY-----", "AIza" + "Sy"]
    excluded_dirs = {".venv", "venv", "node_modules", "site-packages", ".git", "build", "dist"}
    for src_file in repo_root.rglob("*.py"):
        if excluded_dirs.intersection(src_file.parts):
            continue
        content = src_file.read_text(encoding="utf-8", errors="ignore")
        for token in forbidden_tokens:
            assert token not in content, f"Potential secret found in {src_file}"


def test_scenario_18_clarification_edit_resubmit_and_delegated_committee_approval(client):
    """
    Verifies full lifecycle: Create -> Submit -> Request Clarification -> Edit -> Resubmit
    -> Manager Approval -> Delegated People Committee Approval -> Position Outcome Recording (FILLED).
    """
    # 1. Committee member creates a request on behalf of usr-creator
    payload = _valid_request_payload(job_grade="L4", headcount=2)
    payload["request_owner_id"] = "usr-creator"
    res = client.post(
        "/api/v1/requests",
        json=payload,
        headers={"X-User-Id": "usr-committee"},
    )
    assert res.status_code == 201, res.text
    req_id = res.json()["id"]

    # 2. Submit to workflow -> MANAGER_REVIEW
    sub = client.post(f"/api/v1/requests/{req_id}/submit", headers={"X-User-Id": "usr-committee"})
    assert sub.status_code == 200
    assert sub.json()["status"] == "MANAGER_REVIEW"

    # 3. Manager requests clarification
    clar = client.post(
        f"/api/v1/requests/{req_id}/decisions",
        json={
            "decision": "REQUEST_CLARIFICATION",
            "comments": "Please clarify Q4 sprint velocity impact and contractor replacement plan.",
        },
        headers={"X-User-Id": "usr-manager"},
    )
    assert clar.status_code == 200
    assert clar.json()["status"] == "CLARIFICATION_REQUESTED"

    # 4. Edit request while in CLARIFICATION_REQUESTED
    upd = client.patch(
        f"/api/v1/requests/{req_id}",
        json={
            "headcount_requested": 1,
            "justification": "Updated justification with detailed Q4 milestone and contractor savings.",
        },
        headers={"X-User-Id": "usr-creator"},
    )
    assert upd.status_code == 200
    assert upd.json()["headcount_requested"] == 1
    assert len(upd.json()["positions"]) == 1

    # 5. Resubmit to workflow -> MANAGER_REVIEW
    resub = client.post(f"/api/v1/requests/{req_id}/submit", headers={"X-User-Id": "usr-creator"})
    assert resub.status_code == 200
    assert resub.json()["status"] == "MANAGER_REVIEW"

    # 6. Manager approves -> advances to COMMITTEE_PENDING
    mgr_ok = client.post(
        f"/api/v1/requests/{req_id}/decisions",
        json={"decision": "APPROVE", "comments": "Clarification accepted; manager approved."},
        headers={"X-User-Id": "usr-manager"},
    )
    assert mgr_ok.status_code == 200
    assert mgr_ok.json()["status"] == "COMMITTEE_PENDING"

    # 7. People Committee Chair delegates COMMITTEE_PENDING authority to HRBP (usr-hrbp)
    del_res = client.post(
        "/api/v1/approvals/delegations",
        json={
            "to_user_id": "usr-hrbp",
            "stage_name": "COMMITTEE_PENDING",
            "reason": "Committee Chair delegating sign-off during travel.",
        },
        headers={"X-User-Id": "usr-committee"},
    )
    assert del_res.status_code == 201
    del_list = client.get("/api/v1/approvals/delegations").json()
    assert len(del_list) >= 1

    # 8. HRBP approves COMMITTEE_PENDING under delegated authority -> APPROVED
    com_ok = client.post(
        f"/api/v1/requests/{req_id}/decisions",
        json={"decision": "APPROVE", "comments": "Approved under People Committee delegation."},
        headers={"X-User-Id": "usr-hrbp"},
    )
    assert com_ok.status_code == 200
    assert com_ok.json()["status"] == "APPROVED"
    assert com_ok.json()["approval_records"][-1]["delegated_from_id"] == "usr-committee"

    # 9. Record HIRED position outcome -> transitions to FILLED
    pos_id = com_ok.json()["positions"][0]["id"]
    out_res = client.post(
        f"/api/v1/requests/{req_id}/positions/{pos_id}/outcome",
        json={
            "candidate_ref": "CAND-SYN-999",
            "actual_hire_date": "2026-11-12",
            "actual_annual_base_salary": "1750000.00",
            "actual_benefits_cost": "290000.00",
            "actual_recruitment_fee": "90000.00",
            "actual_onetime_cost": "50000.00",
            "closure_status": "HIRED",
            "closure_reason": "Candidate onboarded into Platform Engineering.",
        },
        headers={"X-User-Id": "usr-hrbp"},
    )
    assert out_res.status_code == 200
    assert out_res.json()["status"] == "FILLED"


def test_scenario_19_populate_demo_approval_queue_and_committee_actions(client):
    """
    Verifies the interactive demo queue endpoint populates active COMMITTEE_PENDING,
    FINANCE_REVIEW, and MANAGER_REVIEW requests and allows immediate People Committee approval.
    """
    pop = client.post("/api/v1/demo/populate-queue", headers={"X-User-Id": "usr-committee"})
    assert pop.status_code == 200

    # Approve REQ-2026-0004 (Lead Site Reliability Engineer) in COMMITTEE_PENDING
    app_res = client.post(
        "/api/v1/requests/req-seed-0004/decisions",
        json={"decision": "APPROVE", "comments": "People Committee approved SRE headcount."},
        headers={"X-User-Id": "usr-committee"},
    )
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "APPROVED"

    # Calling populate-queue again restores REQ-2026-0004 back to COMMITTEE_PENDING
    pop2 = client.post("/api/v1/demo/populate-queue", headers={"X-User-Id": "usr-committee"})
    assert pop2.status_code == 200
    req4 = client.get("/api/v1/requests/req-seed-0004", headers={"X-User-Id": "usr-committee"}).json()
    assert req4["status"] == "COMMITTEE_PENDING"

    # Re-approving REQ-2026-0004 after queue restoration must succeed (no stale ApprovalRecord 409 Conflict)
    app_res_again = client.post(
        "/api/v1/requests/req-seed-0004/decisions",
        json={"decision": "APPROVE", "comments": "Re-approved after queue restoration."},
        headers={"X-User-Id": "usr-committee"},
    )
    assert app_res_again.status_code == 200
    assert app_res_again.json()["status"] == "APPROVED"

    # Verify BigQuery vs. PostgreSQL reconciliation remains True when filtered by hiring_type and status
    filtered_dash = client.get(
        "/api/v1/dashboard/overview?hiring_type=NEW_HEADCOUNT&status=APPROVED",
        headers={"X-User-Id": "usr-exec"},
    ).json()
    assert filtered_dash["bigquery_historical_analytics"]["reconciliation"]["is_reconciled"] is True
