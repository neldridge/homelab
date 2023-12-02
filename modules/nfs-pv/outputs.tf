output "pvc_name" {
  value = kubernetes_persistent_volume_claim.pihole_k8s_services.metadata[0].name
}

output "pv_name" {
  value = kubernetes_persistent_volume_claim.pihole_k8s_services.spec[0].volume_name
}
