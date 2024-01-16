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
  domain               = "a3f.link"
}

resource "kubernetes_namespace" "servarr" {
  metadata {
    name = module.servarr_vars.namespace
  }
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

module "nginxbooks" {
  source         = "./modules/nginx-books"
  service        = "nginx-books"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_media_library]
}

module "lazylibrarian" {
  source  = "./modules/arr"
  service = "lazylibrarian"
  extra_env_vars = {
    "DOCKER_MODS" : "linuxserver/mods:universal-calibre|linuxserver/mods:lazylibrarian-ffmpeg"
  }
  iscsi_portal   = "192.168.11.131:3260"
  iscsi_iqn      = "iqn.2000-01.com.synology:pelican.lazylibrarian.7b01f1cb7fb"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_media_library]
}

module "readarr" {
  source         = "./modules/arr"
  service        = "readarr"
  container_tag  = "nightly"
  iscsi_portal   = "192.168.11.131:3260"
  iscsi_iqn      = "iqn.2000-01.com.synology:pelican.readarr.7b01f1cb7fb"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_media_downloads, module.servarr_media_library]
}

module "sonarr" {
  source         = "./modules/arr"
  service        = "sonarr"
  iscsi_portal   = "192.168.11.131:3260"
  iscsi_iqn      = "iqn.2000-01.com.synology:pelican.sonarr.7b01f1cb7fb"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_media_downloads, module.servarr_media_library]
}

module "radarr" {
  source         = "./modules/arr"
  service        = "radarr"
  iscsi_portal   = "192.168.11.131:3260"
  iscsi_iqn      = "iqn.2000-01.com.synology:pelican.radarr.7b01f1cb7fb"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_media_downloads, module.servarr_media_library]
}

module "prowlarr" {
  source         = "./modules/arr"
  service        = "prowlarr"
  iscsi_portal   = "192.168.11.131:3260"
  iscsi_iqn      = "iqn.2000-01.com.synology:pelican.prowlarr.7b01f1cb7fb"
  workspace_vars = module.servarr_vars
}

module "bazarr" {
  source         = "./modules/arr"
  service        = "bazarr"
  iscsi_portal   = "192.168.11.131:3260"
  iscsi_iqn      = "iqn.2000-01.com.synology:pelican.bazarr.7b01f1cb7fb"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_media_downloads, module.servarr_media_library]
}

module "overseerr" {
  source         = "./modules/arr"
  service        = "overseerr"
  iscsi_portal   = "192.168.11.131:3260"
  iscsi_iqn      = "iqn.2000-01.com.synology:pelican.overseerr.7b01f1cb7fb"
  workspace_vars = module.servarr_vars
}

module "nzbget" {
  source         = "./modules/nzbget"
  service        = "nzbget"
  port           = "6790"
  iscsi_portal   = "192.168.11.131:3260"
  iscsi_iqn      = "iqn.2000-01.com.synology:pelican.nzbget.7b01f1cb7fb"
  workspace_vars = module.servarr_vars
  depends_on     = [module.servarr_media_downloads]
}

module "muximux" {
  source         = "./modules/no-mounts"
  service        = "muximux"
  port           = "8383"
  iscsi_portal   = "192.168.11.131:3260"
  iscsi_iqn      = "iqn.2000-01.com.synology:pelican.muximux.7b01f1cb7fb"
  workspace_vars = module.servarr_vars
}

module "plexmetamanager" {
  source         = "./modules/no-mounts"
  service        = "plex-meta-manager"
  port           = "4321"
  iscsi_portal   = "192.168.11.131:3260"
  iscsi_iqn      = "iqn.2000-01.com.synology:pelican.plexmetamanager.7b01f1cb7fb"
  workspace_vars = module.servarr_vars
}

module "htpcmanager" {
  source         = "./modules/no-mounts"
  service        = "htpcmanager"
  port           = "8085"
  iscsi_portal   = "192.168.11.131:3260"
  iscsi_iqn      = "iqn.2000-01.com.synology:pelican.htpcmanager.7b01f1cb7fb"
  workspace_vars = module.servarr_vars
}

module "tautulli" {
  source         = "./modules/tautulli"
  service        = "tautulli"
  port           = "8181"
  iscsi_portal   = "192.168.11.131:3260"
  iscsi_iqn      = "iqn.2000-01.com.synology:pelican.tautulli.7b01f1cb7fb"
  workspace_vars = module.servarr_vars
}
