resource "kubernetes_persistent_volume" "k8s_services" {
  metadata {
    name = module.workspace_vars.k8s_services_name
    labels = {
      type = module.workspace_vars.k8s_services_name
    }
  }
  spec {
    capacity = {
      storage = "10Gi"
    }

    storage_class_name = "nfs-${module.workspace_vars.k8s_services_name}"
    access_modes = ["ReadWriteMany"]

    persistent_volume_source {
      nfs {
        server = module.workspace_vars.nfs_server
        path = module.workspace_vars.k8s_services_path
      }
    }
  }
}

resource "kubernetes_persistent_volume" "media_downloads" {
  metadata {
    name = module.workspace_vars.media_downloads_name
    labels = {
      type = module.workspace_vars.media_downloads_name
    }
  }
  spec {
    capacity = {
      storage = module.workspace_vars.media_library_size
    }

    storage_class_name = "nfs-${module.workspace_vars.media_downloads_name}"
    access_modes = ["ReadWriteMany"]

    persistent_volume_source {
      nfs {
        server = module.workspace_vars.nfs_server
        path = module.workspace_vars.media_downloads_path
      }
    }
  }
}

resource "kubernetes_persistent_volume" "media_library" {
  metadata {
    name = module.workspace_vars.media_library_name
    labels = {
      type = module.workspace_vars.media_library_name
    }
  }
  spec {
    capacity = {
      storage = module.workspace_vars.media_library_size
    }

    storage_class_name = "nfs-${module.workspace_vars.media_library_name}"
    access_modes = ["ReadWriteMany"]

    persistent_volume_source {
      nfs {
        server = module.workspace_vars.nfs_server
        path = module.workspace_vars.media_library_path
      }
    }
  }
}
