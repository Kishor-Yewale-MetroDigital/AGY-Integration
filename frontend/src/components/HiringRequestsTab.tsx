import React from "react";
import type { Department, HiringRequest } from "../types/talentflow";
import { StatusBadge, formatINR } from "./SharedUi";

export function HiringRequestsTab({
  requests,
  departments,
  jobTitle,
  onJobTitleChange,
  jobFamily,
  onJobFamilyChange,
  deptId,
  onDeptIdChange,
  jobGrade,
  onJobGradeChange,
  hiringType,
  onHiringTypeChange,
  workLocation,
  onWorkLocationChange,
  city,
  onCityChange,
  headcount,
  onHeadcountChange,
  salary,
  onSalaryChange,
  benefits,
  onBenefitsChange,
  targetHiringDate,
  onTargetHiringDateChange,
  requestedStartDate,
  onRequestedStartDateChange,
  justification,
  onJustificationChange,
  impact,
  onImpactChange,
  onCreateRequest,
  editingRequest,
  onCancelEdit,
  editTitle,
  onEditTitleChange,
  editHeadcount,
  onEditHeadcountChange,
  editSalary,
  onEditSalaryChange,
  editJustification,
  onEditJustificationChange,
  onSaveEditedRequest,
  onStartEditRequest,
  onSubmitExistingRequest,
  onApproveStage,
  expandedRequestId,
  onToggleExpandRequest,
  candidateRef,
  onCandidateRefChange,
  actualHireDate,
  onActualHireDateChange,
  actualSalary,
  onActualSalaryChange,
  outcomeReason,
  onOutcomeReasonChange,
  onRecordPositionOutcome,
}: {
  requests: HiringRequest[];
  departments: Department[];
  jobTitle: string;
  onJobTitleChange: (val: string) => void;
  jobFamily: string;
  onJobFamilyChange: (val: string) => void;
  deptId: string;
  onDeptIdChange: (val: string) => void;
  jobGrade: "L3" | "L4" | "L5" | "L6" | "L7" | "L8" | "EXEC";
  onJobGradeChange: (val: "L3" | "L4" | "L5" | "L6" | "L7" | "L8" | "EXEC") => void;
  hiringType: "NEW_HEADCOUNT" | "REPLACEMENT";
  onHiringTypeChange: (val: "NEW_HEADCOUNT" | "REPLACEMENT") => void;
  workLocation: "HYBRID" | "ONSITE" | "REMOTE";
  onWorkLocationChange: (val: "HYBRID" | "ONSITE" | "REMOTE") => void;
  city: string;
  onCityChange: (val: string) => void;
  headcount: number;
  onHeadcountChange: (val: number) => void;
  salary: string;
  onSalaryChange: (val: string) => void;
  benefits: string;
  onBenefitsChange: (val: string) => void;
  targetHiringDate: string;
  onTargetHiringDateChange: (val: string) => void;
  requestedStartDate: string;
  onRequestedStartDateChange: (val: string) => void;
  justification: string;
  onJustificationChange: (val: string) => void;
  impact: string;
  onImpactChange: (val: string) => void;
  onCreateRequest: (e: React.FormEvent, submitImmediately: boolean) => void;
  editingRequest: HiringRequest | null;
  onCancelEdit: () => void;
  editTitle: string;
  onEditTitleChange: (val: string) => void;
  editHeadcount: number;
  onEditHeadcountChange: (val: number) => void;
  editSalary: string;
  onEditSalaryChange: (val: string) => void;
  editJustification: string;
  onEditJustificationChange: (val: string) => void;
  onSaveEditedRequest: (e: React.FormEvent) => void;
  onStartEditRequest: (req: HiringRequest) => void;
  onSubmitExistingRequest: (req: HiringRequest) => void;
  onApproveStage: (req: HiringRequest) => void;
  expandedRequestId: string | null;
  onToggleExpandRequest: (reqId: string | null) => void;
  candidateRef: string;
  onCandidateRefChange: (val: string) => void;
  actualHireDate: string;
  onActualHireDateChange: (val: string) => void;
  actualSalary: string;
  onActualSalaryChange: (val: string) => void;
  outcomeReason: string;
  onOutcomeReasonChange: (val: string) => void;
  onRecordPositionOutcome: (
    reqId: string,
    posId: string,
    closureStatus: "HIRED" | "CANCELLED"
  ) => void;
}) {
  return (
    <section>
      <div
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: "10px",
          padding: "20px",
          marginBottom: "24px",
        }}
      >
        <h3 style={{ marginTop: 0 }}>Create New Hiring Requisition</h3>
        <form
          onSubmit={(e) => onCreateRequest(e, true)}
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "12px",
          }}
        >
          <label style={{ fontSize: "12px", fontWeight: 600 }}>
            Job Title
            <input
              aria-label="Job Title"
              value={jobTitle}
              onChange={(e) => onJobTitleChange(e.target.value)}
              required
              style={{ width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            />
          </label>
          <label style={{ fontSize: "12px", fontWeight: 600 }}>
            Job Family
            <input
              aria-label="Job Family"
              value={jobFamily}
              onChange={(e) => onJobFamilyChange(e.target.value)}
              required
              style={{ width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            />
          </label>
          <label style={{ fontSize: "12px", fontWeight: 600 }}>
            Department
            <select
              aria-label="Department"
              value={deptId}
              onChange={(e) => onDeptIdChange(e.target.value)}
              style={{ width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            >
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>
          </label>
          <label style={{ fontSize: "12px", fontWeight: 600 }}>
            Job Grade
            <select
              aria-label="Job Grade"
              value={jobGrade}
              onChange={(e) =>
                onJobGradeChange(
                  e.target.value as "L3" | "L4" | "L5" | "L6" | "L7" | "L8" | "EXEC"
                )
              }
              style={{ width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            >
              {["L3", "L4", "L5", "L6", "L7", "L8", "EXEC"].map((g) => (
                <option key={g} value={g}>
                  {g} {["L6", "L7", "L8", "EXEC"].includes(g) ? "(Requires Finance Gate)" : ""}
                </option>
              ))}
            </select>
          </label>
          <label style={{ fontSize: "12px", fontWeight: 600 }}>
            Hiring Type
            <select
              aria-label="Hiring Type"
              value={hiringType}
              onChange={(e) =>
                onHiringTypeChange(e.target.value as "NEW_HEADCOUNT" | "REPLACEMENT")
              }
              style={{ width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            >
              <option value="NEW_HEADCOUNT">NEW_HEADCOUNT</option>
              <option value="REPLACEMENT">REPLACEMENT</option>
            </select>
          </label>
          <label style={{ fontSize: "12px", fontWeight: 600 }}>
            Work Location
            <select
              aria-label="Work Location"
              value={workLocation}
              onChange={(e) =>
                onWorkLocationChange(e.target.value as "HYBRID" | "ONSITE" | "REMOTE")
              }
              style={{ width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            >
              <option value="HYBRID">HYBRID</option>
              <option value="ONSITE">ONSITE</option>
              <option value="REMOTE">REMOTE</option>
            </select>
          </label>
          <label style={{ fontSize: "12px", fontWeight: 600 }}>
            City / Country
            <input
              aria-label="City"
              value={city}
              onChange={(e) => onCityChange(e.target.value)}
              required
              style={{ width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            />
          </label>
          <label style={{ fontSize: "12px", fontWeight: 600 }}>
            Positions (Headcount)
            <input
              aria-label="Positions"
              type="number"
              min={1}
              max={50}
              value={headcount}
              onChange={(e) => onHeadcountChange(Number(e.target.value))}
              style={{ width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            />
          </label>
          <label style={{ fontSize: "12px", fontWeight: 600 }}>
            Annual Base Salary / Pos (INR)
            <input
              aria-label="Annual Base Salary"
              value={salary}
              onChange={(e) => onSalaryChange(e.target.value)}
              style={{ width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            />
          </label>
          <label style={{ fontSize: "12px", fontWeight: 600 }}>
            Benefits Cost / Pos (INR)
            <input
              aria-label="Benefits Cost"
              value={benefits}
              onChange={(e) => onBenefitsChange(e.target.value)}
              style={{ width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            />
          </label>
          <label style={{ fontSize: "12px", fontWeight: 600 }}>
            Target Hiring Date
            <input
              aria-label="Target Hiring Date"
              type="date"
              value={targetHiringDate}
              onChange={(e) => onTargetHiringDateChange(e.target.value)}
              style={{ width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            />
          </label>
          <label style={{ fontSize: "12px", fontWeight: 600 }}>
            Requested Start Date
            <input
              aria-label="Requested Start Date"
              type="date"
              value={requestedStartDate}
              onChange={(e) => onRequestedStartDateChange(e.target.value)}
              style={{ width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            />
          </label>
          <label style={{ fontSize: "12px", fontWeight: 600, gridColumn: "span 2" }}>
            Business Justification (min 15 chars)
            <input
              aria-label="Business Justification"
              value={justification}
              onChange={(e) => onJustificationChange(e.target.value)}
              required
              style={{ width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            />
          </label>
          <label style={{ fontSize: "12px", fontWeight: 600, gridColumn: "span 2" }}>
            Expected Business Impact
            <input
              aria-label="Expected Business Impact"
              value={impact}
              onChange={(e) => onImpactChange(e.target.value)}
              required
              style={{ width: "100%", padding: "8px", marginTop: "4px", boxSizing: "border-box" }}
            />
          </label>
          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              gap: "10px",
              gridColumn: "span 2",
            }}
          >
            <button
              type="submit"
              style={{
                padding: "10px 16px",
                background: "#003B7E",
                color: "#fff",
                border: "none",
                borderRadius: "6px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Create & Submit Request
            </button>
            <button
              type="button"
              onClick={(e) => onCreateRequest(e, false)}
              style={{
                padding: "10px 16px",
                background: "#475569",
                color: "#fff",
                border: "none",
                borderRadius: "6px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Save as Draft
            </button>
          </div>
        </form>
      </div>

      {editingRequest && (
        <div
          style={{
            background: "#fffbeb",
            border: "1px solid #f59e0b",
            borderRadius: "10px",
            padding: "16px 20px",
            marginBottom: "20px",
          }}
        >
          <h4 style={{ marginTop: 0 }}>
            Editing {editingRequest.request_code} ({editingRequest.status})
          </h4>
          <form
            onSubmit={onSaveEditedRequest}
            style={{ display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "flex-end" }}
          >
            <label style={{ fontSize: "12px", fontWeight: 600 }}>
              Job Title
              <input
                id="edit-job-title"
                name="job_title"
                aria-label="Edit Job Title"
                value={editTitle}
                onChange={(e) => onEditTitleChange(e.target.value)}
                style={{ display: "block", padding: "6px", marginTop: "4px" }}
              />
            </label>
            <label style={{ fontSize: "12px", fontWeight: 600 }}>
              Headcount
              <input
                id="edit-headcount"
                name="headcount_requested"
                aria-label="Edit Headcount"
                type="number"
                min={1}
                max={50}
                value={editHeadcount}
                onChange={(e) => onEditHeadcountChange(Number(e.target.value))}
                style={{ display: "block", padding: "6px", marginTop: "4px", width: "80px" }}
              />
            </label>
            <label style={{ fontSize: "12px", fontWeight: 600 }}>
              Salary / Pos (INR)
              <input
                id="edit-salary"
                name="est_annual_salary_per_pos"
                aria-label="Edit Salary Per Position"
                value={editSalary}
                onChange={(e) => onEditSalaryChange(e.target.value)}
                style={{ display: "block", padding: "6px", marginTop: "4px" }}
              />
            </label>
            <label style={{ fontSize: "12px", fontWeight: 600, flex: 1 }}>
              Updated Justification
              <input
                id="edit-justification"
                name="justification"
                aria-label="Edit Justification"
                value={editJustification}
                onChange={(e) => onEditJustificationChange(e.target.value)}
                style={{ display: "block", padding: "6px", marginTop: "4px", width: "100%" }}
              />
            </label>
            <button
              type="submit"
              style={{
                padding: "8px 14px",
                background: "#d97706",
                color: "#fff",
                border: "none",
                borderRadius: "6px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Save Changes
            </button>
            <button
              type="button"
              onClick={onCancelEdit}
              style={{
                padding: "8px 14px",
                background: "#e2e8f0",
                color: "#334155",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
          </form>
        </div>
      )}

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
            <th style={{ padding: "12px" }}>Code</th>
            <th style={{ padding: "12px" }}>Title & Location</th>
            <th style={{ padding: "12px" }}>Grade / Type</th>
            <th style={{ padding: "12px" }}>Positions</th>
            <th style={{ padding: "12px" }}>Annualized Forecast</th>
            <th style={{ padding: "12px" }}>In-Period FY Cost</th>
            <th style={{ padding: "12px" }}>Status</th>
            <th style={{ padding: "12px" }}>Lifecycle Actions</th>
          </tr>
        </thead>
        <tbody>
          {requests.map((r) => {
            const isExpanded = expandedRequestId === r.id;
            const canEditOrSubmit =
              r.status === "DRAFT" || r.status === "CLARIFICATION_REQUESTED";
            const canRecordOutcome = ["APPROVED", "RECRUITING", "PARTIALLY_FILLED"].includes(
              r.status
            );
            const hasActiveApproval = r.approval_steps.some((s) => s.step_status === "ACTIVE");

            return (
              <React.Fragment key={r.id}>
                <tr style={{ borderTop: "1px solid #e2e8f0", fontSize: "14px" }}>
                  <td style={{ padding: "12px", fontWeight: 600 }}>{r.request_code}</td>
                  <td style={{ padding: "12px" }}>
                    <div style={{ fontWeight: 600 }}>{r.job_title}</div>
                    <div style={{ fontSize: "12px", color: "#64748b" }}>
                      {r.city}, {r.country} ({r.work_location}) • {r.business_unit}
                    </div>
                  </td>
                  <td style={{ padding: "12px" }}>
                    <strong>{r.job_grade}</strong> • {r.hiring_type}
                  </td>
                  <td style={{ padding: "12px" }}>
                    {r.headcount_requested} (
                    {r.positions.filter((p) => p.status === "FILLED").length} filled)
                  </td>
                  <td style={{ padding: "12px", fontWeight: 600 }}>
                    {formatINR(r.total_annualized_forecast)}
                  </td>
                  <td style={{ padding: "12px" }}>{formatINR(r.in_period_projected_cost)}</td>
                  <td style={{ padding: "12px" }}>
                    <StatusBadge status={r.status} />
                  </td>
                  <td style={{ padding: "12px", display: "flex", gap: "6px", flexWrap: "wrap" }}>
                    {canEditOrSubmit && (
                      <>
                        <button
                          type="button"
                          onClick={() => onSubmitExistingRequest(r)}
                          style={{
                            padding: "5px 10px",
                            background: "#003B7E",
                            color: "#fff",
                            border: "none",
                            borderRadius: "4px",
                            fontSize: "12px",
                            cursor: "pointer",
                          }}
                        >
                          {r.status === "DRAFT" ? "Submit" : "Resubmit"}
                        </button>
                        <button
                          type="button"
                          onClick={() => onStartEditRequest(r)}
                          style={{
                            padding: "5px 10px",
                            background: "#f59e0b",
                            color: "#fff",
                            border: "none",
                            borderRadius: "4px",
                            fontSize: "12px",
                            cursor: "pointer",
                          }}
                        >
                          Edit
                        </button>
                      </>
                    )}
                    {hasActiveApproval && (
                      <button
                        type="button"
                        onClick={() => onApproveStage(r)}
                        style={{
                          padding: "5px 10px",
                          background: "#16a34a",
                          color: "#fff",
                          border: "none",
                          borderRadius: "4px",
                          fontSize: "12px",
                          cursor: "pointer",
                        }}
                      >
                        Approve Stage
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => onToggleExpandRequest(isExpanded ? null : r.id)}
                      style={{
                        padding: "5px 10px",
                        background: "#e2e8f0",
                        color: "#1e293b",
                        border: "none",
                        borderRadius: "4px",
                        fontSize: "12px",
                        cursor: "pointer",
                      }}
                    >
                      {isExpanded
                        ? "Hide Details"
                        : canRecordOutcome
                        ? "Positions / Hire Outcome"
                        : "Details & History"}
                    </button>
                  </td>
                </tr>

                {isExpanded && (
                  <tr style={{ background: "#f8fafc", borderTop: "1px dashed #cbd5e1" }}>
                    <td colSpan={8} style={{ padding: "16px 20px" }}>
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
                          gap: "20px",
                        }}
                      >
                        <div>
                          <h4 style={{ marginTop: 0, marginBottom: "8px" }}>
                            Positions & Recruitment Outcomes ({r.positions.length})
                          </h4>
                          {canRecordOutcome && (
                            <div
                              style={{
                                background: "#ffffff",
                                border: "1px solid #cbd5e1",
                                borderRadius: "6px",
                                padding: "10px",
                                marginBottom: "10px",
                                display: "flex",
                                gap: "8px",
                                flexWrap: "wrap",
                              }}
                            >
                              <input
                                name="candidate_ref"
                                aria-label="Synthetic Candidate ID"
                                placeholder="Synthetic Candidate ID (e.g. CAND-SYN-204)"
                                value={candidateRef}
                                onChange={(e) => onCandidateRefChange(e.target.value)}
                                style={{ padding: "5px 8px", fontSize: "12px" }}
                              />
                              <input
                                name="actual_hire_date"
                                aria-label="Actual Hire Date"
                                type="date"
                                value={actualHireDate}
                                onChange={(e) => onActualHireDateChange(e.target.value)}
                                style={{ padding: "5px 8px", fontSize: "12px" }}
                              />
                              <input
                                name="actual_annual_base_salary"
                                aria-label="Actual Salary (INR)"
                                placeholder="Actual Salary (INR)"
                                value={actualSalary}
                                onChange={(e) => onActualSalaryChange(e.target.value)}
                                style={{ padding: "5px 8px", fontSize: "12px", width: "120px" }}
                              />
                              <input
                                name="closure_reason"
                                aria-label="Closure Reason"
                                placeholder="Closure Reason"
                                value={outcomeReason}
                                onChange={(e) => onOutcomeReasonChange(e.target.value)}
                                style={{ padding: "5px 8px", fontSize: "12px", flex: 1 }}
                              />
                            </div>
                          )}
                          <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "13px" }}>
                            {r.positions.map((p) => (
                              <li key={p.id} style={{ marginBottom: "8px" }}>
                                <strong>{p.position_code}</strong> — Status:{" "}
                                <strong>{p.status}</strong> (Target: {p.target_hire_date})
                                {p.outcome ? (
                                  <span style={{ color: "#166534", marginLeft: "8px" }}>
                                    • Outcome: {p.outcome.closure_status} (
                                    {p.outcome.candidate_ref}, Actual Salary:{" "}
                                    {formatINR(p.outcome.actual_annual_base_salary)})
                                  </span>
                                ) : (
                                  canRecordOutcome && (
                                    <span style={{ marginLeft: "10px" }}>
                                      <button
                                        type="button"
                                        onClick={() =>
                                          onRecordPositionOutcome(r.id, p.id, "HIRED")
                                        }
                                        style={{
                                          padding: "3px 8px",
                                          background: "#16a34a",
                                          color: "#fff",
                                          border: "none",
                                          borderRadius: "4px",
                                          fontSize: "11px",
                                          cursor: "pointer",
                                          marginRight: "6px",
                                        }}
                                      >
                                        Mark HIRED
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() =>
                                          onRecordPositionOutcome(r.id, p.id, "CANCELLED")
                                        }
                                        style={{
                                          padding: "3px 8px",
                                          background: "#dc2626",
                                          color: "#fff",
                                          border: "none",
                                          borderRadius: "4px",
                                          fontSize: "11px",
                                          cursor: "pointer",
                                        }}
                                      >
                                        Cancel Slot
                                      </button>
                                    </span>
                                  )
                                )}
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div>
                          <h4 style={{ marginTop: 0, marginBottom: "8px" }}>
                            Multi-Stage Approval Pipeline & Decision History
                          </h4>
                          <div style={{ fontSize: "13px", marginBottom: "10px" }}>
                            {r.approval_steps.length === 0 ? (
                              <span>No active workflow steps initialized yet.</span>
                            ) : (
                              r.approval_steps.map((s) => (
                                <div key={s.id} style={{ marginBottom: "4px" }}>
                                  Stage {s.sequence_order}: <strong>{s.stage_name}</strong>{" "}
                                  (Role: <code>{s.required_role}</code>) →{" "}
                                  <strong>{s.step_status}</strong>
                                  {s.is_overdue && (
                                    <span style={{ color: "#dc2626", marginLeft: "6px" }}>
                                      [OVERDUE SLA]
                                    </span>
                                  )}
                                </div>
                              ))
                            )}
                          </div>
                          {r.approval_records.length > 0 && (
                            <div
                              style={{
                                fontSize: "12px",
                                background: "#fff",
                                padding: "8px 12px",
                                borderRadius: "6px",
                                border: "1px solid #e2e8f0",
                              }}
                            >
                              <strong>Recorded Decisions:</strong>
                              <ul style={{ margin: "4px 0 0 0", paddingLeft: "18px" }}>
                                {r.approval_records.map((rec) => (
                                  <li key={rec.id}>
                                    <strong>{rec.stage_name}</strong>: {rec.decision} by{" "}
                                    <code>{rec.approver_id}</code> — &ldquo;{rec.comments}
                                    &rdquo;
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
