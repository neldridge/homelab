terraform {
  backend "kubernetes" {
    namespace     = "default"
    secret_suffix = "state"
    config_path   = "~/.kube/config"
  }
}
