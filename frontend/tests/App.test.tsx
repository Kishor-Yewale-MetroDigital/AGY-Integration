import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import App, { formatINR } from "../src/App";
import type {
  ApprovalDelegation,
  ApprovalRule,
  Department,
  HiringRequest,
  User,
} from "../src/types/talentflow";

function createStatefulFetchMock() {
  const users: User[] = [
    {
      id: "usr-committee",
      email: "priya.menon@metro-gsc.in",
      full_name: "Priya Menon",
      role: "COMMITTEE_MEMBER",
      business_unit: "Corporate",
      department_id: "dept-eng",
      is_active: true,
    },
    {
      id: "usr-admin",
      email: "admin@metro-gsc.in",
      full_name: "Vikram Deshmukh",
      role: "ADMIN",
      business_unit: "Digital & Technology",
      department_id: "dept-eng",
      is_active: true,
    },
    {
      id: "usr-hrbp",
      email: "meera.iyer@metro-gsc.in",
      full_name: "Meera Iyer",
      role: "HRBP",
      business_unit: "Human Resources",
      department_id: "dept-eng",
      is_active: true,
    },
    {
      id: "usr-creator",
      email: "ananya.sharma@metro-gsc.in",
      full_name: "Ananya Sharma",
      role: "REQUEST_CREATOR",
      business_unit: "Digital & Technology",
      department_id: "dept-eng",
      is_active: true,
    },
  ];

  const departments: Department[] = [
    {
      id: "dept-eng",
      code: "ENG-CLOUD",
      name: "Cloud Platform Engineering",
      business_unit: "Digital & Technology",
      cost_center: "CC-4100",
      allocated_budget: "85000000.00",
      committed_cost: "24000000.00",
      actual_spent: "12000000.00",
      currency: "INR",
    },
  ];

  const rules: ApprovalRule[] = [
    {
      id: "rule-seed-1",
      rule_name: "Senior Grade L6+ Finance Gate",
      min_grade: "L6",
      min_total_cost: "5000000.00",
      hiring_type: null,
      business_unit: null,
      location_country: null,
      requires_manager_review: true,
      requires_finance_review: true,
      requires_committee_review: true,
      sla_hours: 48,
      is_active: true,
    },
  ];

  const delegations: ApprovalDelegation[] = [];
  const requests: HiringRequest[] = [];

  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const method = (init?.method || "GET").toUpperCase();
    const headers = (init?.headers || {}) as Record<string, string>;
    const actingUserId = headers["X-User-Id"] || "usr-committee";
    const actingUser = users.find((u) => u.id === actingUserId);

    // Mirror backend get_current_user: reject inactive users on authenticated endpoints
    if (!url.endsWith("/api/v1/users") || method !== "GET") {
      if (!actingUser || actingUser.is_active === false) {
        return new Response(
          JSON.stringify({ detail: "Authenticated active user required." }),
          { status: 401, headers: { "Content-Type": "application/json" } }
        );
      }
    }

    const jsonResponse = (data: unknown, status = 200) =>
      new Response(JSON.stringify(data), {
        status,
        headers: { "Content-Type": "application/json" },
      });

    if (url.endsWith("/api/v1/users") && method === "GET") {
      return jsonResponse(users);
    }

    if (url.endsWith("/api/v1/users") && method === "POST") {
      const body = JSON.parse(String(init?.body || "{}"));
      const existing = users.find((u) => u.email === body.email);
      if (existing) {
        existing.full_name = body.full_name;
        existing.role = body.role;
        existing.business_unit = body.business_unit;
        existing.department_id = body.department_id ?? null;
        existing.is_active = body.is_active ?? true;
        return jsonResponse(existing, 201);
      }
      const created: User = {
        id: `usr-${users.length + 1}`,
        email: body.email,
        full_name: body.full_name,
        role: body.role,
        business_unit: body.business_unit,
        department_id: body.department_id ?? null,
        is_active: body.is_active ?? true,
      };
      users.push(created);
      return jsonResponse(created, 201);
    }

    if (url.includes("/api/v1/users/") && method === "PATCH") {
      const userId = url.split("/api/v1/users/")[1];
      const target = users.find((u) => u.id === userId);
      if (!target) return jsonResponse({ detail: "User not found." }, 404);
      const body = JSON.parse(String(init?.body || "{}"));
      if (body.role !== undefined) target.role = body.role;
      if (body.is_active !== undefined) target.is_active = body.is_active;
      if (body.full_name !== undefined) target.full_name = body.full_name;
      return jsonResponse(target, 200);
    }

    if (url.endsWith("/api/v1/departments") && method === "GET") {
      return jsonResponse(departments);
    }

    if (url.includes("/api/v1/requests") && method === "GET") {
      return jsonResponse(requests);
    }

    if (url.endsWith("/api/v1/requests") && method === "POST") {
      const body = JSON.parse(String(init?.body || "{}"));
      const created: HiringRequest = {
        id: `req-${requests.length + 1}`,
        request_code: `REQ-2026-00${requests.length + 1}`,
        job_title: body.job_title,
        job_family: body.job_family,
        department_id: body.department_id,
        business_unit: body.business_unit,
        country: body.country,
        city: body.city,
        work_location: body.work_location,
        job_grade: body.job_grade,
        employment_type: body.employment_type,
        hiring_manager_id: body.hiring_manager_id,
        request_owner_id: body.request_owner_id,
        hiring_type: body.hiring_type,
        headcount_requested: body.headcount_requested,
        justification: body.justification,
        expected_business_impact: body.expected_business_impact,
        requested_start_date: body.requested_start_date,
        target_hiring_date: body.target_hiring_date,
        currency: body.currency,
        est_annual_salary_per_pos: body.est_annual_salary_per_pos,
        est_benefits_cost_per_pos: body.est_benefits_cost_per_pos,
        est_recruitment_fee_per_pos: body.est_recruitment_fee_per_pos,
        est_onetime_cost_per_pos: body.est_onetime_cost_per_pos,
        total_annualized_forecast: "6350000.00",
        in_period_projected_cost: "3175000.00",
        status: "DRAFT",
        submitted_at: null,
        approved_at: null,
        closed_at: null,
        positions: [],
        approval_steps: [],
        approval_records: [],
      };
      requests.unshift(created);
      return jsonResponse(created, 201);
    }

    if (url.endsWith("/api/v1/approvals/rules") && method === "GET") {
      return jsonResponse(rules);
    }

    if (url.endsWith("/api/v1/approvals/rules") && method === "POST") {
      const body = JSON.parse(String(init?.body || "{}"));
      const existing = rules.find((r) => r.rule_name === body.rule_name);
      if (existing) {
        existing.min_grade = body.min_grade ?? null;
        existing.min_total_cost = body.min_total_cost ?? "0.00";
        existing.requires_finance_review = Boolean(body.requires_finance_review);
        existing.sla_hours = Number(body.sla_hours ?? 24);
        existing.is_active = true;
        return jsonResponse(existing, 201);
      }
      const created: ApprovalRule = {
        id: `rule-${rules.length + 1}`,
        rule_name: body.rule_name,
        min_grade: body.min_grade ?? null,
        min_total_cost: body.min_total_cost ?? "0.00",
        hiring_type: null,
        business_unit: null,
        location_country: null,
        requires_manager_review: true,
        requires_finance_review: Boolean(body.requires_finance_review),
        requires_committee_review: true,
        sla_hours: Number(body.sla_hours ?? 24),
        is_active: true,
      };
      rules.push(created);
      return jsonResponse(created, 201);
    }

    if (url.includes("/api/v1/approvals/rules/") && method === "PATCH") {
      const ruleId = url.split("/api/v1/approvals/rules/")[1];
      const target = rules.find((r) => r.id === ruleId);
      if (!target) return jsonResponse({ detail: "Rule not found." }, 404);
      const body = JSON.parse(String(init?.body || "{}"));
      if (body.is_active !== undefined) target.is_active = body.is_active;
      return jsonResponse(target, 200);
    }

    if (url.includes("/api/v1/approvals/rules/") && method === "DELETE") {
      const ruleId = url.split("/api/v1/approvals/rules/")[1];
      const idx = rules.findIndex((r) => r.id === ruleId);
      if (idx === -1) return jsonResponse({ detail: "Rule not found." }, 404);
      const [removed] = rules.splice(idx, 1);
      return jsonResponse({ deleted: true, id: ruleId, rule_name: removed.rule_name }, 200);
    }

    if (url.endsWith("/api/v1/approvals/delegations") && method === "GET") {
      return jsonResponse(delegations);
    }

    if (url.endsWith("/api/v1/approvals/delegations") && method === "POST") {
      const body = JSON.parse(String(init?.body || "{}"));
      const created: ApprovalDelegation = {
        id: `del-${delegations.length + 1}`,
        from_user_id: actingUserId,
        to_user_id: body.to_user_id,
        stage_name: body.stage_name,
        reason: body.reason,
        is_active: true,
      };
      delegations.push(created);
      return jsonResponse(created, 201);
    }

    if (url.includes("/api/v1/dashboard/overview")) {
      return jsonResponse({
        live_operational_metrics: {
          overdue_sla_requests: 0,
          workforce_and_cost: {
            total_requests: requests.length,
            pending_committee_requests: 0,
            approved_positions: 0,
            filled_positions: 0,
            open_approved_positions: 0,
            total_forecast_annual_cost_inr: "0.00",
            total_actual_annual_cost_inr: "0.00",
          },
        },
        bigquery_historical_analytics: {
          monthly_request_trend: [],
          grade_distribution: {},
        },
      });
    }

    if (url.includes("/api/v1/workforce/summary")) {
      return jsonResponse({
        total_requests: requests.length,
        pending_committee_requests: 0,
        approved_positions: 0,
        filled_positions: 0,
        open_approved_positions: 0,
        total_forecast_annual_cost_inr: "0.00",
        total_actual_annual_cost_inr: "0.00",
        delay_cost_projection: {
          estimated_productivity_loss_inr: "0.00",
          overtime_and_backfill_premium_inr: "0.00",
          total_cost_of_delay_inr: "0.00",
        },
      });
    }

    if (url.includes("/api/v1/audit-events")) {
      return jsonResponse([]);
    }

    return jsonResponse({});
  });
}

describe("TalentFlow Frontend Suite", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.stubGlobal("fetch", createStatefulFetchMock());
  });

  it("formats INR values accurately into Crores and Lakhs", () => {
    expect(formatINR("15760000.00")).toBe("₹1.58 Cr");
    expect(formatINR("4500000.00")).toBe("₹45.00 L");
    expect(formatINR("50000.00")).toBe("₹50,000.00");
  });

  it("renders Executive Overview KPIs and navigates across all 6 modules", async () => {
    render(<App />);
    expect(
      screen.getByText(/TalentFlow — Enterprise Hiring & People Committee Platform/i)
    ).toBeDefined();
    expect(screen.getByText(/Total Requests/i)).toBeDefined();
    expect(screen.getByText(/Pending Committee/i)).toBeDefined();
    expect(screen.getAllByText(/Approved Positions/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Monthly Hiring Request Trend/i)).toBeDefined();
    expect(screen.getByText(/Job Grade Distribution/i)).toBeDefined();

    // Navigate to Hiring Requests tab
    fireEvent.click(screen.getByText(/Hiring Requests \(/i));
    expect(screen.getByText(/Create New Hiring Requisition/i)).toBeDefined();
    expect(screen.getByText(/Save as Draft/i)).toBeDefined();

    // Navigate to People Committee Queue tab
    fireEvent.click(screen.getByText(/People Committee Queue/i));
    expect(
      screen.getByText(/People Committee & Multi-Stage Approval Queue/i)
    ).toBeDefined();
    expect(
      screen.getByText(/Auto-Select Authorized Stage Approver/i)
    ).toBeDefined();
    expect(screen.getByText(/Delegate Stage Approval Authority/i)).toBeDefined();
    expect(
      screen.getByText(/Configurable Governance & Approval Rules/i)
    ).toBeDefined();

    // Navigate to Workforce & Cost Planning tab
    fireEvent.click(screen.getByText(/Workforce & Cost Planning/i));
    expect(
      screen.getByText(/Department Budget Envelope vs. Commitments/i)
    ).toBeDefined();
    expect(screen.getByText(/Vacancy Delay Simulation/i)).toBeDefined();

    // Navigate to Immutable Audit Log tab
    fireEvent.click(screen.getByText(/Immutable Audit Log/i));
    expect(screen.getByText(/Immutable Governance Audit Log/i)).toBeDefined();

    // Navigate to Administration & Access tab
    fireEvent.click(screen.getByText(/Administration & Access/i));
    expect(
      screen.getByText(
        /Platform Administration — User Access, Role Rights & Governance Rules/i
      )
    ).toBeDefined();
    expect(
      screen.getByText(/Add User to Application & Assign Required Rights/i)
    ).toBeDefined();
    expect(
      screen.getByText(/Application User Directory & Live Role \/ Rights Assignment/i)
    ).toBeDefined();
    expect(
      screen.getByText(/Enterprise RBAC & Segregation of Duties \(SoD\) Matrix/i)
    ).toBeDefined();
  });

  it("exercises interactive form submissions (+ Add Rule, Grant Delegation, Add User, Role Update, Suspend Current User, Save Draft) without alert errors", async () => {
    render(<App />);

    // 1. People Committee Queue: submit '+ Add Rule' twice (verifying idempotency) and 'Grant Delegation'
    fireEvent.click(screen.getByText(/People Committee Queue/i));

    const addRuleBtn = screen.getByRole("button", { name: /\+ Add Rule/i });
    fireEvent.click(addRuleBtn);
    await waitFor(() => {
      expect(screen.getByRole("status").textContent).toMatch(
        /Saved configurable approval rule: Executive L7\+ Fast-Track Governance/i
      );
    });
    expect(screen.queryByRole("alert")).toBeNull();

    // Click '+ Add Rule' a second time with same default rule name to verify idempotent upsert
    fireEvent.click(addRuleBtn);
    await waitFor(() => {
      expect(screen.getByRole("status").textContent).toMatch(
        /Saved configurable approval rule: Executive L7\+ Fast-Track Governance/i
      );
    });
    expect(screen.queryByRole("alert")).toBeNull();

    // Grant Delegation
    fireEvent.click(screen.getByRole("button", { name: /Grant Delegation/i }));
    await waitFor(() => {
      expect(screen.getByRole("status").textContent).toMatch(
        /Delegated COMMITTEE_PENDING authority/i
      );
    });
    expect(screen.queryByRole("alert")).toBeNull();

    // 2. Administration & Access: provision new user, update role, pause/remove rule, and suspend current acting user
    fireEvent.click(screen.getByText(/Administration & Access/i));

    fireEvent.click(
      screen.getByRole("button", { name: /\+ Add User & Assign Rights/i })
    );
    await waitFor(() => {
      expect(screen.getByRole("status").textContent).toMatch(
        /User "Neha Kulkarni" \(neha\.kulkarni@metro-gsc\.in\) provisioned with role & rights: \[COMMITTEE_MEMBER\]/i
      );
    });
    expect(screen.queryByRole("alert")).toBeNull();

    // Change Neha Kulkarni's role via live role selector (wait for refreshAll to render new row)
    const roleSelect = await screen.findByLabelText(
      /Role for Neha Kulkarni/i
    );
    fireEvent.change(roleSelect, { target: { value: "FINANCE_REVIEWER" } });
    await waitFor(() => {
      expect(screen.getByRole("status").textContent).toMatch(
        /Updated role & workflow rights for Neha Kulkarni .* \[FINANCE_REVIEWER\]/i
      );
    });
    expect(screen.queryByRole("alert")).toBeNull();

    // Suspend the currently acting user (Priya Menon / usr-committee) and verify auto-switch prevents 401 alert
    const suspendBtns = await screen.findAllByRole("button", { name: /^Active$/i });
    fireEvent.click(suspendBtns[0]);
    await waitFor(() => {
      expect(screen.getByRole("status").textContent).toMatch(
        /Account status for .* set to SUSPENDED/i
      );
    });
    expect(screen.queryByRole("alert")).toBeNull();

    // Pause a rule in Administration tab
    const pauseButtons = await screen.findAllByRole("button", { name: /Pause/i });
    fireEvent.click(pauseButtons[0]);
    await waitFor(() => {
      expect(screen.getByRole("status").textContent).toMatch(/is now PAUSED/i);
    });
    expect(screen.queryByRole("alert")).toBeNull();

    // 3. Hiring Requests: Save as Draft
    fireEvent.click(screen.getByText(/Hiring Requests \(/i));
    fireEvent.click(screen.getByRole("button", { name: /Save as Draft/i }));
    await waitFor(() => {
      expect(screen.getByRole("status").textContent).toMatch(
        /Saved REQ-2026-001 .* as DRAFT/i
      );
    });
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
