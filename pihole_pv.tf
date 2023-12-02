resource "kubernetes_persistent_volume" "pihole_k8s_services" {
  metadata {
    name = module.pihole_vars.k8s_services_name
    labels = {
      type = module.pihole_vars.k8s_services_name
    }
  }
  spec {
    capacity = {
      storage = module.pihole_vars.k8s_services_size
    }

    storage_class_name = "nfs-${module.pihole_vars.k8s_services_name}"
    access_modes       = ["ReadWriteMany"]

    persistent_volume_source {
      nfs {
        server = module.pihole_vars.nfs_server
        path   = module.pihole_vars.k8s_services_path
      }
    }
  }
  depends_on = [kubernetes_namespace.pihole]
}
