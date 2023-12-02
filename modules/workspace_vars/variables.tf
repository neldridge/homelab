variable "timezone" {
  type        = string
  description = "Timezone for the container"
  default     = "America/New_York"
}

variable "namespace" {
  type        = string
  description = "K8s namespace to deploy to"
}

variable "domain" {
  type        = string
  description = "Domain to use for the service"
}

variable "uid" {
  type        = string
  description = "UID for the container"
  default     = ""
}

variable "gid" {
  type        = string
  description = "GID for the container"
  default     = ""
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
  default     = ""
}

variable "media_library_size" {
  type        = string
  description = "Size of the media library"
  default     = ""
}

variable "media_downloads_name" {
  type        = string
  description = "Name of the media downloads"
  default     = "media-downloads"
}

variable "media_downloads_path" {
  type        = string
  description = "Path to the media downloads"
  default     = ""
}

variable "media_downloads_size" {
  type        = string
  description = "Size of the media downloads"
  default     = ""
}

variable "k8s_services_name" {
  type        = string
  description = "Name of the k8s services"
  default     = "k8s-services"
}

variable "k8s_services_path" {
  type        = string
  description = "Path to the k8s services"
  default     = ""
}

variable "k8s_services_size" {
  type        = string
  description = "Size of the k8s services"
  default     = ""
}
