#!/usr/bin/env python3
from pathlib import Path

from gatus_endpoints import build_gatus_endpoints
from validate_kubernetes_common import expect, find_document, split_onepassword_selector
import yaml


def validate(repo_root: Path, config: dict, errors: list[str]):
    platform = config["platform"]

    store = find_document(repo_root / "kubernetes" / "manifests" / "platform" / "01-clustersecretstore-onepassword.yaml", "ClusterSecretStore", "onepassword-sdk")
    expect(
        store.get("spec", {}).get("provider", {}).get("onepassword", {}).get("connectHost") == "http://onepassword-connect.onepassword-connect.svc.cluster.local:8080",
        "kubernetes/manifests/platform/01-clustersecretstore-onepassword.yaml: connectHost must match the in-cluster 1Password Connect service",
        errors,
    )
    expect(
        store.get("spec", {}).get("provider", {}).get("onepassword", {}).get("vaults") == {platform["onepassword_vault"]: 1},
        "kubernetes/manifests/platform/01-clustersecretstore-onepassword.yaml: vaults must match platform.onepassword_vault",
        errors,
    )
    expect(
        store.get("spec", {}).get("provider", {}).get("onepassword", {}).get("auth", {}).get("secretRef", {}).get("connectTokenSecretRef") == {
            "name": "onepassword-connect-token",
            "namespace": "onepassword-connect",
            "key": "token",
        },
        "kubernetes/manifests/platform/01-clustersecretstore-onepassword.yaml: connect token secret ref must target onepassword-connect/onepassword-connect-token#token",
        errors,
    )

    cloudflare = find_document(repo_root / "kubernetes" / "manifests" / "platform" / "20-cert-manager-cloudflare-token.yaml", "ExternalSecret", "cloudflare-api-token-secret")
    cloudflare_ref = cloudflare.get("spec", {}).get("data", [{}])[0].get("remoteRef", {})
    cloudflare_item, cloudflare_property = split_onepassword_selector(platform["secrets"]["cloudflare_api_token_key"])
    expect(
        cloudflare_ref.get("key") == cloudflare_item and cloudflare_ref.get("property") == cloudflare_property,
        "kubernetes/manifests/platform/20-cert-manager-cloudflare-token.yaml: remoteRef key/property must match platform.secrets.cloudflare_api_token_key",
        errors,
    )

    renovate_namespace = find_document(repo_root / "kubernetes" / "manifests" / "platform" / "22-renovate.yaml", "Namespace", "renovate")
    expect(
        renovate_namespace.get("metadata", {}).get("annotations", {}).get("argocd.argoproj.io/sync-wave") == "22",
        "kubernetes/manifests/platform/22-renovate.yaml: renovate namespace must use sync-wave 22",
        errors,
    )

    renovate_secret = find_document(repo_root / "kubernetes" / "manifests" / "platform" / "22-renovate.yaml", "ExternalSecret", "renovate-env")
    renovate_ref = renovate_secret.get("spec", {}).get("data", [{}])[0].get("remoteRef", {})
    renovate_item, renovate_property = split_onepassword_selector(platform["secrets"]["renovate_github_token_key"])
    expect(
        renovate_secret.get("metadata", {}).get("namespace") == "renovate",
        "kubernetes/manifests/platform/22-renovate.yaml: renovate ExternalSecret must target the renovate namespace",
        errors,
    )
    expect(
        renovate_secret.get("spec", {}).get("target", {}).get("name") == "renovate-env",
        "kubernetes/manifests/platform/22-renovate.yaml: target secret name must be renovate-env",
        errors,
    )
    expect(
        renovate_secret.get("spec", {}).get("data", [{}])[0].get("secretKey") == "RENOVATE_TOKEN",
        "kubernetes/manifests/platform/22-renovate.yaml: secretKey must be RENOVATE_TOKEN",
        errors,
    )
    expect(
        renovate_ref.get("key") == renovate_item and renovate_ref.get("property") == renovate_property,
        "kubernetes/manifests/platform/22-renovate.yaml: remoteRef key/property must match platform.secrets.renovate_github_token_key",
        errors,
    )

    velero_secret = find_document(repo_root / "kubernetes" / "manifests" / "platform" / "20-velero-backblaze-credentials.yaml", "ExternalSecret", "velero-backblaze-credentials")
    velero_items = {item.get("secretKey"): item.get("remoteRef", {}) for item in velero_secret.get("spec", {}).get("data", [])}
    velero_key_id_item, velero_key_id_property = split_onepassword_selector(platform["secrets"]["velero_key_id_key"])
    velero_app_item, velero_app_property = split_onepassword_selector(platform["secrets"]["velero_application_key_key"])
    expect(
        velero_items.get("key_id") == {"key": velero_key_id_item, "property": velero_key_id_property},
        "kubernetes/manifests/platform/20-velero-backblaze-credentials.yaml: key_id remoteRef key/property must match platform.secrets.velero_key_id_key",
        errors,
    )
    expect(
        velero_items.get("application_key") == {"key": velero_app_item, "property": velero_app_property},
        "kubernetes/manifests/platform/20-velero-backblaze-credentials.yaml: application_key remoteRef key/property must match platform.secrets.velero_application_key_key",
        errors,
    )

    issuer = find_document(repo_root / "kubernetes" / "manifests" / "platform" / "30-clusterissuer-letsencrypt.yaml", "ClusterIssuer", platform["cluster_issuer_name"])
    expect(
        issuer.get("spec", {}).get("acme", {}).get("solvers", [{}])[0].get("selector", {}).get("dnsZones") == [platform["management_domain"]],
        "kubernetes/manifests/platform/30-clusterissuer-letsencrypt.yaml: dnsZones must match platform.management_domain",
        errors,
    )

    argocd_cert = find_document(repo_root / "kubernetes" / "manifests" / "platform" / "35-argocd-certificate.yaml", "Certificate", "argocd-server-tls")
    expect(
        argocd_cert.get("spec", {}).get("dnsNames") == [platform["argocd_hostname"]],
        "kubernetes/manifests/platform/35-argocd-certificate.yaml: dnsNames must match platform.argocd_hostname",
        errors,
    )

    argocd_ingress = find_document(repo_root / "kubernetes" / "manifests" / "platform" / "40-argocd-ingress.yaml", "Ingress", "argocd-server")
    expect(
        argocd_ingress.get("spec", {}).get("rules", [{}])[0].get("host") == platform["argocd_hostname"],
        "kubernetes/manifests/platform/40-argocd-ingress.yaml: ingress host must match platform.argocd_hostname",
        errors,
    )

    home_assistant_service = find_document(repo_root / "kubernetes" / "manifests" / "platform" / "42-home-assistant.yaml", "Service", "home-assistant-external")
    expect(
        home_assistant_service.get("metadata", {}).get("namespace") == "home-assistant",
        "kubernetes/manifests/platform/42-home-assistant.yaml: Service must target the home-assistant namespace",
        errors,
    )
    expect(
        home_assistant_service.get("spec", {}).get("type") == "ExternalName",
        "kubernetes/manifests/platform/42-home-assistant.yaml: Service must use type ExternalName",
        errors,
    )
    expect(
        home_assistant_service.get("spec", {}).get("externalName") == f'{config["home_assistant"]["management_address"]}.sslip.io',
        "kubernetes/manifests/platform/42-home-assistant.yaml: Service externalName must resolve the Home Assistant management address through sslip.io",
        errors,
    )
    expect(
        home_assistant_service.get("spec", {}).get("ports") == [{"name": "http", "port": 80, "protocol": "TCP", "targetPort": 80}],
        "kubernetes/manifests/platform/42-home-assistant.yaml: Service must expose tcp/80 as the Home Assistant backend port",
        errors,
    )

    home_assistant_cert = find_document(repo_root / "kubernetes" / "manifests" / "platform" / "42-home-assistant.yaml", "Certificate", "home-assistant-tls")
    expect(
        home_assistant_cert.get("spec", {}).get("dnsNames") == [platform["home_assistant_hostname"]],
        "kubernetes/manifests/platform/42-home-assistant.yaml: certificate dnsNames must match platform.home_assistant_hostname",
        errors,
    )

    home_assistant_ingress = find_document(repo_root / "kubernetes" / "manifests" / "platform" / "42-home-assistant.yaml", "Ingress", "home-assistant")
    expect(
        home_assistant_ingress.get("spec", {}).get("rules", [{}])[0].get("host") == platform["home_assistant_hostname"],
        "kubernetes/manifests/platform/42-home-assistant.yaml: ingress host must match platform.home_assistant_hostname",
        errors,
    )
    expect(
        home_assistant_ingress.get("spec", {}).get("rules", [{}])[0].get("http", {}).get("paths", [{}])[0].get("backend", {}).get("service", {}).get("name") == "home-assistant-external",
        "kubernetes/manifests/platform/42-home-assistant.yaml: ingress backend service must be home-assistant-external",
        errors,
    )
    expect(
        home_assistant_ingress.get("spec", {}).get("tls", [{}])[0].get("hosts") == [platform["home_assistant_hostname"]],
        "kubernetes/manifests/platform/42-home-assistant.yaml: ingress TLS hosts must match platform.home_assistant_hostname",
        errors,
    )

    velero_config_secret = find_document(repo_root / "kubernetes" / "manifests" / "platform" / "20-velero-backblaze-config.yaml", "ExternalSecret", "velero-backblaze-config")
    velero_config_items = {item.get("secretKey"): item.get("remoteRef", {}) for item in velero_config_secret.get("spec", {}).get("data", [])}
    velero_secret_item, _ = split_onepassword_selector(platform["secrets"]["velero_application_key_key"])
    expect(
        velero_config_items.get("bucket") == {"key": velero_secret_item, "property": "bucket name"},
        "kubernetes/manifests/platform/20-velero-backblaze-config.yaml: bucket remoteRef key/property must match the Velero 1Password item bucket name field",
        errors,
    )
    expect(
        velero_config_items.get("endpoint") == {"key": velero_secret_item, "property": "endpoint"},
        "kubernetes/manifests/platform/20-velero-backblaze-config.yaml: endpoint remoteRef key/property must match the Velero 1Password item endpoint field",
        errors,
    )
    expect(
        velero_config_items.get("region") == {"key": velero_secret_item, "property": "region"},
        "kubernetes/manifests/platform/20-velero-backblaze-config.yaml: region remoteRef key/property must match the Velero 1Password item region field",
        errors,
    )

    velero_reconciler = find_document(repo_root / "kubernetes" / "manifests" / "platform" / "50-velero-backupstoragelocation-reconciler.yaml", "Deployment", "velero-bsl-reconciler")
    reconciler_container = velero_reconciler.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [{}])[0]
    reconciler_env = {
        item.get("name"): item.get("valueFrom", {}).get("secretKeyRef", {})
        for item in reconciler_container.get("env", [])
    }
    expect(
        reconciler_env.get("VELERO_BUCKET") == {"name": "velero-backblaze-config", "key": "bucket"},
        "kubernetes/manifests/platform/50-velero-backupstoragelocation-reconciler.yaml: VELERO_BUCKET must read from secret velero-backblaze-config/bucket",
        errors,
    )
    expect(
        reconciler_env.get("VELERO_REGION") == {"name": "velero-backblaze-config", "key": "region"},
        "kubernetes/manifests/platform/50-velero-backupstoragelocation-reconciler.yaml: VELERO_REGION must read from secret velero-backblaze-config/region",
        errors,
    )
    expect(
        reconciler_env.get("VELERO_S3_URL") == {"name": "velero-backblaze-config", "key": "s3Url"},
        "kubernetes/manifests/platform/50-velero-backupstoragelocation-reconciler.yaml: VELERO_S3_URL must read from secret velero-backblaze-config/s3Url",
        errors,
    )

    metallb_pool = find_document(repo_root / "kubernetes" / "manifests" / "platform" / "55-metallb-address-pool.yaml", "IPAddressPool", "management-lan")
    expect(
        metallb_pool.get("spec", {}).get("addresses") == config["cluster"]["ingress"]["metallb_addresses"],
        "kubernetes/manifests/platform/55-metallb-address-pool.yaml: addresses must match cluster.ingress.metallb_addresses",
        errors,
    )

    homepage_secret = find_document(repo_root / "kubernetes" / "manifests" / "homepage" / "10-homepage.yaml", "ExternalSecret", "homepage-argocd-token")
    homepage_ref = homepage_secret.get("spec", {}).get("data", [{}])[0].get("remoteRef", {})
    homepage_item, homepage_property = split_onepassword_selector(platform["secrets"]["homepage_argocd_key"])
    expect(
        homepage_ref.get("key") == homepage_item and homepage_ref.get("property") == homepage_property,
        "kubernetes/manifests/homepage/10-homepage.yaml: homepage argocd token key/property must match platform.secrets.homepage_argocd_key",
        errors,
    )

    homepage_cert = find_document(repo_root / "kubernetes" / "manifests" / "homepage" / "10-homepage.yaml", "Certificate", "homepage-tls")
    expect(
        homepage_cert.get("spec", {}).get("dnsNames") == [platform["homepage_hostname"]],
        "kubernetes/manifests/homepage/10-homepage.yaml: homepage certificate dnsNames must match platform.homepage_hostname",
        errors,
    )

    n8n_ingress = find_document(repo_root / "kubernetes" / "manifests" / "n8n" / "20-n8n.yaml", "Ingress", "n8n")
    expect(
        n8n_ingress.get("spec", {}).get("rules", [{}])[0].get("host") == platform["n8n_hostname"],
        "kubernetes/manifests/n8n/20-n8n.yaml: ingress host must match platform.n8n_hostname",
        errors,
    )
    expect(
        n8n_ingress.get("spec", {}).get("tls", [{}])[0].get("hosts") == [platform["n8n_hostname"]],
        "kubernetes/manifests/n8n/20-n8n.yaml: ingress TLS hosts must match platform.n8n_hostname",
        errors,
    )

    netbox_secret = find_document(repo_root / "kubernetes" / "manifests" / "netbox" / "10-netbox-secrets.yaml", "ExternalSecret", "netbox-secrets")
    netbox_secret_items = {item.get("secretKey"): item.get("remoteRef", {}) for item in netbox_secret.get("spec", {}).get("data", [])}
    netbox_secret_template_data = netbox_secret.get("spec", {}).get("target", {}).get("template", {}).get("data", {})
    netbox_pepper_item, netbox_pepper_property = split_onepassword_selector(platform["secrets"]["netbox_api_token_pepper_key"])
    expect(
        netbox_secret_items.get("api_token_pepper") == {"key": netbox_pepper_item, "property": netbox_pepper_property},
        "kubernetes/manifests/netbox/10-netbox-secrets.yaml: api_token_pepper remoteRef key/property must match platform.secrets.netbox_api_token_pepper_key",
        errors,
    )
    expect(
        netbox_secret_template_data.get("api_token_peppers.yaml") == 'API_TOKEN_PEPPERS:\n  1: "{{ .api_token_pepper }}"\n',
        "kubernetes/manifests/netbox/10-netbox-secrets.yaml: template data must define api_token_peppers.yaml from api_token_pepper",
        errors,
    )

    netbox_values = yaml.safe_load((repo_root / "kubernetes" / "charts" / "netbox" / "values.yaml").read_text())
    expect(
        netbox_values.get("ingress", {}).get("hosts", [{}])[0].get("host") == platform["netbox_hostname"],
        "kubernetes/charts/netbox/values.yaml: ingress host must match platform.netbox_hostname",
        errors,
    )
    expect(
        netbox_values.get("ingress", {}).get("tls", [{}])[0].get("hosts", [None])[0] == platform["netbox_hostname"],
        "kubernetes/charts/netbox/values.yaml: ingress TLS host must match platform.netbox_hostname",
        errors,
    )
    expect(
        netbox_values.get("extraConfig") == [{"secret": {"secretName": "netbox-secrets", "items": [{"key": "api_token_peppers.yaml", "path": "api_token_peppers.yaml"}]}}],
        "kubernetes/charts/netbox/values.yaml: extraConfig must mount api_token_peppers.yaml from netbox-secrets",
        errors,
    )

    gatus_values = yaml.safe_load((repo_root / "kubernetes" / "charts" / "gatus" / "values.yaml").read_text())
    expect(
        gatus_values.get("ingress", {}).get("hosts", [None])[0] == platform["gatus_hostname"],
        "kubernetes/charts/gatus/values.yaml: ingress host must match platform.gatus_hostname",
        errors,
    )
    expect(
        gatus_values.get("ingress", {}).get("tls", [{}])[0].get("hosts", [None])[0] == platform["gatus_hostname"],
        "kubernetes/charts/gatus/values.yaml: ingress TLS host must match platform.gatus_hostname",
        errors,
    )
    expected_gatus_endpoints = build_gatus_endpoints(config)
    actual_gatus_endpoints = gatus_values.get("config", {}).get("endpoints")
    expect(
        actual_gatus_endpoints == expected_gatus_endpoints,
        "kubernetes/charts/gatus/values.yaml: config.endpoints must match scripts/render-gatus-config output",
        errors,
    )
    if isinstance(actual_gatus_endpoints, list):
        endpoint_names = [endpoint.get("name") for endpoint in actual_gatus_endpoints if isinstance(endpoint, dict)]
        expect(
            len(endpoint_names) == len(set(endpoint_names)),
            "kubernetes/charts/gatus/values.yaml: endpoint names must be unique",
            errors,
        )

    operator_apps = config.get("platform", {}).get("monitoring", {}).get("gatus", {}).get("operator_apps", [])
    operator_app_names = {
        spec.get("name")
        for spec in operator_apps
        if isinstance(spec, dict) and isinstance(spec.get("name"), str)
    }
    operator_hostname_keys = {
        spec.get("hostname_key")
        for spec in operator_apps
        if isinstance(spec, dict) and isinstance(spec.get("hostname_key"), str)
    }
    expect(
        {"Home Assistant", "NetBox", "n8n"}.issubset(operator_app_names),
        "config/home.yaml: platform.monitoring.gatus.operator_apps must include Home Assistant, NetBox, and n8n",
        errors,
    )
    expect(
        {"home_assistant_hostname", "netbox_hostname", "n8n_hostname"}.issubset(operator_hostname_keys),
        "config/home.yaml: platform.monitoring.gatus.operator_apps must cover platform.home_assistant_hostname, platform.netbox_hostname, and platform.n8n_hostname",
        errors,
    )

    longhorn_values = yaml.safe_load((repo_root / "kubernetes" / "charts" / "longhorn" / "values.yaml").read_text())
    expect(
        longhorn_values.get("ingress", {}).get("enabled") is True,
        "kubernetes/charts/longhorn/values.yaml: ingress.enabled must be true",
        errors,
    )
    expect(
        longhorn_values.get("ingress", {}).get("ingressClassName") == "traefik",
        "kubernetes/charts/longhorn/values.yaml: ingressClassName must be traefik",
        errors,
    )
    expect(
        longhorn_values.get("ingress", {}).get("host") == platform["longhorn_hostname"],
        "kubernetes/charts/longhorn/values.yaml: ingress host must match platform.longhorn_hostname",
        errors,
    )
    expect(
        longhorn_values.get("ingress", {}).get("tls") is True,
        "kubernetes/charts/longhorn/values.yaml: ingress TLS must be enabled",
        errors,
    )
    expect(
        longhorn_values.get("ingress", {}).get("tlsSecret") == "longhorn-tls",
        "kubernetes/charts/longhorn/values.yaml: ingress tlsSecret must be longhorn-tls",
        errors,
    )
    expect(
        not (repo_root / "kubernetes" / "manifests" / "storage" / "10-storageclasses.yaml").exists(),
        "kubernetes/manifests/storage/10-storageclasses.yaml: local-path shim manifest must be removed once local-storage is retired",
        errors,
    )

    telemetry_config = find_document(repo_root / "kubernetes" / "manifests" / "telemetry" / "10-prometheus-agent.yaml", "ConfigMap", "prometheus-agent-config")
    prometheus_yml = telemetry_config.get("data", {}).get("prometheus.yml", "")
    expect(platform["telemetry"]["prometheus_remote_write_url"] in prometheus_yml, "kubernetes/manifests/telemetry/10-prometheus-agent.yaml: remote write URL must match platform.telemetry.prometheus_remote_write_url", errors)
