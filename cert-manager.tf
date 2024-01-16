
data "kubernetes_namespace" "namespace" {
  metadata {
    name = "cert-manager"
  }
}

# @TODO: The solvers in this need to get moved to a dictionary and dynamic block
# Structure for the map is pretty basic: [map(domain, region, zoneid, accesskeyid, secretaccesskey)]

resource "kubernetes_manifest" "clusterissuer_letsencrypt_production" {
  manifest = {
    "apiVersion" = "cert-manager.io/v1"
    "kind"       = "ClusterIssuer"
    "metadata" = {
      "name" = "letsencrypt-production"
    }
    "spec" = {
      "acme" = {
        "email" = "nicholas.eldridge@gmail.com"
        "privateKeySecretRef" = {
          "name" = "letsencrypt-production-issuer-account-key"
        }
        "server" = "https://acme-v02.api.letsencrypt.org/directory"
        "solvers" = [
          {
            "dns01" = {
              "route53" = {
                "region"       = "us-east-1",
                "hostedZoneID" = "Z083123433QHFF5C6Q1AO",
                "accessKeyID"  = "${local.route53_credentials.accessKeyId}", # read this value in from cert-manage-rt53-credentials.josn
                # It looks like this is not introduced until cert-manager 1.12.3
                # microk8s cert-manager is 1.8.0
                # "accessKeyIDSecretRef" = {

                #   "name" = "a3f-link-route53-credentials-secret"
                #   "key"  = "access-key-id"
                # },
                "secretAccessKeySecretRef" = {

                  "name" = "a3f-link-route53-credentials-secret"
                  "key"  = "secret-access-key"
                },
              }
            },
            "selector" = {
              "dnsZones" = [
                "*.a3f.link",
                "a3f.link",
              ]
            }
          },
          {
            "dns01" = {
              "route53" = {
                "region"       = "us-east-1",
                "hostedZoneID" = "ZBECE55OG3JSE",
                "accessKeyID"  = "${local.route53_credentials.accessKeyId}", # read this value in from cert-manage-rt53-credentials.josn
                # It looks like this is not introduced until cert-manager 1.12.3
                # microk8s cert-manager is 1.8.0
                # "accessKeyIDSecretRef" = {

                #   "name" = "a3f-link-route53-credentials-secret"
                #   "key"  = "access-key-id"
                # },
                "secretAccessKeySecretRef" = {

                  "name" = "a3f-link-route53-credentials-secret"
                  "key"  = "secret-access-key"
                },
              }
            },
            "selector" = {
              "dnsZones" = [
                "*.neldridge.net",
                "neldridge.net",
              ]
            }
          },
        ]
      }
    }
  }
}

resource "kubernetes_secret" "route53_credentials" {
  metadata {
    name      = "a3f-link-route53-credentials-secret"
    namespace = data.kubernetes_namespace.namespace.metadata[0].name
  }

  data = {
    access-key-id     = local.route53_credentials.accessKeyId
    secret-access-key = local.route53_credentials.secretAccessKey
  }

  type = "Opaque"
}
locals {
  route53_credentials = jsondecode(file("${path.module}/cert-manager-rt53-credentials.json"))
}
