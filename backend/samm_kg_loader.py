"""
================================================================================
SAMM JSON KNOWLEDGE GRAPH LOADER - v5.9.3
================================================================================

Loads the comprehensive JSON knowledge graph and integrates with:
- TwoHopPathFinder (2-hop RAG)
- IntegratedEntityAgent 
- SimpleKnowledgeGraph (existing)

USAGE:
------
# In app_5_9_2.py or app_5_9_3.py:

from samm_kg_loader import SAMMKnowledgeGraph, load_knowledge_graph

# Load the graph
kg = load_knowledge_graph("samm_knowledge_graph.json")

# Use with TwoHopPathFinder
path_finder = TwoHopPathFinder(
    knowledge_graph=kg,
    entity_relationships=kg.get_entity_relationships()
)

================================================================================
"""

import json
import os
from typing import Dict, List, Any, Optional, Set
from pathlib import Path


class SAMMKnowledgeGraph:
    """
    Comprehensive SAMM Knowledge Graph with JSON backend.
    
    Compatible with:
    - SimpleKnowledgeGraph interface (drop-in replacement)
    - TwoHopPathFinder 
    - IntegratedEntityAgent
    """
    
    def __init__(self, json_path: str = None, json_data: Dict = None):
        """
        Initialize from JSON file or dictionary.
        
        Args:
            json_path: Path to JSON knowledge graph file
            json_data: Pre-loaded JSON dictionary
        """
        self.entities = {}
        self.relationships = []
        self.authority_chains = {}
        self.question_mappings = {}
        self.metadata = {}
        
        # Entity indices for fast lookup
        self._entity_by_id = {}
        self._entity_by_label = {}
        self._relationships_by_source = {}
        self._relationships_by_target = {}
        
        if json_path:
            self._load_from_file(json_path)
        elif json_data:
            self._load_from_dict(json_data)
        
        self._build_indices()
        
        print(f"[SAMMKnowledgeGraph] Loaded: {len(self.entities)} entities, {len(self.relationships)} relationships")
    
    def _load_from_file(self, json_path: str):
        """Load knowledge graph from JSON file."""
        path = Path(json_path)
        
        if not path.exists():
            # Try relative to script location
            script_dir = Path(__file__).parent
            path = script_dir / json_path
        
        if not path.exists():
            print(f"[SAMMKnowledgeGraph] Warning: File not found: {json_path}")
            return
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self._load_from_dict(data)
    
    def _load_from_dict(self, data: Dict):
        """Load knowledge graph from dictionary."""
        self.metadata = data.get('metadata', {})
        
        # Flatten entities from categories
        entities_data = data.get('entities', {})
        for category, category_entities in entities_data.items():
            if isinstance(category_entities, dict):
                for entity_id, entity_data in category_entities.items():
                    entity_data['category'] = category
                    self.entities[entity_id] = self._convert_to_kg_format(entity_id, entity_data)
        
        # Load relationships
        for rel in data.get('relationships', []):
            self.relationships.append({
                'source': rel.get('source'),
                'target': rel.get('target'),
                'type': rel.get('type'),
                'description': rel.get('description', ''),
                'section': rel.get('section', ''),
                'weight': rel.get('weight', 5)
            })
        
        # Load authority chains
        self.authority_chains = data.get('authority_chains', {})
        
        # Load question mappings
        self.question_mappings = data.get('question_mappings', {})
    
    def _convert_to_kg_format(self, entity_id: str, entity_data: Dict) -> Dict:
        """Convert to SimpleKnowledgeGraph compatible format."""
        return {
            'id': entity_id,
            'type': entity_data.get('type', 'entity'),
            'properties': {
                'label': entity_data.get('label', entity_id),
                'definition': entity_data.get('definition', ''),
                'section': entity_data.get('section', ''),
                'role': entity_data.get('role', entity_data.get('definition', '')),
                'authority': entity_data.get('authority', ''),
                'category': entity_data.get('category', '')
            }
        }
    
    def _build_indices(self):
        """Build lookup indices for fast access."""
        # Entity indices
        for entity_id, entity in self.entities.items():
            self._entity_by_id[entity_id.lower()] = entity
            label = entity['properties'].get('label', '').lower()
            if label:
                self._entity_by_label[label] = entity
        
        # Relationship indices
        for rel in self.relationships:
            source = rel['source'].lower() if rel['source'] else ''
            target = rel['target'].lower() if rel['target'] else ''
            
            if source:
                if source not in self._relationships_by_source:
                    self._relationships_by_source[source] = []
                self._relationships_by_source[source].append(rel)
            
            if target:
                if target not in self._relationships_by_target:
                    self._relationships_by_target[target] = []
                self._relationships_by_target[target].append(rel)
    
    # =========================================================================
    # SimpleKnowledgeGraph Compatible Methods
    # =========================================================================
    
    def find_entity(self, query: str) -> Optional[Dict]:
        """Find entity by name or label (SimpleKnowledgeGraph compatible)."""
        query_lower = query.lower().strip()
        
        # Direct ID match
        if query_lower in self._entity_by_id:
            return self._entity_by_id[query_lower]
        
        # Label match
        if query_lower in self._entity_by_label:
            return self._entity_by_label[query_lower]
        
        # Partial match
        for entity_id, entity in self._entity_by_id.items():
            if query_lower in entity_id:
                return entity
        
        for label, entity in self._entity_by_label.items():
            if query_lower in label:
                return entity
        
        return None
    
    def get_relationships(self, entity_id: str) -> List[Dict]:
        """Get relationships for an entity (SimpleKnowledgeGraph compatible)."""
        entity_lower = entity_id.lower()
        relationships = []
        
        # Outgoing relationships
        if entity_lower in self._relationships_by_source:
            relationships.extend(self._relationships_by_source[entity_lower])
        
        # Incoming relationships
        if entity_lower in self._relationships_by_target:
            relationships.extend(self._relationships_by_target[entity_lower])
        
        return relationships
    
    # =========================================================================
    # Enhanced Methods for 2-Hop RAG
    # =========================================================================
    
    def get_entity_relationships(self) -> Dict[str, List[str]]:
        """
        Get entity relationships in format expected by TwoHopPathFinder.
        
        Returns:
            Dict mapping entity ID to list of relationship descriptions
        """
        result = {}
        
        for rel in self.relationships:
            source = rel['source']
            target = rel['target']
            rel_type = rel['type']
            
            # Create relationship text
            rel_text = f"{rel_type.replace('_', ' ')} {target}"
            
            if source not in result:
                result[source] = []
            result[source].append(rel_text)
        
        return result
    
    def get_outgoing_relationships(self, entity_id: str) -> List[Dict]:
        """Get only outgoing relationships from an entity."""
        entity_lower = entity_id.lower()
        return self._relationships_by_source.get(entity_lower, [])
    
    def get_incoming_relationships(self, entity_id: str) -> List[Dict]:
        """Get only incoming relationships to an entity."""
        entity_lower = entity_id.lower()
        return self._relationships_by_target.get(entity_lower, [])
    
    def get_authority_chain(self, entity_id: str) -> List[str]:
        """Get pre-defined authority chain for an entity."""
        for chain_id, chain_data in self.authority_chains.items():
            if entity_id.upper() in [e.upper() for e in chain_data.get('chain', [])]:
                return chain_data.get('chain', [])
        return []
    
    def find_path(self, source: str, target: str, max_hops: int = 3) -> List[Dict]:
        """
        Find path between two entities using BFS.
        
        Returns list of relationship dicts forming the path.
        """
        from collections import deque
        
        source_lower = source.lower()
        target_lower = target.lower()
        
        # BFS
        queue = deque([(source_lower, [])])
        visited = {source_lower}
        
        while queue:
            current, path = queue.popleft()
            
            if len(path) >= max_hops:
                continue
            
            for rel in self._relationships_by_source.get(current, []):
                next_entity = rel['target'].lower()
                
                if next_entity in visited:
                    continue
                
                new_path = path + [rel]
                
                if next_entity == target_lower:
                    return new_path
                
                visited.add(next_entity)
                queue.append((next_entity, new_path))
        
        return []
    
    def get_related_entities(self, entity_id: str, max_depth: int = 2) -> Set[str]:
        """Get all entities related within max_depth hops."""
        from collections import deque
        
        entity_lower = entity_id.lower()
        related = set()
        queue = deque([(entity_lower, 0)])
        visited = {entity_lower}
        
        while queue:
            current, depth = queue.popleft()
            
            if depth >= max_depth:
                continue
            
            # Outgoing
            for rel in self._relationships_by_source.get(current, []):
                target = rel['target'].lower()
                related.add(rel['target'])
                if target not in visited:
                    visited.add(target)
                    queue.append((target, depth + 1))
            
            # Incoming
            for rel in self._relationships_by_target.get(current, []):
                source = rel['source'].lower()
                related.add(rel['source'])
                if source not in visited:
                    visited.add(source)
                    queue.append((source, depth + 1))
        
        return related
    
    def get_supervision_chain(self, entity_id: str) -> List[Dict]:
        """
        Get supervision/authority chain for an entity.
        Specifically for questions like "Who supervises X?"
        """
        chain = []
        current = entity_id.lower()
        visited = {current}
        
        supervision_types = ['supervised_by', 'reports_to', 'managed_by', 'directed_by']
        
        for _ in range(5):  # Max 5 levels
            found = False
            for rel in self._relationships_by_source.get(current, []):
                if rel['type'] in supervision_types:
                    target = rel['target'].lower()
                    if target not in visited:
                        chain.append({
                            'from': current.upper(),
                            'to': rel['target'],
                            'type': rel['type'],
                            'section': rel.get('section', '')
                        })
                        visited.add(target)
                        current = target
                        found = True
                        break
            
            if not found:
                break
        
        return chain
    
    def query_for_answer(self, question_id: str) -> Dict:
        """Get pre-mapped answer guidance for known questions."""
        return self.question_mappings.get(question_id, {})
    
    def to_dict(self) -> Dict:
        """Export knowledge graph as dictionary."""
        return {
            'metadata': self.metadata,
            'entities': {eid: e['properties'] for eid, e in self.entities.items()},
            'relationships': self.relationships,
            'authority_chains': self.authority_chains,
            'question_mappings': self.question_mappings
        }
    
    def get_stats(self) -> Dict:
        """Get knowledge graph statistics."""
        entity_types = {}
        for entity in self.entities.values():
            etype = entity.get('type', 'unknown')
            entity_types[etype] = entity_types.get(etype, 0) + 1
        
        rel_types = {}
        for rel in self.relationships:
            rtype = rel.get('type', 'unknown')
            rel_types[rtype] = rel_types.get(rtype, 0) + 1
        
        return {
            'total_entities': len(self.entities),
            'total_relationships': len(self.relationships),
            'entity_types': entity_types,
            'relationship_types': rel_types,
            'authority_chains': len(self.authority_chains),
            'question_mappings': len(self.question_mappings)
        }


def load_knowledge_graph(json_path: str = "samm_knowledge_graph.json") -> SAMMKnowledgeGraph:
    """
    Convenience function to load knowledge graph.
    
    Args:
        json_path: Path to JSON file
        
    Returns:
        SAMMKnowledgeGraph instance
    """
    return SAMMKnowledgeGraph(json_path=json_path)


# =============================================================================
# INTEGRATION CODE
# =============================================================================

def create_combined_knowledge_graph(json_kg: SAMMKnowledgeGraph, ttl_kg) -> SAMMKnowledgeGraph:
    """
    Combine JSON knowledge graph with existing TTL-based SimpleKnowledgeGraph.
    
    Args:
        json_kg: SAMMKnowledgeGraph from JSON
        ttl_kg: SimpleKnowledgeGraph from TTL
        
    Returns:
        Combined SAMMKnowledgeGraph
    """
    # Add TTL entities not in JSON
    for entity_id, entity in ttl_kg.entities.items():
        if entity_id not in json_kg.entities:
            json_kg.entities[entity_id] = entity
            json_kg._entity_by_id[entity_id.lower()] = entity
    
    # Add TTL relationships not in JSON
    existing_rels = {(r['source'], r['target'], r['type']) for r in json_kg.relationships}
    
    for rel in ttl_kg.relationships:
        rel_key = (rel.get('source'), rel.get('target'), rel.get('relationship', rel.get('type')))
        if rel_key not in existing_rels:
            json_kg.relationships.append({
                'source': rel.get('source'),
                'target': rel.get('target'),
                'type': rel.get('relationship', rel.get('type')),
                'description': '',
                'section': '',
                'weight': 5
            })
    
    # Rebuild indices
    json_kg._build_indices()
    
    print(f"[Combined KG] Total: {len(json_kg.entities)} entities, {len(json_kg.relationships)} relationships")
    return json_kg


# =============================================================================
# TEST
# =============================================================================

def test_knowledge_graph():
    """Test the knowledge graph functionality."""
    print("\n" + "="*60)
    print("TESTING SAMM KNOWLEDGE GRAPH")
    print("="*60)
    
    # Load graph
    kg = SAMMKnowledgeGraph(json_path="samm_knowledge_graph.json")
    
    # Print stats
    stats = kg.get_stats()
    print(f"\n📊 Statistics:")
    print(f"   Entities: {stats['total_entities']}")
    print(f"   Relationships: {stats['total_relationships']}")
    print(f"   Entity types: {stats['entity_types']}")
    
    # Test Q4: Who supervises SA?
    print(f"\n🔍 Test: Who supervises SA?")
    
    # Find SA entity
    sa_entity = kg.find_entity("SA")
    if sa_entity:
        print(f"   Found SA: {sa_entity['properties'].get('label')}")
        print(f"   Definition: {sa_entity['properties'].get('definition', '')[:100]}...")
    
    # Get supervision chain
    chain = kg.get_supervision_chain("SA")
    if chain:
        print(f"   Supervision chain:")
        for step in chain:
            print(f"      {step['from']} --[{step['type']}]--> {step['to']}")
    
    # Get SA relationships
    sa_rels = kg.get_relationships("SA")
    print(f"   SA has {len(sa_rels)} relationships")
    for rel in sa_rels[:5]:
        print(f"      • {rel['source']} --[{rel['type']}]--> {rel['target']}")
    
    # Test path finding
    print(f"\n🔍 Test: Path from SA to SECDEF")
    path = kg.find_path("SA", "SECDEF")
    if path:
        print(f"   Path found ({len(path)} hops):")
        for rel in path:
            print(f"      {rel['source']} --[{rel['type']}]--> {rel['target']}")
    else:
        print("   No direct path found")
    
    # Test related entities
    print(f"\n🔍 Test: Entities related to DSCA (2 hops)")
    related = kg.get_related_entities("DSCA", max_depth=2)
    print(f"   Found {len(related)} related entities: {list(related)[:10]}...")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    test_knowledge_graph()
