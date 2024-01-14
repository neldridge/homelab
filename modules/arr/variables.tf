variable "workspace_vars" {
  type        = any
  description = "This should be the module from the root level environment passed through for use locally"
}

variable "service" {
  type        = string
  description = "Name of the service to create"
}

variable "iscsi_portal" {
  type    = string
  default = ""
}

variable "iscsi_iqn" {
  type    = string
  default = ""
}

variable "iscsi_lun" {
  type    = number
  default = 1
}

variable "iscsi_fs_type" {
  type    = string
  default = "ext4"
}

variable "iscsi_read_only" {
  type    = bool
  default = false
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

locals {
  port_mapping = {
    radarr        = "7878"
    sonarr        = "8989"
    bazarr        = "6767"
    prowlarr      = "9696"
    overseerr     = "5055"
    readarr       = "8787"
    lidarr        = "8686"
    whisparr      = "6969"
    lazylibrarian = "5299"
  }
}
