module "tplink_prom_vars" {
  source            = "./modules/workspace_vars"
  namespace         = "tplink-prometheus"
  timezone          = "America/New_York"
  nfs_server        = "192.168.11.131"
  k8s_services_name = "tpl-prom-k8s-services"
  k8s_services_path = "/volume2/k8s-services/"
  k8s_services_size = "10Gi"
  domain            = "a3f.link"
}

resource "kubernetes_namespace" "tplink_prom" {
  metadata {
    name = module.tplink_prom_vars.namespace
  }
}

module "tplink_exporter" {
  source          = "./modules/tplink-plug-exporter"
  service         = "tplink-exporter"
  container_image = "neldridge/tplink-plug-exporter:latest"
  workspace_vars  = module.tplink_prom_vars
  depends_on      = [kubernetes_namespace.pihole, module.tplink_prom_share]
}

module "tplink_prom" {
  source          = "./modules/prometheus"
  service         = "prometheus"
  container_image = "prom/prometheus:latest"
  workspace_vars  = module.tplink_prom_vars
  depends_on      = [kubernetes_namespace.pihole, module.tplink_prom_share]
}

module "tplink_prom_share" {
  source     = "./modules/nfs-pv"
  namespace  = module.tplink_prom_vars.namespace
  nfs_server = module.tplink_prom_vars.nfs_server
  share_name = module.tplink_prom_vars.k8s_services_name
  nfs_path   = module.tplink_prom_vars.k8s_services_path
  capacity   = module.tplink_prom_vars.k8s_services_size
  depends_on = [module.tplink_prom_vars]
}
