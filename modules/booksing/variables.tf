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

variable "container_image" {
  type        = string
  description = "Container image to use for the service"
  default     = "neldridge/booksing"
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
    booksing = "7132"
  }
}
