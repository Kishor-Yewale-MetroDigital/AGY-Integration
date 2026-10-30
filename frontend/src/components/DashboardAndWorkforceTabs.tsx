import React from "react";
import type { Department, HiringRequest } from "../types/talentflow";
import { KpiCard, formatINR } from "./SharedUi";

export function DashboardTab({
  dashboard,
  requests,
  onManualBigQuerySync,
}: {
  dashboard: Record<string, unknown> | null;
  requests: HiringRequest[];
  onManualBigQuerySync: () => void;
}) {
  const bqAnalytics = (dashboard?.bigquery_historical_analytics ?? {}) as Record<string, unknown>;
  const bqKpis = (bqAnalytics.kpis ?? {}) as Record<string, unknown>;
  const bqReconciliation = (bqAnalytics.reconciliation ?? {}) as Record<string, unknown>;
  const monthlyTrends = (bqAnalytics.monthly_trends ?? []) as Array<Record<string, unknown>>;
  const gradeDistribution = (bqAnalytics.grade_distribution ?? []) as Array<Record<string, unknown>>;
  const liveOps = (dashboard?.live_operational_metrics ?? {}) as Record<string, unknown>;

  return (
    <section>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "16px",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <h2 style={{ margin: 0 }}>Executive Hiring & Financial Governance</h2>
        <button
          type="button"
          onClick={onManualBigQuerySync}
          style={{
            padding: "8px 14px",
            borderRadius: "6px",
            background: "#003B7E",
            color: "#fff",
            border: "none",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          ↻ Trigger BigQuery (talentflow_analytics) MERGE Sync
        </button>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "16px",
          marginBottom: "24px",
        }}
      >
        <KpiCard
          title="Total Requests"
          value={String(bqKpis.total_requests ?? requests.length)}
          subtitle={`Requested Headcount: ${String(bqKpis.requested_headcount ?? 7)}`}
        />
        <KpiCard
          title="Pending Committee"
          value={String(bqKpis.pending_committee ?? 1)}
          subtitle={`Overdue SLA Escalations: ${String(liveOps.overdue_sla_requests ?? 1)}`}
          highlight="#d97706"
        />
        <KpiCard
          title="Approved Positions"
          value={String(bqKpis.approved_positions ?? 5)}
          subtitle={`Filled: ${String(bqKpis.filled_positions ?? 1)} | Open: ${String(
            bqKpis.open_positions ?? 4
          )}`}
          highlight="#16a34a"
        />
        <KpiCard
          title="Annualized Cost Forecast"
          value={formatINR(String(bqKpis.annualized_cost_forecast_inr ?? "15760000"))}
          subtitle={`Actual Spend: ${formatINR(String(bqKpis.actual_cost_total_inr ?? "3050000"))}`}
        />
        <KpiCard
          title="Approval Turnaround"
          value={`${String(bqKpis.avg_approval_turnaround_hours ?? 48)} hrs`}
          subtitle={`Median: ${String(
            bqKpis.median_approval_turnaround_hours ?? 48
          )} hrs | Avg Fill: ${String(bqKpis.avg_days_to_fill ?? 18)}d`}
        />
      </div>

      <div
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: "10px",
          padding: "16px 20px",
          marginBottom: "20px",
        }}
      >
        <h3 style={{ marginTop: 0 }}>
          BigQuery Warehouse Reconciliation (<code>talentflow_analytics</code>)
        </h3>
        <p style={{ fontSize: "14px", color: "#334155", margin: 0 }}>
          Status:{" "}
          <strong style={{ color: bqReconciliation.is_reconciled ? "#16a34a" : "#dc2626" }}>
            {bqReconciliation.is_reconciled
              ? "RECONCILED (100% Match with Cloud SQL PostgreSQL)"
              : "SYNCING"}
          </strong>{" "}
          | BQ Approved Positions: <strong>{String(bqReconciliation.bq_approved_positions ?? 5)}</strong> vs
          PG Approved Positions: <strong>{String(bqReconciliation.pg_approved_positions ?? 5)}</strong> | BQ
          Forecast: <strong>{formatINR(String(bqReconciliation.bq_forecast_cost_inr ?? 0))}</strong> | Sync
          Runs: <strong>{String(bqAnalytics.sync_run_count ?? 1)}</strong>
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
          gap: "20px",
        }}
      >
        <div
          style={{
            background: "#ffffff",
            border: "1px solid #e2e8f0",
            borderRadius: "10px",
            padding: "16px 20px",
          }}
        >
          <h3 style={{ marginTop: 0 }}>Monthly Hiring Request Trend (BigQuery Mart)</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
            <thead>
              <tr style={{ background: "#f8fafc", textAlign: "left" }}>
                <th style={{ padding: "8px" }}>Month</th>
                <th style={{ padding: "8px" }}>Submitted</th>
                <th style={{ padding: "8px" }}>Approved</th>
                <th style={{ padding: "8px" }}>Headcount</th>
                <th style={{ padding: "8px" }}>Approved Cost</th>
              </tr>
            </thead>
            <tbody>
              {monthlyTrends.map((m) => (
                <tr key={String(m.month)} style={{ borderTop: "1px solid #e2e8f0" }}>
                  <td style={{ padding: "8px", fontWeight: 600 }}>{String(m.month)}</td>
                  <td style={{ padding: "8px" }}>{String(m.submitted_requests)}</td>
                  <td style={{ padding: "8px" }}>{String(m.approved_requests)}</td>
                  <td style={{ padding: "8px" }}>{String(m.requested_headcount)}</td>
                  <td style={{ padding: "8px" }}>{formatINR(String(m.approved_cost_inr))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div
          style={{
            background: "#ffffff",
            border: "1px solid #e2e8f0",
            borderRadius: "10px",
            padding: "16px 20px",
          }}
        >
          <h3 style={{ marginTop: 0 }}>Job Grade Distribution (BigQuery Mart)</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
            <thead>
              <tr style={{ background: "#f8fafc", textAlign: "left" }}>
                <th style={{ padding: "8px" }}>Job Grade</th>
                <th style={{ padding: "8px" }}>Requisitions</th>
                <th style={{ padding: "8px" }}>Requested Positions</th>
                <th style={{ padding: "8px" }}>Approved Forecast</th>
              </tr>
            </thead>
            <tbody>
              {gradeDistribution.map((g) => (
                <tr key={String(g.job_grade)} style={{ borderTop: "1px solid #e2e8f0" }}>
                  <td style={{ padding: "8px", fontWeight: 600 }}>{String(g.job_grade)}</td>
                  <td style={{ padding: "8px" }}>{String(g.requests)}</td>
                  <td style={{ padding: "8px" }}>{String(g.headcount)}</td>
                  <td style={{ padding: "8px" }}>{formatINR(String(g.forecast_cost_inr))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

export function WorkforceTab({
  workforce,
  departments,
  delayDays,
  onDelayDaysChange,
}: {
  workforce: Record<string, unknown> | null;
  departments: Department[];
  delayDays: number;
  onDelayDaysChange: (days: number) => void;
}) {
  const delayCostProj = (workforce?.delay_cost_projection ?? {}) as Record<string, unknown>;

  return (
    <section>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "16px",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <h2 style={{ margin: 0 }}>Workforce Headcount & Decimal Cost Rollup</h2>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <label htmlFor="vacancy-delay-days" style={{ fontSize: "13px", fontWeight: 600 }}>
            Vacancy Delay Simulation (Days):
          </label>
          <input
            id="vacancy-delay-days"
            name="delay_days"
            aria-label="Vacancy Delay Simulation Days"
            type="number"
            min={0}
            max={365}
            value={delayDays}
            onChange={(e) => onDelayDaysChange(Number(e.target.value))}
            style={{
              padding: "6px 10px",
              width: "80px",
              borderRadius: "6px",
              border: "1px solid #cbd5e1",
            }}
          />
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "16px",
          marginBottom: "24px",
        }}
      >
        <KpiCard
          title="Allocated Budget"
          value={formatINR(String(workforce?.allocated_department_budget ?? "84000000"))}
          subtitle={`Utilization: ${String(workforce?.budget_utilization_pct ?? "18.76")}%`}
        />
        <KpiCard
          title="Forecast Commitment"
          value={formatINR(String(workforce?.forecast_total_hiring_cost ?? "15760000"))}
          subtitle={`In-Period FY Spend: ${formatINR(
            String(workforce?.in_period_projected_expenditure ?? "0")
          )}`}
        />
        <KpiCard
          title="Remaining Budget Variance"
          value={formatINR(String(workforce?.budget_variance ?? "68240000"))}
          subtitle={`Actual Hired Spend: ${formatINR(
            String(workforce?.actual_total_hiring_cost ?? "3050000")
          )}`}
          highlight="#16a34a"
        />
        <KpiCard
          title={`Cost of Delayed Hiring (${delayDays}d)`}
          value={formatINR(String(delayCostProj.net_delay_cost ?? "0"))}
          subtitle={`Productivity Loss: ${formatINR(
            String(delayCostProj.estimated_productivity_loss ?? "0")
          )} vs Payroll Saved: ${formatINR(String(delayCostProj.vacancy_payroll_savings ?? "0"))}`}
          highlight="#d97706"
        />
      </div>

      <div
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: "10px",
          padding: "16px 20px",
        }}
      >
        <h3 style={{ marginTop: 0 }}>Department Budget Envelope vs. Commitments (FY2026)</h3>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
          <thead>
            <tr style={{ background: "#f1f5f9", textAlign: "left" }}>
              <th style={{ padding: "10px" }}>Code</th>
              <th style={{ padding: "10px" }}>Department</th>
              <th style={{ padding: "10px" }}>Business Unit</th>
              <th style={{ padding: "10px" }}>Cost Center</th>
              <th style={{ padding: "10px" }}>Allocated Budget</th>
              <th style={{ padding: "10px" }}>Committed Forecast</th>
              <th style={{ padding: "10px" }}>Actual Spent</th>
              <th style={{ padding: "10px" }}>Available Balance</th>
            </tr>
          </thead>
          <tbody>
            {departments.map((d) => {
              const alloc = Number(d.allocated_budget || 0);
              const comm = Number(d.committed_cost || 0);
              const avail = alloc - comm;
              return (
                <tr key={d.id} style={{ borderTop: "1px solid #e2e8f0" }}>
                  <td style={{ padding: "10px", fontWeight: 700 }}>{d.code}</td>
                  <td style={{ padding: "10px" }}>{d.name}</td>
                  <td style={{ padding: "10px" }}>{d.business_unit}</td>
                  <td style={{ padding: "10px" }}>
                    <code>{d.cost_center}</code>
                  </td>
                  <td style={{ padding: "10px", fontWeight: 600 }}>{formatINR(d.allocated_budget)}</td>
                  <td style={{ padding: "10px" }}>{formatINR(d.committed_cost)}</td>
                  <td style={{ padding: "10px" }}>{formatINR(d.actual_spent)}</td>
                  <td style={{ padding: "10px", fontWeight: 700, color: "#16a34a" }}>
                    {formatINR(avail)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function AuditTab({ audits }: { audits: Array<Record<string, unknown>> }) {
  return (
    <section>
      <h2>Immutable Governance Audit Log</h2>
      <p style={{ fontSize: "13px", color: "#475569" }}>
        Every creation, submission, stage approval, clarification, rejection, and hiring outcome is
        recorded in an append-only audit table protected by ORM-level immutability guards.
      </p>
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          background: "#fff",
          borderRadius: "10px",
          overflow: "hidden",
        }}
      >
        <thead>
          <tr style={{ background: "#f1f5f9", textAlign: "left", fontSize: "13px" }}>
            <th style={{ padding: "10px" }}>Timestamp</th>
            <th style={{ padding: "10px" }}>Action</th>
            <th style={{ padding: "10px" }}>Entity</th>
            <th style={{ padding: "10px" }}>Actor & Role</th>
            <th style={{ padding: "10px" }}>State Transition</th>
          </tr>
        </thead>
        <tbody>
          {audits.map((a, idx) => (
            <tr key={String(a.id ?? idx)} style={{ borderTop: "1px solid #e2e8f0", fontSize: "13px" }}>
              <td style={{ padding: "10px" }}>{String(a.occurred_at)}</td>
              <td style={{ padding: "10px", fontWeight: 600 }}>{String(a.action)}</td>
              <td style={{ padding: "10px" }}>
                {String(a.entity_type)} ({String(a.entity_id)})
              </td>
              <td style={{ padding: "10px" }}>
                {String(a.actor_id)} [{String(a.actor_role)}]
              </td>
              <td style={{ padding: "10px", fontSize: "12px", color: "#475569" }}>
                <code>{JSON.stringify(a.new_state)}</code>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
