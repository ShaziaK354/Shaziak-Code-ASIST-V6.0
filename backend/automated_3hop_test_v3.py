"""
================================================================================
AUTOMATED N-HOP PATH RAG TESTING - v5.9.4 (FIXED)
================================================================================

Test expectations now use ONLY:
- Entity names (DSCA, SECSTATE, FMS)
- Relationship types (supervised_by, reports_to, part_of)

NO description-based keywords like "continuous supervision"

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

# FIXED TEST QUESTIONS - Only entity names and relationship types
TEST_QUESTIONS = [
    {
        "id": "Q4",
        "question": "Who supervises Security Assistance programs?",
        "entities": ["SA", "Security Assistance"],
        "expected_contains": ["SECSTATE", "supervised_by"],
        "category": "authority"
    },
    {
        "id": "Q2",
        "question": "What is the difference between SC and SA?",
        "entities": ["SC", "SA"],
        "expected_contains": ["subset_of", "SC", "SA"],
        "category": "comparison"
    },
    {
        "id": "Q5",
        "question": "What is DSCA's role?",
        "entities": ["DSCA"],
        "expected_contains": ["DSCA", "manages", "administers"],
        "category": "role"
    },
    {
        "id": "Q_DSCA_CHAIN",
        "question": "Who does DSCA report to?",
        "entities": ["DSCA"],
        "expected_contains": ["USD(P)", "reports_to"],
        "category": "authority"
    },
    {
        "id": "Q_FMS_AUTH",
        "question": "What authorizes FMS?",
        "entities": ["FMS"],
        "expected_contains": ["AECA", "authorized_by"],
        "category": "authority"
    },
    {
        "id": "Q_SA_SUPERVISION",
        "question": "Who provides continuous supervision of SA?",
        "entities": ["SA"],
        "expected_contains": ["SECSTATE", "supervised_by"],
        "category": "authority"
    },
    {
        "id": "Q_FMS_CHAIN",
        "question": "What is the supervision chain for FMS?",
        "entities": ["FMS"],
        "expected_contains": ["SA", "part_of"],
        "category": "authority"
    },
    {
        "id": "Q_NAVY_FMS",
        "question": "Who is responsible for Navy FMS cases?",
        "entities": ["NIPO", "FMS"],
        "expected_contains": ["NIPO", "FMS", "manages"],
        "category": "responsibility"
    },
    {
        "id": "Q_DFAS_ROLE",
        "question": "What role does DFAS play in Security Cooperation?",
        "entities": ["DFAS", "SC"],
        "expected_contains": ["DFAS", "SC"],
        "category": "role"
    },
    {
        "id": "Q_JCS_ADVICE",
        "question": "Who provides military advice on Security Cooperation?",
        "entities": ["JCS", "SC", "SECDEF"],
        "expected_contains": ["JCS", "SECDEF"],
        "category": "authority"
    },
    {
        "id": "Q_IAS",
        "question": "What are the Implementing Agencies for each military department?",
        "entities": ["DASA_DEC", "NIPO", "SAF_IA"],
        "expected_contains": ["DASA_DEC", "NIPO", "SAF_IA", "is_IA_for"],
        "category": "responsibility"
    },
    {
        "id": "Q_SCO_SUPERVISION",
        "question": "Who supervises Security Cooperation Organizations (SCOs)?",
        "entities": ["CCDRS", "SCO"],
        "expected_contains": ["SCO", "supervises"],
        "category": "authority"
    },
    {
        "id": "Q_DOS_ROLE",
        "question": "What does Department of State do for Security Assistance?",
        "entities": ["DOS", "SA"],
        "expected_contains": ["DOS", "SA", "supervises"],
        "category": "role"
    },
    {
        "id": "Q_FMS_AUDIT",
        "question": "Who audits FMS contracts?",
        "entities": ["DCAA", "FMS"],
        "expected_contains": ["DCAA", "FMS", "audit"],
        "category": "responsibility"
    },
    {
        "id": "Q_DLA_ROLE",
        "question": "What is the role of DLA in Security Cooperation?",
        "entities": ["DLA", "SC"],
        "expected_contains": ["DLA", "SC", "logistics"],
        "category": "role"
    },
    {
        "id": "Q_CAMPAIGN_PLANS",
        "question": "Who develops campaign plans for Security Cooperation?",
        "entities": ["CCDRS", "SC"],
        "expected_contains": ["CCDRS", "campaign"],
        "category": "authority"
    },
    {
        "id": "Q_ARMY_FMS",
        "question": "Who handles Army FMS materiel programs?",
        "entities": ["USASAC", "FMS"],
        "expected_contains": ["USASAC", "FMS"],
        "category": "responsibility"
    },
    {
        "id": "Q_DOD_STRUCTURE",
        "question": "What organizations are part of DOD?",
        "entities": ["DOD", "DSCA", "DLA"],
        "expected_contains": ["DOD", "part_of"],
        "category": "organization"
    },
    {
        "id": "Q_EXECUTIVE_AGENT",
        "question": "Who acts as Executive Agent for Security Cooperation?",
        "entities": ["DSCA"],
        "expected_contains": ["DSCA"],
        "category": "role"
    },
    {
        "id": "Q_LOA_PROCESS",
        "question": "What is the LOA process?",
        "entities": ["LOA"],
        "expected_contains": ["LOA", "FMS"],
        "category": "process"
    },
    {
        "id": "Q_LOR_PROCESS",
        "question": "Who receives Letter of Request?",
        "entities": ["LOR", "DSCA"],
        "expected_contains": ["LOR", "DSCA"],
        "category": "process"
    },
    {
        "id": "Q_SECTION_36",
        "question": "What is Section 36 of AECA about?",
        "entities": ["DSCA", "AECA"],
        "expected_contains": ["DSCA", "AECA"],
        "category": "authority"
    },
    {
        "id": "Q_DOD_DIRECTIVE",
        "question": "What DOD Directives govern DSCA?",
        "entities": ["DSCA"],
        "expected_contains": ["DSCA", "DOD"],
        "category": "regulation"
    },
    {
        "id": "Q_CCMD_ROLE",
        "question": "What does Geographic Combatant Command do for SC?",
        "entities": ["CCMD", "CCDRS"],
        "expected_contains": ["SCO", "oversees"],
        "category": "organization"
    },
    {
        "id": "Q_IMET",
        "question": "Who manages IMET program?",
        "entities": ["IMET", "DSCA"],
        "expected_contains": ["IMET", "DSCA"],
        "category": "program"
    },
    {
        "id": "Q_BPC",
        "question": "What is Building Partner Capacity?",
        "entities": ["BPC"],
        "expected_contains": ["BPC", "FMS"],
        "category": "program"
    },
    {
        "id": "Q_SDR",
        "question": "What is SDR (Supply Discrepancy Report)?",
        "entities": ["SDR", "DLA"],
        "expected_contains": ["SDR", "DLA"],
        "category": "process"
    },
    {
        "id": "Q_DCAA_AUDIT",
        "question": "What does DCAA do for contracts?",
        "entities": ["DCAA"],
        "expected_contains": ["DCAA", "audit"],
        "category": "organization"
    },
    {
        "id": "Q_USDP_ROLE",
        "question": "What is USD(P) responsible for?",
        "entities": ["USD(P)", "USDP"],
        "expected_contains": ["USD(P)", "SECDEF"],
        "category": "position"
    },
    {
        "id": "Q_DEFENSE_ARTICLES",
        "question": "Who provides Defense Articles?",
        "entities": ["DEFENSE_ARTICLES", "DLA"],
        "expected_contains": ["DEFENSE_ARTICLES", "DLA"],
        "category": "item"
    },
    {
        "id": "Q_STATE_COORDINATION",
        "question": "Who does DSCA coordinate with for SA?",
        "entities": ["DSCA", "STATE"],
        "expected_contains": ["DSCA", "STATE"],
        "category": "coordination"
    },
    # 3-HOP Tests
    {
        "id": "Q_3HOP_DSCA_CHAIN",
        "question": "What is the reporting chain from DSCA?",
        "entities": ["DSCA"],
        "expected_contains": ["DSCA", "USD(P)", "reports_to"],
        "category": "authority_chain"
    },
    {
        "id": "Q_3HOP_FMS_AUTHORITY",
        "question": "What is the full authority chain for FMS?",
        "entities": ["FMS"],
        "expected_contains": ["FMS", "SA", "part_of"],
        "category": "authority_chain"
    },
    {
        "id": "Q_3HOP_LOA_CHAIN",
        "question": "What is the complete chain for LOA?",
        "entities": ["LOA"],
        "expected_contains": ["LOA", "FMS"],
        "category": "authority_chain"
    },
    {
        "id": "Q_3HOP_NIPO_CHAIN",
        "question": "How does NIPO connect to the authority structure?",
        "entities": ["NIPO"],
        "expected_contains": ["NIPO", "FMS"],
        "category": "authority_chain"
    },
    {
        "id": "Q_3HOP_DLA_CHAIN",
        "question": "What is DLA's connection to DOD?",
        "entities": ["DLA"],
        "expected_contains": ["DLA", "DOD"],
        "category": "authority_chain"
    }
]


# =============================================================================
# KNOWLEDGE GRAPH LOADER
# =============================================================================

class SAMMKnowledgeGraph:
    def __init__(self, json_path: str = None):
        self.entities = {}
        self.relationships = []
        
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
                        self.entities[eid] = edata
            
            self.relationships = data.get('relationships', [])
            print(f"[KG] Loaded {len(self.entities)} entities, {len(self.relationships)} relationships")
    
    def _build_indices(self):
        pass


# =============================================================================
# N-HOP PATH FINDER
# =============================================================================

class NHopPathFinder:
    def __init__(self, kg: SAMMKnowledgeGraph):
        self.kg = kg
        self.relationship_graph = {}
        self._build_graph()
    
    def _build_graph(self):
        for rel in self.kg.relationships:
            src = rel['source'].lower()
            tgt = rel['target'].lower()
            
            # Check if this is a reverse relationship
            is_reverse = rel.get('source_db') == 'reverse_generated'
            
            if src not in self.relationship_graph:
                self.relationship_graph[src] = []
            
            self.relationship_graph[src].append({
                'target': tgt,
                'type': rel['type'],
                'is_reverse': is_reverse,
                'weight': 2 if is_reverse else 1  # Reverse gets lower priority
            })
        
        print(f"   Graph has {len(self.relationship_graph)} entities")
    
    def find_nhop_paths(self, entity: str, max_hops: int = 3, max_paths: int = 15) -> List[Dict]:
        entity_lower = entity.lower()
        paths = []
        
        if entity_lower not in self.relationship_graph:
            return paths
        
        queue = deque([(entity_lower, [entity_lower], [], [], 0)])
        visited_paths = set()
        
        while queue and len(paths) < max_paths * 3:
            current, path_nodes, path_rels, path_weights, depth = queue.popleft()
            
            if depth >= max_hops:
                continue
            
            if current in self.relationship_graph:
                for edge in self.relationship_graph[current]:
                    target = edge['target']
                    rel_type = edge['type']
                    weight = edge.get('weight', 1)
                    
                    if target in path_nodes:
                        continue
                    
                    new_path_nodes = path_nodes + [target]
                    new_path_rels = path_rels + [rel_type]
                    new_path_weights = path_weights + [weight]
                    new_depth = depth + 1
                    
                    path_text = f"{entity.upper()}"
                    for i, rel in enumerate(new_path_rels):
                        path_text += f" --[{rel}]--> {new_path_nodes[i+1].upper()}"
                    
                    path_key = " -> ".join(new_path_nodes)
                    
                    if path_key not in visited_paths:
                        visited_paths.add(path_key)
                        total_weight = sum(new_path_weights)
                        
                        paths.append({
                            'hops': new_depth,
                            'path_text': path_text,
                            'relationships': new_path_rels,
                            'weight': total_weight
                        })
                    
                    if new_depth < max_hops:
                        queue.append((target, new_path_nodes, new_path_rels, new_path_weights, new_depth))
        
        # Sort by: hops first, then weight (lower = better = original relationships)
        paths.sort(key=lambda p: (p['hops'], p['weight']))
        return paths[:max_paths]
    
    def find_supervision_chain(self, entity: str) -> List[Dict]:
        entity_lower = entity.lower()
        chain = []
        current = entity_lower
        visited = {current}
        
        supervision_types = ['supervised_by', 'reports_to', 'managed_by', 'part_of', 'supervises']
        
        for _ in range(5):
            found = False
            if current in self.relationship_graph:
                # Prefer original relationships
                edges = sorted(self.relationship_graph[current], key=lambda e: e.get('weight', 1))
                for edge in edges:
                    if edge['type'] in supervision_types:
                        target = edge['target']
                        if target not in visited:
                            chain.append({'from': current, 'to': target, 'type': edge['type']})
                            visited.add(target)
                            current = target
                            found = True
                            break
            if not found:
                break
        return chain
    
    def get_context_for_query(self, entities: List[str]) -> Dict:
        result = {'paths': [], 'authority_chains': {}}
        
        all_paths = []
        for entity in entities:
            paths = self.find_nhop_paths(entity, max_hops=3)
            all_paths.extend(paths)
            
            chain = self.find_supervision_chain(entity)
            if chain:
                result['authority_chains'][entity] = chain
        
        seen = set()
        for path in all_paths:
            if path['path_text'] not in seen:
                seen.add(path['path_text'])
                result['paths'].append(path)
        
        result['paths'] = sorted(result['paths'], key=lambda p: (p['hops'], p['weight']))[:15]
        return result


# =============================================================================
# TEST RUNNER
# =============================================================================

def run_tests():
    print("="*70)
    print("🧪 AUTOMATED N-HOP PATH RAG TESTING - v5.9.4 (FIXED)")
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
        
        print(f"\n--- {test_id}: {question[:50]}... ---")
        
        context = path_finder.get_context_for_query(entities)
        paths = context['paths']
        chains = context['authority_chains']
        
        # Build searchable text
        all_text = " ".join([p['path_text'] for p in paths])
        for entity, chain in chains.items():
            chain_str = " → ".join([c['to'].upper() for c in chain])
            if chain_str:
                all_text += f" {entity.upper()} → {chain_str}"
        
        all_text_upper = all_text.upper()
        
        # Check expected contains (case-insensitive)
        checks_passed = 0
        for expected in expected_contains:
            if expected.upper() in all_text_upper:
                checks_passed += 1
        
        total_checks = len(expected_contains)
        
        if total_checks == 0:
            status = "PASS" if len(paths) > 0 else "FAIL"
        elif checks_passed == total_checks:
            status = "PASS"
        elif checks_passed > 0:
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
        
        print(f"Checks: {checks_passed}/{total_checks} passed")
        
        results.append({
            'id': test_id,
            'status': status,
            'paths_found': len(paths),
            'checks_passed': checks_passed,
            'checks_total': total_checks
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
    success_rate = ((passed + partial) / total) * 100 if total > 0 else 0
    
    print(f"\nStrict Pass Rate: {pass_rate:.1f}%")
    print(f"Success Rate (Pass + Partial): {success_rate:.1f}%")
    
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
                'pass_rate': pass_rate,
                'success_rate': success_rate
            },
            'results': results
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_file}")
    
    return passed, partial, failed


if __name__ == '__main__':
    run_tests()

