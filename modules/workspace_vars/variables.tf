variable "timezone" {
  type        = string
  description = "Timezone for the container"
  default     = "America/New_York"
}

variable "namespace" {
  type        = string
  description = "K8s namespace to deploy to"
}

variable "uid" {
  type        = string
  description = "UID for the container"
}

variable "gid" {
  type        = string
  description = "GID for the container"
}

variable "nfs_server" {
  type        = string
  description = "NFS server"
}

variable "media_library_name" {
  type        = string
  description = "Name of the media library"
  default     = "media-library"
}

variable "media_library_path" {
  type        = string
  description = "Path to the media library"
}

variable "media_library_size" {
  type        = string
  description = "Size of the media library"
}

variable "media_downloads_name" {
  type        = string
  description = "Name of the media downloads"
  default     = "media-downloads"
}

variable "media_downloads_path" {
  type        = string
  description = "Path to the media downloads"
}

variable "media_downloads_size" {
  type        = string
  description = "Size of the media downloads"
}

variable "k8s_services_name" {
  type        = string
  description = "Name of the k8s services"
  default     = "k8s-services"
}

variable "k8s_services_path" {
  type        = string
  description = "Path to the k8s services"
}

variable "k8s_services_size" {
  type        = string
  description = "Size of the k8s services"
}
