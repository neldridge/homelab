resource "kubernetes_persistent_volume_claim" "pihole_k8s_services" {
  metadata {
    name      = module.pihole_vars.k8s_services_name
    namespace = module.pihole_vars.namespace
    labels = {
      type = module.pihole_vars.k8s_services_name
    }
  }
  spec {
    volume_name        = module.pihole_vars.k8s_services_name
    storage_class_name = "nfs-${module.pihole_vars.k8s_services_name}"
    access_modes       = ["ReadWriteMany"]
    selector {
      match_labels = {
        type = module.pihole_vars.k8s_services_name
      }
    }
    resources {
      requests = {
        storage = module.pihole_vars.k8s_services_size
      }
    }
  }
  depends_on = [kubernetes_persistent_volume.pihole_k8s_services]
}
