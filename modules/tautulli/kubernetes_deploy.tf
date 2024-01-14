
resource "kubernetes_deployment" "deployment" {
  metadata {
    name      = var.service
    namespace = var.workspace_vars.namespace
    labels = {
      "servarr.app" = var.service
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        "servarr.app" = var.service
      }
    }

    template {
      metadata {
        labels = {
          "servarr.app" = var.service
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
          port {
            container_port = var.port
          }

          volume_mount {
            name       = "${var.service}-config"
            mount_path = "/config"
          }

          volume_mount {
            name       = "${var.service}-plex-logs"
            mount_path = "/logs"
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

        volume {
          name = "${var.service}-plex-logs"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.plexlogs.metadata.0.name
          }
        }
      }
    }
  }
}
