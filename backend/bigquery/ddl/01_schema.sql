-- BigQuery DDL for dataset `talentflow_analytics`
-- Enforces NUMERIC(18, 2) for financial precision and partitioning/clustering for low-cost queries

CREATE SCHEMA IF NOT EXISTS `talentflow_analytics`
OPTIONS(
  location = 'asia-south1',
  description = 'TalentFlow Curated Hiring, People Committee & Workforce Cost Analytics'
);

CREATE TABLE IF NOT EXISTS `talentflow_analytics.fact_hiring_requests_snapshot` (
  request_id STRING NOT NULL,
  request_code STRING NOT NULL,
  job_title STRING NOT NULL,
  job_family STRING NOT NULL,
  department_id STRING NOT NULL,
  business_unit STRING NOT NULL,
  country STRING NOT NULL,
  city STRING NOT NULL,
  work_location STRING NOT NULL,
  job_grade STRING NOT NULL,
  hiring_type STRING NOT NULL,
  headcount_requested INT64 NOT NULL,
  currency STRING NOT NULL,
  total_annualized_forecast_inr NUMERIC(18, 2) NOT NULL,
  status STRING NOT NULL,
  submitted_month STRING NOT NULL,
  approval_turnaround_hours FLOAT64,
  updated_at TIMESTAMP NOT NULL
)
CLUSTER BY business_unit, department_id, status;

CREATE TABLE IF NOT EXISTS `talentflow_analytics.fact_positions` (
  position_id STRING NOT NULL,
  request_id STRING NOT NULL,
  position_code STRING NOT NULL,
  business_unit STRING NOT NULL,
  department_id STRING NOT NULL,
  job_grade STRING NOT NULL,
  country STRING NOT NULL,
  position_status STRING NOT NULL,
  request_status STRING NOT NULL,
  actual_cost_inr NUMERIC(18, 2) NOT NULL,
  days_to_fill INT64
)
CLUSTER BY business_unit, job_grade, position_status;

CREATE TABLE IF NOT EXISTS `talentflow_analytics.fact_approval_events` (
  approval_record_id STRING NOT NULL,
  request_id STRING NOT NULL,
  stage_name STRING NOT NULL,
  approver_id STRING NOT NULL,
  decision STRING NOT NULL,
  created_at TIMESTAMP NOT NULL
)
CLUSTER BY stage_name, decision;
