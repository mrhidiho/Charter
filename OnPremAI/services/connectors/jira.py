import os, requests, time, hashlib
from tqdm import tqdm
from common import upsert_qdrant, index_opensearch

JIRA_BASE = os.getenv("JIRA_BASE", "https://jira.intra.local")
JIRA_USER = os.getenv("JIRA_USER", "ro-svc")
JIRA_TOKEN = os.getenv("JIRA_TOKEN", "changeme")

def iter_issues(jql="project = ENG ORDER BY updated DESC", max_pages=5):
    start = 0
    for _ in range(max_pages):
        r = requests.get(f"{JIRA_BASE}/rest/api/2/search",
                         params={"jql": jql, "startAt": start, "maxResults": 50},
                         auth=(JIRA_USER, JIRA_TOKEN), timeout=30)
        r.raise_for_status()
        data = r.json()
        issues = data.get("issues", [])
        if not issues:
            break
        yield from issues
        start += len(issues)

def main():
    documents = []
    points = []
    for issue in tqdm(iter_issues(), desc="Jira"):
        key = issue["key"]
        fields = issue.get("fields", {})
        summary = fields.get("summary", "")
        desc = fields.get("description", "") or ""
        text = f"{summary}\n\n{desc}"
        doc = {"id": key, "source": f"jira:{key}", "text": text}
        documents.append(doc)
        # Dummy vector (actual embeddings created offline to keep this stub simple)
        vec = [0.0]*1024
        points.append({"id": int(hashlib.sha1(key.encode()).hexdigest()[:8],16), "vector": vec, "payload": doc})

    if documents:
        index_opensearch(documents)
    if points:
        upsert_qdrant(points)

if __name__ == "__main__":
    main()
