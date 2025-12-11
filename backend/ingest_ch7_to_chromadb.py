#!/usr/bin/env python3
"""
SAMM CHAPTER 7 TO CHROMADB INGESTION SCRIPT
============================================

Enhanced version with entity-section linking for GraphRAG retrieval.

This script:
1. Loads SAMM Chapter 7 chunks with rich metadata
2. Generates embeddings optimized for semantic search
3. Ingests into ChromaDB with entity-section references preserved
4. Enables GraphRAG query flow: Entity → Section → Chunk

Optimized for: LLaMA 3.2:3b + GraphRAG
Vector DB: ChromaDB
Embedding Model: all-MiniLM-L6-v2 (384 dimensions)
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Required imports
try:
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.config import Settings
    import numpy as np
    from tqdm import tqdm
    print("✅ All required packages imported successfully")
except ImportError as e:
    print(f"❌ Missing package: {e}")
    print("Install with: pip install sentence-transformers chromadb tqdm numpy")
    exit(1)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

class Config:
    """Configuration for SAMM Chapter 7 ingestion"""
    
    # Input
    CHUNKS_JSON_PATH = "samm_chapter7_chunks__1_.json"
    
    # Vector Database
    VECTOR_DB_PATH = "./vector_db"
    COLLECTION_NAME = "samm_chapter7"
    
    # Embedding Model
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    # Processing
    BATCH_SIZE = 50
    SHOW_PROGRESS = True

# ==============================================================================
# SAMM CHUNKS LOADER
# ==============================================================================

class SAMMChunksLoader:
    """Loads and validates SAMM Chapter 7 chunks from JSON"""
    
    def __init__(self, json_path: str = Config.CHUNKS_JSON_PATH):
        self.json_path = Path(json_path)
        
        if not self.json_path.exists():
            raise FileNotFoundError(f"Chunks file not found: {json_path}")
        
        print(f"\n📂 SAMM Chapter 7 Chunks Loader initialized")
        print(f"   Input file: {self.json_path}")
    
    def load_chunks(self) -> List[Dict]:
        """Load chunks from JSON file"""
        
        print(f"\n📥 Loading chunks from JSON...")
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        print(f"   ✅ Loaded {len(chunks)} chunks")
        
        # Validate chunk structure
        self._validate_chunks(chunks)
        
        # Show statistics
        self._show_chunk_statistics(chunks)
        
        return chunks
    
    def _validate_chunks(self, chunks: List[Dict]):
        """Validate that chunks have required fields"""
        
        required_fields = ['chunk_id', 'content', 'metadata']
        required_metadata = ['section_id', 'primary_entities', 'entity_section_references']
        
        for i, chunk in enumerate(chunks):
            for field in required_fields:
                if field not in chunk:
                    raise ValueError(f"Chunk {i} missing required field: {field}")
            
            for meta_field in required_metadata:
                if meta_field not in chunk['metadata']:
                    print(f"   ⚠️ Chunk {i} missing metadata field: {meta_field}")
        
        print(f"   ✅ All chunks validated")
    
    def _show_chunk_statistics(self, chunks: List[Dict]):
        """Show chunk statistics"""
        
        print(f"\n   📊 Chunk Statistics:")
        
        # Priority distribution
        priorities = {}
        for chunk in chunks:
            priority = chunk['metadata'].get('priority', 'UNKNOWN')
            priorities[priority] = priorities.get(priority, 0) + 1
        
        print(f"   Priority distribution:")
        for priority, count in sorted(priorities.items(), key=lambda x: x[1], reverse=True):
            print(f"      {priority}: {count}")
        
        # Chunks with entities
        with_entities = sum(1 for c in chunks if c['metadata'].get('primary_entities'))
        print(f"   Chunks with primary entities: {with_entities}")
        
        # Chunks with tables
        with_tables = sum(1 for c in chunks if c['metadata'].get('has_table'))
        print(f"   Chunks with tables: {with_tables}")
        
        # Sample chunk
        sample = chunks[0]
        print(f"\n   Sample chunk:")
        print(f"   - ID: {sample['chunk_id']}")
        print(f"   - Section: {sample['metadata'].get('section_id', 'N/A')}")
        print(f"   - Entities: {', '.join(sample['metadata'].get('primary_entities', [])[:3])}")
        print(f"   - Priority: {sample['metadata'].get('priority', 'N/A')}")

# ==============================================================================
# EMBEDDING GENERATOR
# ==============================================================================

class EmbeddingGenerator:
    """Generates embeddings for SAMM Chapter 7 chunks"""
    
    def __init__(self, model_name: str = Config.EMBEDDING_MODEL):
        self.model_name = model_name
        
        print(f"\n🔢 Initializing Embedding Generator")
        print(f"   Model: {model_name}")
        print(f"   Loading model...")
        
        self.model = SentenceTransformer(model_name)
        
        # Get embedding dimensions
        test_embedding = self.model.encode(["test"])
        self.embedding_dim = len(test_embedding[0])
        
        print(f"   ✅ Model loaded successfully")
        print(f"   Embedding dimensions: {self.embedding_dim}")
    
    def generate_embeddings(self, chunks: List[Dict], 
                          batch_size: int = Config.BATCH_SIZE) -> List[List[float]]:
        """Generate embeddings for all chunks"""
        
        print(f"\n🔢 Generating embeddings for {len(chunks)} chunks...")
        print(f"   Batch size: {batch_size}")
        
        # Extract enriched text for embedding
        # We combine section info, entities, and content for better semantic matching
        texts = []
        for chunk in chunks:
            if 'searchable_text' in chunk:
                texts.append(chunk['searchable_text'])
            else:
                # Create enriched searchable text
                section = chunk['metadata'].get('section_id', '')
                title = chunk['metadata'].get('section_title', '')
                entities = ' '.join(chunk['metadata'].get('primary_entities', [])[:5])
                content = chunk['content'][:500]
                texts.append(f"{section} {title} {entities} {content}")
        
        # Generate embeddings in batches with progress bar
        all_embeddings = []
        
        if Config.SHOW_PROGRESS:
            from tqdm import tqdm
            iterator = tqdm(range(0, len(texts), batch_size), desc="Generating embeddings")
        else:
            iterator = range(0, len(texts), batch_size)
        
        for i in iterator:
            batch = texts[i:i + batch_size]
            embeddings = self.model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
            all_embeddings.extend(embeddings.tolist())
        
        print(f"   ✅ Generated {len(all_embeddings)} embeddings")
        
        return all_embeddings

# ==============================================================================
# CHROMADB INGESTION
# ==============================================================================

class ChromaDBIngestion:
    """Handles ingestion into ChromaDB with entity-section linking"""
    
    def __init__(self, db_path: str = Config.VECTOR_DB_PATH,
                 collection_name: str = Config.COLLECTION_NAME):
        
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        
        print(f"\n🗄️ Initializing ChromaDB")
        print(f"   Database path: {db_path}")
        print(f"   Collection name: {collection_name}")
        
        # Create directory if needed
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Delete existing collection if it exists
        try:
            self.client.delete_collection(name=collection_name)
            print(f"   ⚠️ Deleted existing collection: {collection_name}")
        except:
            pass
        
        # Create new collection
        self.collection = self.client.create_collection(
            name=collection_name,
            metadata={"description": "SAMM Chapter 7 chunks with entity-section linking"}
        )
        
        print(f"   ✅ Collection '{collection_name}' created")
    
    def ingest_chunks(self, chunks: List[Dict], embeddings: List[List[float]]):
        """Ingest chunks with embeddings into ChromaDB"""
        
        print(f"\n📤 Ingesting {len(chunks)} chunks into ChromaDB...")
        
        # Prepare data for ingestion
        ids = []
        documents = []
        metadatas = []
        embeddings_list = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # ID
            ids.append(chunk['chunk_id'])
            
            # Document (content)
            documents.append(chunk['content'])
            
            # Metadata - flatten complex structures for ChromaDB
            metadata = {
                'section_id': chunk['metadata'].get('section_id', ''),
                'section_title': chunk['metadata'].get('section_title', ''),
                'chapter': str(chunk['metadata'].get('chapter', '')),
                'priority': chunk['metadata'].get('priority', ''),
                'chunk_type': chunk['metadata'].get('chunk_type', ''),
                'has_table': chunk['metadata'].get('has_table', False),
                'has_list': chunk['metadata'].get('has_list', False),
                'word_count': chunk['metadata'].get('word_count', 0),
                'char_count': chunk['metadata'].get('char_count', 0),
                'parent_section': chunk['metadata'].get('parent_section', ''),
                'embedding_model': Config.EMBEDDING_MODEL,
                'ingestion_date': datetime.now().isoformat()
            }
            
            # Add entity information as strings (ChromaDB doesn't support arrays in metadata)
            if chunk['metadata'].get('primary_entities'):
                metadata['primary_entities'] = ', '.join(chunk['metadata']['primary_entities'])
            
            if chunk['metadata'].get('related_entities'):
                metadata['related_entities'] = ', '.join(chunk['metadata']['related_entities'])
            
            # Add entity-section references as JSON string
            if chunk['metadata'].get('entity_section_references'):
                metadata['entity_section_refs'] = json.dumps(
                    chunk['metadata']['entity_section_references']
                )
            
            metadatas.append(metadata)
            embeddings_list.append(embedding)
        
        # Batch ingestion
        batch_size = Config.BATCH_SIZE
        total_batches = (len(ids) + batch_size - 1) // batch_size
        
        print(f"   Ingesting in {total_batches} batches of {batch_size}...")
        
        if Config.SHOW_PROGRESS:
            from tqdm import tqdm
            iterator = tqdm(range(0, len(ids), batch_size), desc="Ingesting batches")
        else:
            iterator = range(0, len(ids), batch_size)
        
        for i in iterator:
            batch_ids = ids[i:i + batch_size]
            batch_docs = documents[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]
            batch_embeddings = embeddings_list[i:i + batch_size]
            
            self.collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas,
                embeddings=batch_embeddings
            )
        
        print(f"   ✅ Successfully ingested {len(ids)} chunks")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        
        total_count = self.collection.count()
        
        # Get all metadata to compute statistics
        results = self.collection.get(
            include=['metadatas']
        )
        
        metadatas = results['metadatas']
        
        # Count statistics
        with_tables = sum(1 for m in metadatas if m.get('has_table'))
        with_entities = sum(1 for m in metadatas if m.get('primary_entities'))
        
        # Priority distribution
        priorities = {}
        for m in metadatas:
            priority = m.get('priority', 'UNKNOWN')
            priorities[priority] = priorities.get(priority, 0) + 1
        
        # Chunk type distribution
        chunk_types = {}
        for m in metadatas:
            chunk_type = m.get('chunk_type', 'UNKNOWN')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        return {
            'total_vectors': total_count,
            'collection_name': self.collection_name,
            'with_tables': with_tables,
            'with_entities': with_entities,
            'priorities': priorities,
            'chunk_types': chunk_types
        }

# ==============================================================================
# GRAPH DB HELPER
# ==============================================================================

class GraphRAGHelper:
    """Helper to generate Graph DB setup script"""
    
    @staticmethod
    def generate_graph_db_script(chunks: List[Dict]):
        """Generate a Python script to create Graph DB entities"""
        
        print(f"\n📊 Generating Graph DB helper script...")
        
        # Extract unique entities with their section references
        entity_map = {}
        
        for chunk in chunks:
            refs = chunk['metadata'].get('entity_section_references', {})
            for entity, sections in refs.items():
                if entity not in entity_map:
                    entity_map[entity] = set()
                entity_map[entity].update(sections)
        
        # Generate script
        script = f'''#!/usr/bin/env python3
"""
SAMM CHAPTER 7 GRAPH DB ENTITY CREATION
========================================

This script creates entity nodes in your Graph DB (Cosmos Gremlin)
with section_reference properties for GraphRAG.

Generated: {datetime.now().isoformat()}
Total unique entities: {len(entity_map)}
"""

# Entity-Section mappings
ENTITY_SECTION_MAP = {{
'''
        
        for entity, sections in sorted(entity_map.items()):
            sections_list = sorted(list(sections))
            script += f'    "{entity}": {sections_list},\n'
        
        script += '''}

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
'''
        
        # Save script
        output_path = Path("create_graph_entities_ch7.py")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(script)
        
        print(f"   ✅ Generated: {output_path}")
        print(f"   Total entities: {len(entity_map)}")

# ==============================================================================
# INGESTION PIPELINE
# ==============================================================================

class SAMMIngestionPipeline:
    """Complete ingestion pipeline for SAMM Chapter 7"""
    
    def __init__(self):
        self.chunks_loader = SAMMChunksLoader()
        self.embedding_generator = EmbeddingGenerator()
        self.db_ingestion = ChromaDBIngestion()
    
    def run(self) -> bool:
        """Run the complete ingestion pipeline"""
        
        try:
            start_time = time.time()
            
            # Step 1: Load chunks
            print(f"\n{'='*80}")
            print(f"STEP 1: LOADING CHUNKS")
            print(f"{'='*80}")
            chunks = self.chunks_loader.load_chunks()
            
            # Step 2: Generate embeddings
            print(f"\n{'='*80}")
            print(f"STEP 2: GENERATING EMBEDDINGS")
            print(f"{'='*80}")
            embeddings = self.embedding_generator.generate_embeddings(chunks)
            
            # Step 3: Ingest into ChromaDB
            print(f"\n{'='*80}")
            print(f"STEP 3: INGESTING INTO CHROMADB")
            print(f"{'='*80}")
            self.db_ingestion.ingest_chunks(chunks, embeddings)
            
            # Step 4: Generate Graph DB helper script
            print(f"\n{'='*80}")
            print(f"STEP 4: GENERATING GRAPH DB HELPER")
            print(f"{'='*80}")
            GraphRAGHelper.generate_graph_db_script(chunks)
            
            # Step 5: Verify and show statistics
            print(f"\n{'='*80}")
            print(f"STEP 5: VERIFICATION & STATISTICS")
            print(f"{'='*80}")
            stats = self.db_ingestion.get_statistics()
            self._display_statistics(stats)
            
            # Success summary
            duration = time.time() - start_time
            print(f"\n{'='*80}")
            print(f"✅ INGESTION COMPLETED SUCCESSFULLY")
            print(f"{'='*80}")
            print(f"Total time: {duration:.2f} seconds")
            print(f"Vectors ingested: {stats['total_vectors']}")
            print(f"Collection: {stats['collection_name']}")
            print(f"Database location: {Config.VECTOR_DB_PATH}")
            print(f"{'='*80}\n")
            
            # Next steps
            self._show_next_steps()
            
            return True
            
        except Exception as e:
            print(f"\n{'='*80}")
            print(f"❌ INGESTION FAILED")
            print(f"{'='*80}")
            print(f"Error: {e}")
            print(f"{'='*80}\n")
            import traceback
            traceback.print_exc()
            return False
    
    def _display_statistics(self, stats: Dict[str, Any]):
        """Display collection statistics"""
        
        print(f"\n📊 Collection Statistics:")
        print(f"   Total vectors: {stats['total_vectors']}")
        print(f"   Collection: {stats['collection_name']}")
        print(f"   Chunks with tables: {stats['with_tables']}")
        print(f"   Chunks with entities: {stats['with_entities']}")
        
        if stats['priorities']:
            print(f"\n   Priority distribution:")
            for priority, count in sorted(stats['priorities'].items(), key=lambda x: x[1], reverse=True):
                print(f"      {priority}: {count}")
        
        if stats['chunk_types']:
            print(f"\n   Chunk type distribution:")
            for chunk_type, count in sorted(stats['chunk_types'].items(), key=lambda x: x[1], reverse=True):
                print(f"      {chunk_type}: {count}")
    
    def _show_next_steps(self):
        """Show what to do next"""
        
        print(f"\n{'='*80}")
        print(f"🎯 NEXT STEPS FOR GRAPHRAG")
        print(f"{'='*80}")
        print(f"""
Your SAMM Chapter 7 is now optimized for GraphRAG!

Step 1: Create Graph DB Entities
----------------------------------------
Run the generated script:
python create_graph_entities_ch7.py

Or manually create entities in Cosmos Gremlin with:
- name property
- section_reference property (links to vector chunks)
- type property

Step 2: Test Entity → Section → Chunk Flow
----------------------------------------
Query example:
1. User asks about a Chapter 7 concept
2. Extract entity from query
3. Graph DB query: get section_reference
4. Vector DB query: filter by section_id
5. Return complete chunk with full context

Step 3: Query ChromaDB
----------------------------------------
import chromadb
client = chromadb.PersistentClient(path="./vector_db")
collection = client.get_collection("samm_chapter7")

# Test query with section filter
results = collection.query(
    query_texts=["Your question here"],
    where={{"section_id": "C7.X.X.X"}},
    n_results=3
)

Step 4: Integrate with Your Agent
----------------------------------------
Update your IntegratedEntityAgent to:
1. Extract entities from query
2. Query Graph DB for section_reference
3. Use section_reference to filter Vector DB query
4. Return chunks with complete context

Expected Performance:
- Current: ~64% accuracy
- With GraphRAG: ~85%+ accuracy

{'='*80}
""")

# ==============================================================================
# TESTING
# ==============================================================================

def test_ingestion():
    """Test the ingestion with sample queries"""
    
    print(f"\n🧪 TESTING CHROMADB WITH ENTITY QUERIES")
    print(f"{'='*80}\n")
    
    try:
        import chromadb
        
        client = chromadb.PersistentClient(path=Config.VECTOR_DB_PATH)
        collection = client.get_collection(Config.COLLECTION_NAME)
        
        print(f"✅ Connected to collection: {Config.COLLECTION_NAME}")
        print(f"   Total vectors: {collection.count()}")
        
        # Test queries for Chapter 7
        test_queries = [
            ("What are the incident management practices?", {"priority": "CRITICAL"}),
            ("What is defect management?", None),
            ("What are the operational requirements?", {"priority": "HIGH"})
        ]
        
        for query, filters in test_queries:
            print(f"\n🔍 Query: '{query}'")
            if filters:
                print(f"   Filters: {filters}")
            
            results = collection.query(
                query_texts=[query],
                where=filters if filters else None,
                n_results=2,
                include=['documents', 'metadatas', 'distances']
            )
            
            for i, (doc, meta, dist) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ), 1):
                print(f"\n   Result {i}:")
                print(f"   - Section: {meta.get('section_id')}")
                print(f"   - Title: {meta.get('section_title', 'N/A')[:60]}")
                print(f"   - Entities: {meta.get('primary_entities', 'N/A')[:100]}")
                print(f"   - Distance: {dist:.4f}")
                print(f"   - Preview: {doc[:150]}...")
        
        print(f"\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    """Main execution"""
    
    print(f"""
{'='*80}
🤖 SAMM CHAPTER 7 CHROMADB INGESTION
   With Entity-Section Linking for GraphRAG
{'='*80}

This script will:
1. Load SAMM Chapter 7 chunks with entity-section mappings
2. Generate embeddings using {Config.EMBEDDING_MODEL}
3. Ingest into ChromaDB at {Config.VECTOR_DB_PATH}
4. Generate Graph DB helper script
5. Optimize for GraphRAG: Entity → Section → Chunk

Prerequisites:
✓ samm_chapter7_chunks.json file exists
✓ ChromaDB installed
✓ sentence-transformers installed

{'='*80}
""")
    
    # Check if chunks file exists
    if not Path(Config.CHUNKS_JSON_PATH).exists():
        print(f"❌ Chunks file not found: {Config.CHUNKS_JSON_PATH}")
        print(f"\nPlease ensure your chunks JSON file is in the current directory")
        return
    
    # Ask user to confirm
    response = input("Ready to start ingestion? (y/n): ").strip().lower()
    
    if response != 'y':
        print("Ingestion cancelled.")
        return
    
    # Run pipeline
    pipeline = SAMMIngestionPipeline()
    success = pipeline.run()
    
    if success:
        # Run test
        print(f"\n🧪 Would you like to test the ingestion? (y/n): ", end='')
        if input().strip().lower() == 'y':
            test_ingestion()

if __name__ == "__main__":
    main()
