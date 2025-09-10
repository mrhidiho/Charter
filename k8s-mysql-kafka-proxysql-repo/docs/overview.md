
# Overview: Kubernetes + Python Workers + Remote DB

This guide explains the overall architecture.

## Architecture Diagram

```
[Producers] -> Kafka -> Async Service Pods -> ProxySQL -> MySQL
             -> CPU Worker Pods ----------^
```

- **Kafka**: decouples ingestion and DB writes, providing backpressure control.
- **Async Service Pods**: consume telemetry and write in batches.
- **CPU Worker Pods**: perform compute-heavy jobs, write results with upserts.
- **ProxySQL**: connection pooler and router, enforces TLS and read/write split.
- **MySQL**: remote database (Aurora, RDS, or on-prem).

---

## Key Features

- TLS everywhere (app → ProxySQL, ProxySQL → MySQL).
- InitContainer DB checks at startup (fail fast).
- Continuous DB health sidecar (Prometheus metrics).
- PDBs & RollingUpdate strategy to ensure DB-ready pods remain during node drains.
- Strict NetworkPolicies.


See [patterns.md](patterns.md) for detailed explanations of design choices.
