resource "kubernetes_service" "arr" {
  metadata {
    name      = var.service
    namespace = var.workspace_vars.namespace
  }
  spec {
    type = "ClusterIP"
    selector = {
      "service" = var.service
    }
    dynamic "port" {
      for_each = concat(local.dns_ports, local.http_ports)
      content {
        name     = port.value["name"]
        port     = port.value["port"]
        protocol = port.value["protocol"]
      }
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
      "service" = var.service
    }
    dynamic "port" {
      for_each = local.dns_ports
      content {
        name     = port.value["name"]
        port     = port.value["port"]
        protocol = port.value["protocol"]
      }
    }
  }
  depends_on = [
    kubernetes_deployment.deployment
  ]
}

resource "kubernetes_service" "svc_lb_http" {
  metadata {
    name      = "${var.service}-lb-http"
    namespace = var.workspace_vars.namespace
  }
  spec {
    type = "LoadBalancer"
    selector = {
      "service" = var.service
    }
    dynamic "port" {
      for_each = local.http_ports
      content {
        name     = port.value["name"]
        port     = port.value["port"]
        protocol = port.value["protocol"]
      }
    }
  }
  depends_on = [
    kubernetes_deployment.deployment
  ]
}
