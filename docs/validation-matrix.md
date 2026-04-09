# Validation Matrix

Purpose: detailed validator runtime, cadence, and severity reference.
Authority: reference.
Read when: you need more detail than the change-type mapping in
[`AI_RULES.md`](./AI_RULES.md).

| Check target                | Typical runtime                   | Requires network/auth?                                                                          | Run cadence                                                    | Failure severity                                             |
| --------------------------- | --------------------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------ |
| `format-check`              | ~10-60s                           | No                                                                                              | Every commit (before push)                                     | **Blocker** (must pass before PR)                            |
| `yaml-format-check`         | ~5-30s                            | No                                                                                              | Every commit (when YAML changes)                               | **Blocker** for YAML-touching PRs                            |
| `tf-fmt-check`              | ~2-10s                            | No                                                                                              | Every commit (when Terraform changes)                          | **Blocker** for Terraform-touching PRs                       |
| `env-validate`              | ~2-15s                            | No                                                                                              | Every commit (when `config/` changes), every PR                | **Blocker** for environment config changes                   |
| `test`                      | ~2-20s                            | No                                                                                              | Every PR when repo scripts, generators, or validators change   | **High** (blocker for automation workflow changes)           |
| `tf-validate`               | ~10-45s                           | Provider plugins may require network on first run; no cloud auth required with `-backend=false` | Every PR (and every commit when Terraform changes)             | **Blocker** for Terraform changes                            |
| `tf-lint`                   | ~10-60s                           | May require network on first run (plugin/module download)                                       | Every PR (Terraform changes), release                          | **High** (treat as blocker unless triaged)                   |
| `ansible-syntax`            | ~10-40s                           | No (for syntax phase)                                                                           | Every PR (Ansible changes)                                     | **Blocker** for Ansible changes                              |
| `ansible-lint`              | ~10-60s                           | No (assuming local deps installed)                                                              | Every PR (Ansible changes), release                            | **High** (policy/blocker by default)                         |
| `yaml-lint`                 | ~5-30s                            | No                                                                                              | Every commit for YAML-heavy changes; every PR                  | **Medium-High** (often blocker in CI)                        |
| `shell-lint`                | ~2-20s                            | No                                                                                              | Every PR when scripts change                                   | **Medium** (escalate to blocker for production script paths) |
| `github-actions-lint`       | ~2-20s                            | No                                                                                              | Every PR when `.github/workflows` changes                      | **Blocker** for workflow changes                             |
| `kubernetes-validate`       | ~5-30s                            | No                                                                                              | Every PR when `kubernetes/` or app wiring changes              | **Blocker** for Kubernetes changes                           |
| `kubeconform-validate`      | ~20-180s                          | **Yes** (downloads schema/CRD definitions)                                                      | PRs touching manifests/charts/apps; release                    | **High** (block release if failing)                          |
| `checkov-validate`          | ~30-240s                          | No auth required; may fetch metadata/rules depending on installation                            | Every PR for IaC changes; release                              | **High/Critical** (security findings gate merges per policy) |
| `gitleaks-validate`         | ~5-60s                            | No                                                                                              | Every commit (pre-push), every PR, incident response           | **Critical** (immediate stop and rotate exposed material)    |
| `gitleaks-history-validate` | ~30-300s                          | No                                                                                              | Weekly schedule, manual triage, release readiness              | **Critical** (catches historical secret exposure)            |
| `secret-catalog-validate`   | ~5-30s                            | No auth required for static catalog checks                                                      | Every PR touching secret refs/catalog; release                 | **High** (blocker for secrets governance paths)              |
| `validate`                  | ~1-5s                             | No                                                                                              | Every commit/PR (fast sanity)                                  | **Blocker** (repo structure invariant)                       |
| `check`                     | ~2-10 min (depends on tool cache) | Mixed (mostly no network after bootstrap)                                                       | Every PR                                                       | **Blocker** (primary CI-quality gate)                        |
| `check-all`                 | ~4-20 min                         | Mixed; includes networked schema validation                                                     | Release candidates, scheduled full validation, incident triage | **Blocker/Critical** (full confidence gate)                  |

## Suggested Operating Policy

- Every commit: `format-check`, plus targeted checks for changed areas.
- Every PR: `make check`; use `make check-all` when schemas, security posture,
  or operator workflow changes materially.
- Repo-managed Python requirements and Ansible collection pins should be
  updated through Renovate PRs rather than ad hoc version edits.
- Release or cutover windows: require a green `make check-all` close to the
  release point.
- Incident response: include `gitleaks-validate` and the relevant stack checks
  to reduce regression risk during hotfixes.
- Run `make gitleaks-history-validate` manually during secret incidents or use
  the scheduled workflow for continuous coverage of git history.
