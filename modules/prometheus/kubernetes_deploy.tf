
resource "kubernetes_deployment" "deployment" {
  metadata {
    name      = var.service
    namespace = var.workspace_vars.namespace
    labels = {
      "service" = var.service
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        "service" = var.service
      }
    }

    template {
      metadata {
        labels = {
          "service" = var.service
        }
      }

      spec {
        container {
          image = local.container_image
          name  = var.service
          env_from {
            config_map_ref {
              name = kubernetes_config_map.env.metadata.0.name
            }
          }

          dynamic "port" {
            for_each = local.http_ports
            content {
              name           = port.value["name"]
              container_port = port.value["port"]
              protocol       = port.value["protocol"]
            }

          }

          volume_mount {
            name       = "${var.service}-config"
            mount_path = "/etc/prometheus"
            sub_path   = "${var.service}-prometheus/"
          }
        }

        volume {
          name = "${var.service}-config"
          persistent_volume_claim {
            claim_name = var.workspace_vars.k8s_services_name
          }
        }
      }
    }
  }
}
