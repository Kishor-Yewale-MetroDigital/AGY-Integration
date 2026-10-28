output "cloud_run_url" {
  description = "Deployed TalentFlow Cloud Run Service URL"
  value       = google_cloud_run_v2_service.talentflow_app.uri
}

output "cloudsql_connection_name" {
  description = "Cloud SQL PostgreSQL Instance Connection Name"
  value       = google_sql_database_instance.talentflow_pg.connection_name
}

output "bigquery_dataset_id" {
  description = "BigQuery Analytics Dataset ID"
  value       = google_bigquery_dataset.talentflow_analytics.dataset_id
}

output "wif_provider_name" {
  description = "Workload Identity Provider resource name for GitHub Actions"
  value       = google_iam_workload_identity_pool_provider.github_provider.name
}
