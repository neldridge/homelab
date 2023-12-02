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
  workspace_vars  = module.pihole_vars
  container_image = "pihole/pihole:latest"
  depends_on      = [kubernetes_namespace.pihole, kubernetes_persistent_volume_claim.pihole_k8s_services]
}
