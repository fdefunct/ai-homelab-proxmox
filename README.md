# ai-homelab-proxmox

Public starter repo for a Proxmox-based homelab. It is meant to provide a
useful starting point for a setup that combines:

- Proxmox and k3s infrastructure managed from tracked config
- gateway hosts for AI-agent workloads alongside normal homelab services
- a repo structure that is practical to adapt with agentic coding tools

The repo uses:

- Terraform for Proxmox guest lifecycle and foundation resources
- Ansible for host bootstrap, guest preparation, and k3s bootstrap
- Argo CD and committed manifests for Kubernetes steady-state GitOps

The checked-in `home` environment is intentionally sanitized. Hostnames use
`example.com`, management networking uses `192.0.2.0/24`, and all tracked
1Password references are placeholder contracts rather than live secrets.

The operating model assumes the system can be deployed, operated, and
maintained by AI agents that run both on the homelab itself and from external
operator environments. The example gateway VMs are tuned for OpenClaw-style
agent workflows, but they are just Ubuntu-based agent hosts and can be adapted
for any similar autonomous or semi-autonomous agent stack. Because OpenClaw is
still evolving quickly, the current example keeps the OpenClaw application
install as a manual operator step rather than freezing a workflow that may
change upstream.

Treat this repo as a working template, not a drop-in deployment.

## Purpose

This repo manages the `home` environment across three ownership layers:

- Terraform owns Proxmox API objects, templates, pools, and guest lifecycle.
- Ansible owns host bootstrap, guest preparation, k3s bootstrap, and narrow
  bootstrap exceptions.
- GitOps owns committed Kubernetes desired state for `homelab-core` under
  `kubernetes/`.

The Proxmox ISO install and first management IP assignment are the deliberate
Day 0 exception. Everything after that should converge from tracked config,
automation, and 1Password-backed secrets.

## First Adaptation Steps

1. Update [`config/home.yaml`](./config/home.yaml) with your real hostnames,
   subnets, disk selectors, MACs, and repo URL.
2. Review [`docs/secret-catalog.yaml`](./docs/secret-catalog.yaml) and create
   matching 1Password items in your own vault.
3. Run `make bootstrap`, then `make ENV=home generate-config`.
4. Run `make check` and fix every validation issue before any live apply.
5. Use [`docs/bootstrap-home.md`](./docs/bootstrap-home.md) only after the
   example values have been fully adapted to your environment.

## Primary Docs

Use only one of these as your next hop:

- [`docs/AI_RULES.md`](./docs/AI_RULES.md): authoritative AI/operator policy,
  source-of-truth rules, and validation selection
- [`docs/bootstrap-home.md`](./docs/bootstrap-home.md): authoritative live
  runbook for bootstrapping and validating `home`
- [`docs/contributor-quickstart.md`](./docs/contributor-quickstart.md):
  authoritative local workstation setup for contributors
- [`docs/architecture.md`](./docs/architecture.md): durable design rationale
- [`docs/secrets.md`](./docs/secrets.md): secret ownership and bootstrap
  exceptions

Supporting references stay under [`docs/README.md`](./docs/README.md).

## Authority Order

When docs and repo state disagree, resolve them in this order:

1. `config/<env>.yaml` for exact environment values
2. `make help` for supported entrypoints and command names
3. [`docs/AI_RULES.md`](./docs/AI_RULES.md) for operator policy and validation
   selection
4. [`docs/bootstrap-home.md`](./docs/bootstrap-home.md) for the ordered `home`
   live procedure
5. subsystem references such as [`docs/secrets.md`](./docs/secrets.md)
6. [`docs/architecture.md`](./docs/architecture.md) for rationale only

## Operator Surface

- Use `make help` to see the supported command surface.
- Use `make ENV=<env> ...` to target a different environment.
- Renovate policy lives in `.renovate/*.json5` and is composed by
  `.renovaterc.json5`.
- Exact pins in repo-managed Python requirements and Ansible collections are
  intentional; Renovate updates them through grouped PRs and daily AI review
  remains the merge gate.
- Kubernetes-specific PR validation lives in
  `.github/workflows/kubernetes-pr.yml`.

## Repo Layout

- `config/`: canonical non-secret environment topology
- `terraform/`: Proxmox infrastructure boundary
- `ansible/`: host bootstrap, guest prep, and k3s bootstrap
- `kubernetes/`: GitOps-managed platform apps, manifests, and chart values
- `.github/`: CI, repo automation, and PR labeling
- `.renovate/`: grouped dependency policy
- `docs/`: runbooks, reference material, and appendices
