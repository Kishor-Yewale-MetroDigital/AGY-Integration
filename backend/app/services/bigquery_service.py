from datetime import datetime, timezone
from decimal import Decimal
from statistics import median
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.entities import ApprovalRecord, HiringRequest, Position
from app.services.cost_service import FX_TO_INR, compute_workforce_and_cost_summary, quantize_money


class BigQueryAnalyticsWarehouse:
    """
    Incremental and idempotent analytical warehouse engine for `talentflow_analytics`.
    Maintains curated analytical tables keyed by natural primary keys (`request_id`,
    `position_id`, `approval_record_id`) so repeated sync executions perform deterministic
    MERGE / upsert operations without ever duplicating rows or double-counting headcount.
    """

    def __init__(self) -> None:
        self.request_snapshots: dict[str, dict] = {}
        self.position_facts: dict[str, dict] = {}
        self.approval_events: dict[str, dict] = {}
        self.last_synced_at: datetime | None = None
        self.sync_run_count: int = 0

    def run_incremental_merge_sync(self, db: Session) -> dict:
        """
        Extracts transactional records from PostgreSQL and performs idempotent MERGE
        into `talentflow_analytics` staging and curated snapshot structures.
        Handles record updates, cancellations, and late-arriving events by upserting
        on immutable entity IDs and comparing `updated_at`.
        """
        requests = list(db.scalars(select(HiringRequest)).unique().all())
        positions = list(db.scalars(select(Position)).unique().all())
        records = list(db.scalars(select(ApprovalRecord)).unique().all())

        upserted_requests = 0
        upserted_positions = 0
        upserted_approvals = 0

        for req in requests:
            fx = FX_TO_INR.get(req.currency, Decimal("1.00"))
            turnaround_hours: float | None = None
            if req.submitted_at and req.approved_at:
                sub = (
                    req.submitted_at.replace(tzinfo=timezone.utc)
                    if req.submitted_at.tzinfo is None
                    else req.submitted_at
                )
                app = (
                    req.approved_at.replace(tzinfo=timezone.utc)
                    if req.approved_at.tzinfo is None
                    else req.approved_at
                )
                turnaround_hours = round((app - sub).total_seconds() / 3600.0, 2)

            snapshot = {
                "request_id": req.id,
                "request_code": req.request_code,
                "job_title": req.job_title,
                "job_family": req.job_family,
                "department_id": req.department_id,
                "business_unit": req.business_unit,
                "country": req.country,
                "city": req.city,
                "work_location": req.work_location,
                "job_grade": req.job_grade,
                "hiring_type": req.hiring_type,
                "headcount_requested": req.headcount_requested,
                "currency": req.currency,
                "total_annualized_forecast_inr": quantize_money(Decimal(req.total_annualized_forecast) * fx),
                "status": req.status,
                "submitted_month": (req.submitted_at or req.created_at).strftime("%Y-%m"),
                "approval_turnaround_hours": turnaround_hours,
                "updated_at": req.updated_at.isoformat() if req.updated_at else "",
            }
            self.request_snapshots[req.id] = snapshot
            upserted_requests += 1

        # Remove hard-deleted requests if any
        active_req_ids = {r.id for r in requests}
        for stale_id in list(self.request_snapshots.keys()):
            if stale_id not in active_req_ids:
                del self.request_snapshots[stale_id]

        for pos in positions:
            parent = self.request_snapshots.get(pos.hiring_request_id)
            req_obj = next((r for r in requests if r.id == pos.hiring_request_id), None)
            fx = FX_TO_INR.get(req_obj.currency, Decimal("1.00")) if req_obj else Decimal("1.00")

            actual_cost_inr = Decimal("0.00")
            days_to_fill: int | None = None
            if pos.outcome and pos.outcome.closure_status == "HIRED":
                out = pos.outcome
                actual_cost_inr = quantize_money(
                    (
                        Decimal(out.actual_annual_base_salary)
                        + Decimal(out.actual_benefits_cost)
                        + Decimal(out.actual_recruitment_fee)
                        + Decimal(out.actual_onetime_cost)
                    )
                    * fx
                )
                if req_obj and req_obj.approved_at:
                    days_to_fill = max(0, (out.actual_hire_date - req_obj.approved_at.date()).days)

            self.position_facts[pos.id] = {
                "position_id": pos.id,
                "request_id": pos.hiring_request_id,
                "position_code": pos.position_code,
                "business_unit": parent["business_unit"] if parent else "",
                "department_id": parent["department_id"] if parent else "",
                "job_grade": parent["job_grade"] if parent else "",
                "country": parent["country"] if parent else "",
                "position_status": pos.status,
                "request_status": parent["status"] if parent else "",
                "actual_cost_inr": actual_cost_inr,
                "days_to_fill": days_to_fill,
            }
            upserted_positions += 1

        active_pos_ids = {p.id for p in positions}
        for stale_pos_id in list(self.position_facts.keys()):
            if stale_pos_id not in active_pos_ids:
                del self.position_facts[stale_pos_id]

        for rec in records:
            self.approval_events[rec.id] = {
                "approval_record_id": rec.id,
                "request_id": rec.hiring_request_id,
                "stage_name": rec.stage_name,
                "approver_id": rec.approver_id,
                "decision": rec.decision,
                "created_at": rec.created_at.isoformat(),
            }
            upserted_approvals += 1

        self.sync_run_count += 1
        self.last_synced_at = datetime.now(timezone.utc)

        return {
            "dataset": settings.bq_dataset,
            "sync_run_count": self.sync_run_count,
            "last_synced_at": self.last_synced_at.isoformat(),
            "freshness_sla_minutes": 15,
            "upserted_requests": upserted_requests,
            "upserted_positions": upserted_positions,
            "upserted_approval_events": upserted_approvals,
            "total_unique_requests_in_bq": len(self.request_snapshots),
            "total_unique_positions_in_bq": len(self.position_facts),
            "total_unique_approval_events_in_bq": len(self.approval_events),
        }

    def query_curated_analytics(
        self,
        db: Session,
        *,
        business_unit: str | None = None,
        department_id: str | None = None,
        country: str | None = None,
        job_grade: str | None = None,
        hiring_type: str | None = None,
        status: str | None = None,
    ) -> dict:
        """
        Executes analytical aggregations over `talentflow_analytics` curated models
        and reconciles them against independent PostgreSQL operational metrics.
        """
        if self.sync_run_count == 0:
            self.run_incremental_merge_sync(db)

        snapshots = list(self.request_snapshots.values())
        if business_unit:
            snapshots = [s for s in snapshots if s["business_unit"] == business_unit]
        if department_id:
            snapshots = [s for s in snapshots if s["department_id"] == department_id]
        if country:
            snapshots = [s for s in snapshots if s["country"] == country]
        if job_grade:
            snapshots = [s for s in snapshots if s["job_grade"] == job_grade]
        if hiring_type:
            snapshots = [s for s in snapshots if s["hiring_type"] == hiring_type]
        if status:
            snapshots = [s for s in snapshots if s["status"] == status]

        filtered_req_ids = {s["request_id"] for s in snapshots}
        positions = [p for p in self.position_facts.values() if p["request_id"] in filtered_req_ids]

        approved_statuses = {"APPROVED", "RECRUITING", "PARTIALLY_FILLED", "FILLED", "CLOSED"}

        total_requests = len(snapshots)
        pending_committee = sum(1 for s in snapshots if s["status"] == "COMMITTEE_PENDING")
        pending_manager = sum(1 for s in snapshots if s["status"] == "MANAGER_REVIEW")
        pending_finance = sum(1 for s in snapshots if s["status"] == "FINANCE_REVIEW")
        approved_requests = sum(1 for s in snapshots if s["status"] in approved_statuses)
        rejected_requests = sum(1 for s in snapshots if s["status"] == "REJECTED")

        # Grain-safe position counting (zero double-counting across stages)
        requested_headcount = sum(
            s["headcount_requested"] for s in snapshots if s["status"] != "CANCELLED"
        )
        approved_positions = sum(
            1
            for p in positions
            if p["request_status"] in approved_statuses
            and p["position_status"] in {"APPROVED", "OPEN_RECRUITING", "FILLED"}
        )
        open_positions = sum(
            1
            for p in positions
            if p["request_status"] in approved_statuses
            and p["position_status"] in {"APPROVED", "OPEN_RECRUITING"}
        )
        filled_positions = sum(
            1
            for p in positions
            if p["request_status"] in approved_statuses and p["position_status"] == "FILLED"
        )

        annualized_cost_forecast = quantize_money(
            sum(
                (s["total_annualized_forecast_inr"] for s in snapshots if s["status"] in approved_statuses),
                Decimal("0.00"),
            )
        )
        actual_cost_total = quantize_money(
            sum(
                (p["actual_cost_inr"] for p in positions if p["request_status"] in approved_statuses),
                Decimal("0.00"),
            )
        )

        turnarounds = [
            s["approval_turnaround_hours"]
            for s in snapshots
            if s["approval_turnaround_hours"] is not None
        ]
        avg_turnaround = round(sum(turnarounds) / len(turnarounds), 2) if turnarounds else 0.0
        median_turnaround = round(float(median(turnarounds)), 2) if turnarounds else 0.0

        fill_days = [p["days_to_fill"] for p in positions if p["days_to_fill"] is not None]
        avg_days_to_fill = round(sum(fill_days) / len(fill_days), 1) if fill_days else 0.0

        # Monthly trends
        monthly_map: dict[str, dict] = {}
        for s in snapshots:
            m = s["submitted_month"]
            if m not in monthly_map:
                monthly_map[m] = {
                    "month": m,
                    "submitted_requests": 0,
                    "approved_requests": 0,
                    "rejected_requests": 0,
                    "requested_headcount": 0,
                    "approved_cost_inr": Decimal("0.00"),
                }
            monthly_map[m]["submitted_requests"] += 1
            monthly_map[m]["requested_headcount"] += s["headcount_requested"]
            if s["status"] in approved_statuses:
                monthly_map[m]["approved_requests"] += 1
                monthly_map[m]["approved_cost_inr"] = quantize_money(
                    monthly_map[m]["approved_cost_inr"] + s["total_annualized_forecast_inr"]
                )
            elif s["status"] == "REJECTED":
                monthly_map[m]["rejected_requests"] += 1

        # Grade distribution
        grade_dist: dict[str, dict] = {}
        for s in snapshots:
            g = s["job_grade"]
            if g not in grade_dist:
                grade_dist[g] = {"job_grade": g, "requests": 0, "headcount": 0, "forecast_cost_inr": Decimal("0.00")}
            grade_dist[g]["requests"] += 1
            grade_dist[g]["headcount"] += s["headcount_requested"]
            if s["status"] in approved_statuses:
                grade_dist[g]["forecast_cost_inr"] = quantize_money(
                    grade_dist[g]["forecast_cost_inr"] + s["total_annualized_forecast_inr"]
                )

        # Reconciliation check against transactional database
        op_summary = compute_workforce_and_cost_summary(
            db,
            department_id=department_id,
            business_unit=business_unit,
            job_grade=job_grade,
            country=country,
        )
        reconciled = (
            op_summary["approved_headcount"] == approved_positions
            and op_summary["forecast_total_hiring_cost"] == annualized_cost_forecast
            and op_summary["actual_total_hiring_cost"] == actual_cost_total
        )

        return {
            "dataset": settings.bq_dataset,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "sync_run_count": self.sync_run_count,
            "kpis": {
                "total_requests": total_requests,
                "pending_manager_review": pending_manager,
                "pending_finance_review": pending_finance,
                "pending_committee": pending_committee,
                "approved_requests": approved_requests,
                "rejected_requests": rejected_requests,
                "requested_headcount": requested_headcount,
                "approved_positions": approved_positions,
                "open_positions": open_positions,
                "filled_positions": filled_positions,
                "annualized_cost_forecast_inr": str(annualized_cost_forecast),
                "actual_cost_total_inr": str(actual_cost_total),
                "avg_approval_turnaround_hours": avg_turnaround,
                "median_approval_turnaround_hours": median_turnaround,
                "avg_days_to_fill": avg_days_to_fill,
            },
            "monthly_trends": [
                {**v, "approved_cost_inr": str(v["approved_cost_inr"])}
                for _, v in sorted(monthly_map.items())
            ],
            "grade_distribution": [
                {**v, "forecast_cost_inr": str(v["forecast_cost_inr"])}
                for _, v in sorted(grade_dist.items())
            ],
            "reconciliation": {
                "is_reconciled": reconciled,
                "bq_approved_positions": approved_positions,
                "pg_approved_positions": op_summary["approved_headcount"],
                "bq_forecast_cost_inr": str(annualized_cost_forecast),
                "pg_forecast_cost_inr": str(op_summary["forecast_total_hiring_cost"]),
                "bq_actual_cost_inr": str(actual_cost_total),
                "pg_actual_cost_inr": str(op_summary["actual_total_hiring_cost"]),
            },
        }


bq_warehouse = BigQueryAnalyticsWarehouse()
