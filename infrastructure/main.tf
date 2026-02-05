resource "google_project_service" "mimir_apis" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "pubsub.googleapis.com",
    "bigquery.googleapis.com",
    "aiplatform.googleapis.com", # For Vertex AI (Phase 3)
    "iam.googleapis.com",
    "cloudbuild.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  # Don't disable the service if we destroy the Terraform (safety net)
  disable_on_destroy = false
}

# Python logs pushed to pub/sub
resource "google_pubsub_topic" "mimir_ingest" {
    name = "mimir-ingest-topic"
} 
# Mimir Lake (BigQuery) Dataset
resource "google_bigquery_dataset" "mimir_lake" {
    dataset_id = "mimir_security_lake"
    location = "US"
}

# Investigations bigquery dataset
resource "google_bigquery_table" "investigations" {
    dataset_id = google_bigquery_dataset.mimir_lake.dataset_id
    table_id = "investigations_results"
    friendly_name = "Investigations Results"
    description = "Table to store investigation results"
    schema = file("${path.module}/schema.json")
}

# Artifact Registry where Docker images are stored
resource "google_artifact_registry_repository" "mimir_repo" {
    location = var.region
    repository_id = "mimir-repo"
    project       = var.project_id
    format = "DOCKER"
    description = "Artifact Registry for Mimir Docker images"
    depends_on = [google_project_service.mimir_apis]
}