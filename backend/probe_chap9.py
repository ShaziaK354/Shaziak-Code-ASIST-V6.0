# probe_vectors.py
# Safe, one-file probe for Chroma collections (Windows-friendly)
import sys
from collections import Counter
from pprint import pprint

try:
    import chromadb
except Exception as e:
    print("[ERR] chromadb not installed in this venv:", e)
    sys.exit(1)

# ====== CONFIG: update your DB path here ======
DB_PATH = r"C:\Users\ShaziaKashif\ASIST Project\ASIST2.1\ASIST_V2.1\backend\vector_db"
PRIMARY_COLLECTION = "samm_chapter9"     # <- probe this first
ALSO_CHECK_SAMM_ALL = True               # <- set False if you don't want to probe samm_all
SAMM_ALL_NAME = "samm_all"
# ==============================================

def open_collection(path: str, name: str):
    client = chromadb.PersistentClient(path=path)
    try:
        col = client.get_collection(name)
        return client, col
    except Exception as e:
        print(f"[ERR] Could not open collection '{name}' at '{path}': {e}")
        sys.exit(1)

def count_ids(col) -> int:
    try:
        got = col.get()
        return len(got.get("ids", []))
    except Exception as e:
        print("[ERR] count_ids:", e)
        return 0

def embedding_dim(col) -> int | None:
    try:
        info = col.get(limit=1, include=["embeddings"])
        embs = info.get("embeddings") or []
        if len(embs) == 0 or embs[0] is None:
            return None
        # embs[0] may be list or numpy array; len() works for both
        return len(embs[0])
    except Exception as e:
        print("[WARN] embedding_dim:", e)
        return None

def meta_keys(col, sample_n=20):
    try:
        info = col.get(limit=sample_n, include=["metadatas"])
        metas = info.get("metadatas") or []
        keys = set()
        for m in metas:
            if isinstance(m, dict):
                keys.update(m.keys())
        return sorted(keys)
    except Exception as e:
        print("[WARN] meta_keys:", e)
        return []

def print_samples(col, n=5):
    try:
        info = col.get(limit=n, include=["metadatas", "documents"])
        mets = info.get("metadatas") or []
        docs = info.get("documents") or []
        for i, (m, d) in enumerate(zip(mets, docs), start=1):
            m = m or {}
            chap = m.get("chapter") or m.get("chapter_number")
            sec  = m.get("section_id") or m.get("section")
            title = m.get("title")
            prev = (d or "")[:200].replace("\n"," ")
            print(f"\n--- Sample {i} ---")
            print("chapter:", chap, "| section_id:", sec)
            if title:
                print("title  :", title)
            print("preview:", prev)
    except Exception as e:
        print("[WARN] print_samples:", e)

def query_smoketest(col, text="What is billing in FMS?", k=5):
    try:
        res = col.query(query_texts=[text], n_results=k)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        if not metas:
            print("[Query] No results.")
            return
        print(f"[Query] Top {len(metas)} results for: {text!r}")
        for m, d in zip(metas, docs):
            chap = (m or {}).get("chapter") or (m or {}).get("chapter_number")
            sec  = (m or {}).get("section_id") or (m or {}).get("section")
            print(" -", chap, sec)
    except Exception as e:
        print("[WARN] query_smoketest:", e)

def count_by_chapter(col, page=1000):
    cnt = Counter()
    offset = 0
    while True:
        try:
            got = col.get(limit=page, offset=offset, include=["metadatas"])
        except Exception as e:
            print("[WARN] count_by_chapter page fetch:", e)
            break
        metas = got.get("metadatas") or []
        if not metas:
            break
        for m in metas:
            ch = (m or {}).get("chapter") or (m or {}).get("chapter_number")
            if ch:
                cnt[ch] += 1
        offset += len(metas)
    return dict(cnt)

def main():
    print("\n=== PROBING COLLECTION:", PRIMARY_COLLECTION, "===")
    client, col = open_collection(DB_PATH, PRIMARY_COLLECTION)

    total = count_ids(col)
    dim = embedding_dim(col)
    print(f"[OK] {PRIMARY_COLLECTION} -> count={total}, dim={dim}")

    keys = meta_keys(col)
    print("[META KEYS]", keys)

    print_samples(col, n=5)
    query_smoketest(col, "What is billing in FMS?", k=5)

    if ALSO_CHECK_SAMM_ALL:
        print("\n=== OPTIONAL: PROBING samm_all ===")
        _, allc = open_collection(DB_PATH, SAMM_ALL_NAME)
        totals = count_by_chapter(allc)
        print("[samm_all] Chapter counts:", totals)

        # Quick peek of C9 from samm_all
        try:
            got = allc.get(where={"chapter": {"$eq": "C9"}}, limit=3, include=["metadatas","documents"])
            mets = got.get("metadatas") or []
            docs = got.get("documents") or []
            print("\n[samm_all] C9 sample:")
            for m, d in zip(mets, docs):
                ch = (m or {}).get("chapter")
                sec = (m or {}).get("section_id") or (m or {}).get("section")
                prev = (d or "")[:160].replace("\n"," ")
                print("-", ch, sec, "|", prev)
        except Exception as e:
            print("[WARN] samm_all C9 peek:", e)

if __name__ == "__main__":
    main()
