resource "kubernetes_persistent_volume_claim" "k8s_services" {
  metadata {
    name      = module.workspace_vars.k8s_services_name
    namespace = module.workspace_vars.namespace
    labels = {
      type = module.workspace_vars.k8s_services_name
    }
  }
  spec {
    volume_name        = module.workspace_vars.k8s_services_name
    storage_class_name = "nfs-${module.workspace_vars.k8s_services_name}"
    access_modes       = ["ReadWriteMany"]
    selector {
      match_labels = {
        type = module.workspace_vars.k8s_services_name
      }
    }
    resources {
      requests = {
        storage = module.workspace_vars.k8s_services_size
      }
    }
  }
}

resource "kubernetes_persistent_volume_claim" "media_downloads" {
  metadata {
    name      = module.workspace_vars.media_downloads_name
    namespace = module.workspace_vars.namespace
    labels = {
      type = module.workspace_vars.media_downloads_name
    }
  }
  spec {
    volume_name        = module.workspace_vars.media_downloads_name
    storage_class_name = "nfs-${module.workspace_vars.media_downloads_name}"
    access_modes       = ["ReadWriteMany"]
    selector {
      match_labels = {
        type = module.workspace_vars.media_downloads_name
      }
    }
    resources {
      requests = {
        storage = module.workspace_vars.media_library_size
      }
    }
  }
}

resource "kubernetes_persistent_volume_claim" "media_library" {
  metadata {
    name      = module.workspace_vars.media_library_name
    namespace = module.workspace_vars.namespace
    labels = {
      type = module.workspace_vars.media_library_name
    }
  }
  spec {
    volume_name        = module.workspace_vars.media_library_name
    storage_class_name = "nfs-${module.workspace_vars.media_library_name}"
    access_modes       = ["ReadWriteMany"]
    selector {
      match_labels = {
        type = module.workspace_vars.media_library_name
      }
    }
    resources {
      requests = {
        storage = module.workspace_vars.media_library_size
      }
    }
  }
}
