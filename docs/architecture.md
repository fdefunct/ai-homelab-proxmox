# Architecture

Purpose: durable design rationale and ownership boundaries for this repo.
Authority: reference.
Read when: you need to understand why the system is shaped this way, not how to
run it.

## Intent

`ai-homelab-proxmox` is the physical foundation for AI Homelab.

The repo uses a config-driven infrastructure pattern with:

- environment-driven config
- thin operator entrypoints
- explicit ownership boundaries
- generated Terraform and Ansible inputs instead of hardcoded duplication

## Ownership Boundaries

Steady-state responsibility is:

- Terraform for Proxmox API objects, guest pools, templates, and VM lifecycle
- Ansible for host bootstrap, guest preparation, k3s installation, and narrow
  bootstrap exceptions
- GitOps for downstream workload and platform desired state inside
  `homelab-core`, including cluster-local automation such as Renovate

There is one deliberate front-of-chain exception: the Proxmox ISO install and
first management IP assignment. The API cannot be managed until the node
already exists.

## Foundation Design

The design is intentionally optimized for a small physical footprint with clear
growth paths:

- one Proxmox node is acceptable as the first physical failure domain
- guest workload storage lives on a dedicated NVMe-backed ZFS datastore
- operator access and control-plane reachability use Tailscale as the stable
  overlay
- external monitoring and Rancher stay outside the cluster rather than being
  recreated inside `homelab-core`
- Kubernetes desired state is reconciled by GitOps after the bootstrap boundary

Environment details such as hostnames, IPs, disk IDs, and vault selectors are
config, not architecture.

OpenClaw gateways intentionally stay on the Terraform plus Ansible side of the
boundary: Terraform clones and sizes the VM, Ansible applies the Ubuntu
baseline and bot-user setup, and the OpenClaw application install remains a
manual operator step so the repo does not freeze a fast-moving upstream
process.

## Why ZFS On The Guest Disk

For a single-node Proxmox host, a dedicated guest-disk target cleanly separates
host lifecycle from workload storage. ZFS on that device provides checksumming,
compression, scrub scheduling, and a better snapshot substrate than `lvmthin`.

The intended split is:

- installer-created root-disk storage covers the host baseline
- a separate ZFS-backed datastore carries VM and container disks
- faster guest I/O lands on the workload device without coupling it to the
  Proxmox root install

## Why k3s Looks Different Here

This repo's k3s design reflects a single physical Proxmox host rather than
multiple real failure domains.

- topology should match real failure domains and not pretend to provide HA
- current `home` uses one embedded-etcd server and two workers
- the server is tainted after bootstrap so steady-state workloads land on
  workers
- packaged `traefik`, `servicelb`, and `local-storage` stay disabled so
  ingress, load-balancing, and storage remain explicitly owned
- Longhorn is the intended steady-state storage layer
- Longhorn replica policy stays conservative until a second real failure domain
  exists
- etcd snapshots and workload backups are expected to leave the cluster

## Monitoring And Backup Boundaries

`homelab-core` does not own a full in-cluster observability stack or its own
Rancher server.

- host metrics remain local to the host and are exposed for external scraping
- cluster metrics and logs are shipped to an external ops stack
- the cluster is imported into an existing external Rancher instance
- Rancher-owned `cattle-system` resources are an intentional management
  exception after import
- Proxmox owns the client side of guest backups, while PBS owns destination
  identity, datastore policy, and retention

## Bootstrap Identity Model

Ansible uses a Day 0 bootstrap SSH identity for the first convergence, then
creates and maintains the steady-state operator account.

That split keeps bootstrap access narrow and disposable while preserving a
repeatable automation path for normal operations.
