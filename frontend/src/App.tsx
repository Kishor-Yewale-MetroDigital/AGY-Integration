import React, { useEffect, useState } from "react";
import {
  createApprovalRule,
  createDelegation,
  createHiringRequest,
  fetchApprovalRules,
  fetchAuditEvents,
  fetchDashboardOverview,
  fetchDelegations,
  fetchDepartments,
  fetchRequests,
  fetchUsers,
  fetchWorkforceSummary,
  populateDemoApprovalQueue,
  recordPositionOutcome,
  setActiveUserId,
  submitApprovalDecision,
  submitHiringRequest,
  triggerBigQuerySync,
  updateHiringRequest,
} from "./api/client";
import type {
  ApprovalDelegation,
  ApprovalRule,
  Department,
  HiringRequest,
  User,
} from "./types/talentflow";
import { METRO_COLORS } from "./assets/metroBrand";
import {
  type ActiveTab,
  MetroFooter,
  MetroHeader,
  formatINR,
} from "./components/SharedUi";
import {
  AuditTab,
  DashboardTab,
  WorkforceTab,
} from "./components/DashboardAndWorkforceTabs";
import { CommitteeQueueTab } from "./components/CommitteeQueueTab";
import { HiringRequestsTab } from "./components/HiringRequestsTab";

export { formatINR };

const STAGE_DEFAULT_USER: Record<string, string> = {
  MANAGER_REVIEW: "usr-manager",
  FINANCE_REVIEW: "usr-finance",
  COMMITTEE_PENDING: "usr-committee",
};

const STAGE_FALLBACK_USER: Record<string, string> = {
  MANAGER_REVIEW: "usr-hrbp",
  FINANCE_REVIEW: "usr-admin",
  COMMITTEE_PENDING: "usr-admin",
};

export function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("dashboard");
  const [users, setUsers] = useState<User[]>([]);
  const [currentUserId, setCurrentUserId] = useState<string>("usr-committee");
  const [departments, setDepartments] = useState<Department[]>([]);
  const [requests, setRequests] = useState<HiringRequest[]>([]);
  const [dashboard, setDashboard] = useState<Record<string, unknown> | null>(null);
  const [workforce, setWorkforce] = useState<Record<string, unknown> | null>(null);
  const [audits, setAudits] = useState<Array<Record<string, unknown>>>([]);
  const [rules, setRules] = useState<ApprovalRule[]>([]);
  const [delegations, setDelegations] = useState<ApprovalDelegation[]>([]);

  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // Filters
  const [searchFilter, setSearchFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [deptFilter, setDeptFilter] = useState<string>("");
  const [gradeFilter, setGradeFilter] = useState<string>("");
  const [hiringTypeFilter, setHiringTypeFilter] = useState<string>("");
  const [delayDays, setDelayDays] = useState<number>(30);

  // New Request Form State
  const [jobTitle, setJobTitle] = useState("Staff Backend Engineer (Cloud Run)");
  const [jobFamily, setJobFamily] = useState("Software Engineering");
  const [deptId, setDeptId] = useState("dept-eng");
  const [country] = useState("India");
  const [city, setCity] = useState("Pune");
  const [workLocation, setWorkLocation] = useState<"HYBRID" | "ONSITE" | "REMOTE">("HYBRID");
  const [jobGrade, setJobGrade] = useState<"L3" | "L4" | "L5" | "L6" | "L7" | "L8" | "EXEC">("L5");
  const [hiringType, setHiringType] = useState<"NEW_HEADCOUNT" | "REPLACEMENT">("NEW_HEADCOUNT");
  const [headcount, setHeadcount] = useState(2);
  const [salary, setSalary] = useState("2500000.00");
  const [benefits, setBenefits] = useState("450000.00");
  const [recFee] = useState("150000.00");
  const [onetimeCost] = useState("75000.00");
  const [targetHiringDate, setTargetHiringDate] = useState("2026-11-15");
  const [requestedStartDate, setRequestedStartDate] = useState("2026-12-01");
  const [justification, setJustification] = useState(
    "Scale high-throughput API platform and BigQuery ingestion services for FY2026."
  );
  const [impact, setImpact] = useState(
    "Support 3x transaction growth and maintain 99.95% service availability."
  );

  // Edit Request State
  const [editingRequest, setEditingRequest] = useState<HiringRequest | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editHeadcount, setEditHeadcount] = useState(1);
  const [editSalary, setEditSalary] = useState("");
  const [editJustification, setEditJustification] = useState("");

  // Expanded Request Detail / Position Outcomes Drawer
  const [expandedRequestId, setExpandedRequestId] = useState<string | null>(null);
  const [candidateRef, setCandidateRef] = useState("CAND-SYN-204");
  const [actualHireDate, setActualHireDate] = useState("2026-11-10");
  const [actualSalary, setActualSalary] = useState("2450000.00");
  const [outcomeReason, setOutcomeReason] = useState(
    "Candidate accepted offer and completed background verification."
  );

  // People Committee & Multi-Stage Approval Queue Controls
  const [decisionComment, setDecisionComment] = useState("");
  const [autoSelectStageApprover, setAutoSelectStageApprover] = useState<boolean>(true);
  const [showOnlyPendingQueue, setShowOnlyPendingQueue] = useState<boolean>(false);

  // Delegation & Approval Rule Forms
  const [delegateToUserId, setDelegateToUserId] = useState("usr-hrbp");
  const [delegateStage, setDelegateStage] = useState<
    "MANAGER_REVIEW" | "FINANCE_REVIEW" | "COMMITTEE_PENDING"
  >("COMMITTEE_PENDING");
  const [delegateReason, setDelegateReason] = useState(
    "Authorized backup coverage during Q4 global talent review."
  );

  const [newRuleName, setNewRuleName] = useState("Executive L7+ Fast-Track Governance");
  const [newRuleMinGrade, setNewRuleMinGrade] = useState("L7");
  const [newRuleMinCost, setNewRuleMinCost] = useState("7500000.00");
  const [newRuleSla, setNewRuleSla] = useState(24);

  async function refreshAll(customDelayDays?: number) {
    setLoading(true);
    try {
      const [u, d, r, dash, wf, aud, rl, del] = await Promise.all([
        fetchUsers(),
        fetchDepartments(),
        fetchRequests({
          status: statusFilter || undefined,
          department_id: deptFilter || undefined,
          job_grade: gradeFilter || undefined,
          hiring_type: hiringTypeFilter || undefined,
          search: searchFilter || undefined,
        }),
        fetchDashboardOverview({
          department_id: deptFilter || undefined,
          job_grade: gradeFilter || undefined,
          hiring_type: hiringTypeFilter || undefined,
          status: statusFilter || undefined,
        }),
        fetchWorkforceSummary({
          department_id: deptFilter || undefined,
          job_grade: gradeFilter || undefined,
          hiring_type: hiringTypeFilter || undefined,
          status: statusFilter || undefined,
          delay_days: customDelayDays ?? delayDays,
        }),
        fetchAuditEvents(),
        fetchApprovalRules(),
        fetchDelegations(),
      ]);
      setUsers(u);
      setDepartments(d);
      setRequests(r);
      setDashboard(dash);
      setWorkforce(wf);
      setAudits(aud);
      setRules(rl);
      setDelegations(del);
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setActiveUserId(currentUserId);
    void refreshAll();
  }, [currentUserId, statusFilter, deptFilter, gradeFilter, hiringTypeFilter]);

  function handleUserChange(newId: string) {
    setCurrentUserId(newId);
    setActiveUserId(newId);
    setErrorBanner(null);
    setSuccessBanner(null);
  }

  async function handleCreateRequest(e: React.FormEvent, submitImmediately: boolean) {
    e.preventDefault();
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      const selectedDept = departments.find((d) => d.id === deptId);
      const effectiveCreatorId =
        currentUserId === "usr-exec" && autoSelectStageApprover ? "usr-creator" : currentUserId;

      const created = await createHiringRequest(
        {
          job_title: jobTitle,
          job_family: jobFamily,
          department_id: deptId,
          business_unit: selectedDept?.business_unit ?? "Digital & Technology",
          country,
          city,
          work_location: workLocation,
          job_grade: jobGrade,
          employment_type: "FULL_TIME",
          hiring_manager_id: "usr-manager",
          request_owner_id: "usr-creator",
          hiring_type: hiringType,
          headcount_requested: Number(headcount),
          justification,
          expected_business_impact: impact,
          requested_start_date: requestedStartDate,
          target_hiring_date: targetHiringDate,
          currency: "INR",
          est_annual_salary_per_pos: salary,
          est_benefits_cost_per_pos: benefits,
          est_recruitment_fee_per_pos: recFee,
          est_onetime_cost_per_pos: onetimeCost,
        },
        effectiveCreatorId
      );

      if (submitImmediately) {
        const submitted = await submitHiringRequest(created.id, effectiveCreatorId);
        setSuccessBanner(
          `Created & submitted ${submitted.request_code} (${submitted.job_title}) → Now in ${submitted.status}.`
        );
      } else {
        setSuccessBanner(
          `Saved ${created.request_code} (${created.job_title}) as DRAFT. You can edit or submit it anytime.`
        );
      }
      await refreshAll();
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleSubmitExistingRequest(req: HiringRequest) {
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      const effectiveActor =
        currentUserId === "usr-exec" && autoSelectStageApprover ? "usr-creator" : currentUserId;
      const submitted = await submitHiringRequest(req.id, effectiveActor);
      setSuccessBanner(
        `Submitted ${submitted.request_code} to workflow → Current stage: ${submitted.status}.`
      );
      await refreshAll();
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : String(err));
    }
  }

  function startEditRequest(req: HiringRequest) {
    setEditingRequest(req);
    setEditTitle(req.job_title);
    setEditHeadcount(req.headcount_requested);
    setEditSalary(req.est_annual_salary_per_pos);
    setEditJustification(req.justification);
  }

  async function handleSaveEditedRequest(e: React.FormEvent) {
    e.preventDefault();
    if (!editingRequest) return;
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      const effectiveActor =
        currentUserId === "usr-exec" && autoSelectStageApprover ? "usr-creator" : currentUserId;
      const updated = await updateHiringRequest(
        editingRequest.id,
        {
          job_title: editTitle,
          headcount_requested: Number(editHeadcount),
          est_annual_salary_per_pos: editSalary,
          justification: editJustification,
        },
        effectiveActor
      );
      setEditingRequest(null);
      setSuccessBanner(
        `Updated ${updated.request_code} — Forecast recalculated to ${formatINR(
          updated.total_annualized_forecast
        )}.`
      );
      await refreshAll();
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : String(err));
    }
  }

  function resolveAuthorizedApproverForRequest(req: HiringRequest): {
    approverId: string;
    activeStage: string | null;
    switched: boolean;
  } {
    const activeStep = req.approval_steps.find((s) => s.step_status === "ACTIVE");
    const activeStage = activeStep ? activeStep.stage_name : null;

    if (!autoSelectStageApprover || !activeStage) {
      return { approverId: currentUserId, activeStage, switched: false };
    }

    const currentUser = users.find((u) => u.id === currentUserId);
    const stageAllowedRoles: Record<string, string[]> = {
      MANAGER_REVIEW: ["HIRING_MANAGER", "HRBP", "ADMIN"],
      FINANCE_REVIEW: ["FINANCE_REVIEWER", "ADMIN"],
      COMMITTEE_PENDING: ["COMMITTEE_MEMBER", "ADMIN"],
    };
    const allowed = stageAllowedRoles[activeStage] || [];
    const hasDelegation = delegations.some(
      (d) => d.is_active && d.stage_name === activeStage && d.to_user_id === currentUserId
    );

    if (
      currentUser &&
      (allowed.includes(currentUser.role) || hasDelegation) &&
      req.request_owner_id !== currentUserId
    ) {
      return { approverId: currentUserId, activeStage, switched: false };
    }

    let targetUserId = STAGE_DEFAULT_USER[activeStage] || "usr-committee";
    if (targetUserId === req.request_owner_id) {
      targetUserId = STAGE_FALLBACK_USER[activeStage] || "usr-admin";
    }
    return {
      approverId: targetUserId,
      activeStage,
      switched: targetUserId !== currentUserId,
    };
  }

  async function handleDecision(
    req: HiringRequest,
    decision: "APPROVE" | "REJECT" | "REQUEST_CLARIFICATION"
  ) {
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      const { approverId, activeStage, switched } = resolveAuthorizedApproverForRequest(req);
      let finalComment = decisionComment.trim();
      const isMismatchedPreset =
        (decision === "APPROVE" &&
          (finalComment.startsWith("Rejected") ||
            finalComment.startsWith("Clarification requested:"))) ||
        (decision === "REQUEST_CLARIFICATION" &&
          (finalComment.startsWith("Approved") || finalComment.startsWith("Rejected"))) ||
        (decision === "REJECT" &&
          (finalComment.startsWith("Approved") ||
            finalComment.startsWith("Clarification requested:")));
      if (!finalComment || isMismatchedPreset) {
        if (decision === "APPROVE") {
          finalComment = `Approved at stage ${
            activeStage || req.status
          } in accordance with FY2026 workforce plan.`;
        } else if (decision === "REQUEST_CLARIFICATION") {
          finalComment =
            "Clarification requested: Please provide detailed breakdown of Q4 milestone deliverables and cost center allocation.";
        } else {
          finalComment =
            "Rejected: Role scope overlaps with existing approved squad headcount for this quarter.";
        }
      } else if (
        (decision === "REJECT" || decision === "REQUEST_CLARIFICATION") &&
        finalComment.length < 5
      ) {
        finalComment = `${finalComment} — detailed justification required by governance policy.`;
      }

      if (switched) {
        setCurrentUserId(approverId);
        setActiveUserId(approverId);
      }

      const updated = await submitApprovalDecision(req.id, decision, finalComment, approverId);
      const approverObj = users.find((u) => u.id === approverId);
      setDecisionComment("");
      setSuccessBanner(
        `${decision} recorded on ${updated.request_code} (${activeStage || "Stage"}) by ${
          approverObj?.full_name || approverId
        } → Status is now ${updated.status}.`
      );
      await refreshAll();
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleFastTrackToCommittee(req: HiringRequest) {
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      let current = req;
      let safety = 0;
      while (
        current.status !== "COMMITTEE_PENDING" &&
        current.status !== "APPROVED" &&
        safety < 4
      ) {
        safety += 1;
        const activeStep = current.approval_steps.find((s) => s.step_status === "ACTIVE");
        if (!activeStep) break;
        let actorId = STAGE_DEFAULT_USER[activeStep.stage_name] || "usr-admin";
        if (actorId === current.request_owner_id) {
          actorId = STAGE_FALLBACK_USER[activeStep.stage_name] || "usr-admin";
        }
        current = await submitApprovalDecision(
          current.id,
          "APPROVE",
          `Pre-committee stage ${activeStep.stage_name} approved to advance to People Committee.`,
          actorId
        );
      }
      setCurrentUserId("usr-committee");
      setActiveUserId("usr-committee");
      setSuccessBanner(
        `${current.request_code} advanced to ${current.status} and ready for People Committee decision.`
      );
      await refreshAll();
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleRecordPositionOutcome(
    reqId: string,
    posId: string,
    closureStatus: "HIRED" | "CANCELLED"
  ) {
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      const effectiveActor =
        currentUserId === "usr-exec" && autoSelectStageApprover ? "usr-hrbp" : currentUserId;
      const updated = await recordPositionOutcome(
        reqId,
        posId,
        {
          candidate_ref: candidateRef.trim() || `CAND-SYN-${Math.floor(100 + Math.random() * 899)}`,
          actual_hire_date: actualHireDate,
          actual_annual_base_salary: actualSalary,
          actual_benefits_cost: "450000.00",
          actual_recruitment_fee: "140000.00",
          actual_onetime_cost: "75000.00",
          closure_status: closureStatus,
          closure_reason:
            outcomeReason.trim().length >= 5
              ? outcomeReason.trim()
              : `Position marked ${closureStatus} via TalentFlow recruitment tracker.`,
        },
        effectiveActor
      );
      setSuccessBanner(
        `Recorded ${closureStatus} outcome for position on ${updated.request_code} → Request status is now ${updated.status}.`
      );
      await refreshAll();
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : String(err));
    }
  }

  async function handlePopulateDemoQueue() {
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      const res = await populateDemoApprovalQueue();
      setSuccessBanner(
        res.items.length > 0
          ? `Approval Queue populated/restored: ${res.items.join(", ")}`
          : "All sample requests are already active in the approval queue!"
      );
      await refreshAll();
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleManualBigQuerySync() {
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      const res = await triggerBigQuerySync();
      setSuccessBanner(
        `BigQuery (talentflow_analytics) incremental MERGE sync #${String(
          res.sync_run_count
        )} completed — ${String(res.total_unique_requests_in_bq)} unique requests & ${String(
          res.total_unique_positions_in_bq
        )} positions reconciled.`
      );
      await refreshAll();
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleCreateDelegation(e: React.FormEvent) {
    e.preventDefault();
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      const actorId = STAGE_DEFAULT_USER[delegateStage] || currentUserId;
      const d = await createDelegation(
        {
          to_user_id: delegateToUserId,
          stage_name: delegateStage,
          reason: delegateReason,
        },
        actorId
      );
      setSuccessBanner(
        `Delegated ${d.stage_name} authority from ${d.from_user_id} to ${d.to_user_id}.`
      );
      await refreshAll();
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleCreateRule(e: React.FormEvent) {
    e.preventDefault();
    setErrorBanner(null);
    setSuccessBanner(null);
    try {
      const created = await createApprovalRule(
        {
          rule_name: newRuleName,
          min_grade: newRuleMinGrade,
          min_total_cost: newRuleMinCost,
          requires_manager_review: true,
          requires_finance_review: true,
          requires_committee_review: true,
          sla_hours: Number(newRuleSla),
        },
        "usr-admin"
      );
      setSuccessBanner(`Created configurable approval rule: ${created.rule_name}.`);
      await refreshAll();
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : String(err));
    }
  }

  const queueRequests = showOnlyPendingQueue
    ? requests.filter((r) => r.approval_steps.some((s) => s.step_status === "ACTIVE"))
    : requests;

  return (
    <div
      style={{
        fontFamily: "'Nunito', sans-serif",
        color: METRO_COLORS.bodyText,
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        backgroundColor: "#f4f7fb",
      }}
    >
      <MetroHeader
        users={users}
        currentUserId={currentUserId}
        onUserChange={handleUserChange}
        onPopulateDemoQueue={() => void handlePopulateDemoQueue()}
      />

      <nav
        style={{
          background: "#ffffff",
          borderBottom: "1px solid #d1d1d1",
          padding: "12px 28px",
          display: "flex",
          gap: "10px",
          flexWrap: "wrap",
          boxShadow: "0 1px 3px rgba(0, 59, 126, 0.05)",
        }}
      >
        {(
          [
            ["dashboard", "Executive Overview (BigQuery + Live)"],
            ["requests", `Hiring Requests (${requests.length})`],
            [
              "committee",
              `People Committee Queue (${
                requests.filter((r) => r.approval_steps.some((s) => s.step_status === "ACTIVE"))
                  .length
              } Active)`,
            ],
            ["workforce", "Workforce & Cost Planning"],
            ["audit", `Immutable Audit Log (${audits.length})`],
          ] as Array<[ActiveTab, string]>
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setActiveTab(key)}
            style={{
              padding: "10px 18px",
              background: activeTab === key ? METRO_COLORS.secondaryGold : METRO_COLORS.primaryNavy,
              border: "none",
              borderRadius: "6px",
              color: activeTab === key ? "#000000" : "#ffffff",
              fontWeight: activeTab === key ? 800 : 600,
              cursor: "pointer",
              fontSize: "14px",
              boxShadow:
                activeTab === key
                  ? "0 4px 6px -1px rgba(0, 0, 0, 0.14), 0 2px 4px -2px rgba(0, 0, 0, 0.1)"
                  : "none",
            }}
          >
            {label}
          </button>
        ))}
      </nav>

      <main
        style={{
          padding: "24px 28px",
          maxWidth: "1440px",
          width: "100%",
          margin: "0 auto",
          flex: 1,
        }}
      >
        {errorBanner && (
          <div
            role="alert"
            style={{
              background: "#fef2f2",
              border: "1px solid #f87171",
              color: "#991b1b",
              padding: "12px 16px",
              borderRadius: "8px",
              marginBottom: "16px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span>{errorBanner}</span>
            <button
              type="button"
              onClick={() => setErrorBanner(null)}
              style={{
                background: "transparent",
                border: "none",
                color: "#991b1b",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              ✕
            </button>
          </div>
        )}
        {successBanner && (
          <div
            role="status"
            style={{
              background: "#f0fdf4",
              border: "1px solid #4ade80",
              color: "#166534",
              padding: "12px 16px",
              borderRadius: "8px",
              marginBottom: "16px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span>{successBanner}</span>
            <button
              type="button"
              onClick={() => setSuccessBanner(null)}
              style={{
                background: "transparent",
                border: "none",
                color: "#166534",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              ✕
            </button>
          </div>
        )}

        <section
          style={{
            background: "#ffffff",
            border: "1px solid #e2e8f0",
            borderRadius: "10px",
            padding: "12px 16px",
            marginBottom: "20px",
            display: "flex",
            gap: "12px",
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <strong style={{ fontSize: "13px", color: "#334155" }}>Global Filters:</strong>
          <input
            id="global-filter-search"
            name="search"
            aria-label="Search job title or REQ code"
            type="text"
            placeholder="Search job title or REQ code..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void refreshAll()}
            style={{
              padding: "6px 10px",
              borderRadius: "6px",
              border: "1px solid #cbd5e1",
              minWidth: "200px",
            }}
          />
          <select
            id="global-filter-department"
            name="department_id"
            aria-label="Filter by Department"
            value={deptFilter}
            onChange={(e) => setDeptFilter(e.target.value)}
            style={{ padding: "6px 10px", borderRadius: "6px", border: "1px solid #cbd5e1" }}
          >
            <option value="">All Departments</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.code} — {d.name}
              </option>
            ))}
          </select>
          <select
            id="global-filter-grade"
            name="job_grade"
            aria-label="Filter by Job Grade"
            value={gradeFilter}
            onChange={(e) => setGradeFilter(e.target.value)}
            style={{ padding: "6px 10px", borderRadius: "6px", border: "1px solid #cbd5e1" }}
          >
            <option value="">All Job Grades</option>
            {["L3", "L4", "L5", "L6", "L7", "L8", "EXEC"].map((g) => (
              <option key={g} value={g}>
                Grade {g}
              </option>
            ))}
          </select>
          <select
            id="global-filter-hiring-type"
            name="hiring_type"
            aria-label="Filter by Hiring Type"
            value={hiringTypeFilter}
            onChange={(e) => setHiringTypeFilter(e.target.value)}
            style={{ padding: "6px 10px", borderRadius: "6px", border: "1px solid #cbd5e1" }}
          >
            <option value="">All Hiring Types</option>
            <option value="NEW_HEADCOUNT">NEW_HEADCOUNT</option>
            <option value="REPLACEMENT">REPLACEMENT</option>
          </select>
          <select
            id="global-filter-status"
            name="status"
            aria-label="Filter by Status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ padding: "6px 10px", borderRadius: "6px", border: "1px solid #cbd5e1" }}
          >
            <option value="">All Statuses</option>
            {[
              "DRAFT",
              "MANAGER_REVIEW",
              "FINANCE_REVIEW",
              "COMMITTEE_PENDING",
              "CLARIFICATION_REQUESTED",
              "APPROVED",
              "RECRUITING",
              "PARTIALLY_FILLED",
              "FILLED",
              "REJECTED",
              "CANCELLED",
            ].map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => void refreshAll()}
            style={{
              padding: "6px 12px",
              borderRadius: "6px",
              background: "#003B7E",
              color: "#fff",
              border: "none",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Apply / Refresh
          </button>
          {(searchFilter || deptFilter || gradeFilter || hiringTypeFilter || statusFilter) && (
            <button
              type="button"
              onClick={() => {
                setSearchFilter("");
                setDeptFilter("");
                setGradeFilter("");
                setHiringTypeFilter("");
                setStatusFilter("");
              }}
              style={{
                padding: "6px 10px",
                borderRadius: "6px",
                background: "#f1f5f9",
                color: "#334155",
                border: "1px solid #cbd5e1",
                cursor: "pointer",
              }}
            >
              Clear Filters
            </button>
          )}
          {loading && <span style={{ fontSize: "12px", color: "#64748b" }}>Refreshing...</span>}
        </section>

        {activeTab === "dashboard" && (
          <DashboardTab
            dashboard={dashboard}
            requests={requests}
            onManualBigQuerySync={() => void handleManualBigQuerySync()}
          />
        )}

        {activeTab === "requests" && (
          <HiringRequestsTab
            requests={requests}
            departments={departments}
            jobTitle={jobTitle}
            onJobTitleChange={setJobTitle}
            jobFamily={jobFamily}
            onJobFamilyChange={setJobFamily}
            deptId={deptId}
            onDeptIdChange={setDeptId}
            jobGrade={jobGrade}
            onJobGradeChange={setJobGrade}
            hiringType={hiringType}
            onHiringTypeChange={setHiringType}
            workLocation={workLocation}
            onWorkLocationChange={setWorkLocation}
            city={city}
            onCityChange={setCity}
            headcount={headcount}
            onHeadcountChange={setHeadcount}
            salary={salary}
            onSalaryChange={setSalary}
            benefits={benefits}
            onBenefitsChange={setBenefits}
            targetHiringDate={targetHiringDate}
            onTargetHiringDateChange={setTargetHiringDate}
            requestedStartDate={requestedStartDate}
            onRequestedStartDateChange={setRequestedStartDate}
            justification={justification}
            onJustificationChange={setJustification}
            impact={impact}
            onImpactChange={setImpact}
            onCreateRequest={(e, sub) => void handleCreateRequest(e, sub)}
            editingRequest={editingRequest}
            onCancelEdit={() => setEditingRequest(null)}
            editTitle={editTitle}
            onEditTitleChange={setEditTitle}
            editHeadcount={editHeadcount}
            onEditHeadcountChange={setEditHeadcount}
            editSalary={editSalary}
            onEditSalaryChange={setEditSalary}
            editJustification={editJustification}
            onEditJustificationChange={setEditJustification}
            onSaveEditedRequest={(e) => void handleSaveEditedRequest(e)}
            onStartEditRequest={startEditRequest}
            onSubmitExistingRequest={(r) => void handleSubmitExistingRequest(r)}
            onApproveStage={(r) => void handleDecision(r, "APPROVE")}
            expandedRequestId={expandedRequestId}
            onToggleExpandRequest={setExpandedRequestId}
            candidateRef={candidateRef}
            onCandidateRefChange={setCandidateRef}
            actualHireDate={actualHireDate}
            onActualHireDateChange={setActualHireDate}
            actualSalary={actualSalary}
            onActualSalaryChange={setActualSalary}
            outcomeReason={outcomeReason}
            onOutcomeReasonChange={setOutcomeReason}
            onRecordPositionOutcome={(reqId, posId, st) =>
              void handleRecordPositionOutcome(reqId, posId, st)
            }
          />
        )}

        {activeTab === "committee" && (
          <CommitteeQueueTab
            queueRequests={queueRequests}
            users={users}
            delegations={delegations}
            rules={rules}
            autoSelectStageApprover={autoSelectStageApprover}
            onAutoSelectStageApproverChange={setAutoSelectStageApprover}
            showOnlyPendingQueue={showOnlyPendingQueue}
            onShowOnlyPendingQueueChange={setShowOnlyPendingQueue}
            decisionComment={decisionComment}
            onDecisionCommentChange={setDecisionComment}
            onDecision={(r, d) => void handleDecision(r, d)}
            onFastTrackToCommittee={(r) => void handleFastTrackToCommittee(r)}
            onSubmitExistingRequest={(r) => void handleSubmitExistingRequest(r)}
            delegateStage={delegateStage}
            onDelegateStageChange={setDelegateStage}
            delegateToUserId={delegateToUserId}
            onDelegateToUserIdChange={setDelegateToUserId}
            delegateReason={delegateReason}
            onDelegateReasonChange={setDelegateReason}
            onCreateDelegation={(e) => void handleCreateDelegation(e)}
            newRuleName={newRuleName}
            onNewRuleNameChange={setNewRuleName}
            newRuleMinGrade={newRuleMinGrade}
            onNewRuleMinGradeChange={setNewRuleMinGrade}
            newRuleMinCost={newRuleMinCost}
            onNewRuleMinCostChange={setNewRuleMinCost}
            newRuleSla={newRuleSla}
            onNewRuleSlaChange={setNewRuleSla}
            onCreateRule={(e) => void handleCreateRule(e)}
          />
        )}

        {activeTab === "workforce" && (
          <WorkforceTab
            workforce={workforce}
            departments={departments}
            delayDays={delayDays}
            onDelayDaysChange={(d) => {
              setDelayDays(d);
              void refreshAll(d);
            }}
          />
        )}

        {activeTab === "audit" && <AuditTab audits={audits} />}
      </main>

      <MetroFooter />
    </div>
  );
}

export default App;
