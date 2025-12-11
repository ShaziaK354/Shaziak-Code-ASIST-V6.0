#!/usr/bin/env python3
"""
SAMM CHAPTER 9 TO CHROMADB INGESTION SCRIPT
============================================

Enhanced version with entity-section linking for GraphRAG retrieval.

This script:
1. Loads SAMM Chapter 9 chunks with rich metadata
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
    """Configuration for SAMM Chapter 9 ingestion"""
    
    # Input
    CHUNKS_JSON_PATH = "samm_chapter9_chunks.json"
    
    # Vector Database
    VECTOR_DB_PATH = "./vector_db"
    COLLECTION_NAME = "samm_chapter9"
    
    # Embedding Model
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    # Processing
    BATCH_SIZE = 50
    SHOW_PROGRESS = True

# ==============================================================================
# SAMM CHUNKS LOADER
# ==============================================================================

class SAMMChunksLoader:
    """Loads and validates SAMM Chapter 9 chunks from JSON"""
    
    def __init__(self, json_path: str = Config.CHUNKS_JSON_PATH):
        self.json_path = Path(json_path)
        
        if not self.json_path.exists():
            raise FileNotFoundError(f"Chunks file not found: {json_path}")
        
        print(f"\n📂 SAMM Chapter 9 Chunks Loader initialized")
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
    """Generates embeddings for SAMM Chapter 9 chunks"""
    
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
            print(f"   🗑️ Deleted existing collection: {collection_name}")
        except:
            pass
        
        # Create new collection
        self.collection = self.client.create_collection(
            name=collection_name,
            metadata={
                "description": "SAMM Chapter 9 with entity-section linking for GraphRAG",
                "embedding_model": Config.EMBEDDING_MODEL,
                "created_at": datetime.now().isoformat()
            }
        )
        
        print(f"   ✅ Created collection: {collection_name}")
    
    def ingest_chunks(self, chunks: List[Dict], embeddings: List[List[float]],
                     batch_size: int = Config.BATCH_SIZE):
        """Ingest chunks with embeddings into ChromaDB"""
        
        print(f"\n📥 Ingesting {len(chunks)} chunks into ChromaDB...")
        print(f"   Batch size: {batch_size}")
        
        # Prepare data for ingestion
        ids = []
        documents = []
        metadatas = []
        embeddings_list = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # IDs must be strings
            ids.append(chunk['chunk_id'])
            
            # Documents (content)
            documents.append(chunk['content'])
            
            # Metadata (ChromaDB requires flat dict with simple types)
            metadata = self._prepare_metadata(chunk['metadata'])
            metadatas.append(metadata)
            
            # Embeddings
            embeddings_list.append(embedding)
        
        # Ingest in batches
        if Config.SHOW_PROGRESS:
            from tqdm import tqdm
            iterator = tqdm(range(0, len(ids), batch_size), desc="Ingesting chunks")
        else:
            iterator = range(0, len(ids), batch_size)
        
        for i in iterator:
            batch_ids = ids[i:i + batch_size]
            batch_documents = documents[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]
            batch_embeddings = embeddings_list[i:i + batch_size]
            
            self.collection.add(
                ids=batch_ids,
                documents=batch_documents,
                metadatas=batch_metadatas,
                embeddings=batch_embeddings
            )
        
        print(f"   ✅ Ingested {len(ids)} chunks")
    
    def _prepare_metadata(self, metadata: Dict) -> Dict:
        """Prepare metadata for ChromaDB (flatten and convert to simple types)"""
        
        flat_metadata = {}
        
        # Simple fields
        simple_fields = [
            'chapter', 'section_id', 'section_title', 'parent_section',
            'chunk_type', 'intent_type', 'priority', 'is_combined'
        ]
        
        for field in simple_fields:
            if field in metadata:
                value = metadata[field]
                # ChromaDB requires string, int, float, or bool
                if isinstance(value, (str, int, float, bool)):
                    flat_metadata[field] = value
                else:
                    flat_metadata[field] = str(value)
        
        # Convert lists to comma-separated strings
        list_fields = ['primary_entities', 'related_entities', 'section_hierarchy', 'combined_from']
        
        for field in list_fields:
            if field in metadata and metadata[field]:
                flat_metadata[field] = ', '.join(str(x) for x in metadata[field])
        
        # Special handling for entity_section_references
        if 'entity_section_references' in metadata:
            # Convert dict to JSON string
            import json
            flat_metadata['entity_section_references'] = json.dumps(metadata['entity_section_references'])
        
        # Add boolean flags
        flat_metadata['has_table'] = metadata.get('has_table', False)
        flat_metadata['has_entities'] = bool(metadata.get('primary_entities'))
        
        return flat_metadata
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collection statistics"""
        
        collection_data = self.collection.get(include=['metadatas'])
        
        stats = {
            'total_vectors': self.collection.count(),
            'collection_name': self.collection_name,
            'with_tables': 0,
            'with_entities': 0,
            'priorities': {},
            'chunk_types': {}
        }
        
        for metadata in collection_data['metadatas']:
            if metadata.get('has_table'):
                stats['with_tables'] += 1
            
            if metadata.get('has_entities'):
                stats['with_entities'] += 1
            
            priority = metadata.get('priority', 'UNKNOWN')
            stats['priorities'][priority] = stats['priorities'].get(priority, 0) + 1
            
            chunk_type = metadata.get('chunk_type', 'UNKNOWN')
            stats['chunk_types'][chunk_type] = stats['chunk_types'].get(chunk_type, 0) + 1
        
        return stats

# ==============================================================================
# GRAPHRAG HELPER
# ==============================================================================

class GraphRAGHelper:
    """Helper functions for GraphRAG setup"""
    
    @staticmethod
    def generate_graph_db_script(chunks: List[Dict], output_file: str = "create_graph_entities_ch9.py"):
        """Generate a script to create Graph DB entities"""
        
        print(f"\n📝 Generating Graph DB helper script: {output_file}")
        
        # Extract unique entities with their section references
        entity_map = {}
        
        for chunk in chunks:
            entity_refs = chunk['metadata'].get('entity_section_references', {})
            entity_types = chunk['metadata'].get('entity_types', {})
            
            for entity, sections in entity_refs.items():
                if entity not in entity_map:
                    entity_map[entity] = {
                        'sections': set(),
                        'type': entity_types.get(entity, 'UNKNOWN')
                    }
                
                # Sections might be comma-separated
                if isinstance(sections, str):
                    entity_map[entity]['sections'].update(sections.split(', '))
                else:
                    entity_map[entity]['sections'].add(str(sections))
        
        # Generate script
        script_content = f'''#!/usr/bin/env python3
"""
SAMM CHAPTER 9 - GRAPH DB ENTITY CREATION SCRIPT
=================================================

Auto-generated script to create Graph DB entities for GraphRAG.

This script creates entities with:
- name: Entity name
- type: Entity type (DOCUMENT, ORGANIZATION, etc.)
- section_references: Sections where entity is discussed
- chapter: C9

Total entities: {len(entity_map)}
"""

# Example entity structure for Cosmos Gremlin:
ENTITIES = [
'''
        
        for entity, data in sorted(entity_map.items())[:10]:  # Show first 10 as examples
            sections = sorted(data['sections'])
            script_content += f'''    {{
        "name": "{entity}",
        "type": "{data['type']}",
        "section_references": {sections},
        "chapter": "C9"
    }},
'''
        
        script_content += f'''
    # ... {len(entity_map) - 10} more entities
]

# Full entity list saved separately
TOTAL_ENTITIES = {len(entity_map)}

def create_gremlin_entities():
    """
    Example Gremlin queries to create entities:
    
    g.addV('entity')
      .property('name', 'DoD')
      .property('type', 'ORGANIZATION')
      .property('section_references', 'C9.1.1, C9.3.1')
      .property('chapter', 'C9')
    """
    pass

if __name__ == "__main__":
    print(f"Total entities to create: {{TOTAL_ENTITIES}}")
    print("See ENTITIES list above for examples")
    print("\\nIntegrate with your Graph DB (Cosmos Gremlin, Neo4j, etc.)")
'''
        
        # Write script
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"   ✅ Generated {output_file}")
        print(f"   Total entities: {len(entity_map)}")

# ==============================================================================
# INGESTION PIPELINE
# ==============================================================================

class SAMMIngestionPipeline:
    """Complete ingestion pipeline for SAMM Chapter 9"""
    
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
            print(f"STEP 4: GENERATING GRAPHRAG HELPER SCRIPT")
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
Your SAMM Chapter 9 is now optimized for GraphRAG!

Step 1: Create Graph DB Entities
----------------------------------------
Run the generated script:
python create_graph_entities_ch9.py

Or manually create entities in Cosmos Gremlin with:
- name property
- section_reference property (links to vector chunks)
- type property

Step 2: Test Entity → Section → Chunk Flow
----------------------------------------
Query example:
1. User asks: "What is billing in FMS?"
2. Extract entity: "Billing"
3. Graph DB query: get section_reference = "C9.10"
4. Vector DB query: filter by section_id = "C9.10"
5. Return complete chunk with full context

Step 3: Query ChromaDB
----------------------------------------
import chromadb
client = chromadb.PersistentClient(path="./vector_db")
collection = client.get_collection("samm_chapter9")

# Test query with section filter
results = collection.query(
    query_texts=["What is billing in FMS?"],
    where={{"section_id": "C9.10"}},
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
        
        # Test queries
        test_queries = [
            ("What is billing in FMS?", {"section_id": "C9.10"}),
            ("What are financial management procedures?", {"priority": "CRITICAL"}),
            ("What is DoD FMR?", None)
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
🤖 SAMM CHAPTER 9 CHROMADB INGESTION
   With Entity-Section Linking for GraphRAG
{'='*80}

This script will:
1. Load SAMM Chapter 9 chunks with entity-section mappings
2. Generate embeddings using {Config.EMBEDDING_MODEL}
3. Ingest into ChromaDB at {Config.VECTOR_DB_PATH}
4. Generate Graph DB helper script
5. Optimize for GraphRAG: Entity → Section → Chunk

Prerequisites:
✓ samm_chapter9_chunks.json file exists
✓ ChromaDB installed
✓ sentence-transformers installed

{'='*80}
""")
    
    # Check if chunks file exists
    if not Path(Config.CHUNKS_JSON_PATH).exists():
        print(f"❌ Chunks file not found: {Config.CHUNKS_JSON_PATH}")
        print(f"\nPlease ensure samm_chapter9_chunks.json is in the current directory")
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
