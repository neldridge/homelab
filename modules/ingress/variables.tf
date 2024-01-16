variable "workspace_vars" {
  type        = any
  description = "This should be the module from the root level environment passed through for use locally"
}

variable "service_scope" {
  type        = string
  description = "Name of the service to create"
}

variable "domains" {
  type = map(object({
    service = string
    port    = number
  }))
  description = "Name of the service(s) to create ingresses for"
}

locals {
  ingress_domains = [
    for domain, service in var.domains : "${domain}"
  ]
}
