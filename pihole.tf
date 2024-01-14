module "pihole_vars" {
  source            = "./modules/workspace_vars"
  namespace         = "pihole"
  timezone          = "America/New_York"
  nfs_server        = "192.168.11.131"
  k8s_services_name = "pihole-k8s-services"
  k8s_services_path = "/volume2/k8s-services/"
  k8s_services_size = "10Gi"
  domain            = "a3f.link"
  uid               = 1024
  gid               = 100
}

resource "kubernetes_namespace" "pihole" {
  metadata {
    name = module.pihole_vars.namespace
  }
}

module "pihole" {
  source          = "./modules/pihole"
  service         = "pihole"
  container_image = "pihole/pihole:latest"
  iscsi_portal    = "192.168.11.131:3260"
  iscsi_iqn       = "iqn.2000-01.com.synology:pelican.pihole.7b01f1cb7fb"
  workspace_vars  = module.pihole_vars
  depends_on      = [kubernetes_namespace.pihole]
}
