# merge_c7_c9_into_samm_all.py  -- FINAL (numpy-safe, no 'ids' in include)
import re, uuid
import chromadb

DB_PATH = r"C:\Users\ShaziaKashif\ASIST Project\ASIST2.1\ASIST_V2.1\backend\vector_db"

SRC_C7 = "samm_chapter7"
SRC_C9 = "samm_chapter9"
TMP_MERGED = "samm_c7_c9_merged"
TARGET_ALL = "samm_all"

def open_col(client, name):
    try:
        return client.get_collection(name)
    except Exception:
        return client.create_collection(name)

def first_dim(col):
    g = col.get(limit=1, include=["embeddings"])
    embs = g.get("embeddings")
    if embs is None or len(embs) == 0 or embs[0] is None:
        return None
    return len(embs[0])

def chapter_from_meta(m):
    ch = (m or {}).get("chapter")
    if isinstance(ch, str) and re.fullmatch(r"C\d+", ch):
        return ch
    sid = (m or {}).get("section_id") or (m or {}).get("section") or ""
    m1 = re.match(r"(C\d+)\.", str(sid))
    if m1: return m1.group(1)
    if isinstance(ch, str) and ch.isdigit():
        return f"C{ch}"
    return None

def normalize_meta(m):
    m = dict(m or {})
    if "entity_section_refs" in m and "entity_section_references" not in m:
        m["entity_section_references"] = m.pop("entity_section_refs")
    ch = chapter_from_meta(m)
    if ch: m["chapter"] = ch
    for k, v in list(m.items()):
        if v is None: 
            continue
        if not isinstance(v, (str, int, float, bool)):
            m[k] = str(v)
    return m

def copy_all(src, dst, prefix, base_dim=None):
    # validate dim first
    d = first_dim(src)
    if d is None:
        print(f"[WARN] {src.name} has no embeddings; skipping.")
        return base_dim, 0
    if base_dim is None:
        base_dim = d
        print(f"[INFO] embedding dim set: {base_dim}")
    elif d != base_dim:
        raise RuntimeError(f"Dim mismatch: {src.name}={d}, base={base_dim}")

    added, off = 0, 0
    while True:
        # IMPORTANT: never use "or []" on arrays
        got = src.get(limit=1000, offset=off, include=["documents", "embeddings", "metadatas"])

        ids   = got.get("ids")
        docs  = got.get("documents")
        embs  = got.get("embeddings")
        metas = got.get("metadatas")

        # normalize Nones (no boolean checks on arrays)
        if ids   is None: ids   = []
        if docs  is None: docs  = []
        if embs  is None: embs  = []
        if metas is None: metas = []

        if len(ids) == 0:
            break

        new_ids, new_docs, new_embs, new_metas = [], [], [], []
        for _id, doc, emb, meta in zip(ids, docs, embs, metas):
            if emb is None:
                continue
            nid = f"{prefix}:{_id}" if _id else f"{prefix}:auto-{uuid.uuid4().hex}"
            new_ids.append(nid)
            new_docs.append("" if doc is None else str(doc))
            new_embs.append(emb)
            # your normalize_meta() already defined above
            new_metas.append(normalize_meta(meta))

        if len(new_ids) > 0:
            dst.add(ids=new_ids, documents=new_docs, embeddings=new_embs, metadatas=new_metas)
            added += len(new_ids)

        off += len(ids)

    return base_dim, added

def main():
    client = chromadb.PersistentClient(path=DB_PATH)

    # sources
    c7 = open_col(client, SRC_C7)
    c9 = open_col(client, SRC_C9)
    print("C7 count:", len(c7.get().get("ids", [])))
    print("C9 count:", len(c9.get().get("ids", [])))

    # temp merged (clear)
    tmp = open_col(client, TMP_MERGED)
    existing = tmp.get().get("ids", [])
    if existing:
        tmp.delete(ids=existing)

    # copy both into temp
    base_dim, total = None, 0
    base_dim, a = copy_all(c7, tmp, "c7", base_dim)
    total += a
    base_dim, b = copy_all(c9, tmp, "c9", base_dim)
    total += b
    print(f"[TMP] merged added: {total} (C7={a}, C9={b})")

    # target samm_all — remove old C7/C9
    allc = open_col(client, TARGET_ALL)
    to_delete, off = [], 0
    while True:
        got = allc.get(limit=1000, offset=off, include=["metadatas"])
        ids   = got.get("ids") or []
        metas = got.get("metadatas") or []
        if len(ids) == 0:
            break
        for _id, m in zip(ids, metas):
            m = m or {}
            ch  = m.get("chapter")
            sid = m.get("section_id") or m.get("section") or ""
            if ch in ("C7","C9") or (isinstance(sid, str) and (sid.startswith("C7.") or sid.startswith("C9."))):
                to_delete.append(_id)
        off += len(ids)

    if to_delete:
        for i in range(0, len(to_delete), 1000):
            allc.delete(ids=to_delete[i:i+1000])
        print(f"[CLEAN] removed old from samm_all: {len(to_delete)}")
    else:
        print("[CLEAN] no existing C7/C9 found in samm_all")

    # copy temp → samm_all
    # copy temp → samm_all (safe for numpy arrays)
    added_all, off = 0, 0
    while True:
        got = tmp.get(limit=1000, offset=off, include=["documents", "embeddings", "metadatas"])
        ids   = got.get("ids")
        docs  = got.get("documents")
        embs  = got.get("embeddings")
        metas = got.get("metadatas")

        if ids   is None: ids   = []
        if docs  is None: docs  = []
        if embs  is None: embs  = []
        if metas is None: metas = []

        if len(ids) == 0:
            break

        allc.add(
            ids=ids,
            documents=[str(d) if d is not None else "" for d in docs],
            embeddings=embs,
            metadatas=[normalize_meta(m) for m in metas],
        )
        added_all += len(ids)
        off += len(ids)

    print(f"[RESULT] inserted into samm_all (C7+C9): {added_all}")

    # counts
    from collections import Counter
    cnt, off = Counter(), 0
    while True:
        got = allc.get(limit=1000, offset=off, include=["metadatas"])
        metas = got.get("metadatas") or []
        if len(metas) == 0:
            break
        for m in metas:
            ch = (m or {}).get("chapter")
            if ch:
                cnt[ch] += 1
        off += len(metas)
    print("Chapter counts (samm_all):", dict(cnt))

if __name__ == "__main__":
    main()
