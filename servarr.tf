module "servarr_vars" {
  source               = "./modules/workspace_vars"
  namespace            = "servarr"
  timezone             = "America/New_York"
  uid                  = "997"
  gid                  = "997"
  nfs_server           = "192.168.11.131"
  media_library_size   = "10Ti"
  media_library_path   = "/volume2/media-library/"
  media_downloads_path = "/volume2/media-downloads/"
  media_downloads_size = "3Ti"
  k8s_services_path    = "/volume2/k8s-services/"
  k8s_services_size    = "10Gi"
  domain               = "a3f.link"
}

resource "kubernetes_namespace" "servarr" {
  metadata {
    name = module.servarr_vars.namespace
  }
}

module "servarr_k8s_services" {
  source     = "./modules/nfs-pv"
  namespace  = module.servarr_vars.namespace
  nfs_server = module.servarr_vars.nfs_server
  share_name = module.servarr_vars.k8s_services_name
  nfs_path   = module.servarr_vars.k8s_services_path
  capacity   = module.servarr_vars.k8s_services_size
  depends_on = [module.servarr_vars]
}


module "servarr_media_downloads" {
  source     = "./modules/nfs-pv"
  namespace  = module.servarr_vars.namespace
  nfs_server = module.servarr_vars.nfs_server
  share_name = module.servarr_vars.media_downloads_name
  nfs_path   = module.servarr_vars.media_downloads_path
  capacity   = module.servarr_vars.media_downloads_size
  depends_on = [module.servarr_vars]
}

module "servarr_media_library" {
  source     = "./modules/nfs-pv"
  namespace  = module.servarr_vars.namespace
  nfs_server = module.servarr_vars.nfs_server
  share_name = module.servarr_vars.media_library_name
  nfs_path   = module.servarr_vars.media_library_path
  capacity   = module.servarr_vars.media_library_size
  depends_on = [module.servarr_vars]
}

module "sonarr" {
  source         = "./modules/arr"
  service        = "sonarr"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_k8s_services, module.servarr_media_downloads, module.servarr_media_library]
}

module "radarr" {
  source         = "./modules/arr"
  service        = "radarr"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_k8s_services, module.servarr_media_downloads, module.servarr_media_library]
}

module "prowlarr" {
  source         = "./modules/arr"
  service        = "prowlarr"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_k8s_services]
}

module "bazarr" {
  source         = "./modules/arr"
  service        = "bazarr"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_k8s_services, module.servarr_media_downloads, module.servarr_media_library]
}

module "overseerr" {
  source         = "./modules/arr"
  service        = "overseerr"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_k8s_services]
}

module "nzbget" {
  source         = "./modules/nzbget"
  service        = "nzbget"
  port           = "6790"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_k8s_services, module.servarr_media_downloads]
}

module "muximux" {
  source         = "./modules/no-mounts"
  service        = "muximux"
  port           = "8383"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_k8s_services]
}

module "plexmetamanager" {
  source         = "./modules/no-mounts"
  service        = "plex-meta-manager"
  port           = "4321"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_k8s_services]
}

module "htpcmanager" {
  source         = "./modules/no-mounts"
  service        = "htpcmanager"
  port           = "8085"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_k8s_services]
}

module "tautulli" {
  source         = "./modules/tautulli"
  service        = "tautulli"
  port           = "8181"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_k8s_services]
}
