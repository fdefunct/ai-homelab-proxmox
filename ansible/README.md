# Ansible

This directory owns host bootstrap for `pve-0` and k3s bootstrap for `homelab-core`.

Responsibilities:

- baseline package setup and host hardening
- Linux admin user creation after first connecting with the Day 0 bootstrap SSH identity
- Proxmox repository and firewall baseline
- NVMe-backed ZFS storage preparation
- Tailscale installation and enrollment
- host-level observability such as node exporter, ZFS scrub scheduling, and recurring health checks
- guest baseline preparation for Ubuntu cluster nodes
- guest baseline preparation for OpenClaw gateway Ubuntu VMs, including bot user
  setup, Homebrew installation, 1Password CLI installation, and optional
  Caddy-based HTTPS ingress
- k3s server and agent installation from `/etc/rancher/k3s/config.yaml`
- Argo CD bootstrap
- 1Password Connect bootstrap exceptions
- kubeconfig artifact generation and server node tainting after workers join

Non-responsibilities:

- VM or LXC lifecycle
- Kubernetes steady-state desired state after Argo CD takes over
- Rancher server installation
- full in-cluster observability stack ownership

Operator entrypoints:

- `make ansible-known-hosts`
- `make ansible`
- `make ansible-secrets`
- `ENV_NAME=home ./scripts/run-ansible ansible/inventories/home/generated.yml ansible/playbooks/site.yml --check`

Generated inventory values come from `config/<env>.yaml` rather than being hand-edited.
The Ansible wrapper reads the bootstrap SSH identity from the tracked 1Password references under `ansible/bootstrap-ssh-*` and the cluster guest operator key from `ansible/operator-ssh-private-key`.
Before live Ansible runs, rebuild the repo-local `.ansible/known_hosts` file
with `make ENV=<env> ansible-known-hosts`. Standard Ansible runs now require
host key verification through that file instead of disabling SSH trust checks.
For OpenClaw gateways, Ansible prepares the shared Ubuntu baseline, the
bot-specific admin account, Homebrew and 1Password CLI under that account,
optional gateway-local Caddy HTTPS ingress, and optional Tailscale enrollment;
it does not install OpenClaw itself.
For `home`, the full site `--check` path is supported. Use
[`../docs/bootstrap-home.md`](../docs/bootstrap-home.md) for the current
ordered validation contract and expected `home` outcomes.
On a freshly reinstalled Proxmox host, the practical Day 0 bridge is:

- log in once as `root` with the installer password
- install the tracked bootstrap public key
- create the tracked bootstrap user if it does not already exist
- run `make ENV=home generate-config`
- run `make ENV=home ansible-known-hosts`
- switch back to the normal `make ansible` flow for repeatable reruns

The current boundary keeps Proxmox datacenter and node firewalling disabled on
purpose. Exposure control currently relies on upstream network design,
Tailscale, and Kubernetes or ingress-layer policy rather than Proxmox firewall
rules.
