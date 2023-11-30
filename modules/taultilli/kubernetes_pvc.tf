resource "kubernetes_persistent_volume_claim" "plexlogs" {
  metadata {
    name      = "plex-logs"
    namespace = module.workspace_vars.namespace
    labels = {
      type = "plex-logs"
    }
  }
  spec {
    volume_name        = "plex-logs"
    storage_class_name = "nfs-plex-logs"
    access_modes       = ["ReadWriteMany"]
    selector {
      match_labels = {
        type = "plex-logs"
      }
    }
    resources {
      requests = {
        storage = "10Gi"
      }
    }
  }
}
