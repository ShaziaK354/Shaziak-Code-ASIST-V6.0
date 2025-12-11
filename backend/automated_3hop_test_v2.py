"""
================================================================================
AUTOMATED N-HOP PATH RAG TESTING - v5.9.4
================================================================================

This script tests the N-Hop Path RAG implementation (supports 1, 2, 3+ hops)
Tests are updated to handle bidirectional relationship matching.

USAGE:
------
python automated_3hop_test_v2.py

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

# Test questions with expected answers - UPDATED FOR BIDIRECTIONAL MATCHING
TEST_QUESTIONS = [
    {
        "id": "Q4",
        "question": "Who supervises Security Assistance programs?",
        "entities": ["SA", "Security Assistance"],
        "expected_contains": ["Secretary of State", "SECSTATE", "supervision", "direction"],
        "expected_paths": ["SA --[supervised_by]--> SECSTATE"],
        "alt_paths": ["SECSTATE --[supervises]--> SA"],  # Alternative direction
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
        "expected_contains": ["directs", "administers", "USD(P)", "manages"],
        "expected_paths": ["DSCA --[reports_to]--> USD(P)"],
        "category": "role"
    },
    {
        "id": "Q_DSCA_CHAIN",
        "question": "Who does DSCA report to?",
        "entities": ["DSCA"],
        "expected_contains": ["USD(P)", "SECDEF"],
        "expected_paths": ["DSCA --[reports_to]--> USD(P)"],
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
        "alt_paths": ["SECSTATE --[supervises]--> SA"],
        "category": "authority"
    },
    {
        "id": "Q_FMS_CHAIN",
        "question": "What is the supervision chain for FMS?",
        "entities": ["FMS"],
        "expected_contains": ["SA", "SECSTATE", "AECA"],
        "expected_paths": ["FMS --[part_of]--> SA"],
        "category": "authority"
    },
    {
        "id": "Q_NAVY_FMS",
        "question": "Who is responsible for Navy FMS cases?",
        "entities": ["NIPO", "FMS", "DEPT_NAVY"],
        "expected_contains": ["NIPO", "Navy", "FMS"],
        "expected_paths": ["NIPO --[manages]--> FMS", "NIPO --[is_IA_for]--> DEPT_NAVY"],
        "alt_paths": ["FMS --[managed_by]--> NIPO"],
        "category": "responsibility"
    },
    {
        "id": "Q_DFAS_ROLE",
        "question": "What role does DFAS play in Security Cooperation?",
        "entities": ["DFAS", "SC"],
        "expected_contains": ["accounting", "billing", "disburs", "collect", "fund", "process"],
        "expected_paths": [],
        "category": "role"
    },
    {
        "id": "Q_JCS_ADVICE",
        "question": "Who provides military advice on Security Cooperation?",
        "entities": ["JCS", "SC", "SECDEF"],
        "expected_contains": ["Joint Chiefs", "military advice", "SECDEF", "JCS"],
        "expected_paths": ["JCS --[provides_military_advice]--> SECDEF"],
        "category": "authority"
    },
    {
        "id": "Q_IAS",
        "question": "What are the Implementing Agencies for each military department?",
        "entities": ["DASA_DEC", "NIPO", "SAF_IA", "DEPT_ARMY", "DEPT_NAVY", "DEPT_AIR_FORCE"],
        "expected_contains": ["DASA", "NIPO", "SAF", "Army", "Navy", "Air Force"],
        "expected_paths": ["DASA_DEC --[is_IA_for]--> DEPT_ARMY", "NIPO --[is_IA_for]--> DEPT_NAVY"],
        "category": "responsibility"
    },
    {
        "id": "Q_SCO_SUPERVISION",
        "question": "Who supervises Security Cooperation Organizations (SCOs)?",
        "entities": ["CCDRS", "SCO"],
        "expected_contains": ["Combatant Commander", "CCDR", "supervise", "SCO", "CCMD"],
        "expected_paths": ["CCDRS --[supervises]--> SCO"],
        "category": "authority"
    },
    {
        "id": "Q_DOS_ROLE",
        "question": "What does Department of State do for Security Assistance?",
        "entities": ["DOS", "SA"],
        "expected_contains": ["supervises", "direction", "Security Assistance", "State"],
        "expected_paths": ["DOS --[supervises]--> SA"],
        "alt_paths": ["SA --[supervised_by]--> DOS"],
        "category": "role"
    },
    {
        "id": "Q_FMS_AUDIT",
        "question": "Who audits FMS contracts?",
        "entities": ["DCAA", "FMS"],
        "expected_contains": ["DCAA", "audit"],
        "expected_paths": ["DCAA --[performs_auditing]--> FMS"],
        "alt_paths": ["FMS --[audited_by]--> DCAA"],
        "category": "responsibility"
    },
    {
        "id": "Q_DLA_ROLE",
        "question": "What is the role of DLA in Security Cooperation?",
        "entities": ["DLA", "SC"],
        "expected_contains": ["logistics", "DLA", "Defense Logistics", "support", "provides"],
        "expected_paths": ["DLA --[provides_logistics_for]--> SC"],
        "category": "role"
    },
    {
        "id": "Q_CAMPAIGN_PLANS",
        "question": "Who develops campaign plans for Security Cooperation?",
        "entities": ["CCDRS", "SC"],
        "expected_contains": ["CCDR", "Combatant Commander", "campaign plan", "develops"],
        "expected_paths": ["CCDRS --[develops_campaign_plans_for]--> SC"],
        "category": "authority"
    },
    {
        "id": "Q_ARMY_FMS",
        "question": "Who handles Army FMS materiel programs?",
        "entities": ["USASAC", "FMS", "DEPT_ARMY"],
        "expected_contains": ["USASAC", "Army", "FMS"],
        "expected_paths": ["USASAC --[responsible_for]--> FMS"],
        "category": "responsibility"
    },
    {
        "id": "Q_DOD_STRUCTURE",
        "question": "What organizations are part of DOD?",
        "entities": ["DOD", "DEPARTMENT_OF_DEFENSE", "DSCA", "DLA"],
        "expected_contains": ["DSCA", "DLA", "DOD"],
        "expected_paths": [],
        "category": "organization"
    },
    {
        "id": "Q_EXECUTIVE_AGENT",
        "question": "Who acts as Executive Agent for Security Cooperation?",
        "entities": ["EXECUTIVE_AGENT", "EA", "DSCA"],
        "expected_contains": ["DSCA", "Executive Agent", "EA"],
        "expected_paths": [],
        "category": "role"
    },
    {
        "id": "Q_LOA_PROCESS",
        "question": "What is the LOA process?",
        "entities": ["LOA", "LETTER_OF_OFFER_AND_ACCEPTANCE"],
        "expected_contains": ["FMS", "DSCA", "LOR"],
        "expected_paths": [],
        "category": "process"
    },
    {
        "id": "Q_LOR_PROCESS",
        "question": "Who receives Letter of Request?",
        "entities": ["LOR", "LETTER_OF_REQUEST", "DSCA"],
        "expected_contains": ["DSCA"],
        "expected_paths": ["LOR --[submitted_to]--> DSCA"],
        "alt_paths": ["DSCA --[receives]--> LOR", "DSCA --[receives_from]--> LOR"],
        "category": "process"
    },
    {
        "id": "Q_SECTION_36",
        "question": "What is Section 36 of AECA about?",
        "entities": ["SECTION_36_AECA", "AECA_SECTION_36", "DSCA"],
        "expected_contains": ["DSCA", "AECA"],
        "expected_paths": [],
        "category": "authority"
    },
    {
        "id": "Q_DOD_DIRECTIVE",
        "question": "What DOD Directives govern DSCA?",
        "entities": ["DOD_DIRECTIVE_510565", "DSCA"],
        "expected_contains": ["DSCA", "5105"],
        "expected_paths": [],
        "category": "regulation"
    },
    {
        "id": "Q_CCMD_ROLE",
        "question": "What does Geographic Combatant Command do for SC?",
        "entities": ["CCMD", "CCDRS", "COMBATANT_COMMAND"],
        "expected_contains": ["SCO", "SC", "campaign", "oversees", "supervises"],
        "expected_paths": ["CCDRS --[supervises]--> SCO"],
        "category": "organization"
    },
    {
        "id": "Q_IMET",
        "question": "Who manages IMET program?",
        "entities": ["IMET", "DSCA"],
        "expected_contains": ["DSCA", "manage"],
        "expected_paths": [],
        "alt_paths": ["IMET --[managedby]--> DSCA", "DSCA --[manages]--> IMET"],
        "category": "program"
    },
    {
        "id": "Q_BPC",
        "question": "What is Building Partner Capacity?",
        "entities": ["BPC", "BUILDING_PARTNER_CAPACITY"],
        "expected_contains": ["FMS", "Title", "partner", "authorized"],
        "expected_paths": [],
        "category": "program"
    },
    {
        "id": "Q_SDR",
        "question": "What is SDR (Supply Discrepancy Report)?",
        "entities": ["SDR", "SUPPLY_DISCREPANCY_REPORT", "DLA"],
        "expected_contains": ["DLA", "discrepancy", "supply", "contract"],
        "expected_paths": [],
        "alt_paths": ["DLA --[handles]--> SDR", "SDR --[handled_by]--> DLA"],
        "category": "process"
    },
    {
        "id": "Q_DCAA_AUDIT",
        "question": "What does DCAA do for contracts?",
        "entities": ["DCAA", "DEFENSE_CONTRACT_AUDIT_AGENCY_DCAA"],
        "expected_contains": ["audit", "contract", "FMS"],
        "expected_paths": [],
        "category": "organization"
    },
    {
        "id": "Q_USDP_ROLE",
        "question": "What is USD(P) responsible for?",
        "entities": ["USD(P)", "USDP", "UNDER_SECRETARY_OF_DEFENSE_FOR_POLICY"],
        "expected_contains": ["DSCA", "policy", "SECDEF", "SC"],
        "expected_paths": [],
        "category": "position"
    },
    {
        "id": "Q_DEFENSE_ARTICLES",
        "question": "Who provides Defense Articles?",
        "entities": ["DEFENSE_ARTICLES", "DLA"],
        "expected_contains": ["DLA", "FMS", "IA", "provides"],
        "expected_paths": [],
        "alt_paths": ["DLA --[provides]--> DEFENSE_ARTICLES", "DEFENSE_ARTICLES --[provided_by]--> DLA"],
        "category": "item"
    },
    {
        "id": "Q_STATE_COORDINATION",
        "question": "Who does DSCA coordinate with for SA?",
        "entities": ["DSCA", "DEPARTMENT_OF_STATE", "STATE"],
        "expected_contains": ["State", "DOS", "coordinate", "DSCA"],
        "expected_paths": [],
        "alt_paths": ["DSCA --[coordinates_with]--> STATE", "STATE --[coordinates_with]--> DSCA"],
        "category": "coordination"
    },
    # ============ 3-HOP SPECIFIC TEST QUESTIONS ============
    {
        "id": "Q_3HOP_DSCA_CHAIN",
        "question": "What is the reporting chain from DSCA?",
        "entities": ["DSCA"],
        "expected_contains": ["USD(P)", "SECDEF"],
        "expected_paths": ["DSCA --[reports_to]--> USD(P)"],
        "expected_3hop": True,
        "category": "authority_chain"
    },
    {
        "id": "Q_3HOP_FMS_AUTHORITY",
        "question": "What is the full authority chain for FMS?",
        "entities": ["FMS"],
        "expected_contains": ["SA", "SECSTATE", "AECA"],
        "expected_paths": ["FMS --[part_of]--> SA"],
        "expected_3hop": True,
        "category": "authority_chain"
    },
    {
        "id": "Q_3HOP_LOA_CHAIN",
        "question": "What is the complete chain for LOA?",
        "entities": ["LOA"],
        "expected_contains": ["FMS", "DSCA"],
        "expected_paths": [],
        "expected_3hop": True,
        "category": "authority_chain"
    },
    {
        "id": "Q_3HOP_NIPO_CHAIN",
        "question": "How does NIPO connect to the authority structure?",
        "entities": ["NIPO"],
        "expected_contains": ["FMS", "SA", "Navy"],
        "expected_paths": [],
        "expected_3hop": True,
        "category": "authority_chain"
    },
    {
        "id": "Q_3HOP_DLA_CHAIN",
        "question": "What is DLA's connection to DOD?",
        "entities": ["DLA"],
        "expected_contains": ["DOD", "SC", "logistics"],
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
            
            for category, cat_entities in data.get('entities', {}).items():
                if isinstance(cat_entities, dict):
                    for eid, edata in cat_entities.items():
                        self.entities[eid] = {
                            'id': eid,
                            'label': edata.get('label', eid),
                            'type': edata.get('type', category),
                            'definition': edata.get('definition', ''),
                            'section': edata.get('section', '')
                        }
            
            self.relationships = data.get('relationships', [])
            
            print(f"[KG] Loaded {len(self.entities)} entities, {len(self.relationships)} relationships")
    
    def _build_indices(self):
        self._entity_by_id = {e.lower(): self.entities[e] for e in self.entities}
        
        for rel in self.relationships:
            src = rel['source'].lower()
            tgt = rel['target'].lower()
            
            if src not in self._relationships_by_source:
                self._relationships_by_source[src] = []
            self._relationships_by_source[src].append(rel)
            
            if tgt not in self._relationships_by_target:
                self._relationships_by_target[tgt] = []
            self._relationships_by_target[tgt].append(rel)
    
    def get_entity_by_id(self, entity_id: str):
        return self._entity_by_id.get(entity_id.lower())
    
    def get_relationships_from(self, entity_id: str):
        return self._relationships_by_source.get(entity_id.lower(), [])
    
    def get_relationships_to(self, entity_id: str):
        return self._relationships_by_target.get(entity_id.lower(), [])


# =============================================================================
# N-HOP PATH FINDER
# =============================================================================

class NHopPathFinder:
    """N-Hop path finder with configurable depth."""
    
    def __init__(self, kg: SAMMKnowledgeGraph):
        self.kg = kg
        self.relationship_graph = {}
        self._build_graph()
    
    def _build_graph(self):
        for rel in self.kg.relationships:
            src = rel['source'].lower()
            tgt = rel['target'].lower()
            
            if src not in self.relationship_graph:
                self.relationship_graph[src] = []
            
            self.relationship_graph[src].append({
                'target': tgt,
                'type': rel['type'],
                'section': rel.get('section', ''),
                'weight': rel.get('weight', 5)
            })
        
        print(f"   Graph has {len(self.relationship_graph)} entities")
    
    def get_priority_for_query(self, query: str) -> List[str]:
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ['supervise', 'oversight', 'who supervises']):
            return ['supervised_by', 'supervises', 'reports_to', 'oversees', 'overseen_by', 'managed_by', 'manages']
        elif any(kw in query_lower for kw in ['report', 'chain', 'who does', 'reports to']):
            return ['reports_to', 'receives_reports_from', 'supervised_by', 'supervises', 'part_of', 'contains']
        elif any(kw in query_lower for kw in ['authorize', 'authority', 'legal']):
            return ['authorized_by', 'authorizes', 'governed_by', 'governs', 'implements', 'implemented_by']
        elif any(kw in query_lower for kw in ['manage', 'administer', 'responsible']):
            return ['manages', 'managed_by', 'managedby', 'administers', 'administered_by', 'responsible_for']
        elif any(kw in query_lower for kw in ['coordinate', 'works with']):
            return ['coordinates_with', 'coordinated_with', 'works_with', 'workswith']
        elif any(kw in query_lower for kw in ['provide', 'support', 'service']):
            return ['provides', 'provided_by', 'supports', 'supported_by', 'provides_logistics_for']
        elif any(kw in query_lower for kw in ['audit', 'review']):
            return ['performs_auditing', 'audited_by', 'reviews', 'reviewed_by']
        else:
            return ['reports_to', 'supervised_by', 'part_of', 'authorized_by', 'manages', 'administers']
    
    def find_nhop_paths(self, entity: str, query: str = "", max_hops: int = 3, max_paths: int = 15) -> List[Dict]:
        """Find all n-hop paths from entity using BFS."""
        entity_lower = entity.lower()
        paths = []
        
        priority_types = self.get_priority_for_query(query)
        
        if entity_lower not in self.relationship_graph:
            return paths
        
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
                    
                    if target in path_nodes:
                        continue
                    
                    new_path_nodes = path_nodes + [target]
                    new_path_rels = path_rels + [rel_type]
                    new_depth = depth + 1
                    
                    path_text = f"{entity.upper()}"
                    for i, rel in enumerate(new_path_rels):
                        path_text += f" --[{rel}]--> {new_path_nodes[i+1].upper()}"
                    
                    path_key = " -> ".join(new_path_nodes)
                    
                    if path_key not in visited_paths:
                        visited_paths.add(path_key)
                        
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
        
        paths.sort(key=lambda p: (p['hops'], p.get('priority', 99)))
        return paths[:max_paths]
    
    def find_supervision_chain(self, entity: str) -> List[Dict]:
        entity_lower = entity.lower()
        chain = []
        current = entity_lower
        visited = {current}
        
        supervision_types = ['supervised_by', 'reports_to', 'managed_by', 'directed_by', 'part_of',
                            'supervises', 'receives_reports_from', 'manages', 'directs', 'contains']
        
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
        
        authority_keywords = ['supervise', 'supervision', 'report', 'oversee', 'manage', 'authority', 'who', 'chain']
        result['is_authority_question'] = any(kw in query.lower() for kw in authority_keywords)
        
        all_paths = []
        for entity in entities:
            paths = self.find_nhop_paths(entity, query, max_hops=3)
            all_paths.extend(paths)
            
            if result['is_authority_question']:
                chain = self.find_supervision_chain(entity)
                if chain:
                    result['authority_chains'][entity] = chain
        
        seen = set()
        for path in all_paths:
            if path['path_text'] not in seen:
                seen.add(path['path_text'])
                result['paths'].append(path)
        
        result['paths'] = sorted(result['paths'], key=lambda p: (p['hops'], p.get('priority', 99)))[:10]
        
        return result


# =============================================================================
# TEST RUNNER
# =============================================================================

def run_tests():
    print("="*70)
    print("🧪 AUTOMATED N-HOP PATH RAG TESTING - v5.9.4")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    print("\n📥 Loading Knowledge Graph...")
    kg = SAMMKnowledgeGraph(KG_JSON_PATH)
    
    print("🔧 Initializing N-Hop Path Finder...")
    path_finder = NHopPathFinder(kg)
    
    print("\n" + "="*70)
    print("🧪 RUNNING TEST CASES")
    print("="*70)
    
    results = []
    passed = 0
    partial = 0
    failed = 0
    
    for test in TEST_QUESTIONS:
        test_id = test['id']
        question = test['question']
        entities = test['entities']
        expected_contains = test.get('expected_contains', [])
        expected_paths = test.get('expected_paths', [])
        alt_paths = test.get('alt_paths', [])  # NEW: Alternative paths
        
        print(f"\n--- {test_id}: {question[:50]}... ---")
        
        context = path_finder.get_context_for_query(entities, question)
        
        paths = context['paths']
        chains = context['authority_chains']
        
        # Build searchable text (paths + chain text)
        all_text = " ".join([p['path_text'] for p in paths])
        for entity, chain in chains.items():
            chain_str = " → ".join([c['to'].upper() for c in chain])
            if chain_str:
                all_text += f" {entity.upper()} → {chain_str}"
        
        all_text_lower = all_text.lower()
        
        # Check expected contains (case-insensitive, partial match)
        contains_checks = []
        for expected in expected_contains:
            # Check partial match
            found = expected.lower() in all_text_lower
            contains_checks.append(found)
        
        # Check expected paths OR alternative paths
        path_checks = []
        all_expected = expected_paths + alt_paths
        
        if all_expected:
            for exp_path in all_expected:
                # Normalize for comparison
                exp_normalized = exp_path.lower().replace(' ', '')
                found = any(
                    exp_normalized in p['path_text'].lower().replace(' ', '')
                    for p in paths
                )
                if found:
                    path_checks.append(True)
                    break  # Found at least one matching path
            
            if not path_checks:
                path_checks.append(False)
        
        # Calculate score
        total_checks = len(contains_checks) + len(path_checks)
        passed_checks = sum(contains_checks) + sum(path_checks)
        
        if total_checks == 0:
            status = "PASS" if len(paths) > 0 else "FAIL"
        elif passed_checks == total_checks:
            status = "PASS"
        elif passed_checks > 0:
            status = "PARTIAL"
        else:
            status = "FAIL"
        
        if status == "PASS":
            print(f"Status: ✅ PASS")
            passed += 1
        elif status == "PARTIAL":
            print(f"Status: ⚠️ PARTIAL")
            partial += 1
        else:
            print(f"Status: ❌ FAIL")
            failed += 1
        
        print(f"Paths found: {len(paths)}")
        for p in paths[:10]:
            print(f"  • {p['path_text']}")
        
        if chains:
            print("Authority chains:")
            for entity, chain in chains.items():
                if chain:
                    chain_str = " → ".join([entity.upper()] + [c['to'].upper() for c in chain])
                    print(f"  • {chain_str}")
        
        print(f"Checks: {passed_checks}/{total_checks} passed")
        
        results.append({
            'id': test_id,
            'question': question,
            'status': status,
            'paths_found': len(paths),
            'checks_passed': passed_checks,
            'checks_total': total_checks,
            'paths': [p['path_text'] for p in paths[:10]]
        })
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {len(TEST_QUESTIONS)}")
    print(f"✅ Passed: {passed}")
    print(f"⚠️ Partial: {partial}")
    print(f"❌ Failed: {failed}")
    
    total = len(TEST_QUESTIONS)
    pass_rate = (passed / total) * 100 if total > 0 else 0
    print(f"\nPass Rate: {pass_rate:.1f}%")
    
    # Save results
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{OUTPUT_DIR}/test_results_nhop_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': total,
                'passed': passed,
                'partial': partial,
                'failed': failed,
                'pass_rate': pass_rate
            },
            'results': results
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_file}")
    
    return passed, partial, failed


if __name__ == '__main__':
    run_tests()

