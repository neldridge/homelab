resource "kubernetes_persistent_volume_claim" "persistent_volume_claim" {
  metadata {
    name      = local.volume_claim_name
    namespace = var.namespace
    labels = {
      share    = var.share_name
      pvc_name = local.volume_claim_name
    }
  }
  spec {
    volume_name        = local.volume_name
    storage_class_name = local.storage_class_name
    access_modes       = ["ReadWriteMany"]
    selector {
      match_labels = {
        share   = var.share_name
        pv_name = local.volume_name
      }
    }
    resources {
      requests = {
        storage = var.capacity
      }
    }
  }
  depends_on = [kubernetes_persistent_volume.persistent_volume]
}
