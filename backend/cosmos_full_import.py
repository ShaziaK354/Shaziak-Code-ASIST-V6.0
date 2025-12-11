"""
Full Cosmos DB Import to KG with Duplicate Checking
====================================================
- Imports ALL edges (relationships)
- Imports useful vertices (skips sections, dates, codes)
- Checks duplicates against existing KG
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from gremlin_python.driver import client, serializer
    GREMLIN_AVAILABLE = True
except ImportError:
    GREMLIN_AVAILABLE = False

# Config
COSMOS_GREMLIN_CONFIG = {
    'endpoint': os.getenv("COSMOS_GREMLIN_ENDPOINT", "asist-graph-db.gremlin.cosmos.azure.com"),
    'database': os.getenv("COSMOS_GREMLIN_DATABASE", "ASIST-Agent-1.1DB"),
    'graph': os.getenv("COSMOS_GREMLIN_COLLECTION", "AGENT1.4"),
    'password': os.getenv("COSMOS_GREMLIN_KEY", "")
}

KG_PATH = "samm_knowledge_graph.json"

# NO LABELS SKIPPED - Import EVERYTHING from Cosmos DB
# Sab kuch useful hai - mehnat se dala tha!
SKIP_VERTEX_LABELS = []  # Empty - skip nothing!


def normalize_id(raw_id: str) -> str:
    """Normalize entity ID for comparison."""
    if not raw_id:
        return ""
    # Remove special chars, uppercase, replace spaces/dashes with underscore
    normalized = str(raw_id).upper()
    normalized = normalized.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
    normalized = ''.join(c for c in normalized if c.isalnum() or c == '_')
    return normalized


def normalize_rel_type(rel_type: str) -> str:
    """Normalize relationship type."""
    if not rel_type:
        return "related_to"
    return rel_type.lower().replace(' ', '_').replace('-', '_')


def get_cosmos_client():
    """Connect to Cosmos DB."""
    endpoint = COSMOS_GREMLIN_CONFIG['endpoint'].replace('wss://', '').replace(':443/', '').replace(':443', '')
    username = f"/dbs/{COSMOS_GREMLIN_CONFIG['database']}/colls/{COSMOS_GREMLIN_CONFIG['graph']}"
    endpoint_url = f"wss://{endpoint}:443/gremlin"
    
    return client.Client(
        endpoint_url, 'g',
        username=username,
        password=COSMOS_GREMLIN_CONFIG['password'],
        message_serializer=serializer.GraphSONSerializersV2d0()
    )


def query(c, q):
    """Execute Gremlin query."""
    try:
        return c.submit(q).all().result()
    except Exception as e:
        print(f"Query error: {e}")
        return []


def load_existing_kg(kg_path: str) -> Tuple[Dict, Set[str], Set[Tuple]]:
    """Load existing KG and extract IDs for duplicate checking."""
    kg_data = {'metadata': {}, 'entities': {}, 'relationships': []}
    existing_entity_ids = set()
    existing_rel_keys = set()
    
    path = Path(kg_path)
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            kg_data = json.load(f)
        
        # Get existing entity IDs (normalized)
        for cat, entities in kg_data.get('entities', {}).items():
            if isinstance(entities, dict):
                for eid in entities.keys():
                    existing_entity_ids.add(normalize_id(eid))
        
        # Get existing relationship keys (source, target, type) - normalized
        for rel in kg_data.get('relationships', []):
            key = (
                normalize_id(rel['source']),
                normalize_id(rel['target']),
                normalize_rel_type(rel['type'])
            )
            existing_rel_keys.add(key)
    
    return kg_data, existing_entity_ids, existing_rel_keys


def main():
    result = {
        "success": False,
        "timestamp": datetime.now().isoformat(),
        "cosmos_config": {
            "endpoint": COSMOS_GREMLIN_CONFIG['endpoint'],
            "database": COSMOS_GREMLIN_CONFIG['database'],
            "graph": COSMOS_GREMLIN_CONFIG['graph']
        },
        "stats": {
            "cosmos_vertices": 0,
            "cosmos_edges": 0,
            "entities_added": 0,
            "entities_skipped_duplicate": 0,
            "entities_skipped_label": 0,
            "relationships_added": 0,
            "relationships_skipped_duplicate": 0,
            "kg_total_entities": 0,
            "kg_total_relationships": 0
        },
        "added_entities": [],
        "added_relationships": [],
        "errors": []
    }
    
    if not GREMLIN_AVAILABLE:
        result["errors"].append("gremlin_python not installed")
        print(json.dumps(result, indent=2))
        return
    
    if not COSMOS_GREMLIN_CONFIG['password']:
        result["errors"].append("COSMOS_GREMLIN_KEY not set")
        print(json.dumps(result, indent=2))
        return
    
    # Connect to Cosmos
    try:
        c = get_cosmos_client()
        test = query(c, "g.V().limit(1).count()")
        if not test:
            result["errors"].append("Failed to connect to Cosmos DB")
            print(json.dumps(result, indent=2))
            return
    except Exception as e:
        result["errors"].append(f"Connection error: {str(e)}")
        print(json.dumps(result, indent=2))
        return
    
    # Load existing KG
    kg_data, existing_entity_ids, existing_rel_keys = load_existing_kg(KG_PATH)
    
    print(f"Existing KG: {len(existing_entity_ids)} entities, {len(existing_rel_keys)} relationships", file=__import__('sys').stderr)
    
    # =========================================================================
    # STEP 1: Get ALL vertices from Cosmos (Cosmos DB compatible query)
    # =========================================================================
    print("Fetching vertices...", file=__import__('sys').stderr)
    
    # Cosmos DB doesn't support by(unfold()) - use simpler query
    vertices = query(c, "g.V().valueMap(true)")
    result["stats"]["cosmos_vertices"] = len(vertices)
    
    # Create cosmos_imported category if not exists
    if 'cosmos_imported' not in kg_data['entities']:
        kg_data['entities']['cosmos_imported'] = {}
    
    # Process vertices
    for v in vertices:
        # Cosmos DB returns properties as lists, extract first value
        def get_prop(obj, key, default=''):
            val = obj.get(key, default)
            if isinstance(val, list) and len(val) > 0:
                return val[0]
            return val if val else default
        
        v_label = get_prop(v, 'label', 'entity')
        
        # Skip unwanted labels (empty list = skip nothing)
        if v_label in SKIP_VERTEX_LABELS:
            result["stats"]["entities_skipped_label"] += 1
            continue
        
        # Get ID and name
        v_id = get_prop(v, 'id', '')
        v_name = get_prop(v, 'name', get_prop(v, 'label', v_id))
        
        # Normalize ID for comparison
        normalized_id = normalize_id(v_id)
        
        # Also check by name
        normalized_name = normalize_id(v_name) if v_name else ""
        
        # Skip if duplicate
        if normalized_id in existing_entity_ids or normalized_name in existing_entity_ids:
            result["stats"]["entities_skipped_duplicate"] += 1
            continue
        
        # Create entity
        description = get_prop(v, 'description', get_prop(v, 'definition', ''))
        entity = {
            'id': normalized_id if normalized_id else normalized_name,
            'label': v_name,
            'type': v_label,
            'definition': description[:500] if description else '',
            'cosmos_original_id': v_id,
            'source': 'cosmos_db'
        }
        
        # Add to KG
        entity_key = entity['id']
        if entity_key and entity_key not in kg_data['entities']['cosmos_imported']:
            kg_data['entities']['cosmos_imported'][entity_key] = entity
            existing_entity_ids.add(entity_key)
            result["stats"]["entities_added"] += 1
            
            if result["stats"]["entities_added"] <= 50:
                result["added_entities"].append(f"{entity_key} ({v_label})")
    
    # =========================================================================
    # STEP 2: Get ALL edges from Cosmos
    # =========================================================================
    print("Fetching edges...", file=__import__('sys').stderr)
    
    edges_query = """
    g.E().project('id', 'label', 'source', 'source_name', 'target', 'target_name')
        .by(id)
        .by(label)
        .by(outV().id())
        .by(outV().values('name').fold())
        .by(inV().id())
        .by(inV().values('name').fold())
    """
    edges = query(c, edges_query)
    result["stats"]["cosmos_edges"] = len(edges)
    
    # Get max relationship ID
    max_rel_id = 0
    for rel in kg_data.get('relationships', []):
        rel_id = rel.get('id', 'rel_0')
        if rel_id.startswith('rel_'):
            try:
                num = int(rel_id.split('_')[1])
                max_rel_id = max(max_rel_id, num)
            except:
                pass
    
    # Process edges
    for e in edges:
        source_id = e.get('source', '')
        target_id = e.get('target', '')
        rel_type = e.get('label', 'related_to')
        
        # Get names for better readability
        source_names = e.get('source_name', [])
        target_names = e.get('target_name', [])
        source_name = source_names[0] if source_names else source_id
        target_name = target_names[0] if target_names else target_id
        
        # Normalize
        norm_source = normalize_id(source_name) if source_name else normalize_id(source_id)
        norm_target = normalize_id(target_name) if target_name else normalize_id(target_id)
        norm_type = normalize_rel_type(rel_type)
        
        # Skip if no valid source/target
        if not norm_source or not norm_target:
            continue
        
        # Check duplicate
        key = (norm_source, norm_target, norm_type)
        if key in existing_rel_keys:
            result["stats"]["relationships_skipped_duplicate"] += 1
            continue
        
        # Create relationship
        max_rel_id += 1
        rel = {
            'id': f'rel_{max_rel_id:04d}',
            'source': norm_source,
            'target': norm_target,
            'type': norm_type,
            'description': f'{source_name} {rel_type} {target_name}',
            'source_db': 'cosmos_db',
            'weight': 8
        }
        
        kg_data['relationships'].append(rel)
        existing_rel_keys.add(key)
        result["stats"]["relationships_added"] += 1
        
        if result["stats"]["relationships_added"] <= 100:
            result["added_relationships"].append(f"{norm_source} --[{norm_type}]--> {norm_target}")
    
    # Close connection
    c.close()
    
    # =========================================================================
    # STEP 3: Save updated KG
    # =========================================================================
    kg_data['metadata'] = kg_data.get('metadata', {})
    kg_data['metadata']['last_updated'] = datetime.now().isoformat()
    kg_data['metadata']['cosmos_full_import'] = datetime.now().isoformat()
    kg_data['metadata']['cosmos_source'] = f"{COSMOS_GREMLIN_CONFIG['database']}/{COSMOS_GREMLIN_CONFIG['graph']}"
    
    with open(KG_PATH, 'w', encoding='utf-8') as f:
        json.dump(kg_data, f, indent=2, ensure_ascii=False)
    
    # Calculate final totals
    total_entities = sum(len(v) for v in kg_data['entities'].values() if isinstance(v, dict))
    result["stats"]["kg_total_entities"] = total_entities
    result["stats"]["kg_total_relationships"] = len(kg_data['relationships'])
    result["kg_path"] = KG_PATH
    result["success"] = True
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

