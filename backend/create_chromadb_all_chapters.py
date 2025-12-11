"""
SAMM ChromaDB Creator - All Remaining Chapters (4, 5, 6, 7, 9)
"""

import re
import os
import sys
import json
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_PATH = r"C:\Users\ShaziaKashif\ASIST Project\ASIST2.1\ASIST_V2.1\backend"
CHROMADB_PATH = r"C:\Users\ShaziaKashif\ASIST Project\ASIST2.1\ASIST_V2.1\backend\Chromadb\new_chromadb"

# All chapters to process
CHAPTERS = [
    {"file": "Chapter 4 _ Defense Security Cooperation Agency.pdf", "chapter": "4"},
    {"file": "Chapter 5 _ Defense Security Cooperation Agency.pdf", "chapter": "5"},
    {"file": "Chapter 6 _ Defense Security Cooperation Agency.pdf", "chapter": "6"},
    {"file": "Chapter 7 _ Defense Security Cooperation Agency.pdf", "chapter": "7"},
    {"file": "Chapter 9 _ Defense Security Cooperation Agency.pdf", "chapter": "9"},
]

# =============================================================================
# IMPORTS
# =============================================================================

print("\n" + "="*60)
print("🚀 SAMM ChromaDB Creator - Chapters 4, 5, 6, 7, 9")
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
    model = SentenceTransformer("all-MiniLM-L6-v2")
except:
    print("  ⚠️ SentenceTransformers missing")
    HAS_EMBEDDINGS = False
    model = None

# =============================================================================
# ACRONYMS
# =============================================================================

ACRONYMS = {
    "SC": "Security Cooperation", "SA": "Security Assistance",
    "FMS": "Foreign Military Sales", "IMET": "International Military Education and Training",
    "EDA": "Excess Defense Articles", "BPC": "Building Partner Capacity",
    "LOA": "Letter of Offer and Acceptance", "LOR": "Letter of Request",
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
    "FMF": "Foreign Military Financing", "MAP": "Military Assistance Program",
    "FMSO": "Foreign Military Sales Order", "SDR": "Supply Discrepancy Report",
    "P&A": "Packing and Handling", "ILCO": "International Logistics Control Office",
    "CAS": "Contract Administration Services", "CLSSA": "Cooperative Logistics Supply Support Arrangement",
    "SCIP": "Security Cooperation Information Portal", "MISIL": "Management Information System for International Logistics",
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
        
        # Skip very short sections
        if len(content.split()) < 10:
            continue
        
        # Handle duplicates
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
    if "price" in t or "cost" in t or "fee" in t: return "pricing"
    if "process" in t or "procedure" in t: return "process"
    return "general"

def get_intent_type(title, content):
    t = (title + " " + content[:300]).lower()
    if any(x in t for x in ["definition", "comprises", "purpose"]): return "definition"
    if any(x in t for x in ["authority", "authorized", "delegated"]): return "authority"
    if any(x in t for x in ["agency", "department", "command"]): return "organization"
    if any(x in t for x in ["role", "responsibility"]): return "role"
    if any(x in t for x in ["price", "cost", "fee", "charge"]): return "pricing"
    if any(x in t for x in ["process", "procedure", "step"]): return "process"
    return "general"

def get_authorities(text):
    patterns = [r"DoDD?\s*\d+\.\d+", r"Executive Order\s+\d+", r"Title\s+\d+", 
                r"\d+\s+U\.S\.C\.\s+\d+", r"FAA,?\s+section\s+\d+"]
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

def process_chapter(pdf_path, chapter, client):
    """Process a single chapter and create its collection"""
    
    collection_name = f"chapter_{chapter}"
    print(f"\n{'─'*60}")
    print(f"📖 Processing Chapter {chapter}")
    print(f"{'─'*60}")
    print(f"   PDF: {os.path.basename(pdf_path)}")
    
    if not os.path.exists(pdf_path):
        print(f"   ❌ PDF not found!")
        return 0
    
    # Extract text
    text = extract_text(pdf_path)
    print(f"   📝 {len(text):,} characters")
    
    # Parse sections
    sections = parse_sections(text, chapter)
    print(f"   📑 {len(sections)} sections")
    
    # Create chunks
    chunks = []
    for sec in sections:
        chunk_id = f"samm_ch{chapter}_{sec['unique_id'].replace('.', '_')}"
        metadata = create_metadata(sec, chapter)
        chunks.append((chunk_id, sec['content'], metadata))
    
    # Ensure unique IDs
    all_ids = [c[0] for c in chunks]
    if len(all_ids) != len(set(all_ids)):
        seen = {}
        for i, chunk in enumerate(chunks):
            if chunk[0] in seen:
                chunks[i] = (f"{chunk[0]}_{i}", chunk[1], chunk[2])
            seen[chunk[0]] = True
    
    print(f"   ✂️ {len(chunks)} chunks")
    
    # Delete existing collection
    try:
        client.delete_collection(collection_name)
    except:
        pass
    
    # Create collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": f"SAMM Chapter {chapter}"}
    )
    
    # Prepare data
    ids = [c[0] for c in chunks]
    docs = [c[1] for c in chunks]
    metas = [c[2] for c in chunks]
    
    # Add with embeddings
    if HAS_EMBEDDINGS and model:
        embeddings = model.encode(docs, show_progress_bar=False).tolist()
        collection.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
    else:
        collection.add(ids=ids, documents=docs, metadatas=metas)
    
    print(f"   ✅ Saved to '{collection_name}': {collection.count()} chunks")
    
    return collection.count()

# =============================================================================
# MAIN
# =============================================================================

print(f"\n📂 Base path: {BASE_PATH}")
print(f"💾 ChromaDB: {CHROMADB_PATH}")

# Initialize ChromaDB
client = chromadb.PersistentClient(path=CHROMADB_PATH)

# Process each chapter
total_chunks = 0
results = []

for ch in CHAPTERS:
    pdf_path = os.path.join(BASE_PATH, ch["file"])
    count = process_chapter(pdf_path, ch["chapter"], client)
    total_chunks += count
    results.append({"chapter": ch["chapter"], "chunks": count})

# Summary
print("\n" + "="*60)
print("📊 SUMMARY")
print("="*60)

# Show all collections
all_collections = client.list_collections()
print(f"\n📚 All collections in database:")
grand_total = 0
for coll in all_collections:
    c = client.get_collection(coll.name)
    count = c.count()
    grand_total += count
    print(f"   • {coll.name}: {count} chunks")

print(f"\n   TOTAL: {grand_total} chunks")

print("\n" + "="*60)
print("✅ ALL CHAPTERS PROCESSED!")
print("="*60)
print(f"\n🔜 Next step: Combine all into 'samm_all_chapters'")
