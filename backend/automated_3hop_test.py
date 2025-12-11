"""
================================================================================
AUTOMATED N-HOP PATH RAG TESTING - v5.9.4
================================================================================

This script tests the N-Hop Path RAG implementation (supports 1, 2, 3+ hops)
without needing the full Flask server. It directly tests the knowledge graph 
and path finding.

USAGE:
------
python automated_3hop_test.py

OUTPUT:
- Console results with pass/fail status
- JSON report file: test_results_nhop_TIMESTAMP.json

================================================================================
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import deque

# =============================================================================
# CONFIGURATION
# =============================================================================

KG_JSON_PATH = "samm_knowledge_graph.json"
OUTPUT_DIR = "test_results"

# Test questions with expected answers
TEST_QUESTIONS = [
    {
        "id": "Q4",
        "question": "Who supervises Security Assistance programs?",
        "entities": ["SA", "Security Assistance"],
        "expected_contains": ["Secretary of State", "SECSTATE", "continuous supervision", "general direction"],
        "expected_paths": ["SA --[supervised_by]--> SECSTATE"],
        "category": "authority"
    },
    {
        "id": "Q2",
        "question": "What is the difference between SC and SA?",
        "entities": ["SC", "SA", "Security Cooperation", "Security Assistance"],
        "expected_contains": ["subset", "Title 10", "Title 22"],
        "expected_paths": ["SA --[subset_of]--> SC"],
        "category": "comparison"
    },
    {
        "id": "Q5",
        "question": "What is DSCA's role?",
        "entities": ["DSCA", "Defense Security Cooperation Agency"],
        "expected_contains": ["directs", "administers", "USD(P)"],
        "expected_paths": ["DSCA --[reports_to]--> USD(P)"],
        "category": "role"
    },
    {
        "id": "Q_DSCA_CHAIN",
        "question": "Who does DSCA report to?",
        "entities": ["DSCA"],
        "expected_contains": ["USD(P)", "SECDEF"],
        "expected_paths": ["DSCA --[reports_to]--> USD(P)", "USD(P) --[reports_to]--> SECDEF"],
        "category": "authority"
    },
    {
        "id": "Q_FMS_AUTH",
        "question": "What authorizes FMS?",
        "entities": ["FMS", "Foreign Military Sales"],
        "expected_contains": ["AECA", "Arms Export Control Act"],
        "expected_paths": [],
        "category": "authority"
    },
    {
        "id": "Q_SA_SUPERVISION",
        "question": "Who provides continuous supervision of SA?",
        "entities": ["SA"],
        "expected_contains": ["Secretary of State", "SECSTATE"],
        "expected_paths": ["SA --[supervised_by]--> SECSTATE"],
        "category": "authority"
    },
    {
        "id": "Q_FMS_CHAIN",
        "question": "What is the supervision chain for FMS?",
        "entities": ["FMS"],
        "expected_contains": ["SA", "SECSTATE"],
        "expected_paths": ["FMS --[part_of]--> SA"],
        "category": "authority"
    },
    # ============ NEW TEST QUESTIONS FOR EXPANDED KG ============
    {
        "id": "Q_NAVY_FMS",
        "question": "Who is responsible for Navy FMS cases?",
        "entities": ["NIPO", "FMS", "DEPT_NAVY"],
        "expected_contains": ["NIPO", "Navy", "manages", "FMS"],
        "expected_paths": ["NIPO --[manages]--> FMS", "NIPO --[is_IA_for]--> DEPT_NAVY"],
        "category": "responsibility"
    },
    {
        "id": "Q_DFAS_ROLE",
        "question": "What role does DFAS play in Security Cooperation?",
        "entities": ["DFAS", "SC"],
        "expected_contains": ["accounting", "billing", "disbursing", "collecting"],
        "expected_paths": ["DFAS --[performs_accounting]--> SC"],
        "category": "role"
    },
    {
        "id": "Q_JCS_ADVICE",
        "question": "Who provides military advice on Security Cooperation?",
        "entities": ["JCS", "SC", "SECDEF"],
        "expected_contains": ["Joint Chiefs", "military advice", "SECDEF"],
        "expected_paths": ["JCS --[provides_military_advice]--> SECDEF"],
        "category": "authority"
    },
    {
        "id": "Q_IAS",
        "question": "What are the Implementing Agencies for each military department?",
        "entities": ["DASA_DEC", "NIPO", "SAF_IA", "DEPT_ARMY", "DEPT_NAVY", "DEPT_AIR_FORCE"],
        "expected_contains": ["DASA", "NIPO", "SAF/IA", "Army", "Navy", "Air Force"],
        "expected_paths": ["DASA_DEC --[is_IA_for]--> DEPT_ARMY", "NIPO --[is_IA_for]--> DEPT_NAVY"],
        "category": "responsibility"
    },
    {
        "id": "Q_SCO_SUPERVISION",
        "question": "Who supervises Security Cooperation Organizations (SCOs)?",
        "entities": ["CCDRS", "SCO"],
        "expected_contains": ["Combatant Commander", "CCDR", "supervise", "SCO"],
        "expected_paths": ["CCDRS --[supervises]--> SCO"],
        "category": "authority"
    },
    {
        "id": "Q_DOS_ROLE",
        "question": "What does Department of State do for Security Assistance?",
        "entities": ["DOS", "SA"],
        "expected_contains": ["supervises", "general direction", "Security Assistance"],
        "expected_paths": ["DOS --[supervises]--> SA"],
        "category": "role"
    },
    {
        "id": "Q_FMS_AUDIT",
        "question": "Who audits FMS contracts?",
        "entities": ["DCAA", "FMS"],
        "expected_contains": ["DCAA", "audit", "contract"],
        "expected_paths": ["DCAA --[performs_auditing]--> FMS"],
        "category": "responsibility"
    },
    {
        "id": "Q_DLA_ROLE",
        "question": "What is the role of DLA in Security Cooperation?",
        "entities": ["DLA", "SC"],
        "expected_contains": ["logistics", "DLA", "Defense Logistics"],
        "expected_paths": ["DLA --[provides_logistics_for]--> SC"],
        "category": "role"
    },
    {
        "id": "Q_CAMPAIGN_PLANS",
        "question": "Who develops campaign plans for Security Cooperation?",
        "entities": ["CCDRS", "SC"],
        "expected_contains": ["CCDR", "Combatant Commander", "campaign plan"],
        "expected_paths": ["CCDRS --[develops_campaign_plans_for]--> SC"],
        "category": "authority"
    },
    {
        "id": "Q_ARMY_FMS",
        "question": "Who handles Army FMS materiel programs?",
        "entities": ["USASAC", "FMS", "DEPT_ARMY"],
        "expected_contains": ["USASAC", "Army", "materiel", "FMS"],
        "expected_paths": ["USASAC --[responsible_for]--> FMS"],
        "category": "responsibility"
    },
    # ============ 15 NEW TEST QUESTIONS FOR COSMOS DB DATA ============
    {
        "id": "Q_DOD_STRUCTURE",
        "question": "What organizations are part of DOD?",
        "entities": ["DOD", "DEPARTMENT_OF_DEFENSE"],
        "expected_contains": ["DSCA", "DLA"],
        "expected_paths": ["DSCA --[part_of]--> DOD"],
        "category": "organization"
    },
    {
        "id": "Q_EXECUTIVE_AGENT",
        "question": "Who acts as Executive Agent for Security Cooperation?",
        "entities": ["EXECUTIVE_AGENT", "EA", "DSCA"],
        "expected_contains": ["DSCA", "Executive Agent"],
        "expected_paths": [],
        "category": "role"
    },
    {
        "id": "Q_LOA_PROCESS",
        "question": "What is the LOA process?",
        "entities": ["LOA", "LETTER_OF_OFFER_AND_ACCEPTANCE"],
        "expected_contains": ["FMS", "DSCA"],
        "expected_paths": [],
        "category": "process"
    },
    {
        "id": "Q_LOR_PROCESS",
        "question": "Who receives Letter of Request?",
        "entities": ["LOR", "LETTER_OF_REQUEST"],
        "expected_contains": ["DSCA"],
        "expected_paths": ["DSCA --[receives]--> LOR"],
        "category": "process"
    },
    {
        "id": "Q_THAAD",
        "question": "What is THAAD related to?",
        "entities": ["THAAD", "TERMINAL_HIGH_ALTITUDE_AREA_DEFENSE_THAAD"],
        "expected_contains": [],
        "expected_paths": [],
        "category": "system"
    },
    {
        "id": "Q_SECTION_36",
        "question": "What is Section 36 of AECA about?",
        "entities": ["SECTION_36_AECA", "AECA_SECTION_36", "DSCA"],
        "expected_contains": ["DSCA", "authority"],
        "expected_paths": [],
        "category": "authority"
    },
    {
        "id": "Q_DOD_DIRECTIVE",
        "question": "What DOD Directives govern DSCA?",
        "entities": ["DOD_DIRECTIVE_510565", "DSCA"],
        "expected_contains": ["DSCA", "5105.65"],
        "expected_paths": [],
        "category": "regulation"
    },
    {
        "id": "Q_CCMD_ROLE",
        "question": "What does Geographic Combatant Command do for SC?",
        "entities": ["CCMD", "CCDRS", "COMBATANT_COMMAND"],
        "expected_contains": ["SCO", "SC", "campaign"],
        "expected_paths": ["CCDRS --[supervises]--> SCO"],
        "category": "organization"
    },
    {
        "id": "Q_IMET",
        "question": "Who manages IMET program?",
        "entities": ["IMET"],
        "expected_contains": ["DSCA"],
        "expected_paths": ["DSCA --[manages]--> IMET"],
        "category": "program"
    },
    {
        "id": "Q_BPC",
        "question": "What is Building Partner Capacity?",
        "entities": ["BPC", "BUILDING_PARTNER_CAPACITY"],
        "expected_contains": ["SC", "Security Cooperation"],
        "expected_paths": [],
        "category": "program"
    },
    {
        "id": "Q_SDR",
        "question": "What is SDR (Supply Discrepancy Report)?",
        "entities": ["SDR", "SUPPLY_DISCREPANCY_REPORT"],
        "expected_contains": ["DLA"],
        "expected_paths": ["DLA --[handles]--> SDR"],
        "category": "process"
    },
    {
        "id": "Q_DCAA_AUDIT",
        "question": "What does DCAA do for contracts?",
        "entities": ["DCAA", "DEFENSE_CONTRACT_AUDIT_AGENCY_DCAA"],
        "expected_contains": ["audit", "contract"],
        "expected_paths": [],
        "category": "organization"
    },
    {
        "id": "Q_USDP_ROLE",
        "question": "What is USD(P) responsible for?",
        "entities": ["USD(P)", "USDP", "UNDER_SECRETARY_OF_DEFENSE_FOR_POLICY"],
        "expected_contains": ["DSCA", "policy"],
        "expected_paths": [],
        "category": "position"
    },
    {
        "id": "Q_DEFENSE_ARTICLES",
        "question": "Who provides Defense Articles?",
        "entities": ["DEFENSE_ARTICLES"],
        "expected_contains": ["DLA", "FMS"],
        "expected_paths": ["DLA --[provides]--> DEFENSE_ARTICLES"],
        "category": "item"
    },
    {
        "id": "Q_STATE_COORDINATION",
        "question": "Who does DSCA coordinate with for SA?",
        "entities": ["DSCA", "DEPARTMENT_OF_STATE", "STATE"],
        "expected_contains": ["State", "DOS", "coordinate"],
        "expected_paths": ["DSCA --[coordinates_with]--> STATE"],
        "category": "coordination"
    },
    # ============ 3-HOP SPECIFIC TEST QUESTIONS ============
    {
        "id": "Q_3HOP_DSCA_PRESIDENT",
        "question": "What is the chain from DSCA to President?",
        "entities": ["DSCA"],
        "expected_contains": ["USD(P)", "SECDEF", "President"],
        "expected_paths": ["DSCA --[reports_to]--> USD(P) --[reports_to]--> SECDEF"],
        "expected_3hop": True,
        "category": "authority_chain"
    },
    {
        "id": "Q_3HOP_FMS_CONGRESS",
        "question": "What is the full authority chain for FMS?",
        "entities": ["FMS"],
        "expected_contains": ["SA", "SECSTATE", "AECA"],
        "expected_paths": ["FMS --[part_of]--> SA --[supervised_by]--> SECSTATE"],
        "expected_3hop": True,
        "category": "authority_chain"
    },
    {
        "id": "Q_3HOP_LOA_AUTHORITY",
        "question": "What is the complete authorization chain for LOA?",
        "entities": ["LOA"],
        "expected_contains": ["FMS", "SA", "AECA"],
        "expected_paths": [],
        "expected_3hop": True,
        "category": "authority_chain"
    },
    {
        "id": "Q_3HOP_NIPO_SECSTATE",
        "question": "How does NIPO connect to Secretary of State?",
        "entities": ["NIPO"],
        "expected_contains": ["FMS", "SA", "SECSTATE"],
        "expected_paths": [],
        "expected_3hop": True,
        "category": "authority_chain"
    },
    {
        "id": "Q_3HOP_DLA_AUTHORITY",
        "question": "What is DLA's chain to SECDEF?",
        "entities": ["DLA"],
        "expected_contains": ["DOD", "SECDEF"],
        "expected_paths": [],
        "expected_3hop": True,
        "category": "authority_chain"
    }
]


# =============================================================================
# KNOWLEDGE GRAPH LOADER
# =============================================================================

class SAMMKnowledgeGraph:
    """JSON-based Knowledge Graph loader."""
    
    def __init__(self, json_path: str = None):
        self.entities = {}
        self.relationships = []
        self._entity_by_id = {}
        self._relationships_by_source = {}
        self._relationships_by_target = {}
        
        if json_path:
            self._load_from_file(json_path)
        self._build_indices()
    
    def _load_from_file(self, json_path: str):
        path = Path(json_path)
        if not path.exists():
            path = Path(__file__).parent / json_path
        
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load entities
            for category, cat_entities in data.get('entities', {}).items():
                if isinstance(cat_entities, dict):
                    for eid, edata in cat_entities.items():
                        self.entities[eid] = {
                            'id': eid,
                            'type': edata.get('type', 'entity'),
                            'properties': {
                                'label': edata.get('label', eid),
                                'definition': edata.get('definition', ''),
                                'section': edata.get('section', '')
                            }
                        }
            
            # Load relationships
            for rel in data.get('relationships', []):
                self.relationships.append({
                    'source': rel.get('source'),
                    'target': rel.get('target'),
                    'type': rel.get('type'),
                    'description': rel.get('description', ''),
                    'section': rel.get('section', '')
                })
            
            print(f"[KG] Loaded {len(self.entities)} entities, {len(self.relationships)} relationships")
    
    def _build_indices(self):
        for eid, entity in self.entities.items():
            self._entity_by_id[eid.lower()] = entity
        
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
    
    def find_entity(self, query: str) -> Optional[Dict]:
        return self._entity_by_id.get(query.lower().strip())
    
    def get_relationships(self, entity_id: str) -> List[Dict]:
        entity_lower = entity_id.lower()
        rels = []
        rels.extend(self._relationships_by_source.get(entity_lower, []))
        rels.extend(self._relationships_by_target.get(entity_lower, []))
        return rels


# =============================================================================
# 2-HOP PATH FINDER
# =============================================================================

class TwoHopPathFinder:
    """N-Hop Path RAG Implementation."""
    
    def __init__(self, kg: SAMMKnowledgeGraph):
        self.kg = kg
        self.relationship_graph = {}
        self._build_graph()
    
    def _build_graph(self):
        for rel in self.kg.relationships:
            source = rel['source'].lower() if rel['source'] else ''
            target = rel['target'].lower() if rel['target'] else ''
            rel_type = rel['type']
            
            if source and target:
                if source not in self.relationship_graph:
                    self.relationship_graph[source] = []
                self.relationship_graph[source].append({
                    'target': target,
                    'type': rel_type,
                    'section': rel.get('section', '')
                })
    
    def get_priority_for_query(self, query: str) -> List[str]:
        """Get priority order based on question intent."""
        query_lower = query.lower()
        
        if 'report' in query_lower:
            # Reporting chain questions - "Who does X report to?"
            return [
                'reports_to', 'supervised_by', 'managed_by', 'subset_of',
                'authorized_by', 'administers', 'part_of', 'implements'
            ]
        
        elif 'supervise' in query_lower or 'supervision' in query_lower:
            # Supervision questions - "Who supervises X?"
            return [
                'supervised_by', 'supervises', 'provides_direction_for', 'managed_by',
                'reports_to', 'subset_of', 'authorized_by', 'administers'
            ]
        
        elif 'difference' in query_lower or ' vs ' in query_lower or 'compare' in query_lower:
            # Comparison questions - "What is the difference between X and Y?"
            return [
                'subset_of', 'part_of', 'authorized_by', 'supervised_by',
                'managed_by', 'reports_to', 'administers', 'implements'
            ]
        
        elif 'authorize' in query_lower or 'authority' in query_lower or 'legal' in query_lower:
            # Authority/legal questions - "What authorizes X?"
            return [
                'authorized_by', 'supervised_by', 'reports_to', 'delegates_to',
                'subset_of', 'managed_by', 'administers', 'implements'
            ]
        
        elif 'role' in query_lower or 'responsibility' in query_lower or "'s role" in query_lower:
            # Role questions - "What is X's role?" / "What does X do?"
            return [
                'administers', 'reports_to', 'implements', 'manages', 'executes',
                'supervised_by', 'authorized_by', 'part_of', 'subset_of', 'directs'
            ]
        
        else:
            # Default - based on KG weights
            return [
                'subset_of', 'supervised_by', 'managed_by', 'supervises', 'provides_direction_for',
                'authorized_by', 'reports_to', 'administers', 'advises', 'provided_by',
                'implements', 'applies_to', 'executes', 'approves', 'delegates_to',
                'part_of', 'coordinates_with', 'monitors', 'submits'
            ]
    
    def find_nhop_paths(self, entity: str, query: str = "", max_hops: int = 3, max_paths: int = 15) -> List[Dict]:
        """Find all n-hop paths from entity using BFS."""
        from collections import deque
        
        entity_lower = entity.lower()
        paths = []
        
        # Get intent-based priority
        priority_types = self.get_priority_for_query(query)
        
        if entity_lower not in self.relationship_graph:
            return paths
        
        # BFS: (current_node, path_nodes, path_relationships, depth)
        queue = deque([(entity_lower, [entity_lower], [], 0)])
        visited_paths = set()
        
        while queue and len(paths) < max_paths * 2:
            current, path_nodes, path_rels, depth = queue.popleft()
            
            if depth >= max_hops:
                continue
            
            if current in self.relationship_graph:
                for edge in self.relationship_graph[current]:
                    target = edge['target']
                    rel_type = edge['type']
                    
                    # Avoid cycles
                    if target in path_nodes:
                        continue
                    
                    new_path_nodes = path_nodes + [target]
                    new_path_rels = path_rels + [rel_type]
                    new_depth = depth + 1
                    
                    # Build path text
                    path_text = f"{entity.upper()}"
                    for i, rel in enumerate(new_path_rels):
                        path_text += f" --[{rel}]--> {new_path_nodes[i+1].upper()}"
                    
                    path_key = " -> ".join(new_path_nodes)
                    
                    if path_key not in visited_paths:
                        visited_paths.add(path_key)
                        
                        # Calculate priority
                        min_priority = 99
                        for rel in new_path_rels:
                            if rel in priority_types:
                                min_priority = min(min_priority, priority_types.index(rel))
                        
                        paths.append({
                            'hops': new_depth,
                            'path_text': path_text,
                            'relationships': new_path_rels,
                            'priority': min_priority
                        })
                    
                    if new_depth < max_hops:
                        queue.append((target, new_path_nodes, new_path_rels, new_depth))
        
        # Sort by: 1) hops first (1-hop before 2-hop, etc), 2) then priority
        paths.sort(key=lambda p: (p['hops'], p.get('priority', 99)))
        
        return paths[:max_paths]
    
    # Backward compatibility alias
    def find_2hop_paths(self, entity: str, query: str = "", max_paths: int = 10) -> List[Dict]:
        return self.find_nhop_paths(entity, query, max_hops=2, max_paths=max_paths)
    
    def find_supervision_chain(self, entity: str) -> List[Dict]:
        entity_lower = entity.lower()
        chain = []
        current = entity_lower
        visited = {current}
        
        supervision_types = ['supervised_by', 'reports_to', 'managed_by', 'directed_by', 'part_of']
        
        for _ in range(5):
            found = False
            if current in self.relationship_graph:
                for edge in self.relationship_graph[current]:
                    if edge['type'] in supervision_types:
                        target = edge['target']
                        if target not in visited:
                            chain.append({
                                'from': current,
                                'to': target,
                                'type': edge['type']
                            })
                            visited.add(target)
                            current = target
                            found = True
                            break
            if not found:
                break
        
        return chain
    
    def get_context_for_query(self, entities: List[str], query: str) -> Dict:
        result = {
            'paths': [],
            'authority_chains': {},
            'is_authority_question': False
        }
        
        authority_keywords = ['supervise', 'supervision', 'report', 'oversee', 'manage', 'authority', 'who']
        result['is_authority_question'] = any(kw in query.lower() for kw in authority_keywords)
        
        # Check if this is a comparison/difference question
        is_comparison = any(kw in query.lower() for kw in ['difference', 'vs', 'compare', 'between'])
        
        all_paths = []
        for entity in entities:
            paths = self.find_nhop_paths(entity, query, max_hops=3)  # 3-hop traversal
            all_paths.extend(paths)
            
            if result['is_authority_question']:
                chain = self.find_supervision_chain(entity)
                if chain:
                    result['authority_chains'][entity] = chain
        
        # RE-SORT combined paths by hops first, then priority
        all_paths.sort(key=lambda p: (p['hops'], p.get('priority', 99)))
        
        # For comparison questions: ensure balanced representation
        if is_comparison and len(entities) > 1:
            # Get one path per relationship type per entity for better comparison
            balanced_paths = []
            seen_combinations = set()  # Track (entity, relationship_type) combinations
            
            for path in all_paths:
                entity = path['path_text'].split(' ')[0]  # First word is entity
                rel_type = path['relationships'][0] if path.get('relationships') else 'unknown'
                combination = (entity, rel_type)
                
                if combination not in seen_combinations:
                    seen_combinations.add(combination)
                    balanced_paths.append(path)
            
            # Re-sort balanced paths
            balanced_paths.sort(key=lambda p: (p['hops'], p.get('priority', 99)))
            all_paths = balanced_paths
        
        # Deduplicate while preserving sorted order
        seen = set()
        for path in all_paths:
            if path['path_text'] not in seen:
                seen.add(path['path_text'])
                result['paths'].append(path)
        
        return result


# =============================================================================
# TEST RUNNER
# =============================================================================

def run_single_test(test: Dict, kg: SAMMKnowledgeGraph, path_finder: TwoHopPathFinder) -> Dict:
    """Run a single test case."""
    result = {
        'id': test['id'],
        'question': test['question'],
        'category': test['category'],
        'status': 'PASS',
        'checks': [],
        'paths_found': [],
        'authority_chains': {},
        'entity_definitions': {}
    }
    
    # Get entities
    entities = test['entities']
    
    # Get entity definitions
    for entity in entities:
        ent = kg.find_entity(entity)
        if ent:
            result['entity_definitions'][entity] = ent['properties'].get('definition', '')[:100]
    
    # Get 2-hop context
    context = path_finder.get_context_for_query(entities, test['question'])
    result['paths_found'] = [p['path_text'] for p in context['paths'][:10]]
    result['authority_chains'] = context['authority_chains']
    
    # Check expected paths
    for expected_path in test.get('expected_paths', []):
        found = any(expected_path.lower() in p.lower() for p in result['paths_found'])
        check = {
            'type': 'expected_path',
            'expected': expected_path,
            'found': found
        }
        result['checks'].append(check)
        if not found and expected_path:
            result['status'] = 'PARTIAL'
    
    # Check expected content in ALL sources
    all_text = ' '.join(result['paths_found'])
    all_text += ' ' + ' '.join(str(v) for v in result['entity_definitions'].values())
    all_text += ' ' + ' '.join(str(chain) for chain in result['authority_chains'].values())
    
    # Also check KG entity definitions directly
    for entity in entities:
        ent = kg.find_entity(entity)
        if ent:
            all_text += ' ' + ent['properties'].get('definition', '')
    
    # Also add relationship descriptions from KG
    for entity in entities:
        rels = kg.get_relationships(entity)
        for rel in rels:
            all_text += ' ' + rel.get('description', '')
    
    for expected in test.get('expected_contains', []):
        found = expected.lower() in all_text.lower()
        check = {
            'type': 'expected_content',
            'expected': expected,
            'found': found
        }
        result['checks'].append(check)
        if not found:
            result['status'] = 'PARTIAL'
    
    # If no checks passed, mark as FAIL
    passed_checks = sum(1 for c in result['checks'] if c['found'])
    if passed_checks == 0:
        result['status'] = 'FAIL'
    elif passed_checks == len(result['checks']):
        result['status'] = 'PASS'
    
    return result


def run_all_tests() -> Dict:
    """Run all test cases."""
    print("="*70)
    print("🧪 AUTOMATED N-HOP PATH RAG TESTING - v5.9.3")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Load knowledge graph
    print("\n📥 Loading Knowledge Graph...")
    kg = SAMMKnowledgeGraph(KG_JSON_PATH)
    
    # Initialize path finder
    print("🔧 Initializing N-Hop Path Finder...")
    path_finder = TwoHopPathFinder(kg)
    print(f"   Graph has {len(path_finder.relationship_graph)} entities")
    
    # Run tests
    results = {
        'timestamp': datetime.now().isoformat(),
        'kg_stats': {
            'entities': len(kg.entities),
            'relationships': len(kg.relationships)
        },
        'tests': [],
        'summary': {
            'total': 0,
            'passed': 0,
            'partial': 0,
            'failed': 0
        }
    }
    
    print("\n" + "="*70)
    print("🧪 RUNNING TEST CASES")
    print("="*70)
    
    for test in TEST_QUESTIONS:
        print(f"\n--- {test['id']}: {test['question'][:50]}... ---")
        
        test_result = run_single_test(test, kg, path_finder)
        results['tests'].append(test_result)
        
        # Update summary
        results['summary']['total'] += 1
        if test_result['status'] == 'PASS':
            results['summary']['passed'] += 1
            status_icon = "✅"
        elif test_result['status'] == 'PARTIAL':
            results['summary']['partial'] += 1
            status_icon = "⚠️"
        else:
            results['summary']['failed'] += 1
            status_icon = "❌"
        
        print(f"Status: {status_icon} {test_result['status']}")
        print(f"Paths found: {len(test_result['paths_found'])}")
        for path in test_result['paths_found'][:10]:  # Show top 10
            print(f"  • {path}")
        
        if test_result['authority_chains']:
            print(f"Authority chains:")
            for entity, chain in test_result['authority_chains'].items():
                chain_text = entity.upper()
                for edge in chain:
                    chain_text += f" → {edge['to'].upper()}"
                print(f"  • {chain_text}")
        
        print(f"Checks: {sum(1 for c in test_result['checks'] if c['found'])}/{len(test_result['checks'])} passed")
    
    # Print summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {results['summary']['total']}")
    print(f"✅ Passed: {results['summary']['passed']}")
    print(f"⚠️ Partial: {results['summary']['partial']}")
    print(f"❌ Failed: {results['summary']['failed']}")
    
    pass_rate = (results['summary']['passed'] / results['summary']['total'] * 100) if results['summary']['total'] > 0 else 0
    print(f"\nPass Rate: {pass_rate:.1f}%")
    
    # Save results
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = f"{OUTPUT_DIR}/test_results_nhop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Results saved to: {output_file}")
    
    return results


def test_specific_question(question: str, entities: List[str]):
    """Test a specific question interactively."""
    print(f"\n🔍 Testing: {question}")
    print(f"   Entities: {entities}")
    
    kg = SAMMKnowledgeGraph(KG_JSON_PATH)
    path_finder = TwoHopPathFinder(kg)
    
    context = path_finder.get_context_for_query(entities, question)
    
    print(f"\n📊 Results:")
    print(f"   Is authority question: {context['is_authority_question']}")
    print(f"   Paths found: {len(context['paths'])}")
    
    for path in context['paths'][:5]:
        print(f"   • {path['path_text']}")
    
    if context['authority_chains']:
        print(f"\n   Authority chains:")
        for entity, chain in context['authority_chains'].items():
            chain_text = entity.upper()
            for edge in chain:
                chain_text += f" → {edge['to'].upper()}"
            print(f"   • {chain_text}")
    
    # Show entity definitions
    print(f"\n   Entity definitions:")
    for entity in entities:
        ent = kg.find_entity(entity)
        if ent:
            defn = ent['properties'].get('definition', 'N/A')[:100]
            print(f"   • {entity}: {defn}...")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        # Interactive mode
        print("🧪 Interactive N-Hop Path RAG Testing")
        print("Type 'quit' to exit\n")
        
        while True:
            question = input("Question: ").strip()
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            entities_input = input("Entities (comma-separated): ").strip()
            entities = [e.strip() for e in entities_input.split(',')]
            
            test_specific_question(question, entities)
            print()
    else:
        # Run all tests
        results = run_all_tests()
        
        # Exit with appropriate code
        if results['summary']['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
