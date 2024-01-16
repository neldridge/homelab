# My K8s Homelab
I have been on a journey to replace my home infrastructure with a K8s cluster to force myself to learn more about K8s.

My previous stack was docker compose on 2 nodes, local disk storage with NFS on things that needed shared between. There were many reasons this process was painful, including updating services, keeping services running, and well, the servers were a SPOF.

# Requirements
* Hosts: microk8s (see status below)
* * cert-manager
* * helm
* * metallb
* * ingress
* * DISABLE hostpath-storage
* Hosts: open-iscsi
* Hosts: ipv6 disabled (may not be _required_)

# Terraform
Recommend using https://github.com/tfutils/tfenv

## ./modules
This stuff is a bit of a mess, I was learning as I went and trying to get things done without too much care in reusability. There's a fair bit of work that can be done to slim all of the services down into a single module which can be reused across all.

## State
Currently using local state which is not ideal, plan to setup config w/ S3 and Dynamo to ensure locking.

# Services

## Servarr
Arr stack w/ some extras for Plex & potential media acquisition.

## PiHole
My home DNS to avoid loading malicious pages, side effect is some ads are blocked. I'm considering adding a 2nd pihole with a separate iSCSI LUN to ensure redundancy.

## tplink-prometheus
I use this prometheus, currently, to scrape my tplink KP115 smart plugs for energy consumption which is then pushed to my grafana cloud. There's an assumption of a `prometheus.yml` in the `k8s-services/promtheus-prometheus` aka the `prometheus-config` volume mount, example below:
```
scrape_configs:
  - job_name: "kasa"
    static_configs:
      - targets:
          # IP of your smart plugs
          - 172.18.90.240
    metrics_path: /scrape
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        # IP of the exporter
        replacement: tplink-exporter:9233

remote_write:
  - url: https://prometheus-prod-13-prod-us-east-0.grafana.net/api/prom/push
    basic_auth:
      username: username
      password: password
```

I'll likely add unrelated scrape configs to prometheus for my [temperature-exporter](https://github.com/neldridge/temperature-exporter) app to get better visibility into cooling requirements of my cluster.

# K8s Configuration

## metallb
The metal load balancer will require you to give it a range of IPs to make available for lbs. The syntax is:
`microk8s enable metallb:192.168.11.80-192.168.11.99`. [Documentation](https://microk8s.io/docs/addon-metallb)

## cert-manager
cert-manager module assumes you're using Route53 and want LetsEncrypt for certs.

I've used a `ClusterIssuer` to avoid namespacing issues with certs across my cluster.

`cert-manager-rt53-credentials.json` contents:
```
{
  "accessKeyId": "key",
  "secretAccessKey": "secret"
}

```


## microk8s status (1/16/24)
```
# microk8s status
microk8s is running
high-availability: yes
  datastore master nodes: 192.168.11.57:19001 192.168.11.193:19001 192.168.11.243:19001
  datastore standby nodes: 192.168.11.23:19001 192.168.11.109:19001
addons:
  enabled:
    cert-manager         # (core) Cloud native certificate management
    dashboard            # (core) The Kubernetes dashboard
    dns                  # (core) CoreDNS
    ha-cluster           # (core) Configure high availability on the current node
    helm                 # (core) Helm - the package manager for Kubernetes
    helm3                # (core) Helm 3 - the package manager for Kubernetes
    ingress              # (core) Ingress controller for external access
    metallb              # (core) Loadbalancer for your Kubernetes cluster
    metrics-server       # (core) K8s Metrics Server for API access to service metrics
  disabled:
    community            # (core) The community addons repository
    host-access          # (core) Allow Pods connecting to Host services smoothly
    hostpath-storage     # (core) Storage class; allocates storage from host directory
    kube-ovn             # (core) An advanced network fabric for Kubernetes
    mayastor             # (core) OpenEBS MayaStor
    minio                # (core) MinIO object storage
    observability        # (core) A lightweight observability stack for logs, traces and metrics
    prometheus           # (core) Prometheus operator for monitoring and logging
    rbac                 # (core) Role-Based Access Control for authorisation
    registry             # (core) Private image registry exposed on localhost:32000
    storage              # (core) Alias to hostpath-storage add-on, deprecated
```
