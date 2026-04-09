#!/usr/bin/env python3
from pathlib import Path
import json
import re

import json5
import yaml


def load_yaml_documents(path: Path):
    docs = [doc for doc in yaml.safe_load_all(path.read_text()) if doc is not None]
    if not docs:
        raise ValueError(f"{path}: file contains no YAML documents")
    return docs


def expect(condition: bool, message: str, errors: list[str]):
    if not condition:
        errors.append(message)


def split_onepassword_selector(value: str) -> tuple[str, str]:
    item, field = value.rsplit("/", 1)
    return item, field


def find_document(path: Path, kind: str, name: str):
    for doc in load_yaml_documents(path):
        if isinstance(doc, dict) and doc.get("kind") == kind and doc.get("metadata", {}).get("name") == name:
            return doc
    raise ValueError(f"{path}: missing {kind} named {name}")


def load_json(path: Path):
    try:
        text = path.read_text()
        if path.suffix == ".json5":
            return json5.loads(text)
        return json.loads(text)
    except FileNotFoundError as exc:
        raise ValueError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: JSON parse error: {exc}") from exc


def load_environment_config(repo_root: Path, env_name: str):
    path = repo_root / "config" / f"{env_name}.yaml"
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level YAML object")
    return data


def parse_github_repository(repo_url: str) -> str | None:
    match = re.match(r"^git@github\.com:(?P<repo>[^/]+/[^/]+?)(?:\.git)?$", repo_url)
    if match:
        return match.group("repo")

    match = re.match(r"^https://github\.com/(?P<repo>[^/]+/[^/]+?)(?:\.git)?/?$", repo_url)
    if match:
        return match.group("repo")

    return None


def github_preset(repo: str, path: str) -> str:
    return f"github>{repo}//{path}"
