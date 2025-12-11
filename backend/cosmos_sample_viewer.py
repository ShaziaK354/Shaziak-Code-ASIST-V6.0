"""
View sample data from each vertex/edge type
to decide what to import
"""

import json
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from gremlin_python.driver import client, serializer
    GREMLIN_AVAILABLE = True
except ImportError:
    GREMLIN_AVAILABLE = False
    print('{"error": "gremlin_python not installed"}')
    exit(1)

COSMOS_GREMLIN_CONFIG = {
    'endpoint': os.getenv("COSMOS_GREMLIN_ENDPOINT", "asist-graph-db.gremlin.cosmos.azure.com"),
    'database': os.getenv("COSMOS_GREMLIN_DATABASE", "ASIST-Agent-1.1DB"),
    'graph': os.getenv("COSMOS_GREMLIN_COLLECTION", "AGENT1.4"),
    'password': os.getenv("COSMOS_GREMLIN_KEY", "")
}

def get_client():
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
    try:
        return c.submit(q).all().result()
    except Exception as e:
        return []

def get_samples_for_all_labels(samples_per_label=3):
    """Get sample vertices for each label type."""
    c = get_client()
    
    result = {
        "timestamp": "",
        "samples_per_label": samples_per_label,
        "vertex_samples": {},
        "edge_samples": {}
    }
    
    from datetime import datetime
    result["timestamp"] = datetime.now().isoformat()
    
    # Get all vertex labels
    labels = query(c, "g.V().label().dedup()")
    
    for label in sorted(labels):
        # Get sample vertices of this label
        safe_label = label.replace("'", "\\'")
        samples = query(c, f"g.V().hasLabel('{safe_label}').limit({samples_per_label}).valueMap(true).by(unfold())")
        
        # Simplify the data
        simplified = []
        for s in samples:
            simple = {
                'id': s.get('id', ''),
                'name': s.get('name', s.get('label', s.get('id', ''))),
                'description': s.get('description', s.get('definition', ''))[:200] if s.get('description', s.get('definition', '')) else ''
            }
            # Add any other interesting properties
            for key in ['chapter', 'section', 'type', 'category']:
                if key in s:
                    simple[key] = s[key]
            simplified.append(simple)
        
        result["vertex_samples"][label] = {
            "count": query(c, f"g.V().hasLabel('{safe_label}').count()")[0],
            "samples": simplified
        }
    
    # Get sample edges for top relationship types
    edge_labels = query(c, "g.E().label().dedup()")
    
    # Get samples for important edge types
    important_edges = ['reports_to', 'reportsto', 'authorized_by', 'authorizedby', 
                       'AUTHORIZED_BY', 'supervises', 'administers', 'manages',
                       'MANAGES', 'part_of', 'PART_OF', 'includes', 'INCLUDES',
                       'coordinates_with', 'coordinateswith', 'provides', 'oversees']
    
    for label in edge_labels:
        if label.lower() in [e.lower() for e in important_edges]:
            safe_label = label.replace("'", "\\'")
            edge_query = f"""
            g.E().hasLabel('{safe_label}').limit(5)
                .project('source', 'target', 'label')
                .by(outV().values('id', 'name').fold())
                .by(inV().values('id', 'name').fold())
                .by(label)
            """
            edge_samples = query(c, edge_query)
            
            result["edge_samples"][label] = {
                "count": query(c, f"g.E().hasLabel('{safe_label}').count()")[0],
                "samples": edge_samples
            }
    
    c.close()
    return result

def main():
    import sys
    
    samples = 3
    if len(sys.argv) > 1:
        try:
            samples = int(sys.argv[1])
        except:
            pass
    
    result = get_samples_for_all_labels(samples)
    
    # Save to file
    with open('cosmos_outputs/cosmos_samples.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str, ensure_ascii=False)
    
    # Print summary
    output = {
        "success": True,
        "saved_to": "cosmos_outputs/cosmos_samples.json",
        "vertex_labels_sampled": len(result["vertex_samples"]),
        "edge_labels_sampled": len(result["edge_samples"]),
        "samples_per_label": samples
    }
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()

