terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.40"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Artifact Registry (Docker Container Repository)
resource "google_artifact_registry_repository" "talentflow_repo" {
  location      = var.region
  repository_id = "talentflow-repo"
  description   = "TalentFlow Container Registry"
  format        = "DOCKER"
}

# 2. Cloud SQL for PostgreSQL (Pay-When-In-Use db-f1-micro with Activation Policy control)
resource "google_sql_database_instance" "talentflow_pg" {
  name                = "talentflow-pg-on-demand"
  database_version    = "POSTGRES_16"
  region              = var.region
  deletion_protection = false

  settings {
    tier              = "db-f1-micro"
    edition           = "ENTERPRISE"
    activation_policy = var.cloudsql_activation_policy # Toggle to NEVER when idle for $0 compute cost
    availability_type = "ZONAL"
    disk_size         = 10
    disk_type         = "PD_HDD"
    disk_autoresize   = false

    backup_configuration {
      enabled = false
    }
  }
}

resource "google_sql_database" "talentflow_db" {
  name     = "talentflow"
  instance = google_sql_database_instance.talentflow_pg.name
}

# 3. BigQuery Dataset (`talentflow_analytics`)
resource "google_bigquery_dataset" "talentflow_analytics" {
  dataset_id  = "talentflow_analytics"
  location    = var.region
  description = "TalentFlow Curated Hiring, People Committee & Workforce Cost Analytics"
}

# 4. Secret Manager Secrets
resource "google_secret_manager_secret" "db_url" {
  secret_id = "talentflow-db-url"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "talentflow-jwt-secret"
  replication {
    auto {}
  }
}

# 5. Cloud Run v2 Service (Scale-to-Zero: min_instance_count = 0)
resource "google_cloud_run_v2_service" "talentflow_app" {
  name     = "talentflow-app"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.runtime_sa.email

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.talentflow_pg.connection_name]
      }
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/talentflow-repo/talentflow-app:latest"

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "BQ_DATASET"
        value = google_bigquery_dataset.talentflow_analytics.dataset_id
      }
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_url.secret_id
            version = "latest"
          }
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }
  }
}
