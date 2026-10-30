import React from "react";
import { METRO_COLORS } from "../assets/metroBrand";
import type { ApprovalRule, Department, User, UserRole } from "../types/talentflow";
import { formatINR } from "./SharedUi";

export const ROLE_RIGHTS_CATALOG: Record<
  UserRole,
  {
    label: string;
    summary: string;
    rights: string[];
    badgeBg: string;
    badgeFg: string;
  }
> = {
  REQUEST_CREATOR: {
    label: "Request Creator (Squad Lead / Hiring Initiator)",
    summary: "Creates, edits, and submits hiring requisitions and records candidate outcomes.",
    rights: [
      "Create & Edit Hiring Requisitions",
      "Submit Requisitions to Workflow",
      "Record Position Hiring Outcomes",
    ],
    badgeBg: "#f1f5f9",
    badgeFg: "#334155",
  },
  HIRING_MANAGER: {
    label: "Hiring Manager (Stage 1 Approver)",
    summary: "Reviews & approves Stage 1 (MANAGER_REVIEW) requisitions (SoD enforced on own requests).",
    rights: [
      "Approve / Reject / Request Clarification at MANAGER_REVIEW",
      "Create & Submit Hiring Requisitions",
      "Delegate Manager Review Authority",
    ],
    badgeBg: "rgba(0, 137, 203, 0.15)",
    badgeFg: "#003B7E",
  },
  HRBP: {
    label: "HR Business Partner (People Partner & Co-Reviewer)",
    summary: "Co-reviews Manager stage, manages recruitment outcomes, rules, and user onboarding.",
    rights: [
      "Approve / Reject at MANAGER_REVIEW Stage",
      "Configure Governance & Approval Rules",
      "Manage Users & Record Position Outcomes",
    ],
    badgeBg: "#e0f2fe",
    badgeFg: "#0369a1",
  },
  FINANCE_REVIEWER: {
    label: "Finance Reviewer (Mandatory Finance Gate)",
    summary: "Controls Stage 2 (FINANCE_REVIEW) budget envelope sign-off for senior/high-cost roles.",
    rights: [
      "Approve / Reject / Clarify at FINANCE_REVIEW Gate",
      "Configure Cost & Finance Gate Rules",
      "Delegate Finance Review Authority",
    ],
    badgeBg: "#fef3c7",
    badgeFg: "#92400e",
  },
  COMMITTEE_MEMBER: {
    label: "People Committee Member (Final Governance Approver)",
    summary: "Final approval authority at COMMITTEE_PENDING stage to release positions for recruiting.",
    rights: [
      "Final Approve / Reject / Clarify at COMMITTEE_PENDING",
      "Configure Governance Rules & Delegations",
      "Manage Application Users & Role Assignments",
    ],
    badgeBg: "#f9ae00",
    badgeFg: "#000000",
  },
  ADMIN: {
    label: "Platform Administrator (Full Governance & Access Control)",
    summary: "Full administrative rights across users, RBAC assignments, approval rules, and stages.",
    rights: [
      "Add Users & Assign Application Roles/Rights",
      "Create, Pause & Delete Governance Approval Rules",
      "Authorized Across All Workflow Stages (SoD Enforced)",
    ],
    badgeBg: "#dcfce7",
    badgeFg: "#166534",
  },
  EXEC_READONLY: {
    label: "Executive Read-Only (Board & Leadership Observer)",
    summary: "Read-only access to Executive Overview, BigQuery Analytics, Workforce Cost, and Audit Log.",
    rights: [
      "View Executive Dashboard & BigQuery Analytics",
      "View Workforce Budget & Delay Simulations",
      "Inspect Immutable Governance Audit Trail (Zero Write Access)",
    ],
    badgeBg: "#f3e8ff",
    badgeFg: "#6b21a8",
  },
};

const ALL_ROLES: UserRole[] = [
  "REQUEST_CREATOR",
  "HIRING_MANAGER",
  "HRBP",
  "FINANCE_REVIEWER",
  "COMMITTEE_MEMBER",
  "ADMIN",
  "EXEC_READONLY",
];

export function AdminTab({
  users,
  departments,
  rules,
  currentUserId,
  newUserName,
  onNewUserNameChange,
  newUserEmail,
  onNewUserEmailChange,
  newUserRole,
  onNewUserRoleChange,
  newUserDeptId,
  onNewUserDeptIdChange,
  newUserBusinessUnit,
  onNewUserBusinessUnitChange,
  onCreateUser,
  onUpdateUserRole,
  onToggleUserActive,
  onSelectActingUser,
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
  users: User[];
  departments: Department[];
  rules: ApprovalRule[];
  currentUserId: string;
  newUserName: string;
  onNewUserNameChange: (val: string) => void;
  newUserEmail: string;
  onNewUserEmailChange: (val: string) => void;
  newUserRole: UserRole;
  onNewUserRoleChange: (val: UserRole) => void;
  newUserDeptId: string;
  onNewUserDeptIdChange: (val: string) => void;
  newUserBusinessUnit: string;
  onNewUserBusinessUnitChange: (val: string) => void;
  onCreateUser: (e: React.FormEvent) => void;
  onUpdateUserRole: (userId: string, role: UserRole) => void;
  onToggleUserActive: (user: User) => void;
  onSelectActingUser: (userId: string) => void;
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
  onToggleRuleActive: (rule: ApprovalRule) => void;
  onDeleteRule: (ruleId: string) => void;
}) {
  const selectedRoleMeta = ROLE_RIGHTS_CATALOG[newUserRole];

  return (
    <section>
      <div style={{ marginBottom: "18px" }}>
        <h2 style={{ margin: 0, color: METRO_COLORS.primaryNavy }}>
          Platform Administration — User Access, Role Rights &amp; Governance Rules
        </h2>
        <p style={{ color: "#475569", margin: "4px 0 0 0", fontSize: "13px" }}>
          Provision application users, assign Role-Based Access Control (RBAC) rights, and manage
          automated People Committee &amp; Finance Gate governance rules. Every change is recorded in
          the immutable audit log.
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(440px, 1fr))",
          gap: "20px",
          marginBottom: "24px",
        }}
      >
        {/* Card 1: Add New User & Assign Required Rights */}
        <div
          style={{
            background: "#ffffff",
            border: "1px solid #cbd5e1",
            borderTop: `4px solid ${METRO_COLORS.primaryNavy}`,
            borderRadius: "10px",
            padding: "20px",
            boxShadow: "0 2px 6px rgba(0, 59, 126, 0.06)",
          }}
        >
          <h3 style={{ marginTop: 0, color: METRO_COLORS.primaryNavy }}>
            Add User to Application &amp; Assign Required Rights
          </h3>
          <form onSubmit={onCreateUser} style={{ display: "grid", gap: "12px" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div>
                <label
                  htmlFor="admin-user-fullname"
                  style={{
                    display: "block",
                    fontSize: "12px",
                    fontWeight: 700,
                    color: "#334155",
                    marginBottom: "4px",
                  }}
                >
                  Full Name *
                </label>
                <input
                  id="admin-user-fullname"
                  name="full_name"
                  aria-label="User Full Name"
                  type="text"
                  required
                  value={newUserName}
                  onChange={(e) => onNewUserNameChange(e.target.value)}
                  placeholder="e.g. Neha Kulkarni"
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid #cbd5e1",
                    boxSizing: "border-box",
                  }}
                />
              </div>
              <div>
                <label
                  htmlFor="admin-user-email"
                  style={{
                    display: "block",
                    fontSize: "12px",
                    fontWeight: 700,
                    color: "#334155",
                    marginBottom: "4px",
                  }}
                >
                  Corporate Email *
                </label>
                <input
                  id="admin-user-email"
                  name="email"
                  aria-label="User Email"
                  type="email"
                  required
                  value={newUserEmail}
                  onChange={(e) => onNewUserEmailChange(e.target.value)}
                  placeholder="e.g. neha.kulkarni@metro-gsc.in"
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid #cbd5e1",
                    boxSizing: "border-box",
                  }}
                />
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div>
                <label
                  htmlFor="admin-user-role"
                  style={{
                    display: "block",
                    fontSize: "12px",
                    fontWeight: 700,
                    color: "#334155",
                    marginBottom: "4px",
                  }}
                >
                  Assign Application Role &amp; Rights *
                </label>
                <select
                  id="admin-user-role"
                  name="role"
                  aria-label="Assign User Role"
                  value={newUserRole}
                  onChange={(e) => onNewUserRoleChange(e.target.value as UserRole)}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid #cbd5e1",
                    fontWeight: 700,
                    color: METRO_COLORS.primaryNavy,
                    boxSizing: "border-box",
                  }}
                >
                  {ALL_ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r} — {ROLE_RIGHTS_CATALOG[r].label.split("(")[0].trim()}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="admin-user-department"
                  style={{
                    display: "block",
                    fontSize: "12px",
                    fontWeight: 700,
                    color: "#334155",
                    marginBottom: "4px",
                  }}
                >
                  Department Scope
                </label>
                <select
                  id="admin-user-department"
                  name="department_id"
                  aria-label="Assign User Department"
                  value={newUserDeptId}
                  onChange={(e) => {
                    const val = e.target.value;
                    onNewUserDeptIdChange(val);
                    const matched = departments.find((d) => d.id === val);
                    if (matched) {
                      onNewUserBusinessUnitChange(matched.business_unit);
                    }
                  }}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid #cbd5e1",
                    boxSizing: "border-box",
                  }}
                >
                  <option value="">Global / Cross-Department</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.code} — {d.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label
                htmlFor="admin-user-bu"
                style={{
                  display: "block",
                  fontSize: "12px",
                  fontWeight: 700,
                  color: "#334155",
                  marginBottom: "4px",
                }}
              >
                Business Unit *
              </label>
              <input
                id="admin-user-bu"
                name="business_unit"
                aria-label="User Business Unit"
                type="text"
                required
                value={newUserBusinessUnit}
                onChange={(e) => onNewUserBusinessUnitChange(e.target.value)}
                style={{
                  width: "100%",
                  padding: "8px 10px",
                  borderRadius: "6px",
                  border: "1px solid #cbd5e1",
                  boxSizing: "border-box",
                }}
              />
            </div>

            {/* Live Rights Preview */}
            <div
              style={{
                background: "#f8fafc",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                padding: "10px 12px",
                fontSize: "12px",
              }}
            >
              <div style={{ fontWeight: 800, color: METRO_COLORS.primaryNavy, marginBottom: "4px" }}>
                Rights Granted for {newUserRole}:
              </div>
              <div style={{ color: "#475569", marginBottom: "6px" }}>{selectedRoleMeta.summary}</div>
              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                {selectedRoleMeta.rights.map((right) => (
                  <span
                    key={right}
                    style={{
                      background: selectedRoleMeta.badgeBg,
                      color: selectedRoleMeta.badgeFg,
                      padding: "3px 8px",
                      borderRadius: "4px",
                      fontWeight: 700,
                      fontSize: "11px",
                    }}
                  >
                    ✓ {right}
                  </span>
                ))}
              </div>
            </div>

            <button
              type="submit"
              style={{
                padding: "10px 16px",
                background: METRO_COLORS.primaryNavy,
                color: "#ffffff",
                border: "none",
                borderRadius: "6px",
                fontWeight: 800,
                cursor: "pointer",
                fontSize: "13px",
              }}
            >
              + Add User &amp; Assign Rights
            </button>
          </form>
        </div>

        {/* Card 2: Configurable Governance & Approval Rules Engine */}
        <div
          style={{
            background: "#ffffff",
            border: "1px solid #cbd5e1",
            borderTop: `4px solid ${METRO_COLORS.secondaryGold}`,
            borderRadius: "10px",
            padding: "20px",
            boxShadow: "0 2px 6px rgba(0, 59, 126, 0.06)",
          }}
        >
          <h3 style={{ marginTop: 0, color: METRO_COLORS.primaryNavy }}>
            Configurable Governance &amp; Approval Rules Engine
          </h3>
          <p style={{ fontSize: "12px", color: "#475569", marginTop: 0 }}>
            Define or update approval routing thresholds (Minimum Job Grade, Minimum Annualized Cost
            in INR, Mandatory Finance Gate, and SLA Hours). Submitting an existing rule name updates
            it in place.
          </p>
          <form
            onSubmit={onCreateRule}
            style={{
              display: "grid",
              gap: "10px",
              marginBottom: "14px",
              background: "#f8fafc",
              padding: "12px",
              borderRadius: "8px",
              border: "1px solid #e2e8f0",
            }}
          >
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "8px" }}>
              <input
                aria-label="Admin Rule Name"
                value={newRuleName}
                onChange={(e) => onNewRuleNameChange(e.target.value)}
                placeholder="Rule Name"
                required
                style={{
                  padding: "7px 10px",
                  borderRadius: "6px",
                  border: "1px solid #cbd5e1",
                }}
              />
              <select
                aria-label="Admin Minimum Job Grade"
                value={newRuleMinGrade}
                onChange={(e) => onNewRuleMinGradeChange(e.target.value)}
                style={{ padding: "7px", borderRadius: "6px", border: "1px solid #cbd5e1" }}
              >
                <option value="ANY">Any Grade</option>
                {["L3", "L4", "L5", "L6", "L7", "L8", "EXEC"].map((g) => (
                  <option key={g} value={g}>
                    Min Grade {g}
                  </option>
                ))}
              </select>
            </div>
            <div
              style={{
                display: "flex",
                gap: "10px",
                alignItems: "center",
                flexWrap: "wrap",
              }}
            >
              <input
                aria-label="Admin Minimum Cost INR"
                value={newRuleMinCost}
                onChange={(e) => onNewRuleMinCostChange(e.target.value)}
                placeholder="Min Cost INR"
                style={{
                  padding: "7px 10px",
                  borderRadius: "6px",
                  border: "1px solid #cbd5e1",
                  width: "130px",
                }}
              />
              <label style={{ fontSize: "12px", fontWeight: 600, color: "#334155" }}>
                SLA (hrs):{" "}
                <input
                  aria-label="Admin SLA Hours"
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
              </label>
              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "5px",
                  fontSize: "12px",
                  fontWeight: 700,
                  color: "#003B7E",
                  cursor: "pointer",
                }}
              >
                <input
                  aria-label="Admin Require Finance Gate"
                  type="checkbox"
                  checked={newRuleFinanceGate}
                  onChange={(e) => onNewRuleFinanceGateChange(e.target.checked)}
                />
                Require Finance Gate
              </label>
              <button
                type="submit"
                style={{
                  marginLeft: "auto",
                  padding: "7px 14px",
                  background: "#003B7E",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "6px",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                + Add Rule
              </button>
            </div>
          </form>

          <div style={{ maxHeight: "220px", overflowY: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
              <thead>
                <tr style={{ background: "#f1f5f9", textAlign: "left" }}>
                  <th style={{ padding: "6px 8px" }}>Rule Name</th>
                  <th style={{ padding: "6px 8px" }}>Min Grade</th>
                  <th style={{ padding: "6px 8px" }}>Min Cost</th>
                  <th style={{ padding: "6px 8px" }}>Finance Gate</th>
                  <th style={{ padding: "6px 8px" }}>SLA</th>
                  <th style={{ padding: "6px 8px" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rl) => (
                  <tr
                    key={rl.id}
                    style={{
                      borderBottom: "1px solid #e2e8f0",
                      opacity: rl.is_active === false ? 0.55 : 1,
                    }}
                  >
                    <td style={{ padding: "6px 8px", fontWeight: 700 }}>{rl.rule_name}</td>
                    <td style={{ padding: "6px 8px" }}>{rl.min_grade || "Any"}</td>
                    <td style={{ padding: "6px 8px" }}>{formatINR(rl.min_total_cost)}</td>
                    <td style={{ padding: "6px 8px", fontWeight: 700 }}>
                      {rl.requires_finance_review ? "YES" : "NO"}
                    </td>
                    <td style={{ padding: "6px 8px" }}>{rl.sla_hours}h</td>
                    <td style={{ padding: "6px 8px", display: "flex", gap: "4px" }}>
                      <button
                        type="button"
                        onClick={() => onToggleRuleActive(rl)}
                        style={{
                          padding: "2px 7px",
                          fontSize: "11px",
                          borderRadius: "4px",
                          border: "1px solid #cbd5e1",
                          background: rl.is_active === false ? "#dcfce7" : "#f8fafc",
                          cursor: "pointer",
                        }}
                      >
                        {rl.is_active === false ? "Enable" : "Pause"}
                      </button>
                      <button
                        type="button"
                        onClick={() => onDeleteRule(rl.id)}
                        style={{
                          padding: "2px 7px",
                          fontSize: "11px",
                          borderRadius: "4px",
                          border: "1px solid #fecaca",
                          background: "#fef2f2",
                          color: "#991b1b",
                          cursor: "pointer",
                        }}
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Application User Directory & Live Role/Rights Assignment */}
      <div
        style={{
          background: "#ffffff",
          border: "1px solid #cbd5e1",
          borderRadius: "10px",
          padding: "20px",
          marginBottom: "24px",
          boxShadow: "0 2px 6px rgba(0, 59, 126, 0.05)",
        }}
      >
        <h3 style={{ marginTop: 0, color: METRO_COLORS.primaryNavy }}>
          Application User Directory &amp; Live Role / Rights Assignment ({users.length} Users)
        </h3>
        <p style={{ fontSize: "12px", color: "#475569", marginTop: 0 }}>
          Reassign any user&apos;s role below to immediately grant or revoke workflow approval and
          administration rights.
        </p>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
            <thead>
              <tr style={{ background: "#f1f5f9", textAlign: "left" }}>
                <th style={{ padding: "10px" }}>User / ID</th>
                <th style={{ padding: "10px" }}>Corporate Email</th>
                <th style={{ padding: "10px" }}>Business Unit &amp; Dept</th>
                <th style={{ padding: "10px" }}>Assigned Role (Change Rights)</th>
                <th style={{ padding: "10px" }}>Granted Rights &amp; Authorities</th>
                <th style={{ padding: "10px" }}>Status &amp; Session</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const roleMeta = ROLE_RIGHTS_CATALOG[u.role] || ROLE_RIGHTS_CATALOG.REQUEST_CREATOR;
                const deptObj = departments.find((d) => d.id === u.department_id);
                const isActive = u.is_active !== false;
                return (
                  <tr
                    key={u.id}
                    style={{
                      borderBottom: "1px solid #e2e8f0",
                      background: u.id === currentUserId ? "rgba(0, 137, 203, 0.06)" : "transparent",
                      opacity: isActive ? 1 : 0.6,
                    }}
                  >
                    <td style={{ padding: "10px" }}>
                      <div style={{ fontWeight: 800, color: METRO_COLORS.primaryNavy }}>
                        {u.full_name}
                      </div>
                      <div style={{ fontSize: "11px", color: "#64748b" }}>ID: {u.id}</div>
                    </td>
                    <td style={{ padding: "10px", fontFamily: "monospace", fontSize: "12px" }}>
                      {u.email}
                    </td>
                    <td style={{ padding: "10px" }}>
                      <div style={{ fontWeight: 600 }}>{u.business_unit}</div>
                      <div style={{ fontSize: "11px", color: "#64748b" }}>
                        {deptObj ? `${deptObj.code} — ${deptObj.name}` : "Cross-Department"}
                      </div>
                    </td>
                    <td style={{ padding: "10px" }}>
                      <select
                        aria-label={`Role for ${u.full_name}`}
                        value={u.role}
                        onChange={(e) => onUpdateUserRole(u.id, e.target.value as UserRole)}
                        style={{
                          padding: "6px 10px",
                          borderRadius: "6px",
                          border: "1px solid #94a3b8",
                          fontWeight: 700,
                          background: roleMeta.badgeBg,
                          color: roleMeta.badgeFg,
                          cursor: "pointer",
                        }}
                      >
                        {ALL_ROLES.map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td style={{ padding: "10px" }}>
                      <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                        {roleMeta.rights.map((rt) => (
                          <span
                            key={rt}
                            style={{
                              background: "#f1f5f9",
                              color: "#334155",
                              padding: "2px 7px",
                              borderRadius: "4px",
                              fontSize: "11px",
                              fontWeight: 600,
                            }}
                          >
                            {rt}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td style={{ padding: "10px" }}>
                      <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                        <button
                          type="button"
                          onClick={() => onToggleUserActive(u)}
                          style={{
                            padding: "4px 8px",
                            borderRadius: "5px",
                            border: "1px solid #cbd5e1",
                            background: isActive ? "#dcfce7" : "#fee2e2",
                            color: isActive ? "#166534" : "#991b1b",
                            fontWeight: 700,
                            fontSize: "11px",
                            cursor: "pointer",
                          }}
                        >
                          {isActive ? "Active" : "Suspended"}
                        </button>
                        {isActive && u.id !== currentUserId && (
                          <button
                            type="button"
                            onClick={() => onSelectActingUser(u.id)}
                            style={{
                              padding: "4px 8px",
                              borderRadius: "5px",
                              border: "1px solid #003B7E",
                              background: "#ffffff",
                              color: "#003B7E",
                              fontWeight: 700,
                              fontSize: "11px",
                              cursor: "pointer",
                            }}
                          >
                            Act As
                          </button>
                        )}
                        {u.id === currentUserId && (
                          <span
                            style={{
                              fontSize: "11px",
                              fontWeight: 800,
                              color: METRO_COLORS.primaryNavy,
                            }}
                          >
                            (Current Session)
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* RBAC & Segregation of Duties Reference Matrix */}
      <div
        style={{
          background: "#ffffff",
          border: "1px solid #cbd5e1",
          borderRadius: "10px",
          padding: "20px",
        }}
      >
        <h3 style={{ marginTop: 0, color: METRO_COLORS.primaryNavy }}>
          Enterprise RBAC &amp; Segregation of Duties (SoD) Matrix
        </h3>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
            <thead>
              <tr style={{ background: "#f1f5f9", textAlign: "left" }}>
                <th style={{ padding: "8px" }}>Role Identifier</th>
                <th style={{ padding: "8px" }}>Create / Submit Request</th>
                <th style={{ padding: "8px" }}>Stage 1: Manager Review</th>
                <th style={{ padding: "8px" }}>Stage 2: Finance Gate</th>
                <th style={{ padding: "8px" }}>Stage 3: People Committee</th>
                <th style={{ padding: "8px" }}>User &amp; Rule Admin</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: "1px solid #e2e8f0" }}>
                <td style={{ padding: "8px", fontWeight: 700 }}>REQUEST_CREATOR</td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>✓ Allowed</td>
                <td style={{ padding: "8px", color: "#991b1b" }}>✕ Blocked</td>
                <td style={{ padding: "8px", color: "#991b1b" }}>✕ Blocked</td>
                <td style={{ padding: "8px", color: "#991b1b" }}>✕ Blocked</td>
                <td style={{ padding: "8px", color: "#991b1b" }}>✕ Blocked</td>
              </tr>
              <tr style={{ borderBottom: "1px solid #e2e8f0" }}>
                <td style={{ padding: "8px", fontWeight: 700 }}>HIRING_MANAGER</td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>✓ Allowed</td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>
                  ✓ Allowed (SoD on own)
                </td>
                <td style={{ padding: "8px", color: "#991b1b" }}>✕ Blocked</td>
                <td style={{ padding: "8px", color: "#991b1b" }}>✕ Blocked</td>
                <td style={{ padding: "8px", color: "#991b1b" }}>✕ Blocked</td>
              </tr>
              <tr style={{ borderBottom: "1px solid #e2e8f0" }}>
                <td style={{ padding: "8px", fontWeight: 700 }}>HRBP</td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>✓ Allowed</td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>
                  ✓ Allowed (SoD on own)
                </td>
                <td style={{ padding: "8px", color: "#64748b" }}>Via Delegation</td>
                <td style={{ padding: "8px", color: "#64748b" }}>Via Delegation</td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>✓ Allowed</td>
              </tr>
              <tr style={{ borderBottom: "1px solid #e2e8f0" }}>
                <td style={{ padding: "8px", fontWeight: 700 }}>FINANCE_REVIEWER</td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>✓ Allowed</td>
                <td style={{ padding: "8px", color: "#64748b" }}>Via Delegation</td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>
                  ✓ Mandatory Gate Sign-off
                </td>
                <td style={{ padding: "8px", color: "#64748b" }}>Via Delegation</td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>✓ Rules Admin</td>
              </tr>
              <tr style={{ borderBottom: "1px solid #e2e8f0" }}>
                <td style={{ padding: "8px", fontWeight: 700 }}>COMMITTEE_MEMBER</td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>✓ Allowed</td>
                <td style={{ padding: "8px", color: "#64748b" }}>Via Delegation</td>
                <td style={{ padding: "8px", color: "#991b1b" }}>✕ Cannot Skip Gate</td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>
                  ✓ Final Committee Sign-off
                </td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>✓ Allowed</td>
              </tr>
              <tr style={{ borderBottom: "1px solid #e2e8f0" }}>
                <td style={{ padding: "8px", fontWeight: 700 }}>ADMIN</td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>✓ Allowed</td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>
                  ✓ Allowed (SoD on own)
                </td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>
                  ✓ Allowed (SoD on own)
                </td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>
                  ✓ Allowed (SoD on own)
                </td>
                <td style={{ padding: "8px", color: "#166534", fontWeight: 700 }}>
                  ✓ Full Platform Admin
                </td>
              </tr>
              <tr>
                <td style={{ padding: "8px", fontWeight: 700 }}>EXEC_READONLY</td>
                <td style={{ padding: "8px", color: "#991b1b" }}>✕ Read-Only</td>
                <td style={{ padding: "8px", color: "#991b1b" }}>✕ Read-Only</td>
                <td style={{ padding: "8px", color: "#991b1b" }}>✕ Read-Only</td>
                <td style={{ padding: "8px", color: "#991b1b" }}>✕ Read-Only</td>
                <td style={{ padding: "8px", color: "#991b1b" }}>✕ Read-Only</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
