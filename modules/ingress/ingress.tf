resource "kubernetes_ingress_v1" "ingress" {
  metadata {
    name      = "${var.workspace_vars.namespace}-${var.service_scope}-ingress"
    namespace = var.workspace_vars.namespace
    annotations = merge(var.extra_annotations, {
      "cert-manager.io/cluster-issuer" : "letsencrypt-production"
      "kubernetes.io/tls-acme" : "true"

    })
  }

  spec {
    ingress_class_name = "public"
    dynamic "rule" {
      for_each = var.domains
      content {
        host = rule.key
        http {
          path {
            backend {
              service {
                name = rule.value["service"]
                port {
                  number = rule.value["port"]
                }
              }
            }
            path      = "/"
            path_type = "Prefix"
          }
        }
      }
    }

    tls {
      secret_name = "${var.workspace_vars.namespace}-${var.service_scope}-ingress-tls"
      hosts       = local.ingress_domains
    }
  }
}
