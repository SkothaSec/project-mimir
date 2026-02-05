variable "project_id" {
    description = "The GCP project ID where resources will be created. Set via TF_VAR_project_id env var."
    type = string
    default = null
    validation {
        condition     = var.project_id != null && length(var.project_id) > 0
        error_message = "Set TF_VAR_project_id (or -var project_id=...) to your GCP project."
    }
}
variable "region" {
    description = "The GCP region where resources will be created."
    type = string
    default = "us-central1"
}
