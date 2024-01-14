
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
          image = "lscr.io/linuxserver/${var.service}:${var.container_tag}"
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
            mount_path = "/config"
          }

          volume_mount {
            name       = "${var.service}-media-library"
            mount_path = "/tv"
            sub_path   = "TV Shows/"
          }

          volume_mount {
            name       = "${var.service}-media-library"
            mount_path = "/movies"
            sub_path   = "Movies/"
          }

          volume_mount {
            name       = "${var.service}-media-library"
            mount_path = "/books"
            sub_path   = "Books/"
          }

          volume_mount {
            name       = "${var.service}-media-downloads"
            mount_path = "/downloads"
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

        volume {
          name = "${var.service}-media-downloads"
          persistent_volume_claim {
            claim_name = var.workspace_vars.media_downloads_name
          }
        }
      }
    }
  }
}
