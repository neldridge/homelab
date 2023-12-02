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
  dns_ports = [
    { port = 53, protocol = "UDP", name = "dns-udp" },
    { port = 53, protocol = "TCP", name = "dns-tcp" },
  ]
  http_ports = [
    { port = 80, protocol = "TCP", name = "pihole-http" },
    { port = 443, protocol = "TCP", name = "pihole-https" },
  ]
}
