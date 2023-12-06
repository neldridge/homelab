output "storage_class_name" {
  value = kubernetes_persistent_volume.persistent_volume.metadata[0].labels["share"]
}

output "volume_name" {
  value = kubernetes_persistent_volume.persistent_volume.metadata[0].name
}

output "volume_claim_name" {
  value = kubernetes_persistent_volume_claim.persistent_volume_claim.metadata[0].name
}
