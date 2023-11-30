
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
          image = "lscr.io/linuxserver/${var.service}:latest"
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
            sub_path   = "${var.service}-config"
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
            name       = "${var.service}-media-downloads"
            mount_path = "/downloads"
          }

          # Not sure why this existed in my previous setup, leaving here in case I need it later
          # volume_mount {
          #   name = "${var.service}-media-downloads"
          #   mount_path = "/data"
          #   sub_path = ""
          # }

        }

        volume {
          name = "${var.service}-config"
          persistent_volume_claim {
            claim_name = var.workspace_vars.k8s_services_name
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
