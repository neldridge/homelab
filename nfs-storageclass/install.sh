# helm repo add csi-driver-nfs https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts
# helm repo update
# helm install csi-driver-nfs csi-driver-nfs/csi-driver-nfs \
#     --namespace kube-system \
#     --set kubeletDir=/var/snap/microk8s/common/var/lib/kubelet
kubectl apply -f - < sc-nfs-media-downloads.yml
kubectl apply -f - < sc-nfs-media-library.yml
