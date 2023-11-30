variable "workspace_vars" {
  type = any
  description = "This should be the module from the root level environment passed through for use locally"
}

variable "service" {
  type = string
  description = "Name of the service to create"
}

locals {
  port_mapping = {
    radarr = "7878"
    sonarr = "8989"
    bazarr = "6767"
    prowlarr = "9696"
    overseerr = "5055"
  }
}
