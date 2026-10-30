variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  default     = "cf-hackathon-ai-poc-testin-b1"
}

variable "region" {
  description = "Google Cloud Region"
  type        = string
  default     = "europe-west3"
}

variable "github_repository" {
  description = "GitHub repository in owner/repo format for Workload Identity Federation"
  type        = string
  default     = "Kishor-Yewale-MetroDigital/AGY-Integration"
}

variable "cloudsql_activation_policy" {
  description = "Pay-When-In-Use control: ALWAYS when actively testing, NEVER when stopped ($0 compute billing)"
  type        = string
  default     = "ALWAYS"
}
