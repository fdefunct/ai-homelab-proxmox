#!/usr/bin/env python3
from pathlib import Path

from validate_kubernetes_common import expect, find_document, load_yaml_documents


def validate_application(path: Path, repo_root: Path, expected_repo_url: str, errors: list[str]):
    docs = load_yaml_documents(path)
    expect(len(docs) == 1, f"{path}: expected exactly one YAML document", errors)
    if not docs:
        return

    doc = docs[0]
    expect(doc.get("kind") == "Application", f"{path}: expected kind Application", errors)
    expect(doc.get("metadata", {}).get("namespace") == "argocd", f"{path}: Application must live in argocd namespace", errors)

    spec = doc.get("spec", {})
    sources = spec.get("sources")
    source = spec.get("source")
    if sources:
        expect(any(item.get("repoURL") == expected_repo_url and item.get("ref") == "values" for item in sources), f"{path}: multi-source app must include repo values source for this repo", errors)
        for item in sources:
            if "path" in item:
                expect((repo_root / item["path"]).exists(), f"{path}: referenced path does not exist: {item['path']}", errors)
    elif source:
        if "path" in source:
            expect(source.get("repoURL") == expected_repo_url, f"{path}: path-based app must use repoURL {expected_repo_url}", errors)
            expect((repo_root / source["path"]).exists(), f"{path}: referenced path does not exist: {source['path']}", errors)
    else:
        errors.append(f"{path}: Application must define spec.source or spec.sources")


def validate(repo_root: Path, config: dict, errors: list[str]):
    expected_repo_url = config["ansible"]["argocd_repo_url"]

    for path in sorted((repo_root / "kubernetes" / "apps").rglob("application.yaml")):
        validate_application(path, repo_root, expected_repo_url, errors)

    root_app = find_document(repo_root / "kubernetes" / "apps" / "root-app.yaml", "Application", "root-app")
    root_source = root_app.get("spec", {}).get("source", {})
    expect(root_source.get("repoURL") == expected_repo_url, "kubernetes/apps/root-app.yaml: repoURL must match ansible.argocd_repo_url", errors)

    forbidden_apps = {"kube-prometheus-stack", "loki", "rancher", "rancher-backup", "rancher-backup-crd", "rancher-backup-config", "monitoring-config"}
    present_apps = set()
    for path in sorted((repo_root / "kubernetes" / "apps" / "platform").rglob("application.yaml")):
        doc = load_yaml_documents(path)[0]
        present_apps.add(doc.get("metadata", {}).get("name"))
    overlap = sorted(forbidden_apps & present_apps)
    expect(not overlap, f"kubernetes/apps/platform contains forbidden apps for homelab-core: {overlap}", errors)
