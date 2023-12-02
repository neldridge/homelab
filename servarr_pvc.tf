resource "kubernetes_persistent_volume_claim" "k8s_services" {
  metadata {
    name      = module.servarr_vars.k8s_services_name
    namespace = module.servarr_vars.namespace
    labels = {
      type = module.servarr_vars.k8s_services_name
    }
  }
  spec {
    volume_name        = module.servarr_vars.k8s_services_name
    storage_class_name = "nfs-${module.servarr_vars.k8s_services_name}"
    access_modes       = ["ReadWriteMany"]
    selector {
      match_labels = {
        type = module.servarr_vars.k8s_services_name
      }
    }
    resources {
      requests = {
        storage = module.servarr_vars.k8s_services_size
      }
    }
  }
  depends_on = [kubernetes_persistent_volume.k8s_services]
}

resource "kubernetes_persistent_volume_claim" "media_downloads" {
  metadata {
    name      = module.servarr_vars.media_downloads_name
    namespace = module.servarr_vars.namespace
    labels = {
      type = module.servarr_vars.media_downloads_name
    }
  }
  spec {
    volume_name        = module.servarr_vars.media_downloads_name
    storage_class_name = "nfs-${module.servarr_vars.media_downloads_name}"
    access_modes       = ["ReadWriteMany"]
    selector {
      match_labels = {
        type = module.servarr_vars.media_downloads_name
      }
    }
    resources {
      requests = {
        storage = module.servarr_vars.media_library_size
      }
    }
  }
  depends_on = [kubernetes_persistent_volume.media_downloads]
}

resource "kubernetes_persistent_volume_claim" "media_library" {
  metadata {
    name      = module.servarr_vars.media_library_name
    namespace = module.servarr_vars.namespace
    labels = {
      type = module.servarr_vars.media_library_name
    }
  }
  spec {
    volume_name        = module.servarr_vars.media_library_name
    storage_class_name = "nfs-${module.servarr_vars.media_library_name}"
    access_modes       = ["ReadWriteMany"]
    selector {
      match_labels = {
        type = module.servarr_vars.media_library_name
      }
    }
    resources {
      requests = {
        storage = module.servarr_vars.media_library_size
      }
    }
  }
  depends_on = [kubernetes_persistent_volume.media_library]
}
