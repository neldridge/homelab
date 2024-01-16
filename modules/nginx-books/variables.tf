variable "workspace_vars" {
  type        = any
  description = "This should be the module from the root level environment passed through for use locally"
}

variable "service" {
  type        = string
  description = "Name of the service to create"
}

variable "container_image" {
  type        = string
  description = "Container image to use for the service"
  default     = "nginx"
}

variable "container_tag" {
  type        = string
  description = "Container tag to use for the service"
  default     = "latest"
}

variable "extra_env_vars" {
  type        = map(string)
  description = "Extra environment variables to pass to the container"
  default     = {}
}
