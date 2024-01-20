resource "kubernetes_config_map" "env" {
  metadata {
    name      = "${var.service}-env"
    namespace = var.workspace_vars.namespace
  }
  data = merge({
    # "BOOKSING_ADMINUSER"     = "",
    "BOOKSING_ALLOWALLUSERS" = "false",
    "BOOKSING_BINDADDRESS"   = "0.0.0.0:7132",
    "BOOKSING_BOOKDIR"       = "/books",
    "BOOKSING_DATABASEDIR"   = "/db",
    "BOOKSING_FAILDIR"       = "/failed/",
    "BOOKSING_IMPORTDIR"     = "/import/",
    "BOOKSING_LOGLEVEL"      = "debug",
    "BOOKSING_MAXSIZE"       = "0",
    "BOOKSING_TIMEZONE"      = "UTC",
    "BOOKSING_USERHEADER"    = "-",
    },
  var.extra_env_vars)
}
