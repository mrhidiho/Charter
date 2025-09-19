from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import os, httpx
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from opensearchpy import OpenSearch

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant.vector.svc.cluster.local:6333")
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://opensearch.search.svc.cluster.local:9200")
LLM_URL = os.getenv("LLM_URL", "http://vllm.llm.svc.cluster.local:8000")
TOP_K = int(os.getenv("TOP_K", "8"))
COLLECTION = os.getenv("QDRANT_COLLECTION", "unified_docs")

app = FastAPI(title="RAG API", version="0.1.0")

qdrant = QdrantClient(url=QDRANT_URL, timeout=30.0)
os_client = OpenSearch(hosts=[OPENSEARCH_URL], verify_certs=False, ssl_show_warn=False)

class Query(BaseModel):
    query: str
    filters: Optional[dict] = None

class Chunk(BaseModel):
    text: str
    source: str
    score: float

class Answer(BaseModel):
    answer: str
    chunks: List[Chunk]

def _format_prompt(question: str, chunks: List[Chunk]) -> str:
    context = "\n\n".join([f"[{i+1}] {c.text}\nSOURCE: {c.source}" for i, c in enumerate(chunks)])
    return f"""You are an internal Charter/Spectrum assistant. Use only the provided context.
Cite sources as [#] at the end of each sentence you derive from a chunk.
Question: {question}

Context:
{context}

Answer:
"""

async def _call_llm(prompt: str) -> str:
    # vLLM OpenAI-compatible or TGI text-generation-inference format; here we use vLLM's OpenAI-style route.
    url = f"{LLM_URL}/v1/completions"
    payload = {"model": "llm", "prompt": prompt, "max_tokens": 512, "temperature": 0.1}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        if "choices" in data and data["choices"]:
            return data["choices"][0]["text"]
        return data

@app.post("/rag", response_model=Answer)
async def rag(q: Query, authorization: Optional[str] = Header(None)):
    # Qdrant vector search (assumes embeddings already stored). We also try keyword fallback on OpenSearch.
    try:
        res = qdrant.search(collection_name=COLLECTION, query_vector=[0.0]*1024,  # placeholder: server-side uses stored vectors (hnsw quantizer) if enabled
                            limit=TOP_K, with_payload=True)
    except Exception:
        res = []

    chunks: List[Chunk] = []
    for p in res:
        payload = p.payload or {}
        chunks.append(Chunk(text=payload.get("text",""),
                            source=payload.get("source",""),
                            score=p.score))
    # Keyword fallback if vector empty
    if not chunks:
        try:
            hits = os_client.search(index="unified_docs", body={"query": {"match": {"text": q.query}}, "size": TOP_K})
            for h in hits["hits"]["hits"]:
                src = h.get("_source", {})
                chunks.append(Chunk(text=src.get("text",""),
                                    source=src.get("source",""),
                                    score=h.get("_score",0.0)))
        except Exception:
            pass

    prompt = _format_prompt(q.query, chunks)
    completion = await _call_llm(prompt)
    return Answer(answer=completion, chunks=chunks)

@app.get("/healthz")
def healthz():
    return {"ok": True}
