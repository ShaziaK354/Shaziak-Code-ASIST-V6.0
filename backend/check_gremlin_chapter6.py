import sys
import os
sys.path.insert(0, '/mnt/user-data/uploads')

# Import necessary modules
from app_3_3_5_modified_v5_FIXED import COSMOS_GREMLIN_CONFIG

try:
    from gremlin_python.driver import client, serializer
    from gremlin_python.driver.protocol import GremlinServerError
    print("✅ Gremlin client imported successfully")
except ImportError:
    print("❌ Gremlin client not available")
    sys.exit(1)

def test_gremlin_connection():
    """Test Gremlin database connection and query Chapter 6 data"""
    
    print("\n" + "="*80)
    print("GREMLIN DATABASE - CHAPTER 6 VERIFICATION")
    print("="*80)
    
    # Configuration
    endpoint = COSMOS_GREMLIN_CONFIG['endpoint']
    database = COSMOS_GREMLIN_CONFIG['database']
    graph = COSMOS_GREMLIN_CONFIG['graph']
    password = COSMOS_GREMLIN_CONFIG['password']
    
    print(f"\n📊 Configuration:")
    print(f"   Endpoint: {endpoint}")
    print(f"   Database: {database}")
    print(f"   Graph: {graph}")
    print(f"   Password: {'***' + password[-4:] if password else 'NOT SET'}")
    
    if not password:
        print("\n❌ ERROR: Cosmos Gremlin password not configured!")
        print("   Set COSMOS_GREMLIN_KEY environment variable")
        return
    
    # Create client
    try:
        gremlin_client = client.Client(
            f'wss://{endpoint}:443/',
            'g',
            username=f"/dbs/{database}/colls/{graph}",
            password=password,
            message_serializer=serializer.GraphSONSerializersV2d0()
        )
        print("\n✅ Gremlin client created successfully")
    except Exception as e:
        print(f"\n❌ Failed to create Gremlin client: {e}")
        return
    
    # Test queries
    queries = [
        {
            "name": "Total Vertex Count",
            "query": "g.V().count()",
            "description": "Count all vertices in the database"
        },
        {
            "name": "Chapter 6 Vertices",
            "query": "g.V().has('chapter', 'Chapter 6').count()",
            "description": "Count vertices tagged with Chapter 6"
        },
        {
            "name": "Chapter 6 Entities",
            "query": "g.V().has('chapter', 'Chapter 6').valueMap()",
            "description": "Get all Chapter 6 entities with properties"
        },
        {
            "name": "MILSTRIP Entity",
            "query": "g.V().has('name', 'MILSTRIP').valueMap()",
            "description": "Search for MILSTRIP entity"
        },
        {
            "name": "MILSTRIP by Acronym",
            "query": "g.V().has('acronym', 'MILSTRIP').valueMap()",
            "description": "Search for MILSTRIP by acronym field"
        },
        {
            "name": "All Acronyms",
            "query": "g.V().has('acronym').values('name', 'acronym').limit(20)",
            "description": "List first 20 entities with acronyms"
        },
        {
            "name": "Search by Text (MILSTRIP)",
            "query": "g.V().or(has('name', containing('MILSTRIP')), has('description', containing('MILSTRIP'))).valueMap()",
            "description": "Text search for MILSTRIP in name or description"
        },
        {
            "name": "C6.3.3 Section",
            "query": "g.V().has('section', 'C6.3.3').valueMap()",
            "description": "Search for section C6.3.3"
        },
        {
            "name": "All Chapter Labels",
            "query": "g.V().has('chapter').values('chapter').dedup().limit(20)",
            "description": "List all unique chapter labels"
        },
        {
            "name": "All Sections in Chapter 6",
            "query": "g.V().has('chapter', 'Chapter 6').values('section').dedup().limit(20)",
            "description": "List all sections in Chapter 6"
        }
    ]
    
    # Execute queries
    for i, test_query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}: {test_query['name']}")
        print(f"Description: {test_query['description']}")
        print(f"{'='*80}")
        print(f"Gremlin: {test_query['query']}")
        print(f"{'-'*80}")
        
        try:
            callback = gremlin_client.submitAsync(test_query['query'])
            results = callback.result()
            
            result_list = []
            for result in results:
                result_list.append(result)
            
            if len(result_list) == 0:
                print("⚠️  No results found")
            else:
                print(f"✅ Found {len(result_list)} result(s):")
                for idx, result in enumerate(result_list[:5], 1):  # Show first 5
                    print(f"\n   Result {idx}:")
                    if isinstance(result, dict):
                        for key, value in result.items():
                            # Handle list values (common in Cosmos DB Gremlin)
                            if isinstance(value, list) and len(value) > 0:
                                print(f"      {key}: {value[0]}")
                            else:
                                print(f"      {key}: {value}")
                    else:
                        print(f"      {result}")
                
                if len(result_list) > 5:
                    print(f"\n   ... and {len(result_list) - 5} more results")
                    
        except GremlinServerError as e:
            print(f"❌ Gremlin Server Error: {e.status_message}")
        except Exception as e:
            print(f"❌ Query Failed: {str(e)}")
    
    # Close client
    try:
        gremlin_client.close()
        print("\n✅ Gremlin client closed")
    except:
        pass
    
    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    test_gremlin_connection()