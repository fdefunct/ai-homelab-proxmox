# Contributor Quickstart

Purpose: local workstation setup and first-pass validation for contributors.
Authority: authoritative for local setup only.
Read when: preparing a workstation to work in this repo for the first time.

## Fast Path

Run these commands from the repo root:

1. `make bootstrap`
2. `make verify`
3. `make ENV=home generate-config`
4. `make check`

If all four pass, the workstation is ready for normal repo work.

Run `make check-all` before opening a high-risk PR or when the change touches
Terraform, Kubernetes schemas, CI/security validation, or the operator
workflow.

## Prerequisites

- Unix-like workstation with Bash and `make`
- network access for bootstrap downloads
- access to the repo's 1Password workflow for `ENV=home` generation and deeper
  checks

Use [`secrets.md`](./secrets.md) and [`secret-catalog.yaml`](./secret-catalog.yaml)
only when you need the full secrets contract.

## Expected Results

- `make bootstrap`: installs or updates repo-local tooling and hooks
- `make verify`: validates local tools, auth, and required files
- `make ENV=home generate-config`: renders the derived Terraform and Ansible
  inputs without errors
- `make check`: passes the standard local validation surface, including the
  repo-local unittest suite

## After Setup

- For AI/operator policy and validation selection, use [`AI_RULES.md`](./AI_RULES.md).
- For live `home` bootstrap or Day 2 validation, use
  [`bootstrap-home.md`](./bootstrap-home.md).
- For durable design rationale, use [`architecture.md`](./architecture.md).
