resource "kubernetes_config_map" "env" {
  metadata {
    name      = "${var.service}-env"
    namespace = var.workspace_vars.namespace
  }
  data = merge({
    "PUID" = var.workspace_vars.uid
    "PGID" = var.workspace_vars.gid
    "TZ"   = var.workspace_vars.timezone
    "port" = local.port_mapping[var.service]
    },
  var.extra_env_vars)
}
