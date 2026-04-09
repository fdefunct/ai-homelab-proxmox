# Terraform

This directory owns the Proxmox Terraform boundary.

Current scope:

- provider wiring for the `home` environment
- generated Proxmox foundation defaults from `config/home.yaml`
- a reusable Ubuntu 24.04 cloud image template
- the `homelab` Proxmox pool
- `homelab-core` VM lifecycle on `nvme-fast`
- OpenClaw gateway VM lifecycle on `nvme-fast`
- the Home Assistant VM as config-driven guest topology on the same datastore and bridge
- DNS domain and server configuration for cloud-init guests, sourced from `config/home.yaml`
- a secure-by-default TLS stance with an explicit bootstrap-only insecure override path

Terraform stays intentionally simple here:

- one environment root per site under `terraform/envs/<env>`
- generated non-secret inputs from `config/<env>.yaml`
- runtime secrets injected only at command execution time
- local Terraform state for the current single-operator workflow

Today the initial host bootstrap still begins with the Proxmox ISO install and first Ansible convergence. Terraform becomes the primary owner of Proxmox API objects once the node already exists and the API token is available.
If the node is still on its Day 0 self-signed certificate, operators may temporarily use `BOOTSTRAP_PROXMOX_INSECURE=1` with the Terraform entrypoints as an explicit runtime-only bootstrap exception.
Once the steady-state Proxmox certificate is in place, the intended local follow-on
is `make trust-proxmox-ca` so Terraform can stay on the secure-by-default path.
For `home`, Terraform now owns the guest substrate for `homelab-core`, the Home
Assistant appliance, and the OpenClaw gateways, including cloned Ubuntu guests
and DHCP-based gateway VMs with pinned MAC identities.
For `home`, use `make ENV=home tf-plan-check` as the detect-only idempotence
gate. It runs `terraform plan -detailed-exitcode` through the repo wrapper and
prints whether the result is steady state, drift, or an execution failure.
Treat exit code `0` as the expected steady-state result before apply. A drifted
plan should be reviewed before any apply. Use
`make ENV=home tf-apply` only when the remaining diff is intentional and
reviewed. Use [`../docs/bootstrap-home.md`](../docs/bootstrap-home.md) for the
broader `home` operator sequence.

## Local State And Runtime Artifacts

This repo currently uses local Terraform state for `home`. That is intentional
to keep the operator model simple while there is a single environment root and
no need for shared remote-state coordination.

Local runtime artifacts may exist on a workstation but must stay untracked:

- `terraform/envs/<env>/.terraform/`
- `terraform/envs/<env>/terraform.tfstate`
- `terraform/envs/<env>/terraform.tfstate.*`

The provider lock file is the exception and should stay tracked:

- `terraform/envs/<env>/.terraform.lock.hcl`

Use `make terraform-runtime-artifacts-check` to confirm runtime artifacts are
not tracked in git. Before any intentional apply, back up the current local
state file if it exists and review the detect-only plan first.

Operator entrypoints:

- `make tf-plan`
- `make tf-plan-check`
- `make tf-apply`
- `make tf-destroy`
