resource "kubernetes_persistent_volume" "persistent_volume" {
  metadata {
    name = local.volume_name
    labels = {
      share   = var.share_name
      pv_name = local.volume_name
    }
  }
  spec {
    capacity = {
      storage = var.capacity
    }

    storage_class_name = local.storage_class_name
    access_modes       = ["ReadWriteMany"]

    persistent_volume_source {
      nfs {
        server = var.nfs_server
        path   = var.nfs_path
      }
    }
  }
}
