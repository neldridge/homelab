data "kubernetes_namespace" "kube_system" {
  metadata {
    name = "kube-system"
  }
}
module "kube_system_vars" {
  source     = "./modules/workspace_vars"
  namespace  = data.kubernetes_namespace.kube_system.metadata[0].name
  domain     = "a3f.link"
  nfs_server = "192.168.11.131"
}

module "k8s_dashbaord_ingress" {
  source         = "./modules/ingress"
  workspace_vars = module.kube_system_vars
  service_scope  = "k8s-dashboard"
  domains = {
    "dashboard.a3f.link" : {
      port : "443",
      service : "kubernetes-dashboard",
    },
  }

  extra_annotations = {
    "nginx.ingress.kubernetes.io/backend-protocol" : "HTTPS",
    # "nginx.ingress.kubernetes.io/configuration-snippet" : "proxy_ssl_server_name: on;\nproxy_ssl_name: dashboard.a3f.link;\n",
  }

  depends_on = [
    data.kubernetes_namespace.kube_system,
    module.kube_system_vars
  ]
}
