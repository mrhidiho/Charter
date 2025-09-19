# On-Network AI System – Full Documentation

This documentation explains how to install, configure, and use the **air-gapped, read-only AI system** for parsing repositories, Jira/Confluence tickets, logs, and metrics. It also includes tips for extending the platform with additional features.

---

## 1. Overview

This project provides a **Retrieval-Augmented Generation (RAG) platform** designed for secure enterprise environments:

- Runs entirely **on-premises** with **no outbound internet access**.  
- Ingests company resources (repos, Jira/Confluence, logs, metrics).  
- Stores structured/unstructured content in **OpenSearch** (keyword search) and **Qdrant** (vector search).  
- Serves an **open-source LLM** (Llama 3.1, Mistral/Mixtral, etc.) with **vLLM** or **TGI**.  
- Provides a **FastAPI-based RAG service** for natural language querying.  
- Enforces **network isolation, read-only accounts, and auditability**.

---

## 2. Prerequisites

- **Kubernetes cluster** (≥ v1.26, GPU nodes recommended for LLM serving).  
- **Internal container registry** (Harbor, Nexus, or Artifactory).  
- **Helm 3.12+** for chart deployments.  
- **Gatekeeper** or **Kyverno** installed for policy enforcement.  
- **Vault** (or equivalent secret manager) for token storage.  
- **GPU drivers and runtime** (NVIDIA GPU Operator or similar).  

---

## 3. Installation

### Step 1: Prepare Namespaces

```bash
kubectl apply -f kubernetes/namespaces.yaml
```

### Step 2: Deploy Security Controls

Install **OPA Gatekeeper** (mirrored internally):

```bash
helm upgrade --install gatekeeper your-mirror/gatekeeper -n gatekeeper-system
kubectl apply -f kubernetes/gatekeeper/constraints/
```

These constraints enforce:
- No privileged pods.  
- No host networking.  
- Read-only root filesystems.  
- Allowed container registries only.  
- Denied egress to the internet.

### Step 3: Deploy OpenSearch

Mirror the upstream OpenSearch chart to your internal registry and apply:

```bash
helm upgrade --install opensearch your-mirror/opensearch   -n search -f helm/values/opensearch-values.yaml
```

### Step 4: Deploy Qdrant

```bash
helm upgrade --install qdrant your-mirror/qdrant   -n vector -f helm/values/qdrant-values.yaml
```

### Step 5: Deploy vLLM (LLM Server)

- Place model weights (e.g., `llama-3.1-8b-instruct`) on an internal object store or PVC.  
- Update `helm/charts/vllm/values.yaml` to point to the model path.  

Deploy:

```bash
helm upgrade --install vllm helm/charts/vllm   -n llm -f helm/charts/vllm/values.yaml
```

### Step 6: Deploy RAG API

Build and push your image:

```bash
make build-api
make push-api
```

Deploy:

```bash
helm upgrade --install rag-api helm/charts/rag-api   -n api -f helm/charts/rag-api/values.yaml
```

### Step 7: Deploy API Gateway (NGINX)

```bash
helm upgrade --install api-gateway helm/charts/api-gateway   -n api -f helm/charts/api-gateway/values.yaml
```

### Step 8: Apply Network Policies

```bash
kubectl apply -f kubernetes/networkpolicies/
```

---

## 4. Usage

### Querying the RAG API

Send queries to the API Gateway (internal only):

```bash
curl -X POST http://api-gateway.api.svc.cluster.local/rag   -H "Content-Type: application/json"   -d '{"query": "Summarize the last 10 Jira tickets"}'
```

Example response:

```json
{
  "answer": "The last 10 Jira tickets include bug fixes for API latency [1], logging improvements [2], and a new deployment workflow [3].",
  "chunks": [
    {"text": "Fixed latency issue in API handler", "source": "jira:ENG-123", "score": 0.92},
    {"text": "Improved log rotation policy", "source": "jira:ENG-124", "score": 0.89}
  ]
}
```

### Health Check

```bash
curl http://api-gateway.api.svc.cluster.local/healthz
```

### Ingesting Jira/Confluence/Git

Connector stubs (`services/connectors/`) pull read-only data into OpenSearch + Qdrant.

Example (Jira):

```bash
kubectl run jira-connector   --image=registry.intra/ai/connectors:v0.1.0   --env-file=.env   --restart=OnFailure -n ingest
```

---

## 5. Tips & Suggestions

- **Embedding Models:** Use `BGE-large-en v1.5` for best retrieval quality; `all-MiniLM-L6-v2` for CPU-only setups.  
- **Scaling vLLM:** Use tensor parallelism if running large models on multiple GPUs.  
- **Dashboards:** Configure OpenSearch Dashboards for log/error exploration.  
- **Feature Store:** Add **Feast** if you want predictive maintenance models.  
- **Observability:** Add Prometheus + Grafana for RAG latency and ingestion lag monitoring.  
- **Content Types:** Extend connectors for Slack, internal wikis, or CI/CD job logs.  

---

## 6. Security Considerations

- **Zero egress:** All pods restricted with `NetworkPolicies`.  
- **No prod writes:** Service accounts have GET-only scopes.  
- **Audit trails:** Log queries and completions (scrub sensitive data).  
- **Immutability:** Container digests pinned; model weights stored read-only.  
- **Change control:** CAB approvals required for new models or connectors.  

---

## 7. Extending the System

- **Multi-language support** (swap in multilingual embeddings like `LaBSE`).  
- **Streaming log parsing** (Kafka → OpenSearch + embeddings).  
- **Fine-tuning adapters** (LoRA on domain-specific tickets).  
- **Chat UI** (internal React dashboard instead of curl).  

---

## 8. Troubleshooting

- **Model not loading:** Ensure PVC or NFS mount path matches `values.yaml`.  
- **No search results:** Check ingestion jobs are running in `ingest` namespace.  
- **Connection errors:** Verify `NetworkPolicies` allow API → LLM/Vector/Search.  
- **High latency:** Scale `rag-api` replicas, increase GPU quota for vLLM.  

---

## 9. How-To Scenarios

### Generate Documentation from Repos
1. Run `git.py` connector with repo list in `.env`.  
2. Embeddings + keyword index stored automatically.  
3. Query:  
   ```bash
   curl -X POST ... -d '{"query": "Generate architecture overview of repo X"}'
   ```

### Parse Logs for Errors
1. Ingest logs into OpenSearch.  
2. Query:  
   ```bash
   curl -X POST ... -d '{"query": "What errors occurred in the last 24 hours?"}'
   ```

### Predict Maintenance Risks
1. Extend ETL to push incident/metrics into **Feast**.  
2. Train models (offline) and publish scores to OpenSearch.  
3. Dashboard shows “at-risk services” for next 30 days.

---

## 10. Conclusion

This system provides a **secure, extensible AI platform** for enterprise knowledge and ops intelligence. It is production-ready with built-in **network isolation, auditability, and scalability**, while remaining **flexible for future extensions** like predictive maintenance, chat interfaces, or new data connectors.

---
