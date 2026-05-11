
----------------------------------------
sudo apt-get update; sudo apt-get install -y rsync
wget https://github.com/azlux/log2ram/archive/refs/tags/1.6.1.tar.gz
tar xvzf 1.6.1.tar.gz
cd log2ram-1.6.1/
>> edit log2ram.conf to increase size of logs (128MB)
chmod +x install.sh
sudo ./install.sh
sudo reboot
sudo systemctl status log2ram
sudo df -h
----------------------------------------
wget https://get.helm.sh/helm-v3.13.1-linux-arm64.tar.gz
tar xvzf helm-v3.13.1-linux-arm64.tar.gz
cd linux-arm64
chmod 0700 helm
sudo mv helm /usr/local/bin
sudo chown root:root /usr/local/bin/helm
----------------------------------------
apt-get install -y snapd kubernetes-client
<ctrl+d> sudo su -
snap install microk8s --classic
microk8s status --wait-ready
microk8s enable dashboard

>>> one node only
microk8s dashboard-proxy
>>> any node to log in
kubectl describe secret -n kube-system microk8s-dashboard-token

---------------------------------------- synology csi
apt-get install -y open-iscsi (all nodes- required)

>>> one node only
apt-get install -y git 
git clone https://github.com/SynologyOpenSource/synology-csi.git
cd synology-csi/
>> edit deploy/helm/values.yaml
>> edit deploy/helm/templates/test.yaml
>> change storage class to the "delete" storage class from values.yml

make up
make test
