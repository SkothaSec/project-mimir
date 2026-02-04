provider "google" {
    project = var.project_id
    region  = var.region
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
    format = "DOCKER"
    description = "Artifact Registry for Mimir Docker images"
}