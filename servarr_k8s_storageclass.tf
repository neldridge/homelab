resource "kubernetes_storage_class" "nfs_media_library" {
  metadata {
    name = "nfs-${module.servarr_vars.media_library_name}"
  }
  storage_provisioner    = "nfs.csi.k8s.io"
  reclaim_policy         = "Delete"
  volume_binding_mode    = "Immediate"
  allow_volume_expansion = false
  parameters = {
    server = module.servarr_vars.nfs_server
    share  = trimsuffix(module.servarr_vars.media_library_path, "/")
  }
  mount_options = [
    "hard",
    "nfsvers=4.1"
  ]
}

resource "kubernetes_storage_class" "nfs_media_downloads" {
  metadata {
    name = "nfs-${module.servarr_vars.media_downloads_name}"
  }
  storage_provisioner    = "nfs.csi.k8s.io"
  reclaim_policy         = "Delete"
  volume_binding_mode    = "Immediate"
  allow_volume_expansion = false
  parameters = {
    server = module.servarr_vars.nfs_server
    share  = trimsuffix(module.servarr_vars.media_downloads_path, "/")
  }
  mount_options = [
    "hard",
    "nfsvers=4.1"
  ]
}
