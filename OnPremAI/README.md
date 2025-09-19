# On‑Network AI Starter (Air‑gapped, Read‑Only)

This starter deploys a **read-only** internal Retrieval‑Augmented Generation (RAG) stack for parsing repos, Jira, Confluence, and logs, and generating docs—**without data egress** and with **no write access** to stage/prod.

## Components
- **LLM Serving (vLLM)** — hosts open‑weights models (e.g., Llama 3.1 / Mistral) with **no outbound internet**.
- **RAG API (FastAPI)** — stateless service that queries Vector DB and OpenSearch and calls the LLM.
- **Vector DB (Qdrant)** — stores embeddings; HA-ready.
- **OpenSearch** — keyword search + logs (values provided to use upstream chart; mirror internally).
- **Airflow/Connectors (optional)** — read-only ingestion of Jira/Confluence/Git/logs into Qdrant/OpenSearch.
- **API Gateway (NGINX)** — internal-only reverse proxy with auth header passthrough.
- **Gatekeeper (OPA) constraints** — enforce no egress, read‑only FS, denied capabilities, registry allowlist.
- **NetworkPolicies** — default‑deny between namespaces; explicit allow only where needed.

> ⚠️ **Air‑gapped note:** Mirror container images and Helm charts to your internal registry/repo. All values reference generic names—replace with your mirrors before applying.

## Namespaces
- `ingest` (Airflow/Connectors)
- `search` (OpenSearch)
- `vector` (Qdrant)
- `llm` (vLLM server)
- `api` (RAG API + API Gateway)

## Quickstart (Kubernetes)
1. Create namespaces: `kubectl apply -f kubernetes/namespaces.yaml`.
2. Install **Gatekeeper** (from internal mirror) then apply constraints:
   ```bash
   kubectl apply -f kubernetes/gatekeeper/constraints/
   ```
3. Deploy OpenSearch (mirror of upstream chart) with provided values:
   ```bash
   helm upgrade --install opensearch your-mirror/opensearch -n search -f helm/values/opensearch-values.yaml
   ```
4. Deploy Qdrant:
   ```bash
   helm upgrade --install qdrant your-mirror/qdrant -n vector -f helm/values/qdrant-values.yaml
   ```
5. Deploy vLLM (chart included):
   ```bash
   helm upgrade --install vllm helm/charts/vllm -n llm -f helm/charts/vllm/values.yaml
   ```
6. Deploy RAG API (chart included):
   ```bash
   helm upgrade --install rag-api helm/charts/rag-api -n api -f helm/charts/rag-api/values.yaml
   ```
7. Deploy API Gateway (internal NGINX reverse proxy):
   ```bash
   helm upgrade --install api-gw helm/charts/api-gateway -n api -f helm/charts/api-gateway/values.yaml
   ```
8. Apply **NetworkPolicies** (after Services are up):
   ```bash
   kubectl apply -f kubernetes/networkpolicies/
   ```

## Model Weights
- Place your model weights (e.g., `Llama-3.1-8B-Instruct`) on an internal object store or NFS and mount to vLLM.
- **No outbound calls**; pod egress is blocked at NetworkPolicy. Edit `helm/charts/vllm/values.yaml` volumes to point to your storage.

## Security Controls
- **Zero egress**: Egress `NetworkPolicies` + Gateway/Firewall deny; no cluster-wide egress.
- **Read-only FS**: Pod spec enforces `readOnlyRootFilesystem: true`.
- **No host access**: Deny `hostNetwork`, `hostPID`, `hostIPC`, privileged, NET_RAW, NET_ADMIN.
- **Image allowlist**: Gatekeeper constraint restricts registries to your internal mirrors.
- **No prod writes**: This stack does not mount creds for prod/stage. Connectors only use read-only tokens.

## Local Build
- RAG API: `make build-api` then `make push-api` (edit image names).
- vLLM chart mounts model path; ensure node has access to internal model store.

## Connector Stubs
`services/connectors/` has Jira/Git/Confluence/OpenSearch stubs that **pull read-only** and index into Qdrant/OpenSearch.
Wire them into Airflow if desired.

---

## Directory Map
```
onnet-ai-starter/
  helm/
    charts/
      vllm/
      rag-api/
      api-gateway/
    values/
      opensearch-values.yaml
      qdrant-values.yaml
  kubernetes/
    namespaces.yaml
    gatekeeper/constraints/...
    networkpolicies/...
  services/
    rag_api/...
    connectors/...
  Makefile
  .env.example
  README.md
```
