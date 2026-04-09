# AI Rules

Purpose: canonical policy for AI agents and automation-oriented contributors.
Authority: authoritative.
Read when: planning or making any repo change.

## Authority Order

Resolve ambiguity in this order:

1. `config/<env>.yaml` for exact environment values
2. `make help` for supported command names and operator entrypoints
3. this document for repo policy and validation selection
4. [`bootstrap-home.md`](./bootstrap-home.md) for the ordered `home` live
   procedure
5. subsystem references such as [`secrets.md`](./secrets.md)
6. [`architecture.md`](./architecture.md) for rationale only

## Core Rules

- Prefer changing the owning source of truth over making ad hoc runtime fixes.
- Keep ownership boundaries intact:
  - Terraform owns Proxmox infrastructure creation.
  - Ansible owns host bootstrap and narrow bootstrap exceptions.
  - Argo CD owns committed Kubernetes desired state under `kubernetes/`.
  - `config/<env>.yaml` is the canonical non-secret environment topology.
- Do not store plaintext secrets in tracked files.
- Keep tracked `op://...` references aligned with
  [`secret-catalog.yaml`](./secret-catalog.yaml).
- Avoid embedding environment-specific trivia in durable docs unless it belongs
  in a runbook.

## Derived Outputs

Generated artifacts are derived outputs, not primary inputs.

- Edit `config/<env>.yaml`.
- Run `make ENV=<env> generate-config` when config or topology changes.
- Never hand-edit generated outputs.

The main generated artifacts are:

- `ansible/inventories/<env>/generated.yml`
- `terraform/envs/<env>/generated.auto.tfvars.json`

## Operating Flow

1. Start at [`../README.md`](../README.md) to choose the right next document.
2. Identify which layer owns the change.
3. Make the smallest change in that owning layer.
4. Regenerate derived outputs only when config or topology changes.
5. Run targeted validators for the changed area.
6. Run `make check` before declaring repo changes ready.
7. Use [`bootstrap-home.md`](./bootstrap-home.md) for any ordered live
   `home` validation or convergence sequence.

## Validation Selection

Treat validators as gates. Choose them by change type:

- Local environment or toolchain setup:
  - `make verify`

- `config/` or topology metadata:
  - `make ENV=<env> generate-config`
  - `make ENV=<env> env-validate`
  - `make ENV=<env> kubernetes-validate` when environment-facing Kubernetes
    wiring changes

- Terraform changes:
  - `make tf-fmt-check`
  - `make tf-validate`
  - `make tf-lint`
  - `make checkov-validate` when the change affects IaC security posture
  - `make terraform-runtime-artifacts-check` when changing Terraform workflow,
    ignore rules, or repo guardrails
  - `make ENV=<env> tf-plan-check` before any intentional live apply

- Ansible changes:
  - `make ansible-syntax`
  - `make ansible-lint`

- Repo scripts, generators, or validators:
  - `make test`
  - `make shell-lint` when shell entrypoints change

- Kubernetes and GitOps changes:
  - `make ENV=<env> kubernetes-validate`
  - `make kubeconform-validate`
  - `make checkov-validate` when manifests or security posture change
  - `make ENV=<env> check-platform` only after live convergence

- Secret references or ownership metadata:
  - `make secret-catalog-validate`

- Markdown, YAML, JSON, or workflow changes:
  - `make format-check`
  - `make github-actions-lint` when `.github/workflows/` changes

- Broad or high-risk changes:
  - `make check`
  - `make check-all` when Terraform, Kubernetes schemas, CI/security
    validation, or the operator workflow itself changes materially

Use [`validation-matrix.md`](./validation-matrix.md) only when you need the
detailed runtime, cadence, or severity table.

## Secrets

Use [`secrets.md`](./secrets.md) for the secret ownership model and bootstrap
exceptions. When adding or changing a secret reference, put it in the smallest
responsible ownership layer and update
[`secret-catalog.yaml`](./secret-catalog.yaml) when a tracked `op://...`
reference or owner changes.

## Repo-Specific Conventions

- Prefer Tailscale hostnames or MagicDNS names as stable host identifiers.
- Do not treat `100.x` Tailscale addresses as durable across rebuilds.
- Treat Homepage at `https://core.example.com/` as an internal operator endpoint.
- Treat `rancher.example.com` as a cluster-consumed control-plane endpoint that
  must remain reachable from `homelab-core` nodes.
- Treat Beta as the sole merge decision-maker for Renovate PRs.
- Treat exact pins in `requirements/bootstrap.txt` and
  `ansible/requirements.yml` as reproducibility controls; Renovate remains the
  automated update path for those files.
