"""
================================================================================
2-HOP PATH RAG IMPLEMENTATION - Version 5.9.3
================================================================================

INTEGRATION INSTRUCTIONS:
-------------------------
Add this code to app_5_9_2.py to enable 2-hop relationship traversal.

CHANGES SUMMARY:
1. New TwoHopPathFinder class - Traverses relationship chains
2. Enhanced IntegratedEntityAgent._extract_entities_enhanced() - Better entity matching
3. Enhanced _get_comprehensive_relationships() - 2-hop path retrieval  
4. New _build_relationship_graph() - Graph structure for traversal
5. New _find_2hop_paths() - BFS-based path finding
6. Updated prompt generation with path context

EXPECTED IMPROVEMENTS:
- Q4 "Who supervises SA?" should now find: SA → supervised_by → SECSTATE → USD(P) chain
- Questions about authority chains should have complete context
- Relationship questions should find indirect connections

================================================================================
"""

import re
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, deque
from datetime import datetime

# =============================================================================
# 2-HOP PATH RAG CLASS
# =============================================================================

class TwoHopPathFinder:
    """
    Two-Hop Path RAG Implementation
    
    Finds relationship paths like:
    - SA → supervised_by → Secretary of State → reports_to → USD(P)
    - DSCA → reports_to → USD(P) → advises → SECDEF
    
    Uses BFS to find all paths up to 2 hops from source entities.
    """
    
    # Relationship type synonyms for matching
    RELATIONSHIP_SYNONYMS = {
        "supervised_by": ["supervises", "supervision", "oversees", "oversight", "direction"],
        "reports_to": ["reports_to", "reports", "subordinate_to", "under"],
        "directs": ["directs", "manages", "administers", "controls"],
        "responsible_for": ["responsible_for", "handles", "manages"],
        "approves": ["approves", "authorizes", "signs"],
        "coordinates_with": ["coordinates_with", "works_with", "collaborates"],
        "subset_of": ["subset_of", "part_of", "included_in", "within"],
        "authorized_by": ["authorized_by", "enabled_by", "pursuant_to"],
        "implements": ["implements", "executes", "carries_out"],
        "funds": ["funds", "finances", "provides_funding_for"],
    }
    
    # Priority weights for relationship types (higher = more important)
    RELATIONSHIP_PRIORITY = {
        "supervised_by": 10,
        "reports_to": 9,
        "directs": 9,
        "responsible_for": 8,
        "approves": 8,
        "authorized_by": 7,
        "coordinates_with": 5,
        "subset_of": 6,
        "implements": 6,
        "funds": 5,
        "default": 3
    }
    
    def __init__(self, knowledge_graph=None, entity_relationships: Dict = None):
        """
        Initialize the path finder with relationship data sources.
        
        Args:
            knowledge_graph: SimpleKnowledgeGraph instance
            entity_relationships: Dictionary of entity -> relationships
        """
        self.knowledge_graph = knowledge_graph
        self.entity_relationships = entity_relationships or {}
        self.relationship_graph = {}
        self.reverse_graph = {}  # For bidirectional traversal
        self._build_graphs()
        
        print(f"[TwoHopPathFinder] Initialized with {len(self.relationship_graph)} entities in graph")
    
    def _build_graphs(self):
        """Build forward and reverse relationship graphs from all sources."""
        
        # Build from knowledge_graph relationships
        if self.knowledge_graph:
            for rel in self.knowledge_graph.relationships:
                source = rel.get('source', '').lower()
                target = rel.get('target', '').lower()
                rel_type = rel.get('type', 'related_to')
                
                if source and target:
                    if source not in self.relationship_graph:
                        self.relationship_graph[source] = []
                    self.relationship_graph[source].append({
                        'target': target,
                        'type': rel_type,
                        'source_system': 'knowledge_graph'
                    })
                    
                    # Build reverse graph
                    if target not in self.reverse_graph:
                        self.reverse_graph[target] = []
                    self.reverse_graph[target].append({
                        'source': source,
                        'type': self._reverse_relationship(rel_type),
                        'source_system': 'knowledge_graph'
                    })
        
        # Build from entity_relationships dictionary
        for entity, relationships in self.entity_relationships.items():
            entity_lower = entity.lower()
            if entity_lower not in self.relationship_graph:
                self.relationship_graph[entity_lower] = []
            
            for rel_text in relationships:
                # Parse relationship text like "reports to USD(P)"
                parsed = self._parse_relationship_text(entity, rel_text)
                if parsed:
                    self.relationship_graph[entity_lower].append(parsed)
                    
                    # Add reverse edge
                    target = parsed['target']
                    if target not in self.reverse_graph:
                        self.reverse_graph[target] = []
                    self.reverse_graph[target].append({
                        'source': entity_lower,
                        'type': self._reverse_relationship(parsed['type']),
                        'source_system': 'entity_relationships'
                    })
        
        print(f"[TwoHopPathFinder] Built graphs: {len(self.relationship_graph)} forward, {len(self.reverse_graph)} reverse")
    
    def _parse_relationship_text(self, entity: str, rel_text: str) -> Optional[Dict]:
        """Parse relationship text like 'reports to USD(P)' into structured format."""
        rel_text_lower = rel_text.lower()
        
        # Common patterns
        patterns = [
            (r'reports to ([\w\(\)\-\/&\s]+)', 'reports_to'),
            (r'supervised by ([\w\(\)\-\/&\s]+)', 'supervised_by'),
            (r'subject to.*supervision.*of ([\w\(\)\-\/&\s]+)', 'supervised_by'),
            (r'directs ([\w\(\)\-\/&\s]+)', 'directs'),
            (r'administers ([\w\(\)\-\/&\s]+)', 'administers'),
            (r'responsible for ([\w\(\)\-\/&\s]+)', 'responsible_for'),
            (r'approves ([\w\(\)\-\/&\s]+)', 'approves'),
            (r'authorized (?:by|under) ([\w\(\)\-\/&\s]+)', 'authorized_by'),
            (r'coordinates with ([\w\(\)\-\/&\s]+)', 'coordinates_with'),
            (r'subset of ([\w\(\)\-\/&\s]+)', 'subset_of'),
            (r'part of ([\w\(\)\-\/&\s]+)', 'subset_of'),
            (r'under ([\w\(\)\-\/&\s]+)', 'reports_to'),
        ]
        
        for pattern, rel_type in patterns:
            match = re.search(pattern, rel_text_lower)
            if match:
                target = match.group(1).strip()
                # Clean up target
                target = re.sub(r'\s+', ' ', target)
                target = target.rstrip('.,;')
                return {
                    'target': target,
                    'type': rel_type,
                    'original_text': rel_text,
                    'source_system': 'entity_relationships'
                }
        
        return None
    
    def _reverse_relationship(self, rel_type: str) -> str:
        """Get the reverse of a relationship type."""
        reverse_map = {
            'reports_to': 'receives_reports_from',
            'supervised_by': 'supervises',
            'directs': 'directed_by',
            'administers': 'administered_by',
            'responsible_for': 'responsibility_of',
            'approves': 'approved_by',
            'authorized_by': 'authorizes',
            'coordinates_with': 'coordinates_with',  # Symmetric
            'subset_of': 'contains',
        }
        return reverse_map.get(rel_type, f'reverse_{rel_type}')
    
    def _normalize_entity(self, entity: str) -> str:
        """Normalize entity name for matching."""
        entity_lower = entity.lower().strip()
        
        # Common normalizations
        normalizations = {
            'security assistance': 'sa',
            'security cooperation': 'sc',
            'secretary of state': 'secstate',
            'secretary of defense': 'secdef',
            'defense security cooperation agency': 'dsca',
            'defense finance and accounting service': 'dfas',
            'under secretary of defense for policy': 'usd(p)',
            'foreign military sales': 'fms',
            'foreign military financing': 'fmf',
        }
        
        # Try exact match first
        if entity_lower in normalizations:
            return normalizations[entity_lower]
        
        # Check if it's already an acronym
        return entity_lower
    
    def find_paths(self, source_entity: str, max_hops: int = 2, 
                   target_entity: str = None, query_intent: str = None) -> List[Dict]:
        """
        Find all relationship paths from source entity up to max_hops.
        
        Args:
            source_entity: Starting entity
            max_hops: Maximum path length (default 2)
            target_entity: Optional target to find specific paths
            query_intent: Query intent to prioritize relevant relationships
            
        Returns:
            List of paths, each containing:
            - path: List of (entity, relationship, entity) tuples
            - total_weight: Sum of relationship priorities
            - relevant_to_intent: Whether path matches query intent
        """
        source_norm = self._normalize_entity(source_entity)
        paths = []
        
        # BFS to find all paths up to max_hops
        queue = deque()
        
        # Each queue item: (current_entity, current_path, visited)
        queue.append((source_norm, [], {source_norm}))
        
        while queue:
            current, current_path, visited = queue.popleft()
            
            if len(current_path) >= max_hops:
                continue
            
            # Get outgoing edges from forward graph
            for edge in self.relationship_graph.get(current, []):
                target = edge['target']
                
                if target in visited:
                    continue
                
                new_path = current_path + [{
                    'from': current,
                    'to': target,
                    'type': edge['type'],
                    'source_system': edge.get('source_system', 'unknown')
                }]
                
                new_visited = visited | {target}
                
                # If we found target or reached max depth, save path
                if target_entity and self._normalize_entity(target_entity) == target:
                    paths.append(self._format_path(new_path, query_intent))
                elif len(new_path) <= max_hops:
                    paths.append(self._format_path(new_path, query_intent))
                    
                # Continue BFS if not at max depth
                if len(new_path) < max_hops:
                    queue.append((target, new_path, new_visited))
        
        # Sort paths by weight (most relevant first)
        paths.sort(key=lambda p: p['total_weight'], reverse=True)
        
        print(f"[TwoHopPathFinder] Found {len(paths)} paths from '{source_entity}'")
        return paths[:10]  # Return top 10 paths
    
    def _format_path(self, path: List[Dict], query_intent: str = None) -> Dict:
        """Format a path with metadata for use in context."""
        total_weight = 0
        path_text_parts = []
        
        for i, edge in enumerate(path):
            # Calculate weight
            rel_type = edge['type']
            weight = self.RELATIONSHIP_PRIORITY.get(rel_type, self.RELATIONSHIP_PRIORITY['default'])
            total_weight += weight
            
            # Build readable path
            if i == 0:
                path_text_parts.append(f"{edge['from'].upper()}")
            path_text_parts.append(f" --[{rel_type}]--> {edge['to'].upper()}")
        
        # Check relevance to query intent
        relevant = self._check_intent_relevance(path, query_intent)
        if relevant:
            total_weight += 5  # Bonus for relevance
        
        return {
            'path': path,
            'path_text': ''.join(path_text_parts),
            'total_weight': total_weight,
            'relevant_to_intent': relevant,
            'hop_count': len(path),
            'entities_in_path': [path[0]['from']] + [edge['to'] for edge in path]
        }
    
    def _check_intent_relevance(self, path: List[Dict], query_intent: str) -> bool:
        """Check if path is relevant to query intent."""
        if not query_intent:
            return False
        
        query_intent_lower = query_intent.lower()
        
        # Map intents to relevant relationship types
        intent_rel_map = {
            'authority': ['supervised_by', 'reports_to', 'directs', 'approves', 'authorized_by'],
            'supervision': ['supervised_by', 'reports_to', 'directs', 'oversight'],
            'organization': ['reports_to', 'part_of', 'subset_of', 'responsible_for'],
            'relationship': ['reports_to', 'coordinates_with', 'subset_of'],
            'role': ['responsible_for', 'directs', 'administers'],
        }
        
        relevant_rels = intent_rel_map.get(query_intent_lower, [])
        
        for edge in path:
            if edge['type'] in relevant_rels:
                return True
        
        return False
    
    def find_authority_chain(self, entity: str) -> List[Dict]:
        """
        Special method to find authority/supervision chain for an entity.
        
        For "Who supervises SA?", this finds:
        SA → supervised_by → Secretary of State → reports_to → ...
        """
        entity_norm = self._normalize_entity(entity)
        chain = []
        visited = {entity_norm}
        current = entity_norm
        
        # Follow supervision/reporting chain upward
        authority_rels = ['supervised_by', 'reports_to', 'directed_by', 'under']
        
        for _ in range(5):  # Max 5 levels up
            found_next = False
            
            for edge in self.relationship_graph.get(current, []):
                if edge['type'] in authority_rels and edge['target'] not in visited:
                    chain.append({
                        'from': current,
                        'to': edge['target'],
                        'type': edge['type'],
                        'source_system': edge.get('source_system', 'unknown')
                    })
                    visited.add(edge['target'])
                    current = edge['target']
                    found_next = True
                    break
            
            if not found_next:
                break
        
        print(f"[TwoHopPathFinder] Authority chain for '{entity}': {len(chain)} levels")
        return chain
    
    def get_context_for_query(self, entities: List[str], query: str, 
                              intent: str = None) -> Dict[str, Any]:
        """
        Main method to get 2-hop context for a query.
        
        Args:
            entities: List of entities extracted from query
            query: Original query text
            intent: Detected intent
            
        Returns:
            Dictionary with:
            - paths: All discovered paths
            - authority_chains: Authority chains for entities
            - context_text: Formatted context for LLM
            - relationship_summary: Summary of relationships found
        """
        all_paths = []
        authority_chains = {}
        entities_found = set()
        
        query_lower = query.lower()
        
        # Determine if this is an authority/supervision question
        is_authority_question = any(term in query_lower for term in [
            'supervise', 'supervision', 'authority', 'oversee', 'oversight',
            'reports to', 'responsible', 'who', 'manages', 'directs'
        ])
        
        for entity in entities:
            # Find general 2-hop paths
            paths = self.find_paths(entity, max_hops=2, query_intent=intent)
            all_paths.extend(paths)
            
            # For authority questions, also get authority chain
            if is_authority_question:
                chain = self.find_authority_chain(entity)
                if chain:
                    authority_chains[entity] = chain
            
            # Collect all entities found
            for path in paths:
                entities_found.update(path.get('entities_in_path', []))
        
        # Build context text for LLM
        context_text = self._build_context_text(entities, all_paths, authority_chains, query)
        
        return {
            'paths': all_paths,
            'authority_chains': authority_chains,
            'context_text': context_text,
            'entities_found': list(entities_found),
            'relationship_count': len(all_paths),
            'is_authority_question': is_authority_question
        }
    
    def _build_context_text(self, entities: List[str], paths: List[Dict], 
                           authority_chains: Dict, query: str) -> str:
        """Build formatted context text for inclusion in LLM prompt."""
        lines = []
        
        lines.append("=== 2-HOP RELATIONSHIP CONTEXT ===")
        lines.append("")
        
        # Add authority chains if present
        if authority_chains:
            lines.append("AUTHORITY/SUPERVISION CHAIN:")
            for entity, chain in authority_chains.items():
                if chain:
                    chain_parts = [chain[0]['from'].upper()]
                    for edge in chain:
                        chain_parts.append(f" → ({edge['type']}) → {edge['to'].upper()}")
                    lines.append(f"  {entity.upper()}: {''.join(chain_parts)}")
            lines.append("")
        
        # Add top relationship paths
        if paths:
            lines.append("KEY RELATIONSHIP PATHS:")
            seen_paths = set()
            for path in paths[:8]:  # Top 8 paths
                path_text = path['path_text']
                if path_text not in seen_paths:
                    seen_paths.add(path_text)
                    relevance = " (RELEVANT)" if path['relevant_to_intent'] else ""
                    lines.append(f"  • {path_text}{relevance}")
            lines.append("")
        
        # Add relationship summary
        if paths or authority_chains:
            lines.append("RELATIONSHIP SUMMARY:")
            
            # Summarize key findings
            all_targets = set()
            rel_types = defaultdict(int)
            
            for path in paths:
                for edge in path['path']:
                    all_targets.add(edge['to'])
                    rel_types[edge['type']] += 1
            
            for entity, chain in authority_chains.items():
                for edge in chain:
                    all_targets.add(edge['to'])
                    rel_types[edge['type']] += 1
            
            if 'supervised_by' in rel_types or 'reports_to' in rel_types:
                # Find the top authority
                if authority_chains:
                    for entity, chain in authority_chains.items():
                        if chain:
                            top_authority = chain[-1]['to']
                            lines.append(f"  • {entity.upper()} is ultimately under {top_authority.upper()}")
            
            lines.append(f"  • Connected entities: {', '.join(sorted(all_targets)[:10])}")
        
        lines.append("=== END 2-HOP CONTEXT ===")
        
        return '\n'.join(lines)
    
    def add_relationship(self, source: str, target: str, rel_type: str):
        """Add a new relationship to the graph."""
        source_norm = self._normalize_entity(source)
        target_norm = self._normalize_entity(target)
        
        if source_norm not in self.relationship_graph:
            self.relationship_graph[source_norm] = []
        
        self.relationship_graph[source_norm].append({
            'target': target_norm,
            'type': rel_type,
            'source_system': 'dynamic'
        })
        
        # Add reverse
        if target_norm not in self.reverse_graph:
            self.reverse_graph[target_norm] = []
        
        self.reverse_graph[target_norm].append({
            'source': source_norm,
            'type': self._reverse_relationship(rel_type),
            'source_system': 'dynamic'
        })


# =============================================================================
# ENHANCED SAMM RELATIONSHIP DATA
# =============================================================================

# Add these to the existing entity_relationships in IntegratedEntityAgent
ENHANCED_SAMM_RELATIONSHIPS = {
    # Security Assistance relationships (critical for Q4)
    "SA": [
        "supervised by Secretary of State",
        "subject to continuous supervision and general direction of SECSTATE",
        "authorized under Title 22",
        "subset of Security Cooperation",
        "administered by DoD",
        "includes FMS, IMET, FMF, EDA programs"
    ],
    "Security Assistance": [
        "supervised by Secretary of State",
        "subject to continuous supervision and general direction of SECSTATE",
        "authorized under Title 22",
        "subset of Security Cooperation",
        "administered by DoD",
        "includes FMS, IMET, FMF, EDA programs"
    ],
    
    # Secretary of State relationships
    "Secretary of State": [
        "supervises Security Assistance programs",
        "provides continuous supervision and general direction",
        "approves export licenses",
        "determines FMS eligibility",
        "coordinates with Secretary of Defense"
    ],
    "SECSTATE": [
        "supervises Security Assistance programs",
        "provides continuous supervision and general direction of SA",
        "approves export licenses",
        "determines FMS eligibility",
        "coordinates with SECDEF"
    ],
    
    # DSCA relationships
    "DSCA": [
        "reports to USD(P)",
        "directs DoD SC activities",
        "administers FMS program",
        "Executive Agent for Regional Centers",
        "implements SA policy"
    ],
    "Defense Security Cooperation Agency": [
        "reports to USD(P)",
        "directs DoD SC activities",
        "administers FMS program",
        "Executive Agent for Regional Centers",
        "implements SA policy"
    ],
    
    # USD(P) relationships  
    "USD(P)": [
        "reports to SECDEF",
        "principal staff assistant on SC matters",
        "oversees DSCA",
        "develops SC policy guidance",
        "issues Guidance for Employment of the Force (GEF)"
    ],
    "Under Secretary of Defense for Policy": [
        "reports to Secretary of Defense",
        "principal staff assistant on SC matters",
        "oversees DSCA",
        "develops SC policy guidance"
    ],
    
    # Security Cooperation relationships
    "SC": [
        "authorized under Title 10",
        "includes Security Assistance as subset",
        "managed by Secretary of Defense",
        "implemented by DSCA"
    ],
    "Security Cooperation": [
        "authorized under Title 10",
        "includes Security Assistance as subset",
        "managed by Secretary of Defense",
        "implemented by DSCA"
    ],
    
    # SECDEF relationships
    "SECDEF": [
        "oversees Security Cooperation",
        "receives reports from USD(P)",
        "coordinates with Secretary of State on SA",
        "implements SA programs through DoD"
    ],
    "Secretary of Defense": [
        "oversees Security Cooperation",
        "receives reports from USD(P)",
        "coordinates with Secretary of State on SA",
        "implements SA programs through DoD"
    ],
    
    # DFAS relationships
    "DFAS": [
        "reports to USD(C)",
        "performs accounting for SC programs",
        "handles billing and disbursing",
        "primary site at DFAS-IN"
    ],
    
    # Title relationships
    "Title 22": [
        "authorizes Security Assistance",
        "includes FAA and AECA",
        "provides SA authorities"
    ],
    "Title 10": [
        "authorizes Security Cooperation",
        "provides NDAA authorities",
        "enables DoD SC programs"
    ],
    
    # Legal authorities
    "FAA": [
        "authorizes Security Assistance",
        "Foreign Assistance Act of 1961",
        "Title 22 authority"
    ],
    "Foreign Assistance Act": [
        "authorizes Security Assistance",
        "enacted 1961",
        "Title 22 authority"
    ],
    "AECA": [
        "authorizes FMS and related programs",
        "Arms Export Control Act of 1976",
        "Title 22 authority"
    ],
    "Arms Export Control Act": [
        "authorizes FMS and related programs",
        "enacted 1976",
        "Title 22 authority"
    ],
    
    # Executive Order
    "E.O. 13637": [
        "delegates SA authority from President",
        "allocates SA responsibility to SECDEF and SECSTATE",
        "further delegated to USD(P) and DSCA"
    ],
    "Executive Order 13637": [
        "delegates SA authority from President",
        "allocates SA responsibility to SECDEF and SECSTATE",
        "further delegated to USD(P) and DSCA"
    ],
}


# =============================================================================
# EXACT STRING MATCH FIX FOR ENTITY EXTRACTION
# =============================================================================

def enhanced_entity_extraction_fix(query: str, samm_entity_patterns: Dict) -> List[str]:
    """
    Enhanced entity extraction with exact acronym matching.
    
    FIXES the substring matching bug where:
    - "SA" matches "SAMM", "USAID", etc.
    - "SC" matches "DSCA", "ASCAR", etc.
    
    Uses word boundary matching for acronyms.
    """
    entities = []
    query_lower = query.lower()
    query_upper = query.upper()
    
    # HIGH PRIORITY: Exact acronym matching with word boundaries
    EXACT_ACRONYMS = {
        # Two-letter acronyms (most problematic)
        'SA': ['security assistance'],
        'SC': ['security cooperation'],
        'EO': ['executive order'],
        'EA': ['executive agent'],
        
        # Three+ letter acronyms
        'FMS': ['foreign military sales'],
        'FMF': ['foreign military financing'],
        'IMET': ['international military education and training'],
        'EDA': ['excess defense articles'],
        'DCS': ['direct commercial sales'],
        'FAA': ['foreign assistance act'],
        'AECA': ['arms export control act'],
        'NDAA': ['national defense authorization act'],
        'DSCA': ['defense security cooperation agency'],
        'DFAS': ['defense finance and accounting service'],
        'SECDEF': ['secretary of defense'],
        'SECSTATE': ['secretary of state'],
        'USD(P)': ['under secretary of defense for policy'],
        'USML': ['united states munitions list'],
        'ITAR': ['international traffic in arms regulations'],
    }
    
    # Check for exact acronyms with word boundaries
    for acronym, full_forms in EXACT_ACRONYMS.items():
        # Build word boundary pattern
        # Handle special characters in acronyms like USD(P)
        acronym_escaped = re.escape(acronym)
        pattern = rf'\b{acronym_escaped}\b'
        
        if re.search(pattern, query_upper, re.IGNORECASE):
            entities.append(acronym)
            print(f"[EntityFix] Exact match: '{acronym}' in query")
            continue
        
        # Also check for full forms
        for full_form in full_forms:
            if full_form in query_lower:
                entities.append(acronym)  # Normalize to acronym
                print(f"[EntityFix] Full form match: '{full_form}' -> '{acronym}'")
                break
    
    # Check for other entities from patterns (existing logic)
    for category, patterns in samm_entity_patterns.items():
        for pattern in patterns:
            pattern_lower = pattern.lower()
            
            # Skip if it's a short acronym (handled above)
            if len(pattern) <= 3 and pattern.upper() in EXACT_ACRONYMS:
                continue
            
            # Use word boundary for short patterns
            if len(pattern) <= 5:
                pattern_escaped = re.escape(pattern_lower)
                if re.search(rf'\b{pattern_escaped}\b', query_lower):
                    if pattern not in entities:
                        entities.append(pattern)
            else:
                # Longer patterns can use simple contains
                if pattern_lower in query_lower:
                    if pattern not in entities:
                        entities.append(pattern)
    
    return entities


# =============================================================================
# INTEGRATION CODE FOR IntegratedEntityAgent
# =============================================================================

def integrate_two_hop_rag(entity_agent_instance, knowledge_graph, entity_relationships: Dict):
    """
    Integrate 2-hop RAG into an IntegratedEntityAgent instance.
    
    Call this after creating the IntegratedEntityAgent:
        integrate_two_hop_rag(orchestrator.entity_agent, knowledge_graph, entity_relationships)
    """
    
    # Merge enhanced relationships
    all_relationships = {**entity_relationships, **ENHANCED_SAMM_RELATIONSHIPS}
    
    # Create path finder
    entity_agent_instance.path_finder = TwoHopPathFinder(
        knowledge_graph=knowledge_graph,
        entity_relationships=all_relationships
    )
    
    # Store reference to enhanced extraction
    entity_agent_instance.enhanced_entity_extraction = enhanced_entity_extraction_fix
    
    print("[Integration] 2-Hop Path RAG integrated successfully")
    return entity_agent_instance


# =============================================================================
# UPDATED _get_comprehensive_relationships METHOD
# =============================================================================

def get_comprehensive_relationships_with_2hop(
    self,  # IntegratedEntityAgent instance
    entities: List[str], 
    data_sources: Dict
) -> List[str]:
    """
    Enhanced relationship retrieval with 2-hop path finding.
    
    This replaces the original _get_comprehensive_relationships method.
    """
    relationships = []
    
    # === EXISTING 1-HOP LOGIC ===
    
    # Add relationships from knowledge graph
    if self.knowledge_graph:
        for entity in entities:
            entity_lower = entity.lower()
            for rel in self.knowledge_graph.relationships:
                if (rel['source'].lower() == entity_lower or 
                    rel['target'].lower() == entity_lower):
                    rel_text = f"{rel['source']} {rel['type']} {rel['target']} (from SAMM)"
                    if rel_text not in relationships:
                        relationships.append(rel_text)
    
    # Add predefined relationships
    for entity in entities:
        if entity in self.entity_relationships:
            for relationship in self.entity_relationships[entity]:
                rel_text = f"{entity} {relationship}"
                if rel_text not in relationships:
                    relationships.append(rel_text)
    
    # === NEW 2-HOP LOGIC ===
    
    if hasattr(self, 'path_finder') and self.path_finder:
        # Get current query from context (stored during extract_entities)
        query = getattr(self, 'current_query', '')
        intent = getattr(self, 'current_intent', None)
        
        # Get 2-hop context
        two_hop_context = self.path_finder.get_context_for_query(
            entities=entities,
            query=query,
            intent=intent
        )
        
        # Add 2-hop paths as relationship text
        for path in two_hop_context.get('paths', [])[:5]:
            rel_text = f"[2-HOP PATH] {path['path_text']}"
            if rel_text not in relationships:
                relationships.append(rel_text)
        
        # Add authority chain information
        for entity, chain in two_hop_context.get('authority_chains', {}).items():
            if chain:
                chain_text = f"[AUTHORITY CHAIN] {entity.upper()}"
                for edge in chain:
                    chain_text += f" → {edge['to'].upper()}"
                if chain_text not in relationships:
                    relationships.append(chain_text)
        
        # Store context for prompt building
        self.two_hop_context = two_hop_context
    
    # === EXISTING DB LOGIC ===
    
    # Add relationships from Cosmos DB Gremlin results
    cosmos_results = data_sources.get("cosmos_gremlin", {}).get("results", [])
    for result in cosmos_results:
        if result.get("type") == "edge":
            edge_data = result.get("data", {})
            if isinstance(edge_data, dict):
                label = edge_data.get("label", "relates_to")
                from_name = edge_data.get("from_name", edge_data.get("outV", "unknown"))
                to_name = edge_data.get("to_name", edge_data.get("inV", "unknown"))
                rel_text = f"{from_name} {label} {to_name}"
                if rel_text not in relationships:
                    relationships.append(rel_text)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_relationships = []
    for rel in relationships:
        if rel not in seen:
            seen.add(rel)
            unique_relationships.append(rel)
    
    print(f"[IntegratedEntityAgent] Total relationships found (with 2-hop): {len(unique_relationships)}")
    return unique_relationships


# =============================================================================
# UPDATED PROMPT BUILDING WITH 2-HOP CONTEXT
# =============================================================================

def build_prompt_with_2hop_context(
    query: str,
    intent_info: Dict,
    entity_info: Dict,
    two_hop_context: Dict = None
) -> str:
    """
    Build LLM prompt with 2-hop relationship context included.
    """
    prompt_parts = []
    
    # Add query
    prompt_parts.append(f"USER QUESTION: {query}")
    prompt_parts.append("")
    
    # Add intent
    intent = intent_info.get('intent', 'general')
    prompt_parts.append(f"DETECTED INTENT: {intent}")
    prompt_parts.append("")
    
    # Add entities
    entities = entity_info.get('entities', [])
    if entities:
        prompt_parts.append(f"KEY ENTITIES: {', '.join(entities)}")
        prompt_parts.append("")
    
    # === ADD 2-HOP CONTEXT ===
    if two_hop_context and two_hop_context.get('context_text'):
        prompt_parts.append(two_hop_context['context_text'])
        prompt_parts.append("")
    
    # Add traditional relationships
    relationships = entity_info.get('relationships', [])
    if relationships:
        prompt_parts.append("DIRECT RELATIONSHIPS:")
        for rel in relationships[:10]:
            if not rel.startswith('[2-HOP') and not rel.startswith('[AUTHORITY'):
                prompt_parts.append(f"  • {rel}")
        prompt_parts.append("")
    
    # Add text context
    text_sections = entity_info.get('text_sections', [])
    if text_sections:
        prompt_parts.append("RELEVANT SAMM TEXT:")
        for section in text_sections[:5]:
            content = section.get('content', section) if isinstance(section, dict) else section
            if content:
                prompt_parts.append(f"  {content[:500]}...")
        prompt_parts.append("")
    
    # Add citations
    citations = entity_info.get('citations', {})
    if citations.get('primary'):
        prompt_parts.append(f"PRIMARY CITATION: {citations['primary']}")
        if citations.get('references'):
            prompt_parts.append(f"ADDITIONAL REFERENCES: {', '.join(citations['references'])}")
        prompt_parts.append("")
    
    return '\n'.join(prompt_parts)


# =============================================================================
# INSTALLATION INSTRUCTIONS
# =============================================================================

INSTALLATION_INSTRUCTIONS = """
================================================================================
INSTALLATION INSTRUCTIONS FOR 2-HOP PATH RAG
================================================================================

1. ADD THIS FILE TO YOUR PROJECT:
   - Save as: two_hop_path_rag_v5_9_3.py
   - Place in same directory as app_5_9_2.py

2. IMPORT IN app_5_9_2.py:
   Add after other imports (around line 90):
   
   ```python
   from two_hop_path_rag_v5_9_3 import (
       TwoHopPathFinder,
       ENHANCED_SAMM_RELATIONSHIPS,
       enhanced_entity_extraction_fix,
       integrate_two_hop_rag,
       get_comprehensive_relationships_with_2hop,
       build_prompt_with_2hop_context
   )
   ```

3. INTEGRATE INTO IntegratedEntityAgent.__init__():
   Add at the end of __init__ (around line 5200):
   
   ```python
   # Initialize 2-Hop Path Finder
   all_relationships = {**self.entity_relationships, **ENHANCED_SAMM_RELATIONSHIPS}
   self.path_finder = TwoHopPathFinder(
       knowledge_graph=knowledge_graph,
       entity_relationships=all_relationships
   )
   self.two_hop_context = None
   self.current_query = ""
   self.current_intent = None
   print("[IntegratedEntityAgent] 2-Hop Path RAG initialized")
   ```

4. UPDATE extract_entities() METHOD:
   At the start of the method, add:
   
   ```python
   # Store for 2-hop context
   self.current_query = query
   self.current_intent = intent_info.get('intent') if intent_info else None
   ```

5. UPDATE _get_comprehensive_relationships() METHOD:
   Replace the method with get_comprehensive_relationships_with_2hop from this file,
   OR add the 2-hop logic after the existing relationship gathering.

6. UPDATE PROMPT BUILDING IN orchestrator._build_answer_prompt():
   Add 2-hop context to the prompt:
   
   ```python
   # Get 2-hop context if available
   two_hop_context = getattr(entity_agent, 'two_hop_context', None)
   
   # Include in prompt
   if two_hop_context and two_hop_context.get('context_text'):
       prompt += "\\n\\n" + two_hop_context['context_text']
   ```

================================================================================
"""

# =============================================================================
# TEST CODE
# =============================================================================

def test_two_hop_rag():
    """Test the 2-hop path RAG implementation."""
    print("\n" + "="*70)
    print("TESTING 2-HOP PATH RAG")
    print("="*70)
    
    # Create test path finder with sample relationships
    test_relationships = {
        "SA": [
            "supervised by Secretary of State",
            "authorized under Title 22",
            "subset of Security Cooperation"
        ],
        "Security Assistance": [
            "supervised by Secretary of State",
            "authorized under Title 22"
        ],
        "Secretary of State": [
            "coordinates with Secretary of Defense",
            "approves export licenses"
        ],
        "SECSTATE": [
            "supervises SA programs",
            "coordinates with SECDEF"
        ],
        "DSCA": [
            "reports to USD(P)",
            "administers FMS"
        ],
        "USD(P)": [
            "reports to SECDEF",
            "oversees DSCA"
        ],
    }
    
    path_finder = TwoHopPathFinder(
        knowledge_graph=None,
        entity_relationships=test_relationships
    )
    
    # Test Q4: "Who supervises SA?"
    print("\n--- Test: Who supervises SA? ---")
    context = path_finder.get_context_for_query(
        entities=["SA", "Security Assistance"],
        query="Who supervises Security Assistance programs?",
        intent="authority"
    )
    
    print(f"\nPaths found: {context['relationship_count']}")
    print(f"Authority chains: {list(context['authority_chains'].keys())}")
    print(f"\nContext text:\n{context['context_text']}")
    
    # Test entity extraction fix
    print("\n--- Test: Entity Extraction Fix ---")
    test_queries = [
        "Who supervises SA?",
        "What is the difference between SC and SA?",
        "What does DSCA do?",
    ]
    
    for query in test_queries:
        entities = enhanced_entity_extraction_fix(query, {})
        print(f"Query: '{query}' -> Entities: {entities}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    test_two_hop_rag()
    print(INSTALLATION_INSTRUCTIONS)
