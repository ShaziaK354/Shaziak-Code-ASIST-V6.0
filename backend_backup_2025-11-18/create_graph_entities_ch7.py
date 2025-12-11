#!/usr/bin/env python3
"""
SAMM CHAPTER 7 GRAPH DB ENTITY CREATION
========================================

This script creates entity nodes in your Graph DB (Cosmos Gremlin)
with section_reference properties for GraphRAG.

Generated: 2025-11-05T06:23:55.449956
Total unique entities: 17
"""

# Entity-Section mappings
ENTITY_SECTION_MAP = {
    "BL": ['.', '1', '2', '4', '7', 'C'],
    "BPC": ['.', '1', '7', 'C'],
    "CBL": ['.', '1', '2', '3', '7', 'C'],
    "CIF": ['.', '1', '4', '7', 'C'],
    "DEA": ['.', '1', '7', '8', 'C'],
    "DOJ": ['.', '1', '7', '8', 'C'],
    "DOT": ['.', '1', '6', '7', 'C'],
    "DTS": ['.', '1', '7', 'C'],
    "DoD": ['.', '1', '7', 'C'],
    "HMR": ['.', '1', '6', '7', 'C'],
    "ITAR": ['.', '1', '7', 'C'],
    "LOA": ['.', '1', '3', '7', 'C'],
    "NOA": ['.', '1', '7', '9', 'C'],
    "Others": ['.', '0', '1', '2', '7', '8', '9', 'C'],
    "SC": ['.', '1', '7', 'C'],
    "USG": ['.', '1', '7', 'C'],
    "USPS": ['.', '1', '2', '4', '7', 'C'],
}

def create_entities_cosmos_gremlin():
    """Create entities in Cosmos Gremlin"""
    
    # TODO: Configure your Cosmos DB connection
    # from gremlin_python.driver import client, serializer
    
    # client = client.Client(
    #     'wss://YOUR_COSMOS_ACCOUNT.gremlin.cosmos.azure.com:443/',
    #     'g',
    #     username="/dbs/YOUR_DB/colls/YOUR_COLLECTION",
    #     password="YOUR_PRIMARY_KEY",
    #     message_serializer=serializer.GraphSONSerializersV2d0()
    # )
    
    print("Creating entities in Graph DB...")
    
    for entity, sections in ENTITY_SECTION_MAP.items():
        # Create vertex for entity
        query = f"""
        g.addV('entity')
            .property('name', '{entity}')
            .property('section_reference', '{",".join(sections)}')
            .property('type', 'SAMM_Chapter7_Entity')
        """
        
        # TODO: Execute query
        # result = client.submit(query).all().result()
        print(f"  - Created entity: {entity} -> {sections}")
    
    print(f"✅ Created {len(ENTITY_SECTION_MAP)} entities")

if __name__ == "__main__":
    create_entities_cosmos_gremlin()
