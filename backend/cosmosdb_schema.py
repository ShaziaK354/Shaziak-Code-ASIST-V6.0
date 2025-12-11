import sys
import os
sys.path.insert(0, 'C:\\Users\\ShaziaKashif\\ASIST Project\\ASIST2.1\\ASIST_V2.1\\backend')

# Import necessary modules
from dotenv import load_dotenv
load_dotenv()

try:
    from gremlin_python.driver import client, serializer
    from gremlin_python.driver.protocol import GremlinServerError
    print("✅ Gremlin client imported successfully")
except ImportError:
    print("❌ Gremlin client not available")
    sys.exit(1)

def explore_database_schema():
    """Explore the actual database schema to find correct property names"""
    
    print("\n" + "="*80)
    print("DATABASE SCHEMA EXPLORER - Finding Actual Property Names")
    print("="*80)
    
    # Configuration from environment
    endpoint = os.getenv("COSMOS_GREMLIN_ENDPOINT", "asist-graph-db.gremlin.cosmos.azure.com").replace('wss://', '').replace(':443/', '')
    database = os.getenv("COSMOS_GREMLIN_DATABASE", "ASIST-Agent-1.1DB")
    graph = os.getenv("COSMOS_GREMLIN_COLLECTION", "AGENT1.4")
    password = os.getenv("COSMOS_GREMLIN_KEY", "")
    
    print(f"\n📊 Configuration:")
    print(f"   Endpoint: {endpoint}")
    print(f"   Database: {database}")
    print(f"   Graph: {graph}")
    
    if not password:
        print("\n❌ ERROR: Cosmos Gremlin password not configured!")
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
        print("✅ Gremlin client created successfully\n")
    except Exception as e:
        print(f"❌ Failed to create Gremlin client: {e}")
        return
    
    # Exploration queries
    queries = [
        {
            "name": "Sample 5 Vertices with ALL Properties",
            "query": "g.V().limit(5).valueMap(true)",
            "description": "Get first 5 vertices with ALL properties including ID and label"
        },
        {
            "name": "All Property Keys in Database",
            "query": "g.V().properties().key().dedup().fold()",
            "description": "List ALL unique property keys used in the database"
        },
        {
            "name": "Vertices with 'Ch' in Properties",
            "query": "g.V().has('Ch').limit(5).valueMap(true)",
            "description": "Find vertices with properties starting with 'Ch'"
        },
        {
            "name": "Search for Chapter-like Properties",
            "query": "g.V().or(has('Chapter'), has('ch'), has('Ch'), has('CHAPTER')).limit(5).valueMap(true)",
            "description": "Try different chapter property variations"
        },
        {
            "name": "Vertices Containing '6' in Any Property",
            "query": "g.V().filter(values().is(containing('6'))).limit(10).valueMap(true)",
            "description": "Find any vertices with '6' in their properties"
        },
        {
            "name": "All Vertex Labels",
            "query": "g.V().label().dedup().fold()",
            "description": "Get all unique vertex labels/types"
        },
        {
            "name": "Sample Vertex with 'section' Property",
            "query": "g.V().has('section').limit(5).valueMap(true)",
            "description": "Find vertices that have 'section' property"
        },
        {
            "name": "Sample Vertex with 'acronym' Property (Detailed)",
            "query": "g.V().has('acronym', 'DSCA').valueMap(true)",
            "description": "Get full DSCA entity to see its structure"
        },
        {
            "name": "Search for 'MILSTRIP' in ANY Property Value",
            "query": "g.V().where(values().is(containing('MILSTRIP'))).limit(5).valueMap(true)",
            "description": "Search for MILSTRIP anywhere in the data"
        },
        {
            "name": "Search for '6.3' or 'C6' in Properties",
            "query": "g.V().where(values().is(containing('C6'))).limit(10).valueMap(true)",
            "description": "Find any reference to Chapter 6 sections"
        },
        {
            "name": "Sample of Different Entity Types",
            "query": "g.V().group().by(label).by(limit(2).valueMap(true))",
            "description": "Get sample of each entity type"
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
                print(f"✅ Found {len(result_list)} result(s):\n")
                
                # Display results based on query type
                for idx, result in enumerate(result_list[:3], 1):  # Show first 3
                    print(f"   Result {idx}:")
                    
                    if isinstance(result, dict):
                        # Pretty print dictionary
                        for key, value in result.items():
                            if isinstance(value, list):
                                if len(value) > 0:
                                    # For Cosmos DB, values are often in lists
                                    if isinstance(value[0], dict):
                                        print(f"      {key}: {value[0]}")
                                    else:
                                        print(f"      {key}: {value[0]}")
                                else:
                                    print(f"      {key}: []")
                            else:
                                print(f"      {key}: {value}")
                    elif isinstance(result, list):
                        # For property lists
                        print(f"      Properties: {', '.join(map(str, result[:20]))}")
                        if len(result) > 20:
                            print(f"      ... and {len(result) - 20} more")
                    else:
                        print(f"      {result}")
                    print()
                
                if len(result_list) > 3:
                    print(f"   ... and {len(result_list) - 3} more results\n")
                    
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
    print("SCHEMA EXPLORATION COMPLETE")
    print("="*80)
    print("\n💡 KEY FINDINGS TO LOOK FOR:")
    print("   1. What property names are actually used? (chapter vs Chapter vs Ch)")
    print("   2. What is the structure of property values? (string vs list)")
    print("   3. Are there any Chapter 6 references at all?")
    print("   4. What labels/types exist in the database?")
    print("   5. How are sections stored? (section vs Section vs sec)")

if __name__ == "__main__":
    explore_database_schema()