# Kubernetes

This directory owns the GitOps layer for the `homelab-core` k3s cluster hosted on `pve-0`.

Current scope:

- Argo CD root app and platform applications
- chart values for third-party platform components
- raw manifests for cluster configuration and bootstrap exceptions
- platform services such as cert-manager, External Secrets, MetalLB, Traefik, Homepage, Velero, Renovate, and telemetry agents
- Kubernetes-targeted CI validation through `.github/workflows/kubernetes-pr.yml`
  and the repo-wide `make kubernetes-validate` / `make kubeconform-validate`
  entrypoints

Notes:

- Argo CD `Application` manifests under `kubernetes/apps/` remain the GitOps
  entrypoint for steady-state platform sync
- high-value CRDs and workflows now carry YAML schema comments to improve IDE
  validation without changing rendered cluster state

Intentional non-scope:

- no local Grafana, Loki, Prometheus stack, or Rancher server
- no direct management of Rancher-created `cattle-system` resources after import
