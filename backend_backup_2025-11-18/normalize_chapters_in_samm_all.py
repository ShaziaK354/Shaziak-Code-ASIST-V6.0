import re
import chromadb

DB_PATH = r"C:\Users\ShaziaKashif\ASIST Project\ASIST2.1\ASIST_V2.1\backend\vector_db"
COL_NAME = "samm_all"

client = chromadb.PersistentClient(path=DB_PATH)
col = client.get_collection(COL_NAME)

def derive_chapter(meta):
    # if already "C#" keep it
    ch = (meta or {}).get("chapter")
    if isinstance(ch, str) and re.fullmatch(r"C\d+", ch):
        return ch
    # if numeric like "1" -> "C1"
    if isinstance(ch, str) and ch.isdigit():
        return f"C{ch}"
    # else try from section_id like "C6.2.4"
    sid = (meta or {}).get("section_id") or (meta or {}).get("section") or ""
    m = re.match(r"(C\d+)\.", str(sid))
    if m:
        return m.group(1)
    return ch  # leave as-is

updated, offset = 0, 0
BATCH = 1000

while True:
    got = col.get(limit=BATCH, offset=offset, include=["metadatas"])
    ids = got.get("ids") or []
    metas = got.get("metadatas") or []
    if len(ids) == 0:
        break

    upd_ids, upd_metas = [], []
    for _id, m in zip(ids, metas):
        m = dict(m or {})
        new_ch = derive_chapter(m)
        if new_ch and new_ch != m.get("chapter"):
            m["chapter"] = new_ch
            upd_ids.append(_id)
            upd_metas.append(m)

    if upd_ids:
        col.update(ids=upd_ids, metadatas=upd_metas)
        updated += len(upd_ids)

    offset += len(ids)

print(f"[DONE] Updated chapter field on {updated} items")

# Verify counts
from collections import Counter
cnt, offset = Counter(), 0
while True:
    got = col.get(limit=BATCH, offset=offset, include=["metadatas"])
    metas = got.get("metadatas") or []
    if not metas:
        break
    for m in metas:
        ch = (m or {}).get("chapter")
        if ch:
            cnt[ch] += 1
    offset += len(metas)

print("Chapter counts (normalized):", dict(cnt))
