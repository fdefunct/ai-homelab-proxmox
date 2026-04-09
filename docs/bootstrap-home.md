# Bootstrap `home`

Purpose: ordered live runbook for bootstrapping and validating the `home`
environment on `pve-0` and `homelab-core`.
Authority: authoritative for `home` live procedure.
Read when: installing, re-bootstrapping, or validating the live `home`
environment.

This public starter uses sanitized example values. Replace `example.com`,
`192.0.2.0/24`, disk selectors, MAC addresses, and 1Password item names before
running any live command against your own hardware.

## 1. Day 0 Manual Install

Perform the base install manually from the official Proxmox VE 9.1 ISO.

Recommended installer choices:

- install Proxmox onto the 1 TB SSD
- leave the NVMe workload disk unused during install so automation can claim it
- set hostname to `pve-0`
- configure the first management IP and bridge to match
  [`../config/home.yaml`](../config/home.yaml)
- enable VT-x and VT-d in BIOS before or immediately after install
- avoid hand-configuring managed storage, users, or observability after this
  point
- keep the management uplink aligned with committed config

## 2. Preflight Inputs

Before any live bootstrap or validation run:

- review [`../config/home.yaml`](../config/home.yaml) for hostnames, storage,
  networking, cluster topology, backup settings, and integrations
- confirm required 1Password items exist in the vault named by
  `platform.onepassword_vault`
- use [`secret-catalog.yaml`](./secret-catalog.yaml) and
  [`secrets.md`](./secrets.md) as the secret contract

Minimum live prerequisites include:

- Day 0 bootstrap SSH access
- steady-state `homelab-ops` SSH access
- `homelab-core` operator SSH access
- Proxmox Terraform API token
- Tailscale auth key
- Argo CD repo deploy key and admin password
- k3s cluster token
- 1Password Connect bootstrap credentials
- Cloudflare DNS token
- Renovate GitHub PAT
- Velero S3 credentials
- Rancher API token
- PBS credentials for the `pve-0` to `pbs-0` backup target

For a freshly reinstalled host, perform the one-time bridge before normal
automation:

- SSH to the Day 0 host as `root` using the installer password
- install the tracked bootstrap public key
- create the tracked bootstrap user if it does not already exist
- run `make ENV=home generate-config`
- run `make ENV=home ansible-known-hosts`

## 3. Canonical Command Sequence

Run this sequence in order for `home`.

### Phase A: local repo gate

1. `make bootstrap`
2. `make verify`
3. `make ENV=home generate-config`
4. `make check`
5. `make check-all`

### Phase B: detect-only infrastructure checks

1. `make ENV=home tf-plan-check`
2. `ENV_NAME=home ./scripts/run-ansible ansible/inventories/home/generated.yml ansible/playbooks/site.yml --check`

Expected result:

- Terraform detect-only plan returns exit code `0`
- full Ansible `--check` succeeds with `changed=0`

Before the Ansible check or any live Ansible run, refresh the repo-local SSH
trust file:

1. `make ENV=home ansible-known-hosts`

### Phase C: live convergence and platform checks

1. `make ENV=home ansible`
2. `make ENV=home ansible`
3. `make ENV=home check-platform`
4. `KUBECONFIG=ansible/artifacts/kubeconfig/homelab-core-server-0.yaml kubectl get nodes`

Expected result:

- both live Ansible runs succeed with `changed=0`
- `make ENV=home check-platform` passes after GitOps convergence
- `kubectl get nodes` reports the server and both workers as `Ready`

Conditional commands:

- `BOOTSTRAP_PROXMOX_INSECURE=1 make ENV=home tf-plan` only while the Proxmox
  host is still on the Day 0 self-signed certificate
- `make ENV=home tf-apply` only after reviewing an intentional Terraform diff
- `make rancher-import` when first registering or re-registering the cluster
- `make trust-proxmox-ca` once the host is serving the steady-state Proxmox CA

## 4. Runtime Outcomes To Confirm

After the canonical sequence passes, confirm the live system still matches the
current repo contract:

- the NVMe-backed ZFS pool and Proxmox datastore from
  [`../config/home.yaml`](../config/home.yaml) exist
- Tailscale is healthy on the intended nodes
- Linux operator and admin users exist with the expected SSH keys
- host observability services and timers are active
- `/etc/network/interfaces` matches the tracked management uplink
- the PBS storage and scheduled backup job exist
- the Proxmox pool and Ubuntu cloud template exist
- the `homelab-core` VMs exist and boot at the configured identities
- the Home Assistant VM exists with its configured VM ID, bridge, datastore,
  MAC identity, and management IP identity
- the OpenClaw gateway VMs exist, boot via DHCP, and receive the configured
  reserved MAC and IP identities
- gateway bot users have the expected SSH keys, passwordless sudo, Homebrew,
  and working `op` CLI access
- gateways with `caddy.enabled: true` serve valid certificates and proxy to
  their configured local upstreams
- Argo CD reports the root app and committed platform apps as healthy
- Longhorn is healthy and exposed privately at the configured endpoint
- platform ingress hostnames resolve privately and serve valid certificates
- MetalLB assigns service IPs from the configured range
- Velero backup storage is available

Homepage requires dedicated read-only API credentials for Proxmox and PBS.
`make rancher-import` assumes the Rancher endpoint is reachable from cluster
pods over the intended external network path.
Proxmox datacenter and node firewalling remain intentionally disabled in this
pass; current exposure control relies on upstream network design, Tailscale,
and Kubernetes or ingress-layer policy instead.

## Appendix: External Ops Boundary

Neither the Proxmox host nor `homelab-core` owns the external monitoring stack.
Treat the committed `ops.watchtower` and `platform.telemetry` values as the
integration contract for:

- Gatus checks for configured infrastructure and platform endpoints
- Prometheus remote write from the cluster to the external ops stack
- Loki push from the cluster to the external ops stack
- Rancher import into the existing external Rancher instance

## Appendix: Rare Host Network Triage

For `pve-0` link and uplink triage, use:

- `journalctl -k -b | grep -A30 -B30 -E 'e1000e|r8152|nic0|vmbr0'`
- `/usr/local/sbin/capture-management-nic-diagnostics`
- `ip -br link show`
- `bridge link show master vmbr0`
