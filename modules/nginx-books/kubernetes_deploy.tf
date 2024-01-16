
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
          image = "${var.container_image}:${var.container_tag}"
          name  = var.service
          env_from {
            config_map_ref {
              name = kubernetes_config_map.env.metadata.0.name
            }
          }
          port {
            container_port = 80
          }

          volume_mount {
            name       = "${var.service}-config"
            mount_path = "/etc/nginx/conf.d/"
          }

          volume_mount {
            name       = "${var.service}-media-library"
            mount_path = "/books"
            sub_path   = "Books/"
          }

        }

        volume {
          name = "${var.service}-config"
          config_map {
            name = kubernetes_config_map.config.metadata.0.name
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
