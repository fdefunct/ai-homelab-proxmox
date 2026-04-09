# Adapting This Repo

Purpose: environment adaptation reference for cloning this repo pattern to a
new site or environment.
Authority: appendix.
Read when: creating a new environment or reusing this repo structure elsewhere.

## Adaptation Workflow

1. create a new environment file under `config/`
2. run commands with `make ENV=<your-env> ...`
3. update `config/<env>.yaml` first:
   - hostnames
   - management subnet, gateway, and DNS
   - bridge names or uplink interfaces
   - management NIC tuning if needed
   - Proxmox API endpoint
   - storage IDs, ZFS pool names, and disk selectors
   - 1Password vault and item names
   - external monitoring target names and endpoints
   - Git repo identity under `ansible.argocd_repo_url`
4. update committed identity references that are not generated from config:
   - Argo CD `repoURL` references under `kubernetes/apps/`
   - the self-hosted Renovate target repository in
     `kubernetes/charts/renovate/values.yaml`
   - repo-identity preset references in `.renovaterc.json5`
   - user-facing repo links and bookmarks under
     `kubernetes/manifests/homepage/`
5. create `terraform/envs/<env>/secrets.tfvars.template`
6. run `make ENV=<env> generate-config`
7. run the validators selected by [`AI_RULES.md`](./AI_RULES.md), including the
   environment, Kubernetes, Terraform, Ansible, and secret-catalog gates

## Invariants To Preserve

- keep `config/<env>.yaml` as the canonical non-secret environment source of
  truth
- treat generated Terraform vars and Ansible inventory as derived outputs
- preserve the Day 0 bootstrap versus steady-state operator identity split
  unless the new environment has a stronger automated bootstrap path
- keep ownership boundaries intact until there is a concrete reason to change
- keep `.renovate/*.json5` as the canonical Renovate policy fragments
- keep `.renovaterc.json5` as the active Renovate entrypoint that composes
  those fragments
