export type UserRole =
  | "REQUEST_CREATOR"
  | "HIRING_MANAGER"
  | "HRBP"
  | "FINANCE_REVIEWER"
  | "COMMITTEE_MEMBER"
  | "ADMIN"
  | "EXEC_READONLY";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  business_unit: string;
  department_id: string | null;
}

export interface Department {
  id: string;
  code: string;
  name: string;
  business_unit: string;
  cost_center: string;
  allocated_budget: string;
  committed_cost: string;
  actual_spent: string;
  currency: string;
}

export interface Position {
  id: string;
  position_index: number;
  position_code: string;
  status: string;
  target_hire_date: string;
  outcome?: {
    id: string;
    candidate_ref: string;
    actual_hire_date: string;
    actual_annual_base_salary: string;
    closure_status: string;
    closure_reason: string;
  } | null;
}

export interface ApprovalStep {
  id: string;
  sequence_order: number;
  stage_name: string;
  required_role: string;
  step_status: string;
  due_at: string | null;
  completed_at: string | null;
  is_overdue: boolean;
}

export interface ApprovalRecord {
  id: string;
  approval_step_id: string;
  approver_id: string;
  delegated_from_id: string | null;
  stage_name: string;
  decision: string;
  comments: string;
  created_at: string;
}

export interface HiringRequest {
  id: string;
  request_code: string;
  job_title: string;
  job_family: string;
  department_id: string;
  business_unit: string;
  country: string;
  city: string;
  work_location: "ONSITE" | "HYBRID" | "REMOTE";
  job_grade: "L3" | "L4" | "L5" | "L6" | "L7" | "L8" | "EXEC";
  employment_type: "FULL_TIME" | "CONTRACT" | "PART_TIME";
  hiring_manager_id: string;
  request_owner_id: string;
  hiring_type: "NEW_HEADCOUNT" | "REPLACEMENT";
  headcount_requested: number;
  justification: string;
  expected_business_impact: string;
  requested_start_date: string;
  target_hiring_date: string;
  currency: string;
  est_annual_salary_per_pos: string;
  est_benefits_cost_per_pos: string;
  est_recruitment_fee_per_pos: string;
  est_onetime_cost_per_pos: string;
  total_annualized_forecast: string;
  in_period_projected_cost: string;
  status: string;
  submitted_at: string | null;
  approved_at: string | null;
  closed_at: string | null;
  positions: Position[];
  approval_steps: ApprovalStep[];
  approval_records: ApprovalRecord[];
}
