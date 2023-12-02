variable "namespace" {
  description = "The namespace to deploy to"
  type        = string
}

variable "share_name" {
  description = "The name of the share"
  type        = string
}

variable "capacity" {
  description = "The capacity of the PV"
  type        = string
}

variable "nfs_server" {
  description = "The NFS server to use"
  type        = string
}

variable "nfs_path" {
  description = "The NFS path to use"
  type        = string
}

locals {
  volume_name = "nfs-${var.share_name}"
}

