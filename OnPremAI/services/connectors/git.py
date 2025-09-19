import os, subprocess, tempfile, hashlib, pathlib
from tqdm import tqdm
from common import upsert_qdrant, index_opensearch

REPOS = os.getenv("GIT_REPOS", "").split(",")  # comma-separated https://internal/scm/repo.git (read-only)
BRANCH = os.getenv("GIT_BRANCH", "main")

def collect(repo_url):
    with tempfile.TemporaryDirectory() as d:
        subprocess.check_call(["git", "clone", "--depth", "1", "--branch", BRANCH, repo_url, d])
        root = pathlib.Path(d)
        for p in root.rglob("*"):
            if p.is_file() and p.stat().st_size < 2_000_000:
                try:
                    text = p.read_text(errors="ignore")
                except Exception:
                    continue
                rel = p.relative_to(root).as_posix()
                yield {"id": f"{repo_url}::{rel}", "source": f"git:{repo_url}#{BRANCH}:{rel}", "text": text}

def main():
    docs, points = [], []
    for repo in filter(None, REPOS):
        for doc in tqdm(collect(repo), desc=f"repo:{repo}"):
            docs.append(doc)
            pid = int(hashlib.sha1(doc["id"].encode()).hexdigest()[:8],16)
            points.append({"id": pid, "vector":[0.0]*1024, "payload": doc})
    if docs: index_opensearch(docs)
    if points: upsert_qdrant(points)

if __name__ == "__main__":
    main()
