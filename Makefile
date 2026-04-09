SHELL := /bin/sh
ENV ?= home
TF_ENV_DIR := terraform/envs/$(ENV)
ANSIBLE_INVENTORY := ansible/inventories/$(ENV)/generated.yml
ANSIBLE_PLAYBOOK := ansible/playbooks/site.yml
ENV_CONFIG := config/$(ENV).yaml
VENV_BIN := .venv/bin
ANSIBLE_PLAYBOOK_BIN := $(VENV_BIN)/ansible-playbook
YAMLLINT_BIN := $(VENV_BIN)/yamllint
YAMLFMT_BIN := $(VENV_BIN)/yamlfmt
ARGOCD_APP ?= root-app
K8S_NAMESPACE ?= default
K8S_SECRET ?=
K8S_POD ?=
K8S_CONTAINER ?=

.PHONY: help bootstrap verify generate-config render-gatus-config generated-file-edits-check terraform-runtime-artifacts-check fmt format yaml-format format-check yaml-format-check tf-fmt-check tf-validate tf-lint ansible-syntax ansible-lint yaml-lint shell-lint github-actions-lint kubernetes-validate kubeconform-validate checkov-validate gitleaks-validate gitleaks-history-validate secret-catalog-validate env-validate test tf-init tf-plan tf-plan-check tf-apply tf-destroy inventory ansible-known-hosts ansible ansible-secrets rancher-import trust-proxmox-ca argocd-refresh argocd-hard-refresh kubectl-view-secret kubectl-pod-shell check-platform validate check check-all

help:
	@printf "%s\n" \
		"Targets:" \
		"  make ENV=<env> ... Run a target against a specific environment (default: home)" \
		"  make bootstrap Install/check Terraform, create a repo-local venv, provision validation tools, and seed generated config" \
		"  make verify    Verify local tools, repo-local validation binaries, 1Password auth, and required local files" \
		"  make generate-config Generate Terraform and Ansible inputs from config/\$$ENV.yaml" \
		"  make generated-file-edits-check Fail if generated artifacts are edited without source config changes" \
		"  make terraform-runtime-artifacts-check Fail if Terraform state or provider cache artifacts are tracked in git" \
		"  make render-gatus-config Render the expected Gatus endpoints from config/\$$ENV.yaml" \
		"  make fmt       Format Terraform if available" \
		"  make format    Format tracked Markdown and JSON with Prettier, then YAML with yamlfmt" \
		"  make yaml-format Format tracked YAML with yamlfmt" \
		"  make format-check Check tracked Markdown and JSON with Prettier, then YAML with yamlfmt" \
		"  make yaml-format-check Check tracked YAML formatting with yamlfmt" \
		"  make tf-fmt-check Run terraform fmt in check mode" \
		"  make tf-validate Validate the Terraform configuration for \$$ENV" \
		"  make tf-lint   Run tflint against terraform/envs/\$$ENV" \
		"  make ansible-syntax Run ansible-playbook syntax-check with repo config" \
		"  make ansible-lint Run ansible-lint against the playbook" \
		"  make yaml-lint Lint repository YAML files" \
		"  make shell-lint Run shellcheck on repo shell scripts" \
		"  make github-actions-lint Validate GitHub Actions workflows with actionlint" \
		"  make kubernetes-validate Validate Argo app wiring and Kubernetes YAML structure" \
		"  make kubeconform-validate Validate Kubernetes manifests against API schemas and CRD schemas" \
		"  make checkov-validate Run Checkov IaC security analysis against Terraform and Kubernetes" \
		"  make gitleaks-validate Run a tracked working-tree secret scan with gitleaks" \
		"  make gitleaks-history-validate Run a full git history secret scan with gitleaks" \
		"  make secret-catalog-validate Validate tracked 1Password references and ownership metadata" \
		"  make env-validate Validate config/\$$ENV.yaml and required inventory invariants" \
		"  make test      Run the repo-local unittest suite for custom automation" \
		"  make tf-init   Initialize Terraform in terraform/envs/\$$ENV" \
		"  make tf-plan   Run terraform plan with 1Password-injected secrets" \
		"  make tf-plan-check Run a detect-only Terraform plan and fail when drift or an error is present" \
		"  make tf-apply  Run terraform apply with 1Password-injected secrets" \
		"  make tf-destroy Run terraform destroy with 1Password-injected secrets" \
		"  make inventory Generate derived config artifacts from config/\$$ENV.yaml" \
		"  make ansible-known-hosts Rebuild the repo-local SSH known_hosts file for Ansible targets" \
		"  make ansible-secrets Render 1Password-backed Ansible secrets to stdout" \
		"  make ansible   Run the Ansible site playbook against generated inventory" \
		"  make rancher-import Import the cluster into an external Rancher instance" \
		"  make trust-proxmox-ca Fetch and trust the Proxmox root CA on the local workstation" \
		"  make ARGOCD_APP=<name> argocd-refresh Request an Argo CD app refresh (default: root-app)" \
		"  make ARGOCD_APP=<name> argocd-hard-refresh Request a hard Argo CD app refresh (default: root-app)" \
		"  make K8S_NAMESPACE=<ns> K8S_SECRET=<name> kubectl-view-secret Decode and print a Kubernetes secret" \
		"  make K8S_NAMESPACE=<ns> K8S_POD=<name> [K8S_CONTAINER=<name>] kubectl-pod-shell Open /bin/sh in a pod" \
		"  make check-platform Run live platform convergence checks against the cluster" \
		"  make validate  Validate scaffold conventions" \
		"  make check     Run all lightweight checks" \
		"  make check-all Run the full local validation surface, including kubeconform, checkov, and gitleaks" \
		"  docs/validation-matrix.md Validation runtimes, cadence, and failure severity guidance"

bootstrap:
	@ENV_NAME=$(ENV) ./scripts/bootstrap

verify:
	@ENV_NAME=$(ENV) ./scripts/verify

generate-config: $(ENV_CONFIG)
	@$(VENV_BIN)/python ./scripts/generate-config $(ENV)

render-gatus-config: $(ENV_CONFIG)
	@$(VENV_BIN)/python ./scripts/render-gatus-config $(ENV)

generated-file-edits-check:
	@./scripts/check-generated-file-edits --staged

terraform-runtime-artifacts-check:
	@python3 ./scripts/check-terraform-runtime-artifacts

fmt:
	@if command -v terraform >/dev/null 2>&1; then \
		terraform -chdir=terraform fmt -recursive; \
	else \
		echo "terraform not installed; skipping fmt"; \
	fi

format:
	@npm exec -- prettier --write .
	@$(MAKE) yaml-format

yaml-format:
	@$(YAMLFMT_BIN) -conf .yamlfmt.yaml ".github/**/*.yml" ".github/**/*.yaml" "config/**/*.yaml" "kubernetes/**/*.yaml"

format-check:
	@npm exec -- prettier --check .
	@$(MAKE) yaml-format-check

yaml-format-check:
	@$(YAMLFMT_BIN) -conf .yamlfmt.yaml -lint ".github/**/*.yml" ".github/**/*.yaml" "config/**/*.yaml" "kubernetes/**/*.yaml"

tf-fmt-check:
	@terraform -chdir=terraform fmt -check -recursive

tf-validate:
	@terraform -chdir=$(TF_ENV_DIR) init -backend=false >/dev/null
	@terraform -chdir=$(TF_ENV_DIR) validate

tf-lint:
	@terraform -chdir=$(TF_ENV_DIR) init -backend=false >/dev/null
	@tflint --chdir=$(TF_ENV_DIR) --format compact

ansible-syntax:
	@$(MAKE) generate-config
	@ANSIBLE_CONFIG=ansible/ansible.cfg ANSIBLE_HOME=.ansible ANSIBLE_LOCAL_TEMP=.ansible/tmp $(ANSIBLE_PLAYBOOK_BIN) -i $(ANSIBLE_INVENTORY) $(ANSIBLE_PLAYBOOK) --syntax-check

ansible-lint:
	@cd ansible && ../$(VENV_BIN)/ansible-lint playbooks/site.yml

yaml-lint:
	@$(YAMLLINT_BIN) -c .yamllint .

shell-lint:
	@grep -Erl '^#!/bin/(sh|bash)' scripts/ | sort | xargs shellcheck

github-actions-lint:
	@actionlint

kubernetes-validate:
	@ENV_NAME=$(ENV) $(VENV_BIN)/python ./scripts/validate-kubernetes

kubeconform-validate:
	@PATH="$(VENV_BIN):$$PATH" kubeconform \
		--schema-location default \
		--schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
		--ignore-missing-schemas \
		--strict \
		--summary \
		kubernetes/manifests kubernetes/apps

checkov-validate:
	@$(VENV_BIN)/checkov -d terraform/envs/$(ENV) --quiet --compact
	@$(VENV_BIN)/checkov -d kubernetes --quiet --compact

gitleaks-validate:
	@GITLEAKS_BIN="$${GITLEAKS_BIN:-$(VENV_BIN)/gitleaks}" ./scripts/gitleaks-validate

gitleaks-history-validate:
	@GITLEAKS_BIN="$${GITLEAKS_BIN:-$(VENV_BIN)/gitleaks}" ./scripts/gitleaks-history-validate

secret-catalog-validate:
	@ENV_NAME=$(ENV) $(VENV_BIN)/python ./scripts/validate-secret-catalog

env-validate:
	@$(VENV_BIN)/python ./scripts/validate-environment $(ENV)

test:
	@$(VENV_BIN)/python -m unittest discover -s tests

tf-init:
	@$(MAKE) generate-config
	@terraform -chdir=$(TF_ENV_DIR) init

tf-plan:
	@$(MAKE) generate-config
	@ENV_NAME=$(ENV) ./scripts/run-terraform plan

tf-plan-check:
	@$(MAKE) generate-config
	@set +e; \
	ENV_NAME=$(ENV) ./scripts/run-terraform plan -detailed-exitcode; \
	rc=$$?; \
	if [ "$$rc" -eq 0 ]; then \
		printf '%s\n' "Terraform detect-only plan is empty."; \
		exit 0; \
	fi; \
	if [ "$$rc" -eq 2 ]; then \
		printf '%s\n' "Terraform detect-only plan found drift. Review the diff before apply."; \
		exit 2; \
	fi; \
	printf 'Terraform detect-only plan failed with exit code %s.\n' "$$rc"; \
	exit "$$rc"

tf-apply:
	@$(MAKE) generate-config
	@ENV_NAME=$(ENV) ./scripts/run-terraform apply

tf-destroy:
	@$(MAKE) generate-config
	@ENV_NAME=$(ENV) ./scripts/run-terraform destroy

inventory:
	@$(MAKE) generate-config

ansible-known-hosts: $(ENV_CONFIG)
	@$(MAKE) generate-config
	@$(VENV_BIN)/python ./scripts/build-ansible-known-hosts $(ENV)

ansible-secrets:
	@./scripts/render-ansible-secrets

ansible:
	@$(MAKE) generate-config
	@ENV_NAME=$(ENV) ./scripts/run-ansible $(ANSIBLE_INVENTORY) $(ANSIBLE_PLAYBOOK)

rancher-import:
	@ENV_NAME=$(ENV) ./scripts/import-rancher-cluster

trust-proxmox-ca:
	@ENV_NAME=$(ENV) ./scripts/trust-proxmox-ca

argocd-refresh:
	@kubectl -n argocd annotate application/$(ARGOCD_APP) argocd.argoproj.io/refresh=normal --overwrite

argocd-hard-refresh:
	@kubectl -n argocd annotate application/$(ARGOCD_APP) argocd.argoproj.io/refresh=hard --overwrite

kubectl-view-secret:
	@test -n "$(K8S_SECRET)" || { printf '%s\n' "Set K8S_SECRET=<name>."; exit 1; }
	@kubectl -n "$(K8S_NAMESPACE)" get secret "$(K8S_SECRET)" -o json | $(VENV_BIN)/python -c 'import base64, json, sys; secret = json.load(sys.stdin); data = secret.get("data", {}); [print(f"{k}:\\n{base64.b64decode(v).decode(errors=\"replace\")}\\n") for k, v in sorted(data.items())]'

kubectl-pod-shell:
	@test -n "$(K8S_POD)" || { printf '%s\n' "Set K8S_POD=<name>."; exit 1; }
	@if [ -n "$(K8S_CONTAINER)" ]; then \
		kubectl -n "$(K8S_NAMESPACE)" exec -it "$(K8S_POD)" -c "$(K8S_CONTAINER)" -- /bin/sh; \
	else \
		kubectl -n "$(K8S_NAMESPACE)" exec -it "$(K8S_POD)" -- /bin/sh; \
	fi

check-platform:
	@ENV_NAME=$(ENV) ./scripts/check-platform

validate:
	@$(MAKE) terraform-runtime-artifacts-check
	@test -d terraform
	@test -d terraform/envs/$(ENV)
	@test -d ansible
	@test -d kubernetes/apps
	@test -d kubernetes/charts
	@test -d kubernetes/manifests
	@test -d config
	@test -d docs

check: validate
	@$(MAKE) format-check
	@$(MAKE) env-validate
	@$(MAKE) test
	@$(MAKE) tf-fmt-check
	@$(MAKE) tf-validate
	@$(MAKE) tf-lint
	@$(MAKE) ansible-syntax
	@$(MAKE) ansible-lint
	@$(MAKE) yaml-lint
	@$(MAKE) shell-lint
	@$(MAKE) github-actions-lint
	@$(MAKE) kubernetes-validate
	@$(MAKE) secret-catalog-validate

check-all: check
	@$(MAKE) kubeconform-validate
	@$(MAKE) checkov-validate
	@$(MAKE) gitleaks-validate
