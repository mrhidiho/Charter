
# Kubernetes + MySQL + Kafka + ProxySQL (with TLS, NetworkPolicies, Health Probes)

This repository documents and provides working manifests for running **multi-CPU Python applications** and **asynchronous consumers** on Kubernetes, writing safely to a **remote MySQL database** through **ProxySQL**.

The design includes:
- Multi-process CPU workers (Python, `multiprocessing`).
- Async I/O workers (Python, asyncio + aiomysql).
- Kafka ingestion.
- ProxySQL as connection pooler/router (TLS-enabled).
- End-to-end TLS enforcement (apps → ProxySQL, ProxySQL → MySQL).
- Strict NetworkPolicies (apps can only reach ProxySQL, Kafka, DNS; ProxySQL can only reach MySQL + DNS).
- InitContainers to **fail fast** on DB connectivity at startup.
- Sidecar containers to **continuously monitor DB connectivity**, exposing `/db` readiness, `/healthz`, and `/metrics`.
- PodDisruptionBudgets to ensure DB-ready pods remain during node drains.
- Deployment strategies (RollingUpdate with `maxUnavailable:0`) to align with PDBs.

---

## Repository Structure

- `docs/` – Markdown guides that explain each piece of the setup.
- `k8s/` – Kubernetes manifests (namespace, secrets, configmaps, deployments, ProxySQL, networkpolicies, PDBs, HPA/KEDA optional).
- `app/` – Python code for async service, CPU worker, Alembic migrations.
- `Dockerfile` – Container build for both app types.

---

## Quick Start

1. Build the Python app image:
   ```bash
   docker build -t ghcr.io/yourorg/py-stack:1.0.0 .
   docker push ghcr.io/yourorg/py-stack:1.0.0
   ```

2. Apply manifests (namespace, secrets, ProxySQL, migrations, apps, policies):
   ```bash
   kubectl apply -f k8s/00-namespace.yaml
   kubectl -n apps apply -f k8s/10-secrets-config.yaml
   kubectl -n apps apply -f k8s/21-proxysql-tls.yaml
   kubectl -n apps apply -f k8s/30-migrations-job.yaml
   kubectl -n apps apply -f k8s/40-apps.yaml
   kubectl -n apps apply -f k8s/60-networkpolicies.yaml
   ```

3. Verify DB connectivity via sidecar:
   ```bash
   kubectl -n apps port-forward deploy/async-writer 9090:9090
   curl localhost:9090/db
   ```

---

## Notes for the Team

- **Readiness = DB reachability.** Pods won’t serve until ProxySQL and MySQL are healthy.
- **Liveness = App process.** Still monitored independently, so we can distinguish app crashes from DB issues.
- **TLS everywhere.** Both client-side (apps → ProxySQL) and backend (ProxySQL → MySQL). Optionally mTLS to DB.
- **NetworkPolicies** ensure least-privilege communication paths.
- **PDBs + rollout strategy** ensure safe upgrades without losing DB-ready capacity.
- **Monitoring**: Sidecar exports Prometheus metrics at `/metrics` (port 9090).

---

## Learning Materials

See `docs/overview.md` and `docs/patterns.md` for detailed walkthroughs of why we use:
- Multiprocessing vs asyncio in Python
- Batching and idempotent upserts
- ProxySQL connection pooling
- PodDisruptionBudgets + Deployment strategy
- TLS enforcement and secret rotation

---

