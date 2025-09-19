import os, requests, hashlib
from tqdm import tqdm
from common import upsert_qdrant, index_opensearch

BASE = os.getenv("CONFLUENCE_BASE","https://confluence.intra.local")
USER = os.getenv("CONFLUENCE_USER","ro-svc")
TOKEN = os.getenv("CONFLUENCE_TOKEN","changeme")

def pages(space_key="ENG", limit=100):
    start = 0
    while True:
        r = requests.get(f"{BASE}/rest/api/content",
                         params={"spaceKey": space_key, "limit": 50, "start": start, "expand":"body.storage"},
                         auth=(USER,TOKEN), timeout=30)
        r.raise_for_status()
        data = r.json()
        results = data.get("results",[])
        if not results: break
        for pg in results:
            body = pg.get("body",{}).get("storage",{}).get("value","")
            yield {"id": pg["id"], "title": pg.get("title",""), "text": body}
        start += len(results)

def main():
    docs, points = [], []
    for p in tqdm(pages(), desc="Confluence"):
        text = f"{p['title']}\n\n{p['text']}"
        doc = {"id": p["id"], "source": f"confluence:{p['id']}", "text": text}
        docs.append(doc)
        pid = int(hashlib.sha1(p["id"].encode()).hexdigest()[:8],16)
        points.append({"id": pid, "vector":[0.0]*1024, "payload": doc})
    if docs: index_opensearch(docs)
    if points: upsert_qdrant(points)

if __name__ == "__main__":
    main()
