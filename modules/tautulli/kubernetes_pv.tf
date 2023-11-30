resource "kubernetes_persistent_volume" "plexlogs" {
  metadata {
    name = "plex-logs"
    labels = {
      type = "plex-logs"
    }
  }
  spec {
    capacity = {
      storage = "10Gi"
    }

    storage_class_name = "nfs-plex-logs"
    access_modes       = ["ReadWriteMany"]

    persistent_volume_source {
      nfs {
        server = "192.168.11.199"
        path   = "/plexlogs"
      }
    }
  }
}
