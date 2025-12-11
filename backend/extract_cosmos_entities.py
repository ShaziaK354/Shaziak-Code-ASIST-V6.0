"""
Extract Entities & Relationships from YOUR Cosmos DB
====================================================
Configured for: asist-graph-db / ASIST-Agent-1.1DB / AGENT1.4

All outputs are in JSON format!
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

# Load .env file automatically
try:
    from dotenv import load_dotenv
    load_dotenv()  # Loads from .env file in current directory
    DOTENV_LOADED = True
except ImportError:
    DOTENV_LOADED = False

# Try importing gremlin
try:
    from gremlin_python.driver import client, serializer
    from gremlin_python.driver.protocol import GremlinServerError
    GREMLIN_AVAILABLE = True
except ImportError:
    GREMLIN_AVAILABLE = False

# =============================================================================
# YOUR COSMOS DB CONFIG
# =============================================================================

COSMOS_GREMLIN_CONFIG = {
    'endpoint': os.getenv("COSMOS_GREMLIN_ENDPOINT", "asist-graph-db.gremlin.cosmos.azure.com"),
    'database': os.getenv("COSMOS_GREMLIN_DATABASE", "ASIST-Agent-1.1DB"),
    'graph': os.getenv("COSMOS_GREMLIN_COLLECTION", "AGENT1.4"),
    'password': os.getenv("COSMOS_GREMLIN_KEY", "")
}

KG_PATH = "samm_knowledge_graph.json"
OUTPUT_DIR = "cosmos_outputs"


class CosmosGremlinExtractor:
    """Extract data from your Cosmos DB Gremlin."""
    
    def __init__(self):
        self.client = None
        self.connected = False
        
    def connect(self) -> dict:
        """Connect to Cosmos Gremlin. Returns JSON status."""
        result = {
            "success": False,
            "endpoint": COSMOS_GREMLIN_CONFIG['endpoint'],
            "database": COSMOS_GREMLIN_CONFIG['database'],
            "graph": COSMOS_GREMLIN_CONFIG['graph'],
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        if not GREMLIN_AVAILABLE:
            result["message"] = "gremlin_python not installed. Run: pip install gremlinpython --break-system-packages"
            return result
            
        endpoint = COSMOS_GREMLIN_CONFIG['endpoint'].replace('wss://', '').replace(':443/', '').replace(':443', '')
        
        if not COSMOS_GREMLIN_CONFIG['password']:
            result["message"] = "COSMOS_GREMLIN_KEY not set! Run: export COSMOS_GREMLIN_KEY='your-key'"
            return result
        
        try:
            username = f"/dbs/{COSMOS_GREMLIN_CONFIG['database']}/colls/{COSMOS_GREMLIN_CONFIG['graph']}"
            endpoint_url = f"wss://{endpoint}:443/gremlin"
            
            self.client = client.Client(
                endpoint_url,
                'g',
                username=username,
                password=COSMOS_GREMLIN_CONFIG['password'],
                message_serializer=serializer.GraphSONSerializersV2d0()
            )
            
            # Test connection
            test_result = self.client.submit("g.V().limit(1).count()").all().result()
            self.connected = True
            result["success"] = True
            result["message"] = f"Connected successfully. Test query returned: {test_result}"
            
        except Exception as e:
            result["message"] = f"Connection failed: {str(e)}"
            
        return result
    
    def close(self):
        if self.client:
            self.client.close()
    
    def query(self, gremlin_query: str) -> List:
        """Execute a Gremlin query."""
        if not self.connected:
            return []
        try:
            return self.client.submit(gremlin_query).all().result()
        except GremlinServerError as e:
            return []
    
    def get_summary(self) -> dict:
        """Get Cosmos DB summary as JSON."""
        result = {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "endpoint": COSMOS_GREMLIN_CONFIG['endpoint'],
                "database": COSMOS_GREMLIN_CONFIG['database'],
                "graph": COSMOS_GREMLIN_CONFIG['graph']
            },
            "counts": {},
            "vertex_labels": [],
            "edge_labels": [],
            "sample_vertices": []
        }
        
        if not self.connected:
            result["error"] = "Not connected to Cosmos DB"
            return result
        
        try:
            # Counts
            result["counts"]["vertices"] = self.query("g.V().count()")[0]
            result["counts"]["edges"] = self.query("g.E().count()")[0]
            
            # Vertex labels with counts
            v_labels = self.query("g.V().label().dedup()")
            result["vertex_labels"] = []
            for label in sorted(v_labels):
                count = self.query(f"g.V().hasLabel('{label}').count()")[0]
                result["vertex_labels"].append({"label": label, "count": count})
            
            # Edge labels with counts
            e_labels = self.query("g.E().label().dedup()")
            result["edge_labels"] = []
            for label in sorted(e_labels):
                count = self.query(f"g.E().hasLabel('{label}').count()")[0]
                result["edge_labels"].append({"label": label, "count": count})
            
            # Sample vertices
            samples = self.query("g.V().limit(20).valueMap(true).by(unfold())")
            result["sample_vertices"] = samples
            
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    def get_all_vertices(self) -> dict:
        """Get all vertices as JSON."""
        result = {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "count": 0,
            "vertices": []
        }
        
        if not self.connected:
            result["error"] = "Not connected"
            return result
        
        try:
            vertices = self.query("g.V().valueMap(true).by(unfold())")
            result["vertices"] = vertices
            result["count"] = len(vertices)
            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    def get_all_edges(self) -> dict:
        """Get all edges as JSON."""
        result = {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "count": 0,
            "edges": []
        }
        
        if not self.connected:
            result["error"] = "Not connected"
            return result
        
        try:
            query = """
            g.E().project('id', 'label', 'source', 'target', 'properties')
                .by(id)
                .by(label)
                .by(outV().id())
                .by(inV().id())
                .by(valueMap())
            """
            edges = self.query(query)
            result["edges"] = edges
            result["count"] = len(edges)
            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    def export_all(self) -> dict:
        """Export everything (vertices + edges) as JSON."""
        result = {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "endpoint": COSMOS_GREMLIN_CONFIG['endpoint'],
                "database": COSMOS_GREMLIN_CONFIG['database'],
                "graph": COSMOS_GREMLIN_CONFIG['graph']
            },
            "vertices": {"count": 0, "data": []},
            "edges": {"count": 0, "data": []}
        }
        
        if not self.connected:
            result["error"] = "Not connected"
            return result
        
        try:
            # Get vertices
            vertices = self.query("g.V().valueMap(true).by(unfold())")
            result["vertices"]["data"] = vertices
            result["vertices"]["count"] = len(vertices)
            
            # Get edges
            query = """
            g.E().project('id', 'label', 'source', 'target', 'properties')
                .by(id)
                .by(label)
                .by(outV().id())
                .by(inV().id())
                .by(valueMap())
            """
            edges = self.query(query)
            result["edges"]["data"] = edges
            result["edges"]["count"] = len(edges)
            
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            
        return result


def save_json(data: dict, filename: str):
    """Save data to JSON file."""
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    
    return filepath


def cmd_summary():
    """Get Cosmos summary → JSON output."""
    extractor = CosmosGremlinExtractor()
    
    # Connect
    conn_result = extractor.connect()
    if not conn_result["success"]:
        print(json.dumps(conn_result, indent=2))
        return
    
    try:
        # Get summary
        summary = extractor.get_summary()
        
        # Save to file
        filepath = save_json(summary, "cosmos_summary.json")
        summary["saved_to"] = filepath
        
        # Print JSON output
        print(json.dumps(summary, indent=2, default=str))
        
    finally:
        extractor.close()


def cmd_vertices():
    """Get all vertices → JSON output."""
    extractor = CosmosGremlinExtractor()
    
    conn_result = extractor.connect()
    if not conn_result["success"]:
        print(json.dumps(conn_result, indent=2))
        return
    
    try:
        result = extractor.get_all_vertices()
        filepath = save_json(result, "cosmos_vertices.json")
        result["saved_to"] = filepath
        print(json.dumps(result, indent=2, default=str))
    finally:
        extractor.close()


def cmd_edges():
    """Get all edges → JSON output."""
    extractor = CosmosGremlinExtractor()
    
    conn_result = extractor.connect()
    if not conn_result["success"]:
        print(json.dumps(conn_result, indent=2))
        return
    
    try:
        result = extractor.get_all_edges()
        filepath = save_json(result, "cosmos_edges.json")
        result["saved_to"] = filepath
        print(json.dumps(result, indent=2, default=str))
    finally:
        extractor.close()


def cmd_export():
    """Export all (vertices + edges) → JSON output."""
    extractor = CosmosGremlinExtractor()
    
    conn_result = extractor.connect()
    if not conn_result["success"]:
        print(json.dumps(conn_result, indent=2))
        return
    
    try:
        result = extractor.export_all()
        filepath = save_json(result, "cosmos_full_export.json")
        result["saved_to"] = filepath
        
        # Print summary (not full data - too large)
        output = {
            "success": result["success"],
            "timestamp": result["timestamp"],
            "config": result["config"],
            "vertices_count": result["vertices"]["count"],
            "edges_count": result["edges"]["count"],
            "saved_to": filepath
        }
        print(json.dumps(output, indent=2))
        
    finally:
        extractor.close()


def cmd_merge():
    """Merge Cosmos data into local KG → JSON output."""
    result = {
        "success": False,
        "timestamp": datetime.now().isoformat(),
        "stats": {
            "entities_added": 0,
            "entities_skipped": 0,
            "relationships_added": 0,
            "relationships_skipped": 0
        },
        "kg_totals": {
            "entities": 0,
            "relationships": 0
        }
    }
    
    extractor = CosmosGremlinExtractor()
    
    conn_result = extractor.connect()
    if not conn_result["success"]:
        result["error"] = conn_result["message"]
        print(json.dumps(result, indent=2))
        return
    
    try:
        # Get Cosmos data
        vertices = extractor.query("g.V().valueMap(true).by(unfold())")
        edges_query = """
        g.E().project('id', 'label', 'source', 'target', 'properties')
            .by(id).by(label).by(outV().id()).by(inV().id()).by(valueMap())
        """
        edges = extractor.query(edges_query)
        
        # Load existing KG
        kg_path = Path(KG_PATH)
        if kg_path.exists():
            with open(kg_path, 'r', encoding='utf-8') as f:
                kg_data = json.load(f)
        else:
            kg_data = {'entities': {}, 'relationships': []}
        
        # Get existing IDs
        existing_entity_ids = set()
        for cat, entities in kg_data.get('entities', {}).items():
            if isinstance(entities, dict):
                existing_entity_ids.update(k.upper() for k in entities.keys())
        
        existing_rel_keys = set()
        for rel in kg_data.get('relationships', []):
            key = (rel['source'].upper(), rel['target'].upper(), rel['type'].lower())
            existing_rel_keys.add(key)
        
        # Add entities
        if 'cosmos_imported' not in kg_data['entities']:
            kg_data['entities']['cosmos_imported'] = {}
        
        added_entities = []
        for v in vertices:
            v_id = str(v.get('id', '')).upper().replace(' ', '_').replace('-', '_')
            
            if not v_id or v_id in existing_entity_ids:
                result["stats"]["entities_skipped"] += 1
                continue
            
            entity = {
                'id': v_id,
                'label': v.get('name', v.get('label', v_id)),
                'type': v.get('label', 'entity'),
                'definition': v.get('definition', v.get('description', '')),
                'source': 'cosmos_db'
            }
            
            kg_data['entities']['cosmos_imported'][v_id] = entity
            existing_entity_ids.add(v_id)
            result["stats"]["entities_added"] += 1
            added_entities.append(v_id)
        
        # Add relationships
        max_rel_id = 0
        for rel in kg_data.get('relationships', []):
            rel_id = rel.get('id', 'rel_0')
            if rel_id.startswith('rel_'):
                try:
                    num = int(rel_id.split('_')[1])
                    max_rel_id = max(max_rel_id, num)
                except:
                    pass
        
        added_rels = []
        for e in edges:
            source = str(e.get('source', '')).upper().replace(' ', '_').replace('-', '_')
            target = str(e.get('target', '')).upper().replace(' ', '_').replace('-', '_')
            rel_type = str(e.get('label', 'related_to')).lower().replace(' ', '_')
            
            key = (source, target, rel_type)
            
            if key in existing_rel_keys:
                result["stats"]["relationships_skipped"] += 1
                continue
            
            max_rel_id += 1
            rel = {
                'id': f'rel_{max_rel_id:03d}',
                'source': source,
                'target': target,
                'type': rel_type,
                'description': f'{source} {rel_type} {target}',
                'source_db': 'cosmos_db',
                'weight': 8
            }
            
            kg_data['relationships'].append(rel)
            existing_rel_keys.add(key)
            result["stats"]["relationships_added"] += 1
            added_rels.append(f"{source}--[{rel_type}]-->{target}")
        
        # Save KG
        kg_data['metadata'] = kg_data.get('metadata', {})
        kg_data['metadata']['last_cosmos_sync'] = datetime.now().isoformat()
        
        with open(kg_path, 'w', encoding='utf-8') as f:
            json.dump(kg_data, f, indent=2, ensure_ascii=False)
        
        # Calculate totals
        total_entities = sum(len(v) for v in kg_data['entities'].values() if isinstance(v, dict))
        result["kg_totals"]["entities"] = total_entities
        result["kg_totals"]["relationships"] = len(kg_data['relationships'])
        result["added_entities"] = added_entities[:20]  # First 20
        result["added_relationships"] = added_rels[:20]  # First 20
        result["kg_path"] = str(kg_path)
        result["success"] = True
        
        print(json.dumps(result, indent=2))
        
    finally:
        extractor.close()


# =============================================================================
# CLI - All outputs are JSON!
# =============================================================================

if __name__ == '__main__':
    commands = {
        'summary': cmd_summary,
        'vertices': cmd_vertices,
        'edges': cmd_edges,
        'export': cmd_export,
        'merge': cmd_merge
    }
    
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        help_output = {
            "script": "extract_cosmos_entities.py",
            "description": "Extract data from Cosmos DB Gremlin - All outputs in JSON",
            "config": {
                "endpoint": COSMOS_GREMLIN_CONFIG['endpoint'],
                "database": COSMOS_GREMLIN_CONFIG['database'],
                "graph": COSMOS_GREMLIN_CONFIG['graph'],
                "key_set": bool(COSMOS_GREMLIN_CONFIG['password'])
            },
            "commands": {
                "summary": "Get Cosmos DB summary (counts, labels, samples)",
                "vertices": "Get all vertices/entities",
                "edges": "Get all edges/relationships", 
                "export": "Export everything to JSON file",
                "merge": "Merge Cosmos data into local KG"
            },
            "usage": [
                "export COSMOS_GREMLIN_KEY='your-key'",
                "python extract_cosmos_entities.py summary",
                "python extract_cosmos_entities.py export",
                "python extract_cosmos_entities.py merge"
            ],
            "output_directory": OUTPUT_DIR
        }
        print(json.dumps(help_output, indent=2))
    else:
        commands[sys.argv[1]]()

