# Longhorn On `homelab-core`

Purpose: Longhorn-specific storage reference for `homelab-core`.
Authority: appendix.
Read when: changing Longhorn behavior, validating storage, or reviewing the
storage migration history.

## Repo Contract

This repo treats Longhorn as the default Kubernetes storage layer for
`homelab-core`.

- Argo CD installs Longhorn into `longhorn-system`
- Longhorn is the default `StorageClass`
- the Longhorn UI is exposed privately at `https://longhorn.core.example.com/`
- Homepage exposes Longhorn through both the Platform tile and the
  Longhorn-specific info widget
- PVC-backed platform apps declare `longhorn` where this repo owns the workload
  manifest or chart values

## Current Constraints

The current topology is still a single physical Proxmox host, so Longhorn is
configured conservatively:

- default replica count is `2`
- the default Longhorn storage class also uses replica count `2`
- Longhorn backups and recurring snapshot jobs are intentionally out of scope
  for this first rollout
- `multipathd` must stay disabled on all `homelab-core` nodes because Longhorn
  warns that it can claim Longhorn-backed block devices and trigger attach,
  mount, or I/O failures

## Current State

The following PVC-backed workloads have been cut over to Longhorn:

- `gatus`
- `redis`
- `n8n`
- `netbox`
- `postgresql`

The old k3s packaged `local-path` addon is retired. Longhorn is the only
supported steady-state PVC storage system on `homelab-core`.

## Validation

- `make kubernetes-validate`
- `make check`
- `make check-platform`
- `curl -fsSIL https://longhorn.core.example.com/`
- `kubectl get storageclass`
- `kubectl -n longhorn-system get pods`

Use a disposable PVC with no `storageClassName` to confirm the cluster default
binds to `longhorn`.
