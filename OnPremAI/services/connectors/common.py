import os
from qdrant_client import QdrantClient
from opensearchpy import OpenSearch

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant.vector.svc.cluster.local:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "unified_docs")
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://opensearch.search.svc.cluster.local:9200")

qdrant = QdrantClient(url=QDRANT_URL, timeout=60)
os_client = OpenSearch(hosts=[OPENSEARCH_URL], verify_certs=False, ssl_show_warn=False)

def upsert_qdrant(points):
    qdrant.upsert(collection_name=QDRANT_COLLECTION, points=points)

def index_opensearch(documents):
    for d in documents:
        os_client.index(index="unified_docs", document=d)
