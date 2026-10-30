import React from "react";
import type {
  ApprovalDelegation,
  ApprovalRule,
  HiringRequest,
  User,
} from "../types/talentflow";
import { StatusBadge, formatINR } from "./SharedUi";

export function CommitteeQueueTab({
  queueRequests,
  users,
  delegations,
  rules,
  autoSelectStageApprover,
  onAutoSelectStageApproverChange,
  showOnlyPendingQueue,
  onShowOnlyPendingQueueChange,
  decisionComment,
  onDecisionCommentChange,
  onDecision,
  onFastTrackToCommittee,
  onSubmitExistingRequest,
  delegateStage,
  onDelegateStageChange,
  delegateToUserId,
  onDelegateToUserIdChange,
  delegateReason,
  onDelegateReasonChange,
  onCreateDelegation,
  newRuleName,
  onNewRuleNameChange,
  newRuleMinGrade,
  onNewRuleMinGradeChange,
  newRuleMinCost,
  onNewRuleMinCostChange,
  newRuleSla,
  onNewRuleSlaChange,
  newRuleFinanceGate,
  onNewRuleFinanceGateChange,
  onCreateRule,
  onToggleRuleActive,
  onDeleteRule,
}: {
  queueRequests: HiringRequest[];
  users: User[];
  delegations: ApprovalDelegation[];
  rules: ApprovalRule[];
  autoSelectStageApprover: boolean;
  onAutoSelectStageApproverChange: (val: boolean) => void;
  showOnlyPendingQueue: boolean;
  onShowOnlyPendingQueueChange: (val: boolean) => void;
  decisionComment: string;
  onDecisionCommentChange: (val: string) => void;
  onDecision: (
    req: HiringRequest,
    decision: "APPROVE" | "REJECT" | "REQUEST_CLARIFICATION"
  ) => void;
  onFastTrackToCommittee: (req: HiringRequest) => void;
  onSubmitExistingRequest: (req: HiringRequest) => void;
  delegateStage: "MANAGER_REVIEW" | "FINANCE_REVIEW" | "COMMITTEE_PENDING";
  onDelegateStageChange: (
    val: "MANAGER_REVIEW" | "FINANCE_REVIEW" | "COMMITTEE_PENDING"
  ) => void;
  delegateToUserId: string;
  onDelegateToUserIdChange: (val: string) => void;
  delegateReason: string;
  onDelegateReasonChange: (val: string) => void;
  onCreateDelegation: (e: React.FormEvent) => void;
  newRuleName: string;
  onNewRuleNameChange: (val: string) => void;
  newRuleMinGrade: string;
  onNewRuleMinGradeChange: (val: string) => void;
  newRuleMinCost: string;
  onNewRuleMinCostChange: (val: string) => void;
  newRuleSla: number;
  onNewRuleSlaChange: (val: number) => void;
  newRuleFinanceGate: boolean;
  onNewRuleFinanceGateChange: (val: boolean) => void;
  onCreateRule: (e: React.FormEvent) => void;
  onToggleRuleActive?: (rule: ApprovalRule) => void;
  onDeleteRule?: (ruleId: string) => void;
}) {
  return (
    <section>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          marginBottom: "12px",
        }}
      >
        <div>
          <h2 style={{ margin: 0 }}>People Committee & Multi-Stage Approval Queue</h2>
          <p style={{ color: "#475569", margin: "4px 0 0 0", fontSize: "13px" }}>
            Enforces Role-Based Access Control (RBAC), Segregation of Duties (SoD), and mandatory
            Finance Review gates before People Committee approval.
          </p>
        </div>
        <div style={{ display: "flex", gap: "14px", alignItems: "center", flexWrap: "wrap" }}>
          <label
            style={{
              fontSize: "13px",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: "6px",
              cursor: "pointer",
              background: "#eff6ff",
              padding: "6px 12px",
              borderRadius: "6px",
              border: "1px solid #bfdbfe",
            }}
          >
            <input
              type="checkbox"
              checked={autoSelectStageApprover}
              onChange={(e) => onAutoSelectStageApproverChange(e.target.checked)}
            />
            Auto-Select Authorized Stage Approver (Seamless Single-Click Testing)
          </label>
          <label
            style={{
              fontSize: "13px",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              cursor: "pointer",
            }}
          >
            <input
              type="checkbox"
              checked={showOnlyPendingQueue}
              onChange={(e) => onShowOnlyPendingQueueChange(e.target.checked)}
            />
            Show Active Pending Only
          </label>
        </div>
      </div>

      <div
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: "10px",
          padding: "14px 16px",
          marginBottom: "18px",
        }}
      >
        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", alignItems: "center" }}>
          <input
            aria-label="Decision / Rejection / Clarification Reason"
            placeholder="Enter approval comment, clarification request, or rejection justification (auto-filled if left blank)..."
            value={decisionComment}
            onChange={(e) => onDecisionCommentChange(e.target.value)}
            style={{
              flex: 1,
              minWidth: "280px",
              padding: "9px 12px",
              borderRadius: "6px",
              border: "1px solid #cbd5e1",
            }}
          />
          <button
            type="button"
            onClick={() =>
              onDecisionCommentChange(
                "Approved by People Committee: Strategic FY2026 headcount validated within department budget."
              )
            }
            style={{
              padding: "7px 10px",
              fontSize: "12px",
              borderRadius: "6px",
              border: "1px solid #86efac",
              background: "#f0fdf4",
              color: "#166534",
              cursor: "pointer",
            }}
          >
            Preset: Approve Note
          </button>
          <button
            type="button"
            onClick={() =>
              onDecisionCommentChange(
                "Clarification requested: Please confirm Q4 onboarding timeline and vendor replacement savings."
              )
            }
            style={{
              padding: "7px 10px",
              fontSize: "12px",
              borderRadius: "6px",
              border: "1px solid #fde047",
              background: "#fefce8",
              color: "#854d0e",
              cursor: "pointer",
            }}
          >
            Preset: Clarification Note
          </button>
          <button
            type="button"
            onClick={() =>
              onDecisionCommentChange(
                "Rejected by People Committee: Deferred to Q1 next fiscal year due to cost center prioritization."
              )
            }
            style={{
              padding: "7px 10px",
              fontSize: "12px",
              borderRadius: "6px",
              border: "1px solid #fca5a5",
              background: "#fef2f2",
              color: "#991b1b",
              cursor: "pointer",
            }}
          >
            Preset: Rejection Note
          </button>
        </div>
      </div>

      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          background: "#fff",
          borderRadius: "10px",
          overflow: "hidden",
          marginBottom: "28px",
        }}
      >
        <thead>
          <tr style={{ background: "#f1f5f9", textAlign: "left", fontSize: "13px" }}>
            <th style={{ padding: "12px" }}>Code</th>
            <th style={{ padding: "12px" }}>Role & Justification</th>
            <th style={{ padding: "12px" }}>Grade & Forecast</th>
            <th style={{ padding: "12px" }}>Workflow Pipeline Progress</th>
            <th style={{ padding: "12px" }}>Active Stage & Required Role</th>
            <th style={{ padding: "12px" }}>Committee & Stage Actions</th>
          </tr>
        </thead>
        <tbody>
          {queueRequests.map((r) => {
            const activeStep = r.approval_steps.find((s) => s.step_status === "ACTIVE");
            const isOverdue = Boolean(activeStep?.is_overdue);
            const canResubmit = r.status === "DRAFT" || r.status === "CLARIFICATION_REQUESTED";

            return (
              <tr key={r.id} style={{ borderTop: "1px solid #e2e8f0", fontSize: "14px" }}>
                <td style={{ padding: "12px", fontWeight: 600 }}>{r.request_code}</td>
                <td style={{ padding: "12px" }}>
                  <div style={{ fontWeight: 600 }}>{r.job_title}</div>
                  <div style={{ fontSize: "12px", color: "#64748b" }}>{r.justification}</div>
                </td>
                <td style={{ padding: "12px" }}>
                  <div>
                    <strong>{r.job_grade}</strong> • {r.headcount_requested} pos
                  </div>
                  <div style={{ fontWeight: 700, color: "#0f172a" }}>
                    {formatINR(r.total_annualized_forecast)}
                  </div>
                </td>
                <td style={{ padding: "12px", fontSize: "12px" }}>
                  {r.approval_steps.length === 0 ? (
                    <span style={{ color: "#64748b" }}>Completed / Pre-seeded</span>
                  ) : (
                    r.approval_steps.map((s) => (
                      <div key={s.id} style={{ marginBottom: "3px" }}>
                        <span
                          style={{
                            display: "inline-block",
                            width: "8px",
                            height: "8px",
                            borderRadius: "50%",
                            marginRight: "6px",
                            background:
                              s.step_status === "APPROVED"
                                ? "#16a34a"
                                : s.step_status === "ACTIVE"
                                ? "#2563eb"
                                : s.step_status === "REJECTED"
                                ? "#dc2626"
                                : "#94a3b8",
                          }}
                        />
                        {s.sequence_order}. {s.stage_name}: <strong>{s.step_status}</strong>
                      </div>
                    ))
                  )}
                </td>
                <td style={{ padding: "12px" }}>
                  <StatusBadge status={r.status} />
                  {activeStep && (
                    <div style={{ fontSize: "12px", color: "#334155", marginTop: "4px" }}>
                      Requires: <strong>{activeStep.required_role}</strong>
                    </div>
                  )}
                  {isOverdue && (
                    <span
                      style={{
                        display: "inline-block",
                        marginTop: "4px",
                        background: "#fef2f2",
                        color: "#dc2626",
                        padding: "2px 8px",
                        borderRadius: "99px",
                        fontSize: "11px",
                        fontWeight: 700,
                      }}
                    >
                      OVERDUE SLA
                    </span>
                  )}
                </td>
                <td style={{ padding: "12px" }}>
                  {activeStep ? (
                    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                      <button
                        type="button"
                        onClick={() => onDecision(r, "APPROVE")}
                        style={{
                          padding: "6px 12px",
                          background: "#16a34a",
                          color: "#fff",
                          border: "none",
                          borderRadius: "6px",
                          cursor: "pointer",
                          fontWeight: 600,
                        }}
                      >
                        {activeStep.stage_name === "COMMITTEE_PENDING"
                          ? "Approve (Committee)"
                          : `Approve (${activeStep.stage_name})`}
                      </button>
                      {activeStep.stage_name !== "COMMITTEE_PENDING" && (
                        <button
                          type="button"
                          onClick={() => onFastTrackToCommittee(r)}
                          style={{
                            padding: "6px 10px",
                            background: "#003B7E",
                            color: "#fff",
                            border: "none",
                            borderRadius: "6px",
                            cursor: "pointer",
                            fontSize: "12px",
                            fontWeight: 600,
                          }}
                        >
                          Fast-Track to Committee
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => onDecision(r, "REQUEST_CLARIFICATION")}
                        style={{
                          padding: "6px 12px",
                          background: "#d97706",
                          color: "#fff",
                          border: "none",
                          borderRadius: "6px",
                          cursor: "pointer",
                          fontWeight: 600,
                        }}
                      >
                        Clarify
                      </button>
                      <button
                        type="button"
                        onClick={() => onDecision(r, "REJECT")}
                        style={{
                          padding: "6px 12px",
                          background: "#dc2626",
                          color: "#fff",
                          border: "none",
                          borderRadius: "6px",
                          cursor: "pointer",
                          fontWeight: 600,
                        }}
                      >
                        Reject
                      </button>
                    </div>
                  ) : canResubmit ? (
                    <button
                      type="button"
                      onClick={() => onSubmitExistingRequest(r)}
                      style={{
                        padding: "6px 12px",
                        background: "#003B7E",
                        color: "#fff",
                        border: "none",
                        borderRadius: "6px",
                        cursor: "pointer",
                        fontWeight: 600,
                      }}
                    >
                      Resubmit to Approval Queue
                    </button>
                  ) : (
                    <span style={{ fontSize: "12px", color: "#64748b", fontWeight: 600 }}>
                      ✓ Decision Complete ({r.status})
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

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
          <h3 style={{ marginTop: 0 }}>Delegate Stage Approval Authority</h3>
          <form
            onSubmit={onCreateDelegation}
            style={{ display: "grid", gap: "10px", marginBottom: "14px" }}
          >
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
              <select
                id="delegate-stage"
                name="stage_name"
                aria-label="Delegation Stage"
                value={delegateStage}
                onChange={(e) =>
                  onDelegateStageChange(
                    e.target.value as
                      | "MANAGER_REVIEW"
                      | "FINANCE_REVIEW"
                      | "COMMITTEE_PENDING"
                  )
                }
                style={{ padding: "7px", borderRadius: "6px", border: "1px solid #cbd5e1" }}
              >
                <option value="COMMITTEE_PENDING">COMMITTEE_PENDING</option>
                <option value="FINANCE_REVIEW">FINANCE_REVIEW</option>
                <option value="MANAGER_REVIEW">MANAGER_REVIEW</option>
              </select>
              <select
                id="delegate-to-user"
                name="to_user_id"
                aria-label="Delegate To User"
                value={delegateToUserId}
                onChange={(e) => onDelegateToUserIdChange(e.target.value)}
                style={{
                  padding: "7px",
                  borderRadius: "6px",
                  border: "1px solid #cbd5e1",
                  flex: 1,
                }}
              >
                {users
                  .filter((u) => u.is_active !== false)
                  .map((u) => (
                    <option key={u.id} value={u.id}>
                      Delegate To: {u.full_name} [{u.role}]
                    </option>
                  ))}
              </select>
            </div>
            <div style={{ display: "flex", gap: "10px" }}>
              <input
                id="delegate-reason"
                name="reason"
                aria-label="Delegation Reason"
                value={delegateReason}
                onChange={(e) => onDelegateReasonChange(e.target.value)}
                placeholder="Delegation reason (min 5 chars)"
                style={{
                  flex: 1,
                  padding: "7px 10px",
                  borderRadius: "6px",
                  border: "1px solid #cbd5e1",
                }}
              />
              <button
                type="submit"
                style={{
                  padding: "7px 14px",
                  background: "#003B7E",
                  color: "#fff",
                  border: "none",
                  borderRadius: "6px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Grant Delegation
              </button>
            </div>
          </form>
          <div style={{ fontSize: "12px", color: "#475569" }}>
            <strong>Active Delegations ({delegations.length}):</strong>
            {delegations.length === 0 ? (
              <div>No custom delegations active.</div>
            ) : (
              <ul style={{ margin: "4px 0 0 0", paddingLeft: "18px" }}>
                {delegations.map((d) => (
                  <li key={d.id}>
                    Stage <strong>{d.stage_name}</strong>: <code>{d.from_user_id}</code> →{" "}
                    <code>{d.to_user_id}</code> ({d.reason})
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div
          style={{
            background: "#ffffff",
            border: "1px solid #e2e8f0",
            borderRadius: "10px",
            padding: "16px 20px",
          }}
        >
          <h3 style={{ marginTop: 0 }}>Configurable Governance & Approval Rules</h3>
          <form
            onSubmit={onCreateRule}
            style={{
              display: "flex",
              gap: "8px",
              flexWrap: "wrap",
              alignItems: "center",
              marginBottom: "12px",
            }}
          >
            <input
              id="new-rule-name"
              name="rule_name"
              aria-label="Rule Name"
              value={newRuleName}
              onChange={(e) => onNewRuleNameChange(e.target.value)}
              placeholder="Rule Name (e.g. Executive L7+ Fast-Track)"
              required
              style={{
                padding: "6px 10px",
                borderRadius: "6px",
                border: "1px solid #cbd5e1",
                flex: 1,
                minWidth: "180px",
              }}
            />
            <select
              id="new-rule-min-grade"
              name="min_grade"
              aria-label="Minimum Job Grade"
              value={newRuleMinGrade}
              onChange={(e) => onNewRuleMinGradeChange(e.target.value)}
              style={{ padding: "6px", borderRadius: "6px", border: "1px solid #cbd5e1" }}
            >
              <option value="ANY">Any Grade</option>
              {["L3", "L4", "L5", "L6", "L7", "L8", "EXEC"].map((g) => (
                <option key={g} value={g}>
                  Min {g}
                </option>
              ))}
            </select>
            <input
              id="new-rule-min-cost"
              name="min_total_cost"
              aria-label="Minimum Cost INR"
              value={newRuleMinCost}
              onChange={(e) => onNewRuleMinCostChange(e.target.value)}
              placeholder="Min Cost INR"
              style={{
                padding: "6px 8px",
                borderRadius: "6px",
                border: "1px solid #cbd5e1",
                width: "110px",
              }}
            />
            <input
              id="new-rule-sla"
              name="sla_hours"
              aria-label="SLA Hours"
              type="number"
              min={1}
              max={720}
              value={newRuleSla}
              onChange={(e) => onNewRuleSlaChange(Number(e.target.value))}
              style={{
                padding: "6px 8px",
                borderRadius: "6px",
                border: "1px solid #cbd5e1",
                width: "65px",
              }}
            />
            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: "4px",
                fontSize: "12px",
                fontWeight: 600,
                color: "#334155",
                cursor: "pointer",
              }}
            >
              <input
                id="new-rule-finance-gate"
                name="requires_finance_review"
                aria-label="Require Finance Gate"
                type="checkbox"
                checked={newRuleFinanceGate}
                onChange={(e) => onNewRuleFinanceGateChange(e.target.checked)}
              />
              Finance Gate
            </label>
            <button
              type="submit"
              style={{
                padding: "6px 12px",
                background: "#003B7E",
                color: "#fff",
                border: "none",
                borderRadius: "6px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              + Add Rule
            </button>
          </form>
          <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "12px", color: "#334155" }}>
            {rules.map((rl) => (
              <li
                key={rl.id}
                style={{
                  marginBottom: "6px",
                  opacity: rl.is_active === false ? 0.55 : 1,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: "8px",
                    flexWrap: "wrap",
                  }}
                >
                  <span>
                    <strong>{rl.rule_name}</strong> — Min Grade: {rl.min_grade || "Any"}, Min Cost:{" "}
                    {formatINR(rl.min_total_cost)}, Finance Gate:{" "}
                    <strong>{rl.requires_finance_review ? "YES" : "NO"}</strong>, SLA:{" "}
                    {rl.sla_hours}h{" "}
                    {rl.is_active === false && (
                      <span style={{ color: "#b91c1c", fontWeight: 700 }}>(Paused)</span>
                    )}
                  </span>
                  <span style={{ display: "inline-flex", gap: "6px" }}>
                    {onToggleRuleActive && (
                      <button
                        type="button"
                        onClick={() => onToggleRuleActive(rl)}
                        style={{
                          padding: "2px 8px",
                          fontSize: "11px",
                          borderRadius: "4px",
                          border: "1px solid #cbd5e1",
                          background: rl.is_active === false ? "#dcfce7" : "#f8fafc",
                          color: rl.is_active === false ? "#166534" : "#334155",
                          cursor: "pointer",
                          fontWeight: 600,
                        }}
                      >
                        {rl.is_active === false ? "Enable" : "Pause"}
                      </button>
                    )}
                    {onDeleteRule && (
                      <button
                        type="button"
                        onClick={() => onDeleteRule(rl.id)}
                        style={{
                          padding: "2px 8px",
                          fontSize: "11px",
                          borderRadius: "4px",
                          border: "1px solid #fecaca",
                          background: "#fef2f2",
                          color: "#991b1b",
                          cursor: "pointer",
                          fontWeight: 600,
                        }}
                      >
                        Remove
                      </button>
                    )}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
