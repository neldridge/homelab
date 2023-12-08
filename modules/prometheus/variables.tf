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
  default     = ""
}

locals {
  container_image = (var.container_image == "" ? "lscr.io/linuxserver/${var.service}:latest" : var.container_image)

  http_ports = [
    { port = 9090, protocol = "TCP", name = "prometheus-http" },
  ]
}
