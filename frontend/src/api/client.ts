import type {
  ApprovalDelegation,
  ApprovalRule,
  Department,
  HiringRequest,
  User,
} from "../types/talentflow";

const API_BASE = "/api/v1";

let activeUserId = "usr-committee";

export function setActiveUserId(userId: string): void {
  activeUserId = userId;
}

export function getActiveUserId(): string {
  return activeUserId;
}

async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  overrideUserId?: string,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-User-Id": overrideUserId || activeUserId,
    ...(options.headers as Record<string, string> | undefined),
  };

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    let parsedDetail = errorBody;
    try {
      const jsonErr = JSON.parse(errorBody);
      if (typeof jsonErr.detail === "string") {
        parsedDetail = jsonErr.detail;
      } else if (Array.isArray(jsonErr.detail)) {
        parsedDetail = jsonErr.detail
          .map((e: { loc?: string[]; msg?: string }) => `${(e.loc || []).join(".")}: ${e.msg}`)
          .join("; ");
      }
    } catch {
      // keep text
    }
    throw new Error(`API Error ${response.status}: ${parsedDetail}`);
  }

  return response.json() as Promise<T>;
}

function buildQuery(params?: Record<string, string | number | undefined>): string {
  if (!params) return "";
  const searchParams = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") {
      searchParams.set(k, String(v));
    }
  }
  const qs = searchParams.toString();
  return qs ? `?${qs}` : "";
}

export async function fetchUsers(): Promise<User[]> {
  return apiRequest<User[]>("/users");
}

export async function fetchDepartments(): Promise<Department[]> {
  return apiRequest<Department[]>("/departments");
}

export async function fetchRequests(filters?: {
  status?: string;
  department_id?: string;
  business_unit?: string;
  country?: string;
  work_location?: string;
  job_grade?: string;
  hiring_type?: string;
  search?: string;
}): Promise<HiringRequest[]> {
  return apiRequest<HiringRequest[]>(`/requests${buildQuery(filters)}`);
}

export async function createHiringRequest(
  payload: Record<string, unknown>,
  overrideUserId?: string,
): Promise<HiringRequest> {
  return apiRequest<HiringRequest>(
    "/requests",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    overrideUserId,
  );
}

export async function updateHiringRequest(
  requestId: string,
  payload: Record<string, unknown>,
  overrideUserId?: string,
): Promise<HiringRequest> {
  return apiRequest<HiringRequest>(
    `/requests/${requestId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
    overrideUserId,
  );
}

export async function submitHiringRequest(
  requestId: string,
  overrideUserId?: string,
): Promise<HiringRequest> {
  return apiRequest<HiringRequest>(
    `/requests/${requestId}/submit`,
    {
      method: "POST",
    },
    overrideUserId,
  );
}

export async function submitApprovalDecision(
  requestId: string,
  decision: "APPROVE" | "REJECT" | "REQUEST_CLARIFICATION",
  comments: string,
  overrideUserId?: string,
): Promise<HiringRequest> {
  return apiRequest<HiringRequest>(
    `/requests/${requestId}/decisions`,
    {
      method: "POST",
      body: JSON.stringify({ decision, comments }),
    },
    overrideUserId,
  );
}

export async function recordPositionOutcome(
  requestId: string,
  positionId: string,
  payload: {
    candidate_ref: string;
    actual_hire_date: string;
    actual_annual_base_salary: string;
    actual_benefits_cost?: string;
    actual_recruitment_fee?: string;
    actual_onetime_cost?: string;
    closure_status: "HIRED" | "OFFER_DECLINED" | "CANCELLED";
    closure_reason: string;
  },
  overrideUserId?: string,
): Promise<HiringRequest> {
  return apiRequest<HiringRequest>(
    `/requests/${requestId}/positions/${positionId}/outcome`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    overrideUserId,
  );
}

export async function fetchApprovalRules(): Promise<ApprovalRule[]> {
  return apiRequest<ApprovalRule[]>("/approvals/rules");
}

export async function createApprovalRule(
  payload: Record<string, unknown>,
  overrideUserId?: string,
): Promise<{ id: string; rule_name: string }> {
  return apiRequest<{ id: string; rule_name: string }>(
    "/approvals/rules",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    overrideUserId,
  );
}

export async function fetchDelegations(): Promise<ApprovalDelegation[]> {
  return apiRequest<ApprovalDelegation[]>("/approvals/delegations");
}

export async function createDelegation(
  payload: {
    to_user_id: string;
    stage_name: "MANAGER_REVIEW" | "FINANCE_REVIEW" | "COMMITTEE_PENDING";
    reason: string;
  },
  overrideUserId?: string,
): Promise<ApprovalDelegation> {
  return apiRequest<ApprovalDelegation>(
    "/approvals/delegations",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    overrideUserId,
  );
}

export async function fetchWorkforceSummary(filters?: {
  department_id?: string;
  business_unit?: string;
  job_grade?: string;
  country?: string;
  hiring_type?: string;
  status?: string;
  delay_days?: number;
}): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>(`/workforce/summary${buildQuery(filters)}`);
}

export async function fetchDashboardOverview(filters?: {
  business_unit?: string;
  department_id?: string;
  country?: string;
  job_grade?: string;
  hiring_type?: string;
  status?: string;
}): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>(`/dashboard/overview${buildQuery(filters)}`);
}

export async function triggerBigQuerySync(): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>("/analytics/sync", { method: "POST" });
}

export async function populateDemoApprovalQueue(): Promise<{
  status: string;
  items: string[];
}> {
  return apiRequest<{ status: string; items: string[] }>("/demo/populate-queue", {
    method: "POST",
  });
}

export async function fetchAuditEvents(): Promise<Array<Record<string, unknown>>> {
  return apiRequest<Array<Record<string, unknown>>>("/audit-events");
}
