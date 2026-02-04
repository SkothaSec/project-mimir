variable "project_id" {
    description = "The GCP project ID where resources will be created."
    type = string
    default = "project-mimir-486403"
}
variable "region" {
    description = "The GCP region where resources will be created."
    type = string
    default = "us-central1"
}