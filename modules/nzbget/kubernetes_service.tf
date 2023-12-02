resource "kubernetes_service" "arr" {
  metadata {
    name      = var.service
    namespace = var.workspace_vars.namespace
  }
  spec {
    type = "ClusterIP"
    selector = {
      "servarr.app" = var.service
    }
    port {
      port = var.port
    }
  }
  depends_on = [
    kubernetes_deployment.deployment
  ]
}

resource "kubernetes_service" "svc_lb" {
  metadata {
    name      = "${var.service}-lb"
    namespace = var.workspace_vars.namespace
  }
  spec {
    type = "LoadBalancer"
    selector = {
      "servarr.app" = var.service
    }
    port {
      port = var.port
    }
  }
  depends_on = [
    kubernetes_deployment.deployment
  ]
}
