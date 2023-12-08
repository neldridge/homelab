resource "kubernetes_config_map" "env" {
  metadata {
    name      = "${var.service}-env"
    namespace = var.workspace_vars.namespace
  }
  data = {
    "TZ" = var.workspace_vars.timezone
  }
}
