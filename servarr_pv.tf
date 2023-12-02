resource "kubernetes_persistent_volume" "k8s_services" {
  metadata {
    name = module.servarr_vars.k8s_services_name
    labels = {
      type = module.servarr_vars.k8s_services_name
    }
  }
  spec {
    capacity = {
      storage = module.servarr_vars.k8s_services_size
    }

    storage_class_name = "nfs-${module.servarr_vars.k8s_services_name}"
    access_modes       = ["ReadWriteMany"]

    persistent_volume_source {
      nfs {
        server = module.servarr_vars.nfs_server
        path   = module.servarr_vars.k8s_services_path
      }
    }
  }
  depends_on = [kubernetes_namespace.servarr]
}

resource "kubernetes_persistent_volume" "media_downloads" {
  metadata {
    name = module.servarr_vars.media_downloads_name
    labels = {
      type = module.servarr_vars.media_downloads_name
    }
  }
  spec {
    capacity = {
      storage = module.servarr_vars.media_library_size
    }

    storage_class_name = "nfs-${module.servarr_vars.media_downloads_name}"
    access_modes       = ["ReadWriteMany"]

    persistent_volume_source {
      nfs {
        server = module.servarr_vars.nfs_server
        path   = module.servarr_vars.media_downloads_path
      }
    }
  }
  depends_on = [kubernetes_namespace.servarr]
}

resource "kubernetes_persistent_volume" "media_library" {
  metadata {
    name = module.servarr_vars.media_library_name
    labels = {
      type = module.servarr_vars.media_library_name
    }
  }
  spec {
    capacity = {
      storage = module.servarr_vars.media_library_size
    }

    storage_class_name = "nfs-${module.servarr_vars.media_library_name}"
    access_modes       = ["ReadWriteMany"]

    persistent_volume_source {
      nfs {
        server = module.servarr_vars.nfs_server
        path   = module.servarr_vars.media_library_path
      }
    }
  }
  depends_on = [kubernetes_namespace.servarr]
}
