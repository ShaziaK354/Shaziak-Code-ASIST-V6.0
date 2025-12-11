"""
Check if FAA (Foreign Assistance Act) exists in Cosmos DB Gremlin
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from gremlin_python.driver import client, serializer
    from gremlin_python.driver.protocol import GremlinServerError
    print("✅ Gremlin Python installed")
except ImportError:
    print("❌ Gremlin Python not installed. Run: pip install gremlinpython")
    sys.exit(1)

# Cosmos Gremlin Configuration
COSMOS_GREMLIN_CONFIG = {
    'endpoint': os.getenv("COSMOS_GREMLIN_ENDPOINT", "asist-graph-db.gremlin.cosmos.azure.com").replace('wss://', '').replace(':443/', ''),
    'database': os.getenv("COSMOS_GREMLIN_DATABASE", "ASIST-Agent-1.1DB"),
    'graph': os.getenv("COSMOS_GREMLIN_COLLECTION", "AGENT1.4"),
    'password': os.getenv("COSMOS_GREMLIN_KEY", "")
}

def get_gremlin_client():
    """Create Gremlin client connection"""
    endpoint = f"wss://{COSMOS_GREMLIN_CONFIG['endpoint']}:443/"
    
    print(f"\n📡 Connecting to: {COSMOS_GREMLIN_CONFIG['endpoint']}")
    print(f"📁 Database: {COSMOS_GREMLIN_CONFIG['database']}")
    print(f"📊 Graph: {COSMOS_GREMLIN_CONFIG['graph']}")
    
    if not COSMOS_GREMLIN_CONFIG['password']:
        print("❌ COSMOS_GREMLIN_KEY not set in .env")
        return None
    
    try:
        gremlin_client = client.Client(
            endpoint,
            'g',
            username=f"/dbs/{COSMOS_GREMLIN_CONFIG['database']}/colls/{COSMOS_GREMLIN_CONFIG['graph']}",
            password=COSMOS_GREMLIN_CONFIG['password'],
            message_serializer=serializer.GraphSONSerializersV2d0()
        )
        print("✅ Connected to Cosmos Gremlin!")
        return gremlin_client
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def run_query(gremlin_client, query, description):
    """Run a Gremlin query and display results"""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"📝 Query: {query}")
    print('='*60)
    
    try:
        result_set = gremlin_client.submit(query)
        results = result_set.all().result()
        
        if results:
            print(f"✅ Found {len(results)} results:")
            for i, result in enumerate(results[:20], 1):  # Limit to 20
                print(f"  {i}. {result}")
        else:
            print("❌ No results found")
        
        return results
    except GremlinServerError as e:
        print(f"❌ Gremlin Error: {e}")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def main():
    print("="*60)
    print("🔍 FAA (Foreign Assistance Act) CHECK IN COSMOS DB")
    print("="*60)
    
    # Connect to Cosmos Gremlin
    gremlin_client = get_gremlin_client()
    if not gremlin_client:
        return
    
    try:
        # Query 1: Search for FAA vertex by ID pattern
        run_query(
            gremlin_client,
            "g.V().has('id', containing('faa')).valueMap(true).limit(10)",
            "Searching for vertices with 'faa' in ID"
        )
        
        # Query 2: Search for FAA in label
        run_query(
            gremlin_client,
            "g.V().has('label', containing('faa')).valueMap(true).limit(10)",
            "Searching for vertices with 'faa' in label"
        )
        
        # Query 3: Search for Foreign Assistance Act
        run_query(
            gremlin_client,
            "g.V().has('id', containing('foreign_assistance')).valueMap(true).limit(10)",
            "Searching for 'foreign_assistance' in vertex ID"
        )
        
        # Query 4: Search edges with FAA
        run_query(
            gremlin_client,
            "g.E().has('label', containing('faa')).limit(10)",
            "Searching for edges with 'faa' in label"
        )
        
        # Query 5: Check Secretary of State relationships
        run_query(
            gremlin_client,
            "g.V().has('id', containing('secretary_of_state')).outE().valueMap(true).limit(20)",
            "Secretary of State outgoing edges"
        )
        
        # Query 6: Check what legal_basis edges exist
        run_query(
            gremlin_client,
            "g.E().has('label', 'legal_basis').limit(20)",
            "All 'legal_basis' edges"
        )
        
        # Query 7: Get Secretary of State vertex and all connected vertices
        run_query(
            gremlin_client,
            "g.V().has('id', containing('secretary_of_state')).both().id().limit(30)",
            "All vertices connected to Secretary of State"
        )
        
        # Query 8: Search for AECA to compare
        run_query(
            gremlin_client,
            "g.V().has('id', containing('aeca')).valueMap(true).limit(10)",
            "Searching for AECA vertices (for comparison)"
        )
        
        # Query 9: Count all vertices
        run_query(
            gremlin_client,
            "g.V().count()",
            "Total vertex count"
        )
        
        # Query 10: Count all edges
        run_query(
            gremlin_client,
            "g.E().count()",
            "Total edge count"
        )
        
    finally:
        gremlin_client.close()
        print("\n✅ Connection closed")

if __name__ == "__main__":
    main()
