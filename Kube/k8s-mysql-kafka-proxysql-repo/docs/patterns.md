
# Patterns and Rationale

This document explains the design patterns used in this repo, with examples. It is intended to help your team understand *why* each choice was made.

---

## 1. Multiprocessing vs Asyncio in Python

**Multiprocessing** is best for CPU-bound workloads because Python’s Global Interpreter Lock (GIL) prevents true multi-core parallelism in threads. By forking multiple processes, you can utilize all available CPUs.

Example (CPU worker):
```python
from multiprocessing import Pool
import time, os

def heavy_compute(x):
    return sum(i*i for i in range(10**6))

if __name__ == "__main__":
    with Pool(processes=os.cpu_count()) as pool:
        results = pool.map(heavy_compute, range(10))
        print(results)
```

**Asyncio** is best for I/O-bound workloads (e.g., DB writes, network requests) where tasks spend time waiting. Async lets you handle many concurrent connections efficiently in a single process.

Example (Async service):
```python
import asyncio

async def fetch(i):
    await asyncio.sleep(1)
    return i

async def main():
    tasks = [fetch(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    print(results)

asyncio.run(main())
```

**In this repo:**  
- `cpu_worker.py` → multiprocessing for CPU-heavy jobs  
- `async_service.py` → asyncio for I/O-heavy Kafka-to-MySQL writes

---

## 2. Batching and Idempotent Upserts

### Why Batching?
- Reduces number of round-trips to DB.
- Amortizes overhead of commits and network latency.
- Smooths out spikes in message inflow.

### Why Idempotent Upserts?
- Messages may be retried or re-processed.
- Ensures multiple inserts of the same record won’t corrupt data.

**Example (MySQL upsert):**
```sql
INSERT INTO telemetry (device_id, ts, metric, value)
VALUES ('router-1', '2025-09-03 17:00:00', 'rx_errors', 3)
ON DUPLICATE KEY UPDATE value=VALUES(value);
```

If the same row is ingested twice, it will just overwrite the value instead of duplicating.

---

## 3. ProxySQL Connection Pooling

Directly opening many DB connections per pod can exhaust MySQL limits. ProxySQL helps by:

- Multiplexing many client connections onto fewer backend connections.
- Routing `SELECT` queries to replicas, `INSERT/UPDATE` to writers.
- Enforcing TLS to the backend DB.

**Config snippet:**
```ini
mysql_servers =
(
  { address="mysql-writer.example.com", port=3306, hostgroup_id=10, use_ssl=1 },
  { address="mysql-reader.example.com", port=3306, hostgroup_id=20, use_ssl=1 }
)

mysql_query_rules =
(
  { rule_id=1, match_digest="^SELECT", destination_hostgroup=20, apply=1, active=1 },
  { rule_id=2, match_digest=".*", destination_hostgroup=10, apply=1, active=1 }
)
```

This routes reads to readers and writes to the writer.

---

## 4. PodDisruptionBudgets + Deployment Strategy

### PodDisruptionBudgets (PDBs)
Ensure a minimum number (or percentage) of pods remain available during voluntary disruptions (e.g., node drains). Combined with readiness probes tied to DB connectivity, this ensures the system never drops below safe DB-ready capacity.

Example:
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: async-writer-pdb }
spec:
  minAvailable: 2
  selector:
    matchLabels: { app: async-writer }
```

### Deployment Strategy
We use **RollingUpdate** with:
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 0
    maxSurge: 1
```

This ensures:
- No DB-ready pods are taken down until replacements are up and verified.
- Rollouts are safe even with strict PDBs.

---

## 5. TLS Enforcement and Secret Rotation

### TLS Enforcement
- Apps → ProxySQL: require TLS using CA validation (`ssl={"ca": "/etc/mysql/proxysql-ca.pem"}`).
- ProxySQL → MySQL: `use_ssl=1` with CA, certs, and optional client keys.

### Secret Rotation
- Store certs in Kubernetes Secrets.  
- To rotate, update the Secret and restart pods:
  ```bash
  kubectl -n apps create secret generic proxysql-frontend-tls --from-file=proxysql-ca.pem --from-file=proxysql-cert.pem --from-file=proxysql-key.pem --dry-run=client -o yaml | kubectl apply -f -
  kubectl -n apps rollout restart deploy/proxysql
  kubectl -n apps rollout restart deploy/async-writer deploy/cpu-writer
  ```

---

## Key Takeaways

- Use the right concurrency model for the workload.  
- Batch + upsert for efficiency and correctness.  
- Pool DB connections with ProxySQL to prevent overload.  
- Protect availability with PDBs + rolling updates.  
- Encrypt traffic and rotate secrets regularly.

