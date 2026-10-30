-- Parameterized & Idempotent MERGE and Analytical Queries for `talentflow_analytics`

-- 1. Idempotent Incremental MERGE for Hiring Request Snapshots
MERGE `talentflow_analytics.fact_hiring_requests_snapshot` AS target
USING `talentflow_analytics.stg_hiring_requests` AS source
ON target.request_id = source.request_id
WHEN MATCHED AND source.updated_at >= target.updated_at THEN
  UPDATE SET
    status = source.status,
    headcount_requested = source.headcount_requested,
    total_annualized_forecast_inr = source.total_annualized_forecast_inr,
    approval_turnaround_hours = source.approval_turnaround_hours,
    updated_at = source.updated_at
WHEN NOT MATCHED THEN
  INSERT (
    request_id, request_code, job_title, job_family, department_id,
    business_unit, country, city, work_location, job_grade, hiring_type,
    headcount_requested, currency, total_annualized_forecast_inr, status,
    submitted_month, approval_turnaround_hours, updated_at
  )
  VALUES (
    source.request_id, source.request_code, source.job_title, source.job_family, source.department_id,
    source.business_unit, source.country, source.city, source.work_location, source.job_grade, source.hiring_type,
    source.headcount_requested, source.currency, source.total_annualized_forecast_inr, source.status,
    source.submitted_month, source.approval_turnaround_hours, source.updated_at
  );

-- 2. Parameterized Executive Overview Query (Avoids Multi-Position Double Counting)
SELECT
  COUNT(DISTINCT r.request_id) AS total_requests,
  COUNTIF(r.status = 'COMMITTEE_PENDING') AS pending_committee_requests,
  SUM(IF(r.status != 'CANCELLED', r.headcount_requested, 0)) AS requested_headcount,
  SUM(IF(r.status IN ('APPROVED', 'RECRUITING', 'PARTIALLY_FILLED', 'FILLED', 'CLOSED'), r.total_annualized_forecast_inr, 0)) AS approved_annual_cost_forecast_inr,
  ROUND(AVG(r.approval_turnaround_hours), 2) AS avg_approval_turnaround_hours
FROM `talentflow_analytics.fact_hiring_requests_snapshot` r
WHERE (@business_unit IS NULL OR r.business_unit = @business_unit)
  AND (@country IS NULL OR r.country = @country)
  AND (@job_grade IS NULL OR r.job_grade = @job_grade);
