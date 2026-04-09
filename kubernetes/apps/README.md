# Apps

Argo CD `Application` definitions for `homelab-core` live here.

Current layout:

- `root-app.yaml`: the top-level app-of-apps entrypoint
- `platform/`: platform services owned by Argo CD for the base cluster, including shared infrastructure apps and cluster-local automation such as Renovate
