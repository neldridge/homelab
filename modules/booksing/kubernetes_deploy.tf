
resource "kubernetes_deployment" "deployment" {
  metadata {
    name      = var.service
    namespace = var.workspace_vars.namespace
    labels = {
      "app" = var.service
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        "app" = var.service
      }
    }

    template {
      metadata {
        labels = {
          "app" = var.service
        }
      }

      spec {
        container {
          image = "${var.container_image}:${var.container_tag}"
          name  = var.service
          env_from {
            config_map_ref {
              name = kubernetes_config_map.env.metadata.0.name
            }
          }
          port {
            container_port = local.port_mapping[var.service]
          }

          volume_mount {
            name       = "${var.service}-config"
            mount_path = "/db"
          }

          volume_mount {
            name       = "${var.service}-media-library"
            mount_path = "/books"
            sub_path   = "Books/"
          }

          volume_mount {
            name       = "${var.service}-media-library"
            mount_path = "/import"
            sub_path   = "Books/"
          }

          volume_mount {
            name       = "${var.service}-media-library"
            mount_path = "/failed"
            sub_path   = "Booksing-Failed/"
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
          name = "${var.service}-media-library"
          persistent_volume_claim {
            claim_name = var.workspace_vars.media_library_name
          }
        }
      }
    }
  }
}
