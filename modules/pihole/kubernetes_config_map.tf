resource "kubernetes_config_map" "env" {
  metadata {
    name      = "${var.service}-env"
    namespace = var.workspace_vars.namespace
  }
  data = {
    "TZ"           = var.workspace_vars.timezone
    "VIRTUAL_HOST" = var.workspace_vars.domain
    # "WEBPASSWORD"  = random_password.webpassword.result
    # "PIHOLE_UID"   = var.workspace_vars.uid
    # "PIHOLE_GID"   = var.workspace_vars.gid
    "WEB_UID" = var.workspace_vars.uid
    "WEB_GID" = var.workspace_vars.gid
  }
}
