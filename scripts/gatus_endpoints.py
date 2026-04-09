#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

import yaml


DEFAULT_INTERVAL = "60s"
DEFAULT_HTTP_CONDITIONS = [
    "[STATUS] == 200",
    "[RESPONSE_TIME] < 3000",
]
DEFAULT_TCP_CONDITIONS = [
    "[CONNECTED] == true",
]
STATIC_MONITORING_ENDPOINTS = (
    {
        "name": "Grafana",
        "group": "monitoring",
        "url": "https://grafana.ops.example.com/api/health",
    },
    {
        "name": "Prometheus",
        "group": "monitoring",
        "url": "https://prometheus.ops.example.com/-/healthy",
    },
    {
        "name": "Loki",
        "group": "monitoring",
        "url": "https://loki.ops.example.com/loki/api/v1/status/buildinfo",
    },
)
STATIC_EXTERNAL_ENDPOINTS = (
    {
        "name": "Cloudflare",
        "group": "external",
        "url": "https://cloudflare.com/cdn-cgi/trace",
    },
    {
        "name": "Google",
        "group": "external",
        "url": "https://www.google.com",
    },
    {
        "name": "GitHub",
        "group": "external",
        "url": "https://github.com",
    },
)


def load_environment_config(repo_root: Path, env_name: str):
    path = repo_root / "config" / f"{env_name}.yaml"
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level YAML object")
    return data


def format_endpoint_url(template: str, config: dict) -> str:
    context = {}
    context.update(config.get("platform", {}))
    context.update(config.get("ops", {}).get("watchtower", {}))
    return template.format(**context)


def build_endpoint(name: str, group: str, url: str, *, insecure: bool = False):
    endpoint = {
        "name": name,
        "group": group,
        "url": url,
        "interval": DEFAULT_INTERVAL,
    }

    if url.startswith("tcp://"):
        endpoint["conditions"] = list(DEFAULT_TCP_CONDITIONS)
        return endpoint

    endpoint["conditions"] = list(DEFAULT_HTTP_CONDITIONS)
    if insecure:
        endpoint["client"] = {"insecure": True}
    return endpoint


def build_gatus_endpoints(config: dict):
    monitoring = config["platform"]["monitoring"]["gatus"]
    watchtower = config["ops"]["watchtower"]
    cluster_nodes = config["cluster"]["nodes"]
    gateways = config.get("gateways", {}).get("instances", {})

    endpoints = []

    for spec in monitoring["operator_apps"]:
        endpoints.append(
            build_endpoint(
                spec["name"],
                "operator apps",
                format_endpoint_url(spec["url"], config),
                insecure=spec.get("insecure", False),
            )
        )

    for spec in monitoring["platform_dependencies"]:
        endpoints.append(
            build_endpoint(
                spec["name"],
                "platform dependencies",
                format_endpoint_url(spec["url"], config),
                insecure=spec.get("insecure", False),
            )
        )

    for spec in STATIC_MONITORING_ENDPOINTS:
        endpoints.append(build_endpoint(spec["name"], spec["group"], spec["url"]))

    for spec in watchtower["gatus_endpoints"]:
        endpoints.append(
            build_endpoint(
                spec["name"],
                "infrastructure",
                format_endpoint_url(spec["url"], config),
                insecure=spec.get("insecure", False),
            )
        )

    for gateway_name, gateway in sorted(gateways.items()):
        caddy = gateway.get("caddy", {})
        hostname = caddy.get("hostname")
        if caddy.get("enabled") and isinstance(hostname, str) and hostname:
            endpoints.append(
                build_endpoint(
                    gateway_name.title(),
                    "openclaw gateways",
                    f"https://{hostname}/",
                )
            )

    for node_name, node in cluster_nodes.items():
        endpoints.append(
            build_endpoint(
                node_name,
                "infrastructure",
                f"tcp://{node['management_address']}:22",
            )
        )

    for spec in STATIC_EXTERNAL_ENDPOINTS:
        endpoints.append(build_endpoint(spec["name"], spec["group"], spec["url"]))

    return endpoints


def main():
    repo_root = Path(__file__).resolve().parent.parent
    env_name = sys.argv[1] if len(sys.argv) > 1 else "home"
    config = load_environment_config(repo_root, env_name)
    print(yaml.safe_dump(build_gatus_endpoints(config), sort_keys=False), end="")


if __name__ == "__main__":
    main()
