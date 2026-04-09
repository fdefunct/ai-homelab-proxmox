# Secrets

Purpose: secret ownership model and bootstrap exception reference.
Authority: reference.
Read when: a change touches credentials, vault references, or secret ownership
boundaries.

Use [`secret-catalog.yaml`](./secret-catalog.yaml) for tracked `op://...`
references and [`../config/home.yaml`](../config/home.yaml) for
environment-specific item names or selectors.

## Ownership Model

This repo tracks 1Password references as part of the declared system state.

- `terraform`: Proxmox API authentication plus guest template and VM lifecycle
  inputs
- `bootstrap`: first-run SSH access and other early bootstrap material such as
  the shared k3s cluster token
- `ansible`: host-level runtime credentials and operational credentials such as
  Rancher import
- `argocd-bootstrap`: bootstrap-only secrets required to bring up Argo CD and
  the in-cluster 1Password Connect path before GitOps reaches steady state
- `gitops`: Kubernetes secret references consumed through External Secrets and
  platform manifests

OpenClaw gateway VMs reuse the shared operator access material from the
`Homelab` vault. Bot-specific application secrets are intentionally out of scope
for this repo and should live in bot-specific vaults.

## Rules

- keep tracked `op://...` references in the smallest responsible layer
- prefer runtime injection over checked-in plaintext
- keep bootstrap exceptions narrow
- keep bootstrap SSH identity distinct from the steady-state operator identity
  when possible
- keep the installer `root` password as break-glass access, not the normal
  automation path
- keep Kubernetes runtime secrets in 1Password and project them through
  External Secrets where possible

## Bootstrap Exceptions

Steady-state cluster secrets should flow through External Secrets, not through
long-lived Ansible-managed Kubernetes secrets.

Bootstrap-only exceptions are intentionally narrow:

- the Argo CD admin password secret
- the Argo CD repository credential secret
- the 1Password Connect bootstrap token and credentials
- the Rancher import token used during cluster registration

In [`secret-catalog.yaml`](./secret-catalog.yaml), the Argo CD and 1Password
Connect bootstrap material uses the `argocd-bootstrap` owner. Runtime cluster
integrations that land in steady-state manifests remain `gitops`, and
operator/runtime credentials remain `ansible` or `bootstrap` as appropriate.

## Tracked Secret Entrypoints

- `ansible/secrets.yml`
- `ansible/bootstrap-ssh-private-key`
- `ansible/bootstrap-ssh-user`
- `ansible/operator-ssh-private-key`
- `ansible/argocd-repo-private-key`
- `terraform/envs/home/secrets.tfvars.template`
- [`secret-catalog.yaml`](./secret-catalog.yaml)

## Verbatim References Vs Metadata Selectors

Some Kubernetes runtime secret selectors are intentionally stored as item/key
metadata in `config/home.yaml` rather than as literal `op://...` references.
Those selectors still form part of the repo contract even when they do not
appear verbatim in the secret catalog.
