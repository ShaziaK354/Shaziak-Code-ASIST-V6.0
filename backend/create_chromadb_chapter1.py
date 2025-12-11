"""
SAMM ChromaDB Creator - Chapter 1 (Correct Collection Name)
"""

import re
import os
import sys
import json
from datetime import datetime

# =============================================================================
# YOUR PATHS
# =============================================================================

PDF_PATH = r"C:\Users\ShaziaKashif\ASIST Project\ASIST2.1\ASIST_V2.1\backend\Chapter 1 _ Defense Security Cooperation Agency.pdf"
CHAPTER = "1"
CHROMADB_PATH = r"C:\Users\ShaziaKashif\ASIST Project\ASIST2.1\ASIST_V2.1\backend\Chromadb\new_chromadb"
COLLECTION_NAME = "chapter_1"  # ✅ Correct name!

# =============================================================================
# IMPORTS
# =============================================================================

print("\n" + "="*60)
print("🚀 SAMM ChromaDB Creator - Chapter 1")
print("="*60)

print("\n🔄 Loading libraries...")

try:
    import fitz
    print("  ✅ PyMuPDF")
except:
    print("  ❌ PyMuPDF missing. Run: pip install pymupdf")
    sys.exit(1)

try:
    import chromadb
    print("  ✅ ChromaDB")
except:
    print("  ❌ ChromaDB missing. Run: pip install chromadb")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
    print("  ✅ SentenceTransformers")
    HAS_EMBEDDINGS = True
except:
    print("  ⚠️ SentenceTransformers missing (optional)")
    HAS_EMBEDDINGS = False

# =============================================================================
# ACRONYMS
# =============================================================================

ACRONYMS = {
    "SC": "Security Cooperation", "SA": "Security Assistance",
    "FMS": "Foreign Military Sales", "IMET": "International Military Education and Training",
    "DSCA": "Defense Security Cooperation Agency", "DoD": "Department of Defense",
    "DFAS": "Defense Finance and Accounting Service", "DCMA": "Defense Contract Management Agency",
    "DLA": "Defense Logistics Agency", "DTRA": "Defense Threat Reduction Agency",
    "MDA": "Missile Defense Agency", "NGA": "National Geospatial-Intelligence Agency",
    "NSA": "National Security Agency", "DA": "Department of the Army",
    "DoN": "Department of the Navy", "DAF": "Department of the Air Force",
    "USASAC": "U.S. Army Security Assistance Command", "NIPO": "Navy International Programs Office",
    "SAF/IA": "Deputy Under Secretary of the Air Force for International Affairs",
    "SECDEF": "Secretary of Defense", "USD(P)": "Under Secretary of Defense for Policy",
    "CJCS": "Chairman of the Joint Chiefs of Staff", "CCMD": "Combatant Command",
    "SCO": "Security Cooperation Organization", "IA": "Implementing Agency",
    "FAA": "Foreign Assistance Act", "AECA": "Arms Export Control Act",
    "NDAA": "National Defense Authorization Act", "EO": "Executive Order",
}

# =============================================================================
# FUNCTIONS
# =============================================================================

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def parse_sections(text, chapter):
    pattern = re.compile(r'(C' + chapter + r'(?:\.\d+)+\.?)\s*[-–.]?\s*([^\n]+)', re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections = []
    
    seen_ids = {}
    
    for i, match in enumerate(matches):
        section_id = match.group(1).rstrip('.')
        title = match.group(2).strip()
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        
        if len(content.split()) < 10:
            continue
        
        if section_id in seen_ids:
            seen_ids[section_id] += 1
            unique_id = f"{section_id}_v{seen_ids[section_id]}"
        else:
            seen_ids[section_id] = 1
            unique_id = section_id
        
        sections.append({
            'section_id': section_id,
            'unique_id': unique_id,
            'title': title,
            'content': content,
            'level': section_id.count('.'),
            'words': len(content.split()),
            'chars': len(content)
        })
    return sections

def get_acronyms(text):
    found = {}
    for acr, full in ACRONYMS.items():
        if re.search(r'\b' + re.escape(acr) + r'\b', text, re.IGNORECASE):
            found[acr] = full
    return found

def get_entities(text, acronyms):
    scores = {}
    for acr, full in acronyms.items():
        count = len(re.findall(r'\b' + re.escape(acr) + r'\b', text, re.IGNORECASE))
        if count > 0:
            scores[full] = count
    return [e[0] for e in sorted(scores.items(), key=lambda x: -x[1])[:5]]

def get_chunk_type(title):
    t = title.lower()
    if "definition" in t or "purpose" in t: return "definition"
    if "authorit" in t: return "authority"
    if "role" in t: return "role"
    if "responsibilit" in t: return "responsibility"
    if "department" in t or "agency" in t or "command" in t: return "organization"
    return "general"

def get_intent_type(title, content):
    t = (title + " " + content[:300]).lower()
    if any(x in t for x in ["definition", "comprises", "purpose"]): return "definition"
    if any(x in t for x in ["authority", "authorized", "delegated"]): return "authority"
    if any(x in t for x in ["agency", "department", "command"]): return "organization"
    if any(x in t for x in ["role", "responsibility"]): return "role"
    return "general"

def get_authorities(text):
    patterns = [r"DoDD?\s*\d+\.\d+", r"Executive Order\s+\d+", r"Title\s+\d+"]
    found = set()
    for p in patterns:
        found.update(re.findall(p, text, re.IGNORECASE))
    return list(found)

def build_hierarchy(section_id):
    parts = section_id.split('.')
    h = []
    curr = ""
    for p in parts:
        curr = curr + "." + p if curr else p
        h.append(curr)
    return h

def create_metadata(section, chapter):
    acronyms = get_acronyms(section['content'])
    entities = get_entities(section['content'], acronyms)
    
    return {
        "section_id": section['section_id'],
        "section_title": section['title'][:100],
        "section_hierarchy": json.dumps(build_hierarchy(section['section_id'])),
        "section_level": section['level'],
        "chunk_type": get_chunk_type(section['title']),
        "intent_type": get_intent_type(section['title'], section['content']),
        "primary_entities": json.dumps(entities),
        "acronyms": json.dumps(acronyms),
        "authorities_mentioned": json.dumps(get_authorities(section['content'])),
        "has_definition": bool(re.search(r'definition|comprises', section['content'], re.IGNORECASE)),
        "has_authority_citation": len(get_authorities(section['content'])) > 0,
        "completeness": "full_section",
        "chapter": chapter,
        "source": f"SAMM_Chapter_{chapter}",
        "word_count": section['words'],
        "character_count": section['chars'],
    }

# =============================================================================
# MAIN
# =============================================================================

print(f"\n📄 PDF: {PDF_PATH}")
print(f"💾 Output: {CHROMADB_PATH}")
print(f"📚 Collection: {COLLECTION_NAME}")

if not os.path.exists(PDF_PATH):
    print(f"\n❌ PDF not found: {PDF_PATH}")
    sys.exit(1)

print("\n🔄 Extracting PDF text...")
text = extract_text(PDF_PATH)
print(f"   ✅ {len(text):,} characters")

print("\n🔍 Parsing sections...")
sections = parse_sections(text, CHAPTER)
print(f"   ✅ {len(sections)} sections found")

print("\n✂️ Creating chunks...")
chunks = []
for sec in sections:
    chunk_id = f"samm_ch{CHAPTER}_{sec['unique_id'].replace('.', '_')}"
    metadata = create_metadata(sec, CHAPTER)
    chunks.append((chunk_id, sec['content'], metadata))

all_ids = [c[0] for c in chunks]
if len(all_ids) != len(set(all_ids)):
    seen = {}
    for i, chunk in enumerate(chunks):
        if chunk[0] in seen:
            new_id = f"{chunk[0]}_{i}"
            chunks[i] = (new_id, chunk[1], chunk[2])
        seen[chunk[0]] = True

print(f"   ✅ {len(chunks)} unique chunks created")

print("\n💾 Creating ChromaDB...")
os.makedirs(CHROMADB_PATH, exist_ok=True)

client = chromadb.PersistentClient(path=CHROMADB_PATH)

# Delete existing chapter_1 collection if exists
try:
    client.delete_collection(COLLECTION_NAME)
    print(f"   🗑️ Deleted old '{COLLECTION_NAME}' collection")
except:
    pass

# Also delete the wrong samm_all_chapters if exists
try:
    client.delete_collection("samm_all_chapters")
    print(f"   🗑️ Deleted old 'samm_all_chapters' collection")
except:
    pass

collection = client.create_collection(
    name=COLLECTION_NAME,
    metadata={"description": f"SAMM Chapter {CHAPTER} - Semantic Chunks"}
)

ids = [c[0] for c in chunks]
docs = [c[1] for c in chunks]
metas = [c[2] for c in chunks]

if HAS_EMBEDDINGS:
    print("\n🔄 Generating embeddings...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(docs, show_progress_bar=True).tolist()
    collection.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
else:
    collection.add(ids=ids, documents=docs, metadatas=metas)

print("\n🔍 Verifying...")
count = collection.count()
print(f"   ✅ {count} chunks in '{COLLECTION_NAME}'")

# Show all collections
all_collections = client.list_collections()
print(f"\n📚 All collections in this database:")
for coll in all_collections:
    c = client.get_collection(coll.name)
    print(f"   • {coll.name}: {c.count()} chunks")

print("\n🧪 Test: 'What is Security Cooperation?'")
results = collection.query(query_texts=["What is Security Cooperation?"], n_results=3)
for i, meta in enumerate(results['metadatas'][0]):
    print(f"   {i+1}. {meta['section_id']} - {meta['section_title'][:40]}...")

print("\n" + "="*60)
print("✅ SUCCESS!")
print("="*60)
print(f"\n📂 ChromaDB: {CHROMADB_PATH}")
print(f"📚 Collection: {COLLECTION_NAME} ({count} chunks)")
print(f"\n🔜 Next: Add chapter 4, 5, 6, 7, 9 similarly")
print(f"   Then combine all into 'samm_all_chapters'")
