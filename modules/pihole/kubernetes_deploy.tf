
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
            for_each = concat(local.dns_ports, local.http_ports)
            content {
              name           = port.value["name"]
              container_port = port.value["port"]
              protocol       = port.value["protocol"]
            }

          }

          volume_mount {
            name       = "${var.service}-config"
            mount_path = "/etc/pihole"
            sub_path   = "pihole"
          }

          volume_mount {
            name       = "${var.service}-config"
            mount_path = "/etc/dnsmasq.d"
            sub_path   = "dnsmasq.d"
          }

          volume_mount {
            name       = "${var.service}-config"
            mount_path = "/var/log"
            sub_path   = "log"
          }

        }

        volume {
          name = "${var.service}-config"
          iscsi {
            target_portal = var.iscsi_portal
            iqn           = var.iscsi_iqn
            lun           = var.iscsi_lun
            fs_type       = var.iscsi_fs_type
            read_only     = var.iscsi_read_only
          }
        }
      }
    }
  }
}
