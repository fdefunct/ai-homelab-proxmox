#!/usr/bin/env python3
from pathlib import Path
import json
import re

from validate_kubernetes_common import expect, github_preset, load_json, load_yaml_documents, parse_github_repository
import yaml


def validate(repo_root: Path, config: dict, errors: list[str]):
    renovate_config = load_json(repo_root / ".renovaterc.json5")
    renovate_custom_managers = load_json(repo_root / ".renovate" / "customManagers.json5")
    renovate_groups = load_json(repo_root / ".renovate" / "groups.json5")
    renovate_labels = load_json(repo_root / ".renovate" / "labels.json5")
    renovate_semantic = load_json(repo_root / ".renovate" / "semanticCommits.json5")
    expected_repository = parse_github_repository(config["ansible"]["argocd_repo_url"])

    renovate_values = yaml.safe_load((repo_root / "kubernetes" / "charts" / "renovate" / "values.yaml").read_text())
    renovate_admin_config = json.loads(renovate_values.get("renovate", {}).get("config", "{}"))
    expect(
        renovate_values.get("existingSecret") == "renovate-env",
        "kubernetes/charts/renovate/values.yaml: existingSecret must be renovate-env",
        errors,
    )
    expect(
        renovate_values.get("cronjob", {}).get("schedule") == "0 0 * * *",
        "kubernetes/charts/renovate/values.yaml: cronjob schedule must be 0 0 * * *",
        errors,
    )
    expect(
        renovate_values.get("cronjob", {}).get("timeZone") == "America/Chicago",
        "kubernetes/charts/renovate/values.yaml: cronjob timeZone must be America/Chicago",
        errors,
    )

    expect(
        renovate_config.get("$schema") == "https://docs.renovatebot.com/renovate-schema.json",
        ".renovaterc.json5: $schema must point to the Renovate schema",
        errors,
    )
    expect(
        renovate_config.get("timezone") == "America/Chicago",
        ".renovaterc.json5: timezone must be America/Chicago",
        errors,
    )
    expect(
        renovate_config.get("schedule") == ["after 12am and before 1am"],
        ".renovaterc.json5: schedule must keep runs in the 12am-1am daily window",
        errors,
    )
    expect(
        renovate_config.get("enabledManagers") == [
            "ansible-galaxy",
            "custom.regex",
            "github-actions",
            "helm-values",
            "kubernetes",
            "pip_requirements",
            "terraform",
        ],
        ".renovaterc.json5: enabledManagers must match the supported repo managers",
        errors,
    )
    expect(
        "helpers:pinGitHubActionDigests" in renovate_config.get("extends", []),
        ".renovaterc.json5: extends must pin GitHub Action digests",
        errors,
    )
    expect(
        expected_repository is not None,
        "config/home.yaml: ansible.argocd_repo_url must be a GitHub repo URL that scripts/validate-kubernetes can map to owner/repo",
        errors,
    )
    expect(
        renovate_admin_config.get("repositories") == [expected_repository] if expected_repository else False,
        "kubernetes/charts/renovate/values.yaml: self-hosted config must target the repository derived from ansible.argocd_repo_url",
        errors,
    )

    if expected_repository is not None:
        expected_presets = [
            github_preset(expected_repository, ".renovate/customManagers.json5"),
            github_preset(expected_repository, ".renovate/groups.json5"),
            github_preset(expected_repository, ".renovate/labels.json5"),
            github_preset(expected_repository, ".renovate/semanticCommits.json5"),
        ]
        for preset in expected_presets:
            expect(
                preset in renovate_config.get("extends", []),
                f".renovaterc.json5: extends must include {preset}",
                errors,
            )

    regex_manager = next(
        (
            manager
            for manager in renovate_custom_managers.get("customManagers", [])
            if manager.get("customType") == "regex"
            and any(pattern == "/^kubernetes\\/apps\\/platform\\/.+\\/application\\.yaml$/" for pattern in manager.get("managerFilePatterns", []))
        ),
        None,
    )
    expect(regex_manager is not None, ".renovate/customManagers.json5: missing custom regex manager for Argo CD Helm applications", errors)
    if regex_manager is not None:
        expect(regex_manager.get("datasourceTemplate") == "helm", ".renovate/customManagers.json5: custom regex manager datasourceTemplate must be helm", errors)
        expect(regex_manager.get("versioningTemplate") == "helm", ".renovate/customManagers.json5: custom regex manager versioningTemplate must be helm", errors)
        matchers = [re.compile(pattern.replace("(?<", "(?P<"), re.MULTILINE) for pattern in regex_manager.get("matchStrings", [])]
        expect(bool(matchers), ".renovate/customManagers.json5: custom regex manager must define at least one matchStrings pattern", errors)

        for path in sorted((repo_root / "kubernetes" / "apps" / "platform").rglob("application.yaml")):
            doc = load_yaml_documents(path)[0]
            sources = doc.get("spec", {}).get("sources", [])
            helm_sources = [
                item for item in sources
                if isinstance(item, dict) and item.get("repoURL", "").startswith("https://") and item.get("chart") and item.get("targetRevision")
            ]
            if not helm_sources:
                continue

            file_text = path.read_text()
            for source_item in helm_sources:
                matched = False
                for matcher in matchers:
                    for match in matcher.finditer(file_text):
                        groups = match.groupdict()
                        if (
                            groups.get("registryUrl") == source_item.get("repoURL")
                            and groups.get("depName") == source_item.get("chart")
                            and groups.get("currentValue") == str(source_item.get("targetRevision"))
                        ):
                            matched = True
                            break
                    if matched:
                        break
                expect(matched, f".renovate/customManagers.json5: custom regex manager must match the Helm source in {path}", errors)

    label_rules = renovate_labels.get("packageRules", [])
    expect(any(rule.get("labels") == ["type/major"] for rule in label_rules), ".renovate/labels.json5: must label major updates with type/major", errors)
    expect(any(rule.get("labels") == ["type/minor"] for rule in label_rules), ".renovate/labels.json5: must label minor updates with type/minor", errors)
    expect(any(rule.get("labels") == ["type/patch"] for rule in label_rules), ".renovate/labels.json5: must label patch updates with type/patch", errors)
    expect(any(rule.get("labels") == ["type/digest"] for rule in label_rules), ".renovate/labels.json5: must label digest updates with type/digest", errors)

    group_rules = renovate_groups.get("packageRules", [])
    expect(any(rule.get("groupName") == "kubernetes platform helm charts" for rule in group_rules), ".renovate/groups.json5: must group Argo CD Helm chart updates", errors)
    expect(any(rule.get("groupName") == "kubernetes images" for rule in group_rules), ".renovate/groups.json5: must group Kubernetes image updates", errors)

    semantic_rules = renovate_semantic.get("packageRules", [])
    expect(any(rule.get("semanticCommitScope") == "github-action" for rule in semantic_rules), ".renovate/semanticCommits.json5: must define semantic commit scope for GitHub Actions", errors)
