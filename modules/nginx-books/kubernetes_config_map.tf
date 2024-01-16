resource "kubernetes_config_map" "env" {
  metadata {
    name      = "${var.service}-env"
    namespace = var.workspace_vars.namespace
  }
  data = merge({
    "PUID" = var.workspace_vars.uid
    "PGID" = var.workspace_vars.gid
    "TZ"   = var.workspace_vars.timezone
    },
  var.extra_env_vars)
}
resource "kubernetes_config_map" "config" {
  metadata {
    name      = "${var.service}-config"
    namespace = var.workspace_vars.namespace
  }
  data = {
    "books.conf" = file("${path.module}/books.conf")
  }

}

