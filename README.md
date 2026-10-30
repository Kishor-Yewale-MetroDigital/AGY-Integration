# TalentFlow — Enterprise Hiring & People Committee Platform

Production-grade enterprise web application for managing hiring requisitions, workforce planning, configurable People Committee approvals, recruitment outcomes, and BigQuery hiring cost analytics.

## Architecture & Modules

1. **Module 1 — Hiring Request Management**: Multi-position requisitions, mandatory business case validation, currency & decimal cost modeling.
2. **Module 2 — People Committee Approval Workflow**: Configurable multi-stage approval engine (`DRAFT` → `SUBMITTED` → `MANAGER_REVIEW` → `FINANCE_REVIEW` [conditional] → `COMMITTEE_PENDING` → `APPROVED` / `REJECTED` / `CLARIFICATION_REQUESTED` → `RECRUITING` → `PARTIALLY_FILLED` / `FILLED` → `CLOSED`), Segregation of Duties (SoD), delegation, and SLA overdue escalation.
3. **Module 3 — Workforce & Cost Planning**: `Decimal`-based annualized salary commitments, employer benefits, one-time recruitment fees, prorated in-period expenditure, budget utilization/variance, and delayed hiring cost calculator.
4. **Module 4 — Executive Dashboard**: Real-time operational metrics alongside historical BigQuery analytics with multi-dimensional filtering and drill-down.
5. **Module 5 — BigQuery Analytics (`talentflow_analytics`)**: Incremental, idempotent `MERGE` pipeline from PostgreSQL into BigQuery staging and curated analytical views/marts.
6. **Module 6 — RBAC & Immutable Audit Trail**: 7 enterprise roles enforced in the backend with append-only audit history.
7. **Module 8 — Pay-When-In-Use GCP Deployment**: Cloud Run (`min-instances=0`), Cloud SQL PostgreSQL (`db-f1-micro` with on-demand Start/Auto-Stop workflow), BigQuery, Artifact Registry, Secret Manager, and GitHub Actions Workload Identity Federation (WIF).

## Financial & Analytical Assumptions

- **Monetary Precision**: All monetary fields use `NUMERIC(18, 2)` in PostgreSQL/BigQuery and `Decimal` in Python (zero floating-point arithmetic).
- **Annualized Cost per Position**: `est_annual_salary_per_pos + est_benefits_cost_per_pos`.
- **Total First-Year Forecast**: `(est_annual_salary_per_pos + est_benefits_cost_per_pos + est_recruitment_fee_per_pos + est_onetime_cost_per_pos) * headcount_requested`.
- **In-Period Expenditure**: Prorated by remaining days in the fiscal year from `target_hiring_date` (or `actual_hire_date`) plus 100% of one-time and recruitment fees incurred upon hire.
- **BigQuery Freshness SLA**: 15-minute incremental sync watermark using `updated_at` and idempotent `MERGE` keys (`request_id`, `position_id`, `approval_record_id`).

## Quickstart

### Backend (FastAPI + SQLAlchemy + Pytest)
```bash
cd backend
pip install -e ".[dev]"
alembic upgrade head
pytest -v
uvicorn app.main:app --reload --port 8000
```

### Frontend (React + TypeScript + Vite + Vitest)
```bash
cd frontend
npm install
npm test -- --run
npm run dev
```
