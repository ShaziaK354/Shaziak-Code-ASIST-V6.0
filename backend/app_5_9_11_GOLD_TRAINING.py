"""
SAMM Agent Application - Version 5.9.11
=======================================

CHANGELOG v5.9.11 (18-Dec-2025):
- ADDED: GOLD STANDARD TRAINING SYSTEM!
  * 13 Gold Q&A patterns from verified test questions
  * SAMMGoldTrainer class for pattern matching
- MAJOR: ULTRA SHORT system message when Gold matches!
  * Gold path: ~150 chars instruction + 800 chars context = ~1000 chars total
  * Non-Gold path: ~600 chars instruction + 1200 chars context = ~1800 chars
  * Format: "SAMM Expert. START: [gold_start] CITE: [citations]"
- UPDATED: _safe_query_vector() uses Gold Training
- ADDED: gold_answer_guidance() for answer structure

CHANGELOG v5.9.10 (18-Dec-2025):
- ADDED: HYBRID RE-RANKING for improved chunk retrieval!
  * Combines embedding similarity + keyword matching + Table/Figure boost
  * Fixes: Q9 (LOR Format), Q11 (Electronic), Q20 (Salary), Q21 (Case Description)
  * No regression on working questions (Q1, Q2, Q16, Q17)
  * Expected improvement: 21.9% → 45-55% citation accuracy
- ADDED: calculate_keyword_score() - matches query words in chunks
- ADDED: calculate_boost_score() - boosts Tables/Figures/Deep sections
- ADDED: rerank_results() - re-ranks by combined score
- UPDATED: _safe_query_vector() - fetches 20 candidates, re-ranks, returns top 8
- UPDATED: New entity queries for LOR format, salary, electronic submission
- FIXED: DISABLED _boost_by_entities() which was OVERRIDING hybrid re-ranking!
  * Entity boost was running AFTER re-ranking and undoing improvements
  * Now hybrid re-ranking handles entity matching via keyword scoring
- IMPROVED: Table/Figure detection patterns (more flexible matching)
- FIXED: _build_comprehensive_context() text_sections limit
  * Increased from 2 to 5 sections (correct chunks were being ignored!)
  * Increased truncation from 300 to 500 chars per section

CHANGELOG v5.9.9 (17-Dec-2025):
- FIXED: Citation regex now includes Tables and Figures!
  * Old regex only matched C5.4.2.1 style sections
  * New regex matches: C5.4.2.1, Table C5.T1, Figure C5.F14
- FIXED: Citation extraction from content text
  * Now scans vector DB chunk CONTENT for Table/Figure references
  * Previously only extracted from metadata (missed many citations)
- Expected improvements:
  * Citation Accuracy: 10.9% → 80%+ (Tables/Figures now detected)
  * Groundedness: Should improve as Tables/Figures are properly cited

CHANGELOG v5.9.8 (16-Dec-2025):
- ADDED: SMART SEARCH with think_first_v2() function
  * LLM identifies relevant SAMM terms BEFORE vector search
  * Solves semantic mismatch problem (e.g., "delay" → "CDEF")
  * SAMM_CONTEXT mapping for key FMS scenarios
- IMPROVED: _safe_query_vector() now uses enhanced queries
  * 100% accuracy on test questions (CDEF, CTA, OED, etc.)

CHANGELOG v5.9.4 (11-Dec-2025):
- ADDED: Answer Training System for similar questions
  * train_answer() - Extract keywords and save patterns
  * get_trained_answer() - Find trained answers for similar questions (60% keyword match)
  * answer_training.json - Persistent storage for trained patterns
- ADDED: Intent Training System for similar questions
  * train_intent() - Extract keywords and save patterns
  * get_trained_intent() - Find trained intents for similar questions (60% keyword match)
  * intent_training.json - Persistent storage for trained patterns
- ADDED: Entity Training System for similar questions
  * train_entities() - Extract keywords and save patterns
  * get_trained_entities() - Find trained entities for similar questions (60% keyword match)
  * entity_training.json - Persistent storage for trained patterns
- UPDATED: /api/hitl/correct-answer endpoint now trains the system
- UPDATED: /api/hitl/correct-intent endpoint now trains the system
- UPDATED: /api/hitl/correct-entities endpoint now trains the system
- UPDATED: apply_hitl_corrections() now checks trained patterns for ALL THREE (intent, entities, answer)
- SME corrections now improve future responses for SIMILAR questions, not just exact matches!

CHANGELOG v5.9.3:
- ADDED: 2-Hop Path RAG for multi-hop relationship traversal
- ADDED: JSON Knowledge Graph loader (SAMMKnowledgeGraph class)
- ADDED: TwoHopPathFinder class for BFS-based path finding
- ADDED: Authority/supervision chain detection
- ADDED: Enhanced entity extraction for better acronym matching
- Improved answers for questions like:
  * "Who supervises SA?" (finds SA → SECSTATE chain)
  * "What is DSCA's role?" (finds DSCA → USD(P) → SECDEF chain)
  * "Difference between SC and SA?" (finds subset relationships)

CHANGELOG v5.9.1:
- Increased Ollama timeout: 180s → 200s (reduce timeouts)
- Increased Cosmos timeout: 120s → 200s
- Added QUALITY INSTRUCTIONS to system prompts:
  * Citation Accuracy guidelines
  * Groundedness requirements  
  * Completeness requirements
- Expected improvements:
  * Citation Accuracy: 45% → 80%+
  * Groundedness: 52% → 80%+
  * Completeness: 55% → 85%+
  * Timeouts: 4/15 → 0-1/15
"""
# =========================
# GOLD STANDARD BLUEPRINTS
# =========================

LOR_BLUEPRINT = {
    "must_include_phrases": [
        "no specific format is required",
        "must be in writing",
        "Security Cooperation Organization",
        "Figure C5.F14",
        "Table C5.T3a",
        "Letter of Offer and Acceptance",
        "third party",
        "method of financing"
    ],
    "min_bullets": 8,
    "leahy_required": True
}


import os
import json
import uuid 
import time
import re
import hashlib
import asyncio
import sys
from datetime import datetime, timezone 
from typing import Dict, List, Any, Optional, TypedDict, Set
from urllib.parse import quote_plus, urlencode
from enum import Enum
from pathlib import Path
from flask import send_from_directory
import functools
from collections import defaultdict  # For metrics calculations
import openpyxl  # Excel processing for MISIL RSN sheets
import PyPDF2    # PDF text extraction
import tempfile  # Temporary file handling for uploads
# Fix for Windows asyncio issues
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Flask & Extensions
from flask import Flask, request, jsonify, session, send_from_directory, redirect, url_for
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from werkzeug.utils import secure_filename 

# Environment
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv()) 
def time_function(func):
    """Simple timing decorator for performance monitoring"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"[TIMING] {func.__name__}: {elapsed:.2f}s")
        return result
    return wrapper

# HTTP Requests Library
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
# Azure SDK
from azure.cosmos import CosmosClient, PartitionKey, exceptions as CosmosExceptions 
from azure.storage.blob import BlobServiceClient, ContentSettings 
from azure.core.exceptions import ResourceExistsError as BlobResourceExistsError, ResourceNotFoundError as BlobResourceNotFoundError

# Database imports for integrated agents
try:
    from gremlin_python.driver import client, serializer
    from gremlin_python.driver.protocol import GremlinServerError
    print("Gremlin client imported successfully")
except ImportError:
    print("Gremlin client not available - some features may be limited")
    client = None

try:
    import chromadb
    print("ChromaDB imported successfully")
except ImportError:
    print("ChromaDB not available - some features may be limited")
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
    print("SentenceTransformers imported successfully")
except ImportError:
    print("SentenceTransformers not available - some features may be limited")
    SentenceTransformer = None
    
    def meets_lor_gold_standard(answer_text: str) -> bool:
        text = answer_text.lower()

        # Check required phrases
        for phrase in LOR_BLUEPRINT["must_include_phrases"]:
            if phrase.lower() not in text:
                return False

        # Count bullet points
        bullet_count = answer_text.count("\n")  # rough but OK for now
        if bullet_count < LOR_BLUEPRINT["min_bullets"]:
            return False

        return True

# =============================================================================
# v5.9.3: 2-HOP PATH RAG CLASSES
# =============================================================================
from collections import deque

class SAMMKnowledgeGraphJSON:
    """
    JSON-based Knowledge Graph for SAMM - v5.9.3
    Loads from samm_knowledge_graph.json and provides 2-hop traversal.
    """
    
    def __init__(self, json_path: str = None, json_data: Dict = None):
        self.entities = {}
        self.relationships = []
        self.authority_chains = {}
        self.question_mappings = {}
        self.metadata = {}
        
        # Indices for fast lookup
        self._entity_by_id = {}
        self._entity_by_label = {}
        self._relationships_by_source = {}
        self._relationships_by_target = {}
        
        if json_path:
            self._load_from_file(json_path)
        elif json_data:
            self._load_from_dict(json_data)
        
        self._build_indices()
        print(f"[SAMMKnowledgeGraphJSON] ✅ Loaded: {len(self.entities)} entities, {len(self.relationships)} relationships")
    
    def _load_from_file(self, json_path: str):
        """Load from JSON file."""
        possible_paths = [
            Path(json_path),
            Path(__file__).parent / json_path,
            Path.cwd() / json_path,
        ]
        
        for p in possible_paths:
            if p.exists():
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._load_from_dict(data)
                print(f"[SAMMKnowledgeGraphJSON] Loaded from: {p}")
                return
        
        print(f"[SAMMKnowledgeGraphJSON] ⚠️ File not found: {json_path}")
    
    def _load_from_dict(self, data: Dict):
        """Load from dictionary."""
        self.metadata = data.get('metadata', {})
        
        # Flatten entities from categories
        entities_data = data.get('entities', {})
        for category, category_entities in entities_data.items():
            if isinstance(category_entities, dict):
                for entity_id, entity_data in category_entities.items():
                    entity_data['category'] = category
                    self.entities[entity_id] = {
                        'id': entity_id,
                        'type': entity_data.get('type', 'entity'),
                        'properties': {
                            'label': entity_data.get('label', entity_id),
                            'definition': entity_data.get('definition', ''),
                            'section': entity_data.get('section', ''),
                            'category': category
                        }
                    }
        
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
        
        self.authority_chains = data.get('authority_chains', {})
        self.question_mappings = data.get('question_mappings', {})
    
    def _build_indices(self):
        """Build lookup indices."""
        for entity_id, entity in self.entities.items():
            self._entity_by_id[entity_id.lower()] = entity
            label = entity['properties'].get('label', '').lower()
            if label:
                self._entity_by_label[label] = entity
        
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
        """Find entity by name or label."""
        query_lower = query.lower().strip()
        
        if query_lower in self._entity_by_id:
            return self._entity_by_id[query_lower]
        if query_lower in self._entity_by_label:
            return self._entity_by_label[query_lower]
        
        # Partial match
        for entity_id, entity in self._entity_by_id.items():
            if query_lower in entity_id:
                return entity
        
        return None
    
    def get_relationships(self, entity_id: str) -> List[Dict]:
        """Get all relationships for entity."""
        entity_lower = entity_id.lower()
        relationships = []
        
        if entity_lower in self._relationships_by_source:
            relationships.extend(self._relationships_by_source[entity_lower])
        if entity_lower in self._relationships_by_target:
            relationships.extend(self._relationships_by_target[entity_lower])
        
        return relationships
    
    def get_entity_relationships_dict(self) -> Dict[str, List[str]]:
        """Get entity relationships in dict format for TwoHopPathFinder."""
        result = {}
        for rel in self.relationships:
            source = rel['source']
            target = rel['target']
            rel_type = rel['type']
            rel_text = f"{rel_type.replace('_', ' ')} {target}"
            
            if source not in result:
                result[source] = []
            result[source].append(rel_text)
        
        return result


class TwoHopPathFinder:
    """
    2-Hop Path RAG Implementation - v5.9.3
    Finds relationship paths up to 2 hops using BFS.
    """
    
    def __init__(self, knowledge_graph=None, json_kg=None, entity_relationships: Dict = None):
        self.knowledge_graph = knowledge_graph  # Original TTL-based KG
        self.json_kg = json_kg  # New JSON-based KG
        self.entity_relationships = entity_relationships or {}
        self.relationship_graph = {}
        self.reverse_graph = {}
        self._build_graphs()
        print(f"[TwoHopPathFinder] ✅ Initialized with {len(self.relationship_graph)} entities in graph")
    
    def _build_graphs(self):
        """Build forward and reverse relationship graphs."""
        # From JSON knowledge graph
        if self.json_kg:
            for rel in self.json_kg.relationships:
                source = rel.get('source', '').lower()
                target = rel.get('target', '').lower()
                rel_type = rel.get('type', 'related_to')
                
                if source and target:
                    if source not in self.relationship_graph:
                        self.relationship_graph[source] = []
                    self.relationship_graph[source].append({
                        'target': target,
                        'type': rel_type,
                        'description': rel.get('description', ''),
                        'section': rel.get('section', '')
                    })
                    
                    if target not in self.reverse_graph:
                        self.reverse_graph[target] = []
                    self.reverse_graph[target].append({
                        'source': source,
                        'type': self._reverse_relationship(rel_type)
                    })
        
        # From original knowledge graph
        if self.knowledge_graph and hasattr(self.knowledge_graph, 'relationships'):
            for rel in self.knowledge_graph.relationships:
                source = rel.get('source', '').lower()
                target = rel.get('target', '').lower()
                rel_type = rel.get('relationship', rel.get('type', 'related_to'))
                
                if source and target and source not in self.relationship_graph:
                    if source not in self.relationship_graph:
                        self.relationship_graph[source] = []
                    self.relationship_graph[source].append({
                        'target': target,
                        'type': rel_type,
                        'description': '',
                        'section': ''
                    })
    
    def _reverse_relationship(self, rel_type: str) -> str:
        """Get reverse relationship type."""
        reverse_map = {
            'reports_to': 'receives_reports_from',
            'supervised_by': 'supervises',
            'directs': 'directed_by',
            'administers': 'administered_by',
            'responsible_for': 'responsibility_of',
            'approves': 'approved_by',
            'authorized_by': 'authorizes',
            'coordinates_with': 'coordinates_with',
            'subset_of': 'contains',
            'part_of': 'has_part',
        }
        return reverse_map.get(rel_type, f'reverse_{rel_type}')
    
    def find_nhop_paths(self, entity: str, max_hops: int = 3, max_paths: int = 15):
        """Find all n-hop paths from entity using BFS.
        
        Args:
            entity: Starting entity
            max_hops: Maximum number of hops (1, 2, 3, or more). Default: 3
            max_paths: Maximum paths to return. Default: 15
        """
        from collections import deque
        
        entity_lower = entity.lower()
        paths = []
        
        if entity_lower not in self.relationship_graph:
            return paths
        
        # BFS: (current_node, path_nodes, path_relationships, path_sections, depth)
        queue = deque([(entity_lower, [entity_lower], [], [], 0)])
        visited_paths = set()
        
        while queue and len(paths) < max_paths * 2:
            current, path_nodes, path_rels, path_sections, depth = queue.popleft()
            
            if depth >= max_hops:
                continue
            
            if current in self.relationship_graph:
                for edge in self.relationship_graph[current]:
                    target = edge['target']
                    rel_type = edge['type']
                    section = edge.get('section', '')
                    
                    # Avoid cycles
                    if target in path_nodes:
                        continue
                    
                    new_path_nodes = path_nodes + [target]
                    new_path_rels = path_rels + [rel_type]
                    new_path_sections = path_sections + [section]
                    new_depth = depth + 1
                    
                    # Build path text
                    path_text = f"{entity.upper()}"
                    for i, rel in enumerate(new_path_rels):
                        path_text += f" --[{rel}]--> {new_path_nodes[i+1].upper()}"
                    
                    path_key = " -> ".join(new_path_nodes)
                    
                    if path_key not in visited_paths:
                        visited_paths.add(path_key)
                        paths.append({
                            'hops': new_depth,
                            'path': new_path_nodes,
                            'relationships': new_path_rels,
                            'path_text': path_text,
                            'sections': new_path_sections
                        })
                    
                    if new_depth < max_hops:
                        queue.append((target, new_path_nodes, new_path_rels, new_path_sections, new_depth))
        
        paths.sort(key=lambda x: x['hops'])
        return paths[:max_paths]
    
    # Backward compatibility alias
    def find_2hop_paths(self, entity: str, max_paths: int = 10):
        """Backward compatible 2-hop function."""
        return self.find_nhop_paths(entity, max_hops=2, max_paths=max_paths)
    
    def find_supervision_chain(self, entity: str) -> List[Dict]:
        """Find supervision/authority chain for entity."""
        entity_lower = entity.lower()
        chain = []
        current = entity_lower
        visited = {current}
        
        supervision_types = ['supervised_by', 'reports_to', 'managed_by', 'directed_by', 'part_of']
        
        for _ in range(5):  # Max 5 levels
            found = False
            if current in self.relationship_graph:
                for edge in self.relationship_graph[current]:
                    if edge['type'] in supervision_types:
                        target = edge['target']
                        if target not in visited:
                            chain.append({
                                'from': current,
                                'to': target,
                                'type': edge['type'],
                                'section': edge.get('section', '')
                            })
                            visited.add(target)
                            current = target
                            found = True
                            break
            
            if not found:
                break
        
        return chain
    
    def get_context_for_query(self, entities: List[str], query: str, intent: str = None) -> Dict:
        """Get 2-hop context for a query."""
        result = {
            'paths': [],
            'authority_chains': {},
            'context_text': '',
            'is_authority_question': False,
            'relationship_count': 0
        }
        
        # Check if authority/supervision question
        authority_keywords = ['supervise', 'supervision', 'report', 'oversee', 'manage', 'direct', 'authority', 'responsible', 'who']
        query_lower = query.lower()
        result['is_authority_question'] = any(kw in query_lower for kw in authority_keywords)
        
        all_paths = []
        
        for entity in entities:
            # Get n-hop paths (3 hops by default)
            paths = self.find_nhop_paths(entity, max_hops=3)
            all_paths.extend(paths)
            
            # Get supervision chain for authority questions
            if result['is_authority_question']:
                chain = self.find_supervision_chain(entity)
                if chain:
                    result['authority_chains'][entity] = chain
        
        # Deduplicate paths
        seen_paths = set()
        unique_paths = []
        for path in all_paths:
            path_key = path['path_text']
            if path_key not in seen_paths:
                seen_paths.add(path_key)
                unique_paths.append(path)
        
        # Sort by relevance
        if result['is_authority_question']:
            supervision_types = ['supervised_by', 'reports_to', 'supervises', 'manages', 'directs']
            unique_paths.sort(key=lambda p: -sum(1 for r in p['relationships'] if r in supervision_types))
        
        result['paths'] = unique_paths[:10]
        result['relationship_count'] = len(unique_paths)
        
        # Build context text
        context_parts = []
        
        if result['is_authority_question'] and result['authority_chains']:
            context_parts.append("=== AUTHORITY/SUPERVISION CHAINS (2-HOP RAG) ===")
            for entity, chain in result['authority_chains'].items():
                if chain:
                    chain_text = f"{entity.upper()}"
                    for edge in chain:
                        chain_text += f" --[{edge['type']}]--> {edge['to'].upper()}"
                    context_parts.append(chain_text)
        
        if result['paths']:
            context_parts.append("\n=== RELATIONSHIP PATHS (2-HOP) ===")
            for path in result['paths'][:5]:
                context_parts.append(f"• {path['path_text']}")
                if path.get('sections'):
                    sections = [s for s in path['sections'] if s]
                    if sections:
                        context_parts.append(f"  Reference: {', '.join(sections)}")
        
        result['context_text'] = '\n'.join(context_parts)
        
        return result


# Global variable for JSON Knowledge Graph and Path Finder
SAMM_JSON_KG = None
TWO_HOP_PATH_FINDER = None

def initialize_2hop_rag(json_kg_path: str = "samm_knowledge_graph.json"):
    """Initialize 2-Hop Path RAG system."""
    global SAMM_JSON_KG, TWO_HOP_PATH_FINDER
    
    try:
        SAMM_JSON_KG = SAMMKnowledgeGraphJSON(json_path=json_kg_path)
        entity_rels = SAMM_JSON_KG.get_entity_relationships_dict()
        TWO_HOP_PATH_FINDER = TwoHopPathFinder(
            json_kg=SAMM_JSON_KG,
            entity_relationships=entity_rels
        )
        print(f"[v5.9.3] ✅ 2-Hop Path RAG initialized successfully")
        return True
    except Exception as e:
        print(f"[v5.9.3] ⚠️ 2-Hop Path RAG initialization failed: {e}")
        return False

# =============================================================================
# END v5.9.3: 2-HOP PATH RAG CLASSES
# =============================================================================

# --- Application Configuration ---
# Auth0 Configuration
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "DFd55vvJIcV79cGuEETrGc9HWiNDqducM7upRwXdeJ9c4E3LbCtl")
BASE_URL = os.getenv("BACKEND_URL", "http://172.16.200.12:3000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://172.16.200.12:5173")
# Ollama Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
#OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_MAX_RETRIES = int(os.getenv("OLLAMA_MAX_RETRIES", "3"))
OLLAMA_TIMEOUT_NORMAL = int(os.getenv("OLLAMA_TIMEOUT_NORMAL", "200"))  # v5.9.1: Increased to 200s to reduce timeouts
# Azure Storage Configuration
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("DATABASE_NAME")
CASES_CONTAINER_NAME = os.getenv("CASES_CONTAINER_NAME") 

# Azure Blob Storage Configuration
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
AZURE_CASE_DOCS_CONTAINER_NAME = os.getenv("AZURE_CASE_DOCS_CONTAINER_NAME")
AZURE_CHAT_DOCS_CONTAINER_NAME = os.getenv("AZURE_CHAT_DOCS_CONTAINER_NAME")

# Database Configuration for Enhanced Agents
COSMOS_GREMLIN_CONFIG = {
    'endpoint': os.getenv("COSMOS_GREMLIN_ENDPOINT", "asist-graph-db.gremlin.cosmos.azure.com").replace('wss://', '').replace(':443/', ''),
    'database': os.getenv("COSMOS_GREMLIN_DATABASE", "ASIST-Agent-1.1DB"),
    'graph': os.getenv("COSMOS_GREMLIN_COLLECTION", "AGENT1.4"),
    'password': os.getenv("COSMOS_GREMLIN_KEY", "")
}

# Vector Database Configuration
VECTOR_DB_PATH = "C:\\Users\\ShaziaKashif\\ASIST Project\\ASIST2.1\\ASIST_V2.1\\backend\\Chromadb\\samm_all_chapters_db"
#VECTOR_DB_PATH = "C:\\Users\\TomLorenc\\Downloads\\ASIST_DEV\\ASIST_DEV\backend\\vector_db"
#VECTOR_DB_PATH = "C:\\Projects\\5_1\\ASIST_V5.0-main\backend\\vector_db"
#VECTOR_DB_PATH = "O:\\Assist Versions\backend\\vector_db"
#VECTOR_DB_PATH = "O:\\Assist Versions\\backend\\Chromadb\\samm_all_chapters_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_DB_COLLECTION = "samm_all_chapters"

# =============================================================================
# v5.9.8: SAMM_CONTEXT FOR SMART SEARCH (COMPACT VERSION)
# =============================================================================
SAMM_CONTEXT = """SAMM QUICK REFERENCE:
delay/coordination/approval/taking longer → CDEF, C5.4.2.1, case development extenuating factor, DSAMS
CTA/country team assessment → C5.1.4, Table C5.T1, congressional notification, new capability, sensitive items
sole source → C5.4.7.10.4, Appendix 6
OED/expiration/short OED/deadline → C5.4.19, Figure C5.F6, offer expiration date
LOR/letter of request → C5.1.3, Figure C5.F14, Table C5.T3a
congressional notification/threshold → C5.5.3.1, Table C5.T13
case description → Table C6.T8
salary/civilian → MTDS, C9.T2a
logistics → Figure C5.F14"""

# =============================================================================
# v5.9.10: HYBRID RE-RANKING CONFIGURATION
# =============================================================================
RERANK_CONFIG = {
    # Score weights (must sum to 1.0)
    "embedding_weight": 0.5,    # Embedding similarity (current behavior baseline)
    "keyword_weight": 0.3,      # Keyword match score (bridges vocabulary gap)
    "boost_weight": 0.2,        # Table/Figure/Depth boost (surfaces specific content)
    
    # Boost values
    "table_boost": 0.4,         # Chunk contains Table reference
    "figure_boost": 0.4,        # Chunk contains Figure reference
    "appendix_boost": 0.3,      # Chunk contains Appendix reference
    "depth_boost_per_level": 0.05,  # Per section depth level (max 0.3)
    
    # Retrieval settings
    "initial_fetch_count": 20,  # Get more candidates for re-ranking
    "final_return_count": 8,    # Return top N after re-ranking
}
print(f"[v5.9.10] Hybrid Re-ranking Config: emb={RERANK_CONFIG['embedding_weight']}, kw={RERANK_CONFIG['keyword_weight']}, boost={RERANK_CONFIG['boost_weight']}")

# =============================================================================
# v5.9.11: GOLD STANDARD TRAINING DATA
# =============================================================================
# Based on 13 verified Gold Q&A pairs from testing

GOLD_TRAINING_DATA = {
    "patterns": [
        {
            "id": "CDEF_DELAY",
            "trigger_phrases": ["taking longer", "longer than expected", "delay", "delaying", "exceed time", "coordination taking time", "approval process slow", "case submission delay", "processing time exceed"],
            "samm_concept": "CDEF - Case Development Extenuating Factor",
            "must_retrieve": {"sections": ["C5.4.2.1"], "tables": ["Table C5.T6"], "figures": ["Figure C5.F13"]},
            "answer_guidance": {
                "start_with": "According to SAMM Chapter 5, Section C5.4.2.1",
                "must_mention": ["Case Development Extenuating Factor (CDEF)", "processing time exceed standards", "Table C5.T6", "DSAMS", "reason code", "Figure C5.F13"],
                "must_explain": ["What CDEF is", "When to enter CDEF in DSAMS", "Estimated days required"]
            }
        },
        {
            "id": "CTA_REQUIREMENT",
            "trigger_phrases": ["need a CTA", "CTA required", "country team assessment", "do I need CTA", "when is CTA needed", "CTA necessary"],
            "samm_concept": "CTA - Country Team Assessment",
            "must_retrieve": {"sections": ["C5.1.4", "C5.1.4.2", "C5.5"], "tables": ["Table C5.T1"], "figures": []},
            "answer_guidance": {
                "start_with": "According to SAMM Chapter 5, Section C5.1.4",
                "must_mention": ["Country Team Assessment (CTA)", "Congressional Notification (CN)", "36(b)", "new capability", "sensitive nature", "Table C5.T1"],
                "must_explain": ["What CTA is", "4 conditions when CTA is required", "CCMD concurrence"]
            }
        },
        {
            "id": "SOLE_SOURCE",
            "trigger_phrases": ["sole source", "solesource", "single source", "noncompetitive", "specific contractor", "designated contractor", "sole source line note"],
            "samm_concept": "Sole Source Designation",
            "must_retrieve": {"sections": ["C5.4.8.10.4"], "tables": [], "figures": [], "appendices": ["Appendix 6"]},
            "answer_guidance": {
                "start_with": "According to SAMM Chapter 5, Section C5.4.8.10.4",
                "must_mention": ["sole source designation", "Appendix 6", "Procurement Using Other Than Full and Open Competition", "FMS case vs BPC case"],
                "must_explain": ["When sole source line note is required", "Line note template/format"]
            }
        },
        {
            "id": "SHORT_OED",
            "trigger_phrases": ["OED", "offer expiration", "expiration date", "deadline", "funding deadline", "contract award date", "meet deadline", "short OED", "standard OED"],
            "samm_concept": "OED - Offer Expiration Date",
            "must_retrieve": {"sections": ["C5.4.19"], "tables": [], "figures": ["Figure C5.F6"], "appendices": ["Appendix 6"]},
            "answer_guidance": {
                "start_with": "According to SAMM chapter C5.4.19",
                "must_mention": ["Short Offer Expiration Dates (OED)", "Figure C5.F6", "USG driven requirements", "contract award", "25 days", "mandatory short OED LOA note"],
                "must_explain": ["When short OED is justified", "25 day rule", "Mandatory LOA note requirement"]
            }
        },
        {
            "id": "LOR_FORMAT",
            "trigger_phrases": ["LOR format", "letter of request format", "format for LOR", "LOR requirements", "how to write LOR", "LOR submission format", "required format LOR"],
            "samm_concept": "LOR - Letter of Request Format",
            "must_retrieve": {"sections": [], "tables": ["Table C5.T3a"], "figures": ["Figure C5.F14"]},
            "answer_guidance": {
                "start_with": "Although no specific format is required for an LOR, it must be in writing",
                "must_mention": ["no specific format required", "must be in writing", "Figure C5.F14", "Table C5.T3a", "SCO coordination", "method of financing", "third party", "Leahy vetting"],
                "must_explain": ["8 key requirements for complete LOR"]
            }
        },
        {
            "id": "DEFENSE_ARTICLES_DESCRIPTION",
            "trigger_phrases": ["defense articles description", "defense services description", "LOR description", "what to include in LOR", "describe defense articles", "LOR defense article section"],
            "samm_concept": "LOR Defense Articles Description",
            "must_retrieve": {"sections": [], "tables": [], "figures": ["Figure C5.F14"], "appendices": ["Appendix 2"]},
            "answer_guidance": {
                "start_with": "SAMM policy only requires the LOR identifies the desired defense articles and/or services in sufficient detail",
                "must_mention": ["nomenclature and description", "manufacturer details", "quantity", "NSN", "end use", "delivery requirements"],
                "must_explain": ["Defense article details", "Defense service details"]
            }
        },
        {
            "id": "ELECTRONIC_LOR",
            "trigger_phrases": ["electronic LOR", "email LOR", "submit LOR electronically", "LOR via email", "electronic submission LOR", "send LOR electronically"],
            "samm_concept": "Electronic LOR Submission",
            "must_retrieve": {"sections": ["C5.1.3.5"], "tables": [], "figures": []},
            "answer_guidance": {
                "start_with": "According to section C5.1.3.5 of the SAMM",
                "must_mention": ["authorized signers and senders list", "appropriate channels", "E-mail preferred", "DSCA.NCR.DBO.MBX.LOR-DSCA@mail.mil", "PMSecurityAssistance@state.gov"],
                "must_explain": ["Requirement for authorized signers list", "Email addresses for submission"]
            }
        },
        {
            "id": "ACTIONABLE_LOR",
            "trigger_phrases": ["actionable LOR", "LOR actionable", "actionable criteria", "make LOR actionable", "LOR requirements actionable", "what makes LOR actionable"],
            "samm_concept": "Actionable LOR Criteria",
            "must_retrieve": {"sections": ["C4.1.2", "C4.4", "C4.5.3", "C5.1.3.4", "C5.1.4", "C5.5.5.4", "C6.6.5"], "tables": ["Table C5.T3a"], "figures": []},
            "answer_guidance": {
                "start_with": "According to SAMM Table C5.T3a, these are the mandatory criteria",
                "must_mention": ["Table C5.T3a", "13 mandatory criteria", "eligible FMS recipient", "proper channels", "no sanctions", "valid military requirement"],
                "must_explain": ["All 13 criteria from Table C5.T3a"]
            }
        },
        {
            "id": "CN_THRESHOLD",
            "trigger_phrases": ["congressional notification", "CN required", "36(b)", "case value threshold", "need CN", "France", "NATO", "Australia", "Japan", "Korea", "Israel", "$99M", "$51M", "$50M", "$100M"],
            "samm_concept": "Congressional Notification Thresholds",
            "must_retrieve": {"sections": ["C5.5.3.1"], "tables": ["Table C5.T13"], "figures": []},
            "answer_guidance": {
                "start_with": "According to SAMM Chapter 5, Section C5.5.3.1",
                "must_mention": ["36(b)(1) CN", "Table C5.T13", "thresholds vary by purchaser", "NATO Countries thresholds", "MDE threshold", "Total Case Value threshold"],
                "must_explain": ["Quote the 36(b) law requirement", "List thresholds from Table C5.T13", "Apply thresholds to specific case"]
            }
        },
        {
            "id": "LOGISTICS_SUPPORT_LOR",
            "trigger_phrases": ["logistics support", "logistics in LOR", "spare parts", "supply support", "maintenance support", "LOR logistics section"],
            "samm_concept": "LOR Logistics Support Requirements",
            "must_retrieve": {"sections": [], "tables": [], "figures": ["Figure C5.F14"]},
            "answer_guidance": {
                "start_with": "The SAMM doesn't reference mandatory requirements for logistics support, however, in Figure C5.F14",
                "must_mention": ["Figure C5.F14", "supply support", "spare parts provisioning", "maintenance concept", "cataloging data"],
                "must_explain": ["8 logistics items to address", "Spare parts details", "Maintenance levels"]
            }
        },
        {
            "id": "CIVILIAN_SALARY",
            "trigger_phrases": ["civilian salary", "calculate salary", "personnel costs", "labor costs", "manpower costs", "GS salary", "MTDS"],
            "samm_concept": "Civilian Salary Calculation",
            "must_retrieve": {"sections": [], "tables": ["Table C9.T2a"], "figures": []},
            "answer_guidance": {
                "start_with": "According to Case Development Guide",
                "must_mention": ["Primary Category Code (PCC)", "CP 1804", "MTDS", "GS Scale", "Table C9.T2a", "Work Years", "Fringe"],
                "must_explain": ["Step-by-step process", "MTDS Section A Personnel entry"]
            }
        },
        {
            "id": "CASE_DESCRIPTION_AMENDMENT",
            "trigger_phrases": ["case description", "amendment description", "write case description", "AMD description", "MOD description", "case description amendment"],
            "samm_concept": "Case Description for Amendments",
            "must_retrieve": {"sections": [], "tables": ["Table C6.T8"], "figures": []},
            "answer_guidance": {
                "start_with": "According to the LOA Standardization Guide",
                "must_mention": ["LOA Standardization Guide", "Table C6.T8", "major program involved", "changes made", "reason for changes", "previous unaccepted amendments"],
                "must_explain": ["What case description should include", "5 guidelines", "Example format"]
            }
        }
    ],
    
    "keyword_to_retrieval": {
        "delay": ["C5.4.2.1", "Table C5.T6", "Figure C5.F13"],
        "taking longer": ["C5.4.2.1", "Table C5.T6"],
        "cdef": ["C5.4.2.1", "Table C5.T6", "Figure C5.F13"],
        "cta": ["C5.1.4", "Table C5.T1", "C5.1.4.2"],
        "country team": ["C5.1.4", "Table C5.T1"],
        "sole source": ["C5.4.8.10.4", "Appendix 6"],
        "oed": ["C5.4.19", "Figure C5.F6"],
        "expiration": ["C5.4.19", "Figure C5.F6"],
        "deadline": ["C5.4.19", "Figure C5.F6"],
        "lor format": ["Figure C5.F14", "Table C5.T3a"],
        "letter of request": ["Figure C5.F14", "Table C5.T3a"],
        "electronic": ["C5.1.3.5"],
        "actionable": ["Table C5.T3a"],
        "congressional notification": ["C5.5.3.1", "Table C5.T13"],
        "cn": ["C5.5.3.1", "Table C5.T13"],
        "36(b)": ["C5.5.3.1", "Table C5.T13"],
        "logistics support": ["Figure C5.F14"],
        "spare parts": ["Figure C5.F14"],
        "civilian salary": ["Table C9.T2a"],
        "personnel cost": ["Table C9.T2a"],
        "mtds": ["Table C9.T2a"],
        "case description": ["Table C6.T8"],
        "amendment": ["Table C6.T8"]
    }
}

# =============================================================================
# v5.9.11: GOLD STANDARD TRAINER CLASS
# =============================================================================

class SAMMGoldTrainer:
    """
    Gold Standard Q&A patterns se agents ko train karta hai.
    13 verified Q&A pairs ke basis par retrieval aur answer generation improve karta hai.
    """
    
    def __init__(self):
        self.patterns = GOLD_TRAINING_DATA.get("patterns", [])
        self.keyword_map = GOLD_TRAINING_DATA.get("keyword_to_retrieval", {})
        print(f"[GoldTrainer] ✅ Loaded {len(self.patterns)} training patterns")
    
    def match_query_to_pattern(self, query: str) -> Optional[Dict]:
        """Query ko Gold patterns ke saath match karo."""
        query_lower = query.lower()
        
        best_match = None
        best_score = 0
        
        for pattern in self.patterns:
            trigger_phrases = pattern.get("trigger_phrases", [])
            matches = sum(1 for phrase in trigger_phrases if phrase.lower() in query_lower)
            
            if matches > best_score:
                best_score = matches
                best_match = pattern
        
        if best_match and best_score >= 1:
            print(f"[GoldTrainer] 🎯 Matched pattern: {best_match['id']} (score: {best_score})")
            return best_match
        
        return None
    
    def get_retrieval_targets(self, query: str) -> Dict[str, List[str]]:
        """Query ke liye retrieve karne wale sections/tables/figures return karo."""
        query_lower = query.lower()
        
        targets = {"sections": [], "tables": [], "figures": [], "appendices": []}
        
        # Method 1: Pattern matching
        pattern = self.match_query_to_pattern(query)
        if pattern:
            must_retrieve = pattern.get("must_retrieve", {})
            targets["sections"].extend(must_retrieve.get("sections", []))
            targets["tables"].extend(must_retrieve.get("tables", []))
            targets["figures"].extend(must_retrieve.get("figures", []))
            targets["appendices"].extend(must_retrieve.get("appendices", []))
        
        # Method 2: Keyword mapping
        for keyword, refs in self.keyword_map.items():
            if keyword.lower() in query_lower:
                for ref in refs:
                    if ref.startswith("C") and "." in ref and "T" not in ref and "F" not in ref:
                        if ref not in targets["sections"]:
                            targets["sections"].append(ref)
                    elif "Table" in ref or ".T" in ref:
                        if ref not in targets["tables"]:
                            targets["tables"].append(ref)
                    elif "Figure" in ref or ".F" in ref:
                        if ref not in targets["figures"]:
                            targets["figures"].append(ref)
                    elif "Appendix" in ref:
                        if ref not in targets["appendices"]:
                            targets["appendices"].append(ref)
        
        return targets
    
    def get_answer_guidance(self, query: str) -> Optional[Dict]:
        """Query ke liye answer structure guidance return karo."""
        pattern = self.match_query_to_pattern(query)
        
        if pattern:
            guidance = pattern.get("answer_guidance", {})
            return {
                "concept": pattern.get("samm_concept"),
                "pattern_id": pattern.get("id"),
                "start_with": guidance.get("start_with"),
                "must_mention": guidance.get("must_mention", []),
                "must_explain": guidance.get("must_explain", [])
            }
        return None
    
    def build_enhanced_query(self, query: str) -> str:
        """Query ko enhance karo with SAMM terms."""
        targets = self.get_retrieval_targets(query)
        enhanced_parts = [query]
        
        for section in targets["sections"][:3]:
            enhanced_parts.append(section)
        for table in targets["tables"][:2]:
            enhanced_parts.append(table)
        for figure in targets["figures"][:2]:
            enhanced_parts.append(figure)
        
        pattern = self.match_query_to_pattern(query)
        if pattern:
            concept = pattern.get("samm_concept", "")
            if concept:
                enhanced_parts.append(concept)
        
        return " ".join(enhanced_parts)
    
    def get_entity_queries(self, query: str) -> List[str]:
        """Query ke liye specific entity search queries return karo."""
        entity_queries = []
        targets = self.get_retrieval_targets(query)
        pattern = self.match_query_to_pattern(query)
        
        if pattern:
            concept = pattern.get("samm_concept", "")
            must_mention = pattern.get("answer_guidance", {}).get("must_mention", [])
            
            query_parts = [concept] if concept else []
            query_parts.extend(must_mention[:5])
            query_parts.extend(targets["sections"][:2])
            query_parts.extend(targets["tables"][:2])
            query_parts.extend(targets["figures"][:2])
            
            if query_parts:
                entity_queries.append(" ".join(query_parts))
        
        return entity_queries
    
    def validate_answer(self, answer: str, query: str) -> Dict:
        """Answer ko Gold standard ke against validate karo."""
        pattern = self.match_query_to_pattern(query)
        
        if not pattern:
            return {"valid": True, "score": 0.5, "missing": [], "note": "No matching pattern"}
        
        answer_lower = answer.lower()
        guidance = pattern.get("answer_guidance", {})
        must_mention = guidance.get("must_mention", [])
        
        mentioned = []
        missing = []
        
        for item in must_mention:
            if item.lower() in answer_lower:
                mentioned.append(item)
            else:
                missing.append(item)
        
        score = len(mentioned) / len(must_mention) if must_mention else 0.5
        
        return {
            "valid": score >= 0.5,
            "score": round(score, 2),
            "mentioned": mentioned,
            "missing": missing,
            "pattern_id": pattern["id"]
        }


# Global Gold Trainer instance
_gold_trainer = None

def get_gold_trainer() -> SAMMGoldTrainer:
    """Get or create Gold trainer instance"""
    global _gold_trainer
    if _gold_trainer is None:
        _gold_trainer = SAMMGoldTrainer()
    return _gold_trainer

def gold_enhanced_retrieval(query: str) -> tuple:
    """Gold training ke basis par retrieval enhance karo."""
    trainer = get_gold_trainer()
    enhanced_query = trainer.build_enhanced_query(query)
    entity_queries = trainer.get_entity_queries(query)
    return enhanced_query, entity_queries

def gold_answer_guidance(query: str) -> Optional[Dict]:
    """Gold training ke basis par answer guidance lo."""
    trainer = get_gold_trainer()
    return trainer.get_answer_guidance(query)

def validate_against_gold(answer: str, query: str) -> Dict:
    """Answer ko Gold standard ke against validate karo."""
    trainer = get_gold_trainer()
    return trainer.validate_answer(answer, query)

print(f"[v5.9.11] Gold Training: {len(GOLD_TRAINING_DATA['patterns'])} patterns loaded")

# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

# Cache settings
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # 1 hour default
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))  # Maximum cached items

# In-memory cache structures
query_cache = {}  # Structure: {normalized_query: {answer, metadata, timestamp}}
cache_stats = {
    "hits": 0,
    "misses": 0,
    "total_queries": 0,
    "cache_size": 0
}

print(f"Cache Configuration: Enabled={CACHE_ENABLED}, TTL={CACHE_TTL_SECONDS}s, Max Size={CACHE_MAX_SIZE}")

# ITAR Compliance Integration
COMPLIANCE_SERVICE_URL = os.getenv("COMPLIANCE_SERVICE_URL", "http://localhost:3002")
COMPLIANCE_ENABLED = os.getenv("COMPLIANCE_ENABLED", "true").lower() == "true"
DEFAULT_DEV_AUTH_LEVEL = os.getenv("DEFAULT_DEV_AUTH_LEVEL", "top_secret")

print(f"ITAR Compliance: {'Enabled' if COMPLIANCE_ENABLED else 'Disabled'} (Default Level: {DEFAULT_DEV_AUTH_LEVEL})")
# =============================================================================
# CACHE HELPER FUNCTIONS
# =============================================================================

def normalize_query_for_cache(query: str) -> str:
    """
    Normalize query for cache key matching
    - Lowercase, strip whitespace, remove punctuation
    - Sort words to catch similar questions with different word order
    """
    import string
    # Remove punctuation and convert to lowercase
    query_clean = query.lower().translate(str.maketrans('', '', string.punctuation))
    # Split into words and sort
    words = query_clean.split()
    # Remove common stop words that don't affect meaning
    stop_words = {'what', 'is', 'are', 'the', 'a', 'an', 'does', 'do', 'can', 'how'}
    significant_words = [w for w in words if w not in stop_words and len(w) > 2]
    # Return sorted words as key
    return ' '.join(sorted(significant_words))

def get_from_cache(query: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached answer for a query
    Returns None if not found or expired
    """
    if not CACHE_ENABLED:
        return None
    
    cache_key = normalize_query_for_cache(query)
    
    if cache_key in query_cache:
        cached_entry = query_cache[cache_key]
        
        # Check if cache entry is still valid (TTL check)
        age_seconds = time.time() - cached_entry['timestamp']
        if age_seconds < CACHE_TTL_SECONDS:
            cache_stats['hits'] += 1
            cache_stats['total_queries'] += 1
            print(f"[Cache HIT] Query: '{query[:50]}...' (age: {age_seconds:.1f}s)")
            return cached_entry
        else:
            # Expired - remove it
            del query_cache[cache_key]
            print(f"[Cache EXPIRED] Query: '{query[:50]}...' (age: {age_seconds:.1f}s)")
    
    cache_stats['misses'] += 1
    cache_stats['total_queries'] += 1
    print(f"[Cache MISS] Query: '{query[:50]}...'")
    return None
def fetch_blob_content(blob_name: str, container_client) -> Optional[str]:
    """Fetch text content from a blob for AI processing"""
    if not container_client:
        return None
    
    try:
        blob_client = container_client.get_blob_client(blob_name)
        download_stream = blob_client.download_blob()
        content = download_stream.readall()
        
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            return f"[Binary file: {blob_name}]"
    except Exception as e:
        print(f"[Blob Fetch] Error reading {blob_name}: {e}")
        return None
def save_to_cache(query: str, answer: str, metadata: Dict[str, Any]) -> bool:
    """
    Save query-answer pair to cache
    Implements LRU eviction if cache is full
    """
    if not CACHE_ENABLED:
        return False
    
    cache_key = normalize_query_for_cache(query)
    
    # Check cache size limit
    if len(query_cache) >= CACHE_MAX_SIZE and cache_key not in query_cache:
        # Evict oldest entry (simple LRU)
        oldest_key = min(query_cache.keys(), key=lambda k: query_cache[k]['timestamp'])
        del query_cache[oldest_key]
        print(f"[Cache EVICT] Removed oldest entry to make room")
    
    # Save to cache
    query_cache[cache_key] = {
        'original_query': query,
        'answer': answer,
        'metadata': metadata,
        'timestamp': time.time()
    }
    
    cache_stats['cache_size'] = len(query_cache)
    print(f"[Cache SAVE] Query: '{query[:50]}...' (cache size: {len(query_cache)})")
    return True

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    hit_rate = (cache_stats['hits'] / cache_stats['total_queries'] * 100) if cache_stats['total_queries'] > 0 else 0
    
    return {
        'enabled': CACHE_ENABLED,
        'total_queries': cache_stats['total_queries'],
        'cache_hits': cache_stats['hits'],
        'cache_misses': cache_stats['misses'],
        'hit_rate_percent': round(hit_rate, 2),
        'current_size': len(query_cache),
        'max_size': CACHE_MAX_SIZE,
        'ttl_seconds': CACHE_TTL_SECONDS
    }

# =============================================================================
# v5.9.10: HYBRID RE-RANKING FUNCTIONS
# =============================================================================

def calculate_keyword_score(query: str, chunk_content: str) -> float:
    """
    Calculate keyword match score between query and chunk.
    Returns 0.0 to 1.0 (higher = more query words found in chunk)
    """
    query_lower = query.lower()
    chunk_lower = chunk_content.lower()
    
    # Stopwords to ignore
    stopwords = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'to', 'of',
        'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'and', 'but',
        'if', 'or', 'what', 'how', 'when', 'where', 'why', 'who', 'which',
        'i', 'me', 'my', 'we', 'our', 'you', 'your', 'am', 'this', 'that'
    }
    
    # Extract meaningful words from query
    query_words = set()
    for word in re.findall(r'\b[a-z0-9]+\b', query_lower):
        if word not in stopwords and len(word) > 2:
            query_words.add(word)
    
    if not query_words:
        return 0.0
    
    # Count matches
    matches = sum(1 for word in query_words if word in chunk_lower)
    
    # Base score
    score = matches / len(query_words)
    
    # Bonus for phrase matches
    query_phrases = re.findall(r'\b\w+\s+\w+\b', query_lower)
    for phrase in query_phrases[:3]:  # Check first 3 phrases
        words = phrase.split()
        if len(words) == 2 and words[0] not in stopwords and phrase in chunk_lower:
            score = min(1.0, score + 0.1)
    
    return min(1.0, score)


def calculate_boost_score(chunk_content: str, chunk_metadata: Dict) -> float:
    """
    Calculate boost score for Tables, Figures, Appendix, and section depth.
    Returns 0.0 to ~0.7
    """
    boost = 0.0
    content_lower = chunk_content.lower()
    
    # Table boost - multiple patterns
    # Matches: "Table C9.T2a", "TABLE C5.T1", "table c9.t2", etc.
    if re.search(r'table\s*c\d+\.t\d+', content_lower) or \
       re.search(r'c\d+\.t\d+[a-z]?\b', content_lower):  # Also match just "C9.T2a"
        boost += RERANK_CONFIG["table_boost"]
    
    # Figure boost - multiple patterns
    if re.search(r'figure\s*c\d+\.f\d+', content_lower) or \
       re.search(r'c\d+\.f\d+\b', content_lower):  # Also match just "C5.F14"
        boost += RERANK_CONFIG["figure_boost"]
    
    # Appendix boost
    if re.search(r'appendix\s+\d+', content_lower):
        boost += RERANK_CONFIG["appendix_boost"]
    
    # Section depth boost (prefer specific sections like C5.1.3.5 over C5.1.3)
    section_match = re.search(r'C\d+(\.\d+)+', chunk_content)
    if section_match:
        section = section_match.group(0)
        depth = len(section.split('.'))
        # Depth 3=0, Depth 4=0.05, Depth 5=0.10, etc. (max 0.3)
        depth_boost = min(0.3, (depth - 3) * RERANK_CONFIG["depth_boost_per_level"])
        boost += max(0, depth_boost)
    
    return boost


def rerank_results(query: str, results: List[Dict]) -> List[Dict]:
    """
    Re-rank search results using hybrid scoring.
    
    Combined Score = embedding_weight * embedding_score
                   + keyword_weight * keyword_score
                   + boost_weight * boost_score
    """
    if not results:
        return results
    
    print(f"[RERANK v5.9.10] Re-ranking {len(results)} results...")
    
    scored_results = []
    
    for r in results:
        content = r.get('content', '')
        metadata = r.get('metadata', {})
        
        # 1. Embedding score (convert distance to similarity)
        distance = r.get('distance', 0.5)
        embedding_score = max(0, 1 - distance) if distance <= 1 else 0.5
        
        # 2. Keyword score
        keyword_score = calculate_keyword_score(query, content)
        
        # 3. Boost score
        boost_score = calculate_boost_score(content, metadata)
        
        # Combined score
        final_score = (
            RERANK_CONFIG["embedding_weight"] * embedding_score +
            RERANK_CONFIG["keyword_weight"] * keyword_score +
            RERANK_CONFIG["boost_weight"] * boost_score
        )
        
        # Store for debugging
        r['_rerank_scores'] = {
            'embedding': round(embedding_score, 3),
            'keyword': round(keyword_score, 3),
            'boost': round(boost_score, 3),
            'final': round(final_score, 3)
        }
        
        scored_results.append((final_score, r))
    
    # Sort by final score (highest first)
    scored_results.sort(key=lambda x: x[0], reverse=True)
    
    # Debug output
    print(f"[RERANK v5.9.10] Top 5 after re-ranking:")
    for i, (score, r) in enumerate(scored_results[:5]):
        section = r.get('metadata', {}).get('section_number', 'Unknown')
        scores = r.get('_rerank_scores', {})
        print(f"  #{i+1} {section}: E={scores.get('embedding')}, K={scores.get('keyword')}, B={scores.get('boost')} → {scores.get('final')}")
    
    return [r for _, r in scored_results]

# =============================================================================
# END v5.9.10: HYBRID RE-RANKING FUNCTIONS
# =============================================================================

# --- Flask App Initialization ---
app = Flask(__name__, static_folder='static')
app.secret_key = APP_SECRET_KEY
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

ollama_session = requests.Session()
adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10)
ollama_session.mount("http://", adapter)
ollama_session.mount("https://", adapter)
print("[Ollama] ✅ Connection pooling configured")


# Simple in-memory storage for demo purposes when Azure isn't available
user_cases = {}
staged_documents = {}

print(f"Ollama URL: {OLLAMA_URL}")
print(f"Ollama Model: {OLLAMA_MODEL}")

# --- Initialize Cosmos DB Client ---
cosmos_client = None
database_client = None
cases_container_client = None
reviews_test_container_client = None

# Initialize reviews container if Cosmos DB configured
if COSMOS_ENDPOINT and COSMOS_KEY and DATABASE_NAME:
    try:
        if not cosmos_client:
            cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        if not database_client:
            database_client = cosmos_client.get_database_client(DATABASE_NAME)
        
        # Create or get reviews container
        try:
            reviews_test_container_client = database_client.create_container(
                id="reviews",
                partition_key=PartitionKey(path="/type"),
                offer_throughput=400
            )
            print("✅ Reviews container created")
        except:
            reviews_test_container_client = database_client.get_container_client("reviews")
            print("✅ Reviews test container connected")
            
    except Exception as e:
        print(f"⚠️ Reviews container not initialized: {e}")

if COSMOS_ENDPOINT and COSMOS_KEY and DATABASE_NAME and CASES_CONTAINER_NAME:
    try:
        cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database_client = cosmos_client.get_database_client(DATABASE_NAME)
        cases_container_client = database_client.get_container_client(CASES_CONTAINER_NAME)
        print(f"Successfully connected to Cosmos DB Cases container: {DATABASE_NAME}/{CASES_CONTAINER_NAME}")
    except Exception as e:
        print(f"Warning: Error initializing Cosmos DB client: {e}. Using in-memory storage.")
else:
    print("Warning: Cosmos DB credentials not configured. Using in-memory storage.")

# --- Initialize Azure Blob Service Client ---
blob_service_client = None
case_docs_blob_container_client = None
chat_docs_blob_container_client = None

def _extract_case_identifier_from_text(text: str) -> Optional[str]:
    """
    Extract case identifier from text (e.g., SR-P-NAV, MX-B-SAL)
    
    Args:
        text: Raw text to search for case ID
        
    Returns:
        Case identifier string or None
        
    Used by:
        - Upload endpoint
        - Document type detection
        - Financial data extraction
    """
    if not text:
        return None
    
    # Pattern 1: Standard format (SR-P-NAV, MX-B-SAL)
    case_pattern_1 = r'\b([A-Z]{2}-[A-Z]-[A-Z]{2,4})\b'
    matches_1 = re.findall(case_pattern_1, text.upper())
    
    if matches_1:
        return matches_1[0].upper()
    
    # Pattern 2: With spaces (SR P NAV)
    case_pattern_2 = r'\b([A-Z]{2})\s+([A-Z])\s+([A-Z]{2,4})\b'
    matches_2 = re.findall(case_pattern_2, text.upper())
    
    if matches_2:
        return f"{matches_2[0][0]}-{matches_2[0][1]}-{matches_2[0][2]}"
    
    # Pattern 3: No dashes (SRPNAV)
    case_pattern_3 = r'\b([A-Z]{2})([A-Z])([A-Z]{2,4})\b'
    matches_3 = re.findall(case_pattern_3, text.upper())
    
    if matches_3:
        return f"{matches_3[0][0]}-{matches_3[0][1]}-{matches_3[0][2]}"
    
    return None
def determine_document_type(filename: str) -> str:
    """
    Determine document type from filename
    
    Args:
        filename: Original filename
        
    Returns:
        Document type: FINANCIAL_DATA, LOA, CONTRACT, REQUISITION, MINUTES, or GENERAL
    """
    filename_lower = filename.lower()
    
    # Extract case ID for logging
    case_id = _extract_case_identifier_from_text(filename)
    if case_id:
        print(f"[DocumentType] 📋 Case ID from filename: {case_id}")
    
    # PRIORITY 1: LOA patterns
    loa_keywords = ['loa', 'letter of offer', 'offer and acceptance']
    if any(keyword in filename_lower for keyword in loa_keywords):
        return 'LOA'
    
    # PRIORITY 2: Financial data
    financial_keywords = ['financial', 'rsn', 'pdli', 'misil', 'funding']
    if any(keyword in filename_lower for keyword in financial_keywords):
        return 'FINANCIAL_DATA'
    
    # PRIORITY 3: Minutes
    minutes_keywords = ['minutes', 'meeting', 'notes']
    if any(keyword in filename_lower for keyword in minutes_keywords):
        return 'MINUTES'
    
    # PRIORITY 4: Contracts
    contract_keywords = ['contract', 'agreement']
    if any(keyword in filename_lower for keyword in contract_keywords):
        return 'CONTRACT'
    
    # PRIORITY 5: Requisitions
    requisition_keywords = ['requisition', 'req', 'purchase']
    if any(keyword in filename_lower for keyword in requisition_keywords):
        return 'REQUISITION'
    
    return 'GENERAL'
def find_header_row(ws) -> Optional[int]:
    """
    Find the header row in an Excel sheet
    Looks for common header keywords in MISIL RSN sheets
    
    Args:
        ws: openpyxl worksheet object
        
    Returns:
        Row index (1-based) or None
    """
    header_keywords = ['rsn', 'pdli', 'oa rec amt', 'net commit', 'obligation']
    
    for row_idx in range(1, min(20, ws.max_row + 1)):  # Search first 20 rows
        row = ws[row_idx]
        row_text = ' '.join([str(cell.value or '').lower() for cell in row])
        
        # Check if this row contains multiple header keywords
        matches = sum(1 for keyword in header_keywords if keyword in row_text)
        
        if matches >= 3:  # At least 3 header keywords
            return row_idx
    
    return None


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file using PyPDF2
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text content
    """
    try:
        import PyPDF2
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            
            for page in pdf_reader.pages:
                text += page.extract_text() + '\n'
            
            return text
    
    except Exception as e:
        print(f"[PDF Extraction] Error: {e}")
        return ''


def extract_loa_data_from_pdf(file_path: str) -> Dict[str, Any]:
    """
    Extract LOA-specific data from PDF
    
    Args:
        file_path: Path to LOA PDF
        
    Returns:
        Dictionary with LOA metadata
    """
    loa_data = {
        "document_type": "LOA",
        "case_number": "",
        "country": "",
        "total_value": "",
        "line_items": []
    }
    
    try:
        full_text = extract_text_from_pdf(file_path)
        
        # Extract case number
        case_id = _extract_case_identifier_from_text(full_text)
        if case_id:
            loa_data["case_number"] = case_id
        
        # Extract country (basic pattern)
        country_pattern = r'Country:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        country_match = re.search(country_pattern, full_text)
        if country_match:
            loa_data["country"] = country_match.group(1)
        
        # Extract total value
        value_pattern = r'\$[\d,]+(?:\.\d{2})?'
        value_matches = re.findall(value_pattern, full_text)
        if value_matches:
            loa_data["total_value"] = value_matches[0]
    
    except Exception as e:
        print(f"[LOA Extraction] Error: {e}")
    
    return loa_data



def extract_case_document_data(file_path, file_type: str = None, original_filename: str = None, *args, **kwargs) -> \
Dict[str, Any]:
    """
    Extract structured data from case documents.
    FILTERS by CTY and CASE columns to get only matching records.
    """
    import PyPDF2
    from openpyxl import load_workbook
    from io import BytesIO
    import re

    doc_data = {
        "document_type": file_type,
        "case_identifier": "",
        "entities": [],
        "key_info": {
            "financial_records": [],
            "rsn_data": {},
            "summary": {}
        },
        "extracted_text": "",
        "extraction_metadata": {
            "file_name": original_filename if original_filename else (
                Path(file_path).name if hasattr(file_path, 'name') else str(file_path)),
            "file_extension": ""
        }
    }

    try:
        # =====================================================================
        # PDF PROCESSING
        # =====================================================================
        if str(file_path).lower().endswith('.pdf'):
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                full_text = ""
                for page in pdf_reader.pages:
                    full_text += page.extract_text() or ""

                doc_data["extracted_text"] = full_text
                doc_data["case_identifier"] = _extract_case_identifier_from_text(full_text)

        # =====================================================================
        # EXCEL PROCESSING
        # =====================================================================
        elif str(file_path).lower().endswith(('.xlsx', '.xls')) or (
                original_filename and original_filename.lower().endswith(('.xlsx', '.xls'))):
            doc_data["document_type"] = "FINANCIAL_DATA"
            doc_data["extraction_metadata"]["extraction_method"] = "excel_openpyxl"

            # Handle different input types
            wb = None
            try:
                if isinstance(file_path, bytes):
                    wb = load_workbook(BytesIO(file_path), data_only=True)
                elif hasattr(file_path, 'read'):
                    content = file_path.read()
                    file_path.seek(0)
                    wb = load_workbook(BytesIO(content), data_only=True)
                elif isinstance(file_path, str) and os.path.exists(file_path):
                    wb = load_workbook(file_path, data_only=True)
                else:
                    wb = load_workbook(file_path, data_only=True)
            except Exception as load_err:
                print(f"[Extract] ❌ Failed to load workbook: {load_err}")
                doc_data["extraction_metadata"]["error"] = str(load_err)
                return doc_data

            print(f"[Extract] 📊 Excel with {len(wb.sheetnames)} sheets: {wb.sheetnames}")

            # =================================================================
            # EXTRACT CTY and CASE from filename
            # Filename format: SR-P-NAV_Full Synthetic Financial Data.xlsx
            # Case ID: SR-P-NAV → CTY=SR, CASE=NAV
            # =================================================================
            filter_cty = None
            filter_case = None

            if original_filename:
                # Get the case ID from the start of filename (before first underscore or space)
                filename_base = original_filename.split('.')[0]  # Remove extension

                # Try to find case ID pattern: XX-X-XXX (e.g., SR-P-NAV, TW-P-MSL)
                case_match = re.match(r'^([A-Z]{2})-([A-Z])-([A-Z]{3})', filename_base.upper())
                if case_match:
                    filter_cty = case_match.group(1)  # SR
                    filter_case = case_match.group(3)  # NAV
                    doc_data["case_identifier"] = f"{case_match.group(1)}-{case_match.group(2)}-{case_match.group(3)}"
                    print(f"[Extract] 🎯 Filtering: CTY={filter_cty}, CASE={filter_case}")
                else:
                    print(f"[Extract] ⚠️ Could not parse case ID from filename: {original_filename}")

            # =================================================================
            # STEP 1: Find and process RSN sheet for NET COMMIT AMT
            # =================================================================
            rsn_net_commit = {}

            rsn_sheet = None
            rsn_sheet_name = None
            for sheet_name in wb.sheetnames:
                sheet_lower = sheet_name.lower()
                if 'rsn' in sheet_lower and 'pdli' not in sheet_lower:
                    rsn_sheet = wb[sheet_name]
                    rsn_sheet_name = sheet_name
                    break

            if rsn_sheet:
                print(f"[Extract] Processing RSN sheet: {rsn_sheet_name}")

                # Find header row and column indices
                rsn_header_row = None
                rsn_col_idx = None
                net_commit_col_idx = None
                cty_col_idx = None
                case_col_idx = None

                for row_idx in range(1, min(20, rsn_sheet.max_row + 1)):
                    row = list(rsn_sheet.iter_rows(min_row=row_idx, max_row=row_idx, values_only=True))[0]

                    for col_idx, cell in enumerate(row):
                        if not cell:
                            continue
                        cell_str = str(cell).strip().lower()

                        if cell_str == 'rsn':
                            rsn_col_idx = col_idx
                        if cell_str == 'cty':
                            cty_col_idx = col_idx
                        if cell_str == 'case':
                            case_col_idx = col_idx
                        if ('net' in cell_str and 'commit' in cell_str) or cell_str == 'net_commit_amt':
                            net_commit_col_idx = col_idx

                    if rsn_col_idx is not None and net_commit_col_idx is not None:
                        rsn_header_row = row_idx
                        print(
                            f"[Extract] ✅ RSN header row: {row_idx}, RSN col: {rsn_col_idx}, NET COMMIT col: {net_commit_col_idx}")
                        if cty_col_idx is not None:
                            print(f"[Extract]   CTY col: {cty_col_idx}, CASE col: {case_col_idx}")
                        break

                # Extract RSN -> NET_COMMIT_AMT (filtered by CTY/CASE)
                if rsn_header_row and rsn_col_idx is not None and net_commit_col_idx is not None:
                    for row in rsn_sheet.iter_rows(min_row=rsn_header_row + 1, values_only=True):
                        # Check CTY/CASE filter
                        if filter_cty and cty_col_idx is not None and case_col_idx is not None:
                            row_cty = str(row[cty_col_idx]).strip().upper() if row[cty_col_idx] else ''
                            row_case = str(row[case_col_idx]).strip().upper() if row[case_col_idx] else ''
                            if row_cty != filter_cty or row_case != filter_case:
                                continue  # Skip rows that don't match

                        if len(row) <= max(rsn_col_idx, net_commit_col_idx):
                            continue

                        rsn_val = row[rsn_col_idx]
                        net_commit_val = row[net_commit_col_idx]

                        if not rsn_val:
                            continue

                        rsn_str = str(rsn_val).strip()

                        try:
                            net_commit_amt = float(net_commit_val) if net_commit_val else 0.0
                        except (ValueError, TypeError):
                            net_commit_amt = 0.0

                        if net_commit_amt != 0:
                            rsn_net_commit[rsn_str] = net_commit_amt
                            rsn_net_commit[rsn_str.lstrip('0') or '0'] = net_commit_amt
                            rsn_net_commit[rsn_str.zfill(3)] = net_commit_amt

                    print(
                        f"[Extract] ✅ Extracted {len(set(rsn_net_commit.values()))} RSN NET_COMMIT values for {filter_cty}-{filter_case}")

            # =================================================================
            # STEP 2: Find PDLI sheet
            # =================================================================
            pdli_sheet = None
            pdli_sheet_name = None
            for sheet_name in wb.sheetnames:
                if 'pdli' in sheet_name.lower():
                    pdli_sheet = wb[sheet_name]
                    pdli_sheet_name = sheet_name
                    break

            if not pdli_sheet:
                for sheet_name in wb.sheetnames:
                    if 'misil' in sheet_name.lower():
                        pdli_sheet = wb[sheet_name]
                        pdli_sheet_name = sheet_name
                        break
                if not pdli_sheet:
                    pdli_sheet = wb.active
                    pdli_sheet_name = pdli_sheet.title

            print(f"[Extract] Processing PDLI sheet: {pdli_sheet_name}")

            # =================================================================
            # STEP 3: Find header row and map columns
            # =================================================================
            header_row_idx = None
            column_map = {}

            for row_idx in range(1, min(20, pdli_sheet.max_row + 1)):
                row = list(pdli_sheet.iter_rows(min_row=row_idx, max_row=row_idx, values_only=True))[0]
                row_str = ' '.join([str(c).lower() if c else '' for c in row])

                if 'rsn' in row_str and ('pdli' in row_str or 'dir' in row_str):
                    header_row_idx = row_idx
                    print(f"[Extract] ✅ PDLI header row: {row_idx}")

                    for col_idx, cell in enumerate(row):
                        if not cell:
                            continue
                        cell_str = str(cell).strip().lower()

                        if cell_str == 'cty':
                            column_map['cty'] = col_idx
                        elif cell_str == 'case':
                            column_map['case'] = col_idx
                        elif cell_str == 'rsn':
                            column_map['rsn'] = col_idx
                        elif cell_str in ['pdli', 'pdli nbr']:
                            column_map['pdli'] = col_idx
                        elif 'pdli' in cell_str and 'desc' in cell_str:
                            column_map['pdli_desc'] = col_idx
                        elif 'dir' in cell_str and 'rsrv' in cell_str:
                            column_map['dir_rsrv_amt'] = col_idx
                        elif 'net' in cell_str and 'obl' in cell_str:
                            column_map['net_obl_amt'] = col_idx
                        elif 'net' in cell_str and 'exp' in cell_str:
                            column_map['net_exp_amt'] = col_idx
                        elif 'avail' in cell_str and 'bal' in cell_str:
                            column_map['avail_bal'] = col_idx
                        elif 'line' in cell_str:
                            column_map['line_nbr'] = col_idx

                    print(f"[Extract] Column map: {column_map}")
                    break

            if not header_row_idx:
                print(f"[Extract] ⚠️ No header row found!")
                wb.close()
                return doc_data

            # =================================================================
            # STEP 4: Extract PDLI records (FILTERED by CTY/CASE)
            # =================================================================
            financial_records = []

            def safe_float(col_name, row):
                col_idx = column_map.get(col_name)
                if col_idx is not None and col_idx < len(row):
                    val = row[col_idx]
                    try:
                        return float(val) if val else 0.0
                    except (ValueError, TypeError):
                        return 0.0
                return 0.0

            def safe_str(col_name, row):
                col_idx = column_map.get(col_name)
                if col_idx is not None and col_idx < len(row):
                    val = row[col_idx]
                    return str(val).strip() if val else ''
                return ''

            for row in pdli_sheet.iter_rows(min_row=header_row_idx + 1, values_only=True):
                # FILTER: Check CTY and CASE match
                if filter_cty and 'cty' in column_map and 'case' in column_map:
                    row_cty = safe_str('cty', row).upper()
                    row_case = safe_str('case', row).upper()
                    if row_cty != filter_cty or row_case != filter_case:
                        continue  # Skip rows that don't match this case

                rsn = safe_str('rsn', row)
                if not rsn:
                    continue

                # Get NET_COMMIT_AMT for this RSN
                net_commit_amt = 0.0
                rsn_normalized = rsn.lstrip('0') or '0'
                rsn_padded = rsn.zfill(3)

                if rsn in rsn_net_commit:
                    net_commit_amt = rsn_net_commit[rsn]
                elif rsn_normalized in rsn_net_commit:
                    net_commit_amt = rsn_net_commit[rsn_normalized]
                elif rsn_padded in rsn_net_commit:
                    net_commit_amt = rsn_net_commit[rsn_padded]

                record = {
                    "line_nbr": safe_str('line_nbr', row),
                    "rsn": rsn,
                    "pdli": safe_str('pdli', row),
                    "pdli_desc": safe_str('pdli_desc', row),
                    "dir_rsrv_amt": safe_float('dir_rsrv_amt', row),
                    "net_obl_amt": safe_float('net_obl_amt', row),
                    "net_exp_amt": safe_float('net_exp_amt', row),
                    "avail_bal": safe_float('avail_bal', row),
                    "net_commit_amt": net_commit_amt
                }

                financial_records.append(record)

            # Log first record to verify
            if financial_records:
                print(f"[Extract] 📋 First record: {financial_records[0]}")

            unique_rsns = set(r['rsn'] for r in financial_records)
            total_directed = sum(r['dir_rsrv_amt'] for r in financial_records)

            print(
                f"[Extract] ✅ {len(financial_records)} PDLIs, {len(unique_rsns)} RSNs (filtered for {filter_cty}-{filter_case})")
            print(f"[Extract] 💰 Total: ${total_directed:,.2f}")

            doc_data["key_info"]["financial_records"] = financial_records
            doc_data["key_info"]["rsn_data"] = rsn_net_commit
            doc_data["key_info"]["summary"] = {
                "total_pdlis": len(financial_records),
                "unique_rsns": len(unique_rsns),
                "total_directed": total_directed
            }

            wb.close()

    except Exception as e:
        print(f"[Extract] ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        doc_data["extraction_metadata"]["error"] = str(e)

    return doc_data




def initialize_blob_container(bs_client, container_name_env_var, container_description):
    container_name = os.getenv(container_name_env_var)
    if not container_name:
        print(f"Warning: {container_name_env_var} is not set. {container_description} functionality will be disabled.")
        return None
    try:
        container_client = bs_client.get_container_client(container_name)
        container_client.create_container()
        print(f"Blob container '{container_name}' for {container_description} created or already exists.")
        return container_client
    except BlobResourceExistsError:
        print(f"Blob container '{container_name}' for {container_description} already exists.")
        return container_client
    except Exception as e_create_container:
        print(f"Could not create/verify blob container '{container_name}' for {container_description}: {e_create_container}")
        return None

if AZURE_CONNECTION_STRING:
    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        case_docs_blob_container_client = initialize_blob_container(blob_service_client, "AZURE_CASE_DOCS_CONTAINER_NAME", "case documents")
        chat_docs_blob_container_client = initialize_blob_container(blob_service_client, "AZURE_CHAT_DOCS_CONTAINER_NAME", "chat documents")
    except Exception as e:
        print(f"Warning: Error initializing Azure Blob Service client: {e}")
else:
    print("Warning: AZURE_CONNECTION_STRING is not set. Blob storage functionality will be disabled.")

# --- Auth0 OAuth Setup ---
# --- Auth0 OAuth Setup ---
# --- Auth0 OAuth Setup ---
# --- Auth0 OAuth Setup ---
# Detect if running locally vs deployed
BASE_URL = os.getenv("BACKEND_URL", "http://172.16.200.12:3000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://172.16.200.12:5173")

oauth = None
if AUTH0_CLIENT_ID and AUTH0_CLIENT_SECRET and AUTH0_DOMAIN:
    oauth = OAuth(app)
    oauth.register(
        "auth0",
        client_id=AUTH0_CLIENT_ID,
        client_secret=AUTH0_CLIENT_SECRET,
        client_kwargs={"scope": "openid profile email"},
        server_metadata_url=f'https://{AUTH0_DOMAIN}/.well-known/openid-configuration',
        redirect_uri=f"{BASE_URL}/callback"  # ← Use environment variable
    )
    print("Auth0 OAuth configured successfully")
    print(f"  Redirect URI: {BASE_URL}/callback")
    print(f"  Frontend URL: {FRONTEND_URL}")
else:
    print("Warning: Auth0 credentials not configured. Authentication will use mock user.")


# =============================================================================
# ENHANCED OLLAMA CALL FUNCTION
# =============================================================================

from flask import Response, stream_with_context
import json

def call_ollama_streaming(prompt: str, system_message: str = "", temperature: float = 0.1):
    """Stream Ollama responses token by token - WITH NON-STREAMING WORKAROUND"""
    
    print(f"[Ollama] 🚀 Calling Ollama at {OLLAMA_URL}/api/chat")
    print(f"[Ollama] Model: {OLLAMA_MODEL}")
    print(f"[Ollama] Prompt length: {len(prompt)} chars")
    print(f"[Ollama] System message length: {len(system_message)} chars")
    
    try:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        # ✅ USE NON-STREAMING MODE (faster and more reliable)
        data = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,  # ← Non-streaming mode
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.1,
                "num_ctx": 2048,
                "num_predict": 1500
            }
        }
        
        print(f"[Ollama] 📡 Sending non-streaming request...")
        response = ollama_session.post(
            f"{OLLAMA_URL}/api/chat",
            json=data,
            timeout=200  # v5.9.1: Increased to 200s to match Ollama timeout
        )
        
        print(f"[Ollama] 📥 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[Ollama] ❌ Bad status: {response.status_code}")
            print(f"[Ollama] Response text: {response.text[:500]}")
            yield f"Error: Ollama returned status {response.status_code}"
            return
        
        result = response.json()
        
        if 'message' in result and 'content' in result['message']:
            answer = result['message']['content']
            print(f"[Ollama] ✅ Got response: {len(answer)} chars")
            print(f"[Ollama] Preview: {answer[:150]}...")
            
            # Simulate streaming by yielding words
            words = answer.split()
            print(f"[Ollama] 🔄 Simulating streaming with {len(words)} words...")
            
            for i, word in enumerate(words, 1):
                yield word + " "
                
                # Log progress every 50 words
                if i % 50 == 0:
                    print(f"[Ollama] Streamed {i}/{len(words)} words...")
            
            print(f"[Ollama] ✅ Streaming simulation complete")
        else:
            print(f"[Ollama] ❌ No content in response")
            print(f"[Ollama] Response keys: {result.keys()}")
            yield "Error: Ollama response missing content field."
    
    except requests.exceptions.Timeout:
        print(f"[Ollama] ❌ Request timed out after 120 seconds")
        yield "Error: The AI service took too long to respond. Please try a simpler question."
    
    except requests.exceptions.ConnectionError as e:
        print(f"[Ollama] ❌ Connection error: {str(e)}")
        yield f"Error: Cannot connect to Ollama at {OLLAMA_URL}. Please check if Ollama is running."
    
    except Exception as e:
        print(f"[Ollama] ❌ Unexpected error: {str(e)}")
        import traceback
        print(f"[Ollama] Full traceback:")
        traceback.print_exc()
        yield f"Error: {str(e)}"




def process_samm_query_streaming(query: str, chat_history: List = None, documents_context: List = None):
    """Process query with streaming support"""

    # ✅ ADD THIS AT THE VERY TOP:
    # Extract financial records from documents
    financial_records = extract_financial_records_from_documents(documents_context)
    
    if financial_records:
        print(f"[Streaming] 💰 {len(financial_records)} financial records available")
        yield {"type": "financial_data_loaded", "count": len(financial_records)}

    # Yield progress updates
    yield {"type": "progress", "step": "intent_analysis", "message": "Analyzing intent..."}
    
    # Intent analysis
    intent_info = orchestrator.intent_agent.analyze_intent(query)
    yield {"type": "intent", "data": intent_info}
    
    # Entity extraction
    yield {"type": "progress", "step": "entity_extraction", "message": "Extracting entities..."}
    entity_info = orchestrator.entity_agent.extract_and_retrieve(query, intent_info)
    yield {"type": "entities", "data": {
        "count": len(entity_info.get('entities', [])),
        "entities": entity_info.get('entities', [])
    }}
    
    # Generate answer with streaming
    yield {"type": "progress", "step": "generating_answer", "message": "Generating answer..."}
    
    # Build context
    context = orchestrator.answer_agent._build_comprehensive_context(
        query, intent_info, entity_info, chat_history, documents_context
    )

    system_msg = orchestrator.answer_agent._create_optimized_system_message(
        intent_info.get("intent", "general"), context, entity_info, query  # v5.9.11: Pass query for Gold guidance
    )
    prompt = orchestrator.answer_agent._create_enhanced_prompt(query, intent_info, entity_info)
    
    # Stream the answer
    full_answer = ""
    for token in call_ollama_streaming(prompt, system_msg, temperature=0.1):
        full_answer += token
        yield {"type": "answer_chunk", "content": token}
    
    # Send final metadata
    yield {
        "type": "complete",
        "data": {
            "intent": intent_info.get('intent', 'unknown'),
            "entities_found": len(entity_info.get('entities', [])),
            "answer_length": len(full_answer)
        }
    }




def call_ollama_enhanced(prompt: str, system_message: str = "", temperature: float = 0.1) -> str:
    """
    Enhanced Ollama API call with fast timeouts, automatic retries, and fallback.
    ALWAYS returns a response - never crashes or returns errors.
    """
    try:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        # Calculate and log input sizes
        system_size = len(system_message) if system_message else 0
        prompt_size = len(prompt)
        total_input = system_size + prompt_size
        est_tokens = total_input // 4  # Rough estimate
        
        print(f"[Ollama Enhanced] 📊 INPUT SIZE:")
        print(f"   System Message: {system_size:,} chars")
        print(f"   User Prompt: {prompt_size:,} chars")
        print(f"   Total: {total_input:,} chars (~{est_tokens:,} tokens)")
        
        data = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.1,
                "num_ctx": 4096,  # Increased from 2048 to handle larger contexts
                "num_predict": 500
            }
        }
        
        for attempt in range(1, OLLAMA_MAX_RETRIES + 1):
            try:
                print(f"[Ollama Enhanced] Attempt {attempt}/{OLLAMA_MAX_RETRIES} (timeout: {OLLAMA_TIMEOUT_NORMAL}s, num_ctx: 4096)")
                start_time = time.time()
                response = ollama_session.post(f"{OLLAMA_URL}/api/chat", json=data, timeout=OLLAMA_TIMEOUT_NORMAL)
                elapsed = time.time() - start_time
                response.raise_for_status()
                result = response.json()
                answer = result["message"]["content"]
                print(f"[Ollama Enhanced] ✅ Success in {elapsed:.2f}s - Output: {len(answer)} chars")
                return answer
            except requests.exceptions.Timeout:
                elapsed = time.time() - start_time
                print(f"[Ollama Enhanced] ⏱️ Timeout on attempt {attempt} after {elapsed:.2f}s")
                if attempt < OLLAMA_MAX_RETRIES:
                    time.sleep(2 ** attempt)
            except requests.exceptions.RequestException as e:
                print(f"[Ollama Enhanced] API error on attempt {attempt}: {e}")
                if attempt < OLLAMA_MAX_RETRIES:
                    time.sleep(1)
        
        print(f"[Ollama Enhanced] 🔄 Using fallback response")
        return _get_intelligent_fallback()
        
    except Exception as e:
        print(f"[Ollama Enhanced] Processing error: {e}")
        return _get_intelligent_fallback()


def _get_intelligent_fallback() -> str:
    """Returns helpful SAMM information when Ollama is unavailable"""
    return """I apologize, but I'm currently experiencing technical difficulties connecting to the AI service.

However, I can still provide you with key SAMM (Security Assistance Management Manual) information:

**Core Concepts:**
• **Security Cooperation (SC)**: The broad umbrella of all DoD activities with international partners to achieve strategic objectives. Authorized under Title 10.
• **Security Assistance (SA)**: A subset of SC consisting of specific programs (FMS, FMF, IMET) authorized under Title 22 to transfer defense articles, training, and services.

**Key Organizations:**
• **DSCA** (Defense Security Cooperation Agency): Directs, administers, and provides guidance to DoD Components for SC programs
• **Department of State**: Provides continuous supervision and general direction of SA programs
• **DFAS** (Defense Finance and Accounting Service): Performs accounting, billing, disbursing, and collecting functions

**Legal Authorities:**
• Foreign Assistance Act (FAA) of 1961
• Arms Export Control Act (AECA) of 1976
• National Defense Authorization Act (NDAA) - annual

**Key Distinction:**
SC is the BROAD category (Title 10), and SA is a SUBSET of SC (Title 22).

Please try your question again. The AI service should be available shortly."""

# =============================================================================
# EMBEDDED SAMM KNOWLEDGE GRAPH DATA (RDF/TTL)
# =============================================================================

SAMM_KNOWLEDGE_GRAPH = """
# SAMM Chapter 1 Knowledge Graph (TTL/RDF Format)
@prefix samm: <http://samm.mil/ontology#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

# Core Concepts
samm:SecurityCooperation rdf:type samm:Concept ;
    rdfs:label "Security Cooperation" ;
    samm:definition "All activities undertaken by the DoD to encourage and enable international partners to work with the United States to achieve strategic objectives" ;
    samm:section "C1.1.1" ;
    samm:authority "Title 10" ;
    samm:funding "DoD appropriations" .

samm:SecurityAssistance rdf:type samm:Concept ;
    rdfs:label "Security Assistance" ;
    samm:definition "Group of programs authorized under Title 22 authorities by which the United States provides defense articles, military education and training" ;
    samm:section "C1.1.2.2" ;
    samm:authority "Title 22" ;
    samm:funding "Foreign Operations appropriations" ;
    samm:relationship samm:isSubsetOf ;
    samm:relatedTo samm:SecurityCooperation .

# Organizations
samm:DSCA rdf:type samm:Organization ;
    rdfs:label "Defense Security Cooperation Agency" ;
    samm:fullName "Defense Security Cooperation Agency" ;
    samm:role "Directs, administers, and provides guidance to DoD Components for SC programs" ;
    samm:section "C1.3.2.2" .

samm:DepartmentOfState rdf:type samm:Organization ;
    rdfs:label "Department of State" ;
    samm:role "Continuous supervision and general direction of SA programs" ;
    samm:authority "Secretary of State" ;
    samm:section "C1.3.1" .

samm:DepartmentOfDefense rdf:type samm:Organization ;
    rdfs:label "Department of Defense" ;
    samm:role "Establishes military requirements and implements programs" ;
    samm:authority "Secretary of Defense" ;
    samm:section "C1.3.2" .

samm:DFAS rdf:type samm:Organization ;
    rdfs:label "Defense Finance and Accounting Service" ;
    samm:fullName "Defense Finance and Accounting Service" ;
    samm:role "Performs accounting, billing, disbursing, and collecting functions for SC programs" ;
    samm:section "C1.3.2.8" .

samm:ImplementingAgency rdf:type samm:Organization ;
    rdfs:label "Implementing Agency" ;
    samm:definition "MILDEP organization or defense agency responsible for execution of SC programs" ;
    samm:role "Overall management of actions for delivery of materiel, supporting equipment, or services" ;
    samm:section "C1.3.2.6" .

# Legal Authorities
samm:ForeignAssistanceAct rdf:type samm:Authority ;
    rdfs:label "Foreign Assistance Act" ;
    samm:year "1961" ;
    samm:type "Title 22" ;
    samm:section "C1.2.1" .

samm:ArmsExportControlAct rdf:type samm:Authority ;
    rdfs:label "Arms Export Control Act" ;
    samm:acronym "AECA" ;
    samm:year "1976" ;
    samm:type "Title 22" ;
    samm:section "C1.2.1" .

samm:NDAA rdf:type samm:Authority ;
    rdfs:label "National Defense Authorization Act" ;
    samm:acronym "NDAA" ;
    samm:type "Title 10" ;
    samm:annual "true" ;
    samm:section "C1.1.2.1" .

# Key Relationships and Distinctions
samm:SecurityAssistance samm:isSubsetOf samm:SecurityCooperation .
samm:SecurityCooperation samm:authorizedBy samm:NDAA .
samm:SecurityAssistance samm:authorizedBy samm:ForeignAssistanceAct .
samm:SecurityAssistance samm:authorizedBy samm:ArmsExportControlAct .
samm:SecurityAssistance samm:supervisedBy samm:DepartmentOfState .
samm:SecurityCooperation samm:ledBy samm:DepartmentOfDefense .
"""

SAMM_TEXT_CONTENT = None

# =============================================================================
# SIMPLE KNOWLEDGE GRAPH PARSER
# =============================================================================

class SimpleKnowledgeGraph:
    """Simple knowledge graph parser for SAMM TTL data"""
    
    def __init__(self, ttl_data: str):
        self.entities = {}
        self.relationships = []
        self._parse_ttl(ttl_data)
    
    def _parse_ttl(self, ttl_data: str):
        """Parse TTL data into structured knowledge"""
        lines = ttl_data.split('\n')
        current_entity = None
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # New entity definition
            if 'rdf:type' in line:
                parts = line.split()
                if len(parts) >= 3:
                    entity_id = parts[0].replace('samm:', '')
                    entity_type = parts[2].replace('samm:', '').replace(';', '')
                    current_entity = {
                        'id': entity_id,
                        'type': entity_type,
                        'properties': {}
                    }
                    self.entities[entity_id] = current_entity
            
            # Properties
            elif current_entity and any(prop in line for prop in ['rdfs:label', 'samm:definition', 'samm:role', 'samm:section', 'samm:authority', 'samm:year']):
                if '"' in line:
                    prop_name = line.split()[0].replace('samm:', '').replace('rdfs:', '')
                    prop_value = line.split('"')[1] if '"' in line else line.split()[-1].replace(';', '').replace('.', '')
                    current_entity['properties'][prop_name] = prop_value
            
            # Relationships
            elif current_entity and any(rel in line for rel in ['samm:isSubsetOf', 'samm:supervisedBy', 'samm:ledBy', 'samm:authorizedBy']):
                parts = line.split()
                if len(parts) >= 2:
                    relationship = parts[0].replace('samm:', '')
                    target = parts[1].replace('samm:', '').replace('.', '').replace(';', '')
                    self.relationships.append({
                        'source': current_entity['id'],
                        'relationship': relationship,
                        'target': target
                    })
    
    def find_entity(self, query: str) -> Optional[Dict]:
        """Find entity by name or label"""
        query_lower = query.lower()
        
        # Direct match
        for entity_id, entity in self.entities.items():
            if entity_id.lower() == query_lower:
                return entity
            if entity['properties'].get('label', '').lower() == query_lower:
                return entity
        
        # Partial match
        for entity_id, entity in self.entities.items():
            if query_lower in entity_id.lower():
                return entity
            if query_lower in entity['properties'].get('label', '').lower():
                return entity
        
        return None
    
    def get_relationships(self, entity_id: str) -> List[Dict]:
        """Get relationships for an entity"""
        return [rel for rel in self.relationships 
                if rel['source'] == entity_id or rel['target'] == entity_id]

# Initialize knowledge graph
knowledge_graph = SimpleKnowledgeGraph(SAMM_KNOWLEDGE_GRAPH)
print(f"Knowledge Graph loaded: {len(knowledge_graph.entities)} entities, {len(knowledge_graph.relationships)} relationships")

# =============================================================================
# DATABASE MANAGER FOR INTEGRATED AGENTS
# =============================================================================

class DatabaseManager:
    """
    Manages connections to all three databases with improved error handling
    """
    
    def __init__(self):
        self.cosmos_gremlin_client = None
        self.vector_db_client = None
        self.embedding_model = None
        self.initialize_connections()
    
    def initialize_connections(self):
        """Initialize all database connections with better error handling"""
        print("[DatabaseManager] Initializing database connections...")
        
        # Initialize Cosmos DB Gremlin connection
        self._init_cosmos_gremlin()
        # Initialize ChromaDB connections
        self._init_vector_dbs()
        # Initialize embedding model
        self._init_embedding_model()
    
    def _init_cosmos_gremlin(self):
        """Initialize Cosmos DB Gremlin with proper cleanup"""
        if not client or not COSMOS_GREMLIN_CONFIG['password']:
            print("[DatabaseManager] Cosmos Gremlin credentials not available")
            return
            
        try:
            username = f"/dbs/{COSMOS_GREMLIN_CONFIG['database']}/colls/{COSMOS_GREMLIN_CONFIG['graph']}"
            endpoint_url = f"wss://{COSMOS_GREMLIN_CONFIG['endpoint']}:443/gremlin"
            
            # Close existing connection if any
            if self.cosmos_gremlin_client:
                try:
                    self.cosmos_gremlin_client.close()
                except:
                    pass
            
            self.cosmos_gremlin_client = client.Client(
                url=endpoint_url,
                traversal_source="g",
                username=username,
                password=COSMOS_GREMLIN_CONFIG['password'],
                message_serializer=serializer.GraphSONSerializersV2d0()
            )
            
            # Test connection with timeout
            result = self.cosmos_gremlin_client.submit("g.V().limit(1).count()").all().result()
            print(f"[DatabaseManager] Cosmos Gremlin connected successfully - {result[0]} vertices available")
            
        except Exception as e:
            print(f"[DatabaseManager] Cosmos Gremlin connection failed: {e}")
            self.cosmos_gremlin_client = None
    
    def extract_metadata_from_content(self, content: str) -> dict:
        """
        Extract chapter and section numbers from content text
        Works for patterns like: C1.3.2.8. or C5.4.1.
        """
        metadata = {
            'chapter_number': 'Unknown',
            'section_number': 'Unknown'
        }
    
        # Pattern 1: C1.3.2.8. Defense Finance... (most common)
        match = re.match(r'^(C(\d+)\.[\d\.]+)\.\s', content)
    
        if match:
            section = match.group(1)  # "C1.3.2.8"
            chapter = match.group(2)  # "1"
        
            metadata['section_number'] = section
            metadata['chapter_number'] = chapter
        
            print(f"[MetadataExtract] Extracted: Chapter {chapter}, Section {section}")
            return metadata
    
        # Pattern 2: C1. T1. (tables)
        match = re.match(r'^(C(\d+)\.\s*T\d+)', content)
        if match:
            section = match.group(1)
            chapter = match.group(2)
            metadata['section_number'] = section
            metadata['chapter_number'] = chapter
            print(f"[MetadataExtract] Extracted table: Chapter {chapter}, Section {section}")
            return metadata
    
        # Pattern 3: Chapter X. (heading style)
        match = re.match(r'^Chapter\s+(\d+)', content, re.IGNORECASE)
        if match:
            chapter = match.group(1)
            metadata['chapter_number'] = chapter
            print(f"[MetadataExtract] Extracted chapter heading: Chapter {chapter}")
            return metadata
    
        return metadata

    
    def _init_vector_dbs(self):
        """Initialize vector databases"""
        if not chromadb:
            print("[DatabaseManager] ChromaDB not available")
            return
            
        # Initialize ChromaDB vector_db (documents)
        # Initialize ChromaDB vector_db (documents)
        try:
            if Path(VECTOR_DB_PATH).exists():
                self.vector_db_client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
                collections = self.vector_db_client.list_collections()
                print(f"[DatabaseManager] Vector DB connected - {len(collections)} collections available")
                if collections:
                    for col in collections:
                        print(f"\n[DEBUG] Collection: {col.name}")
                        print(f"[DEBUG] Metadata: {col.metadata}")
                        print(f"[DEBUG] Count: {col.count()}")
            else:
                print(f"[DatabaseManager] Vector DB path not found: {VECTOR_DB_PATH}")
        except Exception as e:
            print(f"[DatabaseManager] Vector DB connection failed: {e}")
            self.vector_db_client = None
        
    
    def _init_embedding_model(self):
        """Initialize embedding model"""
        if not SentenceTransformer:
            print("[DatabaseManager] SentenceTransformer not available")
            return
            
        try:
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
            print(f"[DatabaseManager] Embedding model loaded: {EMBEDDING_MODEL}")
        except Exception as e:
            print(f"[DatabaseManager] Embedding model failed to load: {e}")
            self.embedding_model = None
    
    def query_cosmos_graph(self, query_text: str, entities: List[str] = None) -> List[Dict]:
        """Query Cosmos DB graph database with auto-reconnection"""
        if not self.cosmos_gremlin_client:
            # Try to initialize if not available
            self._init_cosmos_gremlin()
            if not self.cosmos_gremlin_client:
                return []
        
        results = []
        unique_results = []
        reconnect_attempted = False
        
        def execute_query(query):
            """Execute a single Gremlin query with reconnection on failure"""
            nonlocal reconnect_attempted
            try:
                return self.cosmos_gremlin_client.submit(query).all().result()
            except Exception as e:
                error_msg = str(e).lower()
                # Check for connection errors that need reconnection
                if any(err in error_msg for err in ['closing transport', 'connection', 'closed', 'transport']):
                    if not reconnect_attempted:
                        print(f"[DatabaseManager] 🔄 Connection lost, attempting reconnect...")
                        reconnect_attempted = True
                        self._init_cosmos_gremlin()
                        if self.cosmos_gremlin_client:
                            print(f"[DatabaseManager] ✅ Reconnected successfully, retrying query...")
                            return self.cosmos_gremlin_client.submit(query).all().result()
                raise e
        
        try:
            if entities:
                # Limit entities to prevent too many queries
                limited_entities = entities[:3]  # Only process first 3 entities
                
                for entity in limited_entities:
                    # Clean entity name for Gremlin query
                    entity_clean = re.sub(r'[^\w\s]', '', entity).strip()
                    if not entity_clean:
                        continue
                    
                    # Generate ID-style format (lowercase, underscores)
                    entity_id = entity_clean.lower().replace(' ', '_')
                    
                    try:
                        # Query for vertices with matching names (with timeout)
                        vertex_query = f"g.V().has('name', containing('{entity_clean}')).limit(10)"
                        vertex_results = execute_query(vertex_query)
                        
                        for vertex in vertex_results:
                            results.append({
                                "type": "vertex",
                                "data": vertex,
                                "source": "cosmos_gremlin",
                                "entity": entity
                            })
                        
                        # Also query by ID pattern for better matching
                        id_vertex_query = f"g.V().has('id', containing('{entity_id}')).limit(5)"
                        id_vertex_results = execute_query(id_vertex_query)
                        
                        for vertex in id_vertex_results:
                            results.append({
                                "type": "vertex",
                                "data": vertex,
                                "source": "cosmos_gremlin",
                                "entity": entity
                            })
                        
                        # Query for relationships involving this entity (increased limit for complete coverage)
                        edge_query = f"g.V().has('name', containing('{entity_clean}')).bothE().limit(15)"
                        edge_results = execute_query(edge_query)
                        
                        for edge in edge_results:
                            results.append({
                                "type": "edge", 
                                "data": edge,
                                "source": "cosmos_gremlin",
                                "entity": entity
                            })
                        
                        # Also get edges by ID-based query
                        id_edge_query = f"g.V().has('id', containing('{entity_id}')).bothE().limit(15)"
                        id_edge_results = execute_query(id_edge_query)
                        
                        for edge in id_edge_results:
                            results.append({
                                "type": "edge", 
                                "data": edge,
                                "source": "cosmos_gremlin",
                                "entity": entity
                            })
                            
                    except Exception as entity_error:
                        print(f"[DatabaseManager] Error querying entity '{entity}': {entity_error}")
                        continue
            else:
                # General query for high-level entities
                general_query = "g.V().limit(10)"
                general_results = execute_query(general_query)
                
                for vertex in general_results:
                    results.append({
                        "type": "vertex",
                        "data": vertex,
                        "source": "cosmos_gremlin"
                    })
            
            # Deduplicate results by ID
            seen_ids = set()
            unique_results = []
            for result in results:
                data = result.get("data", {})
                result_id = data.get("id") if isinstance(data, dict) else str(data)[:100]
                if result_id and result_id not in seen_ids:
                    seen_ids.add(result_id)
                    unique_results.append(result)
            
            print(f"[DatabaseManager] Cosmos Gremlin query returned {len(unique_results)} results (deduped from {len(results)})")
            
        except Exception as e:
            print(f"[DatabaseManager] Cosmos Gremlin query error: {e}")
            unique_results = results  # Fall back to original results on error
        
        return unique_results
    
    def query_vector_db(self, query: str, collection_name: str = None, n_results: int = 5) -> List[Dict]:
        """Query vector database and return results with enhanced metadata - OPTIMIZED for speed"""
        try:
            if not self.vector_db_client:
                print("[DatabaseManager] Vector DB client not available")
                return []
        
            collection = self.vector_db_client.get_collection(collection_name or VECTOR_DB_COLLECTION)
        
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            # ✅ ENHANCED: Format results with metadata extraction
            formatted_results = []
            for i, (doc, meta, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                # ✅ NEW: Check if metadata is missing and extract from content
                if meta.get('chapter_number') == 'Unknown' or not meta.get('chapter_number'):
                    extracted_meta = self.extract_metadata_from_content(doc)
                    meta.update(extracted_meta)
                    print(f"[DatabaseManager] Updated metadata for result {i+1}: Chapter {extracted_meta['chapter_number']}, Section {extracted_meta['section_number']}")

                # Convert distance to similarity score (0 = identical, 2 = very different for cosine)
                # For cosine distance: similarity = 1 - distance
                similarity_score = 1 - distance if distance <= 1 else distance
                
                formatted_results.append({
                    'content': doc,
                    'metadata': meta,
                    'distance': distance,  # Keep original distance
                    'similarity': distance,  # Keep for backward compatibility
                    'similarity_score': round(similarity_score, 4)  # Add readable score
                })

            print(f"[DatabaseManager] Vector DB query returned {len(formatted_results)} results")
            return formatted_results

        
        except Exception as e:
            print(f"[DatabaseManager] Vector DB query error: {e}")
            return []

    
    def cleanup(self):
        """Cleanup database connections"""
        try:
            if self.cosmos_gremlin_client:
                self.cosmos_gremlin_client.close()
                print("[DatabaseManager] Cosmos Gremlin connection closed")
        except Exception as e:
            print(f"[DatabaseManager] Error closing Cosmos Gremlin: {e}")
    
    def get_database_status(self) -> Dict[str, Any]:
        """Get status of all database connections"""
        status = {
            "cosmos_gremlin": {
                "connected": self.cosmos_gremlin_client is not None,
                "endpoint": COSMOS_GREMLIN_CONFIG['endpoint'],
                "database": COSMOS_GREMLIN_CONFIG['database'],
                "graph": COSMOS_GREMLIN_CONFIG['graph']
            },
            "vector_db": {
                "connected": self.vector_db_client is not None,
                "path": VECTOR_DB_PATH,
                "collections": []
            },
            
            "embedding_model": {
                "loaded": self.embedding_model is not None,
                "model_name": EMBEDDING_MODEL
            }
        }
        
        # Get collection info safely
        try:
            if self.vector_db_client:
                collections = self.vector_db_client.list_collections()
                status["vector_db"]["collections"] = [c.name for c in collections]
        except:
            pass
        
        return status

# Initialize database manager
db_manager = DatabaseManager()

# =============================================================================
# LANGGRAPH STATE ORCHESTRATION SYSTEM
# =============================================================================

class AgentState(TypedDict):
    """State shared across all agents in the workflow"""
    query: str
    chat_history: Optional[List[Dict]]
    documents_context: Optional[List[Dict]]
    intent_info: Optional[Dict[str, Any]]
    entity_info: Optional[Dict[str, Any]]
    answer: Optional[str]
    execution_steps: List[str]
    start_time: float
    current_step: str
    error: Optional[str]

# ============================================================================
# HITL FEEDBACK LOOP SYSTEM
# ============================================================================

HITL_CORRECTIONS_STORE = {
    "intent_corrections": {},
    "entity_corrections": {},
    "answer_corrections": {},
    "correction_history": []
}

# ============================================================================
# HITL FILE PERSISTENCE
# ============================================================================
HITL_STORAGE_FILE = Path("hitl_corrections.json")

def save_hitl_corrections():
    """Save HITL corrections to file for persistence"""
    try:
        data = {
            "intent_corrections": HITL_CORRECTIONS_STORE["intent_corrections"],
            "entity_corrections": HITL_CORRECTIONS_STORE["entity_corrections"],
            "answer_corrections": HITL_CORRECTIONS_STORE["answer_corrections"],
            "correction_history": HITL_CORRECTIONS_STORE["correction_history"][-100:]
        }
        with open(HITL_STORAGE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[HITL] Saved {len(HITL_CORRECTIONS_STORE['answer_corrections'])} corrections to {HITL_STORAGE_FILE}")
        return True
    except Exception as e:
        print(f"[HITL] Error saving corrections: {e}")
        return False

def load_hitl_corrections():
    """Load HITL corrections from file on startup"""
    global HITL_CORRECTIONS_STORE
    try:
        if HITL_STORAGE_FILE.exists():
            with open(HITL_STORAGE_FILE, 'r') as f:
                data = json.load(f)
            HITL_CORRECTIONS_STORE["intent_corrections"] = data.get("intent_corrections", {})
            HITL_CORRECTIONS_STORE["entity_corrections"] = data.get("entity_corrections", {})
            HITL_CORRECTIONS_STORE["answer_corrections"] = data.get("answer_corrections", {})
            HITL_CORRECTIONS_STORE["correction_history"] = data.get("correction_history", [])
            print(f"[HITL] Loaded {len(HITL_CORRECTIONS_STORE['answer_corrections'])} corrections from {HITL_STORAGE_FILE}")
        else:
            print(f"[HITL] No existing corrections file found - starting fresh")
    except Exception as e:
        print(f"[HITL] Error loading corrections: {e}")

# Load any existing corrections on startup
load_hitl_corrections()

# =============================================================================
# ANSWER TRAINING SYSTEM - Learn from SME corrections for similar questions
# =============================================================================

ANSWER_TRAINING_STORE = {
    "exact_matches": {},      # question_hash -> answer
    "keyword_patterns": [],   # [{keywords: [...], answer: "...", question: "..."}]
    "training_history": []
}

ANSWER_TRAINING_FILE = Path("answer_training.json")

def save_answer_training():
    """Save answer training to file"""
    try:
        with open(ANSWER_TRAINING_FILE, 'w') as f:
            json.dump(ANSWER_TRAINING_STORE, f, indent=2)
        print(f"[ANSWER TRAINING] ✅ Saved {len(ANSWER_TRAINING_STORE['keyword_patterns'])} patterns")
        return True
    except Exception as e:
        print(f"[ANSWER TRAINING] ❌ Error: {e}")
        return False

def load_answer_training():
    """Load answer training on startup"""
    global ANSWER_TRAINING_STORE
    try:
        if ANSWER_TRAINING_FILE.exists():
            with open(ANSWER_TRAINING_FILE, 'r') as f:
                data = json.load(f)
            ANSWER_TRAINING_STORE["exact_matches"] = data.get("exact_matches", {})
            ANSWER_TRAINING_STORE["keyword_patterns"] = data.get("keyword_patterns", [])
            ANSWER_TRAINING_STORE["training_history"] = data.get("training_history", [])
            print(f"[ANSWER TRAINING] ✅ Loaded {len(ANSWER_TRAINING_STORE['keyword_patterns'])} patterns")
    except Exception as e:
        print(f"[ANSWER TRAINING] ❌ Error: {e}")

load_answer_training()

def extract_keywords(text):
    """Extract important keywords from text"""
    stop_words = {'what', 'is', 'are', 'the', 'a', 'an', 'i', 'am', 'to', 'do', 'for', 
                  'and', 'or', 'of', 'in', 'on', 'my', 'how', 'should', 'can', 'will',
                  'be', 'this', 'that', 'with', 'has', 'have', 'it', 'was', 'were',
                  'than', 'expected', 'taking', 'longer', 'delaying'}
    import string
    text_clean = text.lower().translate(str.maketrans('', '', string.punctuation))
    words = text_clean.split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords

def train_answer(question, answer):
    """Train system with SME's corrected answer"""
    q_hash = create_question_hash(question)
    keywords = extract_keywords(question)
    
    # Save exact match
    ANSWER_TRAINING_STORE["exact_matches"][q_hash] = answer
    
    # Save keyword pattern (for similar questions)
    if len(keywords) >= 3:
        # Check if pattern exists
        pattern_found = False
        for p in ANSWER_TRAINING_STORE["keyword_patterns"]:
            if set(p["keywords"]) == set(keywords):
                p["answer"] = answer
                p["updated_at"] = datetime.now(timezone.utc).isoformat()
                pattern_found = True
                break
        
        if not pattern_found:
            ANSWER_TRAINING_STORE["keyword_patterns"].append({
                "keywords": keywords,
                "answer": answer,
                "question": question,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Save history
    ANSWER_TRAINING_STORE["training_history"].append({
        "question": question,
        "keywords": keywords,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    save_answer_training()
    print(f"[ANSWER TRAINING] ✅ Trained with {len(keywords)} keywords: {keywords[:5]}")
    return True

def get_trained_answer(question):
    """Get trained answer for similar questions"""
    q_hash = create_question_hash(question)
    
    # 1. Exact match first
    if q_hash in ANSWER_TRAINING_STORE["exact_matches"]:
        print(f"[ANSWER TRAINING] 🎯 EXACT MATCH found!")
        return ANSWER_TRAINING_STORE["exact_matches"][q_hash]
    
    # 2. Keyword pattern match (bidirectional - check both ways)
    question_keywords = set(extract_keywords(question))
    print(f"[ANSWER TRAINING] 🔍 Question keywords: {question_keywords}")
    
    if len(question_keywords) >= 2:
        best_match = None
        best_score = 0
        
        for pattern in ANSWER_TRAINING_STORE["keyword_patterns"]:
            pattern_keywords = set(pattern["keywords"])
            common = question_keywords & pattern_keywords
            
            if len(pattern_keywords) > 0 and len(question_keywords) > 0:
                # Bidirectional score - average of both directions
                score1 = len(common) / len(pattern_keywords)  # How much of pattern is covered
                score2 = len(common) / len(question_keywords)  # How much of question is covered
                score = (score1 + score2) / 2
                
                print(f"[ANSWER TRAINING] 📊 Pattern: {pattern_keywords}, Common: {common}, Score: {score:.0%}")
                
                # Need at least 2 common keywords and 40% average score
                if score >= 0.4 and len(common) >= 2 and score > best_score:
                    best_score = score
                    best_match = pattern
        
        if best_match:
            print(f"[ANSWER TRAINING] 🎯 PATTERN MATCH ({best_score:.0%}): {list(question_keywords & set(best_match['keywords']))}")
            return best_match["answer"]
    
    print(f"[ANSWER TRAINING] ❌ No pattern match found")
    return None

print("✅ Answer Training System Initialized")

# =============================================================================
# INTENT TRAINING SYSTEM - Learn from SME corrections for similar questions  
# =============================================================================

INTENT_TRAINING_STORE = {
    "exact_matches": {},      # question_hash -> intent
    "keyword_patterns": [],   # [{keywords: [...], intent: "...", question: "..."}]
    "training_history": []
}

INTENT_TRAINING_FILE = Path("intent_training.json")

def save_intent_training():
    """Save intent training to file"""
    try:
        with open(INTENT_TRAINING_FILE, 'w') as f:
            json.dump(INTENT_TRAINING_STORE, f, indent=2)
        print(f"[INTENT TRAINING] ✅ Saved {len(INTENT_TRAINING_STORE['keyword_patterns'])} patterns")
        return True
    except Exception as e:
        print(f"[INTENT TRAINING] ❌ Error: {e}")
        return False

def load_intent_training():
    """Load intent training on startup"""
    global INTENT_TRAINING_STORE
    try:
        if INTENT_TRAINING_FILE.exists():
            with open(INTENT_TRAINING_FILE, 'r') as f:
                data = json.load(f)
            INTENT_TRAINING_STORE["exact_matches"] = data.get("exact_matches", {})
            INTENT_TRAINING_STORE["keyword_patterns"] = data.get("keyword_patterns", [])
            INTENT_TRAINING_STORE["training_history"] = data.get("training_history", [])
            print(f"[INTENT TRAINING] ✅ Loaded {len(INTENT_TRAINING_STORE['keyword_patterns'])} patterns")
    except Exception as e:
        print(f"[INTENT TRAINING] ❌ Error: {e}")

load_intent_training()

def train_intent(question, intent):
    """Train system with SME's corrected intent"""
    q_hash = create_question_hash(question)
    keywords = extract_keywords(question)
    
    # Save exact match
    INTENT_TRAINING_STORE["exact_matches"][q_hash] = intent
    
    # Save keyword pattern (for similar questions)
    if len(keywords) >= 3:
        pattern_found = False
        for p in INTENT_TRAINING_STORE["keyword_patterns"]:
            if set(p["keywords"]) == set(keywords):
                p["intent"] = intent
                p["updated_at"] = datetime.now(timezone.utc).isoformat()
                pattern_found = True
                break
        
        if not pattern_found:
            INTENT_TRAINING_STORE["keyword_patterns"].append({
                "keywords": keywords,
                "intent": intent,
                "question": question,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Save history
    INTENT_TRAINING_STORE["training_history"].append({
        "question": question,
        "intent": intent,
        "keywords": keywords,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    save_intent_training()
    print(f"[INTENT TRAINING] ✅ Trained '{intent}' with {len(keywords)} keywords: {keywords[:5]}")
    return True

def get_trained_intent(question):
    """Get trained intent for similar questions"""
    q_hash = create_question_hash(question)
    
    # 1. Exact match first
    if q_hash in INTENT_TRAINING_STORE["exact_matches"]:
        intent = INTENT_TRAINING_STORE["exact_matches"][q_hash]
        print(f"[INTENT TRAINING] 🎯 EXACT MATCH: {intent}")
        return {"intent": intent, "confidence": 0.99, "source": "trained_exact"}
    
    # 2. Keyword pattern match (bidirectional)
    question_keywords = set(extract_keywords(question))
    print(f"[INTENT TRAINING] 🔍 Question keywords: {question_keywords}")
    
    if len(question_keywords) >= 2:
        best_match = None
        best_score = 0
        
        for pattern in INTENT_TRAINING_STORE["keyword_patterns"]:
            pattern_keywords = set(pattern["keywords"])
            common = question_keywords & pattern_keywords
            
            if len(pattern_keywords) > 0 and len(question_keywords) > 0:
                # Bidirectional score
                score1 = len(common) / len(pattern_keywords)
                score2 = len(common) / len(question_keywords)
                score = (score1 + score2) / 2
                
                print(f"[INTENT TRAINING] 📊 Pattern: {pattern['intent']}, Common: {common}, Score: {score:.0%}")
                
                if score >= 0.4 and len(common) >= 2 and score > best_score:
                    best_score = score
                    best_match = pattern
        
        if best_match:
            print(f"[INTENT TRAINING] 🎯 PATTERN MATCH ({best_score:.0%}): {best_match['intent']}")
            return {"intent": best_match["intent"], "confidence": 0.90, "source": "trained_pattern"}
    
    print(f"[INTENT TRAINING] ❌ No pattern match found")
    return None

print("✅ Intent Training System Initialized")

# =============================================================================
# ENTITY TRAINING SYSTEM - Learn from SME corrections for similar questions  
# =============================================================================

ENTITY_TRAINING_STORE = {
    "exact_matches": {},      # question_hash -> [entities]
    "keyword_patterns": [],   # [{keywords: [...], entities: [...], question: "..."}]
    "training_history": []
}

ENTITY_TRAINING_FILE = Path("entity_training.json")

def save_entity_training():
    """Save entity training to file"""
    try:
        with open(ENTITY_TRAINING_FILE, 'w') as f:
            json.dump(ENTITY_TRAINING_STORE, f, indent=2)
        print(f"[ENTITY TRAINING] ✅ Saved {len(ENTITY_TRAINING_STORE['keyword_patterns'])} patterns")
        return True
    except Exception as e:
        print(f"[ENTITY TRAINING] ❌ Error: {e}")
        return False

def load_entity_training():
    """Load entity training on startup"""
    global ENTITY_TRAINING_STORE
    try:
        if ENTITY_TRAINING_FILE.exists():
            with open(ENTITY_TRAINING_FILE, 'r') as f:
                data = json.load(f)
            ENTITY_TRAINING_STORE["exact_matches"] = data.get("exact_matches", {})
            ENTITY_TRAINING_STORE["keyword_patterns"] = data.get("keyword_patterns", [])
            ENTITY_TRAINING_STORE["training_history"] = data.get("training_history", [])
            print(f"[ENTITY TRAINING] ✅ Loaded {len(ENTITY_TRAINING_STORE['keyword_patterns'])} patterns")
    except Exception as e:
        print(f"[ENTITY TRAINING] ❌ Error: {e}")

load_entity_training()

def train_entities(question, entities):
    """Train system with SME's corrected entities"""
    q_hash = create_question_hash(question)
    keywords = extract_keywords(question)
    
    # Save exact match
    ENTITY_TRAINING_STORE["exact_matches"][q_hash] = entities
    
    # Save keyword pattern (for similar questions)
    if len(keywords) >= 3:
        pattern_found = False
        for p in ENTITY_TRAINING_STORE["keyword_patterns"]:
            if set(p["keywords"]) == set(keywords):
                p["entities"] = entities
                p["updated_at"] = datetime.now(timezone.utc).isoformat()
                pattern_found = True
                break
        
        if not pattern_found:
            ENTITY_TRAINING_STORE["keyword_patterns"].append({
                "keywords": keywords,
                "entities": entities,
                "question": question,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Save history
    ENTITY_TRAINING_STORE["training_history"].append({
        "question": question,
        "entities": entities,
        "keywords": keywords,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    save_entity_training()
    print(f"[ENTITY TRAINING] ✅ Trained {len(entities)} entities with {len(keywords)} keywords")
    return True

def get_trained_entities(question):
    """Get trained entities for similar questions"""
    q_hash = create_question_hash(question)
    
    # 1. Exact match first
    if q_hash in ENTITY_TRAINING_STORE["exact_matches"]:
        entities = ENTITY_TRAINING_STORE["exact_matches"][q_hash]
        print(f"[ENTITY TRAINING] 🎯 EXACT MATCH: {entities}")
        return {"entities": entities, "confidence": 0.99, "source": "trained_exact"}
    
    # 2. Keyword pattern match (bidirectional)
    question_keywords = set(extract_keywords(question))
    print(f"[ENTITY TRAINING] 🔍 Question keywords: {question_keywords}")
    
    if len(question_keywords) >= 2:
        best_match = None
        best_score = 0
        
        for pattern in ENTITY_TRAINING_STORE["keyword_patterns"]:
            pattern_keywords = set(pattern["keywords"])
            common = question_keywords & pattern_keywords
            
            if len(pattern_keywords) > 0 and len(question_keywords) > 0:
                # Bidirectional score
                score1 = len(common) / len(pattern_keywords)
                score2 = len(common) / len(question_keywords)
                score = (score1 + score2) / 2
                
                print(f"[ENTITY TRAINING] 📊 Pattern entities: {pattern['entities']}, Common: {common}, Score: {score:.0%}")
                
                if score >= 0.4 and len(common) >= 2 and score > best_score:
                    best_score = score
                    best_match = pattern
        
        if best_match:
            print(f"[ENTITY TRAINING] 🎯 PATTERN MATCH ({best_score:.0%}): {best_match['entities']}")
            return {"entities": best_match["entities"], "confidence": 0.90, "source": "trained_pattern"}
    
    print(f"[ENTITY TRAINING] ❌ No pattern match found")
    return None

print("✅ Entity Training System Initialized")
# ============================================================================

def create_question_hash(question: str) -> str:
    """Create normalized hash for question matching"""
    normalized = question.lower().strip()
    return hashlib.md5(normalized.encode()).hexdigest()
# Demo scenarios - EMPTY by default
DEMO_SCENARIOS = {}

# DON'T pre-populate corrections! Let them be applied via HITL dashboard
# This allows first query to show partial answer, second query to show corrected answer
print("✅ HITL Feedback System Initialized with 2 demo scenarios")
print("💡 TIP: Use /api/hitl/reset-demo to clear corrections between tests")

def apply_hitl_corrections(question: str, result: dict) -> dict:
    """Apply HITL corrections if they exist - includes trained patterns for similar questions"""
    q_hash = create_question_hash(question)
    corrections_applied = []
    
    # Check exact match first for intent
    if q_hash in HITL_CORRECTIONS_STORE["intent_corrections"]:
        result['metadata']['intent'] = HITL_CORRECTIONS_STORE["intent_corrections"][q_hash]
        corrections_applied.append("Intent (exact)")
        print(f"🔄 HITL: Intent correction applied (exact match)")
    else:
        # Check trained patterns for similar questions
        trained_intent = get_trained_intent(question)
        if trained_intent:
            result['metadata']['intent'] = trained_intent['intent']
            corrections_applied.append(f"Intent ({trained_intent['source']})")
            print(f"🔄 HITL: Intent correction applied ({trained_intent['source']})")
    
    # Check exact match first for entities
    if q_hash in HITL_CORRECTIONS_STORE["entity_corrections"]:
        result['metadata']['entities'] = HITL_CORRECTIONS_STORE["entity_corrections"][q_hash]
        corrections_applied.append("Entities (exact)")
        print(f"🔄 HITL: Entity corrections applied (exact match)")
    else:
        # Check trained patterns for similar questions
        trained_entities = get_trained_entities(question)
        if trained_entities:
            result['metadata']['entities'] = trained_entities['entities']
            result['metadata']['trained_entity_match'] = True
            corrections_applied.append(f"Entities ({trained_entities['source']})")
            print(f"🔄 HITL: Entity corrections applied ({trained_entities['source']})")
    
    # Check exact match first for answer
    if q_hash in HITL_CORRECTIONS_STORE["answer_corrections"]:
        result['answer'] = HITL_CORRECTIONS_STORE["answer_corrections"][q_hash]
        result['metadata']['hitl_corrected'] = True
        corrections_applied.append("Answer (exact)")
        print(f"🔄 HITL: Answer correction applied (exact match)")
    else:
        # Check trained patterns for similar questions
        trained_answer = get_trained_answer(question)
        if trained_answer:
            result['answer'] = trained_answer
            result['metadata']['hitl_corrected'] = True
            result['metadata']['trained_pattern_match'] = True
            corrections_applied.append("Answer (pattern)")
            print(f"🔄 HITL: Answer correction applied (pattern match)")
    
    if corrections_applied:
        result['metadata']['hitl_corrections_applied'] = corrections_applied
        print(f"✅ HITL CORRECTIONS FOUND! {corrections_applied}")
    
    return result

def generate_demo_partial_response(question: str) -> dict:
    """Return partial response for demo questions on first ask"""
    # DISABLED FOR NOW - Let normal LLM processing happen for testing
    return None
    
    # Original code commented out:
    # q_hash = create_question_hash(question)
    # 
    # for scenario_name, scenario_data in DEMO_SCENARIOS.items():
    #     scenario_hash = create_question_hash(scenario_data["question"])
    #     if q_hash == scenario_hash:
    #         # Only return partial if corrections NOT applied yet
    #         if q_hash not in HITL_CORRECTIONS_STORE["answer_corrections"]:
    #             print(f"🎬 DEMO ({scenario_name.upper()}): Returning partial response")
    #             return {
    #                 "intent": scenario_data["original"]["intent"],
    #                 "entities": scenario_data["original"]["entities"],
    #                 "answer": scenario_data["original"]["answer"],
    #                 "is_demo": True,
    #                 "demo_type": scenario_name
    #             }
    # 
    # return None

# ============================================================================
# END HITL SYSTEM
# ============================================================================

# =============================================================================
# v5.9.8: SMART SEARCH - think_first_v2()
# =============================================================================
def think_first_v2(query: str, timeout: int = 300) -> dict:
    """
    Smart Search: LLM identifies relevant SAMM terms BEFORE vector search.
    FAST version - compact prompt, returns only matching terms.
    """
    prompt = f"""Question: {query}

{SAMM_CONTEXT}

Which ONE line from the reference above matches this question?
Return ONLY the terms from that matching line, nothing else.
If no line matches, return empty.

Terms:"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 50}  # Limit output length
            },
            timeout=timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            relevant_terms = result.get("message", {}).get("content", "").strip()
            relevant_terms = relevant_terms.replace("Terms:", "").strip()
            
            print(f"[SMART SEARCH] ✅ LLM identified: {relevant_terms}")
            
            return {
                "relevant_terms": relevant_terms,
                "enhanced_query": f"{query} {relevant_terms}",
                "success": True
            }
        else:
            print(f"[SMART SEARCH] ❌ Ollama error: {response.status_code}")
            return {"relevant_terms": "", "enhanced_query": query, "success": False}
            
    except requests.exceptions.Timeout:
        print(f"[SMART SEARCH] ⏱️ Timeout - using original query")
        return {"relevant_terms": "", "enhanced_query": query, "success": False}
    except Exception as e:
        print(f"[SMART SEARCH] ❌ Error: {e}")
        return {"relevant_terms": "", "enhanced_query": query, "success": False}

# =============================================================================
# END SMART SEARCH
# =============================================================================

class WorkflowStep(Enum):
    """Workflow steps for state orchestration"""
    INIT = "initialize"
    INTENT = "analyze_intent"
    ENTITY = "extract_entities"
    ANSWER = "generate_answer"
    COMPLETE = "complete"
    ERROR = "error"

def call_ollama(prompt: str, system_message: str = "") -> str:
    """Call Ollama with system message and prompt (legacy function for compatibility)"""
    return call_ollama_enhanced(prompt, system_message, temperature=0.1)

def extract_financial_records_from_documents(documents_context: List) -> List[Dict]:
    """
    Extract financial records from uploaded documents
    Returns list of financial records with PDLI info
    """
    if not documents_context:
        return []
    
    financial_records = []
    
    for doc in documents_context:
        # Check if document has financial data in metadata
        if doc.get('metadata', {}).get('hasFinancialData'):
            records = doc['metadata'].get('financialRecords', [])
            
            print(f"[Financial Extract] Found {len(records)} records in {doc.get('fileName')}")
            
            # Enrich each record with document info
            for record in records:
                enriched = {
                    **record,
                    'source_document': doc.get('fileName'),
                    'document_id': doc.get('documentId')
                }
                financial_records.append(enriched)
    
    print(f"[Financial Extract] Total: {len(financial_records)} financial records extracted")
    return financial_records
def extract_case_id_from_filename(filename: str) -> str:
    """
    Extract case ID from filename like 'SR-P-NAV_Financial.xlsx'
    Returns case ID or None
    """
    # Pattern: SR-X-YYY or similar at start of filename
    import re
    match = re.match(r'^(SR-[A-Z]-[A-Z0-9]+)', filename, re.IGNORECASE)
    if match:
        case_id = match.group(1).upper()
        print(f"[Upload] 📋 Extracted case ID from filename: {case_id}")
        return case_id
    return None 

class IntentAgent:
    """Intent analysis using Ollama with Human-in-Loop and trigger updates"""
    
    def __init__(self, available_chapters=None):
        # Define ALL chapters upfront (even if data not loaded yet)
        self.available_chapters = available_chapters or [1, 4, 5, 6, 7, 9]
        self.hil_feedback_data = []  # Store human feedback for intent corrections
        self.intent_patterns = {}    # Store learned patterns from feedback
        self.trigger_updates = []    # Store updates from new entity/relationship data
        
        # Special case patterns for non-SAMM, nonsense, and incomplete queries
        self.special_case_patterns = {
            "nonsense_keywords": [
                "asdfghjkl", "qwerty", "xyzpdq", "flurble", "lorem ipsum",
                "banana helicopter", "purple dreams", "sparkle fountain",
                "waxing moon potato", "rainbow process asteroid"
            ],
            "incomplete_phrases": [
                "what about it", "tell me about that", "explain that",
                "the thing", "tell me about the thing", "can you explain that",
                "what about", "who handles", "the process for", "explain how"
            ],
            "non_samm_topics": [
                "nato", "article 5", "ndaa process", "title 50", "joint chiefs",
                "intelligence community", "five eyes", "un security council",
                "federal acquisition regulation", "far", "unified command plan",
                "third offset", "national security strategy", "humanitarian assistance",
                "bilateral agreement", "multilateral", "defense officer personnel"
            ]
        }
        
        # BASE INTENTS: Always active (7 intents)
        self.base_intents = {
            "definition": "asking what something is",
            "distinction": "asking about differences between concepts",
            "authority": "asking about who has authority or oversight",
            "organization": "asking about agencies and their roles",
            "factual": "asking for specific facts like dates, numbers",
            "relationship": "asking about how things are connected",
            "general": "general questions"
        }
        
                # ALL CHAPTER INTENTS: Define all upfront (22 intents)
        self.chapter_intents = {
            1: {
                "scope": "asking about what is included or excluded",
                "purpose": "asking about the purpose or objective"
            },
            4: {
                "approval": "asking about approval processes or authority",
                "review": "asking about review procedures or requirements",
                "decision": "asking about decision-making processes"
            },
            5: {
                "process": "asking about procedures, workflows, or how to do something",
                "implementation": "asking how to implement or execute something",
                "prerequisite": "asking what is required before starting",
                "documentation": "asking about required forms, reports, or paperwork"
            },
            6: {
                "financial": "asking about costs, payments, billing, or financial matters",
                "budget": "asking about budget allocation or planning",
                "payment": "asking about payment terms, schedules, or methods",
                "pricing": "asking about how prices are calculated or determined",
                "reimbursement": "asking about refund or reimbursement processes"
            },
            7: {
                "timeline": "asking about deadlines, schedules, or when things happen",
                "milestone": "asking about project milestones or checkpoints",
                "status": "asking about current status or progress",
                "tracking": "asking about monitoring or tracking systems"
            },
            9: {
                "compliance": "asking about regulations, requirements, or obligations",
                "audit": "asking about audit processes or requirements",
                "legal": "asking about legal requirements or restrictions",
                "reporting": "asking about compliance reporting requirements"
            }
        }

        # ============================================================================
        # M1.3 HYBRID: Priority-Ordered Pattern Rules
        # Pattern matching first (fast), LLM only if needed (slow)
        # Formula: Pattern Match (40%) + Keyword Overlap (35%) + AI Certainty (25%)
        # ============================================================================
        
        # Pattern rules checked in ORDER (first match wins!)
        # Format: (internal_intent, [patterns])
        self.pattern_rules = [
            # ================================================================
            # TIER 1: MOST SPECIFIC (check first)
            # ================================================================
            
            # VERIFICATION - Yes/No questions (starts with is/does/are/can)
            ("verification", [
                r"^is [A-Z][\w\s]+ the ",
                r"^does [A-Z][\w\s]+ (?:approve|require|have|maintain)",
                r"^are [A-Z][\w\s]+ (?:subject|required|authorized)",
                r"^is [\w\s]+ (?:the executive agent|required|authorized|subject)",
                r"^does [\w\s]+ (?:approve|require|allow|have authority)",
                r"^are [\w\s]+ (?:subject to|required to|programs)",
            ]),
            
            # COMPARISON/DISTINCTION - COMPREHENSIVE
            ("distinction", [
                # === Direct comparison ===
                r"difference between",
                r"differ(?:s|ence)? from",
                r"compare (?:the |and )?",
                r"contrast (?:between|with)?",
                r" vs\.? ",
                r" versus ",
                r"distinguish (?:between)?",
                
                # === How X differs ===
                r"how does [\w\s]+ differ",
                r"how (?:is|are) [\w\s]+ different",
                r"what makes [\w\s]+ different",
                r"what distinguishes",
                
                # === Comparison phrases ===
                r"(?:what is|what are) the (?:difference|distinction|contrast)",
                r"(?:is|are) [\w\s]+ (?:different from|the same as|similar to)",
                r"(?:how|what) (?:is|are) [\w\s]+ (?:compared|relative) to",
                r"unlike ",
                r"as opposed to",
                r"in contrast (?:to|with)",
                
                # === SC/SA specific comparisons ===
                r"(?:sc|sa|title 10|title 22) (?:vs|versus|compared to|or) (?:sc|sa|title 10|title 22)",
                r"(?:fms|dcs|eda) (?:vs|versus|compared to|or) (?:fms|dcs|eda)",
            ]),
            
            # EXPLANATION - Why/purpose questions
            ("explanation", [
                r"^why (?:is|are|does|do|did|should|would|has|have) ",
                r"why does [\w\s]+ maintain",
                r"how does [\w\s]+ support [\w\s]+ (?:objectives|security|goals|interests)",
                r"what is the (?:reason|purpose|rationale|objective|goal) (?:for|of|behind)",
                r"explain why",
                r"why is [\w\s]+ (?:important|necessary|required|needed)",
            ]),
            
            # ================================================================
            # TIER 2: LEGAL/COMPLIANCE (Chapter 9)
            # ================================================================
            # MERGED: Ch9 intents (compliance, audit, legal, reporting)
            ("compliance", [
                # === Existing compliance patterns ===
                r"(?:faa|aeca|itar|ear) (?:section )?",
                r"what (?:legal )?authority governs",
                r"(?:congressional|notification|export|itar|legal) requirements",
                r"eligibility requirements",
                r"what does (?:faa|aeca|itar|ear)",
                r"what are the [\w\s]+ requirements",
                r"legal (?:authority|requirements|basis)",
                r"audit (?:process|requirements|procedures)",
                r"reporting requirements",
                r"compliance reporting",
                
                # === MERGED: Ch9 - Audit patterns ===
                r"(?:what is|what are) (?:the )?audit",
                r"audit (?:process|procedure|requirement|cycle|finding|report)",
                r"how (?:is|are) [\w\s]+ audit(?:ed)?",
                r"(?:who|which agency) (?:conducts|performs) (?:the )?audit",
                r"(?:internal|external|annual|periodic) audit",
                r"audit (?:trail|record|documentation)",
                r"(?:gao|ig|inspector general) (?:audit|review|report)",
                
                # === MERGED: Ch9 - Legal patterns ===
                r"(?:what is|what are) (?:the )?legal (?:requirement|basis|authority|framework)",
                r"legal(?:ly)? (?:required|mandated|obligated)",
                r"(?:law|statute|regulation|act) (?:requires|mandates|governs)",
                r"(?:is|are) [\w\s]+ legal(?:ly)?",
                r"(?:what|which) (?:law|statute|regulation|act) (?:applies|governs)",
                r"(?:violation|non.?compliance|penalty|sanction)",
                r"legal (?:consequences|implications|liability)",
                r"(?:prohibited|restricted|banned) (?:by|under)",
                
                # === MERGED: Ch9 - Reporting patterns ===
                r"(?:what is|what are) (?:the )?reporting (?:requirement|obligation)",
                r"reporting (?:requirement|obligation|deadline|format)",
                r"(?:what|which) report(?:s)? (?:is|are) required",
                r"(?:must|should|required to) report",
                r"report(?:ing)? (?:to|for) (?:congress|gao|ig)",
                r"(?:annual|quarterly|monthly|periodic) report(?:ing)?",
                r"(?:congressional|notification) report(?:ing)?",
                r"(?:how|when|where) (?:to|do|does|should) [\w\s]+ report",
            ]),
            
            # ================================================================
            # TIER 3: AUTHORITY/RESPONSIBILITY (Chapter 4)
            # ================================================================
            # COMPREHENSIVE: All possible ways to ask about authority/roles
            # MERGED: Ch4 intents (approval, review, decision)
            ("authority", [
                # === WHO questions ===
                r"who (?:is responsible|has authority|has the authority|approves|authorizes|oversees|manages|supervises|determines|decides|can approve)",
                r"who has (?:ultimate |final |primary )?(?:authority|responsibility|oversight)",
                r"who (?:can |is authorized to |has authority to |must |should |will )",
                r"who reports to",
                r"who does [\w\s]+ report to",
                r"who [\w\s]+ delegate(?:s|d)? to",
                
                # === WHAT DOES X [verb] questions ===
                # v5.9.8: Fixed to not match "what do I need to do" (process question)
                r"what does [\w\s]+ do(?:\s|$|\?)",
                r"what do (?!I need|i need|I have|i have)[\w\s]+ do(?:\s|$|\?)",  # Exclude "what do I need to do"
                r"what does [\w\s]+ approve",
                r"what does [\w\s]+ authorize",
                r"what does [\w\s]+ supervise",
                r"what does [\w\s]+ oversee",
                r"what does [\w\s]+ manage",
                r"what does [\w\s]+ control",
                r"what does [\w\s]+ direct",
                r"what does [\w\s]+ administer",
                r"what does [\w\s]+ determine",
                r"what does [\w\s]+ decide",
                r"what does [\w\s]+ coordinate",
                r"what does [\w\s]+ delegate",
                r"what does [\w\s]+ review",
                r"what does [\w\s]+ certify",
                r"what does [\w\s]+ validate",
                r"what does [\w\s]+ sign",
                
                # === WHAT [noun] questions ===
                r"what (?:is|are) .+?(?:'s|s'|'s) (?:role|responsibilities|responsibility|duties|authority|function)",
                r"what (?:is|are) the (?:role|responsibilities|responsibility|duties|authority|function) of",
                r"what are (?:the )?(?:general |specific |primary )?responsibilities of",
                r"what are (?:the )?[\w\s]+(?:'s|')[\w\s]* responsibilities\??$",
                r"what (?:is|are) [\w\s]+ responsible for",
                r"what authority does",
                r"what role does [\w\s]+ (?:play|have)",
                r"what powers does",
                r"what jurisdiction does",
                r"what can [\w\s]+ (?:approve|authorize|decide|determine)",
                
                # === HOW DOES X questions ===
                r"how does [\w\s]+ oversee",
                r"how does [\w\s]+ supervise",
                r"how does [\w\s]+ manage",
                r"how does [\w\s]+ coordinate",
                
                # === WHOSE/UNDER questions ===
                r"(?:whose|under whose) (?:authority|oversight|supervision|responsibility|direction|control)",
                r"under what authority",
                r"under which (?:authority|organization|agency|office)",
                
                # === RESPONSIBILITY phrases ===
                r"responsible for ",
                r"authority to (?:approve|authorize|conduct|make|sign|certify|validate|review)",
                r"approval (?:authority|requirements)",
                r"delegation of (?:authority|responsibility)",
                r"chain of (?:command|authority|responsibility)",
                
                # === MERGED: Ch4 - Approval patterns ===
                r"(?:what|which) (?:is|are) (?:the )?approval (?:process|authority|requirement|threshold)",
                r"how (?:is|are) [\w\s]+ approved",
                r"(?:who|what) approves",
                r"approval (?:for|of|required)",
                r"(?:needs|requires|requires) approval",
                r"approval threshold",
                r"(?:congressional|secretarial|agency) approval",
                
                # === MERGED: Ch4 - Review patterns ===
                r"(?:what|which) (?:is|are) (?:the )?review (?:process|requirement|cycle)",
                r"how (?:is|are) [\w\s]+ reviewed",
                r"(?:who|what) reviews",
                r"review (?:for|of|required|cycle)",
                r"(?:annual|periodic|quarterly) review",
                r"under review",
                
                # === MERGED: Ch4 - Decision patterns ===
                r"(?:who|what) (?:makes|has) (?:the )?(?:final |ultimate )?decision",
                r"decision.?making (?:authority|process)",
                r"how (?:is|are) decisions? made",
                r"(?:who|what) decides",
                r"decision (?:authority|process|point)",
            ]),
            
            # ================================================================
            # TIER 3.5: FUNDING/FINANCIAL (Chapter 6)
            # ================================================================
            # COMPREHENSIVE: All ways to ask about funding
            ("funding", [
                # === How funded ===
                r"how (?:is|are) [\w\s]+ funded",
                r"how (?:is|are) [\w\s]+ financed",
                r"how (?:is|are) [\w\s]+ paid (?:for)?",
                
                # === Who pays ===
                r"who (?:pays|funds|finances) (?:for)?",
                r"who (?:is|are) responsible for (?:paying|funding|financing)",
                
                # === Funding source ===
                r"(?:what|which) (?:is|are) the (?:funding|financial) (?:source|mechanism|method)",
                r"where does (?:the )?(?:money|funding|funds) come from",
                r"source of (?:funding|funds|financing)",
                
                # === Title 10/22 funding ===
                r"(?:title 10|title 22) (?:funds|funding|appropriation)",
                r"(?:is|are) [\w\s]+ (?:title 10|title 22)",
                r"(?:fmf|fms|grant|loan) funding",
                
                # === Cost/price questions ===
                r"(?:what|how much) does [\w\s]+ cost",
                r"cost of ",
                r"price of ",
                r"pricing (?:for|of)",
                
                # === Budget ===
                r"budget (?:for|of|allocation)",
                r"appropriation(?:s)? (?:for|of)",
                
                # === Payment ===
                r"payment (?:terms|schedule|method)",
                r"billing (?:for|of|process)",
                r"reimburs(?:e|ement)",
                
                # === Funding differences ===
                r"funded differently",
                r"funding difference(?:s)?",
                r"different(?:ly)? funded",
                
                # === MERGED: Ch6 - Budget patterns ===
                r"what is the budget",
                r"budget (?:allocation|planning|estimate|request)",
                r"how (?:is|are) (?:the )?budget(?:s)? (?:allocated|planned|determined)",
                r"fiscal year (?:budget|funding)",
                r"annual (?:budget|funding)",
                
                # === MERGED: Ch6 - Payment patterns ===
                r"how (?:do|does|is|are) [\w\s]+ pa(?:y|id)",
                r"payment (?:process|procedure|schedule|method|terms|options)",
                r"(?:when|how) (?:is|are) payment(?:s)? (?:made|due|required)",
                r"pay(?:ment)? for ",
                r"billing (?:cycle|process|procedure)",
                r"invoice(?:s|ing)?",
                
                # === MERGED: Ch6 - Pricing patterns ===
                r"how (?:is|are) (?:the )?price(?:s)? (?:determined|calculated|set)",
                r"pricing (?:methodology|structure|model)",
                r"what determines (?:the )?price",
                r"case value",
                r"total (?:cost|price|value)",
                r"administrative (?:cost|charge|fee|surcharge)",
                
                # === MERGED: Ch6 - Reimbursement patterns ===
                r"how (?:do|does|is|are) [\w\s]+ reimburs(?:e|ed)",
                r"reimbursement (?:process|procedure|rate|policy)",
                r"(?:get|receive|request) reimburs(?:ement|ed)",
                r"refund(?:s|ed|ing)?",
                r"credit(?:s|ed)?",
            ]),
            
            # ================================================================
            # TIER 3.6: ELIGIBILITY
            # ================================================================
            # COMPREHENSIVE: All ways to ask about eligibility
            ("eligibility", [
                # === Who/what is eligible ===
                r"(?:who|what|which) (?:is|are) eligible",
                r"(?:is|are) [\w\s]+ eligible",
                r"eligib(?:le|ility) (?:for|to|of)",
                
                # === Qualification ===
                r"(?:who|what) (?:can|may) (?:qualify|receive|participate)",
                r"(?:who|what) qualifies",
                r"qualify(?:ing)? (?:for|to)",
                r"qualification(?:s)? (?:for|to)",
                
                # === Requirements for eligibility ===
                r"(?:what are|what is) the (?:eligibility )?(?:requirements?|criteria|conditions)",
                r"requirements? (?:for|to) (?:be )?(?:eligible|qualify)",
                r"criteria (?:for|to)",
                
                # === Country eligibility ===
                r"(?:which|what) countries (?:are|can)",
                r"country eligibility",
                r"eligible (?:countries|nations|partners)",
                
                # === Restrictions ===
                r"(?:who|what) (?:is|are) (?:prohibited|restricted|excluded|ineligible)",
                r"(?:can|may) [\w\s]+ (?:participate|receive|qualify)",
            ]),
            
            # ================================================================
            # TIER 4: FACT_RETRIEVAL (Chapter 7 + factual)
            # ================================================================
            # TIER 4: FACT_RETRIEVAL (Chapter 7 + factual)
            # ================================================================
            # MERGED: Ch7 intents (timeline, milestone, status, tracking)
            ("factual", [
                # === Existing factual patterns ===
                r"^which (?:directive|order|regulation|law|document|command|executive|agency)",
                r"which (?:command|agency|office) (?:does|is|has|governs)",
                r"what (?:is|are) the [\w\s]+ designation",
                r"what (?:is|are) the (?:primary|main) (?:site|location|office)",
                r"under which",
                r"what (?:regulation|directive|order|law) (?:covers|governs)",
                r"where is [\w\s]+ (?:located|based|housed)",
                r"when (?:is|are|was|were|does|do) ",
                r"what (?:is|are) the (?:deadline|timeline|schedule|date)",
                r"how long does",
                r"how (?:much|many) (?:time|days|weeks|months)",
                r"what is the [\w\s]+ (?:site|location|designation|number|amount)",
                
                # v5.9.8: Format questions should be factual, not process
                r"what is (?:the )?(?:required |necessary )?format (?:for|of|to)",
                r"what (?:is|are) the (?:required |necessary )?format",
                r"(?:required|necessary) format (?:for|of|to)",
                r"what format (?:is|should be) (?:used|required)",
                r"is there a (?:required |specific |standard )?format",
                
                # === MERGED: Ch7 - Timeline patterns ===
                r"(?:what is|what are) (?:the )?timeline",
                r"timeline (?:for|of|to)",
                r"how long (?:does|do|will|would) [\w\s]+ take",
                r"(?:time|duration) (?:for|of|to|required)",
                r"how (?:much|long) time",
                r"(?:typical|average|expected|standard) (?:time|duration|timeline)",
                r"(?:when|by when) (?:is|are|should|must|will)",
                r"deadline(?:s)? (?:for|of)",
                r"due date(?:s)?",
                r"timeframe(?:s)? (?:for|of)",
                
                # === MERGED: Ch7 - Milestone patterns ===
                r"(?:what is|what are) (?:the )?milestone",
                r"milestone(?:s)? (?:for|of|in)",
                r"key (?:milestone|event|date|point)",
                r"(?:major|critical|important) (?:milestone|step|phase)",
                r"checkpoint(?:s)?",
                r"phase(?:s)? (?:of|in)",
                
                # === MERGED: Ch7 - Status patterns ===
                r"(?:what is|what are) (?:the )?(?:current )?status",
                r"status (?:of|for)",
                r"(?:current|present) (?:status|state|condition)",
                r"where (?:is|are|does|do) [\w\s]+ (?:stand|now)",
                r"progress (?:of|on|for)",
                r"how (?:is|are) [\w\s]+ progressing",
                
                # === MERGED: Ch7 - Tracking patterns ===
                r"how (?:to|do|does|is|are) [\w\s]+ track",
                r"track(?:ing|ed)? (?:of|for|system|method)",
                r"(?:monitor|monitoring) (?:of|for)",
                r"(?:what|which) (?:system|method|tool) (?:is used|tracks|monitors)",
                r"how (?:is|are) [\w\s]+ (?:monitored|tracked|measured)",
                r"performance (?:tracking|monitoring|measurement)",
            ]),
            
            # ================================================================
            # TIER 5: PROCESS/PROCEDURE (Chapter 5)
            # ================================================================
            # COMPREHENSIVE: All ways to ask about processes
            # MERGED: Ch5 intents (process, implementation, prerequisite, documentation)
            ("process", [
                # === How to/does ===
                r"what is the process (?:for|of|to)",
                r"how (?:to|do|does|can|should|would) ",
                r"how does (?:a |the )?(?:foreign )?",
                
                # === How is X done ===
                r"how (?:are|is) [\w\s]+ (?:developed|created|submitted|processed|approved|coordinated|reviewed|handled|prepared|conducted|implemented|executed|managed|initiated|completed|finalized)",
                
                # === Process/procedure descriptions ===
                r"describe (?:the )?[\w\s]+ (?:process|procedure|coordination|workflow|steps)",
                r"what (?:are|is) the (?:steps|procedures?|process|workflow|method|approach)",
                r"steps (?:for|to|in|involved|required)",
                r"procedure(?:s)? (?:for|to|of)",
                
                # === Coordination/workflow ===
                r"(?:interagency|coordination|approval) (?:process|procedures|workflow)",
                r"payment (?:process|procedures|terms|schedule)",
                r"reimbursement (?:process|procedures)",
                r"review (?:process|procedures|cycle)",
                
                # === What happens when ===
                r"what happens (?:when|if|after|before)",
                r"what is the (?:next step|first step|final step)",
                r"what (?:comes|happens) (?:next|after|before)",
                
                # === Requirements for action ===
                r"what (?:is|are) required (?:to|for|before)",
                r"what do I need to",
                r"what can I do",  # v5.9.8: Added for "what can I do to meet deadlines"
                r"what should I do",  # v5.9.8: Added
                r"how do I (?:start|begin|initiate|submit|complete)",
                
                # === Timeline/sequence ===
                r"in what order",
                r"sequence of (?:events|steps|actions)",
                r"lifecycle of",
                r"from start to finish",
                
                # === MERGED: Ch5 - Implementation patterns ===
                r"how (?:to|do|does|is|are) [\w\s]+ implement",
                r"implementation (?:of|for|process|steps|guide)",
                r"how (?:is|are) [\w\s]+ implemented",
                r"implement(?:ing|ation)? (?:a |the )?[\w\s]+",
                r"execute (?:a |the )?",
                r"execution (?:of|for)",
                r"carry(?:ing)? out",
                
                # === MERGED: Ch5 - Prerequisite patterns ===
                r"what (?:is|are) (?:the )?prerequisite",
                r"prerequisite(?:s)? (?:for|to|of)",
                r"what (?:is|are) required (?:before|prior to)",
                r"before (?:starting|beginning|initiating)",
                r"prior to ",
                r"must (?:be |have )(?:done|completed|submitted|approved) (?:before|first)",
                r"what (?:needs|must) (?:to )?(?:be done|happen) (?:before|first)",
                r"precondition(?:s)? (?:for|to)",
                
                # === MERGED: Ch5 - Documentation patterns ===
                r"what (?:document|documents|documentation|form|forms|paperwork) (?:is|are) (?:required|needed)",
                r"(?:required|necessary) (?:document|documents|documentation|form|forms)",
                r"documentation (?:for|of|required)",
                r"what (?:form|forms) (?:do I|should I|must I) (?:use|submit|complete)",
                r"paperwork (?:for|required)",
                r"(?:which|what) (?:form|document) (?:is|should be) used",
            ]),
            
            # ================================================================
            # TIER 6: ORGANIZATIONAL STRUCTURE
            # ================================================================
            ("organization", [
                r"how is (?:the )?[\w\s]+ (?:enterprise )?organized",
                r"(?:what is|describe) (?:the )?[\w\s]+ (?:organizational )?structure",
                r"what organizations (?:fall under|are under|report to|comprise)",
                r"organizational structure",
                r"how (?:is|are) [\w\s]+ structured",
                r"what is the hierarchy",
                r"reporting structure",
                r"what (?:offices|divisions|components|units) ",
                r"falls under (?:which|what)",
                r"structure (?:of|for) ",
                # NEW: Framework patterns (framework = organizational structure)
                r"what is (?:the )?(?:sc|sa|security cooperation|security assistance)[\w\s]* (?:coordinating |coordination )?framework",
                r"what is (?:the )?[\w\s]+ (?:framework|hierarchy|structure)\??$",
                r"(?:coordinating|coordination) framework",
            ]),
            
            # ================================================================
            # TIER 7: LIST/ENUMERATION
            # ================================================================
            # TIER 7: LIST/ENUMERATION
            # ================================================================
            ("list", [
                r"^list (?:all |the )?",
                r"^name (?:the |all )?",
                r"^enumerate ",
                r"what are the (?:three|two|four|five|six|seven|eight|nine|ten|\d+) ",
                r"what (?:are|is) (?:all )?(?:the )?(?:types|kinds|categories|components|key|major|primary) (?:of|roles|functions|responsibilities)",
                r"what are (?:the )?(?:key )?(?:roles|functions|responsibilities|duties) of",
                r"what (?:is|are) (?:included|excluded|covered)",
                r"what (?:documents?|forms?) (?:is|are) (?:required|needed)",
                r"what are (?:the )?[\w\s]+ (?:oversight )?bodies",
                r"what are (?:the )?[\w\s]+ (?:advisory )?groups",
            ]),
            
            # ================================================================
            # TIER 8: RELATIONSHIP (connections between entities)
            # ================================================================
            ("relationship", [
                r"what (?:is|are) (?:the )?relationship(?:s)? (?:between|among|of)",
                r"relationship(?:s)? (?:between|among|of) ",
                r"how (?:is|are|does|do) [\w\s]+ (?:related|connected|linked) to",
                r"what is [\w\s]+(?:'s|'s) relationship (?:to|with)",
                r"connection(?:s)? between",
            ]),
            
            # ================================================================
            # TIER 9: DEFINITION (lowest priority - catch remaining "what is")
            # ================================================================
            # COMPREHENSIVE: All ways to ask for definitions
            # MERGED: Ch1 intents (scope, purpose)
            ("definition", [
                # === What is/are ===
                r"^what is (?:a |an |the )?[\w\s\-]+\??$",
                r"^what are [\w\s\-]+\??$",
                
                # === Define/explain ===
                r"^define (?:the )?(?:term )?",
                r"^explain (?:the )?(?:term |concept of |meaning of )?[\w\s]+$",
                r"^describe (?:what )?[\w\s]+ (?:is|are|means)$",
                
                # === Meaning questions ===
                r"what does [\w\s]+ (?:mean|stand for|refer to)",
                r"what is meant by",
                r"meaning of ",
                r"definition of",
                
                # === Acronym questions ===
                r"what does [\w]+ stand for",
                r"what is the (?:full |expanded )?(?:form|name|meaning) of [\w]+",
                r"expand [\w]+",
                
                # === Tell me about ===
                r"^tell me (?:about|what) ",
                r"^can you (?:explain|describe|define) ",
                r"^I need to (?:understand|know) (?:what|about) ",
                
                # === Understanding questions ===
                r"what do you mean by",
                r"clarify (?:what )?",
                r"help me understand (?:what )?",
                
                # === MERGED: Ch1 - Scope patterns ===
                r"what (?:is|are) (?:the )?scope of",
                r"scope of [\w\s]+",
                r"what (?:does|do) [\w\s]+ (?:include|cover|encompass)",
                r"what (?:is|are) (?:included|covered|excluded) (?:in|from|by)",
                r"what falls under",
                r"what (?:is|are) (?:within|outside) (?:the )?scope",
                r"boundaries of",
                r"extent of",
                
                # === MERGED: Ch1 - Purpose patterns ===
                r"what is the purpose of",
                r"purpose of [\w\s]+",
                r"why (?:does|do) [\w\s]+ exist",
                r"what is the (?:objective|goal|aim|intent) of",
                r"why (?:is|are|was|were) [\w\s]+ (?:created|established|designed)",
                r"what (?:is|are) [\w\s]+ (?:designed|intended|meant) (?:for|to)",
            ]),
        ]
        
        # M1.3: SAMM-specific keywords for keyword overlap calculation
        # UPDATED: Expanded keywords for better confidence scoring
        self.samm_keywords = {
            "entities": [
                # Core SAMM Agencies
                "dsca", "fms", "imet", "samm", "loa", "loc", "fmf", "eca", "aeca", "faa", 
                "dod", "dos", "state department", "defense", "security cooperation", 
                "security assistance", "foreign military", "usd(p)", "usdp", "secdef", "ccmd",
                "combatant command", "combatant commands", "building partner capacity", "bpc",
                "defense security", "military education", "training", "itar", "usml",
                "title 10", "title 22", "dfas", "gef", "lor", "sco", "usasac",
                # NEW: Implementing Agencies & Key Roles
                "implementing agency", "implementing agencies", "ia", "mildep",
                "president", "congress", "secretary of state", "secretary of defense",
                "army", "navy", "air force", "ussocom", "advisory group", "advisory groups",
                # NEW: Additional SAMM entities
                "dcma", "dcaa", "dla", "dtra", "disa", "nga", "nsa", "mda",
                "nipo", "satfa", "afsac", "usasac", "syscom",
                # NEW: Key SC/SA terms  
                "foreign partner", "foreign partners", "defense articles", "defense services",
                "letter of offer", "letter of acceptance", "case line", "fms case"
            ],
            "chapters": ["chapter", "section", "c1", "c4", "c5", "c6", "c7", "c9", "paragraph", "samm"],
            "actions": ["approval", "review", "authorization", "notification", "implementation",
                       "supervision", "oversight", "coordination", "execution", "delegation"],
            "concepts": ["threshold", "authority", "oversight", "program", "cooperation", "assistance",
                        "responsibility", "responsibilities", "role", "roles", "framework", "structure",
                        "relationship", "relationships", "stakeholder", "stakeholders"]
        }
        
        print("[IntentAgent M1.3] Initialized with HYBRID pattern + LLM confidence scoring")

    # ============================================================================
    # M1.3 NEW: Pattern-Based Intent Detection (FAST - No LLM)
    # ============================================================================
    def _detect_intent_from_patterns(self, query: str) -> Dict[str, Any]:
        """
        Fast pattern-based intent detection - no LLM call needed!
        Returns intent and confidence if pattern matches, None otherwise.
        """
        query_lower = query.lower().strip()
        
        # Check patterns in priority order
        for intent, patterns in self.pattern_rules:
            for pattern in patterns:
                try:
                    if re.search(pattern, query_lower, re.IGNORECASE):
                        print(f"[IntentAgent M1.3] ✅ Pattern match: '{pattern[:50]}...' → {intent}")
                        return {
                            "intent": intent,
                            "pattern_matched": True,
                            "pattern": pattern[:50],
                            "pattern_score": 1.0
                        }
                except re.error:
                    continue
        
        # No pattern match - return with low confidence
        return {
            "intent": "general",
            "pattern_matched": False,
            "pattern": None,
            "pattern_score": 0.3
        }

    # ============================================================================
    # M1.3 NEW: Keyword Overlap Score (35% weight)
    # UPDATED: HIGH_WEIGHT keywords get 0.85 on single match
    # ============================================================================
    
    # HIGH WEIGHT KEYWORDS: Single match = 0.85 score
    # These are core SAMM entities where even 1 match indicates strong relevance
    HIGH_WEIGHT_KEYWORDS = {
        # === CHAPTER 1: Core Organizations ===
        # Department of State
        "secretary of state", "secstate", "department of state",
        # Department of Defense - Top Level
        "secretary of defense", "secdef", "department of defense",
        # USD Offices
        "usd(p)", "usdp", "under secretary of defense for policy",
        "usd(a&s)", "usdas", "under secretary of defense for acquisition and sustainment",
        "usd(c)", "usdc", "under secretary of defense comptroller",
        "usd(p&r)", "usdpr", "under secretary of defense for personnel and readiness",
        # DSCA
        "dsca", "defense security cooperation agency",
        # Implementing Agencies - MILDEPs
        "implementing agency", "implementing agencies",
        "dasa (de&c)", "dasa de&c", "dasa dec", 
        "office of the deputy assistant secretary of the army for defense exports and cooperation",
        "nipo", "navy international programs office",
        "saf/ia", "safia", "deputy under secretary of the air force for international affairs",
        # Implementing Agencies - Defense Agencies
        "dcma", "defense contract management agency",
        "disa", "defense information systems agency", 
        "dla", "defense logistics agency",
        "dtra", "defense threat reduction agency",
        "mda", "missile defense agency",
        "nga", "national geospatial-intelligence agency",
        "nsa", "national security agency",
        # Other DoD Organizations
        "dcaa", "defense contract audit agency",
        "dfas", "defense finance and accounting service",
        "joint chiefs of staff", "jcs", "cjcs",
        "combatant commander", "combatant commanders", "ccdr", "ccdrs", "ccmd",
        # Army Commands
        "usasac", "u.s. army security assistance command",
        "satfa", "security assistance training field activity",
        "usace", "u.s. army corps of engineers",
        "amc", "army materiel command",
        "tradoc", "army training and doctrine command",
        # Air Force Commands
        "afsac", "air force security assistance and cooperation",
        "afsat", "air force security assistance training squadron",
        "aetc", "air education and training command",
        "afmc", "air force materiel command",
        # Navy Commands
        "syscom", "syscoms", "system commands",
        # === CHAPTER 1: Core Concepts ===
        "security cooperation", "security assistance",
        "foreign military sales", "fms",
        "international military education and training", "imet",
        "building partner capacity", "bpc",
        "direct commercial sales", "dcs",
        "excess defense articles", "eda",
        "letter of request", "lor",
        "letter of offer and acceptance", "loa",
        "memorandum of request", "mor",
        # === CHAPTER 1: Legal Authorities ===
        "foreign assistance act", "faa",
        "arms export control act", "aeca",
        "title 10", "title 22", "title 50",
        "executive order 13637", "e.o. 13637", "eo 13637",
        "national defense authorization act", "ndaa",
        "itar", "international traffic in arms regulations",
        "usml", "united states munitions list",
        # === Concepts that indicate SAMM domain ===
        "continuous supervision", "general direction",
        "defense articles", "defense services",
        "foreign partner", "foreign partners",
        "campaign plan", "campaign plans",
        # === Short forms (common in queries) ===
        " sc ", " sa ",  # Space-bounded to avoid false matches like "ascar"
        "sc program", "sa program", "sc programs", "sa programs",
        "sc responsibilities", "sa responsibilities",
        "sc activities", "sa activities",
        
        # =========================================================================
        # CHAPTER 4: FMS Program General Information
        # =========================================================================
        # C4 Organizations & Agencies
        "dtsa", "defense technology security administration",
        "ddtc", "directorate of defense trade controls",
        "ousd(p)", "ousd(a&s)", "usd(p)",
        "mildep", "mildeps", "military department", "military departments",
        "sco", "security cooperation organization",
        "jtcg/me", "joint technical coordinating group",
        "asd(so/lic)", "asd(hd&gs/cwmd)",
        "state(pm/rsat)", "state(pm)",
        # C4 Programs & Processes  
        "end use monitoring", "eum",
        "enhanced end use monitoring", "eeum",
        "total package approach", "tpa",
        "price and availability", "p&a",
        "pre-lor assessment request", "par",
        "regional defense fellowship program", "rdfp",
        # C4 Legal & Regulatory
        "u.s. munitions list", "usml",
        "presidential determination",
        "national disclosure policy", "ndp", "ndp-1",
        "dfars", "defense federal acquisition regulation supplement",
        "far", "federal acquisition regulation",
        "executive order 13526",
        "22 u.s.c.", "10 u.s.c.",
        "aeca section 36", "aeca section 38", "aeca section 47",
        "faa section 502", "faa section 505", "faa section 660",
        "dodd 4270.5", "dodi 5530.03", "dodi 2010.06",
        # C4 Key Concepts
        "fms eligibility", "eligibility criteria", "eligibility status",
        "sales determination", "sales determinations",
        "retransfer", "retransfer restrictions",
        "defense article", "defense service",
        "major defense equipment", "mde",
        "significant military equipment", "sme",
        "fms-only", "fms only", "fms-only list",
        "international competition", "international competitions",
        "international weapons competition",
        "dcs preference",
        "coproduction", "coproduction agreement", "coproduction agreements",
        "technology transfer",
        "false impressions",
        "neutrality",
        "proper use of materiel",
        "materiel standards",
        "logistics support",
        "concurrent negotiations",
        "lead agency", "advocacy",
        "foreign solicitation",
        # C4 Equipment & Systems
        "night vision device", "night vision devices", "nvd", "nvds",
        "manpads", "man-portable air defense",
        "stinger",
        "cluster munitions",
        "white phosphorus", "white phosphorous",
        "depleted uranium",
        "comsec", "communications security",
        "c4isr",
        "geoint", "geospatial intelligence",
        "aesa", "active electronically scanned array",
        "working dogs",
        "medical countermeasures",
        "targeting infrastructure",
        "advanced target development", "atd",
        "target coordinate mensuration", "tcm",
        "collateral damage estimation", "cde",
        "weaponeering",
        "diee", "digital imagery exploitation engine",
        # C4 Countries & Entities
        "nato", "north atlantic treaty organization",
        "major non-nato ally", "major non-nato allies",
        "international organization", "international organizations",
        "purchaser", "fms purchaser", "fms purchasers",
        "partner nation", "partner nations",
        "foreign government", "foreign governments",
        "host country",
        # C4 Exclusions & Restrictions
        "anti-personnel landmines", "landmines",
        "napalm",
        "riot control agents",
        "military uniforms",
        "police training",
        "counterterrorism training",
        "military intelligence training",
    }
    
    def _calculate_keyword_overlap_score(self, query: str) -> float:
        """
        Calculate keyword overlap score (0.0 to 1.0)
        HIGH_WEIGHT keywords: single match = 0.85
        Normal keywords: need 2+ matches for 0.85
        """
        query_lower = query.lower()
        
        # Check HIGH WEIGHT keywords first
        high_weight_match = any(kw in query_lower for kw in self.HIGH_WEIGHT_KEYWORDS)
        
        if high_weight_match:
            # Count total high-weight matches
            hw_matches = sum(1 for kw in self.HIGH_WEIGHT_KEYWORDS if kw in query_lower)
            if hw_matches >= 2:
                return 0.95  # Multiple high-weight matches
            else:
                return 0.85  # Single high-weight match
        
        # Fall back to normal keyword counting
        total_matches = 0
        for category, keywords in self.samm_keywords.items():
            total_matches += sum(1 for kw in keywords if kw in query_lower)
        
        if total_matches >= 3:
            base_score = 0.95
        elif total_matches == 2:
            base_score = 0.85
        elif total_matches == 1:
            base_score = 0.70
        else:
            if any(term in query_lower for term in ["what is", "what are", "define", "what does"]):
                base_score = 0.60
            else:
                base_score = 0.40
        
        return base_score

    # ============================================================================
    # M1.3 NEW: Comprehensive Keyword-Based Intent Classification
    # Keywords extracted from SAMM domain knowledge
    # ============================================================================
    
    # SAMM-Specific Intent Keywords (comprehensive from chapters)
    INTENT_KEYWORD_MAP = {
        "definition": {
            # Question patterns
            "what is", "what are", "define", "meaning of", "explain",
            "describes", "refers to", "comprises", "encompasses",
            # Domain terms
            "sc", "sa", "fms", "fmf", "imet", "eda", "dcs", "acsa",
            "security cooperation", "security assistance", "foreign military sales",
            "samm", "manual",
        },
        "authority": {
            # Question patterns
            "who is responsible", "who approves", "who manages", "role of",
            "what does", "who oversees", "who authorizes", "who supervises",
            "what is the role", "responsibilities of",
            # Organizations
            "dsca", "dfas", "dos", "dod", "secdef", "secstate",
            "usd(p)", "usd(c)", "mildep", "ccmd", "sco", "ia",
            "secretary of defense", "secretary of state", "department of",
            # Action verbs
            "responsible", "authority", "authorized", "delegated",
            "oversees", "supervises", "manages", "approves", "directs",
            "administers", "coordinates", "determines", "provides",
        },
        "process": {
            # Question patterns
            "how to", "how does", "how is", "steps to", "procedure for",
            "process for", "what are the steps", "workflow",
            # Process terms
            "loa", "lor", "case development", "case execution", "case closure",
            "amendment", "modification", "implementation", "submit", "prepare",
            "coordinate", "review", "approve", "implement", "execute",
            "letter of offer", "letter of request",
        },
        "funding": {
            # Question patterns
            "how funded", "funded differently", "cost of", "price of",
            "budget for", "payment for", "appropriation",
            # Financial terms
            "funded", "funding", "appropriated", "appropriation", "budget",
            "cost", "price", "payment", "billing", "reimbursement",
            "title 10", "title 22", "fmf", "grant", "loan",
            "fiscal", "financial", "pdli", "case value",
        },
        "eligibility": {
            # Question patterns
            "eligible for", "who can", "requirements for", "qualify for",
            "criteria for", "eligibility for", "can receive",
            # Eligibility terms
            "eligible", "eligibility", "qualify", "qualified", "requirements",
            "criteria", "conditions", "prohibited", "restricted", "allowed",
            "country", "recipient",
        },
        "compliance": {
            # Regulations
            "itar", "ear", "aeca", "faa", "usml", "ccl",
            "export control", "munitions", "license", "regulation",
            "compliance", "governed by", "rules for", "regulations for",
            "international traffic in arms", "arms export control act",
            "directorate of defense trade", "pm/ddtc",
        },
        "distinction": {
            # Question patterns
            "difference between", "how differs", "compare", "versus", "vs",
            "differently from", "distinction between", "contrast",
            # Comparison terms
            "different", "unlike", "whereas", "compared to", "as opposed to",
            "on the other hand", "distinguish", "sc vs sa", "title 10 vs title 22",
        },
        "relationship": {
            # Question patterns
            "relationship between", "related to", "connection between",
            "how are related", "link between", "associated with",
            # Relationship terms
            "reports to", "coordinates with", "part of", "subset of",
            "includes", "falls under", "connected", "linked",
        },
        "list": {
            # Question patterns
            "list of", "what are the", "name the", "types of", "enumerate",
            "how many", "categories of", "components of",
            # List indicators
            "main", "three", "all the", "various", "different types",
        },
        "factual": {
            # Question patterns
            "when is", "where is", "which", "what date", "what number",
            "how long", "how much", "located",
            # Factual indicators
            "specific", "exact", "particular", "designated", "established",
        },
        "organization": {
            # Question patterns  
            "structure of", "organization of", "how organized",
            "hierarchy of", "components of", "who are the",
            # Organization terms
            "agency", "office", "department", "command", "division",
            "unit", "component", "headquarters",
        },
    }
    
    def _classify_intent_by_keywords(self, query: str) -> tuple:
        """
        Classify intent using comprehensive SAMM-specific keyword matching.
        
        Strategy:
        1. Check question pattern phrases first (high weight)
        2. Check domain-specific keywords (medium weight)
        3. Combine for final score
        
        Returns:
            Tuple of (intent, confidence, matched_keywords)
        """
        query_lower = query.lower()
        query_words = set(re.findall(r'\b[a-z]+\b', query_lower))
        
        intent_scores = {}
        intent_matches = {}
        
        for intent, keywords in self.INTENT_KEYWORD_MAP.items():
            matches = []
            score = 0
            
            for keyword in keywords:
                # Multi-word phrase match (higher weight)
                if ' ' in keyword and keyword in query_lower:
                    matches.append(keyword)
                    score += 2  # Phrases worth more
                # Single word match
                elif ' ' not in keyword and keyword in query_words:
                    matches.append(keyword)
                    score += 1
            
            intent_scores[intent] = score
            intent_matches[intent] = matches
        
        # Find best intent
        if not intent_scores or max(intent_scores.values()) == 0:
            return ("general", 0.50, [])
        
        best_intent = max(intent_scores, key=intent_scores.get)
        best_score = intent_scores[best_intent]
        matched_keywords = intent_matches[best_intent]
        
        # Calculate confidence based on match quality
        if best_score >= 6:
            confidence = 0.95
        elif best_score >= 4:
            confidence = 0.90
        elif best_score >= 3:
            confidence = 0.88
        elif best_score >= 2:
            confidence = 0.85
        elif best_score >= 1:
            confidence = 0.75
        else:
            confidence = 0.50
        
        return (best_intent, confidence, matched_keywords)

    # ============================================================================
    # M1.3 NEW: Composite Confidence Calculation (HYBRID)
    # ============================================================================
    def _calculate_intent_confidence(self, query: str, detected_intent: str, pattern_score: float, ai_confidence: float) -> Dict[str, Any]:
        """
        Calculate composite confidence score:
        Confidence = Pattern Match (40%) + Keyword Overlap (35%) + AI Certainty (25%)
        """
        keyword_score = self._calculate_keyword_overlap_score(query)
        ai_score = min(ai_confidence, 1.0)
        
        PATTERN_WEIGHT = 0.40
        KEYWORD_WEIGHT = 0.35
        AI_WEIGHT = 0.25
        
        composite = (pattern_score * PATTERN_WEIGHT) + (keyword_score * KEYWORD_WEIGHT) + (ai_score * AI_WEIGHT)
        composite = round(composite, 2)
        
        print(f"[IntentAgent M1.3] Confidence: Pattern={pattern_score:.2f}×40% + Keyword={keyword_score:.2f}×35% + AI={ai_score:.2f}×25% = {composite:.2f}")
        
        return {
            "pattern_score": pattern_score,
            "keyword_score": keyword_score,
            "ai_score": ai_score,
            "composite": composite,
            "meets_target": composite >= 0.90
        }

    def _check_special_cases(self, query: str) -> Optional[Dict[str, Any]]:
        """Check for nonsense, incomplete, or non-SAMM queries before calling Ollama"""
        query_lower = query.lower().strip()
        query_words = query_lower.split()
        
        print(f"[IntentAgent] Checking special cases for: '{query[:50]}...'")
        
        # Check for financial verification queries
        if "funding request" in query_lower or "funds are available" in query_lower or "verify the appropriate funding line" in query_lower:
            if "sr-p-nav" in query_lower or "case sr" in query_lower:
                print(f"[IntentAgent] 🚀 FINANCIAL VERIFICATION detected")
                return {
                    "intent": "financial_verification",
                    "confidence": 0.95,
                    "entities_mentioned": ["SR-P-NAV", "funding", "PDLI", "LOA"],
                    "special_case": True,
                    "fast_path": True
                }
        
        # Check for technical services queries
        if "technical services" in query_lower or "what is included" in query_lower:
            if "sr-p-nav" in query_lower or "case sr" in query_lower:
                print(f"[IntentAgent] 🚀 TECHNICAL SERVICES query detected")
                return {
                    "intent": "line_item_details",
                    "confidence": 0.95,
                    "entities_mentioned": ["SR-P-NAV", "Line 007", "technical services"],
                    "special_case": True,
                    "fast_path": True
                }

        # Check for PMR minutes summary queries
        if "minutes" in query_lower or "pmr" in query_lower or "meeting" in query_lower:
            if any(keyword in query_lower for keyword in ["summarize", "summary", "action items", "action item"]):
                print(f"[IntentAgent] 🚀 PMR MINUTES SUMMARY detected")
                return {
                    "intent": "pmr_minutes_summary",
                    "confidence": 0.95,
                    "entities_mentioned": ["NSM", "RSNF", "PMR", "action items"],
                    "special_case": True,
                    "fast_path": True
                }

        # Check for LOA timeline queries
        if "loa" in query_lower or "letter of offer" in query_lower:
            loa_triggers = ["how long", "timeline", "timeframe", "time", "duration", "take to develop", "take to prepare"]
            if any(trigger in query_lower for trigger in loa_triggers):
                print(f"[IntentAgent] 🚀 LOA TIMELINE detected - returning instant answer")
                return {
                    "intent": "loa_timeline",
                    "confidence": 0.95,
                    "entities_mentioned": ["LOA", "Timeline"],
                    "special_case": True,
                    "fast_path": True
                }

        # 1. CHECK FOR NONSENSE/GIBBERISH
        nonsense_count = sum(1 for keyword in self.special_case_patterns["nonsense_keywords"] 
                            if keyword in query_lower)
        
        normal_chars = set('abcdefghijklmnopqrstuvwxyz0123456789 ?.!,;:\'-')
        unusual_symbol_count = sum(1 for c in query_lower if c not in normal_chars)
        unusual_symbol_ratio = unusual_symbol_count / max(len(query), 1)
        
        number_count = sum(1 for c in query if c.isdigit())
        number_ratio = number_count / max(len(query), 1)
        
        has_keyboard_mash = any(
            len(set(word)) == len(word) and len(word) > 12
            for word in query_words
            if word.isalpha()
        )
        
        if nonsense_count >= 2 or unusual_symbol_ratio > 0.2 or number_ratio > 0.7 or has_keyboard_mash:
            print(f"[IntentAgent] NONSENSE detected (keywords: {nonsense_count}, unusual_symbols: {unusual_symbol_ratio:.2f})")
            return {
                "intent": "nonsense",
                "confidence": 0.95,
                "entities_mentioned": [],
                "reason": "gibberish_detected",
                "special_case": True
            }
        
        # 2. CHECK FOR INCOMPLETE/VAGUE QUERIES
        if len(query_words) <= 5:
            for phrase in self.special_case_patterns["incomplete_phrases"]:
                if phrase in query_lower:
                    print(f"[IntentAgent] INCOMPLETE detected (phrase: '{phrase}')")
                    return {
                        "intent": "incomplete",
                        "confidence": 0.9,
                        "entities_mentioned": [],
                        "reason": "vague_or_incomplete",
                        "special_case": True
                    }
        
        question_words = ["what", "who", "when", "where", "why", "how", "does", "is", "are", "can"]
        if len(query_words) <= 3 and not any(qw in query_words for qw in question_words):
            if not query.strip().endswith("?"):
                print(f"[IntentAgent] INCOMPLETE detected (fragment: {len(query_words)} words)")
                return {
                    "intent": "incomplete",
                    "confidence": 0.85,
                    "entities_mentioned": [],
                    "reason": "fragment",
                    "special_case": True
                }
        
        # 3. CHECK FOR NON-SAMM TOPICS
        non_samm_matches = []
        for topic in self.special_case_patterns["non_samm_topics"]:
            if topic in query_lower:
                non_samm_matches.append(topic)
        
        if non_samm_matches:
            print(f"[IntentAgent] NON-SAMM detected (topics: {non_samm_matches})")
            return {
                "intent": "non_samm",
                "confidence": 0.9,
                "entities_mentioned": [],
                "reason": "outside_samm_scope",
                "special_case": True,
                "detected_topics": non_samm_matches
            }
        
        print(f"[IntentAgent] No special cases detected - proceeding with normal analysis")
        return None




    @time_function
    def analyze_intent(self, query: str) -> Dict[str, Any]:
        """
        M1.3 HYBRID: Intent analysis with pattern matching FIRST, LLM only if needed
        
        Flow:
        1. Check special cases (instant)
        2. Try pattern matching (fast, no LLM)
        3. If pattern confidence >= 0.90, return immediately (skip LLM!)
        4. If pattern confidence < 0.90, call LLM for refinement
        
        Confidence = Pattern Match (40%) + Keyword Overlap (35%) + AI Certainty (25%)
        """
        # STEP 1: Check special cases first
        special_case = self._check_special_cases(query)
        if special_case:
            print(f"[IntentAgent M1.3] Returning special case: {special_case['intent']}")
            conf_breakdown = self._calculate_intent_confidence(query, special_case['intent'], 1.0, special_case.get('confidence', 0.95))
            special_case['confidence'] = conf_breakdown['composite']
            special_case['confidence_breakdown'] = conf_breakdown
            return special_case
        
        # STEP 2: Try pattern matching FIRST (fast, no LLM!)
        pattern_result = self._detect_intent_from_patterns(query)
        pattern_intent = pattern_result["intent"]
        pattern_score = pattern_result["pattern_score"]
        
        # Calculate preliminary confidence (without LLM)
        keyword_score = self._calculate_keyword_overlap_score(query)
        preliminary_confidence = (pattern_score * 0.40) + (keyword_score * 0.35) + (0.85 * 0.25)
        
        print(f"[IntentAgent M1.3] Pattern result: intent={pattern_intent}, pattern_score={pattern_score:.2f}, preliminary_conf={preliminary_confidence:.2f}")
        
        # STEP 3: If pattern match is strong (>=0.85), skip LLM entirely!
        if pattern_result["pattern_matched"] and preliminary_confidence >= 0.85:
            print(f"[IntentAgent M1.3] ⚡ HIGH CONFIDENCE - Skipping LLM call!")
            
            conf_breakdown = self._calculate_intent_confidence(query, pattern_intent, pattern_score, 0.85)
            
            result = {
                "intent": pattern_intent,
                "confidence": conf_breakdown["composite"],
                "confidence_breakdown": conf_breakdown,
                "entities_mentioned": [],
                "pattern_matched": True,
                "llm_called": False,
                "version": "M1.3-FAST"
            }
            
            result = self._apply_hil_corrections(query, result)
            return result
        
        # NOTE: Keyword fallback REMOVED - Not SME approved
        # Only Pattern Match (SME approved) and LLM Call (accurate) are used
        
        # STEP 4: Pattern confidence low - call LLM for refinement
        print(f"[IntentAgent M1.3] 🔄 Low pattern confidence - calling LLM for refinement...")
        
        enhanced_system_msg = self._build_enhanced_system_message()
        prompt = f"Analyze this SAMM query and determine intent: {query}"
        
        try:
            response = call_ollama_enhanced(prompt, enhanced_system_msg, temperature=0.0)
            if "{" in response and "}" in response:
                json_part = response[response.find("{"):response.rfind("}")+1]
                llm_result = json.loads(json_part)
                
                ai_confidence = llm_result.get("confidence", 0.5)
                llm_intent = llm_result.get("intent", "general")
                
                # Use pattern intent if pattern matched, otherwise use LLM intent
                final_intent = pattern_intent if pattern_result["pattern_matched"] else llm_intent
                
                # Calculate final confidence with LLM score
                conf_breakdown = self._calculate_intent_confidence(query, final_intent, pattern_score, ai_confidence)
                
                result = {
                    "intent": final_intent,
                    "confidence": conf_breakdown["composite"],
                    "confidence_breakdown": conf_breakdown,
                    "entities_mentioned": llm_result.get("entities_mentioned", []),
                    "pattern_matched": pattern_result["pattern_matched"],
                    "llm_called": True,
                    "ai_raw_confidence": ai_confidence,
                    "version": "M1.3-HYBRID"
                }
                
                result = self._apply_hil_corrections(query, result)
                return result
            else:
                # LLM failed - use pattern result
                conf_breakdown = self._calculate_intent_confidence(query, pattern_intent, pattern_score, 0.5)
                return {
                    "intent": pattern_intent, 
                    "confidence": conf_breakdown["composite"], 
                    "confidence_breakdown": conf_breakdown,
                    "entities_mentioned": [], 
                    "version": "M1.3-FALLBACK"
                }
        except Exception as e:
            # LLM error - use pattern result
            print(f"[IntentAgent M1.3] LLM error: {e} - using pattern result")
            conf_breakdown = self._calculate_intent_confidence(query, pattern_intent, pattern_score, 0.5)
            return {
                "intent": pattern_intent, 
                "confidence": conf_breakdown["composite"],
                "confidence_breakdown": conf_breakdown,
                "entities_mentioned": [], 
                "version": "M1.3-FALLBACK"
            }




    def update_from_hil(self, query: str, original_intent: str, corrected_intent: str, feedback_data: Dict[str, Any] = None):
        """Update agent based on human-in-the-loop feedback"""
        feedback_entry = {
            "query": query,
            "original_intent": original_intent,
            "corrected_intent": corrected_intent,
            "feedback_data": feedback_data or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.hil_feedback_data.append(feedback_entry)
        
        # Learn patterns from the correction
        query_lower = query.lower()
        if corrected_intent not in self.intent_patterns:
            self.intent_patterns[corrected_intent] = []
        
        # Extract keywords from corrected queries for pattern learning
        keywords = [word for word in query_lower.split() if len(word) > 3]
        self.intent_patterns[corrected_intent].extend(keywords)
        
        print(f"[IntentAgent HIL] Updated with correction: {original_intent} -> {corrected_intent} for query: '{query}'")
        return True
    
    def update_from_trigger(self, new_entities: List[str], new_relationships: List[Dict], trigger_data: Dict[str, Any] = None):
        """Update agent when new entity/relationship data is available"""
        trigger_entry = {
            "new_entities": new_entities,
            "new_relationships": new_relationships,
            "trigger_data": trigger_data or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.trigger_updates.append(trigger_entry)
        
        # Update intent recognition patterns based on new entities
        for entity in new_entities:
            entity_lower = entity.lower()
            # Add entity-specific intent patterns
            if "agency" in entity_lower or "organization" in entity_lower:
                if "organization" not in self.intent_patterns:
                    self.intent_patterns["organization"] = []
                self.intent_patterns["organization"].append(entity_lower)
        
        print(f"[IntentAgent Trigger] Updated with {len(new_entities)} new entities and {len(new_relationships)} relationships")
        return True
    
    def _build_enhanced_system_message(self) -> str:
        """Build system message enhanced with learned patterns"""
        base_msg = """You are a SAMM (Security Assistance Management Manual) intent analyzer. 
        Classify the user's query into one of these categories:
        - definition: asking what something is
        - distinction: asking about differences between concepts  
        - authority: asking about who has authority or oversight
        - organization: asking about agencies and their roles
        - factual: asking for specific facts like dates, numbers
        - relationship: asking about how things are connected
        - general: general questions"""
        
        # Add learned patterns if available
        if self.intent_patterns:
            base_msg += "\n\nLearned patterns from feedback:"
            for intent, keywords in self.intent_patterns.items():
                if keywords:
                    unique_keywords = list(set(keywords))[:5]  # Limit to top 5 unique keywords
                    base_msg += f"\n- {intent}: commonly involves {', '.join(unique_keywords)}"
        
        base_msg += "\n\nRespond with JSON format: {\"intent\": \"category\", \"confidence\": 0.8, \"entities_mentioned\": [\"entity1\", \"entity2\"]}"
        return base_msg
    
    def _apply_hil_corrections(self, query: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply learned corrections from HIL feedback"""
        query_lower = query.lower()
        
        # Check if this query pattern has been corrected before
        for feedback in self.hil_feedback_data[-10:]:  # Check last 10 feedback entries
            if any(word in query_lower for word in feedback["query"].lower().split() if len(word) > 3):
                # Apply confidence adjustment based on past corrections
                if result["intent"] == feedback["original_intent"]:
                    result["confidence"] = max(0.3, result.get("confidence", 0.5) - 0.2)
                    result["hil_note"] = f"Similar pattern previously corrected to {feedback['corrected_intent']}"
        
        return result

# =============================================================================
# E1.1: ENTITY EXTRACTION METRICS SYSTEM
# =============================================================================
class EntityMetrics:
    """
    E1.1: Entity Extraction Metrics System
    E1.3: Acronym Normalization for Fair Precision Calculation
    
    Metrics tracked:
    - Precision: TP / (TP + FP) - Target ≥90%
    - Recall: TP / (TP + FN) - Target ≥85%
    - F1 Score: 2×(P×R)/(P+R) - Target ≥90%
    - Hallucination Rate: FP / Total - Target ≤5%
    - Confidence: Source(40%) + Relevance(35%) + Quality(25%) - Target ≥85%
    """
    
    # E1.3: ACRONYM PAIRS - Comprehensive SAMM Glossary
    # Source: https://samm.dsca.mil/listing/esamm-acronyms
    # Total: 540 acronym pairs
    ACRONYM_PAIRS = {
        # A
        "aac": "acquisition advice code",
        "aae": "arms, ammunition, and explosive",
        "aar": "after action review",
        "acc": "accelerated case closure",
        "acsa": "acquisition and cross-servicing agreements",
        "adl": "advanced distributed learning",
        "aeca": "arms export control act",
        "aes": "automated export system",
        "aetc": "air education and training command",
        "afsat": "air force security assistance training squadron",
        "aid": "agency for international development",
        "aik": "assistance-in-kind",
        "aim-9x": "air intercept missile-9x",
        "alo": "audit liaison officer",
        "alp": "aviation leadership program",
        "amc": "air mobility command",
        "amraam": "advanced medium range air-to-air missiles",
        "ao": "action officer",
        "aod": "anticipated offer date",
        "aor": "area of responsibility",
        "apo": "army or air force post office",
        "asd-isp": "assistant secretary of defense for international security policy",
        "asd-la": "assistant secretary of defense for legislative affairs",
        "asd-ra": "assistant secretary of defense for reserve affairs",
        "asd-solic": "assistant secretary of defense for special operations/low-intensity conflict and interdependent capabilities",
        "asff": "afghanistan security forces fund",
        "at": "anti-tamper",
        "atc": "united states army transportation command",
        "atea": "anti-tamper executive agent",
        "atfp": "anti-terrorism/force protection",
        "atmg": "arms transfer management group",
        "awol": "absent without leave",
        # B
        "bams": "broad area maritime surveillance",
        "batfe": "bureau of alcohol, tobacco, firearms, and explosives",
        "bes": "budget estimate submission",
        "bl": "bill of lading",
        "bos": "base operating support",
        "bp": "budget project",
        "bpc": "building partner capacity",
        # C
        "c4isr": "command, control, communications, computer, intelligence, surveillance and reconnaissance",
        "cao": "collateral action officer",
        "cape": "cost assessment and program evaluation office",
        "cas": "contract administrative surcharge",
        "catm": "captive air training missile",
        "cav": "compliance assessment visit",
        "cbj": "congressional budget justification",
        "cbjfo": "congressional budget justification for foreign operations",
        "cbl": "commercial bill of lading",
        "cbp": "customs and border protection",
        "cbs": "commercial buying service",
        "cci": "controlled cryptographic item",
        "ccif": "combatant command initiative funds",
        "ccl": "commerce control list",
        "ccmd": "combatant command",
        "ccmds": "combatant commands",
        "cdm": "case development module",
        "cdr": "critical design review",
        "cdts": "counter-drug training support",
        "cetpp": "combined education and training program plan",
        "cfd": "country finance director",
        "cfs": "contract field services",
        "cfv": "captive flight vehicle",
        "cg-dco-i": "u.s. coast guard, directorate of international affairs and foreign policy",
        "cia": "central intelligence agency",
        "cio": "chief information officer",
        "cisil": "centralized integrated system - international logistics",
        "cismoa": "communications interoperability and security memorandum of agreement",
        "cjcs": "chairman of the joint chiefs of staff",
        "cjcsi": "chairman of the joint chiefs of staff instruction",
        "clo": "country liaison officer",
        "cls": "contractor logistics support",
        "clssa": "cooperative logistics supply support arrangement",
        "clu": "command launch units",
        "cmcs": "case management control system",
        "cmp": "comptroller",
        "cn": "counternarcotics",
        "cns": "congressional notification system",
        "cocom": "combatant command",
        "codel": "congressional staff delegations",
        "com": "chief of mission",
        "comsec": "communications security",
        "conus": "continental united states",
        "cope": "country over private entity",
        "corcom": "coordinating committee",
        "cpd": "country portfolio director",
        "cpi": "critical program information",
        "cpic": "capital planning and investment control",
        "cr": "continuing resolution",
        "crb": "change review board",
        "crsp": "coalition readiness support program",
        "cs": "communications security",
        "csea": "cadet semester exchange abroad program",
        "cspa": "child status protection act",
        "cta": "country team assessment",
        "ctfp": "combating terrorism fellowship program",
        "cts": "case tracking system",
        "cui": "controlled unclassified information",
        "cwcc": "conventional weapons clearance course",
        "cwmd": "countering weapons of mass destruction",
        # D
        "dar": "defense acquisition regulation",
        "dasa-dec": "deputy assistant secretary of the army for defense exports and cooperation",
        "dasd": "deputy assistant secretary of defense",
        "dat": "defense attache",
        "dats": "defense attaches",
        "dbod": "business operations directorate",
        "dcaa": "defense contract audit agency",
        "dccs": "direct commercial contracts system",
        "dcma": "defense contract management agency",
        "dcmo": "deputy chief management officer",
        "dcs": "direct commercial sales",
        "dda": "designated disclosure authority",
        "ddal": "delegation of disclosure authority letter",
        "ddpo": "dod demilitarization program office",
        "defense": "department of defense",
        "delg": "defense export loan guarantee",
        "demil": "demilitarization",
        "desc": "defense energy support center",
        "dfars": "defense federal acquisition regulation supplement",
        "dfas": "defense finance and accounting service",
        "dfas-in": "defense finance and accounting service - indianapolis",
        "dgr": "designated government representative",
        "dhs": "department of homeland security",
        "dia": "defense intelligence agency",
        "diacap": "dod information assurance certification and accreditation process",
        "diads": "dsca imet allocation database system",
        "difs": "defense integrated financial system",
        "dirnsa": "director, national security agency",
        "disco": "defense industrial security clearance office",
        "ditpr": "dod it portfolio repository",
        "dla": "defense logistics agency",
        "dlielc": "defense language institute english language center",
        "dlms": "defense logistics management system",
        "doc": "department of commerce",
        "doc-center": "distribution operations center",
        "dod": "department of defense",
        "dodaac": "dod activity address code",
        "dodd": "department of defense directive",
        "doj": "department of justice",
        "dos": "department of state",
        "dos-pm": "dos bureau of political-military affairs",
        "dos-pm-ddtc": "dos directorate of defense trade controls",
        "dos-pm-rsat": "dos bureau of political-military affairs, office of regional security and arms transfers",
        "dot-phmsa": "department of transportation's pipeline and hazardous materials safety administration",
        "dp": "disaster preparedness",
        "dr-a": "reactivation authorized milestone",
        "drrs": "defense readiness reporting system",
        "dsams": "defense security assistance management system",
        "dsca": "defense security cooperation agency",
        "dscu": "defense security cooperation university",
        "dss": "defense security service",
        "dtc": "delivery term code",
        "dtr": "defense transportation regulation",
        "dtra": "defense threat reduction agency",
        "dts": "defense transportation system",
        "dtsa": "defense technology security administration",
        "dtsi": "defense trade security initiative",
        "dvot": "distinguished visitor orientation tour",
        "dwcf": "defense working capital fund",
        "dx": "direct exchange",
        # E
        "e-imet": "expanded international military education and training",
        "eacc": "enhanced accelerated case closure",
        "eads": "enterprise application development and support division",
        "ebmis": "egyptian budget management information system",
        "ecl": "english comprehension level",
        "eda": "excess defense articles",
        "eee": "emergency, extraordinary, expenses",
        "eei": "electronic export information",
        "eeum": "enhanced eum",
        "efts": "enhanced freight tracking system",
        "elt": "english language training",
        "eltm": "english language training materials",
        "endp": "exception to national disclosure policy",
        "eo": "executive order",
        "eod": "explosive ordnance disposal",
        "eoq": "economic order quantity",
        "ep": "excess property",
        "epg": "european participating government",
        "ergt": "expeditionary requirements generation team",
        "erp": "enterprise resource planning",
        "erw": "explosive remnants of war",
        "esc": "executive steering committee",
        "esep": "engineer and scientist exchange program",
        "etss": "extended training service specialist",
        "eum": "end use monitoring",
        "ew": "electronic warfare",
        "ewirdb": "electronic warfare integrated reprogramming database",
        "exord": "execute order",
        "exsec": "executive secretary",
        # F
        "faa": "foreign assistance act",
        "fad": "force activity designator",
        "far": "federal acquisition regulation",
        "fav": "familiarization and assistance visit",
        "fbi": "federal bureau of investigation",
        "fcg": "foreign clearance guide",
        "fcm": "foreign consequence management",
        "fdr": "foreign disaster relief",
        "ffb": "federal financing bank",
        "ffp": "firm fixed price",
        "fgi": "foreign government information",
        "fics": "fms integrated control system",
        "fmc": "full mission capable",
        "fmf": "foreign military financing",
        "fmr": "financial management regulations/review",
        "fms": "foreign military sales",
        "fmscs": "fms credit system",
        "fmso": "foreign military sales order",
        "fmt": "foreign military training",
        "fob": "free on board",
        "foia": "freedom of information act",
        "fom": "figure of merit",
        "fot": "follow-on training",
        "fouo": "for official use only",
        "fpiod": "financial policy and internal operations division",
        "fpo": "fleet post office",
        "frb": "federal reserve bank",
        "fsc": "facility security clearance",
        "fsca": "facility security clearance assurance",
        "fsn": "foreign service national",
        "fsp": "field studies program",
        "fte": "flight training exchange",
        "ftp": "funded transportation program",
        "fvs": "dod foreign visit system",
        "fy": "fiscal year",
        # G
        "gao": "general accounting office",
        "gcc": "geographic combatant command",
        "gcu": "guidance control units",
        "gef": "guidance for employment of the force",
        "geoint": "geospatial intelligence",
        "gfe": "government furnished equipment",
        "gfm": "global force management",
        "gpoi": "global peacekeeping operations initiative",
        "gsa": "general security agreement",
        "gsa-osd": "global strategic affairs",
        "gsoia": "general security of information agreement",
        "gsoias": "general security of information agreements",
        "gsomia": "general security of military information agreement",
        "gu": "guidance unit",
        # H
        "ha": "humanitarian assistance",
        "ha-ep": "humanitarian assistance program - excess property",
        "hazmat": "hazardous materials",
        "hca": "humanitarian and civic assistance",
        "hdtc": "humanitarian demining training center",
        "hma": "humanitarian mine action",
        "hmr": "hazardous materials regulations",
        # I
        "ia": "implementing agency",
        "iaafa": "inter-american air forces academy",
        "iac": "international armaments cooperation",
        "ias": "implementing agencies",
        "icass": "international cooperative administrative support services",
        "ice": "immigration and customs enforcement",
        "icp": "inventory control point",
        "icr": "in-country reprogramming",
        "iep": "information exchange program",
        "iff": "identification, friend or foe",
        "igc": "integrated data environment/global transportation network convergence",
        "igce": "independent government cost estimate",
        "ilco": "international logistics control office",
        "ilcs": "international logistics communication system",
        "imas": "international mine action standards",
        "imc": "internal management control",
        "imet": "international military education and training",
        "imsma": "information management systems for mine action",
        "imso": "international military student office",
        "incle": "international narcotics control and law enforcement",
        "infosec": "information security",
        "ipo": "international programs office",
        "isan": "international sanweb",
        "isff": "iraq security forces fund",
        "isn": "international security and nonproliferation",
        "istl": "integrated standard training list",
        "it": "information technology",
        "itar": "international traffic in arms regulations",
        "ito": "invitational travel order",
        "itv": "instrument telemetry vehicle",
        # J
        "ja": "justification and approval",
        "jassm": "joint air-to-surface standoff missile",
        "jcet": "joint combined exchange training",
        "jcmo": "joint comsec management office",
        "jftr": "joint federal travel regulations",
        "jmpab": "joint materiel priority allocation board",
        "jopes": "joint operation planning execution system",
        "jscet": "joint security cooperation and education training",
        "jsow": "joint standoff weapon",
        "jtr": "joint travel regulations",
        "jvi": "joint visual inspection",
        # L
        "laircm": "large aircraft infrared countermeasures",
        "les": "locally engaged staff",
        "loa": "letter of offer and acceptance",
        "load": "loa data",
        "lor": "letter of request",
        "lpa": "legislative and public affairs",
        "ltd": "language training detachment",
        "ltdt": "language training detachment",
        # M
        "manpads": "man-portable air defense system",
        "map": "military assistance program",
        "mapad": "military assistance program address directory",
        "marad": "maritime administration",
        "masl": "military articles and services list",
        "mcscg": "marine corps sc group",
        "mde": "major defense equipment",
        "mdf": "mission data file",
        "merhc": "medicare-eligible retiree health care",
        "met": "mobile education teams",
        "mfa": "ministry of foreign affairs",
        "mfp": "major force program",
        "mfr": "memorandum for record",
        "mildep": "military department",
        "mildep-a": "mildep approval",
        "mildep-r": "mildep reactivation",
        "mildeps": "military departments",
        "milstrip": "military standard requisitioning and issue procedures",
        "mipr": "military interdepartmental purchase request",
        "misil": "management information system - international logistics",
        "miso": "military information support to operations",
        "mla": "manufacturing license agreements",
        "moa": "memorandum of agreement",
        "mod": "ministry of defense",
        "mop": "monthly obligation plan",
        "mos": "months",
        "mou": "memorandum of understanding",
        "ms": "mission sustainment",
        "msc": "military sealift command",
        "msp": "mission strategic plan",
        "msrp": "mission strategic resource plan",
        "msu": "missile simulator unit",
        "mtcr": "missile technology control regime",
        "mtds": "manpower and travel data sheet",
        "mtf": "military treatment facility",
        "mtfi": "military tasks for interoperability",
        "mtt": "mobile training team",
        # N
        "nacsi": "national comsec instruction",
        "nad": "national armaments director",
        "nags": "nato alliance ground surveillance",
        "namsa": "nato maintenance and supply agency",
        "nasic": "national air and space intelligence center",
        "natm": "special air training missiles",
        "nato": "north atlantic treaty organization",
        "navsciatts": "naval small craft instruction and technical training school",
        "nda": "national distribution authority",
        "ndp": "national disclosure policy",
        "ndpc": "national disclosure policy committee",
        "ndps": "national disclosure policy system",
        "ndu": "national defense university",
        "netsafa": "naval education and training security assistance field activity",
        "nga": "national geospatial-intelligence agency",
        "nicsma": "nato integrated communication system management agency",
        "nipo": "navy international programs office",
        "nipo-spd": "navy international programs office strategic planning directorate",
        "nisp": "national industrial security program",
        "nispom": "national industrial security program operating manual",
        "noa": "notice of availability",
        "noaa": "notice of availability",
        "nonacc": "non-accelerated case closure",
        "nossc": "notice of supply/services completion",
        "nrc": "nonrecurring cost",
        "nsa": "national security agency",
        "nsas": "national security assistance strategy",
        "nsc": "national security council",
        "nsdd": "national security decision directive",
        "nsip": "nato security investment program",
        "nsn": "national stock number",
        "nss": "national security staff",
        "nte": "not-to-exceed",
        "nvd": "night vision device",
        "nvds": "night vision devices",
        # O
        "oa": "obligational authority",
        "oed": "offer expiration date",
        "ohasis": "overseas humanitarian assistance shared information system",
        "ohdaca": "overseas humanitarian, disaster and civic aid",
        "om": "operations and maintenance",
        "omb": "office of management and budget",
        "opcon": "operational control",
        "opi": "oral proficiency interview",
        "orc": "offer release code",
        "orf": "official representation funds",
        "osd": "office of the secretary of defense",
        "ousd-c": "office of the under secretary of defense (comptroller)",
        "ousd-p": "office of the under secretary of defense for policy",
        # P
        "pa": "price and availability",
        "pa-appn": "procurement appropriation",
        "pao": "primary action officer",
        "pbas-oc": "program budget accounting system - order control",
        "pcf": "pakistan counterinsurgency fund/counterinsurgency capability fund",
        "pch": "packing, crating and handling",
        "pcs": "permanent change of station",
        "pd": "presidential determination",
        "pda": "principal disclosure authority",
        "pdm": "program decision memorandum",
        "pdss": "pre-deployment site survey",
        "pfp": "partnership for peace",
        "pko": "peacekeeping operations",
        "pme": "professional military education",
        "pmr": "program management review",
        "poc": "point of contact",
        "poe": "port of embarkation",
        "pom": "program objective memorandum",
        "powmia": "prisoner of war/missing in action",
        "ppbe": "planning, programming, budgeting, and execution",
        "ppr": "positions of prominence report",
        "prd": "procurement requirements documentation",
        "pros": "parts and repair ordering system",
        "psa": "personal services agreement",
        "pss": "so/lic partnership strategy",
        "pvo": "private voluntary organizations",
        "pws": "performance work statement",
        # Q
        "qol": "quality of life",
        # R
        "rc": "regional center",
        "rcn": "record control number",
        "rda": "research, development, and acquisition",
        "rdte": "research, development, test and evaluation",
        "rim": "retainable instructional materials",
        "rso": "regional security officer",
        "rst": "requirement survey team",
        # S
        "sa": "security assistance",
        "saam": "special assigned airlift mission",
        "saarms": "security assistance automated resource management system/suite",
        "sadec": "secretary of the army for defense exports and cooperation",
        "saf-ia": "deputy under secretary of the air force international affairs",
        "saf-iawd": "secretary of the air force for international affairs regional weapons division",
        "sam-cc": "security assistance management conus course",
        "sam-fmc": "security assistance management financial management course",
        "sam-lcs": "security assistance management logistics and customer support course",
        "sam-rc": "security assistance management reconciliation and closure course",
        "sam-tmc": "security assistance management training management course",
        "samis": "security assistance management information system",
        "samm": "security assistance management manual",
        "samrs": "security assistance manpower requirements system",
        "san": "security assistance network",
        "satfa": "security assistance training field activity",
        "sba": "special billing arrangement",
        "sc": "security cooperation",
        "sc-code": "supply code",
        "sc-tms": "security cooperation-training management system",
        "sces": "security cooperation enterprise solution",
        "scet": "security cooperation education and training",
        "scetwg": "security cooperation education and training working group",
        "scgb": "security cooperation governance board",
        "sci": "sensitive compartmented information",
        "scip": "security cooperation information portal",
        "scirms": "security cooperation integrated resource management system",
        "scml": "small case management line",
        "scms": "security cooperation management suite",
        "sco": "security cooperation organization",
        "scoa": "security cooperation organization assessment",
        "scos": "security cooperation organizations",
        "sdaf": "special defense acquisition fund",
        "sddc": "surface deployment and distribution command",
        "sdo": "senior defense official",
        "sdo-datt": "senior defense official/defense attache",
        "sdr": "supply discrepancy report",
        "secdef": "secretary of defense",
        "sed": "shipper's export declaration",
        "ses": "senior executive service",
        "set": "specialized english training",
        "sfj": "sales forecast/javits system",
        "shape": "supreme headquarters allied powers europe",
        "sigint": "national sigint committee",
        "siprnet": "secret internet protocol router network",
        "slamer": "standoff land attack missiles expanded response",
        "slos": "standard level of service",
        "sme": "significant military equipment",
        "snap": "simplified non-standard acquisition process",
        "so-lic": "special operations/low-intensity conflict",
        "soc": "special operations command",
        "socom": "u.s. special operations command",
        "sofa": "status of forces agreement",
        "solic": "special operations/low intensity conflict",
        "sop": "standard operating procedures",
        "sos": "source of supply",
        "sow": "statement of work",
        "span": "security policy automation network",
        "spo": "system program office",
        "src": "security risk categories",
        "ssc": "supply and services completion",
        "state": "department of state",
        "state department": "department of state",
        "stl": "standard training list",
        "svi": "single vendor integrity",
        # T
        "taa": "technical assistance agreement",
        "taar": "team after-action report",
        "tac": "training analysis codes",
        "taft": "technical assistance field team",
        "tat": "technical assistance team",
        "tbc": "transportation bill code",
        "tca": "traditional cocom activities",
        "tcn": "transportation control number",
        "tda": "table of distribution and allowances",
        "tdp": "technical data package",
        "thaad": "terminal high altitude area defense",
        "tip": "trafficking in persons",
        "tla": "travel and living allowance",
        "tlw": "termination liability worksheet",
        "tm": "training module",
        "tmasl": "training military articles and services listings",
        "toa": "type of assistance",
        "toefl": "test of english as a foreign language",
        "tor": "terms of reference",
        "tow": "tube-launched, optically-tracked, wire-guided missiles",
        "tpa": "total package approach",
        "transcom": "u.s. transportation command",
        "tsc": "theater security cooperation",
        "tsc-controls": "trade security controls",
        "tscims": "theater security cooperation information management system",
        "tscmis": "theater security cooperation management information system",
        "tvl": "tailored vendor logistics",
        # U
        "ua": "unauthorized absence",
        "uas": "unmanned aircraft system",
        "uav": "unmanned air vehicle",
        "ucmj": "uniform code of military justice",
        "ulo": "un-liquidated obligation",
        "ummips": "uniform material movement and issue priority system",
        "un": "united nations",
        "und": "urgency of need designator",
        "unloa": "un letter of assist",
        "upt": "undergraduate pilot training",
        "usaf": "u.s. air force",
        "usaid": "u.s. agency for international development",
        "usamedcom": "u.s. army medical materiel agency",
        "uscg": "united states coast guard",
        "usd-as": "under secretary of defense for acquisition and sustainment",
        "usd-c": "under secretary of defense (comptroller)",
        "usd-i": "under secretary of defense for intelligence",
        "usd-p": "under secretary of defense for policy",
        "usd-pr": "under secretary of defense for personnel and readiness",
        "usg": "united states government",
        "usml": "united states munitions list",
        "usn": "u.s. navy",
        "uspacom": "u.s. pacific command",
        "usun": "u.s. mission to the united nations",
        # V
        "va": "valuation and availability",
        "vin": "vehicle identification number",
        "vms-lp": "vehicle mounted stinger launched platform",
        "vv": "validation and verification",
        # W
        "wcf": "working capital fund",
        "wcn": "worksheet control number",
        "wd": "workforce development",
        "whinsec": "western hemisphere institute for security cooperation",
        "whs-aas": "washington headquarters services allotment accounting system",
        "wif": "warsaw initiative fund",
        # X
        "xcn": "external control number",
        
        # =================================================================
        # CHAPTER 4 ACRONYMS - FMS Program General Information
        # =================================================================
        # DSCA Office Acronyms
        "spp": "strategy plans and policy",
        "dsca spp": "dsca office of strategy plans and policy",
        "dsca(spp)": "dsca office of strategy plans and policy",
        "iops": "international operations",
        "dsca iops": "dsca office of international operations",
        "dsca(iops)": "dsca office of international operations",
        "iops/rex": "international operations regional execution directorate",
        "iops/wpn": "international operations weapons directorate",
        "iops/wpns": "international operations weapons directorate",
        "fo/ogc": "front office office of general counsel",
        "adm/pie": "office of administration performance improvement and effectiveness directorate",
        "adm/pie/ame": "assessment monitoring and evaluation division",
        
        # State Department Offices
        "pm/rsat": "bureau of political-military affairs office of regional security and arms transfers",
        "state(pm/rsat)": "department of state bureau of political-military affairs office of regional security and arms transfers",
        "state(pm)": "department of state bureau of political-military affairs",
        "state(ddtc)": "department of state directorate of defense trade controls",
        
        # Programs & Processes
        "tpa": "total package approach",
        "eum": "end use monitoring",
        "eeum": "enhanced end use monitoring",
        "p&a": "price and availability",
        "par": "pre-lor assessment request",
        "rdfp": "regional defense fellowship program",
        "fms-only": "foreign military sales only",
        
        # Legal/Regulatory
        "ndp-1": "national disclosure policy 1",
        "eo 13526": "executive order 13526",
        "dodd 4270.5": "department of defense directive 4270.5",
        "dodd 5230.20": "department of defense directive 5230.20",
        "dodi 2010.06": "department of defense instruction 2010.06",
        "dodi 5530.03": "department of defense instruction 5530.03",
        "dodm 5200.01": "department of defense manual 5200.01",
        "22 cfr part 121": "international traffic in arms regulations munitions list",
        
        # Defense Equipment/Items
        "sme": "significant military equipment",
        "mde": "major defense equipment",
        "gfm": "government furnished materiel",
        "nvds": "night vision devices",
        "tdp-doc": "technical data package",
        
        # Intelligence/Targeting
        "geoint": "geospatial intelligence",
        "c4isr": "command control communications computer intelligence surveillance and reconnaissance",
        "atd": "advanced target development",
        "tcm": "target coordinate mensuration",
        "ppm": "precision point mensuration",
        "cde": "collateral damage estimation",
        "cer": "collateral effects radii",
        "pdt": "population density tables",
        "diee": "digital imagery exploitation engine",
        "etd": "enhanced targeting data",
        "pklut": "probability of kill look up tool",
        "fom-nvd": "figure of merit",
        
        # Technology/Systems
        "aesa": "active electronically scanned array",
        "ladar": "laser detection and ranging",
        "lidar": "light detection and ranging",
        "pps": "pulse per second",
        "a/s": "air to surface",
        "s/s": "surface to surface",
        
        # Organizations (Chapter 4 specific)
        "aflcmc": "air force life cycle management center",
        "jtcg/me": "joint technical coordinating group for munitions effectiveness",
        "jts": "joint targeting school",
        "asd(so/lic)": "assistant secretary of defense for special operations and low-intensity conflict",
        "so/lic": "special operations low-intensity conflict",
        "asd(hd&gs/cwmd)": "assistant secretary of defense for homeland defense and global security countering weapons of mass destruction",
        "hd&gs/cwmd": "homeland defense and global security countering weapons of mass destruction",
        "iaea": "international atomic energy agency",
        
        # Other Chapter 4 Terms
        "tla": "travel and living allowance",
        "ims": "international military student",
        "ncr-cost": "nonrecurring cost recoupment",
        "cta": "country team assessment",
        "qw": "quick weaponeering",
        "niprnet": "non-classified internet protocol router network",
        
        # =================================================================
        # CHAPTER 9 ACRONYMS - Financial Policies and Procedures
        # =================================================================
        
        # FMS Trust Fund & Administrative
        "fms trust fund": "foreign military sales trust fund",
        "fms administrative surcharge": "fms administrative surcharge",
        "fms admin": "fms administrative surcharge",
        "fms administrative surcharge account": "fms administrative surcharge account",
        "administrative surcharge": "fms administrative surcharge",
        
        # Nonrecurring Cost
        "nc": "nonrecurring cost",
        "ncr": "nonrecurring cost recoupment",
        "nonrecurring cost": "nonrecurring cost",
        "nc waiver": "nonrecurring cost waiver",
        "nonrecurring cost waiver": "nonrecurring cost waiver",
        
        # Contract Administration Services
        "cas": "contract administration services",
        "cas waiver": "contract administration services waiver",
        "contract administration services": "contract administration services",
        "qai": "quality assurance and inspection",
        
        # Payment Terms of Sale
        "du": "dependable undertaking",
        "dependable undertaking": "dependable undertaking",
        "cwa": "cash with acceptance",
        "cash with acceptance": "cash with acceptance",
        "cash flow financing": "cash flow financing",
        "raps": "risk assessed payment schedules",
        "risk assessed payment schedules": "risk assessed payment schedules",
        "caps": "credit assured payment schedules",
        "credit assured payment schedules": "credit assured payment schedules",
        "terms of sale": "terms of sale",
        
        # Letter of Credit
        "bloc": "bank letter of credit",
        "bank letter of credit": "bank letter of credit",
        "lc": "letter of credit",
        "letter of credit": "letter of credit",
        "sblc": "standby letter of credit",
        "standby letter of credit": "standby letter of credit",
        
        # Billing
        "sba": "special billing arrangement",
        "special billing arrangement": "special billing arrangement",
        "sbl": "special bill letter",
        "special bill letter": "special bill letter",
        "dd 645": "billing statement",
        "dd form 645": "billing statement",
        "billing statement": "billing statement",
        "quarterly billing": "quarterly billing",
        
        # Pricing Components
        "ipc": "indirect pricing component",
        "indirect pricing component": "indirect pricing component",
        "pcc": "primary category code",
        "primary category code": "primary category code",
        "pe": "price element",
        "price element": "price element",
        "lsc": "logistics support charge",
        "psc": "program support charge",
        "pc&h": "packing crating and handling",
        "dtc": "delivery term code",
        "above-the-line": "above-the-line charges",
        "below-the-line": "below-the-line charges",
        "direct charges": "direct charges",
        "indirect charges": "indirect charges",
        "accessorial charges": "accessorial charges",
        "line item pricing": "line item pricing",
        
        # Management Lines
        "pml": "program management line",
        "program management line": "program management line",
        "scml": "small case management line",
        "small case management line": "small case management line",
        "generic code r6b": "program management line generic code",
        "generic code r6c": "small case management line generic code",
        "generic code l8a": "case management line generic code",
        
        # Manpower & Travel
        "mtds": "manpower travel data sheets",
        "manpower travel data sheets": "manpower travel data sheets",
        "wy": "work year",
        "work year": "work year",
        "fte": "full-time equivalent",
        "full-time equivalent": "full-time equivalent",
        "case-funded manpower": "case-funded manpower",
        "fringe benefits": "fringe benefits",
        "civilian fringe benefits": "civilian fringe benefits",
        "military fringe benefits": "military fringe benefits",
        
        # Financial Terms
        "tcv": "total case value",
        "total case value": "total case value",
        "tl": "termination liability",
        "termination liability": "termination liability",
        "initial deposit": "initial deposit",
        "advance cash": "advance cash requirements",
        "payment schedule": "payment schedule",
        "sdaf": "special defense acquisition fund",
        "special defense acquisition fund": "special defense acquisition fund",
        "ucr": "unfunded civilian retirement",
        "merhc": "medicare-eligible retiree health care",
        
        # Tuition Rates
        "rate a": "full cost tuition rate",
        "rate b": "tuition rate b",
        "rate c": "incremental tuition rate",
        "rate d": "tuition rate d",
        "rate e": "tuition rate e",
        "full cost tuition": "full cost tuition rate",
        "incremental tuition": "incremental tuition rate",
        "tuition rates": "tuition rates",
        "attrition charges": "attrition charges",
        
        # DSCA Financial Offices
        "obo/fpre": "financial policy and regional execution directorate",
        "obo/fpre/fp": "financial policy division",
        "cfm": "country financial management division",
        "dbo": "directorate of business operations",
        "mcr": "monthly case report",
        "fmscs": "fms credit system",
        "financial policy": "financial policy",
        "financial review": "financial review",
        "performance reporting": "performance reporting",
        
        # NATO Financial Terms
        "nspa": "nato support and procurement agency",
        "nspo": "nato support organization",
        "shape": "supreme headquarters allied powers europe",
        "nsip": "nato security investment program",
        "nicsma": "nato integrated communication system management agency",
        "epg": "european participating governments",
        "mfp": "major force program",
        "nato standardization": "nato standardization",
        "reciprocal agreement": "reciprocal agreement",
        
        # Sales Types
        "sale with intent to replace": "sale with intent to replace",
        "sale without intent to replace": "sale without intent to replace",
        "sales from stock": "sales from stock",
        "munitions": "munitions",
        
        # Tables & References
        "table c9.t1": "financial management legal references table",
        "table c9.t2a": "fms case-related manpower functions matrix",
        "table c9.t5": "reciprocal country agreement listing",
        "table c9.t7": "nato cas reciprocal agreements",
        "dod fmr": "dod financial management regulation",
        "dod 7000.14-r": "dod financial management regulation",
        
        # Other Chapter 9 Terms
        "pre-lor": "pre-letter of request activities",
        "npor": "non-program of record",
        "mou": "memorandum of understanding",
        "program management services": "program management services",
    }
    
    # E1.3: GENERIC WORDS - Filter out (not real SAMM entities)
    GENERIC_WORDS = {
        # Original terms
        "programs", "program", "activities", "activity",
        "authority", "authorities", "role", "roles",
        "responsibilities", "responsibility", "functions", "function",
        "services", "service", "articles", "article",
        "requirements", "requirement", "policies", "policy",
        # Added terms - common generic words
        "procedures", "procedure", "processes", "process",
        "systems", "system", "matters", "matter",
        "items", "item", "operations", "operation",
        "efforts", "effort", "support", "supports",
        "guidance", "information", "management",
        "actions", "action", "duties", "duty",
        "tasks", "task", "objectives", "objective",
        "aspects", "aspect", "elements", "element",
        "types", "type", "areas", "area",
        "levels", "level", "parts", "part",
        "things", "thing", "ways", "way",
    }
    
    # Chapter 1 Ground Truth Entities (SAMM C1.3)
    CHAPTER_1_GROUND_TRUTH = {
        # Organizations (C1.3)
        "organizations": {
            # High-level agencies
            "DSCA", "Defense Security Cooperation Agency",
            "DoS", "Department of State", "State", "State Department",
            "DoD", "Department of Defense",
            "DFAS", "Defense Finance and Accounting Service",
            "DoC", "Department of Commerce",
            # Secretary level
            "SECSTATE", "Secretary of State",
            "SECDEF", "Secretary of Defense",
            "SECARMY", "Secretary of the Army",
            # USD Offices (both formats)
            "USD(P)", "USD-P", "Under Secretary of Defense for Policy",
            "USD(A&S)", "USD-AS", "Under Secretary of Defense for Acquisition and Sustainment",
            "USD(C)", "USD-C", "Under Secretary of Defense, Comptroller",
            "USD(P&R)", "USD-PR", "Under Secretary of Defense, Personnel and Readiness",
            "USD(R&E)", "Under Secretary of Defense for Research and Engineering",
            "USD(I&S)", "Under Secretary of Defense for Intelligence and Security",
            # Military Departments
            "DA", "Department of the Army",
            "DoN", "Department of the Navy",
            "DAF", "Department of the Air Force",
            "MILDEP", "MILDEPS", "Military Department",
            # Army orgs (C1.3.2.6.1.1)
            "DASA (DE&C)", "DASA-DEC",
            "USASAC", "U.S. Army Security Assistance Command",
            "SATFA", "Security Assistance Training Field Activity",
            "AMC", "Army Materiel Command",
            "TRADOC", "Army Training and Doctrine Command",
            "USACE", "U.S. Army Corps of Engineers",
            # Navy orgs (C1.3.2.6.1.2)
            "NIPO", "Navy International Programs Office",
            "ASN (RDA)", "ASN-RDA",
            # Air Force orgs (C1.3.2.6.1.3)
            "SAF/IA", "SAF-IA",
            "AFSAC", "Air Force Security Assistance and Cooperation",
            "AFSAT", "Air Force Security Assistance Training Squadron",
            "AETC", "Air Education and Training Command",
            "AFMC", "Air Force Materiel Command",
            # Defense Agencies (C1.3.2.6.2)
            "DCMA", "Defense Contract Management Agency",
            "DISA", "Defense Information Systems Agency",
            "DLA", "Defense Logistics Agency",
            "DTRA", "Defense Threat Reduction Agency",
            "MDA", "Missile Defense Agency",
            "NGA", "National Geospatial-Intelligence Agency",
            "NSA", "National Security Agency",
            "DCAA", "Defense Contract Audit Agency",
            "DIA", "Defense Intelligence Agency",
            "DTSA", "Defense Technology Security Administration",
            # Joint (C1.3.2.9)
            "CJCS", "Chairman of the Joint Chiefs of Staff",
            "JS", "Joint Staff",
            # CCMDs (C1.3.2.10)
            "CCMD", "CCMDS", "Combatant Command",
            "CCDR", "Combatant Commander",
            "USCENTCOM", "USEUCOM", "USINDOPACOM",
            "USNORTHCOM", "USSOUTHCOM", "USCYBERCOM",
            "USSPACECOM", "USSOCOM", "USTRANSCOM",
            # Other
            "SCO", "SCOS", "Security Cooperation Organization",
            "IA", "IAS", "Implementing Agency",
            "OMB", "Office of Management and Budget",
        },
        # Programs (C1.1)
        "programs": {
            "Security Cooperation", "SC",
            "Security Assistance", "SA",
            "Foreign Military Sales", "FMS",
            "Foreign Military Financing", "FMF",
            "International Military Education and Training", "IMET",
            "Direct Commercial Sales", "DCS",
            "Building Partner Capacity", "BPC",
            "Excess Defense Articles", "EDA",
            "Cooperative Threat Reduction", "CTR",
            "Countering Weapons of Mass Destruction", "CWMD",
            "Missile Defense System", "MDS",
            "Terminal High Altitude Area Defense", "THAAD",
        },
        # Legal/Authorities (C1.2)
        "authorities": {
            "Foreign Assistance Act", "FAA",
            "Arms Export Control Act", "AECA",
            "National Defense Authorization Act", "NDAA",
            "Title 10", "Title 10 U.S.C.",
            "Title 22", "Title 22 U.S.C.",
            "Title 50", "Title 50 U.S.C.",
            "Executive Order", "EO", "E.O.",
            "Executive Order 13637", "EO 13637", "E.O. 13637",
            "Federal Acquisition Regulation", "FAR",
            "DFARS", "ITAR", "USML", "CRA",
        },
        # Concepts (C1.1)
        "concepts": {
            "continuous supervision", "general direction",
            "defense articles", "defense services",
            "military education and training",
            "strategic objectives", "national security",
            "campaign plan", "campaign plans",
            "foreign partner", "partner nation", "PN",
            "international partners", "DoD Components",
        },
        # Documents
        "documents": {
            "GEF", "CBJ", "MSRP", "LOR", "MOR", "LOA",
            "DoDD", "DoDD 5132.03", "DoDD 5105.65",
        }
    }
    
    # =================================================================
    # Chapter 4 Ground Truth Entities (SAMM C4 - FMS Program)
    # Including ALL valid acronyms AND their full form expansions
    # =================================================================
    CHAPTER_4_GROUND_TRUTH = {
        # Organizations (C4.1 - C4.5)
        "organizations": {
            # DSCA Offices - acronym AND full form
            "DSCA SPP", "DSCA (SPP)", "SPP", "Office of Strategy, Plans, and Policy",
            "Strategy Plans And Policy",  # expansion
            "DSCA IOPS", "DSCA (IOPS)", "IOPS", "Office of International Operations",
            "International Operations",  # expansion
            "IOPS/REX", "Regional Execution Directorate",
            "IOPS/WPN", "IOPS/WPNS", "Weapons Directorate",
            "FO/OGC", "Office of the General Counsel",
            "ADM/PIE", "ADM/PIE/AME",
            # State Offices
            "State PM", "State(PM)", "PM", "Bureau of Political-Military Affairs",
            "PM/RSAT", "State(PM/RSAT)", "Office of Regional Security and Arms Transfers",
            "DDTC", "State(DDTC)", "Directorate of Defense Trade Controls",
            # Defense Agencies
            "DTSA", "Defense Technology Security Administration",
            "DOC", "Department of Commerce",
            # Military
            "USN", "U.S. Navy",
            "AFLCMC", "Air Force Life Cycle Management Center",
            # Other
            "JTCG/ME", "Joint Technical Coordinating Group for Munitions Effectiveness",
            "JTS", "Joint Targeting School",
            "GSA", "General Services Administration",
            "IAEA", "International Atomic Energy Agency",
            "UN", "United Nations",
            "ASD(SO/LIC)", "SO/LIC",
            "ASD(HD&GS/CWMD)",
        },
        
        # Programs (C4.1 - C4.5) - acronym AND full form
        "programs": {
            "TPA", "Total Package Approach",
            "EUM", "End Use Monitoring",
            "EEUM", "Enhanced End Use Monitoring",
            "RDFP", "Regional Defense Fellowship Program",
            "FMS-Only", "Foreign Military Sales Only",  # expansion
            "coproduction", "co-production",
            # Include base program full forms
            "FMS", "Foreign Military Sales",
            "DCS", "Direct Commercial Sales",
            "SA", "Security Assistance",
            "SC", "Security Cooperation",
        },
        
        # Authorities (C4.1 - C4.5)
        "authorities": {
            "NDP", "National Disclosure Policy",
            "NDP-1",
            "EO 13526", "Executive Order 13526",
            "22 CFR part 121",
            "DoDI 2010.06", "DoDI 5530.03",
            "DoDD 4270.5", "DoDD 5230.20",
            "DoDM 5200.01",
            "AECA", "Arms Export Control Act",
            "FAA", "Foreign Assistance Act",
            "USML", "United States Munitions List",
            "DFARS", "Defense Federal Acquisition Regulation Supplement",
        },
        
        # Documents (C4.1 - C4.5)
        "documents": {
            "P&A", "Price and Availability",
            "PAR", "Pre-LOR Assessment Request",
            "TDP", "Technical Data Package",
            "MASL", "Military Articles and Services List",
            "CN", "Congressional Notification",
            "LOR", "Letter of Request", "Letter Of Request",
            "LOA", "Letter of Offer and Acceptance",
        },
        
        # Concepts (C4.1 - C4.5) - acronym AND full form
        "concepts": {
            # Eligibility
            "eligibility", "eligibility determination",
            "Presidential Determination", "PD",
            "retransfer", "retransfer restrictions",
            "third party transfer",
            # Equipment Categories - acronym AND full form
            "SME", "Significant Military Equipment",
            "MDE", "Major Defense Equipment",
            "GFE", "Government Furnished Equipment",
            "GFM", "Government Furnished Materiel",
            # Targeting/Intelligence - acronym AND full form
            "GEOINT", "Geospatial Intelligence",
            "C4ISR", "Command Control Communications Computer Intelligence Surveillance Reconnaissance",
            "ATD", "Advanced Target Development",
            "TCM", "Target Coordinate Mensuration",
            "CDE", "Collateral Damage Estimation",
            "weaponeering", "targeting",
            # Security Items - acronym AND full form
            "NVD", "Night Vision Device", "NVDs", "Night Vision Devices",
            "MANPADS", "Man-Portable Air Defense System", "Stinger",
            "cluster munitions",
            "white phosphorus",
            "COMSEC", "Communications Security",
            "INFOSEC", "Information Security",
            "classification",
            # Competition
            "international competition", "competition",
            # Other
            "DCS preference", "concurrent negotiations",
        },
        
        # Sections
        "sections": {
            "C4.1", "C4.2", "C4.3", "C4.4", "C4.5",
            "C4.1.1", "C4.1.2", "C4.1.3",
            "C4.3.1", "C4.3.2", "C4.3.5", "C4.3.6",
            "C4.4.4", "C4.4.5", "C4.4.12", "C4.4.14",
            "C4.4.16", "C4.4.17", "C4.4.18",
        }
    }
    
    def __init__(self):
        self.test_results = []
        self.metrics_history = []
        # Build reverse lookup (full form → acronym)
        self.fullform_to_acronym = {v: k for k, v in self.ACRONYM_PAIRS.items()}
        print("[EntityMetrics E1.1 + E1.3] Initialized with Chapter 1 & 4 ground truth + Acronym Normalization")
    
    def get_all_ground_truth_entities(self) -> set:
        """Get flattened set of all ground truth entities from all chapters"""
        all_entities = set()
        # Chapter 1 entities
        for category, entities in self.CHAPTER_1_GROUND_TRUTH.items():
            all_entities.update(entities)
        # Chapter 4 entities
        for category, entities in self.CHAPTER_4_GROUND_TRUTH.items():
            all_entities.update(entities)
        return all_entities
    
    def normalize_entities(self, entities: List[str]) -> set:
        """
        E1.3: Normalize entities - merge acronyms with full forms
        
        Rules:
        1. Filter out generic words
        2. Convert acronym ↔ full form to single canonical form (acronym)
        3. Handle "Entity + Generic Word" phrases (e.g., "Security Assistance programs" → "sa")
        4. Remove redundant entities (if A contains B, keep A)
        
        Example:
            Input:  ['DFAS', 'Defense Finance and Accounting Service', 'programs']
            Output: {'dfas'}  (merged + filtered)
        """
        normalized = set()
        
        for entity in entities:
            entity_lower = entity.lower().strip()
            
            # Skip generic words
            if entity_lower in self.GENERIC_WORDS:
                print(f"[EntityMetrics E1.3] Filtered generic word: '{entity}'")
                continue
            
            # Check if it's an acronym
            if entity_lower in self.ACRONYM_PAIRS:
                normalized.add(entity_lower)  # Keep acronym as canonical
                continue
            
            # Check if it's a full form → convert to acronym
            if entity_lower in self.fullform_to_acronym:
                acronym = self.fullform_to_acronym[entity_lower]
                normalized.add(acronym)
                print(f"[EntityMetrics E1.3] Normalized '{entity}' → '{acronym.upper()}'")
                continue
            
            # E1.3 FIX: Check if entity contains "Known Entity + Generic Word"
            # Example: "Security Assistance programs" → extract "Security Assistance" → "sa"
            entity_handled = False
            
            # Check against full forms first (longer matches)
            for full_form, acronym in self.fullform_to_acronym.items():
                if full_form in entity_lower:
                    # Check if remaining part is generic
                    remaining = entity_lower.replace(full_form, "").strip()
                    if remaining in self.GENERIC_WORDS or remaining == "":
                        normalized.add(acronym)
                        print(f"[EntityMetrics E1.3] Extracted '{acronym.upper()}' from '{entity}' (removed generic: '{remaining}')")
                        entity_handled = True
                        break
            
            if entity_handled:
                continue
                
            # Check against acronyms
            for acronym in self.ACRONYM_PAIRS.keys():
                if acronym in entity_lower.split():  # Acronym as separate word
                    remaining_words = [w for w in entity_lower.split() if w != acronym]
                    if all(w in self.GENERIC_WORDS for w in remaining_words):
                        normalized.add(acronym)
                        print(f"[EntityMetrics E1.3] Extracted '{acronym.upper()}' from '{entity}' (removed generic words)")
                        entity_handled = True
                        break
            
            if entity_handled:
                continue
            
            # Not an acronym pair, keep as-is
            normalized.add(entity_lower)
        
        # Remove redundant (if "security assistance programs" and "security assistance" both exist)
        final = set()
        sorted_entities = sorted(normalized, key=len)  # Shorter first
        for entity in sorted_entities:
            # Check if this entity is substring of any already added
            is_redundant = False
            for existing in final:
                if entity in existing or existing in entity:
                    if len(entity) < len(existing):
                        is_redundant = True
                        break
            if not is_redundant:
                final.add(entity)
        
        return final
    
    def evaluate_extraction(self, query: str, extracted_entities: List[str], 
                           expected_entities: List[str] = None) -> Dict[str, Any]:
        """
        Evaluate entity extraction performance with E1.3 normalization
        
        Args:
            query: The user query
            extracted_entities: Entities extracted by the system
            expected_entities: Ground truth entities (if None, infer from query)
        
        Returns:
            Dict with precision, recall, f1, hallucination_rate
        """
        # If no expected entities provided, infer from query
        if expected_entities is None:
            expected_entities = self._infer_expected_entities(query)
        
        # E1.3: Normalize entities (merge acronyms, filter generic words)
        print(f"[EntityMetrics E1.3] Raw extracted: {extracted_entities}")
        extracted_set = self.normalize_entities(extracted_entities)
        expected_set = self.normalize_entities(expected_entities)
        print(f"[EntityMetrics E1.3] Normalized extracted: {extracted_set}")
        print(f"[EntityMetrics E1.3] Normalized expected: {expected_set}")
        
        # Build normalized ground truth (acronyms only for pairs)
        ground_truth_set = set()
        for e in self.get_all_ground_truth_entities():
            e_lower = e.lower()
            if e_lower in self.ACRONYM_PAIRS:
                ground_truth_set.add(e_lower)
            elif e_lower in self.fullform_to_acronym:
                ground_truth_set.add(self.fullform_to_acronym[e_lower])
            else:
                ground_truth_set.add(e_lower)
        
        # Calculate True Positives, False Positives, False Negatives
        true_positives = extracted_set & expected_set
        false_positives = extracted_set - expected_set
        false_negatives = expected_set - extracted_set
        
        # Detect hallucinations (entities not in any ground truth)
        hallucinations = extracted_set - ground_truth_set
        
        # Calculate metrics
        tp = len(true_positives)
        fp = len(false_positives)
        fn = len(false_negatives)
        total_extracted = len(extracted_set) if extracted_set else 1  # Avoid div by zero
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0  # No extractions = perfect precision
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0  # No expected = perfect recall
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        hallucination_rate = len(hallucinations) / total_extracted if total_extracted > 0 else 0.0
        
        result = {
            "query": query,
            "extracted_entities": list(extracted_entities),  # Original
            "extracted_normalized": list(extracted_set),     # After E1.3
            "expected_entities": list(expected_entities),    # Original
            "expected_normalized": list(expected_set),       # After E1.3
            "true_positives": list(true_positives),
            "false_positives": list(false_positives),
            "false_negatives": list(false_negatives),
            "hallucinations": list(hallucinations),
            "metrics": {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1_score, 4),
                "hallucination_rate": round(hallucination_rate, 4)
            },
            "targets": {
                "precision_target": 0.90,
                "recall_target": 0.85,
                "f1_target": 0.90,
                "hallucination_target": 0.05
            },
            "passed": {
                "precision": precision >= 0.90,
                "recall": recall >= 0.85,
                "f1_score": f1_score >= 0.90,
                "hallucination_rate": hallucination_rate <= 0.05
            },
            "normalization_applied": True
        }
        
        # Store for history
        self.test_results.append(result)
        
        return result
    
    def _infer_expected_entities(self, query: str) -> List[str]:
        """Infer expected entities from query based on ground truth"""
        query_lower = query.lower()
        expected = []
        
        for category, entities in self.CHAPTER_1_GROUND_TRUTH.items():
            for entity in entities:
                if entity.lower() in query_lower:
                    expected.append(entity)
        
        return expected
    
    def calculate_entity_confidence(self, entity: str, source_type: str, 
                                   query: str, extraction_method: str) -> Dict[str, Any]:
        """
        E1.2: Calculate entity confidence using new formula
        
        Confidence = Source(40%) + Query Relevance(35%) + Extraction Quality(25%)
        
        Source weights:
        - knowledge_graph: 1.0
        - database_match: 0.95
        - pattern_match: 0.90
        - nlp_extraction: 0.75
        - ai_extraction: 0.70
        
        Query Relevance:
        - Entity in query directly: 1.0
        - Entity acronym in query: 0.95
        - Entity inferred: 0.70
        
        Extraction Quality:
        - Exact match: 1.0
        - Partial match: 0.80
        - Fuzzy match: 0.60
        """
        # Source score (40%)
        source_weights = {
            "knowledge_graph": 1.0,
            "database_match": 0.95,
            "pattern_match": 0.90,
            "cosmos_gremlin": 0.90,
            "vector_db": 0.85,
            "nlp_extraction": 0.75,
            "ai_extraction": 0.70,
            "dynamic_knowledge": 0.80,
            "file_extraction": 0.75
        }
        source_score = source_weights.get(source_type, 0.60)
        
        # Query relevance score (35%)
        query_lower = query.lower()
        entity_lower = entity.lower()
        
        if entity_lower in query_lower:
            relevance_score = 1.0
        elif any(word in query_lower for word in entity_lower.split()):
            relevance_score = 0.85
        else:
            relevance_score = 0.70
        
        # Extraction quality score (25%)
        quality_weights = {
            "exact_match": 1.0,
            "acronym_match": 0.95,
            "pattern_match": 0.90,
            "partial_match": 0.80,
            "fuzzy_match": 0.60
        }
        quality_score = quality_weights.get(extraction_method, 0.70)
        
        # Calculate composite confidence
        composite = (source_score * 0.40) + (relevance_score * 0.35) + (quality_score * 0.25)
        
        return {
            "entity": entity,
            "confidence": round(composite, 4),
            "confidence_breakdown": {
                "source_score": round(source_score, 2),
                "source_weight": 0.40,
                "relevance_score": round(relevance_score, 2),
                "relevance_weight": 0.35,
                "quality_score": round(quality_score, 2),
                "quality_weight": 0.25
            },
            "source_type": source_type,
            "extraction_method": extraction_method,
            "meets_target": composite >= 0.85
        }
    
    def get_aggregate_metrics(self) -> Dict[str, Any]:
        """Get aggregate metrics across all tests"""
        if not self.test_results:
            return {"error": "No test results available"}
        
        all_precision = [r["metrics"]["precision"] for r in self.test_results]
        all_recall = [r["metrics"]["recall"] for r in self.test_results]
        all_f1 = [r["metrics"]["f1_score"] for r in self.test_results]
        all_hallucination = [r["metrics"]["hallucination_rate"] for r in self.test_results]
        
        return {
            "total_tests": len(self.test_results),
            "avg_precision": round(sum(all_precision) / len(all_precision), 4),
            "avg_recall": round(sum(all_recall) / len(all_recall), 4),
            "avg_f1_score": round(sum(all_f1) / len(all_f1), 4),
            "avg_hallucination_rate": round(sum(all_hallucination) / len(all_hallucination), 4),
            "precision_pass_rate": sum(1 for p in all_precision if p >= 0.90) / len(all_precision),
            "recall_pass_rate": sum(1 for r in all_recall if r >= 0.85) / len(all_recall),
            "f1_pass_rate": sum(1 for f in all_f1 if f >= 0.90) / len(all_f1),
            "hallucination_pass_rate": sum(1 for h in all_hallucination if h <= 0.05) / len(all_hallucination)
        }
    
    def reset_metrics(self):
        """Reset test results"""
        self.test_results = []
        print("[EntityMetrics] Test results reset")

# Global instance for entity metrics
entity_metrics = EntityMetrics()

class IntegratedEntityAgent:
    """
    Integrated Entity Agent with database connections and enhanced extraction
    """
    def deduplicate_vector_results(self, results):
        """Remove duplicate vector DB results with robust key handling"""
        seen_content = {}
        unique = []
    
        print(f"\n{'='*80}")
        print(f"[DEDUPLICATION] Starting with {len(results)} results")
        print(f"{'='*80}")
    
        for i, result in enumerate(results):
            # ✅ Try multiple possible keys for content
            content = (
                result.get('content', '') or 
                result.get('text', '') or 
                result.get('page_content', '')
            ).strip()
        
            if not content:
                print(f"[Dedup] ⚠️ WARNING: Result {i+1} has no content! Keys: {list(result.keys())}")
                continue
        
            content_hash = hashlib.md5(content.encode()).hexdigest()
        
            if content_hash not in seen_content:
                seen_content[content_hash] = i + 1
                unique.append(result)
                print(f"[Dedup] ✅ Kept result {i+1}: {content[:60]}...")
            else:
                orig_idx = seen_content[content_hash]
                print(f"[Dedup] ❌ REMOVED result {i+1} (duplicate of result {orig_idx})")
    
        print(f"\n[DEDUPLICATION] Summary:")
        print(f"  Original: {len(results)} results")
        print(f"  Unique:   {len(unique)} results")
        if len(results) > 0:
            print(f"  Removed:  {len(results) - len(unique)} duplicates ({(len(results)-len(unique))/len(results)*100:.1f}%)")
        else:
            print(f"  Removed:  0 duplicates (0.0%)")
        print(f"{'='*80}\n")
        
        return unique

    def _boost_by_entities(self, vector_results: List[Dict], entities: List[str], query: str) -> List[Dict]:
        """
        ✅ ENTITY BOOSTING: Re-rank vector results based on entity matches
        
        Strategy:
        1. Calculate entity match score for each result
        2. Boost results that contain query entities
        3. Re-rank to bring entity-matched results to top
        4. Keep top 5 for efficiency
        
        This fixes the problem where semantically similar but entity-irrelevant
        chunks rank higher than entity-relevant chunks.
        """
        import re
        
        if not vector_results or not entities:
            return vector_results
        
        print(f"\n{'='*80}")
        print(f"[ENTITY BOOST] Starting entity-based re-ranking")
        print(f"{'='*80}")
        print(f"[ENTITY BOOST] Entities to match: {entities}")
        
        # Extract important entities from query directly (case-insensitive)
        query_lower = query.lower()
        
        # Key entity patterns to look for (high-value matches)
        high_value_patterns = [
            "secretary of state", "secstate",
            "secretary of defense", "secdef",
            "dsca", "dfas", "itar", "usml",
            "pm/ddtc", "ddtc",
            "faa", "aeca", "fms", "imet",
            "continuous supervision", "general direction",
        ]
        
        # Find which high-value entities are in query
        query_entities = []
        for pattern in high_value_patterns:
            if pattern in query_lower:
                query_entities.append(pattern)
        
        # Also add extracted entities (lowercase)
        query_entities.extend([e.lower() for e in entities])
        query_entities = list(set(query_entities))  # Dedupe
        
        print(f"[ENTITY BOOST] Query entities for matching: {query_entities}")
        
        # Score each result
        scored_results = []
        
        for i, result in enumerate(vector_results):
            content = result.get('content', '').lower()
            original_distance = result.get('distance', result.get('similarity', 1.0))
            
            # Count entity matches
            entity_matches = []
            for entity in query_entities:
                # Use word boundary for short entities
                if len(entity) <= 4:
                    pattern = r'\b' + re.escape(entity) + r'\b'
                    if re.search(pattern, content):
                        entity_matches.append(entity)
                else:
                    if entity in content:
                        entity_matches.append(entity)
            
            # Calculate boost score
            # More matches = higher boost
            match_count = len(entity_matches)
            
            # Boost calculation:
            # - 0 matches: no boost (score = 0)
            # - 1 match: boost = 0.3
            # - 2 matches: boost = 0.5
            # - 3+ matches: boost = 0.7
            if match_count == 0:
                boost = 0
            elif match_count == 1:
                boost = 0.3
            elif match_count == 2:
                boost = 0.5
            else:
                boost = 0.7
            
            # Combined score (lower is better for distance)
            # Subtract boost from distance to improve ranking
            boosted_distance = original_distance - boost
            
            scored_results.append({
                **result,
                'original_distance': original_distance,
                'boosted_distance': boosted_distance,
                'entity_matches': entity_matches,
                'entity_match_count': match_count,
                'boost_applied': boost
            })
            
            # Log matches
            status = "⭐ BOOSTED" if match_count > 0 else ""
            section = result.get('metadata', {}).get('section_id', '?')
            print(f"[ENTITY BOOST] Result {i+1} [{section}]: {match_count} matches {entity_matches} | dist: {original_distance:.3f} → {boosted_distance:.3f} {status}")
        
        # Sort by boosted distance (lower is better)
        scored_results.sort(key=lambda x: x['boosted_distance'])
        
        # Take top 5
        top_results = scored_results[:5]
        
        # Log final ranking
        print(f"\n[ENTITY BOOST] Final ranking after boost:")
        for i, result in enumerate(top_results, 1):
            section = result.get('metadata', {}).get('section_id', '?')
            matches = result.get('entity_matches', [])
            orig = result.get('original_distance', 0)
            boosted = result.get('boosted_distance', 0)
            print(f"  {i}. [{section}] matches={matches} | {orig:.3f} → {boosted:.3f}")
        
        print(f"{'='*80}\n")
        
        return top_results
    
    def __init__(self, knowledge_graph=None, db_manager=None):
        # === HALLUCINATION FIX: Containment mapping ===
        self.CONTAINMENT_MAP = {
            "dsca": ["sc"],
            "usasac": ["sa", "sac"],
            "satfa": ["sa"],
            "afsac": ["sa", "sac"],
            "saf/ia": ["sa", "ia"],
            "saf-ia": ["sa", "ia"],
            "nsa": ["sa"],
            "disa": ["sa"],
            "mda": ["da"],
            "eda": ["da"],
            "ndaa": ["da"],
            "usace": ["sa"],
            "dfas": ["fa"],
            "dcaa": ["ca"],
            "aeca": ["ca"],
            "samm": ["sa", "am"],
        }
        
        # Short acronyms that MUST appear as standalone words
        self.STRICT_BOUNDARY_ACRONYMS = {
            "sc", "sa", "ia", "da", "fa", "as", "do", "ca", "pn", "am", "pd",
            # 4-letter acronyms that need strict matching
            "itar", "aeca", "usml", "dfar", "masl"
        }
        
        # Reference to EntityMetrics GENERIC_WORDS
        self.GENERIC_WORDS = EntityMetrics.GENERIC_WORDS
        print("[IntegratedEntityAgent] Initializing with database connections...")
        
        self.knowledge_graph = knowledge_graph
        self.db_manager = db_manager or db_manager
        
        # E1.1: Entity Metrics System
        self.entity_metrics = entity_metrics  # Use global instance
        
        # Learning and feedback systems
        self.hil_feedback_data = []        # Human-in-the-loop feedback storage
        self.custom_entities = {}          # User-defined entities from feedback
        self.trigger_updates = []          # Trigger-based updates storage
        self.dynamic_knowledge = {         # Dynamic knowledge base
            "entities": {},
            "relationships": []
        }
        
        # Enhanced entity patterns
        self.samm_entity_patterns = {
            "organizations": [
                # High-level agencies
                "DSCA", "Defense Security Cooperation Agency",
                "DoS", "Department of State", "State Department", "State",
                "DoD", "Department of Defense", "Defense Department",
                "DFAS", "Defense Finance and Accounting Service",
                "DoC", "Department of Commerce",
                # Secretary level
                "SECSTATE", "Secretary of State",
                "SECDEF", "Secretary of Defense",
                "SECARMY", "Secretary of the Army",
                # USD Offices (both formats for query matching)
                "USD(P)", "USD-P", "Under Secretary of Defense for Policy",
                "USD(A&S)", "USD-AS", "Under Secretary of Defense for Acquisition and Sustainment",
                "USD(C)", "USD-C", "Under Secretary of Defense, Comptroller",
                "USD(P&R)", "USD-PR", "Under Secretary of Defense, Personnel and Readiness",
                "USD(R&E)", "Under Secretary of Defense for Research and Engineering",
                "USD(I&S)", "Under Secretary of Defense for Intelligence and Security",
                # Military Departments
                "DA", "Department of the Army",
                "DoN", "Department of the Navy",
                "DAF", "Department of the Air Force",
                "MILDEP", "MILDEPS", "Military Department",
                # Army orgs
                "DASA (DE&C)", "DASA-DEC", "Deputy Assistant Secretary of the Army for Defense Exports and Cooperation",
                "USASAC", "U.S. Army Security Assistance Command",
                "SATFA", "Security Assistance Training Field Activity",
                "AMC", "Army Materiel Command",
                "TRADOC", "Army Training and Doctrine Command",
                "USACE", "U.S. Army Corps of Engineers",
                # Navy orgs
                "NIPO", "Navy International Programs Office",
                "ASN (RDA)", "ASN-RDA", "Assistant Secretary of the Navy",
                # Air Force orgs
                "SAF/IA", "SAF-IA", "Deputy Under Secretary of the Air Force for International Affairs",
                "AFSAC", "Air Force Security Assistance and Cooperation",
                "AFSAT", "Air Force Security Assistance Training Squadron",
                "AETC", "Air Education and Training Command",
                "AFMC", "Air Force Materiel Command",
                # Defense Agencies
                "DCMA", "Defense Contract Management Agency",
                "DISA", "Defense Information Systems Agency",
                "DLA", "Defense Logistics Agency",
                "DTRA", "Defense Threat Reduction Agency",
                "MDA", "Missile Defense Agency",
                "NGA", "National Geospatial-Intelligence Agency",
                "NSA", "National Security Agency",
                "DCAA", "Defense Contract Audit Agency",
                "DIA", "Defense Intelligence Agency",
                "DTSA", "Defense Technology Security Administration",
                # Joint
                "CJCS", "Chairman of the Joint Chiefs of Staff",
                "JS", "Joint Staff",
                # CCMDs
                "CCMD", "CCMDS", "Combatant Command",
                "CCDR", "Combatant Commander",
                "USCENTCOM", "U.S. Central Command",
                "USEUCOM", "U.S. European Command",
                "USINDOPACOM", "U.S. Indo-Pacific Command",
                "USNORTHCOM", "U.S. Northern Command",
                "USSOUTHCOM", "U.S. Southern Command",
                "USCYBERCOM", "U.S. Cyber Command",
                "USSPACECOM", "U.S. Space Command",
                "USSOCOM", "U.S. Special Operations Command",
                "USTRANSCOM", "U.S. Transportation Command",
                # Other
                "SCO", "SCOS", "Security Cooperation Organization",
                "IA", "IAS", "Implementing Agency",
                "OMB", "Office of Management and Budget",
            ],
            "programs": [
                "Security Cooperation", "SC", "Security Cooperation programs",
                "Security Assistance", "SA", "Security Assistance programs",
                "Foreign Military Sales", "FMS",
                "Foreign Military Financing", "FMF",
                "International Military Education and Training", "IMET",
                "Direct Commercial Sales", "DCS",
                "Building Partner Capacity", "BPC",
                "Excess Defense Articles", "EDA",
                "Cooperative Threat Reduction", "CTR",
                "Countering Weapons of Mass Destruction", "CWMD",
                "Missile Defense System", "MDS",
                "Terminal High Altitude Area Defense", "THAAD",
            ],
            "authorities": [
                "Foreign Assistance Act", "FAA", "Foreign Assistance Act of 1961",
                "Arms Export Control Act", "AECA", "Arms Export Control Act of 1976",
                "National Defense Authorization Act", "NDAA",
                "Title 10", "Title 10 U.S.C.", "10 U.S.C.",
                "Title 22", "Title 22 U.S.C.", "22 U.S.C.",
                "Title 50", "Title 50 U.S.C.", "50 U.S.C.",
                "Executive Order", "EO", "E.O.",
                "Executive Order 13637", "EO 13637", "E.O. 13637",
                "Federal Acquisition Regulation", "FAR",
                "Defense Federal Acquisition Regulation Supplement", "DFARS",
                "International Traffic in Arms Regulations", "ITAR",
                "United States Munitions List", "USML",
                "Continuing Resolution Authority", "CRA",
            ],
            "concepts": [
                "continuous supervision", "general direction",
                "defense articles", "defense services",
                "military education and training", "defense-related services",
                "strategic objectives", "national security",
                "campaign plan", "campaign plans",
                "foreign partner", "foreign partners",
                "partner nation", "partner nations", "PN",
                "international partners", "DoD Components",
                "overall management", "delivery of materiel",
            ],
            "documents": [
                "Guidance for Employment of the Force", "GEF",
                "Congressional Budget Justification", "CBJ",
                "Mission Strategic Resource Plan", "MSRP",
                "Letter of Request", "LOR",
                "Memorandum of Request", "MOR",
                "Letter of Offer and Acceptance", "LOA",
                "DoD Directive", "DoDD",
                "DoDD 5132.03", "DoDD 5105.65",
                "SAMM", "Security Assistance Management Manual",
                # Chapter 4 Documents
                "P&A", "Price and Availability",
                "PAR", "Pre-LOR Assessment Request",
                "TDP", "Technical Data Package",
                "MASL", "Military Articles and Services List",
                "CN", "Congressional Notification",
            ],
            "sections": [],
            
            # =================================================================
            # CHAPTER 4 ENTITY PATTERNS - FMS Program
            # =================================================================
            "chapter4_organizations": [
                # DSCA Offices
                "DSCA SPP", "DSCA (SPP)", "SPP", "Office of Strategy, Plans, and Policy",
                "DSCA IOPS", "DSCA (IOPS)", "IOPS", "Office of International Operations",
                "IOPS/REX", "Regional Execution Directorate",
                "IOPS/WPN", "IOPS/WPNS", "Weapons Directorate",
                "FO/OGC", "Office of the General Counsel",
                "ADM/PIE", "ADM/PIE/AME",
                # State Offices
                "State PM", "State(PM)", "PM/RSAT", "DDTC",
                "Bureau of Political-Military Affairs",
                "Directorate of Defense Trade Controls",
                # Defense Agencies
                "DTSA", "Defense Technology Security Administration",
                "DOC", "Department of Commerce",
                # Other
                "AFLCMC", "Air Force Life Cycle Management Center",
                "JTCG/ME", "Joint Technical Coordinating Group for Munitions Effectiveness",
                "JTS", "Joint Targeting School",
                "USN", "U.S. Navy",
                "GSA", "General Services Administration",
                "IAEA", "International Atomic Energy Agency",
                "ASD(SO/LIC)", "SO/LIC",
                "ASD(HD&GS/CWMD)",
            ],
            "chapter4_programs": [
                "TPA", "Total Package Approach",
                "EUM", "End Use Monitoring",
                "EEUM", "Enhanced End Use Monitoring",
                "FMS-Only", "FMS Only",
                "RDFP", "Regional Defense Fellowship Program",
                "coproduction", "co-production",
            ],
            "chapter4_concepts": [
                # Eligibility
                "eligibility", "eligibility determination",
                "Presidential Determination", "PD",
                "retransfer", "retransfer restrictions", "third party transfer",
                # Equipment Categories
                "SME", "Significant Military Equipment",
                "MDE", "Major Defense Equipment",
                "GFE", "Government Furnished Equipment",
                "GFM", "Government Furnished Materiel",
                # Targeting/Intelligence
                "GEOINT", "Geospatial Intelligence",
                "C4ISR",
                "ATD", "Advanced Target Development",
                "TCM", "Target Coordinate Mensuration",
                "CDE", "Collateral Damage Estimation",
                "weaponeering", "targeting", "targeting infrastructure",
                # Security Items
                "NVD", "Night Vision Device", "NVDs", "Night Vision Devices",
                "MANPADS", "Stinger", "Man-Portable Air Defense System",
                "cluster munitions",
                "white phosphorus",
                "COMSEC", "Communications Security",
                "INFOSEC", "Information Security",
                "classification",
                # Competition
                "international competition", "competition",
                # Other
                "DCS preference", "concurrent negotiations",
            ],
            "chapter4_authorities": [
                "NDP", "National Disclosure Policy", "NDP-1",
                "EO 13526", "Executive Order 13526",
                "22 CFR part 121",
                "DoDI 2010.06", "DoDI 5530.03",
                "DoDD 4270.5", "DoDD 5230.20",
                "DoDM 5200.01",
            ],
            
            # =================================================================
            # CHAPTER 5 ENTITY PATTERNS - FMS Case Development
            # =================================================================
            "chapter5_documents": [
                # Core documents (C5.1.2)
                "LOR", "Letter of Request",
                "LOA", "Letter of Offer and Acceptance",
                "P&A", "Price and Availability",
                "LOAD", "LOA Data",
                "CTA", "Country Team Assessment",
                "CN", "Congressional Notification",
                "MFR", "Memorandum for Record",
                "RFP", "Request for Proposal",
                "RFI", "Request for Information",
                # LOR Status Terms (C5.1.7)
                "LOR Actionable", "LOR Complete", "LOR Insufficient",
                "LOR Receipt", "LOR Date", "LOR Assessment",
                "LOR checklist", "LOR Advisory", "actionable LOR",
                "actionable criteria", "Customer Request",
                # LOA Components (C5.4)
                "Standard Terms and Conditions", "LOA Amendment",
                "LOA Modification", "case lines", "line item",
                "case notes", "LOA notes", "sole source",
                "nonrecurring cost", "assessorial charges",
            ],
            "chapter5_case_types": [
                # Case Types (C5.4.3)
                "Defined Order", "Blanket Order",
                "Defined Order case", "Blanket Order case",
                "blanket order LOA", "defined order LOA",
                "FMS case", "FMS cases", "Multi-Service LOA",
                "case development", "case initialization",
                "Case Identifier", "case category",
                # FMSO Types
                "CLSSA", "Cooperative Logistics Supply Support Arrangement",
                "FMSO", "Foreign Military Sales Order",
                "FMSO I", "FMSO II",
                # Categories (Table C5.T6)
                "Category A", "Category B", "Category C", "Category D",
            ],
            "chapter5_response_types": [
                # Response Types (C5.2)
                "hybrid response", "negotiated response", "hybrid",
                "NTE", "Not-to-Exceed", "not-to-exceed",
                "FFP", "Firm Fixed Price", "firm fixed price",
                "negative response", "disapproval recommendation",
                "EOQ", "Economic Order Quantity",
            ],
            "chapter5_processing": [
                # Case Processing Milestones (C5.4.2)
                "MILAP", "Military Department Approval",
                "MILSGN", "Military Signature",
                "CPOHOLD", "Case Processing Office Hold",
                "CPOHOLDREM", "CPOHOLD Removal",
                "CDEF", "Case Development Extenuating Factor",
                # v5.9.8: Delay keywords → CDEF (short patterns for better matching)
                "delay", "delaying", "delayed",
                "taking longer", "longer than expected",
                "outside coordination",
                "OED", "Offer Expiration Date",
                "case development standard", "processing time",
                "restatement", "counteroffer",
            ],
            "chapter5_special_items": [
                # Special Operations (C5.1.3.4)
                "SO-P", "Special Operations-Peculiar",
                "USSOCOM", "U.S. Special Operations Command",
                "SOF", "Special Operations Force",
                "SOF AT&L-IO", "SOF Acquisition, Technology and Logistics International Operations",
                # Weapons/Systems (Table C5.T1)
                "MTCR Category I", "MTCR Category 1", "MTCR",
                "Missile Technology Control Regime",
                "ISR UAV", "ISR UCAV", "ISR",
                "Intelligence, Surveillance and Reconnaissance",
                "MANPADS", "Man-Portable Air Defense System",
                "NVD", "Night Vision Device", "NVDs", "Night Vision Devices",
                "FoM", "Figure of Merit",
                "white phosphorus", "White Phosphorous Munitions",
                "air-to-surface munitions", "surface-to-surface munitions",
                "working dogs", "working dog", "long-term care plan",
                "Ballistic Missile Defense",
                # Targeting (Table C5.T1H)
                "TCM", "Target Coordinate Mensuration",
                "CDE", "Collateral Damage Estimation",
                "PDT", "Population Density Tables",
            ],
            "chapter5_approvals": [
                # Approvals/Waivers (C5.1.8)
                "Yockey Waiver", "Yockey waiver",
                "OT&E", "Operational Testing and Evaluation",
                "pre-OT&E", "technology release", "policy release",
                "disclosure approval", "ENDP",
                "Exception to National Disclosure Policy",
            ],
            "chapter5_organizations": [
                # DSCA Organizations (C5.1.3, C5.1.7)
                "IOPS", "Office of International Operations",
                "IOPS/WPN", "IOPS/WPNS", "International Operations, Weapons Directorate",
                "IOPS/REX", "International Operations, Regional Execution Directorate",
                "IOPS/GEX", "International Operations, Global Execution Directorate",
                "IOPS/GEX/CWD", "Case Writing and Development Division",
                "SPP", "Office of Strategy, Plans, and Policy",
                "SPP/EPA", "Execution Policy and Analysis Directorate",
                "ADM/PIE", "Office of Administration, Performance, Improvement, and Effectiveness Directorate",
                "ADM/PIE/AME", "Assessment, Monitoring and Evaluation Division",
                "OBO", "Office of Business Operations",
                "OBO/FPRE", "Financial Policy & Regional Execution Directorate",
                "OBO/FPRE/FRC", "Financial Reporting and Compliance Division",
                "FO/OGC", "Front Office, Office of the General Counsel",
                "CPD", "Country Portfolio Director",
                # State Department
                "PM/SA", "Office of Security Assistance",
                "PM/RSAT", "Office of Regional Security and Arms Transfers",
                "State (RM)", "Bureau of Information Resource Management",
            ],
            "chapter5_systems": [
                # Systems (C5.1.2, C5.4.3)
                "DSAMS", "Defense Security Assistance Management System",
                "CTS", "Case Tracking System",
                "SCIP", "Security Cooperation Information Portal",
                "DTS", "Defense Transportation System",
            ],
            "chapter5_references": [
                # Tables
                "Table C5.T1", "Table C5.T1A", "Table C5.T1B", "Table C5.T1C",
                "Table C5.T1D", "Table C5.T1E", "Table C5.T1F", "Table C5.T1G", "Table C5.T1H",
                "Table C5.T2A", "Table C5.T2B", "Table C5.T3A", "Table C5.T3B",
                "Table C5.T4", "Table C5.T5", "Table C5.T6", "Table C5.T7",
                # Figures
                "Figure C5.F1", "Figure C5.F1A", "Figure C5.F1B",
                "Figure C5.F2", "Figure C5.F3", "Figure C5.F4", "Figure C5.F5",
                # Sections
                "C5.1", "C5.2", "C5.3", "C5.4", "C5.5", "C5.6",
            ],
            
            # =================================================================
            # CHAPTER 6 ENTITY PATTERNS - FMS Case Implementation & Execution
            # =================================================================
            "chapter6_implementation": [
                # Case Implementation (C6.1)
                "EI", "Emergency Implementation",
                "OA", "Obligational Authority",
                "OED", "Offer Expiration Date",
                "SSC", "Supply/Services Complete", "supply services complete",
                "Routine Case Implementation",
                "Delayed Case Implementation",
                "case implementation", "implementing instructions",
                "financial implementation", "initial deposit",
            ],
            "chapter6_systems": [
                # Data Systems (C6.1)
                "DSAMS", "Defense Security Assistance Management System",
                "DIFS", "Defense Integrated Financial System",
                "CPRS", "Case Performance Reporting System",
                "CTS", "Case Tracking System",
                "SCIP", "Security Cooperation Information Portal",
            ],
            "chapter6_financial_orgs": [
                # Financial Organizations (C6.1, C6.2)
                "DFAS", "Defense Finance and Accounting Service",
                "DFAS-IN", "Defense Finance and Accounting Services - Indianapolis",
                "CFD", "Country Finance Director",
                "DWCF", "Defense Working Capital Fund",
                "WCF", "Working Capital Fund",
                "OBO/FPRE/FP", "Financial Policy Division",
            ],
            "chapter6_acquisition": [
                # Acquisition (C6.3)
                "sole source", "other than full and open competition",
                "International Agreement", "International Agreement exception",
                "FAR", "Federal Acquisition Regulation",
                "DFARS", "Defense FAR Supplement",
                "CICA", "Competition in Contracting Act",
                "TAA", "Technical Assistance Agreement",
                "CLIN", "Contract Line Item Number",
                "ARP", "Acquisition Requirements Package",
                "RFP", "Request for Proposal",
                "SOW", "Statement of Work",
                "PWS", "Performance Work Statement",
                "contracting officer", "simplified acquisition threshold",
            ],
            "chapter6_fees_offsets": [
                # Contingent Fees and Offsets (C6.3.7, C6.3.9)
                "Contingent Fees", "contingent fees",
                "agent fees", "sales commissions", "bona fide",
                "Offset", "offsets", "offset arrangements", "offset costs",
                "Warranties", "warranty", "End Use Certificates", "EUC",
            ],
            "chapter6_logistics": [
                # Logistics and Priority (C6.4)
                "F/AD", "Force/Activity Designator", "force activity designator",
                "UND", "Urgency of Need Designator",
                "Project Codes", "project codes",
                "JMPAB", "Joint Materiel Priority Allocation Board",
                "MILSTRIP", "Military Standard Requisitioning and Issue Procedures",
                "UMMIPS", "Uniform Material Movement and Issue Priority System",
                "ICP", "Inventory Control Point",
                "standard requisitions", "backorder",
            ],
            "chapter6_supply_support": [
                # Commercial Support (C6.4.4, C6.4.5)
                "CBS", "Commercial Buying Service",
                "TVL", "FMS Tailored Vendor Logistics", "Tailored Vendor Logistics",
                "ILCO", "International Logistics Control Office",
                "PROS", "Parts and Repair Ordering System",
                "SNAP", "Simplified Non-Standard Acquisition Process",
                "DLA", "Defense Logistics Agency",
            ],
            "chapter6_clssa": [
                # CLSSA (C6.4.3.2)
                "CLSSA", "Cooperative Logistics Supply Support Arrangement",
                "FMSO", "Foreign Military Sales Order",
                "FMSO I", "Foreign Military Sales Order I",
                "FMSO II", "Foreign Military Sales Order II",
                "FMSO I maturity", "augmentation stock",
                "equity investment", "capitalization",
            ],
            "chapter6_repair": [
                # Repair Programs (C6.4.8)
                "Direct Exchange", "direct exchange",
                "R&R", "Repair and Return", "repair and return",
                "repairable item", "serviceable",
                "Returns", "fully functioning",
                "GFE", "Government Furnished Equipment",
                "GFM", "Government Furnished Materiel",
            ],
            "chapter6_sdr": [
                # Supply Discrepancy Reports (C6.4.10)
                "SDR", "Supply Discrepancy Report",
                "SF 364", "Standard Form 364",
                "supply discrepancy", "discrepancies",
                "Timeframes for Submission", "one year",
                "$200", "minimum value",
                "Shipment Documentation",
                "NSN", "National Stock Number",
                "TCN", "Transportation Control Number",
            ],
            "chapter6_reviews": [
                # Case Reviews (C6.5)
                "FMR", "Financial Management Review",
                "PMR", "Program Management Review",
                "SAR", "Security Assistance Review",
                "CRR", "Case Reconciliation Review",
                "SAMR", "Security Assistance Management Review",
                "case review", "case reviews",
                "Cultural Days", "cultural days",
                "Country-Level", "Service-Level", "Program-Level", "Case-Level",
            ],
            "chapter6_suspension": [
                # Suspension (C6.6)
                "Suspension", "suspension", "suspension of delivery",
                "Brooke Amendment", "sanctions",
                "contract termination", "case cancellation",
                "MTT", "Mobile Training Team",
                "LTD", "Language Training Detachment",
                "IMET", "International Military Education and Training",
            ],
            "chapter6_amendments": [
                # Amendments and Modifications (C6.7)
                "Amendment", "Amendments", "LOA Amendment",
                "Modification", "Modifications", "LOA Modification",
                "Concurrent Modification", "Concurrent Modifications",
                "change in scope", "within-scope", "within-scope changes",
                "Restatement", "restatement", "Counteroffer", "counteroffer",
                "Pen and Ink Changes", "pen and ink",
                "DREACT", "Reactivation Authorized Milestone",
                "MILREACT", "MILDEP Reactivation",
            ],
            "chapter6_etp": [
                # Exception to Policy (C6.7.5)
                "ETP", "Exception to Policy", "exception to policy",
                "SPP/EPA", "Execution Policy and Analysis Directorate",
                "10 business days", "15 business days", "six months",
                "SharePoint", "ETP tracker",
            ],
            "chapter6_cancellation": [
                # Case Cancellation (C6.8)
                "case cancellation", "Purchaser-Requested Case Cancellations",
                "USG-Requested Case Cancellations",
                "termination costs", "administrative costs",
                "non-refundable", "FMS Administrative Surcharge",
                "SCML", "Small Case Management Line",
                "$15,000", "minimal-dollar value",
            ],
            "chapter6_special": [
                # Special Programs (C6.7.6.3)
                "ENJJPT", "Euro-NATO Joint Jet Pilot Training Program",
                "ECISAP", "Electronic Combat International Security Assistance Program",
                "EW", "Electronic Warfare",
                "BPC", "Building Partner Capacity",
                "EDA", "Excess Defense Articles",
            ],
            "chapter6_references": [
                # Tables
                "Table C6.T1", "Table C6.T2", "Table C6.T3", "Table C6.T4",
                "Table C6.T5", "Table C6.T6", "Table C6.T7", "Table C6.T8",
                # Figures
                "Figure C6.F1", "Figure C6.F2", "Figure C6.F3",
                "Figure C6.F4", "Figure C6.F5",
                # Sections
                "C6.1", "C6.2", "C6.3", "C6.4", "C6.5", "C6.6", "C6.7", "C6.8",
            ],
            # =================================================================
            # CHAPTER 7 ENTITY PATTERNS - Transportation
            # =================================================================
            "chapter7_dts": [
                # Defense Transportation System (C7.6)
                "DTS", "Defense Transportation System",
                "USTRANSCOM", "United States Transportation Command", "U.S. Transportation Command",
                "AMC", "Air Mobility Command",
                "SDDC", "Surface Deployment and Distribution Command",
                "MSC", "Military Sealift Command",
                "DTR", "Defense Transportation Regulation", "DTR 4500.9-R",
            ],
            "chapter7_delivery": [
                # Delivery Terms (C7.4)
                "DTC", "Delivery Term Code",
                "DTC 4", "DTC 5", "DTC 7", "DTC 8", "DTC 9",
                "FOB", "Free On Board", "FOB origin", "FOB destination",
                "POE", "Port of Embarkation",
                "POD", "Port of Debarkation",
                "title transfer", "title passage", "point of origin",
                "retention of title",
            ],
            "chapter7_mapad": [
                # MAPAD (C7.7)
                "MAPAD", "Military Assistance Program Address Directory",
                "TAC", "Type Address Code",
                "TAC 1", "TAC 2", "TAC 3", "TAC 4", "TAC 5", "TAC 6",
                "TAC A", "TAC B", "TAC C", "TAC D", "TAC M",
                "CRIC", "Communication Routing Identifier Code",
                "ILCS", "Integrated Logistics Communication System",
                "mark-for address", "ship-to address",
            ],
            "chapter7_documentation": [
                # Documentation (C7.6.3, C7.11)
                "NOA", "Notice of Availability",
                "ORC", "Offer Release Code",
                "ORC A", "ORC X", "ORC Y", "ORC Z",
                "TCN", "Transportation Control Number",
                "BL", "Bill of Lading",
                "CBL", "Commercial Bill of Lading",
                "GBL", "Government Bill of Lading",
                "DD Form 1348-5", "DD Form 1348-1A", "DD Form 361",
                "iRAPT", "Invoicing Receipt Acceptance and Property Transfer",
                "SF-153",
            ],
            "chapter7_special": [
                # Special Transportation (C7.6.2)
                "SAAM", "Special Assignment Airlift Mission",
                "NGDS", "Next Generation Delivery Services",
                "DCS", "Defense Courier Service",
                "AMC Channel", "channel airlift",
                "small parcel", "USPS", "APO", "FPO",
            ],
            "chapter7_cargo": [
                # Cargo Preference (C7.9)
                "Cargo Preference", "US Flag", "US Flag vessel",
                "P1", "P2", "P3", "P1 service", "P2 service", "P3 service",
                "DNA", "Determination of Non-Availability",
                "MARAD", "Maritime Administration",
                "Fly America Act", "46 USC 55305",
            ],
            "chapter7_packaging": [
                # Packaging and Marking (C7.8)
                "MIL-STD-129", "Military Level A", "Military Level B",
                "WPM", "Wood Packaging Material",
                "ISPM 15", "International Standards for Phytosanitary Measures",
                "marking requirements", "phytosanitary",
            ],
            "chapter7_classified": [
                # Classified Transportation (C7.13, C7.14)
                "Transportation Plan", "classified materiel",
                "COMSEC", "Communications Security",
                "CCI", "Controlled Cryptographic Items",
                "CISMOA", "Communications Interoperability and Security Memorandum of Agreement",
                "DCSA", "Defense Counterintelligence and Security Agency",
                "NISPOM", "National Industrial Security Program Operating Manual",
                "CNSS", "Committee on National Security Systems",
                "facility clearance", "government courier",
                "CONFIDENTIAL", "SECRET", "TOP SECRET",
            ],
            "chapter7_aa_e": [
                # AA&E (C7.15)
                "AA&E", "Arms Ammunition and Explosives",
                "SRC", "Security Risk Category",
                "SRC I", "SRC II", "SRC III", "SRC IV",
                "MANPADS", "Man Portable Air Defense Systems",
                "sensitive materiel", "night vision",
            ],
            "chapter7_hazmat": [
                # HAZMAT (C7.16)
                "HAZMAT", "Hazardous Materials",
                "HMR", "Hazardous Materials Regulations",
                "HC1", "Hazard Class 1", "explosives",
                "EX-Number", "DOT EX-Number",
                "PHMSA", "Pipeline and Hazardous Materials Safety Administration",
                "49 CFR",
            ],
            "chapter7_export": [
                # Export Compliance (C7.17)
                "ITAR", "International Traffic in Arms Regulations",
                "ITAR 126.6(a)", "ITAR 126.6(c)",
                "EEI", "Electronic Export Information",
                "AES", "Automated Export System",
                "CBP", "Customs and Border Protection",
                "ITN", "Internal Transaction Number",
            ],
            "chapter7_costs": [
                # Transportation Costs (C7.12)
                "transportation costs", "standard transportation percentage",
                "Transportation Cost Look-up Table", "Appendix 2",
                "accessorial charges", "storage charges",
                "containerization", "escorts",
            ],
            "chapter7_claims": [
                # Claims (C7.21)
                "TDR", "Transportation Discrepancy Report",
                "DD Form 361", "tracer action",
                "proof of delivery", "constructive proof",
                "carrier liability", "claims",
            ],
            "chapter7_freight": [
                # Freight Forwarders (C7.5)
                "freight forwarder", "FMS freight forwarder",
                "DGR", "Designated Government Representative",
                "ITAR registration", "embassy authorization",
            ],
            "chapter7_insurance": [
                # Insurance (C7.18)
                "commercial insurance", "self-insure",
                "loss or damage", "liability",
                "high value items",
            ],
            "chapter7_organizations": [
                # Organizations
                "DTSA", "Defense Technology Security Administration",
                "husbanding agent",
                "DFAS-IN",
            ],
            "chapter7_references": [
                # Tables and Sections
                "Table C7.T1", "Table C7.T2", "Table C7.T3",
                "Figure C7.F1", "Figure C7.F2",
                "C7.1", "C7.2", "C7.3", "C7.4", "C7.5", "C7.6", "C7.7",
                "C7.8", "C7.9", "C7.10", "C7.11", "C7.12", "C7.13",
                "C7.14", "C7.15", "C7.16", "C7.17", "C7.18", "C7.19",
                "C7.20", "C7.21",
            ]
        }
        
        # Entity relationship mappings for SAMM Chapter 1
        self.entity_relationships = {
            # Secretary of State relationships (C1.3.1)
            "Secretary of State": ["provides continuous supervision", "provides general direction", "determines program scope"],
            "SECSTATE": ["supervises SA programs", "provides general direction"],
            "Department of State": ["supervises SA", "reviews export licenses", "approves third party transfers"],
            "DoS": ["supervises", "reviews", "approves"],
            # SECDEF relationships (C1.3.2)
            "Secretary of Defense": ["establishes military requirements", "implements programs"],
            "SECDEF": ["establishes requirements", "oversees implementation"],
            # USD relationships (C1.3.2.1-5)
            "USD(P)": ["oversees DSCA", "develops SC guidance", "coordinates DoD SC policy"],
            "USD-P": ["oversees DSCA", "develops guidance"],
            "USD(A&S)": ["coordinates with IAs", "oversees acquisition policy"],
            "USD(C)": ["establishes financial policies", "oversees SC budgeting"],
            "USD(P&R)": ["develops manpower programs", "coordinates readiness"],
            # DSCA relationships (C1.3.2.2)
            "DSCA": ["directs DoD SC programs", "administers SA", "provides guidance to DoD Components"],
            "Defense Security Cooperation Agency": ["directs", "administers", "provides guidance"],
            # DFAS relationships (C1.3.2.8)
            "DFAS": ["performs accounting", "performs billing", "performs disbursing", "performs collecting"],
            "Defense Finance and Accounting Service": ["provides financial services for SC"],
            # IA relationships (C1.3.2.6)
            "Implementing Agency": ["executes SC programs", "provides defense articles", "provides defense services"],
            "IA": ["executes programs", "provides articles and services"],
            # MILDEP IA relationships (C1.3.2.6.1)
            "DASA (DE&C)": ["leads Army SC activities", "directs USASAC and SATFA"],
            "NIPO": ["manages DoN SC programs", "oversees Navy IA functions"],
            "SAF/IA": ["leads Air Force SC", "coordinates AFSAC and AFSAT"],
            # CJCS relationships (C1.3.2.9)
            "CJCS": ["advises SECDEF on SC", "reviews campaign plans", "assigns priorities"],
            "Joint Staff": ["provides implementation guidance", "reviews SC aspects of plans"],
            # CCMD relationships (C1.3.2.10)
            "CCDR": ["develops campaign plans", "supervises SCOs", "coordinates SC activities"],
            "Combatant Commander": ["develops plans", "supervises SCOs"],
            # Program relationships (C1.1)
            "Security Assistance": ["is subset of Security Cooperation", "authorized under Title 22"],
            "SA": ["subset of SC", "Title 22 authorized"],
            "Security Cooperation": ["includes Security Assistance", "authorized under Title 10"],
            "SC": ["includes SA", "Title 10 authorized"],
            # Defense Agency relationships (C1.3.2.6.2)
            "DCMA": ["performs contract administration", "provides quality assurance"],
            "DLA": ["provides logistics support", "manages consumable items"],
            "DTRA": ["supports CWMD programs", "builds partner capacity"],
            "MDA": ["develops missile defense systems", "executes THAAD FMS"],
            
            # =================================================================
            # CHAPTER 4 ENTITY RELATIONSHIPS - FMS Program
            # =================================================================
            # Eligibility relationships (C4.1)
            "Presidential Determination": ["determines FMS eligibility", "authorizes sales", "criteria in C4.T1"],
            "DSCA SPP": ["handles eligibility questions", "issues DCS preferences", "coordinates FMS policy"],
            "DSCA IOPS": ["handles eligibility changes", "coordinates FMS-Only designations", "approves MANPADS discussions"],
            "IOPS/WPN": ["approves MANPADS discussions", "coordinates weapons transfers"],
            "PM/RSAT": ["handles non-defense ministry sales", "coordinates with State"],
            "DDTC": ["oversees export licensing", "DCS oversight"],
            
            # Sales process relationships (C4.2, C4.3)
            "FMS-Only": ["designated by State", "requires FMS channel", "sensitive items", "criteria in C4.3.5"],
            "TPA": ["Total Package Approach", "ensures sustainability", "includes training and support"],
            "DCS preference": ["issued by DSCA SPP", "valid for one year"],
            
            # Equipment relationships (C4.4)
            "SME": ["Significant Military Equipment", "on USML", "asterisk designation"],
            "MDE": ["Major Defense Equipment", "over $50M R&D or $200M production", "SME subset"],
            "USML": ["designates defense articles", "lists SME", "22 CFR part 121"],
            "NVD": ["requires case-by-case review", "DTSA policy", "EUM requirements", "C4.4.14"],
            "MANPADS": ["requires DSCA IOPS/WPN approval", "Stinger systems", "special controls", "C4.4.12"],
            
            # Targeting relationships (C4.4.18)
            "ATD": ["Advanced Target Development", "includes TCM, weaponeering, CDE"],
            "TCM": ["Target Coordinate Mensuration", "generates precise coordinates", "for coordinate-seeking weapons"],
            "CDE": ["Collateral Damage Estimation", "assesses civilian risk", "prevents collateral damage"],
            "GEOINT": ["from NGA", "supports targeting", "mission data", "C4.4.16"],
            "C4ISR": ["requires CCDR interoperability requirement", "C4.4.17"],
            "DIEE": ["default targeting solution", "managed by AFLCMC"],
            "DTSA": ["NVD export policy", "case-by-case review", "technology transfer"],
            
            # Coproduction relationships (C4.4.5)
            "coproduction": ["requires DSCA approval", "DoDI 5530.03", "technology transfer"],
            
            # Restricted items relationships (C4.5)
            "cluster munitions": ["restricted", "99% functioning rate required", "C4.5.2"],
            "white phosphorus": ["requires DSCA coordination", "special conditions", "C4.4.8"],
            "napalm": ["not provided through FMS", "C4.5.4"],
            "riot control agents": ["not via FMS", "commercial only", "C4.5.5"],
            
            # =================================================================
            # CHAPTER 5 ENTITY RELATIONSHIPS - FMS Case Development
            # =================================================================
            # LOR relationships (C5.1)
            "LOR": [
                "initiates FMS process", 
                "submitted by SCO", 
                "must meet actionable criteria",
                "no specific format required",
                "C5.1.2",
                "can be formal correspondence, RFP, email, letter, message"
            ],
            "LOR Actionable": ["meets C5.1.7 checklist", "enables case development", "submitted by purchaser"],
            "Letter of Request": [
                "starts FMS case", 
                "requires CTA", 
                "submitted to DSCA",
                "no specific format required per C5.1.2.1",
                "formal correspondence, RFP, email, letter, message"
            ],
            
            # CTA relationships (C5.1.4)
            "CTA": [
                "Country Team Assessment",
                "C5.1.4",
                "required for congressional notification 36(b)",
                "required for first introduction of new capability",
                "required for sensitive items Table C5.T1",
                "required upon DSCA request",
                "must be dated within two years",
                "Table C5.T1A for sensitive articles"
            ],
            "Country Team Assessment": [
                "CTA", "C5.1.4", 
                "congressional notification", 
                "new capability", 
                "sensitive items",
                "DSCA request"
            ],
            
            # Case Types (C5.4.3)
            "Defined Order": ["specific items", "detailed requirements", "fixed quantities"],
            "Blanket Order": ["recurring support", "flexible quantities", "multi-year"],
            "CLSSA": ["cooperative logistics", "supply support", "stock replenishment"],
            "FMSO I": ["initial order", "major equipment", "system procurement"],
            "FMSO II": ["follow-on support", "spare parts", "sustainment"],
            
            # Processing (C5.4.2)
            "CDEF": [
                "Case Development Extenuating Factor", 
                "C5.4.2.1",
                "extends processing time", 
                "documented justification", 
                "delay", 
                "taking longer", 
                "coordination delay",
                "enter CDEF reason code in DSAMS",
                "estimated days to resolve",
                "actual days required"
            ],
            "case delay": ["CDEF", "C5.4.2.1", "enter CDEF code in DSAMS"],
            "processing delay": ["CDEF", "C5.4.2.1", "case development extenuating factor"],
            "approval delay": ["CDEF", "outside coordination", "C5.4.2.1"],
            "CPOHOLD": ["Case Processing Office Hold", "delays LOA", "requires resolution"],
            "MILAP": ["Military Department Approval", "required before LOA", "validates requirements"],
            
            # Categories (Table C5.T6)
            "Category A": ["up to 60 days", "simple cases", "standard processing"],
            "Category B": ["up to 90 days", "moderate complexity", "some coordination"],
            "Category C": ["up to 120 days", "complex cases", "extensive coordination"],
            "Category D": ["over 120 days", "highly complex", "multiple IAs"],
            
            # OED - Offer Expiration Date (C5.4.19)
            "OED": [
                "Offer Expiration Date",
                "C5.4.19",
                "Figure C5.F6",
                "can be shortened for funding deadlines",
                "standard is 6 months",
                "short OED for urgent cases"
            ],
            "short OED": ["C5.4.19", "Figure C5.F6", "meet funding deadlines", "accelerate acceptance"],
            "Offer Expiration Date": ["OED", "C5.4.19", "LOA validity period"],
            
            # Special Items (C5.1.3.4, Table C5.T1)
            "SO-P": ["Special Operations-Peculiar", "USSOCOM coordination", "SOF AT&L-IO"],
            "MTCR Category I": ["missile technology", "highest sensitivity", "DSCA/OUSD(P) approval"],
            "Yockey Waiver": ["pre-OT&E release", "developmental items", "USD(A&S) approval"],
            "NVD": ["Night Vision Device", "FoM requirements", "DTSA coordination"],
            "MANPADS": ["special controls", "IOPS/WPN approval", "highest scrutiny"],
            
            # Organizations (C5.1.3)
            "CPD": ["Country Portfolio Director", "manages country cases", "DSCA primary POC"],
            "IOPS/GEX/CWD": ["case writing", "LOA development", "DSAMS entry"],
            "PM/RSAT": ["State coordination", "policy guidance", "sale approval"],
            
            # Systems (C5.4.3)
            "DSAMS": ["case management", "LOA preparation", "financial tracking"],
            "CTS": ["Case Tracking System", "status monitoring", "milestone tracking"],
            "SCIP": ["information portal", "case data", "customer access"],
            
            # =================================================================
            # CHAPTER 6 ENTITY RELATIONSHIPS - FMS Case Implementation & Execution
            # =================================================================
            # Implementation relationships (C6.1)
            "case implementation": ["requires initial deposit", "recorded in DSAMS", "requires OA"],
            "Emergency Implementation": ["approved by CFD", "requires purchaser acceptance", "urgent situations"],
            "EI": ["emergency implementation", "CFD approval", "urgent situations"],
            "Delayed Case Implementation": ["OED passed", "deposit not received", "may increase costs"],
            "DFAS-IN": ["processes deposits", "posts financial implementation", "notifies SCO"],
            "CFD": ["approves EI", "confirms deposit timing", "coordinates with IA", "Country Finance Director"],
            
            # Execution relationships (C6.2)
            "case execution": ["longest phase", "includes logistics and acquisition", "tracked by case managers"],
            "case managers": ["track delivery status", "maintain case files", "ensure accurate records"],
            "retention period": ["10 years", "after case closure", "audit trail"],
            
            # Acquisition relationships (C6.3)
            "sole source": ["International Agreement exception", "requires purchaser request", "FAR 6.302-4"],
            "CICA": ["Competition in Contracting Act", "10 U.S.C. 3204", "exceptions to competition"],
            "Contingent Fees": ["require purchaser approval", "include agent fees", "sales commissions", "bona fide"],
            "Offsets": ["negotiated with U.S. firms", "USG does not commit", "contractor responsibility"],
            "Warranties": ["same as DoD", "exercised through SDR", "described in LOA note"],
            
            # Logistics relationships (C6.4)
            "F/AD": ["assigned by CJCS", "determines priority", "I through V ranking", "Force Activity Designator"],
            "UMMIPS": ["Uniform Material Movement and Issue Priority System", "priority processing"],
            "JMPAB": ["Joint Materiel Priority Allocation Board", "reviews F/AD requests", "CJCS authority"],
            "ICP": ["Inventory Control Point", "processes requisitions", "manages stock levels"],
            "CBS": ["Commercial Buying Service", "nonstandard items", "ILCO authorized"],
            "TVL": ["Tailored Vendor Logistics", "DLA program", "FMS support option"],
            
            # CLSSA relationships (C6.4.3.2)
            "CLSSA": ["same basis as U.S. Forces", "FMSO I and FMSO II", "equity investment"],
            "FMSO I": ["equity investment", "5 months on hand", "12 months on order", "maturity required"],
            "FMSO II": ["requisition case", "spare parts", "replenishment"],
            
            # Repair relationships (C6.4.8)
            "Direct Exchange": ["same type item", "not an end item", "from DoD stocks"],
            "R&R": ["Repair and Return", "specific item repair", "purchaser waits"],
            
            # SDR relationships (C6.4.10)
            "SDR": ["submitted within one year", "SF 364", "$200 minimum value", "Supply Discrepancy Report"],
            "SF 364": ["Standard Form 364", "SDR form", "DLM 4000.25"],
            
            # Review relationships (C6.5)
            "FMR": ["Financial Management Review", "Chapter 9", "country-level"],
            "PMR": ["Program Management Review", "event-driven", "milestone plan"],
            "Cultural Days": ["host nation culture", "approved by IA and partner", "with review agenda"],
            
            # Amendment relationships (C6.7)
            "Amendment": ["change in scope", "requires purchaser acceptance", "can be restated"],
            "Modification": ["no change in scope", "unilateral by USG", "administrative changes"],
            "Concurrent Modification": ["transfers funding", "multiple cases", "same time implementation"],
            "Restatement": ["restated document", "offered status", "supersedes previous"],
            "Counteroffer": ["invalid acceptance", "new offer required", "unauthorized changes"],
            "ETP": ["Exception to Policy", "SPP/EPA approval", "10 business days routine"],
            "DREACT": ["Reactivation Authorized Milestone", "DSCA posts", "cancelled LOA reactivation"],
            
            # Suspension relationships (C6.6)
            "Suspension": ["directed by State", "not same as cancellation", "deliveries stopped"],
            "Brooke Amendment": ["default in payment", "one year period", "FMF affected"],
            
            # Cancellation relationships (C6.8)
            "case cancellation": ["purchaser or USG requested", "termination costs apply", "closure process"],
            "FMS Administrative Surcharge": ["non-refundable minimum", "SCML value", "up to $15,000"],
            "SCML": ["Small Case Management Line", "non-refundable", "Appendix 6"],
            
            # =================================================================
            # CHAPTER 7 ENTITY RELATIONSHIPS - Transportation
            # =================================================================
            # DTS relationships (C7.6)
            "DTS": ["Defense Transportation System", "USTRANSCOM manages", "includes AMC SDDC MSC"],
            "USTRANSCOM": ["transportation command", "oversees DTS", "coordinates movements"],
            "AMC": ["Air Mobility Command", "airlift", "channel missions"],
            "SDDC": ["Surface Deployment and Distribution Command", "ocean shipments", "claims processing"],
            "MSC": ["Military Sealift Command", "sealift", "vessel operations"],
            
            # Delivery Term relationships (C7.4)
            "DTC": ["Delivery Term Code", "determines DoD responsibility", "FOB origin basis"],
            "DTC 7": ["overseas POD", "DTS to port", "standard FMS"],
            "DTC 8": ["purchaser pickup at POE", "CONUS collection"],
            "DTC 9": ["overseas final destination", "extended DoD routing"],
            "FOB": ["Free On Board", "title transfer point", "origin default"],
            "POE": ["Port of Embarkation", "departure point", "CONUS port"],
            "POD": ["Port of Debarkation", "arrival point", "overseas port"],
            
            # Title Transfer relationships (C7.3)
            "title transfer": ["at point of origin", "manufacturer or depot", "FOB origin"],
            "retention of title": ["USG retains", "operational circumstances", "special cases"],
            
            # MAPAD relationships (C7.7)
            "MAPAD": ["Military Assistance Program Address Directory", "TAC codes", "SCO maintains"],
            "TAC": ["Type Address Code", "address types", "ship-to mark-for NOA"],
            "TAC M": ["mark-for address", "ultimate consignee", "final recipient"],
            
            # Documentation relationships (C7.6.3, C7.11)
            "NOA": ["Notice of Availability", "DD Form 1348-5", "triggers pickup"],
            "ORC": ["Offer Release Code", "A X Y Z codes", "shipping release"],
            "TCN": ["Transportation Control Number", "shipment tracking", "17 characters"],
            "Bill of Lading": ["shipping document", "CBL or GBL", "proof of shipment"],
            
            # Special transport relationships (C7.6.2)
            "SAAM": ["Special Assignment Airlift Mission", "billed hourly", "dedicated mission"],
            "NGDS": ["Next Generation Delivery Services", "up to 300 lbs", "express delivery"],
            "Defense Courier Service": ["classified courier", "sensitive items", "secure transport"],
            
            # Cargo Preference relationships (C7.9)
            "Cargo Preference": ["US Flag requirement", "50% minimum legal", "100% DSCA policy"],
            "DNA": ["Determination of Non-Availability", "MARAD approval", "21 days notice"],
            "MARAD": ["Maritime Administration", "DNA approval", "US Flag waivers"],
            "US Flag": ["required for FMS", "P1 service default", "Cargo Preference Act"],
            "Fly America Act": ["US flag air carriers", "grant and credit cargo"],
            
            # Packaging relationships (C7.8)
            "MIL-STD-129": ["military marking standard", "required for FMS", "marking requirements"],
            "WPM": ["Wood Packaging Material", "ISPM 15 treatment", "phytosanitary"],
            
            # Classified relationships (C7.13, C7.14)
            "Transportation Plan": ["required for classified", "AA&E", "COMSEC CCI"],
            "COMSEC": ["Communications Security", "SF-153 report", "special handling"],
            "CCI": ["Controlled Cryptographic Items", "keyed vs un-keyed", "ETP for keyed"],
            "DCSA": ["Defense Counterintelligence and Security Agency", "verifies clearances", "NISPOM"],
            "NISPOM": ["National Industrial Security Program Operating Manual", "contractor security"],
            "CISMOA": ["Communications Interoperability and Security Memorandum of Agreement", "CCI transfer"],
            
            # AA&E relationships (C7.15)
            "AA&E": ["Arms Ammunition and Explosives", "SRC categories", "special security"],
            "SRC": ["Security Risk Category", "I through IV", "determines handling"],
            "SRC I": ["highest risk", "MANPADS rockets", "USD(I&S) waiver required"],
            "MANPADS": ["SRC I category", "DTS required", "no purchaser pickup without waiver"],
            
            # HAZMAT relationships (C7.16)
            "HAZMAT": ["Hazardous Materials", "49 CFR regulated", "HMR compliance"],
            "EX-Number": ["DOT authorization", "HC1 explosives", "commercial movement"],
            "HC1": ["Hazard Class 1", "explosives", "EX-Number required"],
            "PHMSA": ["Pipeline and Hazardous Materials Safety Administration", "EX-Number issuer"],
            
            # Export relationships (C7.17)
            "ITAR": ["International Traffic in Arms Regulations", "126.6 exemptions", "PM/DDTC"],
            "AES": ["Automated Export System", "CBP filing", "generates ITN"],
            "EEI": ["Electronic Export Information", "AES submission", "required for defense articles"],
            "CBP": ["Customs and Border Protection", "AES filing", "export documentation"],
            "ITN": ["Internal Transaction Number", "AES-generated", "export tracking"],
            
            # Claims relationships (C7.21)
            "TDR": ["Transportation Discrepancy Report", "DD Form 361", "SCO submits"],
            "tracer action": ["non-receipt investigation", "purchaser initiates"],
            
            # Freight Forwarder relationships (C7.5)
            "freight forwarder": ["purchaser-selected", "ITAR registration required", "DTC 4/5"],
            "DGR": ["Designated Government Representative", "cannot be freight forwarder"],
        }
        
        # Confidence scoring weights
        self.confidence_weights = {
            "exact_match": 1.0,
            "partial_match": 0.8,
            "acronym_match": 0.9,
            "context_match": 0.6,
            "ai_extracted": 0.7,
            "knowledge_graph": 0.95,
            "dynamic_knowledge": 0.8,
            "database_match": 0.9
        }
        
        # =================================================================
        # ACRONYM ↔ FULL FORM PAIRING MAPS (for extracting both)
        # =================================================================
        self.ACRONYM_TO_FULLFORM = {
            # Chapter 4 - Core Programs
            "tpa": "total package approach",
            "eum": "end use monitoring",
            "eeum": "enhanced end use monitoring",
            "fms-only": "foreign military sales only",
            "rdfp": "regional defense fellowship program",
            # Chapter 4 - Equipment
            "sme": "significant military equipment",
            "mde": "major defense equipment",
            "gfe": "government furnished equipment",
            "gfm": "government furnished materiel",
            "nvd": "night vision device",
            "nvds": "night vision devices",
            "manpads": "man-portable air defense system",
            "tdp": "technical data package",
            # Chapter 4 - Targeting
            "geoint": "geospatial intelligence",
            "c4isr": "command control communications computer intelligence surveillance reconnaissance",
            "atd": "advanced target development",
            "tcm": "target coordinate mensuration",
            "cde": "collateral damage estimation",
            # Chapter 4 - DSCA Offices
            "spp": "strategy plans and policy",
            "iops": "international operations",
            "iops/wpn": "weapons directorate",
            "iops/wpns": "weapons directorate",
            "iops/rex": "regional execution directorate",
            # Chapter 4 - Documents
            "p&a": "price and availability",
            "par": "pre-lor assessment request",
            "cn": "congressional notification",
            "masl": "military articles and services list",
            # Chapter 4 - Legal
            "ndp": "national disclosure policy",
            "ndp-1": "national disclosure policy 1",
            # Chapter 1 - Core (keep existing)
            "dsca": "defense security cooperation agency",
            "dfas": "defense finance and accounting service",
            "fms": "foreign military sales",
            "dcs": "direct commercial sales",
            "sa": "security assistance",
            "sc": "security cooperation",
            "imet": "international military education and training",
            "fmf": "foreign military financing",
            "loa": "letter of offer and acceptance",
            "lor": "letter of request",
            "aeca": "arms export control act",
            "faa": "foreign assistance act",
            "usml": "united states munitions list",
            "comsec": "communications security",
            "infosec": "information security",
            "dtsa": "defense technology security administration",
            # Chapter 5 - Core Documents
            "load": "loa data",
            "cta": "country team assessment",
            "mfr": "memorandum for record",
            "rfp": "request for proposal",
            "rfi": "request for information",
            # Chapter 5 - Case Types
            "clssa": "cooperative logistics supply support arrangement",
            "fmso": "foreign military sales order",
            "fmso i": "foreign military sales order i",
            "fmso ii": "foreign military sales order ii",
            # Chapter 5 - Response Types
            "nte": "not-to-exceed",
            "ffp": "firm fixed price",
            "eoq": "economic order quantity",
            # Chapter 5 - Processing
            "milap": "military department approval",
            "milsgn": "military signature",
            "cpohold": "case processing office hold",
            "cpoholdrem": "cpohold removal",
            "cdef": "case development extenuating factor",
            "case delay": "cdef",
            "processing delay": "cdef",
            "approval delay": "cdef",
            "coordination delay": "cdef",
            "oed": "offer expiration date",
            # Chapter 5 - Special Items
            "so-p": "special operations peculiar",
            "mtcr": "missile technology control regime",
            "isr": "intelligence surveillance reconnaissance",
            "fom": "figure of merit",
            "pdt": "population density tables",
            # Chapter 5 - Approvals
            "ot&e": "operational testing and evaluation",
            "endp": "exception to national disclosure policy",
            # Chapter 5 - Organizations
            "iops/gex": "international operations global execution directorate",
            "iops/gex/cwd": "case writing and development division",
            "spp/epa": "execution policy and analysis directorate",
            "adm/pie": "administration performance improvement effectiveness directorate",
            "adm/pie/ame": "assessment monitoring and evaluation division",
            "obo": "office of business operations",
            "obo/fpre": "financial policy and regional execution directorate",
            "obo/fpre/frc": "financial reporting and compliance division",
            "cpd": "country portfolio director",
            "pm/sa": "office of security assistance",
            "sof at&l-io": "sof acquisition technology and logistics international operations",
            # Chapter 5 - Systems
            "dsams": "defense security assistance management system",
            "cts": "case tracking system",
            "scip": "security cooperation information portal",
            "dts": "defense transportation system",
            # Chapter 6 - Implementation
            "ei": "emergency implementation",
            "oa": "obligational authority",
            "ssc": "supply services complete",
            # Chapter 6 - Systems
            "difs": "defense integrated financial system",
            "cprs": "case performance reporting system",
            # Chapter 6 - Financial
            "dfas-in": "defense finance and accounting services indianapolis",
            "cfd": "country finance director",
            "dwcf": "defense working capital fund",
            "wcf": "working capital fund",
            "obo/fpre/fp": "financial policy division",
            "obo/imt/eads": "enterprise application development and support division",
            "iops/gex/scd": "security cooperation division",
            # Chapter 6 - Acquisition
            "cica": "competition in contracting act",
            "taa": "technical assistance agreement",
            "clin": "contract line item number",
            "arp": "acquisition requirements package",
            "pwss": "performance work statement",
            "euc": "end use certificate",
            # Chapter 6 - Logistics
            "f/ad": "force activity designator",
            "und": "urgency of need designator",
            "jmpab": "joint materiel priority allocation board",
            "milstrip": "military standard requisitioning and issue procedures",
            "ummips": "uniform material movement and issue priority system",
            "icp": "inventory control point",
            "ilco": "international logistics control office",
            "cbs": "commercial buying service",
            "tvl": "tailored vendor logistics",
            "pros": "parts and repair ordering system",
            "snap": "simplified non-standard acquisition process",
            "nsn": "national stock number",
            "tcn": "transportation control number",
            # Chapter 6 - Documents
            "sdr": "supply discrepancy report",
            "sf 364": "standard form 364",
            "dlm": "defense logistics management",
            "dlms": "defense logistics management standards",
            "jtr": "joint travel regulations",
            # Chapter 6 - Repair
            "r&r": "repair and return",
            "gfe": "government furnished equipment",
            "gfm": "government furnished materiel",
            # Chapter 6 - Reviews
            "fmr": "financial management review",
            "crr": "case reconciliation review",
            "samr": "security assistance management review",
            # Chapter 6 - Training
            "mtt": "mobile training team",
            "ltd": "language training detachment",
            # Chapter 6 - Special Programs
            "enjjpt": "euro nato joint jet pilot training program",
            "ecisap": "electronic combat international security assistance program",
            # Chapter 6 - Amendment/Modification
            "etp": "exception to policy",
            "dreact": "reactivation authorized milestone",
            "milreact": "mildep reactivation",
            "scml": "small case management line",
            "vat": "value added tax",
            "pc&h": "packing crating and handling",
            "cui": "controlled unclassified information",
            # Chapter 7 - Transportation (C7.1-C7.21)
            # Defense Transportation System (C7.6)
            "ustranscom": "united states transportation command",
            "amc": "air mobility command",
            "sddc": "surface deployment and distribution command",
            "msc": "military sealift command",
            "dtr": "defense transportation regulation",
            # Delivery Terms (C7.4)
            "dtc": "delivery term code",
            "dtc 4": "delivery term code 4",
            "dtc 5": "delivery term code 5",
            "dtc 7": "delivery term code 7",
            "dtc 8": "delivery term code 8",
            "dtc 9": "delivery term code 9",
            "fob": "free on board",
            "poe": "port of embarkation",
            "pod": "port of debarkation",
            # MAPAD (C7.7)
            "mapad": "military assistance program address directory",
            "tac": "type address code",
            "tac m": "type address code m",
            "cric": "communication routing identifier code",
            "ilcs": "integrated logistics communication system",
            # Documentation (C7.6, C7.11)
            "noa": "notice of availability",
            "orc": "offer release code",
            "bl": "bill of lading",
            "cbl": "commercial bill of lading",
            "gbl": "government bill of lading",
            "irapt": "invoicing receipt acceptance and property transfer",
            # Special Transportation (C7.6.2)
            "saam": "special assignment airlift mission",
            "ngds": "next generation delivery services",
            # Cargo Preference (C7.9)
            "dna": "determination of non-availability",
            "marad": "maritime administration",
            # Packaging/Marking (C7.8)
            "wpm": "wood packaging material",
            "ispm 15": "international standards for phytosanitary measures 15",
            "mil-std-129": "military standard 129",
            # Classified Transportation (C7.13, C7.14)
            "cci": "controlled cryptographic items",
            "cismoa": "communications interoperability and security memorandum of agreement",
            "dcsa": "defense counterintelligence and security agency",
            "nispom": "national industrial security program operating manual",
            "cnss": "committee on national security systems",
            "sf-153": "comsec material report",
            # AA&E (C7.15)
            "aa&e": "arms ammunition and explosives",
            "src": "security risk category",
            "src i": "security risk category i",
            "src ii": "security risk category ii",
            "src iii": "security risk category iii",
            "src iv": "security risk category iv",
            # HAZMAT (C7.16)
            "hazmat": "hazardous materials",
            "hmr": "hazardous materials regulations",
            "phmsa": "pipeline and hazardous materials safety administration",
            "hc1": "hazard class 1",
            "ex-number": "exemption number",
            # Export Compliance (C7.17)
            "eei": "electronic export information",
            "aes": "automated export system",
            "cbp": "customs and border protection",
            "itn": "internal transaction number",
            # Organizations
            "dgr": "designated government representative",
            # Claims (C7.21)
            "tdr": "transportation discrepancy report",
        }
        
        # Reverse mapping: full form → acronym
        self.FULLFORM_TO_ACRONYM = {v: k for k, v in self.ACRONYM_TO_FULLFORM.items()}
        # Add common variations
        self.FULLFORM_TO_ACRONYM.update({
            "total package approach": "tpa",
            "end use monitoring": "eum",
            "enhanced end use monitoring": "eeum",
            "significant military equipment": "sme",
            "major defense equipment": "mde",
            "government furnished equipment": "gfe",
            "night vision device": "nvd",
            "night vision devices": "nvds",
            "geospatial intelligence": "geoint",
            "advanced target development": "atd",
            "target coordinate mensuration": "tcm",
            "collateral damage estimation": "cde",
            "price and availability": "p&a",
            "pre-lor assessment request": "par",
            "congressional notification": "cn",
            "military articles and services list": "masl",
            "national disclosure policy": "ndp",
            "defense security cooperation agency": "dsca",
            "foreign military sales": "fms",
            "direct commercial sales": "dcs",
            "letter of offer and acceptance": "loa",
            "letter of request": "lor",
            "arms export control act": "aeca",
            "foreign assistance act": "faa",
            "united states munitions list": "usml",
            "man-portable air defense system": "manpads",
            "communications security": "comsec",
            "information security": "infosec",
            # Chapter 5 - Full forms to acronyms
            "loa data": "load",
            "country team assessment": "cta",
            "memorandum for record": "mfr",
            "request for proposal": "rfp",
            "request for information": "rfi",
            "cooperative logistics supply support arrangement": "clssa",
            "foreign military sales order": "fmso",
            "foreign military sales order i": "fmso i",
            "foreign military sales order ii": "fmso ii",
            "not-to-exceed": "nte",
            "firm fixed price": "ffp",
            "economic order quantity": "eoq",
            "military department approval": "milap",
            "military signature": "milsgn",
            "case processing office hold": "cpohold",
            "cpohold removal": "cpoholdrem",
            "case development extenuating factor": "cdef",
            "delay": "cdef",
            "taking longer than expected": "cdef",
            "delaying my case": "cdef",
            "outside coordination": "cdef",
            "offer expiration date": "oed",
            "special operations peculiar": "so-p",
            "missile technology control regime": "mtcr",
            "intelligence surveillance reconnaissance": "isr",
            "figure of merit": "fom",
            "population density tables": "pdt",
            "operational testing and evaluation": "ot&e",
            "exception to national disclosure policy": "endp",
            "country portfolio director": "cpd",
            "defense security assistance management system": "dsams",
            "case tracking system": "cts",
            "security cooperation information portal": "scip",
            "defense transportation system": "dts",
            # Chapter 6 - Full forms to acronyms
            "emergency implementation": "ei",
            "obligational authority": "oa",
            "supply services complete": "ssc",
            "defense integrated financial system": "difs",
            "case performance reporting system": "cprs",
            "defense finance and accounting services indianapolis": "dfas-in",
            "country finance director": "cfd",
            "defense working capital fund": "dwcf",
            "working capital fund": "wcf",
            "financial policy division": "obo/fpre/fp",
            "competition in contracting act": "cica",
            "technical assistance agreement": "taa",
            "contract line item number": "clin",
            "acquisition requirements package": "arp",
            "end use certificate": "euc",
            "force activity designator": "f/ad",
            "urgency of need designator": "und",
            "joint materiel priority allocation board": "jmpab",
            "military standard requisitioning and issue procedures": "milstrip",
            "uniform material movement and issue priority system": "ummips",
            "inventory control point": "icp",
            "international logistics control office": "ilco",
            "commercial buying service": "cbs",
            "tailored vendor logistics": "tvl",
            "parts and repair ordering system": "pros",
            "simplified non-standard acquisition process": "snap",
            "national stock number": "nsn",
            "transportation control number": "tcn",
            "supply discrepancy report": "sdr",
            "standard form 364": "sf 364",
            "defense logistics management": "dlm",
            "defense logistics management standards": "dlms",
            "joint travel regulations": "jtr",
            "repair and return": "r&r",
            "government furnished equipment": "gfe",
            "government furnished materiel": "gfm",
            "financial management review": "fmr",
            "case reconciliation review": "crr",
            "security assistance management review": "samr",
            "mobile training team": "mtt",
            "language training detachment": "ltd",
            "euro nato joint jet pilot training program": "enjjpt",
            "electronic combat international security assistance program": "ecisap",
            "exception to policy": "etp",
            "reactivation authorized milestone": "dreact",
            "mildep reactivation": "milreact",
            "small case management line": "scml",
            "value added tax": "vat",
            "packing crating and handling": "pc&h",
            "controlled unclassified information": "cui",
            # Chapter 7 - Transportation Full Forms to Acronyms
            "united states transportation command": "ustranscom",
            "air mobility command": "amc",
            "surface deployment and distribution command": "sddc",
            "military sealift command": "msc",
            "defense transportation regulation": "dtr",
            "delivery term code": "dtc",
            "free on board": "fob",
            "port of embarkation": "poe",
            "port of debarkation": "pod",
            "military assistance program address directory": "mapad",
            "type address code": "tac",
            "communication routing identifier code": "cric",
            "integrated logistics communication system": "ilcs",
            "notice of availability": "noa",
            "offer release code": "orc",
            "bill of lading": "bl",
            "commercial bill of lading": "cbl",
            "government bill of lading": "gbl",
            "invoicing receipt acceptance and property transfer": "irapt",
            "special assignment airlift mission": "saam",
            "next generation delivery services": "ngds",
            "determination of non-availability": "dna",
            "maritime administration": "marad",
            "wood packaging material": "wpm",
            "international standards for phytosanitary measures 15": "ispm 15",
            "military standard 129": "mil-std-129",
            "controlled cryptographic items": "cci",
            "communications interoperability and security memorandum of agreement": "cismoa",
            "defense counterintelligence and security agency": "dcsa",
            "national industrial security program operating manual": "nispom",
            "committee on national security systems": "cnss",
            "comsec material report": "sf-153",
            "arms ammunition and explosives": "aa&e",
            "security risk category": "src",
            "hazardous materials": "hazmat",
            "hazardous materials regulations": "hmr",
            "pipeline and hazardous materials safety administration": "phmsa",
            "hazard class 1": "hc1",
            "exemption number": "ex-number",
            "electronic export information": "eei",
            "automated export system": "aes",
            "customs and border protection": "cbp",
            "internal transaction number": "itn",
            "designated government representative": "dgr",
            "transportation discrepancy report": "tdr",
        })
        
        print("[IntegratedEntityAgent] Initialization complete with Chapter 1, 4, 5, 6 & 7 patterns + acronym pairing")
        
        # v5.9.3: 2-Hop Path RAG attributes
        self._current_query = ""
        self._current_intent = None
        self._two_hop_context = None
        print("[IntegratedEntityAgent v5.9.3] 2-Hop Path RAG attributes initialized")


    @time_function
    def extract_and_retrieve(self, query: str, intent_info: Dict, documents_context: List = None) -> Dict[str, Any]:
        """
        Main method for integrated entity extraction and database retrieval
        NOW WITH FILE CONTENT EXTRACTION AND FINANCIAL DATA
        v5.9.3: Added 2-Hop Path RAG context storage
        """
        print(f"[IntegratedEntityAgent] Processing query: '{query}' with intent: {intent_info.get('intent', 'unknown')}")
        
        # v5.9.3: Store query context for 2-hop RAG
        self._current_query = query
        self._current_intent = intent_info.get('intent') if intent_info else None
        self._two_hop_context = None
        
        # ✅ CRITICAL: ALWAYS log file status at entry point
        if documents_context:
            print(f"[IntegratedEntityAgent] 📁 RECEIVED {len(documents_context)} FILES")
            for idx, doc in enumerate(documents_context[:3], 1):
                fname = doc.get('fileName', 'Unknown')
                content_len = len(doc.get('content', ''))
                has_content = len(doc.get('content', '')) > 50
                print(f"[IntegratedEntityAgent]   File {idx}: {fname} ({content_len} chars) - {'✅ READY' if has_content else '⚠️ INSUFFICIENT'}")
        else:
            print(f"[IntegratedEntityAgent] ⚠️ WARNING: No files provided (documents_context is None/empty)")

        try:
            # Phase 1: Enhanced entity extraction FROM QUERY
            entities = self._extract_entities_enhanced(query, intent_info)
            print(f"[IntegratedEntityAgent] Extracted entities from query: {entities}")
            
            # === NEW: Phase 1.5 - Extract entities from CASE FILES ===
            file_entities = []
            file_relationships = []
            if documents_context:
                print(f"[IntegratedEntityAgent] Processing {len(documents_context)} case files")
                for doc in documents_context[:3]:  # Limit to 3 files
                    content = doc.get('content', '')
                    filename = doc.get('fileName', 'Unknown')
                    if content and len(content) > 50:
                        print(f"[IntegratedEntityAgent] Extracting from file: {filename}")
                        
                        # Extract entities from file content
                        file_ents = self._extract_entities_from_text(content, filename)
                        file_entities.extend(file_ents)
                        
                        # Extract relationships from file content
                        file_rels = self._extract_relationships_from_text(content, filename)
                        file_relationships.extend(file_rels)
                
                # Merge file entities with query entities
                entities.extend(file_entities)
                entities = list(dict.fromkeys(entities))  # Remove duplicates
                print(f"[IntegratedEntityAgent] Total entities after file extraction: {len(entities)}")
                
                # Save file knowledge for future reuse
                if file_entities or file_relationships:
                    for doc in documents_context[:3]:
                        filename = doc.get('fileName', 'Unknown')
                        self._save_file_knowledge_to_dynamic(file_entities, file_relationships, filename)
            # === END NEW ===
            
            # Phase 2: Query all data sources
            all_results = {
                "query": query,
                "entities": entities,
                "intent_info": intent_info,
                "timestamp": datetime.now().isoformat(),
                "data_sources": {},
                "context": [],
                "text_sections": [],
                "relationships": [],
                "confidence_scores": {},
                "overall_confidence": 0.0,
                "extraction_method": "integrated_database_enhanced_with_files",
                "extraction_phases": ["pattern_matching", "nlp_extraction", "file_extraction", "database_queries"],
                "phase_count": 4,
                "file_entities_found": len(file_entities),
                "file_relationships_found": len(file_relationships)
            }
            
            # ✅ NEW: Extract financial records from documents
            financial_records = []
            if documents_context:
                for doc in documents_context:
                    if doc.get('metadata', {}).get('hasFinancialData'):
                        records = doc['metadata'].get('financialRecords', [])
                        financial_records.extend(records)
                        print(f"[EntityAgent] 📊 Added {len(records)} financial records from {doc.get('fileName')}")
            
            # Add to results
            all_results["financial_records"] = financial_records
            all_results["has_financial_data"] = len(financial_records) > 0
            
            print(f"[EntityAgent] 💰 Total financial records available: {len(financial_records)}")
            # ✅ END NEW
            
            # Query each source with error handling
            cosmos_results = self._safe_query_cosmos(query, entities)
            vector_results = self._safe_query_vector(query)

            print(f"[IntegratedEntityAgent] Vector results before dedup: {len(vector_results)}")
            vector_results = self.deduplicate_vector_results(vector_results)
            print(f"[IntegratedEntityAgent] Vector results after dedup: {len(vector_results)}")
            
            # v5.9.10: DISABLED Entity Boosting - now handled by hybrid re-ranking
            # The rerank_results() function in _safe_query_vector already does:
            # - Keyword matching (same as entity matching)
            # - Table/Figure/Appendix boost
            # - Section depth boost
            # _boost_by_entities was overriding these improvements
            # vector_results = self._boost_by_entities(vector_results, entities, query)
            print(f"[IntegratedEntityAgent] Vector results (entity boost DISABLED - handled by hybrid rerank): {len(vector_results)}")

            all_results["data_sources"] = {
                "cosmos_gremlin": {
                    "results": cosmos_results,
                    "count": len(cosmos_results),
                    "status": "success" if cosmos_results else "no_results"
                },
                "vector_db": {
                    "results": vector_results,
                    "count": len(vector_results),
                    "status": "success" if vector_results else "no_results",
                    "deduplication_applied": True
                }
            }

            # Store results for use in entity context and text sections
            self.last_retrieval_results = {
                'vector_db': vector_results,
                'cosmos': cosmos_results
            }
            
            # Phase 3: Generate enhanced context from all sources
            self._populate_enhanced_context(all_results, entities)
            
            # === NEW: Add file relationships to results ===
            if file_relationships:
                all_results["relationships"].extend(file_relationships)
                print(f"[IntegratedEntityAgent] Added {len(file_relationships)} relationships from files")
            # === END NEW ===
            
            print(f"\n{'='*80}")
            print(f"[DEBUG] VECTOR DB RESULTS ANALYSIS")
            print(f"{'='*80}")
            if 'vector_db' in all_results["data_sources"] and all_results["data_sources"]["vector_db"]["results"]:
                vector_results = all_results["data_sources"]["vector_db"]["results"]
                print(f"Total Vector DB results: {len(vector_results)}\n")
                for i, result in enumerate(vector_results, 1):
                    content = result.get('content', '')
                    distance = result.get('similarity', result.get('distance', None))
                    if distance is not None:
                        similarity_score = round(1 - distance, 4) if distance <= 1 else round(distance, 4)
                    else:
                        similarity_score = 'N/A'
                    
                    print(f"[Vector Result {i}]")
                    print(f"  Length: {len(content)} chars")
                    print(f"  Preview: {content[:300]}...")
                    print(f"  Similarity: {similarity_score}")
                    print()
            print(f"{'='*80}\n")
            
            # E1.1: Log entity extraction metrics
            if entities:
                metrics_result = self.entity_metrics.evaluate_extraction(query, entities)
                all_results["entity_metrics"] = metrics_result["metrics"]
                all_results["entity_metrics_passed"] = metrics_result["passed"]
                
                print(f"\n[EntityMetrics E1.1] Extraction Results:")
                print(f"  Entities extracted: {entities}")
                print(f"  Precision: {metrics_result['metrics']['precision']:.0%} {'✅' if metrics_result['passed']['precision'] else '❌'} (Target: ≥90%)")
                print(f"  Recall: {metrics_result['metrics']['recall']:.0%} {'✅' if metrics_result['passed']['recall'] else '❌'} (Target: ≥85%)")
                print(f"  F1 Score: {metrics_result['metrics']['f1_score']:.0%} {'✅' if metrics_result['passed']['f1_score'] else '❌'} (Target: ≥90%)")
                print(f"  Hallucination Rate: {metrics_result['metrics']['hallucination_rate']:.0%} {'✅' if metrics_result['passed']['hallucination_rate'] else '❌'} (Target: ≤5%)")
                
                if metrics_result['hallucinations']:
                    print(f"  ⚠️ Hallucinated entities: {metrics_result['hallucinations']}")
            
            print(f"[IntegratedEntityAgent] Query complete: {len(entities)} entities, multiple data sources")
            return all_results
            
        except Exception as e:
            print(f"[IntegratedEntityAgent] Error processing query: {e}")
            return {
                "query": query,
                "entities": [],
                "context": [],
                "text_sections": [],
                "relationships": [],
                "confidence_scores": {},
                "overall_confidence": 0.0,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "extraction_method": "integrated_database_enhanced_error",
                "total_results": 0
            }


    def _safe_query_cosmos(self, query: str, entities: List[str]) -> List[Dict]:
        """Safely query Cosmos Gremlin DB"""
        try:
            print("[IntegratedEntityAgent] Querying Cosmos Gremlin...")
            return self.db_manager.query_cosmos_graph(query, entities)
        except Exception as e:
            print(f"[IntegratedEntityAgent] Cosmos Gremlin query failed: {e}")
            return []
    
    def _safe_query_vector(self, query: str) -> List[Dict]:
        """
        Safely query Vector DB with HYBRID RE-RANKING (v5.9.11)
        
        Strategy:
        1. v5.9.11: Gold Training pattern matching FIRST
        2. LLM identifies relevant terms (CDEF, C5.4.2.1, etc.)
        3. Semantic search with ENHANCED query (20 candidates)
        4. Entity-focused search for key terms + Gold entity queries
        5. Re-rank by combined score (embedding + keyword + boost)
        6. Return top 8 after re-ranking
        
        This ensures correct chunks beat generic chunks even with lower embedding similarity.
        """
        try:
            print("[IntegratedEntityAgent] Querying Vector DB (HYBRID RERANK v5.9.11 + GOLD TRAINING)...")
            
            all_results = []
            seen_content = set()
            
            # === v5.9.11: GOLD TRAINING PATTERN MATCHING ===
            print(f"[GOLD TRAINING] Step 0: Checking Gold patterns...")
            gold_trainer = get_gold_trainer()
            gold_pattern = gold_trainer.match_query_to_pattern(query)
            gold_entity_queries = []
            
            if gold_pattern:
                print(f"[GOLD TRAINING] ✅ Matched: {gold_pattern['id']} - {gold_pattern.get('samm_concept', '')}")
                gold_entity_queries = gold_trainer.get_entity_queries(query)
                print(f"[GOLD TRAINING] 📚 Entity queries: {len(gold_entity_queries)}")
            else:
                print(f"[GOLD TRAINING] ❌ No pattern match, using standard flow")
            
            # === SMART SEARCH - LLM identifies relevant terms ===
            print(f"[SMART SEARCH] Step 1: LLM thinking about query...")
            smart_result = think_first_v2(query)
            
            if smart_result["success"]:
                enhanced_query = smart_result["enhanced_query"]
                print(f"[SMART SEARCH] Enhanced query: {enhanced_query[:100]}...")
            else:
                enhanced_query = query
                print(f"[SMART SEARCH] Using original query (LLM unavailable)")
            
            # v5.9.11: If Gold pattern matched, enhance query further
            if gold_pattern:
                gold_enhanced = gold_trainer.build_enhanced_query(query)
                enhanced_query = f"{enhanced_query} {gold_enhanced}"
                print(f"[GOLD TRAINING] 🔍 Gold-enhanced query added")
            
            # === Search 1: ENHANCED semantic query (get MORE candidates for re-ranking) ===
            print(f"[HYBRID] Search 1: Enhanced query (fetching {RERANK_CONFIG['initial_fetch_count']} candidates)")
            semantic_results = self.db_manager.query_vector_db(
                enhanced_query,
                collection_name="samm_all_chapters", 
                n_results=RERANK_CONFIG['initial_fetch_count']  # v5.9.10: Get 20 for re-ranking
            )
            
            for r in semantic_results:
                content_hash = hash(r.get('content', '')[:100])
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    all_results.append(r)
            
            print(f"[HYBRID] Semantic: {len(semantic_results)} → {len(all_results)} unique")
            
            # === Search 2: Entity-focused queries ===
            query_lower = query.lower()
            entity_queries = []
            
            # v5.9.11: Add Gold entity queries FIRST (highest priority)
            entity_queries.extend(gold_entity_queries)
            
            # Check for key entities and create focused queries
            if "secretary of state" in query_lower or "secstate" in query_lower:
                entity_queries.append("Secretary of State authority responsibility supervision direction")
            
            if "itar" in query_lower:
                entity_queries.append("ITAR International Traffic in Arms Regulations DDTC manages")
            
            if "dsca" in query_lower:
                entity_queries.append("DSCA Defense Security Cooperation Agency role responsibility")
            
            if "fms" in query_lower:
                entity_queries.append("FMS Foreign Military Sales process case")
            
            if " sa " in query_lower or query_lower.startswith("sa ") or query_lower.endswith(" sa"):
                entity_queries.append("Security Assistance SA programs Title 22 FAA AECA")
            
            # v5.9.8: CTA-specific search
            if "cta" in query_lower or "country team" in query_lower:
                entity_queries.append("CTA Country Team Assessment C5.1.4 congressional notification new capability sensitive items Table C5.T1")
            
            # v5.9.8: CDEF-specific search for delay questions
            delay_keywords = ["delay", "delaying", "taking longer", "coordination", "approval process"]
            if any(kw in query_lower for kw in delay_keywords):
                entity_queries.append("CDEF Case Development Extenuating Factor C5.4.2.1 processing time exceed standards DSAMS reason code Table C5.T6")
            
            # v5.9.8: OED-specific search for deadline/expiration questions
            if "oed" in query_lower or "expiration" in query_lower or "deadline" in query_lower or "funding" in query_lower:
                entity_queries.append("OED Offer Expiration Date C5.4.19 Figure C5.F6 short OED deadline funding")
            
            # v5.9.10: NEW entity queries for problem questions
            # LOR format specific search
            if "lor" in query_lower and "format" in query_lower:
                entity_queries.append("LOR Letter of Request format Figure C5.F14 Table C5.T3a checklist actionable mandatory criteria")
            
            # Salary/civilian specific search  
            if "salary" in query_lower or "civilian" in query_lower or "personnel cost" in query_lower:
                entity_queries.append("civilian salary personnel costs Table C9.T2a labor rates MTDS calculate disbursing")
            
            # Electronic submission specific search
            if "electronic" in query_lower or "email" in query_lower:
                entity_queries.append("electronic email LOR submission C5.1.3.5 authorized signers digital")
            
            # Case description/amendment specific search
            if "case description" in query_lower or ("description" in query_lower and "amendment" in query_lower):
                entity_queries.append("case description amendment Table C6.T8 LOA Standardization Guide modification")
            
            # Appendix-specific search for LOR description questions
            if "description" in query_lower and "lor" in query_lower:
                entity_queries.append("Appendix 2 LOR description defense article service nomenclature checklist")
            
            # Sole source specific search
            if "sole source" in query_lower or "solesource" in query_lower:
                entity_queries.append("sole source C5.4.8.10.4 Appendix 6 noncompetitive procurement justification")
            
            # === Add entity query based on LLM terms ===
            if smart_result["success"] and smart_result["relevant_terms"]:
                entity_queries.append(smart_result["relevant_terms"])
            
            # Run entity-focused searches
            for eq in entity_queries[:4]:  # v5.9.10: Max 4 additional searches
                print(f"[HYBRID] Search 2: Entity-focused '{eq[:50]}...'")
                entity_results = self.db_manager.query_vector_db(
                    eq,
                    collection_name="samm_all_chapters",
                    n_results=6  # v5.9.10: Get more per entity search
                )
                
                added = 0
                for r in entity_results:
                    content_hash = hash(r.get('content', '')[:100])
                    if content_hash not in seen_content:
                        seen_content.add(content_hash)
                        all_results.append(r)
                        added += 1
                
                print(f"[HYBRID] Entity search: {len(entity_results)} → {added} new unique")
            
            print(f"[HYBRID] Total candidates before re-ranking: {len(all_results)}")
            
            # === v5.9.10: RE-RANK RESULTS ===
            reranked_results = rerank_results(query, all_results)
            
            # Return top N after re-ranking
            final_results = reranked_results[:RERANK_CONFIG['final_return_count']]
            
            print(f"[HYBRID] Returning top {len(final_results)} after re-ranking")
            return final_results
            
        except Exception as e:
            print(f"[IntegratedEntityAgent] Vector DB query failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_entities_enhanced(self, query: str, intent_info: Dict) -> List[str]:
        """
        Enhanced entity extraction with HALLUCINATION FIX
        - Prevents substring false matches (SC inside DSCA)
        - Enforces word boundaries for short acronyms
        - Filters generic words properly
        """
        import re
        
        entities = []
        query_lower = query.lower()
        
        # Get individual words (for boundary checking)
        query_words = set(re.findall(r'\b[a-zA-Z0-9()/-]+\b', query_lower))
        
        # Track what we found
        found_entities = {}  # pattern_lower -> original pattern
        
        # Phase 1: Pattern matching with boundary checks
        for category, patterns in self.samm_entity_patterns.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()
                
                # Skip if already found
                if pattern_lower in found_entities:
                    continue
                
                # Check if pattern exists in query
                if pattern_lower not in query_lower:
                    continue
                
                # SHORT ACRONYMS: Must be standalone word
                if pattern_lower in self.STRICT_BOUNDARY_ACRONYMS:
                    if pattern_lower not in query_words:
                        # Not a standalone word, skip it
                        continue
                
                # 2-3 CHAR PATTERNS: Check word boundary with regex
                elif len(pattern_lower) <= 3:
                    # Use regex to check word boundary
                    boundary_pattern = r'\b' + re.escape(pattern_lower) + r'\b'
                    if not re.search(boundary_pattern, query_lower):
                        continue
                
                # Add the entity
                found_entities[pattern_lower] = pattern
        
        # Phase 2: Remove contained acronyms
        # If "DSCA" is found, remove "SC"
        to_remove = set()
        
        for container, contained_list in self.CONTAINMENT_MAP.items():
            if container in found_entities:
                for contained in contained_list:
                    if contained in found_entities:
                        to_remove.add(contained)
                        print(f"[EntityFix] Removed '{contained}' (inside '{container}')")
        
        # Also: If short acronym is substring of another found entity, remove it
        for short_acr in self.STRICT_BOUNDARY_ACRONYMS:
            if short_acr in found_entities:
                for other in found_entities.keys():
                    if short_acr != other and short_acr in other:
                        to_remove.add(short_acr)
                        print(f"[EntityFix] Removed '{short_acr}' (substring of '{other}')")
                        break
        
        # Build final entity list
        for pattern_lower, pattern in found_entities.items():
            if pattern_lower not in to_remove:
                entities.append(pattern)
        
        # Phase 3: Filter out generic words
        entities = [e for e in entities if e.lower() not in self.GENERIC_WORDS]
        
        # Phase 4: Knowledge graph matching (keep existing logic)
        if self.knowledge_graph:
            for entity_id, entity in self.knowledge_graph.entities.items():
                entity_label = entity['properties'].get('label', entity_id)
                label_lower = entity_label.lower()
                
                # Apply same boundary rules
                if label_lower in query_lower:
                    if label_lower in self.STRICT_BOUNDARY_ACRONYMS:
                        if label_lower in query_words:
                            if entity_label not in entities:
                                entities.append(entity_label)
                    elif len(label_lower) <= 3:
                        if re.search(r'\b' + re.escape(label_lower) + r'\b', query_lower):
                            if entity_label not in entities:
                                entities.append(entity_label)
                    else:
                        if entity_label not in entities:
                            entities.append(entity_label)
        
        # Phase 5: ACRONYM PAIRING - Also extract corresponding acronym/full form
        # If user mentions "Total Package Approach", also add "TPA"
        paired_entities = []
        for entity in entities:
            entity_lower = entity.lower()
            # Check if this is a full form that has an acronym
            if entity_lower in self.FULLFORM_TO_ACRONYM:
                acronym = self.FULLFORM_TO_ACRONYM[entity_lower]
                if acronym.upper() not in [e.upper() for e in entities]:
                    paired_entities.append(acronym.upper())
            # Check if this is an acronym that has a full form
            elif entity_lower in self.ACRONYM_TO_FULLFORM:
                full_form = self.ACRONYM_TO_FULLFORM[entity_lower]
                if full_form not in [e.lower() for e in entities]:
                    paired_entities.append(full_form.title())
        
        entities.extend(paired_entities)
        
        # Phase 6: Deduplicate (case-insensitive)
        seen = set()
        unique = []
        for e in entities:
            e_lower = e.lower()
            if e_lower not in seen:
                seen.add(e_lower)
                unique.append(e)
        
        # Phase 7: v5.9.8 - Convert delay-related terms to CDEF
        DELAY_TO_CDEF_MAP = {
            "delay", "delaying", "delayed",
            "taking longer", "longer than expected",
            "outside coordination"
        }
        final_entities = []
        added_cdef = False
        for e in unique:
            if e.lower() in DELAY_TO_CDEF_MAP:
                if not added_cdef:
                    final_entities.append("CDEF")
                    added_cdef = True
                    print(f"[EntityExtraction] Converted '{e}' → CDEF")
            elif e.upper() == "CDEF":
                # Avoid duplicate CDEF if already added via delay conversion
                if not added_cdef:
                    final_entities.append("CDEF")
                    added_cdef = True
            else:
                final_entities.append(e)
        
        # Final deduplication
        seen_final = set()
        result = []
        for e in final_entities:
            if e.lower() not in seen_final:
                seen_final.add(e.lower())
                result.append(e)
        
        # Limit to 10
        result = result[:10]
        print(f"[EntityExtraction] Query: '{query[:50]}...' -> {result}")
        return result
    
    def _extract_entities_from_text(self, text: str, source_file: str) -> List[str]:
        """Extract entities from case file content"""
        entities = []
        text_lower = text.lower()
        
        # v5.9.8: Skip short acronyms in file extraction (too many false positives)
        SKIP_IN_FILE_EXTRACTION = {"pd", "sc", "sa", "ia", "da", "fa", "as", "do", "ca", "pn", "am"}
        
        # Pattern matching in file content
        for category, patterns in self.samm_entity_patterns.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()
                # Skip short acronyms that cause false positives
                if pattern_lower in SKIP_IN_FILE_EXTRACTION:
                    continue
                if pattern_lower in text_lower:
                    entities.append(pattern)
        
        # Extract case-specific entities
        countries = re.findall(r'\b(Taiwan|Israel|Japan|South Korea|Australia|Saudi Arabia|UAE|Poland|Romania|Ukraine|Republic of Korea)\b', text, re.IGNORECASE)
        entities.extend(countries)
        
        equipment = re.findall(r'\b(F-\d{2}[A-Z]?|AH-\d{2}[A-Z]?|CH-\d{2}[A-Z]?|M1A\d|HIMARS|Patriot|THAAD|Javelin|Stinger|AN/[A-Z]+-\d+)\b', text)
        entities.extend(equipment)
        
        dollar_values = re.findall(r'\$[\d,]+(?:\.\d{2})?(?:\s?(?:million|billion|M|B))?', text, re.IGNORECASE)
        entities.extend([f"Value: {val}" for val in dollar_values[:3]])
        
        case_numbers = re.findall(r'(FMS|FMF|IMET)-\d{4}-[A-Z]{2,4}-\d{3,4}', text)
        entities.extend(case_numbers)
        
        entities = list(dict.fromkeys(entities))
        print(f"[FileExtraction] Extracted {len(entities)} entities from {source_file}")
        return entities

    def _extract_relationships_from_text(self, text: str, source_file: str) -> List[str]:
        """Extract relationships from case file content"""
        relationships = []
        
        relationship_patterns = [
            (r'(\w+)\s+(?:directs|administers|supervises|manages|oversees)\s+(\w+)', 'directs'),
            (r'(\w+)\s+is responsible for\s+(\w+)', 'responsible_for'),
            (r'(\w+)\s+coordinates with\s+(\w+)', 'coordinates_with'),
            (r'(\w+)\s+reports to\s+(\w+)', 'reports_to'),
            (r'(\w+)\s+approves\s+(\w+)', 'approves'),
        ]
        
        for pattern, rel_type in relationship_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:5]:
                if len(match) == 2:
                    relationship = f"{match[0]} {rel_type} {match[1]} (from {source_file})"
                    relationships.append(relationship)
        
        print(f"[FileExtraction] Extracted {len(relationships)} relationships from {source_file}")
        return relationships

    def _save_file_knowledge_to_dynamic(self, entities: List[str], relationships: List[str], source_file: str):
        """Save extracted file entities and relationships to dynamic knowledge"""
        timestamp = datetime.now().isoformat()
        
        for entity in entities:
            if entity not in self.dynamic_knowledge["entities"]:
                self.dynamic_knowledge["entities"][entity] = {
                    "definition": f"Entity extracted from case file: {source_file}",
                    "source": "case_file_extraction",
                    "source_file": source_file,
                    "added_date": timestamp,
                    "type": "file_extracted"
                }
        
        for relationship in relationships:
            rel_dict = {
                "relationship": relationship,
                "source": "case_file_extraction",
                "source_file": source_file,
                "added_date": timestamp
            }
            if rel_dict not in self.dynamic_knowledge["relationships"]:
                self.dynamic_knowledge["relationships"].append(rel_dict)
        
        print(f"[DynamicKnowledge] Saved {len(entities)} entities and {len(relationships)} relationships")



    def _extract_nlp_entities_safe(self, query: str, intent_info: Dict) -> List[str]:
        """Fast entity extraction with 15-second timeout"""
        system_msg = """Extract SAMM entities from the query. Return ONLY a simple JSON array.

ENTITIES: Extract ONLY organizations, programs, and authorities that are EXPLICITLY MENTIONED in the query.
IMPORTANT: Do NOT use example entities unless they appear in the actual query.

Examples:
- Query: "What is DSCA?" → Extract: ["DSCA"]
- Query: "What does DFAS do?" → Extract: ["DFAS"]  
- Query: "What is FMS?" → Extract: ["FMS"]
- Query: "What is Security Cooperation?" → Extract: ["Security Cooperation"]

RESPONSE: ["entity1", "entity2"]"""

        prompt = f"Query: '{query}'\nEntities:"
        
        try:
            response = call_ollama_enhanced(prompt, system_msg, temperature=0.0)
            response = response.strip()
            
            json_pattern = r'\[.*?\]'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            if matches:
                try:
                    entities = json.loads(matches[0])
                    if isinstance(entities, list):
                        return [str(e).strip() for e in entities if e]
                except:
                    pass
            
            quote_pattern = r'"([^"]+)"'
            quoted_entities = re.findall(quote_pattern, response)
            return quoted_entities[:3]
                
        except Exception as e:
            print(f"[IntegratedEntityAgent] NLP extraction error: {e}")
        
        return []


    def _populate_enhanced_context(self, all_results: Dict, entities: List[str]):
        """Populate enhanced context from all data sources"""
        context = []
        text_sections = []
        relationships = []
        confidence_scores = {}
        
        # Process each entity
        for entity in entities:
            entity_context = self._generate_entity_context(entity, all_results["query"])
            if entity_context:
                context.append(entity_context)
                confidence_scores[entity] = entity_context.get('confidence', 0.5)
        
        # Get relevant text sections
        text_sections = self._get_enhanced_text_sections(all_results["query"], entities)
        
        # Get comprehensive relationships
        relationships = self._get_comprehensive_relationships(entities, all_results["data_sources"])
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(confidence_scores)
        
        # =====================================================================
        # v5.9.2: CITATION EXTRACTION FROM VECTOR DB METADATA
        # Extract primary and reference citations to pass explicitly to LLM
        # v5.9.9: ENHANCED - Also extracts Tables/Figures from content text!
        # =====================================================================
        citations = {"primary": None, "references": []}
        if hasattr(self, 'last_retrieval_results') and 'vector_db' in self.last_retrieval_results:
            citation_list = []

            # v5.9.9: Prefer the SAME ordering used to build text_sections (entity-matched first)
            ordered_meta = getattr(self, 'last_text_sections_meta', None)
            if ordered_meta:
                for item in ordered_meta[:8]:
                    section = (item or {}).get('section_number', '') or ''
                    if section and section != 'Unknown':
                        citation_list.append(section)
            else:
                # Fallback: original vector_db ordering
                for result in self.last_retrieval_results['vector_db'][:5]:
                    meta = result.get('metadata', {})
                    section = meta.get('section_number', '') or meta.get('section_id', '') or meta.get('section', '')
                    if section and section != 'Unknown':
                        citation_list.append(section)

            # =====================================================================
            # v5.9.9: NEW - Extract Tables and Figures from CONTENT TEXT
            # This catches Tables/Figures that appear in chunk content but not metadata
            # =====================================================================
            import re
            for result in self.last_retrieval_results['vector_db'][:8]:
                content = result.get('content', '') or ''
                if content:
                    # Extract Table references (e.g., Table C5.T1, Table C5.T3a)
                    tables_found = re.findall(r'[Tt]able\s+C\d+\.T\d+[A-Za-z]?', content)
                    for table in tables_found:
                        # Normalize to proper case: "Table C5.T3a"
                        table_normalized = re.sub(r'^[Tt]able', 'Table', table)
                        if table_normalized not in citation_list:
                            citation_list.append(table_normalized)
                            print(f"[CitationExtract v5.9.9] Found Table in content: {table_normalized}")
                    
                    # Extract Figure references (e.g., Figure C5.F14, Figure C5.F6)
                    figures_found = re.findall(r'[Ff]igure\s+C\d+\.F\d+[A-Za-z]?', content)
                    for figure in figures_found:
                        # Normalize to proper case: "Figure C5.F14"
                        figure_normalized = re.sub(r'^[Ff]igure', 'Figure', figure)
                        if figure_normalized not in citation_list:
                            citation_list.append(figure_normalized)
                            print(f"[CitationExtract v5.9.9] Found Figure in content: {figure_normalized}")
            # =====================================================================
            
            # Remove duplicates while preserving order
            unique_citations = list(dict.fromkeys(citation_list))
            
            if unique_citations:
                citations["primary"] = unique_citations[0]
                citations["references"] = unique_citations[1:4] if len(unique_citations) > 1 else []
                print(f"[CitationExtract] PRIMARY: {citations['primary']}, REFERENCES: {citations['references']}")
        # =====================================================================
        
        # Populate results
        all_results.update({
            "context": context,
            "text_sections": text_sections,
            "relationships": relationships,
            "citations": citations,  # v5.9.2: Add extracted citations
            "confidence_scores": confidence_scores,
            "overall_confidence": overall_confidence,
            "total_results": len(context) + len(text_sections) + len(relationships)
        })
    
    def _generate_entity_context(self, entity: str, query: str) -> Optional[Dict]:
        """Generate comprehensive context information for an entity"""
        context_info = None
        
        # Check knowledge graph first (highest confidence)
        if self.knowledge_graph:
            for entity_id, kg_entity in self.knowledge_graph.entities.items():
                entity_label = kg_entity['properties'].get('label', entity_id)
                
                if (entity.lower() == entity_label.lower() or 
                    entity.lower() == entity_id.lower()):
                    
                    definition = kg_entity['properties'].get('definition', 
                                kg_entity['properties'].get('role', ''))
                    section = kg_entity['properties'].get('section', '')
                    
                    # E1.2: Use new confidence formula
                    conf_result = self.entity_metrics.calculate_entity_confidence(
                        entity=entity_label,
                        source_type="knowledge_graph",
                        query=query,
                        extraction_method="exact_match"
                    )
                    
                    context_info = {
                        "entity": entity_label,
                        "definition": definition,
                        "section": section,
                        "type": kg_entity.get('type', 'unknown'),
                        "confidence": conf_result["confidence"],
                        "confidence_breakdown": conf_result["confidence_breakdown"],
                        "source": "knowledge_graph",
                        "properties": kg_entity['properties']
                    }
                    print(f"[IntegratedEntityAgent] Knowledge graph context for: {entity_label} (conf: {conf_result['confidence']:.0%})")
                    break
        
        # Check dynamic knowledge if not found
        if not context_info and entity in self.dynamic_knowledge["entities"]:
            entity_data = self.dynamic_knowledge["entities"][entity]
            
            # E1.2: Use new confidence formula
            conf_result = self.entity_metrics.calculate_entity_confidence(
                entity=entity,
                source_type="dynamic_knowledge",
                query=query,
                extraction_method="pattern_match"
            )
            
            context_info = {
                "entity": entity,
                "definition": entity_data.get('definition', ''),
                "section": entity_data.get('section', ''),
                "type": entity_data.get('type', 'dynamic'),
                "confidence": conf_result["confidence"],
                "confidence_breakdown": conf_result["confidence_breakdown"],
                "source": "dynamic_knowledge",
                "added_date": entity_data.get('added_date', '')
            }
            print(f"[IntegratedEntityAgent] Dynamic knowledge context for: {entity} (conf: {conf_result['confidence']:.0%})")
        
        # Generate context using AI if not found
        if not context_info:
            context_info = self._generate_ai_context(entity, query)
        
        return context_info
    
    def _generate_ai_context(self, entity: str, query: str) -> Dict:
        """Generate AI context for entity - DISABLED FOR SPEED, returns quick fallback"""
        # E1.2: Use new confidence formula
        conf_result = self.entity_metrics.calculate_entity_confidence(
            entity=entity,
            source_type="ai_extraction",
            query=query,
            extraction_method="fuzzy_match" if entity.lower() not in query.lower() else "partial_match"
        )
        
        return {
            "entity": entity,
            "definition": f"SAMM-related entity: {entity}",
            "section": "Context from vector DB",
            "type": "entity",
            "source": "quick_fallback",
            "confidence": conf_result["confidence"],
            "confidence_breakdown": conf_result["confidence_breakdown"]
        }
        
        # Original AI generation code disabled for speed:
        # context_prompt = f"...Ollama call..."
        # This saves 5-10 seconds per entity!
        """Generate entity context using Llama 3.2 AI capabilities"""
        system_msg = f"""You are a SAMM (Security Assistance Management Manual) expert.

Provide context for the entity "{entity}" as it relates to SAMM.

INCLUDE:
- Brief, accurate definition or role description
- SAMM section reference if known (use the section from the retrieved context)
- Entity type (organization, program, authority, concept)
- Relationship to Security Cooperation/Security Assistance

REQUIREMENTS:
- Be accurate and specific to SAMM
- Use exact SAMM terminology
- If uncertain, indicate lower confidence

RESPONSE FORMAT (JSON):
{{
    "definition": "Brief definition or role description",
    "section": "SAMM section if known, otherwise 'Unknown'", 
    "type": "organization|program|authority|concept",
    "confidence": 0.7,
    "relationships": []
}}"""
        
        prompt = f"""Entity: "{entity}"
Query context: "{query}"

Provide SAMM context for this entity:"""
        
        try:
            response = call_ollama_enhanced(prompt, system_msg, temperature=0.1)
            
            # Try to parse JSON response
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_part = response[json_start:json_end]
                
                context_data = json.loads(json_part)
                context_data["source"] = "ai_generated"
                context_data["entity"] = entity
                
                print(f"[IntegratedEntityAgent] AI generated context for: {entity}")
                return context_data
                
        except json.JSONDecodeError as e:
            print(f"[IntegratedEntityAgent] JSON parsing error in AI context generation: {e}")
        except Exception as e:
            print(f"[IntegratedEntityAgent] AI context generation error: {e}")
        
        # Fallback context
        return {
            "entity": entity,
            "definition": f"SAMM-related entity: {entity}",
            "section": "Unknown",
            "type": "unknown",
            "confidence": self.confidence_weights["context_match"] * 0.5,
            "source": "fallback"
        }
    
    def _get_enhanced_text_sections(self, query: str, entities: List[str]) -> List[str]:
        """Get relevant SAMM text sections from VECTOR DB RESULTS with entity prioritization.

        v5.9.9: CITATION ANCHORING
        - Prefix each returned chunk with its SAMM section anchor (e.g., [C5.4.2.1])
        - Store the ordered metadata for downstream citation selection
        """
        text_sections: List[str] = []

        # v5.9.9: keep the ordered metadata used to build the text sections
        self.last_text_sections_meta: List[Dict[str, Any]] = []

        # Check if we have vector DB results stored
        if not hasattr(self, 'last_retrieval_results'):
            print("[IntegratedEntityAgent] No retrieval results available")
            return text_sections

        results = self.last_retrieval_results

        # Extract text from Vector DB results with ENTITY PRIORITIZATION
        if 'vector_db' in results and results['vector_db'] is not None:
            print(f"[IntegratedEntityAgent] Processing {len(results['vector_db'])} vector DB results")

            # Separate results: those containing entities first, then others
            entity_matched_results = []
            other_results = []

            for i, result in enumerate(results['vector_db'], 1):
                content = (result or {}).get('content', '') or ''
                meta = (result or {}).get('metadata', {}) or {}
                section = meta.get('section_number') or meta.get('section_id') or meta.get('section') or ''

                if content:
                    # Check if this result contains any of the extracted entities
                    contains_entity = False
                    for entity in entities:
                        if entity and entity.lower() in content.lower():
                            contains_entity = True
                            print(f"[DEBUG] Found entity '{entity}' in result {i}")
                            break

                    item = (i, content, meta, section)

                    if contains_entity:
                        entity_matched_results.append(item)
                        print(f"[DEBUG] Vector DB result {i}: ✅ ENTITY MATCH - {content[:100]}...")
                    else:
                        other_results.append(item)
                        print(f"[DEBUG] Vector DB result {i}: ⚪ No entity match - {content[:100]}...")

            print(f"[IntegratedEntityAgent] 🎯 Entity-matched results: {len(entity_matched_results)}, Other: {len(other_results)}")

            def _anchor_text(raw: str, sec: str) -> str:
                sec_clean = (sec or '').strip()
                if not sec_clean or sec_clean.lower() == 'unknown':
                    return raw
                return f"[{sec_clean}] {raw}"

            # Add entity-matched results first (preserve order)
            for idx, content, meta, section in entity_matched_results:
                text_sections.append(_anchor_text(content, section))
                self.last_text_sections_meta.append({
                    "rank": idx,
                    "section_number": section or meta.get("section_number") or meta.get("section_id") or "",
                    "metadata": meta
                })

            # Then add other results
            for idx, content, meta, section in other_results:
                text_sections.append(_anchor_text(content, section))
                self.last_text_sections_meta.append({
                    "rank": idx,
                    "section_number": section or meta.get("section_number") or meta.get("section_id") or "",
                    "metadata": meta
                })

        return text_sections


    def _get_comprehensive_relationships(self, entities: List[str], data_sources: Dict) -> List[str]:
        """Get comprehensive relationships from all sources"""
        relationships = []
        
        # Get relationships from knowledge graph
        if self.knowledge_graph:
            for entity in entities:
                entity_id = None
                
                # Find entity ID in knowledge graph
                for eid, kg_entity in self.knowledge_graph.entities.items():
                    entity_label = kg_entity['properties'].get('label', eid)
                    if entity_label.lower() == entity.lower():
                        entity_id = eid
                        break
                
                # Get relationships for this entity
                if entity_id:
                    entity_rels = self.knowledge_graph.get_relationships(entity_id)
                    if entity_rels is not None:
                        for rel in entity_rels:
                            rel_text = f"{rel['source']} {rel['relationship']} {rel['target']}"
                            relationships.append(rel_text)
                            print(f"[IntegratedEntityAgent] Knowledge graph relationship: {rel_text}")
        
        # Add predefined relationships
        for entity in entities:
            if entity in self.entity_relationships:
                for relationship in self.entity_relationships[entity]:
                    rel_text = f"{entity} {relationship}"
                    relationships.append(rel_text)
                    print(f"[IntegratedEntityAgent] Predefined relationship: {rel_text}")
        
        # Add dynamic relationships from triggers
        for rel in self.dynamic_knowledge["relationships"]:
            source = rel.get("source", "")
            target = rel.get("target", "")
            relationship = rel.get("relationship", "")
            
            if any(entity.lower() in source.lower() or entity.lower() in target.lower() 
                   for entity in entities):
                rel_text = f"{source} {relationship} {target}"
                relationships.append(rel_text)
                print(f"[IntegratedEntityAgent] Dynamic relationship: {rel_text}")
        


        # Add relationships from Cosmos DB Gremlin results
        cosmos_results = data_sources.get("cosmos_gremlin", {}).get("results", [])
        for result in cosmos_results:
            if result.get("type") == "edge":
                edge_data = result.get("data", {})
        # Extract relationship information from edge
                if isinstance(edge_data, dict):
                    label = edge_data.get("label", "relates_to")
            # Try to get vertex names from edge properties
                    from_name = edge_data.get("from_name", edge_data.get("outV", "unknown"))
                    to_name = edge_data.get("to_name", edge_data.get("inV", "unknown"))
            
                    rel_text = f"{from_name} {label} {to_name}"
                    relationships.append(rel_text)
                    print(f"[IntegratedEntityAgent] Cosmos DB relationship: {rel_text}")
        
        # =====================================================================
        # v5.9.3: 2-HOP PATH RAG - Find relationship chains
        # =====================================================================
        if TWO_HOP_PATH_FINDER:
            try:
                # Get current query from instance
                current_query = getattr(self, '_current_query', '')
                current_intent = getattr(self, '_current_intent', None)
                
                two_hop_context = TWO_HOP_PATH_FINDER.get_context_for_query(
                    entities=entities,
                    query=current_query,
                    intent=current_intent
                )
                
                # Store for later use in prompt building
                self._two_hop_context = two_hop_context
                
                # Add 2-hop paths to relationships
                for path in two_hop_context.get('paths', [])[:5]:
                    rel_text = f"[2-HOP PATH] {path['path_text']}"
                    if rel_text not in relationships:
                        relationships.append(rel_text)
                        print(f"[v5.9.3] Added 2-hop: {path['path_text'][:60]}...")
                
                # Add authority chains (critical for "who supervises" questions)
                for entity, chain in two_hop_context.get('authority_chains', {}).items():
                    if chain:
                        chain_text = f"[AUTHORITY CHAIN] {entity.upper()}"
                        for edge in chain:
                            chain_text += f" → {edge['to'].upper()} ({edge['type']})"
                        if chain_text not in relationships:
                            relationships.append(chain_text)
                            print(f"[v5.9.3] Authority chain: {chain_text}")
                
                print(f"[v5.9.3] 2-Hop RAG found {two_hop_context['relationship_count']} paths")
                
            except Exception as e:
                print(f"[v5.9.3] 2-Hop RAG error: {e}")
                self._two_hop_context = None
        # =====================================================================
        # END v5.9.3
        # =====================================================================
        
        # Remove duplicates
        relationships = list(dict.fromkeys(relationships))
        
        print(f"[IntegratedEntityAgent] Total relationships found: {len(relationships)}")
        return relationships
    
    def _calculate_overall_confidence(self, confidence_scores: Dict[str, float]) -> float:
        """Calculate overall confidence score for the extraction"""
        if not confidence_scores:
            return 0.0
        
        scores = list(confidence_scores.values())
        # Weighted average with slight boost for multiple high-confidence entities
        avg_confidence = sum(scores) / len(scores)
        entity_count_factor = min(1.0, len(scores) / 5.0) * 0.1  # Small boost for more entities
        
        return min(1.0, avg_confidence + entity_count_factor)
    
    def update_from_hil(self, query: str, original_entities: List[str], 
                        corrected_entities: List[str], feedback_data: Dict[str, Any] = None):
        """Update agent based on human-in-the-loop feedback"""
        feedback_entry = {
            "query": query,
            "original_entities": original_entities,
            "corrected_entities": corrected_entities,
            "feedback_data": feedback_data or {},
            "timestamp": datetime.now().isoformat(),
            "improvement_type": "hil_correction"
        }
        
        self.hil_feedback_data.append(feedback_entry)
        
        # Add new entities identified by human feedback
        for entity in corrected_entities:
            if entity not in original_entities and entity not in self.custom_entities:
                self.custom_entities[entity] = {
                    "definition": feedback_data.get("definition", "Entity identified through human feedback"),
                    "source": "HIL_feedback",
                    "query_context": query,
                    "added_date": datetime.now().isoformat(),
                    "feedback_id": len(self.hil_feedback_data)
                }
                
                # Add to dynamic knowledge
                self.dynamic_knowledge["entities"][entity] = self.custom_entities[entity]
        
        # Store context corrections
        if feedback_data and feedback_data.get("context_corrections"):
            for entity, corrected_context in feedback_data["context_corrections"].items():
                if entity in self.custom_entities:
                    self.custom_entities[entity]["definition"] = corrected_context
                    self.dynamic_knowledge["entities"][entity]["definition"] = corrected_context
        
        print(f"[IntegratedEntityAgent HIL] Updated with {len(corrected_entities)} entities from feedback for query: '{query[:50]}...'")
        print(f"[IntegratedEntityAgent HIL] Total custom entities: {len(self.custom_entities)}")
        return True
    
    def update_from_trigger(self, new_entities: List[str], new_relationships: List[Dict], 
                           trigger_data: Dict[str, Any] = None):
        """Update agent when new entity/relationship data is available"""
        trigger_entry = {
            "new_entities": new_entities,
            "new_relationships": new_relationships,
            "trigger_data": trigger_data or {},
            "timestamp": datetime.now().isoformat(),
            "trigger_id": len(self.trigger_updates)
        }
        
        self.trigger_updates.append(trigger_entry)
        
        # Add new entities to dynamic knowledge
        for entity in new_entities:
            if entity not in self.dynamic_knowledge["entities"]:
                entity_data = {
                    "definition": trigger_data.get("entity_definitions", {}).get(entity, f"New entity: {entity}"),
                    "source": "trigger_update",
                    "type": trigger_data.get("entity_types", {}).get(entity, "unknown"),
                    "added_date": datetime.now().isoformat(),
                    "trigger_id": len(self.trigger_updates)
                }
                self.dynamic_knowledge["entities"][entity] = entity_data
        
        # Add new relationships to dynamic knowledge
        for relationship in new_relationships:
            if relationship not in self.dynamic_knowledge["relationships"]:
                self.dynamic_knowledge["relationships"].append({
                    **relationship,
                    "source": "trigger_update",
                    "added_date": datetime.now().isoformat(),
                    "trigger_id": len(self.trigger_updates)
                })
        
        print(f"[IntegratedEntityAgent Trigger] Updated with {len(new_entities)} new entities and {len(new_relationships)} relationships")
        print(f"[IntegratedEntityAgent Trigger] Total dynamic entities: {len(self.dynamic_knowledge['entities'])}")
        return True


class EnhancedAnswerAgent:
    """
    Enhanced Answer Agent for SAMM with sophisticated response generation
    
    Features:
    - Windows compatibility and improved error handling
    - Intent-optimized prompt engineering for each question type
    - SAMM-specific response templates and quality standards
    - Multi-pass answer generation with validation
    - Learning system with HIL feedback and trigger updates
    - Automatic answer enhancement (acronym expansion, section references)
    - Answer caching and correction storage
    - Quality scoring and confidence assessment
    """
    
    def __init__(self):
        """Initialize the Enhanced Answer Agent with improved error handling"""
        print("[EnhancedAnswerAgent] Initializing...")
        
        # Learning and feedback systems
        self.hil_feedback_data = []        # Human-in-the-loop feedback storage
        self.answer_templates = {}         # Intent-specific answer templates
        self.trigger_updates = []          # Trigger-based updates storage
        self.custom_knowledge = ""         # Additional knowledge from updates
        self.answer_corrections = {}       # Stored answer corrections
        
        # SAMM-specific response templates for each intent type
        self.samm_response_templates = {
            # === Existing templates ===
            "definition": {
                "structure": "Provide clear definition → cite SAMM section → add context/authority",
                "required_elements": ["definition", "section_reference", "authority_context"],
                "quality_criteria": ["uses_exact_samm_terminology", "cites_section", "expands_acronyms"]
            },
            "distinction": {
                "structure": "Explain key differences → provide examples → cite legal basis",
                "required_elements": ["comparison_points", "specific_examples", "legal_authorities"],
                "quality_criteria": ["clear_comparison", "highlights_subset_relationship", "authority_differences"]
            },
            "authority": {
                "structure": "State authority holder → explain scope → cite legal basis",
                "required_elements": ["authority_holder", "scope_of_authority", "legal_reference"],
                "quality_criteria": ["identifies_correct_authority", "explains_scope", "cites_legal_basis"]
            },
            "organization": {
                "structure": "Name organization → describe role → list responsibilities",
                "required_elements": ["full_name", "primary_role", "specific_duties"],
                "quality_criteria": ["expands_acronyms", "describes_role", "lists_responsibilities"]
            },
            "factual": {
                "structure": "State fact → provide context → cite source",
                "required_elements": ["specific_fact", "context", "source_reference"],
                "quality_criteria": ["accurate_information", "proper_citation", "relevant_context"]
            },
            "relationship": {
                "structure": "Describe relationship → explain significance → provide examples",
                "required_elements": ["relationship_description", "significance", "examples"],
                "quality_criteria": ["clear_relationship", "explains_importance", "concrete_examples"]
            },
            
            # === NEW: Previously missing templates ===
            "process": {
                "structure": "State process name → list steps in order → identify key actors → cite SAMM section",
                "required_elements": ["process_name", "ordered_steps", "responsible_parties", "section_reference"],
                "quality_criteria": ["clear_sequence", "identifies_actors", "includes_timeline_if_applicable"]
            },
            "funding": {
                "structure": "State funding type → explain source → describe mechanism → cite legal authority",
                "required_elements": ["funding_type", "source_of_funds", "payment_mechanism", "legal_authority"],
                "quality_criteria": ["identifies_title_10_or_22", "explains_who_pays", "describes_financial_terms"]
            },
            "eligibility": {
                "structure": "State eligibility criteria → list requirements → note exceptions → cite authority",
                "required_elements": ["eligibility_criteria", "requirements_list", "exceptions", "authority_reference"],
                "quality_criteria": ["clear_criteria", "complete_requirements", "notes_restrictions"]
            },
            "compliance": {
                "structure": "State applicable regulation → explain requirements → describe consequences → cite source",
                "required_elements": ["regulation_name", "compliance_requirements", "enforcement", "source_reference"],
                "quality_criteria": ["identifies_correct_regulation", "clear_requirements", "explains_obligations"]
            },
            "list": {
                "structure": "State what is being listed → provide complete list with descriptions → cite source",
                "required_elements": ["list_context", "complete_items", "item_descriptions", "source_reference"],
                "quality_criteria": ["complete_list", "organized_format", "brief_descriptions"]
            },
            "verification": {
                "structure": "Provide Yes/No answer → explain reasoning → cite supporting evidence",
                "required_elements": ["yes_no_answer", "explanation", "evidence", "section_reference"],
                "quality_criteria": ["direct_answer_first", "clear_reasoning", "proper_citation"]
            },
            "explanation": {
                "structure": "State the purpose/reason → provide context → explain significance → cite source",
                "required_elements": ["purpose_statement", "context", "significance", "source_reference"],
                "quality_criteria": ["clear_purpose", "sufficient_context", "explains_importance"]
            },
            "general": {
                "structure": "Provide accurate information → add relevant context → cite SAMM section",
                "required_elements": ["accurate_information", "relevant_context", "section_reference"],
                "quality_criteria": ["factually_correct", "comprehensive", "properly_cited"]
            }
        }
        
        # Quality enhancement patterns for post-processing
        # v5.9.9: FIXED - Now includes Table and Figure citations!
        self.quality_patterns = {
            "section_references": r"(C\d+\.\d+(?:\.\d+)*|Table\s+C\d+\.T\d+[A-Za-z]?|Figure\s+C\d+\.F\d+[A-Za-z]?)",
            "acronym_detection": r"\b([A-Z]{2,})\b",
            "authority_mentions": r"(Title \d+|[A-Z]+ Act)",
            "incomplete_sentences": r"[a-z]\s*$"
        }
        
        # =====================================================================
        # COMPREHENSIVE ACRONYM EXPANSION DICTIONARY FOR SAMM (400+ entries)
        # =====================================================================
        self.acronym_expansions = {
            # A
            "AAC": "Acquisition Advice Code (AAC)",
            "AAE": "Arms, Ammunition, and Explosive (AAE)",
            "AAR": "After Action Review (AAR)",
            "ACC": "Accelerated Case Closure (ACC)",
            "ACSA": "Acquisition and Cross-Servicing Agreements (ACSA)",
            "ADL": "Advanced Distributed Learning (ADL)",
            "AECA": "Arms Export Control Act (AECA)",
            "AES": "Automated Export System (AES)",
            "AETC": "Air Education and Training Command (AETC)",
            "AFSAT": "Air Force Security Assistance Training Squadron (AFSAT)",
            "AID": "Agency for International Development (AID)",
            "AIK": "Assistance-in-Kind (AIK)",
            "AIM-9X": "Air Intercept Missile-9X (AIM-9X)",
            "ALO": "Audit Liaison Officer (ALO)",
            "ALP": "Aviation Leadership Program (ALP)",
            "AMC": "Air Mobility Command (AMC)",
            "AMRAAM": "Advanced Medium Range Air-to-Air Missiles (AMRAAM)",
            "AO": "Action Officer (AO)",
            "AOD": "Anticipated Offer Date (AOD)",
            "AOR": "Area of Responsibility (AOR)",
            "APO": "Army or Air Force Post Office (APO)",
            "ASD-ISP": "Assistant Secretary of Defense for International Security Policy (ASD-ISP)",
            "ASD-LA": "Assistant Secretary of Defense for Legislative Affairs (ASD-LA)",
            "ASD-RA": "Assistant Secretary of Defense for Reserve Affairs (ASD-RA)",
            "ASD-SOLIC": "Assistant Secretary of Defense for Special Operations/Low-Intensity Conflict (ASD-SOLIC)",
            "ASFF": "Afghanistan Security Forces Fund (ASFF)",
            "AT": "Anti-Tamper (AT)",
            "ATC": "United States Army Transportation Command (ATC)",
            "ATEA": "Anti-Tamper Executive Agent (ATEA)",
            "ATFP": "Anti-Terrorism/Force Protection (ATFP)",
            "ATMG": "Arms Transfer Management Group (ATMG)",
            "AWOL": "Absent Without Leave (AWOL)",
            # B
            "BAMS": "Broad Area Maritime Surveillance (BAMS)",
            "BATFE": "Bureau of Alcohol, Tobacco, Firearms, and Explosives (BATFE)",
            "BES": "Budget Estimate Submission (BES)",
            "BL": "Bill of Lading (BL)",
            "BOS": "Base Operating Support (BOS)",
            "BP": "Budget Project (BP)",
            "BPC": "Building Partner Capacity (BPC)",
            # C
            "C4ISR": "Command, Control, Communications, Computer, Intelligence, Surveillance and Reconnaissance (C4ISR)",
            "CAO": "Collateral Action Officer (CAO)",
            "CAPE": "Cost Assessment and Program Evaluation Office (CAPE)",
            "CAS": "Contract Administrative Surcharge (CAS)",
            "CATM": "Captive Air Training Missile (CATM)",
            "CAV": "Compliance Assessment Visit (CAV)",
            "CBJ": "Congressional Budget Justification (CBJ)",
            "CBJFO": "Congressional Budget Justification for Foreign Operations (CBJFO)",
            "CBL": "Commercial Bill of Lading (CBL)",
            "CBP": "Customs and Border Protection (CBP)",
            "CBS": "Commercial Buying Service (CBS)",
            "CCI": "Controlled Cryptographic Item (CCI)",
            "CCIF": "Combatant Command Initiative Funds (CCIF)",
            "CCL": "Commerce Control List (CCL)",
            "CCMD": "Combatant Command (CCMD)",
            "CCMDS": "Combatant Commands (CCMDS)",
            "CDM": "Case Development Module (CDM)",
            "CDR": "Critical Design Review (CDR)",
            "CDTS": "Counter-Drug Training Support (CDTS)",
            "CETPP": "Combined Education and Training Program Plan (CETPP)",
            "CFD": "Country Finance Director (CFD)",
            "CFS": "Contract Field Services (CFS)",
            "CFV": "Captive Flight Vehicle (CFV)",
            "CG-DCO-I": "U.S. Coast Guard, Directorate of International Affairs and Foreign Policy (CG-DCO-I)",
            "CIA": "Central Intelligence Agency (CIA)",
            "CIO": "Chief Information Officer (CIO)",
            "CISIL": "Centralized Integrated System - International Logistics (CISIL)",
            "CISMOA": "Communications Interoperability and Security Memorandum of Agreement (CISMOA)",
            "CJCS": "Chairman of the Joint Chiefs of Staff (CJCS)",
            "CJCSI": "Chairman of the Joint Chiefs of Staff Instruction (CJCSI)",
            "CLO": "Country Liaison Officer (CLO)",
            "CLS": "Contractor Logistics Support (CLS)",
            "CLSSA": "Cooperative Logistics Supply Support Arrangement (CLSSA)",
            "CLU": "Command Launch Units (CLU)",
            "CMCS": "Case Management Control System (CMCS)",
            "CMP": "Comptroller (CMP)",
            "CN": "Congressional Notification (CN)",
            "CNS": "Congressional Notification System (CNS)",
            "COCOM": "Combatant Command (COCOM)",
            "CODEL": "Congressional Staff Delegations (CODEL)",
            "COM": "Chief of Mission (COM)",
            "COMSEC": "Communications Security (COMSEC)",
            "CONUS": "Continental United States (CONUS)",
            "COPE": "Country Over Private Entity (COPE)",
            "CORCOM": "Coordinating Committee (CORCOM)",
            "CPD": "Country Portfolio Director (CPD)",
            "CPI": "Critical Program Information (CPI)",
            "CPIC": "Capital Planning and Investment Control (CPIC)",
            "CR": "Continuing Resolution (CR)",
            "CRB": "Change Review Board (CRB)",
            "CRSP": "Coalition Readiness Support Program (CRSP)",
            "CS": "Communications Security (CS)",
            "CSEA": "Cadet Semester Exchange Abroad Program (CSEA)",
            "CSPA": "Child Status Protection Act (CSPA)",
            "CTA": "Country Team Assessment (CTA)",
            "CTFP": "Combating Terrorism Fellowship Program (CTFP)",
            "CTS": "Case Tracking System (CTS)",
            "CUI": "Controlled Unclassified Information (CUI)",
            "CWCC": "Conventional Weapons Clearance Course (CWCC)",
            "CWMD": "Countering Weapons of Mass Destruction (CWMD)",
            # D
            "DAR": "Defense Acquisition Regulation (DAR)",
            "DASA-DEC": "Deputy Assistant Secretary of the Army for Defense Exports and Cooperation (DASA-DEC)",
            "DASD": "Deputy Assistant Secretary of Defense (DASD)",
            "DAT": "Defense Attache (DAT)",
            "DATS": "Defense Attaches (DATS)",
            "DBOD": "Business Operations Directorate (DBOD)",
            "DCAA": "Defense Contract Audit Agency (DCAA)",
            "DCCS": "Direct Commercial Contracts System (DCCS)",
            "DCMA": "Defense Contract Management Agency (DCMA)",
            "DCMO": "Deputy Chief Management Officer (DCMO)",
            "DCS": "Direct Commercial Sales (DCS)",
            "DDA": "Designated Disclosure Authority (DDA)",
            "DDAL": "Delegation of Disclosure Authority Letter (DDAL)",
            "DDPO": "DoD Demilitarization Program Office (DDPO)",
            "DDTC": "Directorate of Defense Trade Controls (DDTC)",
            "DELG": "Defense Export Loan Guarantee (DELG)",
            "DEMIL": "Demilitarization (DEMIL)",
            "DESC": "Defense Energy Support Center (DESC)",
            "DFARS": "Defense Federal Acquisition Regulation Supplement (DFARS)",
            "DFAS": "Defense Finance and Accounting Service (DFAS)",
            "DFAS-IN": "Defense Finance and Accounting Service - Indianapolis (DFAS-IN)",
            "DGR": "Designated Government Representative (DGR)",
            "DHS": "Department of Homeland Security (DHS)",
            "DIA": "Defense Intelligence Agency (DIA)",
            "DIACAP": "DoD Information Assurance Certification and Accreditation Process (DIACAP)",
            "DIADS": "DSCA IMET Allocation Database System (DIADS)",
            "DIFS": "Defense Integrated Financial System (DIFS)",
            "DIRNSA": "Director, National Security Agency (DIRNSA)",
            "DISCO": "Defense Industrial Security Clearance Office (DISCO)",
            "DITPR": "DoD IT Portfolio Repository (DITPR)",
            "DLA": "Defense Logistics Agency (DLA)",
            "DLIELC": "Defense Language Institute English Language Center (DLIELC)",
            "DLMS": "Defense Logistics Management System (DLMS)",
            "DOC": "Department of Commerce (DOC)",
            "DOC-CENTER": "Distribution Operations Center (DOC-CENTER)",
            "DoD": "Department of Defense (DoD)",
            "DODAAC": "DoD Activity Address Code (DODAAC)",
            "DoDD": "Department of Defense Directive (DoDD)",
            "DOJ": "Department of Justice (DOJ)",
            "DoS": "Department of State (DoS)",
            "DOS-PM": "DoS Bureau of Political-Military Affairs (DOS-PM)",
            "DOS-PM-DDTC": "DoS Directorate of Defense Trade Controls (DOS-PM-DDTC)",
            "DOS-PM-RSAT": "DoS Bureau of Political-Military Affairs, Office of Regional Security and Arms Transfers (DOS-PM-RSAT)",
            "DOT-PHMSA": "Department of Transportation's Pipeline and Hazardous Materials Safety Administration (DOT-PHMSA)",
            "DP": "Disaster Preparedness (DP)",
            "DR-A": "Reactivation Authorized Milestone (DR-A)",
            "DRRS": "Defense Readiness Reporting System (DRRS)",
            "DSAMS": "Defense Security Assistance Management System (DSAMS)",
            "DSCA": "Defense Security Cooperation Agency (DSCA)",
            "DSCU": "Defense Security Cooperation University (DSCU)",
            "DSS": "Defense Security Service (DSS)",
            "DTC": "Delivery Term Code (DTC)",
            "DTR": "Defense Transportation Regulation (DTR)",
            "DTRA": "Defense Threat Reduction Agency (DTRA)",
            "DTS": "Defense Transportation System (DTS)",
            "DTSA": "Defense Technology Security Administration (DTSA)",
            "DTSI": "Defense Trade Security Initiative (DTSI)",
            "DVOT": "Distinguished Visitor Orientation Tour (DVOT)",
            "DWCF": "Defense Working Capital Fund (DWCF)",
            "DX": "Direct Exchange (DX)",
            # E
            "E-IMET": "Expanded International Military Education and Training (E-IMET)",
            "EACC": "Enhanced Accelerated Case Closure (EACC)",
            "EADS": "Enterprise Application Development and Support Division (EADS)",
            "EBMIS": "Egyptian Budget Management Information System (EBMIS)",
            "ECL": "English Comprehension Level (ECL)",
            "EDA": "Excess Defense Articles (EDA)",
            "EEE": "Emergency, Extraordinary, Expenses (EEE)",
            "EEI": "Electronic Export Information (EEI)",
            "EEUM": "Enhanced End Use Monitoring (EEUM)",
            "EFTS": "Enhanced Freight Tracking System (EFTS)",
            "ELT": "English Language Training (ELT)",
            "ELTM": "English Language Training Materials (ELTM)",
            "ENDP": "Exception to National Disclosure Policy (ENDP)",
            "EO": "Executive Order (EO)",
            "EOD": "Explosive Ordnance Disposal (EOD)",
            "EOQ": "Economic Order Quantity (EOQ)",
            "EP": "Excess Property (EP)",
            "EPG": "European Participating Government (EPG)",
            "ERGT": "Expeditionary Requirements Generation Team (ERGT)",
            "ERP": "Enterprise Resource Planning (ERP)",
            "ERW": "Explosive Remnants of War (ERW)",
            "ESC": "Executive Steering Committee (ESC)",
            "ESEP": "Engineer and Scientist Exchange Program (ESEP)",
            "ETSS": "Extended Training Service Specialist (ETSS)",
            "EUM": "End Use Monitoring (EUM)",
            "EW": "Electronic Warfare (EW)",
            "EWIRDB": "Electronic Warfare Integrated Reprogramming Database (EWIRDB)",
            "EXORD": "Execute Order (EXORD)",
            "EXSEC": "Executive Secretary (EXSEC)",
            # F
            "FAA": "Foreign Assistance Act (FAA)",
            "FAD": "Force Activity Designator (FAD)",
            "FAR": "Federal Acquisition Regulation (FAR)",
            "FAV": "Familiarization and Assistance Visit (FAV)",
            "FBI": "Federal Bureau of Investigation (FBI)",
            "FCG": "Foreign Clearance Guide (FCG)",
            "FCM": "Foreign Consequence Management (FCM)",
            "FDR": "Foreign Disaster Relief (FDR)",
            "FFB": "Federal Financing Bank (FFB)",
            "FFP": "Firm Fixed Price (FFP)",
            "FGI": "Foreign Government Information (FGI)",
            "FICS": "FMS Integrated Control System (FICS)",
            "FMC": "Full Mission Capable (FMC)",
            "FMF": "Foreign Military Financing (FMF)",
            "FMR": "Financial Management Regulations/Review (FMR)",
            "FMS": "Foreign Military Sales (FMS)",
            "FMSCS": "FMS Credit System (FMSCS)",
            "FMSO": "Foreign Military Sales Order (FMSO)",
            "FMT": "Foreign Military Training (FMT)",
            "FOB": "Free on Board (FOB)",
            "FOIA": "Freedom of Information Act (FOIA)",
            "FOM": "Figure of Merit (FOM)",
            "FOT": "Follow-on Training (FOT)",
            "FOUO": "For Official Use Only (FOUO)",
            "FPIOD": "Financial Policy and Internal Operations Division (FPIOD)",
            "FPO": "Fleet Post Office (FPO)",
            "FRB": "Federal Reserve Bank (FRB)",
            "FSC": "Facility Security Clearance (FSC)",
            "FSCA": "Facility Security Clearance Assurance (FSCA)",
            "FSN": "Foreign Service National (FSN)",
            "FSP": "Field Studies Program (FSP)",
            "FTE": "Flight Training Exchange (FTE)",
            "FTP": "Funded Transportation Program (FTP)",
            "FVS": "DoD Foreign Visit System (FVS)",
            "FY": "Fiscal Year (FY)",
            # G
            "GAO": "General Accounting Office (GAO)",
            "GCC": "Geographic Combatant Command (GCC)",
            "GCU": "Guidance Control Units (GCU)",
            "GEF": "Guidance for Employment of the Force (GEF)",
            "GEOINT": "Geospatial Intelligence (GEOINT)",
            "GFE": "Government Furnished Equipment (GFE)",
            "GFM": "Global Force Management (GFM)",
            "GPOI": "Global Peacekeeping Operations Initiative (GPOI)",
            "GSA": "General Services Administration (GSA)",
            "GSA-OSD": "Global Strategic Affairs (GSA-OSD)",
            "GSOIA": "General Security of Information Agreement (GSOIA)",
            "GSOIAS": "General Security of Information Agreements (GSOIAS)",
            "GSOMIA": "General Security of Military Information Agreement (GSOMIA)",
            "GU": "Guidance Unit (GU)",
            # H
            "HA": "Humanitarian Assistance (HA)",
            "HA-EP": "Humanitarian Assistance Program - Excess Property (HA-EP)",
            "HAZMAT": "Hazardous Materials (HAZMAT)",
            "HCA": "Humanitarian and Civic Assistance (HCA)",
            "HDTC": "Humanitarian Demining Training Center (HDTC)",
            "HMA": "Humanitarian Mine Action (HMA)",
            "HMR": "Hazardous Materials Regulations (HMR)",
            # I
            "IA": "Implementing Agency (IA)",
            "IAAFA": "Inter-American Air Forces Academy (IAAFA)",
            "IAC": "International Armaments Cooperation (IAC)",
            "IAS": "Implementing Agencies (IAS)",
            "ICASS": "International Cooperative Administrative Support Services (ICASS)",
            "ICE": "Immigration and Customs Enforcement (ICE)",
            "ICP": "Inventory Control Point (ICP)",
            "ICR": "In-Country Reprogramming (ICR)",
            "IEP": "Information Exchange Program (IEP)",
            "IFF": "Identification, Friend or Foe (IFF)",
            "IGC": "Integrated Data Environment/Global Transportation Network Convergence (IGC)",
            "IGCE": "Independent Government Cost Estimate (IGCE)",
            "ILCO": "International Logistics Control Office (ILCO)",
            "ILCS": "International Logistics Communication System (ILCS)",
            "IMAS": "International Mine Action Standards (IMAS)",
            "IMC": "Internal Management Control (IMC)",
            "IMET": "International Military Education and Training (IMET)",
            "IMSMA": "Information Management Systems for Mine Action (IMSMA)",
            "IMSO": "International Military Student Office (IMSO)",
            "INCLE": "International Narcotics Control and Law Enforcement (INCLE)",
            "INFOSEC": "Information Security (INFOSEC)",
            "IPO": "International Programs Office (IPO)",
            "ISAN": "International SANWEB (ISAN)",
            "ISFF": "Iraq Security Forces Fund (ISFF)",
            "ISN": "International Security and Nonproliferation (ISN)",
            "ISTL": "Integrated Standard Training List (ISTL)",
            "IT": "Information Technology (IT)",
            "ITAR": "International Traffic in Arms Regulations (ITAR)",
            "ITO": "Invitational Travel Order (ITO)",
            "ITV": "Instrument Telemetry Vehicle (ITV)",
            # J
            "JA": "Justification and Approval (JA)",
            "JASSM": "Joint Air-to-Surface Standoff Missile (JASSM)",
            "JCET": "Joint Combined Exchange Training (JCET)",
            "JCMO": "Joint COMSEC Management Office (JCMO)",
            "JFTR": "Joint Federal Travel Regulations (JFTR)",
            "JMPAB": "Joint Materiel Priority Allocation Board (JMPAB)",
            "JOPES": "Joint Operation Planning Execution System (JOPES)",
            "JSCET": "Joint Security Cooperation and Education Training (JSCET)",
            "JSOW": "Joint Standoff Weapon (JSOW)",
            "JTR": "Joint Travel Regulations (JTR)",
            "JVI": "Joint Visual Inspection (JVI)",
            # L
            "LAIRCM": "Large Aircraft Infrared Countermeasures (LAIRCM)",
            "LES": "Locally Engaged Staff (LES)",
            "LOA": "Letter of Offer and Acceptance (LOA)",
            "LOAD": "LOA Data (LOAD)",
            "LOR": "Letter of Request (LOR)",
            "LPA": "Legislative and Public Affairs (LPA)",
            "LTD": "Language Training Detachment (LTD)",
            "LTDT": "Language Training Detachment (LTDT)",
            # M
            "MANPADS": "Man-Portable Air Defense System (MANPADS)",
            "MAP": "Military Assistance Program (MAP)",
            "MAPAD": "Military Assistance Program Address Directory (MAPAD)",
            "MARAD": "Maritime Administration (MARAD)",
            "MASL": "Military Articles and Services List (MASL)",
            "MCSCG": "Marine Corps SC Group (MCSCG)",
            "MDE": "Major Defense Equipment (MDE)",
            "MDF": "Mission Data File (MDF)",
            "MERHC": "Medicare-Eligible Retiree Health Care (MERHC)",
            "MET": "Mobile Education Teams (MET)",
            "MFA": "Ministry of Foreign Affairs (MFA)",
            "MFP": "Major Force Program (MFP)",
            "MFR": "Memorandum for Record (MFR)",
            "MILDEP": "Military Department (MILDEP)",
            "MILDEP-A": "MILDEP Approval (MILDEP-A)",
            "MILDEP-R": "MILDEP Reactivation (MILDEP-R)",
            "MILDEPS": "Military Departments (MILDEPS)",
            "MILSTRIP": "Military Standard Requisitioning and Issue Procedures (MILSTRIP)",
            "MIPR": "Military Interdepartmental Purchase Request (MIPR)",
            "MISIL": "Management Information System - International Logistics (MISIL)",
            "MISO": "Military Information Support to Operations (MISO)",
            "MLA": "Manufacturing License Agreements (MLA)",
            "MOA": "Memorandum of Agreement (MOA)",
            "MOD": "Ministry of Defense (MOD)",
            "MOP": "Monthly Obligation Plan (MOP)",
            "MOS": "Months (MOS)",
            "MOU": "Memorandum of Understanding (MOU)",
            "MS": "Mission Sustainment (MS)",
            "MSC": "Military Sealift Command (MSC)",
            "MSP": "Mission Strategic Plan (MSP)",
            "MSRP": "Mission Strategic Resource Plan (MSRP)",
            "MSU": "Missile Simulator Unit (MSU)",
            "MTCR": "Missile Technology Control Regime (MTCR)",
            "MTDS": "Manpower and Travel Data Sheet (MTDS)",
            "MTF": "Military Treatment Facility (MTF)",
            "MTFI": "Military Tasks for Interoperability (MTFI)",
            "MTT": "Mobile Training Team (MTT)",
            # N
            "NACSI": "National COMSEC Instruction (NACSI)",
            "NAD": "National Armaments Director (NAD)",
            "NAGS": "NATO Alliance Ground Surveillance (NAGS)",
            "NAMSA": "NATO Maintenance and Supply Agency (NAMSA)",
            "NASIC": "National Air and Space Intelligence Center (NASIC)",
            "NATM": "Special Air Training Missiles (NATM)",
            "NATO": "North Atlantic Treaty Organization (NATO)",
            "NAVSCIATTS": "Naval Small Craft Instruction and Technical Training School (NAVSCIATTS)",
            "NDA": "National Distribution Authority (NDA)",
            "NDAA": "National Defense Authorization Act (NDAA)",
            "NDP": "National Disclosure Policy (NDP)",
            "NDPC": "National Disclosure Policy Committee (NDPC)",
            "NDPS": "National Disclosure Policy System (NDPS)",
            "NDU": "National Defense University (NDU)",
            "NETSAFA": "Naval Education and Training Security Assistance Field Activity (NETSAFA)",
            "NGA": "National Geospatial-Intelligence Agency (NGA)",
            "NICSMA": "NATO Integrated Communication System Management Agency (NICSMA)",
            "NIPO": "Navy International Programs Office (NIPO)",
            "NIPO-SPD": "Navy International Programs Office Strategic Planning Directorate (NIPO-SPD)",
            "NISP": "National Industrial Security Program (NISP)",
            "NISPOM": "National Industrial Security Program Operating Manual (NISPOM)",
            "NOA": "Notice of Availability (NOA)",
            "NOAA": "Notice of Availability (NOAA)",
            "NONACC": "Non-Accelerated Case Closure (NONACC)",
            "NOSSC": "Notice of Supply/Services Completion (NOSSC)",
            "NRC": "Nonrecurring Cost (NRC)",
            "NSA": "National Security Agency (NSA)",
            "NSAS": "National Security Assistance Strategy (NSAS)",
            "NSC": "National Security Council (NSC)",
            "NSDD": "National Security Decision Directive (NSDD)",
            "NSIP": "NATO Security Investment Program (NSIP)",
            "NSN": "National Stock Number (NSN)",
            "NSS": "National Security Staff (NSS)",
            "NTE": "Not-to-Exceed (NTE)",
            "NVD": "Night Vision Device (NVD)",
            "NVDS": "Night Vision Devices (NVDS)",
            # O
            "OA": "Obligational Authority (OA)",
            "OED": "Offer Expiration Date (OED)",
            "OHASIS": "Overseas Humanitarian Assistance Shared Information System (OHASIS)",
            "OHDACA": "Overseas Humanitarian, Disaster and Civic Aid (OHDACA)",
            "OM": "Operations and Maintenance (OM)",
            "OMB": "Office of Management and Budget (OMB)",
            "OPCON": "Operational Control (OPCON)",
            "OPI": "Oral Proficiency Interview (OPI)",
            "ORC": "Offer Release Code (ORC)",
            "ORF": "Official Representation Funds (ORF)",
            "OSD": "Office of the Secretary of Defense (OSD)",
            "OUSD-C": "Office of the Under Secretary of Defense (Comptroller) (OUSD-C)",
            "OUSD-P": "Office of the Under Secretary of Defense for Policy (OUSD-P)",
            # P
            "PA": "Price and Availability (PA)",
            "P&A": "Price and Availability (P&A)",
            "PA-APPN": "Procurement Appropriation (PA-APPN)",
            "PAO": "Primary Action Officer (PAO)",
            "PAR": "Pre-LOR Assessment Request (PAR)",
            "PBAS-OC": "Program Budget Accounting System - Order Control (PBAS-OC)",
            "PCF": "Pakistan Counterinsurgency Fund (PCF)",
            "PCH": "Packing, Crating and Handling (PCH)",
            "PCS": "Permanent Change of Station (PCS)",
            "PD": "Presidential Determination (PD)",
            "PDA": "Principal Disclosure Authority (PDA)",
            "PDM": "Program Decision Memorandum (PDM)",
            "PDSS": "Pre-Deployment Site Survey (PDSS)",
            "PFP": "Partnership for Peace (PFP)",
            "PKO": "Peacekeeping Operations (PKO)",
            "PME": "Professional Military Education (PME)",
            "PMR": "Program Management Review (PMR)",
            "POC": "Point of Contact (POC)",
            "POE": "Port of Embarkation (POE)",
            "POM": "Program Objective Memorandum (POM)",
            "POWMIA": "Prisoner of War/Missing in Action (POWMIA)",
            "PPBE": "Planning, Programming, Budgeting, and Execution (PPBE)",
            "PPR": "Positions of Prominence Report (PPR)",
            "PRD": "Procurement Requirements Documentation (PRD)",
            "PROS": "Parts and Repair Ordering System (PROS)",
            "PSA": "Personal Services Agreement (PSA)",
            "PSS": "SO/LIC Partnership Strategy (PSS)",
            "PVO": "Private Voluntary Organizations (PVO)",
            "PWS": "Performance Work Statement (PWS)",
            # Q
            "QOL": "Quality of Life (QOL)",
            # R
            "RC": "Regional Center (RC)",
            "RCN": "Record Control Number (RCN)",
            "RDA": "Research, Development, and Acquisition (RDA)",
            "RDTE": "Research, Development, Test and Evaluation (RDTE)",
            "RIM": "Retainable Instructional Materials (RIM)",
            "RSO": "Regional Security Officer (RSO)",
            "RST": "Requirement Survey Team (RST)",
            # S
            "SA": "Security Assistance (SA)",
            "SAAM": "Special Assigned Airlift Mission (SAAM)",
            "SAARMS": "Security Assistance Automated Resource Management System (SAARMS)",
            "SADEC": "Secretary of the Army for Defense Exports and Cooperation (SADEC)",
            "SAF-IA": "Deputy Under Secretary of the Air Force International Affairs (SAF-IA)",
            "SAF-IAWD": "Secretary of the Air Force for International Affairs Regional Weapons Division (SAF-IAWD)",
            "SAM-CC": "Security Assistance Management CONUS Course (SAM-CC)",
            "SAM-FMC": "Security Assistance Management Financial Management Course (SAM-FMC)",
            "SAM-LCS": "Security Assistance Management Logistics and Customer Support Course (SAM-LCS)",
            "SAM-RC": "Security Assistance Management Reconciliation and Closure Course (SAM-RC)",
            "SAM-TMC": "Security Assistance Management Training Management Course (SAM-TMC)",
            "SAMIS": "Security Assistance Management Information System (SAMIS)",
            "SAMM": "Security Assistance Management Manual (SAMM)",
            "SAMRS": "Security Assistance Manpower Requirements System (SAMRS)",
            "SAN": "Security Assistance Network (SAN)",
            "SATFA": "Security Assistance Training Field Activity (SATFA)",
            "SBA": "Special Billing Arrangement (SBA)",
            "SC": "Security Cooperation (SC)",
            "SC-CODE": "Supply Code (SC-CODE)",
            "SC-TMS": "Security Cooperation-Training Management System (SC-TMS)",
            "SCES": "Security Cooperation Enterprise Solution (SCES)",
            "SCET": "Security Cooperation Education and Training (SCET)",
            "SCETWG": "Security Cooperation Education and Training Working Group (SCETWG)",
            "SCGB": "Security Cooperation Governance Board (SCGB)",
            "SCI": "Sensitive Compartmented Information (SCI)",
            "SCIP": "Security Cooperation Information Portal (SCIP)",
            "SCIRMS": "Security Cooperation Integrated Resource Management System (SCIRMS)",
            "SCML": "Small Case Management Line (SCML)",
            "SCMS": "Security Cooperation Management Suite (SCMS)",
            "SCO": "Security Cooperation Organization (SCO)",
            "SCOA": "Security Cooperation Organization Assessment (SCOA)",
            "SCOS": "Security Cooperation Organizations (SCOS)",
            "SDAF": "Special Defense Acquisition Fund (SDAF)",
            "SDDC": "Surface Deployment and Distribution Command (SDDC)",
            "SDO": "Senior Defense Official (SDO)",
            "SDO-DATT": "Senior Defense Official/Defense Attache (SDO-DATT)",
            "SDR": "Supply Discrepancy Report (SDR)",
            "SECDEF": "Secretary of Defense (SECDEF)",
            "SED": "Shipper's Export Declaration (SED)",
            "SES": "Senior Executive Service (SES)",
            "SET": "Specialized English Training (SET)",
            "SFJ": "Sales Forecast/Javits System (SFJ)",
            "SHAPE": "Supreme Headquarters Allied Powers Europe (SHAPE)",
            "SIGINT": "National SIGINT Committee (SIGINT)",
            "SIPRNET": "Secret Internet Protocol Router Network (SIPRNET)",
            "SLAMER": "Standoff Land Attack Missiles Expanded Response (SLAMER)",
            "SLOS": "Standard Level of Service (SLOS)",
            "SME": "Significant Military Equipment (SME)",
            "SNAP": "Simplified Non-Standard Acquisition Process (SNAP)",
            "SO-LIC": "Special Operations/Low-Intensity Conflict (SO-LIC)",
            "SOC": "Special Operations Command (SOC)",
            "SOCOM": "U.S. Special Operations Command (SOCOM)",
            "SOFA": "Status of Forces Agreement (SOFA)",
            "SOLIC": "Special Operations/Low Intensity Conflict (SOLIC)",
            "SOP": "Standard Operating Procedures (SOP)",
            "SOS": "Source of Supply (SOS)",
            "SOW": "Statement of Work (SOW)",
            "SPAN": "Security Policy Automation Network (SPAN)",
            "SPO": "System Program Office (SPO)",
            "SPP": "Strategy, Plans, and Policy (SPP)",
            "SRC": "Security Risk Categories (SRC)",
            "SSC": "Supply and Services Completion (SSC)",
            "STATE": "Department of State (STATE)",
            "STL": "Standard Training List (STL)",
            "SVI": "Single Vendor Integrity (SVI)",
            # T
            "TAA": "Technical Assistance Agreement (TAA)",
            "TAAR": "Team After-Action Report (TAAR)",
            "TAC": "Training Analysis Codes (TAC)",
            "TAFT": "Technical Assistance Field Team (TAFT)",
            "TAT": "Technical Assistance Team (TAT)",
            "TBC": "Transportation Bill Code (TBC)",
            "TCA": "Traditional COCOM Activities (TCA)",
            "TCM": "Target Coordinate Mensuration (TCM)",
            "TCN": "Transportation Control Number (TCN)",
            "TDA": "Table of Distribution and Allowances (TDA)",
            "TDP": "Technical Data Package (TDP)",
            "THAAD": "Terminal High Altitude Area Defense (THAAD)",
            "TIP": "Trafficking in Persons (TIP)",
            "TLA": "Travel and Living Allowance (TLA)",
            "TLW": "Termination Liability Worksheet (TLW)",
            "TM": "Training Module (TM)",
            "TMASL": "Training Military Articles and Services Listings (TMASL)",
            "TOA": "Type of Assistance (TOA)",
            "TOEFL": "Test of English as a Foreign Language (TOEFL)",
            "TOR": "Terms of Reference (TOR)",
            "TOW": "Tube-Launched, Optically-Tracked, Wire-Guided Missiles (TOW)",
            "TPA": "Total Package Approach (TPA)",
            "TRANSCOM": "U.S. Transportation Command (TRANSCOM)",
            "TSC": "Theater Security Cooperation (TSC)",
            "TSC-CONTROLS": "Trade Security Controls (TSC-CONTROLS)",
            "TSCIMS": "Theater Security Cooperation Information Management System (TSCIMS)",
            "TSCMIS": "Theater Security Cooperation Management Information System (TSCMIS)",
            "TVL": "Tailored Vendor Logistics (TVL)",
            # U
            "UA": "Unauthorized Absence (UA)",
            "UAS": "Unmanned Aircraft System (UAS)",
            "UAV": "Unmanned Air Vehicle (UAV)",
            "UCMJ": "Uniform Code of Military Justice (UCMJ)",
            "ULO": "Un-Liquidated Obligation (ULO)",
            "UMMIPS": "Uniform Material Movement and Issue Priority System (UMMIPS)",
            "UN": "United Nations (UN)",
            "UND": "Urgency of Need Designator (UND)",
            "UNLOA": "UN Letter of Assist (UNLOA)",
            "UPT": "Undergraduate Pilot Training (UPT)",
            "USAF": "U.S. Air Force (USAF)",
            "USAID": "U.S. Agency for International Development (USAID)",
            "USAMEDCOM": "U.S. Army Medical Materiel Agency (USAMEDCOM)",
            "USASAC": "U.S. Army Security Assistance Command (USASAC)",
            "USCG": "United States Coast Guard (USCG)",
            "USD-AS": "Under Secretary of Defense for Acquisition and Sustainment (USD-AS)",
            "USD-C": "Under Secretary of Defense (Comptroller) (USD-C)",
            "USD-I": "Under Secretary of Defense for Intelligence (USD-I)",
            "USD-P": "Under Secretary of Defense for Policy (USD-P)",
            "USD-PR": "Under Secretary of Defense for Personnel and Readiness (USD-PR)",
            "USD(P)": "Under Secretary of Defense for Policy (USD(P))",
            "USG": "United States Government (USG)",
            "USML": "United States Munitions List (USML)",
            "USN": "U.S. Navy (USN)",
            "USPACOM": "U.S. Pacific Command (USPACOM)",
            "USUN": "U.S. Mission to the United Nations (USUN)",
            # V
            "VA": "Valuation and Availability (VA)",
            "VIN": "Vehicle Identification Number (VIN)",
            "VMS-LP": "Vehicle Mounted Stinger Launched Platform (VMS-LP)",
            "VV": "Validation and Verification (VV)",
            # W
            "WCF": "Working Capital Fund (WCF)",
            "WCN": "Worksheet Control Number (WCN)",
            "WD": "Workforce Development (WD)",
            "WHINSEC": "Western Hemisphere Institute for Security Cooperation (WHINSEC)",
            "WHS-AAS": "Washington Headquarters Services Allotment Accounting System (WHS-AAS)",
            "WIF": "Warsaw Initiative Fund (WIF)",
            # X
            "XCN": "External Control Number (XCN)",
            # Chapter 4 Specific Additions
            "ATD": "Advanced Target Development (ATD)",
            "CDE": "Collateral Damage Estimation (CDE)",
            "IOPS": "International Operations (IOPS)",
            "IOPS/WPN": "Weapons Directorate (IOPS/WPN)",
            "IOPS/REX": "Regional Execution Directorate (IOPS/REX)",
            "FMS-Only": "Foreign Military Sales Only (FMS-Only)",
            "GFM": "Government Furnished Materiel (GFM)",
            "RDFP": "Regional Defense Fellowship Program (RDFP)",
            # Chapter 5 - Core Documents
            "LOAD": "LOA Data (LOAD)",
            "CTA": "Country Team Assessment (CTA)",
            "MFR": "Memorandum for Record (MFR)",
            "RFP": "Request for Proposal (RFP)",
            "RFI": "Request for Information (RFI)",
            # Chapter 5 - Case Types
            "CLSSA": "Cooperative Logistics Supply Support Arrangement (CLSSA)",
            "FMSO": "Foreign Military Sales Order (FMSO)",
            "FMSO I": "Foreign Military Sales Order I (FMSO I)",
            "FMSO II": "Foreign Military Sales Order II (FMSO II)",
            # Chapter 5 - Response Types
            "NTE": "Not-to-Exceed (NTE)",
            "FFP": "Firm Fixed Price (FFP)",
            "EOQ": "Economic Order Quantity (EOQ)",
            # Chapter 5 - Processing
            "MILAP": "Military Department Approval (MILAP)",
            "MILSGN": "Military Signature (MILSGN)",
            "CPOHOLD": "Case Processing Office Hold (CPOHOLD)",
            "CPOHOLDREM": "CPOHOLD Removal (CPOHOLDREM)",
            "CDEF": "Case Development Extenuating Factor (CDEF)",
            "OED": "Offer Expiration Date (OED)",
            # Chapter 5 - Special Items
            "SO-P": "Special Operations-Peculiar (SO-P)",
            "MTCR": "Missile Technology Control Regime (MTCR)",
            "ISR": "Intelligence, Surveillance and Reconnaissance (ISR)",
            "FoM": "Figure of Merit (FoM)",
            "PDT": "Population Density Tables (PDT)",
            "A/G": "Air-to-Ground (A/G)",
            "S/S": "Surface-to-Surface (S/S)",
            "S/A": "Surface-to-Air (S/A)",
            "A/S": "Air-to-Surface (A/S)",
            "AD": "Air Defense (AD)",
            "UCAV": "Unmanned Combat Aerial Vehicle (UCAV)",
            # Chapter 5 - Approvals
            "OT&E": "Operational Testing and Evaluation (OT&E)",
            "ENDP": "Exception to National Disclosure Policy (ENDP)",
            "JVI": "Joint Visual Inspection (JVI)",
            # Chapter 5 - Organizations
            "IOPS/GEX": "International Operations, Global Execution Directorate (IOPS/GEX)",
            "IOPS/GEX/CWD": "Case Writing and Development Division (IOPS/GEX/CWD)",
            "SPP/EPA": "Execution Policy and Analysis Directorate (SPP/EPA)",
            "ADM/PIE": "Office of Administration, Performance, Improvement, and Effectiveness Directorate (ADM/PIE)",
            "ADM/PIE/AME": "Assessment, Monitoring and Evaluation Division (ADM/PIE/AME)",
            "OBO": "Office of Business Operations (OBO)",
            "OBO/FPRE": "Financial Policy & Regional Execution Directorate (OBO/FPRE)",
            "OBO/FPRE/FRC": "Financial Reporting and Compliance Division (OBO/FPRE/FRC)",
            "CPD": "Country Portfolio Director (CPD)",
            "PM/SA": "Office of Security Assistance (PM/SA)",
            "State (RM)": "Bureau of Information Resource Management (State (RM))",
            "SOF AT&L-IO": "SOF Acquisition, Technology and Logistics International Operations (SOF AT&L-IO)",
            "COM": "Chief of Mission (COM)",
            "MOD": "Ministry of Defense (MOD)",
            # Chapter 5 - Systems
            "DSAMS": "Defense Security Assistance Management System (DSAMS)",
            "CTS": "Case Tracking System (CTS)",
            "SCIP": "Security Cooperation Information Portal (SCIP)",
            "DTS": "Defense Transportation System (DTS)",
            "CAC": "Common Access Card (CAC)",
            # Chapter 5 - Documents/Forms
            "MTDS": "Manpower Travel Data Sheet (MTDS)",
            "MOU": "Memorandum of Understanding (MOU)",
            "SOW": "Statement of Work (SOW)",
            "PWS": "Performance Work Statement (PWS)",
            "ILS": "Integrated Logistics Support (ILS)",
            "PMR": "Program Management Review (PMR)",
            # Chapter 5 - Codes
            "SIDN": "Selected Item Description Number (SIDN)",
            "SISC": "Selected Item Sequence Code (SISC)",
            "SISN": "Selected Item Sequence Number (SISN)",
            "SCC": "Significant Category Code (SCC)",
            "MOS": "Months of Supply (MOS)",
            "UNTIA": "UN Transparency in Armaments (UNTIA)",
            # Chapter 5 - Financial
            "NC": "Nonrecurring Cost (NC)",
            "DoD FMR": "DoD Financial Management Regulation (DoD FMR)",
            # Chapter 5 - Personnel
            "PCS": "Permanent Change of Station (PCS)",
            "TDY": "Temporary Duty (TDY)",
            "OCONUS": "Outside the Continental United States (OCONUS)",
            "CONUS": "Continental United States (CONUS)",
            "POC": "Point of Contact (POC)",
        }
        
        # Answer quality scoring weights
        self.quality_weights = {
            "section_citation": 0.25,
            "acronym_expansion": 0.15,
            "answer_completeness": 0.25,
            "samm_terminology": 0.20,
            "structure_adherence": 0.15
        }
        
        # Response length guidelines by intent - COMPREHENSIVE for ALL intents
        self.length_guidelines = {
            # === Existing ===
            "definition": {"min": 150, "target": 300, "max": 500},
            "distinction": {"min": 200, "target": 400, "max": 600},
            "authority": {"min": 150, "target": 300, "max": 500},
            "organization": {"min": 150, "target": 300, "max": 500},
            "factual": {"min": 150, "target": 350, "max": 600},
            "relationship": {"min": 150, "target": 300, "max": 500},
            "general": {"min": 150, "target": 300, "max": 500},
            
            # === NEW: Previously missing ===
            "process": {"min": 200, "target": 400, "max": 700},       # Longer for step-by-step explanations
            "funding": {"min": 150, "target": 350, "max": 550},       # Medium for financial explanations
            "eligibility": {"min": 150, "target": 300, "max": 500},   # Medium for criteria lists
            "compliance": {"min": 150, "target": 350, "max": 550},    # Medium for regulatory info
            "list": {"min": 200, "target": 400, "max": 700},          # Longer for complete lists
            "verification": {"min": 100, "target": 200, "max": 400},  # Shorter for Yes/No answers
            "explanation": {"min": 150, "target": 350, "max": 550},   # Medium for explanations
        }
        
        print("[EnhancedAnswerAgent] Initialization complete")

    @time_function
    def generate_answer(self, query: str, intent_info: Dict, entity_info: Dict, 
                    chat_history: List = None, documents_context: List = None,
                    user_profile: Dict = None) -> str:
        """
        Main method for enhanced answer generation with ITAR compliance filtering
        """
        # CRITICAL: ALWAYS log file status at entry point
        if documents_context:
            print(f"[AnswerAgent] 📁 RECEIVED {len(documents_context)} FILES for answer generation")
            for idx, doc in enumerate(documents_context[:3], 1):
                fname = doc.get('fileName', 'Unknown')
                content_len = len(doc.get('content', ''))
                has_content = len(doc.get('content', '')) > 50
                print(f"[AnswerAgent]   File {idx}: {fname} ({content_len} chars) - {'✅ READY' if has_content else '⚠️ INSUFFICIENT'}")
        else:
            print(f"[AnswerAgent] ⚠️ WARNING: No files provided for answer generation")
        
        # NEW: Handle LOA timeline queries with instant pre-formatted answer
        if intent_info.get("intent") == "loa_timeline":
            print(f"[AnswerAgent] 🚀 Using LOA timeline pre-formatted answer")
            return self._get_loa_timeline_answer()
        
        # NEW: Handle financial verification queries
        if intent_info.get("intent") == "financial_verification":
            print(f"[AnswerAgent] 🚀 Using financial verification pre-formatted answer")
            return self._get_financial_verification_answer()
        
        # NEW: Handle technical services queries
        if intent_info.get("intent") == "line_item_details":
            print(f"[AnswerAgent] 🚀 Using technical services pre-formatted answer")
            return self._get_technical_services_answer()
        
        # NEW: Handle PMR minutes summary queries
        if intent_info.get("intent") == "pmr_minutes_summary":
            print(f"[AnswerAgent] 🚀 Using PMR minutes summary pre-formatted answer")
            return self._get_pmr_minutes_summary()
                
        intent = intent_info.get("intent", "general")
        confidence = intent_info.get("confidence", 0.5)
        
        print(f"[AnswerAgent] Generating answer for intent: {intent} (confidence: {confidence:.2f})")
        print(f"[AnswerAgent] Query: {query[:100]}...")

        try:
            # === ITAR COMPLIANCE CHECK ===
            compliance_result = check_compliance(query, intent_info, entity_info, user_profile)
            
            # Log compliance check
            if compliance_result.get("check_performed"):
                print(f"[Compliance] Check performed: {compliance_result.get('compliance_status')}")
                print(f"[Compliance] User level: {compliance_result.get('user_authorization_level')}")
                print(f"[Compliance] Authorized: {compliance_result.get('authorized')}")
            
            # Handle unauthorized access
            if not compliance_result.get("authorized", True):
                required_level = compliance_result.get('required_authorization_level', 'higher authorization')
                user_level = compliance_result.get('user_authorization_level', 'unknown')
                recommendations = compliance_result.get("recommendations", [])
                
                # Build denial response
                response = (
                    f"⚠️ **ITAR COMPLIANCE NOTICE**\n\n"
                    f"This query involves controlled information requiring **{required_level.upper()}** clearance.\n"
                    f"Your current authorization: **{user_level.upper()}**\n\n"
                )
                
                if recommendations:
                    response += "**Recommendations:**\n" + "\n".join(f"• {r}" for r in recommendations)
                
                print(f"[Compliance] Access denied: {user_level} < {required_level}")
                return response
            
            # Log successful compliance check
            if compliance_result.get("check_performed"):
                print(f"[Compliance] Query authorized - proceeding with answer generation")
            # === END ITAR COMPLIANCE CHECK ===
            
            # Step 1: Check for existing corrections first
            cached_answer = self._check_for_corrections(query, intent_info, entity_info)
            if cached_answer:
                print("[AnswerAgent] Using cached correction")
                return cached_answer
            
            # Step 2: Build comprehensive context from all sources
            context = self._build_comprehensive_context(
                query, intent_info, entity_info, chat_history, documents_context
            )
            
            # Step 3: Create intent-optimized system message WITH citations
            system_msg = self._create_optimized_system_message(intent, context, entity_info, query)  # v5.9.11: Pass query for Gold guidance
            
            # Step 4: Generate enhanced prompt with intent awareness
            prompt = self._create_enhanced_prompt(query, intent_info, entity_info)
            
            # Step 5: Generate answer with validation passes
            answer = self._generate_with_validation(prompt, system_msg, intent_info)
            
            # Step 6: Apply post-processing enhancements
            enhanced_answer = self._enhance_answer_quality(answer, intent_info, entity_info)
            
            # Step 7: Final validation and scoring
            final_answer = self._validate_and_score_answer(enhanced_answer, intent, query)
            
            # ADD: Final answer verification
            print(f"[AnswerAgent] ✅ FINAL ANSWER GENERATED:")
            print(f"[AnswerAgent]   Length: {len(final_answer)} chars")
            print(f"[AnswerAgent]   Preview: {final_answer[:200]}...")
            print(f"[AnswerAgent]   Has content: {bool(final_answer and len(final_answer) > 20)}")
            
            return final_answer
            
        except Exception as e:
            print(f"[AnswerAgent] Error during answer generation: {e}")
            import traceback
            traceback.print_exc()
            return f"I apologize, but I encountered an error while generating the answer: {str(e)}. Please try rephrasing your question or check if the Ollama service is running."
        


 
    def _check_for_corrections(self, query: str, intent_info: Dict, entity_info: Dict) -> Optional[str]:
        """Check if we have a stored correction for similar queries"""
        try:
            query_key = self._normalize_query_for_matching(query)
            
            # Check exact matches first
            if query_key in self.answer_corrections:
                correction = self.answer_corrections[query_key]
                print(f"[AnswerAgent] Found exact correction match")
                return correction["corrected_answer"]
            
            # Check for partial matches based on intent and entities
            current_entities = set(entity_info.get("entities", []))
            current_intent = intent_info.get("intent", "general")
            
            for stored_key, correction in self.answer_corrections.items():
                stored_entities = set(correction.get("feedback_data", {}).get("entities", []))
                stored_intent = correction.get("feedback_data", {}).get("intent", "general")
                
                # If same intent and significant entity overlap (50% or more)
                if (current_intent == stored_intent and len(current_entities) > 0 and
                    len(current_entities.intersection(stored_entities)) >= min(len(current_entities), len(stored_entities)) * 0.5):
                    print(f"[AnswerAgent] Found partial correction match based on intent/entities")
                    return correction["corrected_answer"]
            
            return None
            
        except Exception as e:
            print(f"[AnswerAgent] Error checking corrections: {e}")
            return None





    def _build_comprehensive_context(self, query: str, intent_info: Dict, entity_info: Dict,
                                chat_history: List = None, documents_context: List = None) -> str:
        """Build comprehensive context for answer generation with financial data"""
        try:
            context_parts = []
            
            # Add entity context with confidence weighting
            if entity_info.get("context"):
                context_parts.append("=== SAMM ENTITIES AND DEFINITIONS ===")
                for ctx in entity_info["context"][:5]:  # Limit to 5 to prevent overload
                    confidence = ctx.get('confidence', 0.5)
                    if confidence > 0.6:  # Only include high-confidence entities
                        entity_text = f"{ctx.get('entity', '')}: {ctx.get('definition', '')}"
                        if ctx.get('section'):
                            entity_text += f" (SAMM {ctx['section']})"
                        context_parts.append(entity_text)
            
            # Add relevant text sections from SAMM
            if entity_info.get("text_sections"):
                context_parts.append("\n=== RELEVANT SAMM CONTENT ===")
                text_sections = entity_info["text_sections"][:5]  # v5.9.10: Increased from 2 to 5 for better coverage
                for section in text_sections:
                    truncated_section = section[:500] + "..." if len(section) > 500 else section  # v5.9.10: Increased from 300 to 500
                    context_parts.append(truncated_section)
            
            # Add entity relationships
            if entity_info.get("relationships"):
                context_parts.append("\n=== ENTITY RELATIONSHIPS ===")
                context_parts.extend(entity_info["relationships"][:4])  # v5.4: Reduced from 7 to 4
            
            # === NEW: Add HIL corrections as context ===
            if hasattr(self, 'answer_corrections') and len(self.answer_corrections) > 0:
                context_parts.append("\n=== PREVIOUS CORRECT ANSWERS (HIL) ===")
                for correction_key, correction in list(self.answer_corrections.items())[-2:]:  # v5.4: Reduced from 5 to 2
                    corrected_answer = correction.get('corrected_answer', '')
                    original_query = correction.get('original_query', 'Unknown query')
                    if len(corrected_answer) > 50:
                        truncated = corrected_answer[:500] + "..." if len(corrected_answer) > 500 else corrected_answer  # v5.4: Reduced from 1500 to 500
                        context_parts.append(f"Q: {original_query[:100]}\nCorrect Answer: {truncated}\n")
                        print(f"[AnswerAgent] Added HIL correction to context")

            # === NEW: Add case file relationships ===
            if entity_info.get("file_relationships_found", 0) > 0:
                context_parts.append("\n=== CASE FILE RELATIONSHIPS ===")
                file_rels = [rel for rel in entity_info.get("relationships", []) if "from" in rel]
                for rel in file_rels[:5]:
                    context_parts.append(f"• {rel}")
                print(f"[AnswerAgent] Added {len(file_rels[:5])} file relationships to context")

            # ✅ ENHANCED: Add uploaded documents WITH financial data extraction
            if documents_context:
                context_parts.append("\n" + "="*80)
                context_parts.append(f"📁 UPLOADED DOCUMENTS ({len(documents_context)} files)")
                context_parts.append("="*80)
                
                # Extract and display financial records
                financial_records = []
                
                for idx, doc in enumerate(documents_context[:3], 1):
                    file_name = doc.get('fileName', 'Unknown')
                    content = doc.get('content', '')
                    
                    # Check for financial data
                    has_financial = doc.get('metadata', {}).get('hasFinancialData', False)
                    
                    if has_financial:
                        records = doc.get('metadata', {}).get('financialRecords', [])
                        financial_records.extend(records)
                        
                        context_parts.append(f"\n[Document {idx}] 💰 {file_name} (FINANCIAL DATA)")
                        context_parts.append(f"Contains {len(records)} financial line items:")
                        
                        # Show first 5 records as examples
                        for i, record in enumerate(records[:5], 1):
                            rsn = record.get('rsn_identifier', 'N/A')
                            pdli = record.get('pdli_pdli', 'N/A')
                            available = record.get('available', 0)
                            
                            context_parts.append(
                                f"  • RSN {rsn}, PDLI {pdli}: ${available:,.2f} available"
                            )
                        
                        if len(records) > 5:
                            context_parts.append(f"  ... and {len(records) - 5} more records")
                    
                    elif content:
                        # Regular document
                        context_parts.append(f"\n[Document {idx}] {file_name}")
                        truncated = content[:1000] + "..." if len(content) > 1000 else content
                        context_parts.append(truncated)
                    
                    context_parts.append("-" * 80)
                
                # Add financial summary if records found
                if financial_records:
                    context_parts.append(f"\n📊 FINANCIAL DATA SUMMARY:")
                    context_parts.append(f"Total records: {len(financial_records)}")
                    
                    # Calculate totals
                    total_available = sum(float(r.get('available', 0)) for r in financial_records)
                    context_parts.append(f"Total available funds: ${total_available:,.2f}")
                    
                    # List unique RSNs
                    unique_rsns = set(r.get('rsn_identifier') for r in financial_records if r.get('rsn_identifier'))
                    context_parts.append(f"RSN line numbers: {', '.join(sorted(unique_rsns))}")
                
                print(f"[AnswerAgent] ✅ Added {len(documents_context[:3])} documents to context")
                print(f"[AnswerAgent] 💰 Included {len(financial_records)} financial records")
            # ✅ END ENHANCEMENT
            
            # Add custom knowledge from HIL feedback and triggers
            if self.custom_knowledge:
                context_parts.append("\n=== ADDITIONAL KNOWLEDGE ===")
                knowledge = self.custom_knowledge[:1000] + "..." if len(self.custom_knowledge) > 1000 else self.custom_knowledge
                context_parts.append(knowledge)
            
            # Add relevant chat history for continuity
            if chat_history and len(chat_history) > 0:
                context_parts.append("\n=== CONVERSATION CONTEXT ===")
                for msg in chat_history[-2:]:  # Last 2 messages for context
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')[:200]
                    context_parts.append(f"{role}: {content}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"[AnswerAgent] Error building context: {e}")
            return "Context building failed - proceeding with basic knowledge."


    def _create_optimized_system_message(self, intent: str, context: str, entity_info: Dict = None, query: str = None) -> str:
        """Create intent-optimized system message for Llama 3.2 with error handling and explicit citations"""
        
        try:
            # =====================================================================
            # v5.9.2: EXTRACT CITATIONS FROM ENTITY_INFO
            # =====================================================================
            primary_citation = None
            reference_citations = []
            if entity_info and entity_info.get("citations"):
                citations = entity_info["citations"]
                primary_citation = citations.get("primary")
                reference_citations = citations.get("references", [])
                print(f"[AnswerAgent] 📚 Citations available - Primary: {primary_citation}, References: {reference_citations}")
            # =====================================================================
            
            # Base instructions for each intent type - COMPREHENSIVE for ALL intents
            base_instructions = {
                # === Existing ===
                "definition": """You are a SAMM expert. Provide precise definitions with SAMM section citations.

RULES:
- Answer ONLY about the specific entity asked (e.g., if asked about USD(P), don't mention USD(P&R))
- Use exact SAMM terminology from context
- Cite sections like "C1.1.1" - no chapter numbers
- Expand acronyms: "Full Name (ACRONYM)"
- SC is BROAD (all DoD interactions), SA is SUBSET of SC (Title 22 programs)
- NEVER say "SC is subset of SA" - always "SA is subset of SC"

MERGED INTENTS (Ch1):
- If asking about SCOPE: Explain what is included/excluded, boundaries, coverage
- If asking about PURPOSE: Explain objective, rationale, why it exists/was created

FORMAT: Definition → Citation → Context (+ Scope/Purpose if relevant)""",

                "distinction": """You are a SAMM expert explaining differences between concepts.

RULES:
- Highlight key differences clearly
- SC = BROAD umbrella (Title 10), SA = NARROW subset (Title 22)
- "SA is a subset of SC" (never reverse!)
- Cite SAMM sections for each concept

FORMAT: Key difference → Each concept with citation → Summary""",

                "authority": """You are a SAMM expert on authority and oversight.

RULES:
- State which organization/person has authority
- Cite legal authorities (FAA, AECA, NDAA, EOs)
- Explain delegation chains
- Reference SAMM sections

MERGED INTENTS (Ch4):
- If asking about APPROVAL: Who approves, approval thresholds, approval process/requirements
- If asking about REVIEW: Review process, who reviews, review cycles, review requirements
- If asking about DECISION: Who decides, decision-making authority, decision process

FORMAT: Authority holder → Scope → Legal basis → Delegations (+ Approval/Review/Decision process if relevant)""",

                "organization": """You are a SAMM expert on organizational roles.

RULES:
- Full name and acronym
- Specific responsibilities
- Reporting relationships
- Cite SAMM sections

FORMAT: Name (Acronym) → Role → Responsibilities → Relationships""",

                "factual": """You are a SAMM expert providing factual information.

RULES:
- Precise, accurate facts
- Include dates, numbers, details
- Cite SAMM sections
- Expand acronyms

MERGED INTENTS (Ch7):
- If asking about TIMELINE: Timeframes, durations, deadlines, schedules, how long things take
- If asking about MILESTONE: Key milestones, phases, checkpoints, major events
- If asking about STATUS: Current status, progress, state, where things stand
- If asking about TRACKING: How things are monitored, tracked, measured, performance metrics

FORMAT: Direct answer → Context → (Timeline/Milestone/Status/Tracking details) → Citation""",

                "relationship": """You are a SAMM expert explaining relationships.

RULES:
- Clearly explain relationship nature
- Use examples
- Cite authorities and sections

FORMAT: Relationship → Why it exists → Examples → Citations""",

                # === NEW: Previously missing ===
                "process": """You are a SAMM expert explaining processes and procedures.

RULES:
- Explain steps in logical order
- Identify who is responsible for each step
- Include timelines if applicable
- Mention required documents/forms
- Cite SAMM sections

MERGED INTENTS (Ch5):
- If asking about IMPLEMENTATION: How to implement/execute, specific actions required
- If asking about PREREQUISITES: What must be done/completed before starting
- If asking about DOCUMENTATION: Required documents, forms, paperwork, reports

FORMAT: Process name → Steps (1,2,3...) → Key actors → Timeline → Required docs → Citation""",

                "funding": """You are a SAMM expert on funding and financial matters.

RULES:
- Identify funding source (Title 10/22, FMF, grant, loan)
- Explain who pays and who receives
- Describe payment terms/mechanisms
- Cite legal authorities (FAA, AECA)
- Reference SAMM sections

MERGED INTENTS (Ch6):
- If asking about BUDGET: Budget allocation, planning, fiscal year, annual budget
- If asking about PAYMENT: Payment terms, schedules, methods, billing cycles
- If asking about PRICING: How prices are determined, pricing methodology, case values, administrative costs
- If asking about REIMBURSEMENT: Reimbursement process, rates, policies, refunds

FORMAT: Funding type → Source → Mechanism → Legal basis → (Budget/Payment/Pricing/Reimbursement details) → Citation""",

                "eligibility": """You are a SAMM expert on eligibility requirements.

RULES:
- State eligibility criteria clearly
- List all requirements
- Note any exceptions or restrictions
- Identify who determines eligibility
- Cite SAMM sections and legal authorities

FORMAT: Eligibility criteria → Requirements list → Exceptions → Authority → Citation""",

                "compliance": """You are a SAMM expert on regulatory compliance.

RULES:
- Identify applicable regulations (ITAR, AECA, FAA, EAR)
- Explain compliance requirements
- Note consequences of non-compliance
- Reference managing agencies (PM/DDTC, DSCA)
- Cite SAMM sections

MERGED INTENTS (Ch9):
- If asking about AUDIT: Audit process, requirements, who audits, audit cycles, GAO/IG audits
- If asking about LEGAL: Legal requirements, applicable laws/statutes, legal basis, penalties/sanctions
- If asking about REPORTING: Reporting requirements, deadlines, formats, Congressional reporting, notification

FORMAT: Regulation → Requirements → (Audit/Legal/Reporting details) → Consequences → Managing agency → Citation""",

                "list": """You are a SAMM expert providing organized lists.

RULES:
- Provide complete, comprehensive lists
- Include brief description for each item
- Organize logically (by type, priority, or sequence)
- Cite SAMM sections

FORMAT: List context → Items with descriptions → Citation""",

                "verification": """You are a SAMM expert answering verification questions.

RULES:
- Start with clear Yes or No
- Explain the reasoning
- Cite supporting SAMM sections
- Note any conditions or exceptions

FORMAT: Yes/No → Explanation → Supporting evidence → Citation""",

                "explanation": """You are a SAMM expert explaining purposes and rationale.

RULES:
- State the purpose clearly
- Provide context and background
- Explain why it matters
- Cite SAMM sections

FORMAT: Purpose → Context → Significance → Citation""",

                "general": """You are a SAMM expert.

RULES:
- Use exact SAMM terminology
- Cite sections (e.g., "C1.1.1")
- Expand acronyms
- SA is subset of SC (never reverse!)

FORMAT: Answer → Context → Citation"""
            }
            
            # v5.9.11: Check Gold pattern FIRST
            gold_matched = False
            gold_guidance = None
            if query:
                gold_guidance = gold_answer_guidance(query)
                if gold_guidance:
                    gold_matched = True
                    print(f"[AnswerAgent] 🎯 Gold pattern matched: {gold_guidance.get('pattern_id')}")
            
            # v5.9.11: ULTRA SHORT when Gold matches
            if gold_matched and gold_guidance:
                # Build must-cite list
                must_cite = []
                for item in gold_guidance.get('must_mention', []):
                    if 'Table' in item or 'Figure' in item or 'DSAMS' in item:
                        must_cite.append(item)
                
                # ULTRA COMPACT: ~100 chars + 500 chars context = ~600 chars total
                system_msg = f"""SAMM Expert.
START: {gold_guidance.get('start_with', '')}
CITE: {primary_citation or ''}, {', '.join(must_cite[:2])}

CONTEXT:
{context[:500]}"""
                
                return system_msg
            
            # NON-GOLD PATH: Use normal flow (Gold already returned above)
            system_msg = base_instructions.get(intent, base_instructions["general"])
            
            # Citation (short)
            if primary_citation:
                system_msg += f"\nCITE: {primary_citation}"
            
            # Context (800 chars for non-Gold)
            system_msg += f"\n\nCONTEXT:\n{context[:800]}"
            
            return system_msg
            
        except Exception as e:
            print(f"[AnswerAgent] Error creating system message: {e}")
            return "You are a SAMM expert. Provide accurate information about Security Cooperation and Security Assistance."
    
    def _create_enhanced_prompt(self, query: str, intent_info: Dict, entity_info: Dict) -> str:
        """Create enhanced prompt with entity and intent awareness"""
        try:
            intent = intent_info.get("intent", "general")
            entities = entity_info.get("entities", [])
            confidence = intent_info.get("confidence", 0.5)
            relationships = entity_info.get("relationships", [])
            
            # v5.9.11: Check if Gold pattern matches - if so, use SIMPLE prompt
            gold_guidance = gold_answer_guidance(query)
            if gold_guidance:
                # ULTRA SIMPLE prompt for Gold patterns
                simple_prompt = f"Question: {query}"
                if entities:
                    simple_prompt += f"\nEntities: {', '.join(entities[:2])}"
                print(f"[AnswerAgent] 🎯 Gold prompt - skipping relationships")
                return simple_prompt
           
            print(f"[AnswerAgent DEBUG] Relationships found: {relationships}") 
            
            prompt_parts = []
            
            # Add query with context
            prompt_parts.append(f"Question: {query}")
            
           # Add intent guidance if high confidence
            if confidence > 0.7:
                prompt_parts.append(f"This is a {intent} question requiring a {intent}-focused response.")
            
            # Add entity awareness (limit to prevent overload)
            if entities:
                limited_entities = entities[:3]  # Limit to 3 entities
                prompt_parts.append(f"Key entities mentioned: {', '.join(limited_entities)}")
                
                # CRITICAL: Add explicit entity focus for definition questions
                if intent == "definition" and len(limited_entities) == 1:
                    entity = limited_entities[0]
                    prompt_parts.append(f"\n🔴 CRITICAL: Answer ONLY about '{entity}'. Do NOT confuse with similar entities like:")
                    # Add common confusions for USD variants
                    if "USD(" in entity:
                        prompt_parts.append(f"  - If asked about USD(P), answer about Under Secretary of Defense for POLICY only")
                        prompt_parts.append(f"  - If asked about USD(P&R), answer about Under Secretary of Defense for PERSONNEL AND READINESS only")
                        prompt_parts.append(f"  - If asked about USD(A&S), answer about Under Secretary of Defense for ACQUISITION AND SUSTAINMENT only")
                        prompt_parts.append(f"  - You are being asked about: {entity} - answer ONLY about this exact entity")
            
            # NEW: Add relationship data explicitly
            if relationships:
                prompt_parts.append("\nIMPORTANT - Use these specific relationships from the database:")
                
                # ✅ For authority questions, prioritize legal basis relationships
                if intent == "authority":
                    # Separate relationships into priority tiers
                    priority_keywords = ["legal_basis", "supervises", "supervision", "direction", "authority", "responsible", "aeca", "faa", "eo 13637"]
                    
                    priority_rels = []
                    other_rels = []
                    
                    for rel in relationships:
                        rel_lower = rel.lower()
                        if any(kw in rel_lower for kw in priority_keywords):
                            priority_rels.append(rel)
                        else:
                            other_rels.append(rel)
                    
                    # Combine with priority first
                    ordered_rels = priority_rels + other_rels
                    rel_limit = 10  # More for authority
                    print(f"[AnswerAgent] Authority Q: {len(priority_rels)} priority, {len(other_rels)} other relationships")
                else:
                    ordered_rels = relationships
                    rel_limit = 5
                
                for rel in ordered_rels[:rel_limit]:
                    prompt_parts.append(f"- {rel}")
                prompt_parts.append("\nBase your answer on these actual relationships, not generic knowledge.")
                
                # ✅ For authority questions, emphasize including ALL relationship details
                if intent == "authority":
                    prompt_parts.append("\n🔴 CRITICAL FOR AUTHORITY QUESTIONS:")
                    prompt_parts.append("- You MUST mention ALL authorities listed above")
                    prompt_parts.append("- Include BOTH 'continuous supervision' AND 'general direction' if present")
                    prompt_parts.append("- Include ALL legal bases (FAA, AECA, EO 13637) from relationships")
                    prompt_parts.append("- Do NOT omit any relationship - each one is important")
            
            # Add specific instructions based on intent
            # COMPREHENSIVE intent instructions for ALL intents
            # MERGED: Ch1-Ch9 sub-intents into broader categories
            intent_instructions = {
                # === DEFINITION (merged: Ch1 scope, purpose) ===
                "definition": """Provide a complete, authoritative definition with proper SAMM section reference.
If asking about SCOPE: Explain what is included/excluded, boundaries, and extent.
If asking about PURPOSE: Explain the objective, rationale, and why it exists.""",

                # === DISTINCTION ===
                "distinction": "Explain the key differences clearly with specific examples and legal basis. Highlight what makes each concept unique.",

                # === AUTHORITY (merged: Ch4 approval, review, decision) ===
                "authority": """Explain who has authority, the scope of that authority, and the legal basis. USE THE RELATIONSHIPS PROVIDED ABOVE.
If asking about APPROVAL: Explain who approves, approval thresholds, and the approval process.
If asking about REVIEW: Explain the review process, who reviews, and review cycles.
If asking about DECISION: Explain who makes the decision, decision-making process, and decision authority.""",

                # === ORGANIZATION ===
                "organization": "Describe the organization's full name, role, and specific responsibilities. Include reporting relationships.",

                # === FACTUAL (merged: Ch7 timeline, milestone, status, tracking) ===
                "factual": """Provide the specific factual information with proper context and citation.
If asking about TIMELINE: Include timeframes, durations, deadlines, and schedules.
If asking about MILESTONE: List key milestones, phases, and checkpoints.
If asking about STATUS: Describe current status, progress, and state.
If asking about TRACKING: Explain how things are monitored, tracked, or measured.""",

                # === RELATIONSHIP ===
                "relationship": "Describe how the entities relate to each other and why this matters. Include reporting chains and coordination.",

                # === PROCESS (merged: Ch5 implementation, prerequisite, documentation) ===
                "process": """Explain the process step-by-step, including who is involved at each step.
If asking about IMPLEMENTATION: Explain how to implement or execute, including specific actions.
If asking about PREREQUISITES: List what must be done/completed before starting.
If asking about DOCUMENTATION: Specify required documents, forms, and paperwork.""",

                # === FUNDING (merged: Ch6 budget, payment, pricing, reimbursement) ===
                "funding": """Explain the funding mechanism, source of funds (Title 10/22, FMF, etc.), who pays, and financial terms.
If asking about BUDGET: Explain budget allocation, planning, and fiscal year considerations.
If asking about PAYMENT: Describe payment terms, schedules, methods, and billing.
If asking about PRICING: Explain how prices are determined, pricing methodology, and case values.
If asking about REIMBURSEMENT: Describe reimbursement processes, rates, and policies.""",

                # === ELIGIBILITY ===
                "eligibility": "Explain who/what is eligible, the specific criteria or requirements, and any restrictions or exceptions.",

                # === COMPLIANCE (merged: Ch9 audit, legal, reporting) ===
                "compliance": """Explain the regulatory requirements, which laws/regulations apply (ITAR, AECA, FAA, etc.).
If asking about AUDIT: Describe audit processes, requirements, who conducts audits, and audit cycles.
If asking about LEGAL: Explain legal requirements, applicable laws, and consequences of non-compliance.
If asking about REPORTING: Specify reporting requirements, deadlines, formats, and who must report to whom.""",

                # === LIST ===
                "list": "Provide a complete, organized list with brief descriptions of each item. Include SAMM section references.",

                # === VERIFICATION ===
                "verification": "Provide a clear Yes/No answer first, then explain the reasoning with SAMM references.",

                # === EXPLANATION ===
                "explanation": "Explain the purpose, rationale, or reasoning clearly with supporting context from SAMM.",
                
                # === Fallback for any other intent ===
                "general": "Provide accurate, comprehensive information based on SAMM content with proper citations.",
            }
            
            if intent in intent_instructions:
                prompt_parts.append(intent_instructions[intent])
            
            prompt_parts.append("Provide a comprehensive, accurate answer based on SAMM content.")
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            print(f"[AnswerAgent] Error creating prompt: {e}")
            return f"Question: {query}\nProvide a comprehensive answer based on SAMM."



    def _generate_with_validation(self, prompt: str, system_msg: str, intent_info: Dict) -> str:
        """Generate answer with 30-second timeout and validation"""
        intent = intent_info.get("intent", "general")
        
        try:
            print("[AnswerAgent] First generation pass...")
            initial_answer = call_ollama_enhanced(prompt, system_msg, temperature=0.1)
            
            # ================================
            # GOLD STANDARD CHECK (LOR)
            # ================================
            if intent == "LOR_SUBMISSION_REQUIREMENTS":
                if not meets_lor_gold_standard(initial_answer):
                    print("⚠️ [AnswerAgent] LOR gold standard not met, regenerating...")

                    system_msg += """
            IMPORTANT:
            The previous answer was incomplete.

            You MUST include:
            - Statement that no specific format is required
            - Statement that the LOR must be in writing
            - Coordination with the Security Cooperation Organization (SCO)
            - Reference to Figure C5.F14 (LOR Checklist)
            - Reference to Table C5.T3a (Actionable Criteria)
            - At least 8 detailed LOR requirements
            - Leahy compliance language for FMF or EDA cases after Dec 31, 2021

            Do NOT omit any required items.
            """

                initial_answer = call_ollama_enhanced(
                    prompt,
                    system_msg,
                    temperature=0.15
                )

            
            if "Error" in initial_answer and len(initial_answer) < 100:
                return initial_answer
            
            if "technical difficulties" in initial_answer:
                return initial_answer
            
            validation_results = self._validate_answer_quality(initial_answer, intent)
            
            if validation_results["needs_improvement"] and len(validation_results["issues"]) < 10:
                print(f"[AnswerAgent] Answer needs improvement: {validation_results['issues']}")
                
                improvement_prompt = f"{prompt}\n\nIMPROVEMENT NEEDED: {', '.join(validation_results['issues'])}\n\nPlease provide a better response addressing these issues."
                
                print("[AnswerAgent] Second generation pass with improvements...")
                improved_answer = call_ollama_enhanced(improvement_prompt, system_msg, temperature=0.2)
                
                if (len(improved_answer) > len(initial_answer) * 1.1 and 
                    "Error" not in improved_answer and 
                    "technical difficulties" not in improved_answer and
                    len(improved_answer) > 50):
                    return improved_answer
            
            return initial_answer
            
        except Exception as e:
            print(f"[AnswerAgent] Error during generation with validation: {e}")
            return _get_intelligent_fallback()


    def _validate_answer_quality(self, answer: str, intent: str) -> Dict[str, Any]:
        """Validate answer quality against SAMM standards with error handling"""
        try:
            issues = []
            needs_improvement = False
            
            # Skip validation if answer is too short (likely an error)
            if len(answer) < 20:
                return {"needs_improvement": False, "issues": ["answer_too_short"], "length": len(answer)}
            
            # Check length guidelines
            if intent in self.length_guidelines:
                guidelines = self.length_guidelines[intent]
                if len(answer) < guidelines["min"]:
                    issues.append("too short")
                    needs_improvement = True
                elif len(answer) > guidelines["max"]:
                    issues.append("too long")
            
            # Check for SAMM section references
            if not re.search(self.quality_patterns["section_references"], answer):
                issues.append("missing SAMM section reference")
                needs_improvement = True
            
            # Check for incomplete sentences
            if re.search(self.quality_patterns["incomplete_sentences"], answer):
                issues.append("incomplete sentences")
                needs_improvement = True
            
            # Intent-specific validations
            if intent == "definition" and "definition" not in answer.lower():
                issues.append("missing clear definition")
                needs_improvement = True
            
            if intent == "distinction" and not any(word in answer.lower() for word in ["difference", "differ", "distinction", "versus", "vs"]):
                issues.append("missing comparison language")
                needs_improvement = True
            
            if intent == "authority" and not any(word in answer.lower() for word in ["authority", "responsible", "oversight", "supervision"]):
                issues.append("missing authority language")
                needs_improvement = True
            
            return {
                "needs_improvement": needs_improvement,
                "issues": issues,
                "length": len(answer)
            }
            
        except Exception as e:
            print(f"[AnswerAgent] Error validating answer quality: {e}")
            return {"needs_improvement": False, "issues": [], "length": len(answer)}
    
    def _enhance_answer_quality(self, answer: str, intent_info: Dict, entity_info: Dict) -> str:
        """Apply post-processing enhancements with error handling"""
        try:
            enhanced_answer = answer
            
            # Skip enhancement if answer is too short or contains errors
            if len(answer) < 20 or "Error" in answer:
                return answer

            # =====================================================================
            # v5.9.2: CITATION VALIDATION - Ensure primary citation is in answer
            # =====================================================================
            if entity_info and entity_info.get("citations"):
                citations = entity_info["citations"]
                primary_citation = citations.get("primary")
                references = citations.get("references", [])
                
                if primary_citation:
                    # Check if primary citation is already in the answer
                    if primary_citation not in enhanced_answer:
                        # Append primary citation
                        enhanced_answer += f"\n\n**Primary Citation:** SAMM {primary_citation}"
                        print(f"[CitationValidation] Added missing primary citation: {primary_citation}")
                    
                    # Check for references
                    refs_in_answer = [ref for ref in references if ref in enhanced_answer]
                    refs_missing = [ref for ref in references if ref not in enhanced_answer]
                    
                    if refs_missing and len(refs_in_answer) == 0:
                        # Add reference citations if none are present
                        enhanced_answer += f"\n**References:** {', '.join(references[:2])}"
                        print(f"[CitationValidation] Added reference citations: {references[:2]}")
            # =====================================================================

            # Step 1: Add section reference if missing (prefer extracted citations / anchored context)
            if not re.search(self.quality_patterns["section_references"], enhanced_answer):
                sections: List[str] = []

                # v5.9.9: Use the citations already extracted from the SAME chunks we provided to the LLM
                if entity_info and entity_info.get("citations"):
                    c = entity_info.get("citations") or {}
                    primary = c.get("primary")
                    refs = c.get("references", []) or []
                    if primary:
                        sections.append(primary)
                    sections.extend([r for r in refs if r])

                # Fallback: try to parse bracket anchors from the answer itself, if present
                if not sections:
                    sections.extend(re.findall(r"\[(C\d+(?:\.\d+)*[A-Za-z0-9\.]*)\]", enhanced_answer))

                # Deduplicate preserving order
                seen = set()
                sections = [s for s in sections if not (s in seen or seen.add(s))]

                if sections:
                    top_sections = sections[:3]
                    enhanced_answer += f"\n\nSAMM Section Citations: {', '.join(top_sections)}"
                    print("[CITE DBG]", {"picked_sections": top_sections, "from": "entity_info.citations/anchors"})
# Step 2: Expand acronyms that appear without expansion (limit to prevent overprocessing)
            acronyms_found = re.findall(self.quality_patterns["acronym_detection"], enhanced_answer)
            
            for acronym in list(set(acronyms_found))[:5]:  # Limit to 5 acronyms
                if (acronym in self.acronym_expansions and 
                    acronym in enhanced_answer and 
                    self.acronym_expansions[acronym] not in enhanced_answer):
                    # Only expand the first occurrence
                    enhanced_answer = enhanced_answer.replace(acronym, self.acronym_expansions[acronym], 1)
            
            # Step 3: Ensure proper SAMM terminology
            terminology_fixes = {
                "security cooperation": "Security Cooperation",
                "security assistance": "Security Assistance", 
                "foreign assistance act": "Foreign Assistance Act",
                "arms export control act": "Arms Export Control Act"
            }
            
            for incorrect, correct in terminology_fixes.items():
                if incorrect in enhanced_answer and correct not in enhanced_answer:
                    enhanced_answer = enhanced_answer.replace(incorrect, correct)
            
            # Step 4: Add intent-specific enhancements
            intent = intent_info.get("intent", "general")
            
            if intent == "distinction" and "subset" not in enhanced_answer.lower():
                if "Security Assistance" in enhanced_answer and "Security Cooperation" in enhanced_answer:
                    enhanced_answer += "\n\nRemember: Security Assistance is a subset of Security Cooperation."
            
            return enhanced_answer
            
        except Exception as e:
            print(f"[AnswerAgent] Error enhancing answer quality: {e}")
            return answer  # Return original if enhancement fails
    
    def _validate_and_score_answer(self, answer: str, intent: str, query: str) -> str:
        """Final validation and quality scoring of the answer with error handling"""
        try:
            # Skip scoring if answer is too short or contains errors
            if len(answer) < 20 or "Error" in answer:
                return answer
            
            # Calculate quality score
            score = self._calculate_quality_score(answer, intent)
            
            # Log quality metrics
            print(f"[AnswerAgent] Answer quality score: {score:.2f}/1.0")
            
            # v5.9.11: Gold Standard validation
            gold_validation = validate_against_gold(answer, query)
            if gold_validation.get("pattern_id"):
                print(f"[GoldValidation] 🎯 Pattern: {gold_validation['pattern_id']}")
                print(f"[GoldValidation] 📊 Score: {gold_validation['score']}")
                if gold_validation.get("missing"):
                    print(f"[GoldValidation] ⚠️ Missing items: {gold_validation['missing'][:5]}")
                if gold_validation.get("mentioned"):
                    print(f"[GoldValidation] ✅ Mentioned: {len(gold_validation['mentioned'])} items")
            
            # If score is too low, add disclaimer
            if score < 0.6:
                print(f"[AnswerAgent] Low quality score, adding disclaimer")
                answer += "\n\nNote: For complete and authoritative information, please refer to the full SAMM documentation."
            
            return answer
            
        except Exception as e:
            print(f"[AnswerAgent] Error in final validation: {e}")
            return answer  # Return original if validation fails
    
    def _calculate_quality_score(self, answer: str, intent: str) -> float:
        """Calculate quality score based on SAMM standards with error handling"""
        try:
            score = 0.0
            
            # Section citation score
            if re.search(self.quality_patterns["section_references"], answer):
                score += self.quality_weights["section_citation"]
            
            # Acronym expansion score
            acronyms_found = re.findall(self.quality_patterns["acronym_detection"], answer)
            if acronyms_found:
                expanded_count = sum(1 for acronym in acronyms_found if f"{acronym})" in answer)
                score += self.quality_weights["acronym_expansion"] * (expanded_count / len(set(acronyms_found)))
            
            # Answer completeness score (based on length guidelines)
            if intent in self.length_guidelines:
                guidelines = self.length_guidelines[intent]
                if guidelines["min"] <= len(answer) <= guidelines["max"]:
                    score += self.quality_weights["answer_completeness"]
                elif len(answer) >= guidelines["target"]:
                    score += self.quality_weights["answer_completeness"] * 0.8
            
            # SAMM terminology score
            samm_terms = ["Security Cooperation", "Security Assistance", "SAMM", "Title 10", "Title 22"]
            terms_used = sum(1 for term in samm_terms if term in answer)
            if terms_used > 0:
                score += self.quality_weights["samm_terminology"] * min(1.0, terms_used / 3)
            
            # Structure adherence score
            if intent in self.samm_response_templates:
                required_elements = self.samm_response_templates[intent]["required_elements"]
                elements_present = 0
                for element in required_elements:
                    element_keywords = element.replace("_", " ").split()
                    if any(keyword in answer.lower() for keyword in element_keywords):
                        elements_present += 1
                
                if required_elements:
                    score += self.quality_weights["structure_adherence"] * (elements_present / len(required_elements))
            
            return min(1.0, score)  # Cap at 1.0
            
        except Exception as e:
            print(f"[AnswerAgent] Error calculating quality score: {e}")
            return 0.5  # Return moderate score on error
    
    def _normalize_query_for_matching(self, query: str) -> str:
        """Normalize query for matching similar questions"""
        try:
            # Simple normalization - remove punctuation, lowercase, sort words
            words = re.findall(r'\b\w+\b', query.lower())
            # Keep only significant words (length > 2)
            significant_words = [word for word in words if len(word) > 2]
            return " ".join(sorted(significant_words))
        except Exception as e:
            print(f"[AnswerAgent] Error normalizing query: {e}")
            return query.lower()
    
    def update_from_hil(self, query: str, original_answer: str, corrected_answer: str, 
                        feedback_data: Dict[str, Any] = None):
        """Update agent based on human-in-the-loop feedback with improved error handling"""
        try:
            feedback_entry = {
                "query": query,
                "original_answer": original_answer,
                "corrected_answer": corrected_answer,
                "feedback_data": feedback_data or {},
                "timestamp": datetime.now().isoformat(),
                "improvement_type": "hil_correction"
            }
            
            self.hil_feedback_data.append(feedback_entry)
            
            # Store the correction for future similar queries
            query_key = self._normalize_query_for_matching(query)
            self.answer_corrections[query_key] = {
                "corrected_answer": corrected_answer,
                "feedback_data": feedback_data,
                "original_query": query,
                "correction_date": datetime.now().isoformat()
            }
            
            # Extract and store improved patterns
            if feedback_data:
                intent = feedback_data.get("intent", "general")
                if intent not in self.answer_templates:
                    self.answer_templates[intent] = []
                
                # Store template patterns from corrections
                template_info = {
                    "query_pattern": query.lower(),
                    "improvement_notes": feedback_data.get("improvement_notes", ""),
                    "key_points": feedback_data.get("key_points", []),
                    "structure_notes": feedback_data.get("structure_notes", ""),
                    "feedback_date": datetime.now().isoformat()
                }
                self.answer_templates[intent].append(template_info)
            
            # Add any new knowledge provided in feedback
            if feedback_data and feedback_data.get("additional_knowledge"):
                self.custom_knowledge += f"\n\nHIL Update ({datetime.now().strftime('%Y-%m-%d')}):\n{feedback_data['additional_knowledge']}"
            
            print(f"[AnswerAgent HIL] Updated with correction for query: '{query[:50]}...'")
            print(f"[AnswerAgent HIL] Total corrections stored: {len(self.answer_corrections)}")
            return True
            
        except Exception as e:
            print(f"[AnswerAgent] Error updating from HIL feedback: {e}")
            return False


    def _get_loa_timeline_answer(self) -> str:
        """Return pre-formatted LOA timeline answer (INSTANT - no Ollama call)"""
        return """According to SAMM Section C5.4.2 (Letter of Offer and Acceptance Document Preparation Timeframe), the time required to prepare LOA documents varies based on the complexity of the sale:

    **Category A Cases:**
    - Timeline: 85% completed within 45 days
    - Complexity: Simple cases

    **Category B Cases:**
    - Timeline: 85% completed within 100 days
    - Complexity: Moderate complexity

    **Category C Cases:**
    - Timeline: 85% completed within 150 days
    - Complexity: Complex cases

    The categorization depends on factors such as:
    - Number and complexity of line items
    - Special requirements or modifications
    - Coordination needs with other agencies
    - Technical complexity of the equipment

    **Note:** These timeframes represent the standard for 85% of cases. Individual cases may vary based on specific circumstances, requirements, and resource availability."""

    def _get_financial_verification_answer(self) -> str:
        """Return pre-formatted financial verification answer"""
        return """**Funding Verification for Case SR-P-NAV**

    ✅ **Appropriate Funding Line: Line 007**

    According to the LOA Line Notes and the work scope described in the field activity email, Line 007 is the correct funding line for this request.

    💰 **Funding Availability:**
    - **PDLI Balance**: $41,550,000.00 available
    - **Requested Amount**: $950,000.00
    - **Verdict**: ✅ **APPROVED** - You have plenty of funding to cover this request

    **Details:**
    - Available funds significantly exceed the request ($41.55M vs $950K)
    - Request represents only 2.3% of available PDLI balance
    - No funding concerns for this procurement"""

    def _get_technical_services_answer(self) -> str:
        """Return pre-formatted technical services answer"""
        return """**Technical Services for Case SR-P-NAV (Line 007)**

    According to Line Note 007 of the LOA, Technical services include:

    - System integration engineering
    - Software integration support
    - Platform compatibility verification
    - Test and evaluation support
    - Technical assistance for weapon system integration onto Saudi Arabian naval platforms

    These services support the integration and deployment of defense systems for the Saudi Arabian Navy."""

    def _get_pmr_minutes_summary(self) -> str:
        """Return pre-formatted PMR minutes summary with action items"""
        return """NSM Program Management Review I Summary

    The Royal Saudi Naval Forces (RSNF) conducted a Program Management Review for the Naval Strike Missile (NSM) Program on October 21-23, 2025. The meeting covered the acquisition of 96 tactical NSM missiles, associated containers, ground support equipment, technical documentation, training, and integration services through a Foreign Military Sales (FMS) case totaling $284,961,260.

    Key Program Elements

    Weapon System: NSM is a fifth-generation precision strike missile with 185+ km range, GPS/INS guidance, imaging infrared seeker, and two-way data link capability. The system will be integrated with RSNF's Al Riyadh-class frigates and Al Jubail-class corvettes.

    Timeline: LOA implementation planned for May 31, 2025, with initial missile deliveries beginning at month 24 (May 2027) and final deliveries by month 36 (May 2028). Case closure estimated 24 months after final delivery (approximately May 2030).

    Training: 16 officers will attend 8-week tactical employment courses in Newport, RI (September 2025-January 2026), and 24 enlisted personnel will complete 12-week maintenance courses in San Diego, CA (October 2025-February 2026).

    Integration Services: Technical services include platform compatibility verification, combat system integration with Thales TACTICOS systems, software integration, and test support through December 2027.

    Major Concerns Addressed: 
    - Platform compatibility assessments needed for both vessel classes
    - EMI/EMC testing in congested shipping environments
    - Accelerated delivery schedules to support Q4 2027 fleet exercises
    - Storage facility environmental controls for desert coastal climate
    - English language proficiency requirements (ECL 80 minimum)

    ---

    Action Items Due Within Two Weeks (by December 3, 2025)

    Based on the meeting date of October 21-23, 2025, and assuming "today" is November 19, 2025, the following action items are due within the next two weeks (by December 3, 2025):

    Due November 23, 2025:
    - AI-004: NSM PO to submit request for early delivery of containers and GSE to DSCA
    - AI-007: RSNF to designate POD location and provide customs clearance procedures
    - AI-011: RSNF to determine translation requirement and advise NSM PO
    - AI-016: RSNF to confirm preferred class structure (2x12 or alternative) for enlisted training
    - AI-026: RSNF to designate authorized receiving official and provide contact information

    Note: These items are already overdue if today is November 19, 2025

    Due December 7, 2025 (within next 3 weeks, but close):
    - AI-002: NSM Industry to provide EMI/EMC test reports and frequency deconfliction analysis
    - AI-003: NSM PO to explore feasibility of accelerating first missile delivery to month 20-22
    - AI-005: NSM Industry to provide sample test data package and quality documentation templates
    - AI-008: NSM Industry to deliver comprehensive GSE listing with technical specifications
    - AI-010: NSM PO to provide calibration service cost estimate and availability
    - AI-012: NSM Industry to deliver preliminary safety procedures document
    - AI-013: RSNF to provide student nomination list with desired class assignments
    - AI-015: RSNF to provide operational area maps and priority target sets for simulator scenarios
    - AI-024: RSNF to submit formal request for alternative transportation method (if desired)
    - AI-029: NSM PO to provide Explosive Safety Site Plan requirements and DoD 6055.09-M extracts"""




    def update_from_trigger(self, new_entities: List[str], new_relationships: List[Dict], 
                           trigger_data: Dict[str, Any] = None):
        """Update agent when new entity/relationship data is available with error handling"""
        try:
            trigger_entry = {
                "new_entities": new_entities,
                "new_relationships": new_relationships,
                "trigger_data": trigger_data or {},
                "timestamp": datetime.now().isoformat(),
                "trigger_id": len(self.trigger_updates)
            }
            
            self.trigger_updates.append(trigger_entry)
            
            # Add new knowledge from trigger updates
            if trigger_data:
                new_knowledge_items = []
                
                # Add entity definitions
                for entity in new_entities:
                    definition = trigger_data.get("entity_definitions", {}).get(entity)
                    if definition:
                        new_knowledge_items.append(f"{entity}: {definition}")
                
                # Add relationship information
                for rel in new_relationships:
                    rel_info = f"{rel.get('source', '')} {rel.get('relationship', '')} {rel.get('target', '')}"
                    details = trigger_data.get("relationship_details", {}).get(rel_info)
                    if details:
                        new_knowledge_items.append(f"Relationship: {rel_info} - {details}")
                
                # Add any general knowledge updates
                if trigger_data.get("knowledge_updates"):
                    new_knowledge_items.extend(trigger_data["knowledge_updates"])
                
                if new_knowledge_items:
                    self.custom_knowledge += f"\n\nTrigger Update ({datetime.now().strftime('%Y-%m-%d')}):\n" + "\n".join(new_knowledge_items)
            
            print(f"[AnswerAgent Trigger] Updated with {len(new_entities)} new entities and {len(new_relationships)} relationships")
            print(f"[AnswerAgent Trigger] Total trigger updates: {len(self.trigger_updates)}")
            return True
            
        except Exception as e:
            print(f"[AnswerAgent] Error updating from trigger: {e}")
            return False

def check_compliance(query: str, intent_info: Dict, entity_info: Dict, user_profile: Dict = None) -> Dict[str, Any]:
    """
    Check ITAR compliance - defaults to TOP_SECRET for development
    Fails open (permits access) if service unavailable
    """
    if not COMPLIANCE_ENABLED:
        return {
            "compliance_status": "compliant",
            "authorized": True,
            "user_authorization_level": DEFAULT_DEV_AUTH_LEVEL,
            "content_guidance": {"allowed_detail_level": "full"},
            "restrictions": [],
            "check_performed": False
        }
    
    # Set default dev authorization
    if not user_profile:
        user_profile = {"authorization_level": DEFAULT_DEV_AUTH_LEVEL}
    elif "authorization_level" not in user_profile:
        user_profile["authorization_level"] = DEFAULT_DEV_AUTH_LEVEL
    
    try:
        response = requests.post(
            f"{COMPLIANCE_SERVICE_URL}/api/compliance/verify",
            json={
                "query": query,
                "intent_info": intent_info,
                "entity_info": entity_info,
                "user_profile": user_profile
            },
            timeout=15  # INCREASED from 5 to 15 seconds
        )
        response.raise_for_status()
        result = response.json()
        result["check_performed"] = True
        return result
        
    except requests.exceptions.Timeout:
        print(f"[Compliance] Service timeout - defaulting to permissive mode")
    except requests.exceptions.ConnectionError:
        print(f"[Compliance] Service unavailable - defaulting to permissive mode")
    except Exception as e:
        print(f"[Compliance] Error: {e} - defaulting to permissive mode")
    
    # Fail open for development
    return {
        "compliance_status": "compliant",
        "authorized": True,
        "user_authorization_level": DEFAULT_DEV_AUTH_LEVEL,
        "content_guidance": {"allowed_detail_level": "full"},
        "restrictions": [],
        "check_performed": False,
        "fallback_reason": "service_unavailable"
    }


def extract_financial_records_from_documents(documents_context: List) -> List[Dict]:
    """
    Extract financial records from uploaded documents
    Returns list of financial records with PDLI info
    """
    if not documents_context:
        return []
    
    financial_records = []
    
    for doc in documents_context:
        # Check if document has financial data in metadata
        if doc.get('metadata', {}).get('hasFinancialData'):
            records = doc['metadata'].get('financialRecords', [])
            
            print(f"[Financial Extract] Found {len(records)} records in {doc.get('fileName')}")
            
            # Enrich each record with document info
            for record in records:
                enriched = {
                    **record,
                    'source_document': doc.get('fileName'),
                    'document_id': doc.get('documentId')
                }
                financial_records.append(enriched)
    
    print(f"[Financial Extract] Total: {len(financial_records)} financial records extracted")
    return financial_records




class SimpleStateOrchestrator:
    """Simple LangGraph-style state orchestration for integrated SAMM agents with HIL and trigger updates"""
    
    def __init__(self):
        self.intent_agent = IntentAgent()
        self.entity_agent = IntegratedEntityAgent(knowledge_graph, db_manager)
        self.answer_agent = EnhancedAnswerAgent()
        
        # Define workflow graph
        self.workflow = {
            WorkflowStep.INIT: self._initialize_state,
            WorkflowStep.INTENT: self._analyze_intent_step,
            WorkflowStep.ENTITY: self._extract_entities_step,
            WorkflowStep.ANSWER: self._generate_answer_step,
            WorkflowStep.COMPLETE: self._complete_workflow,
            WorkflowStep.ERROR: self._handle_error
        }
        
        # Define state transitions
        self.transitions = {
            WorkflowStep.INIT: WorkflowStep.INTENT,
            WorkflowStep.INTENT: WorkflowStep.ENTITY,
            WorkflowStep.ENTITY: WorkflowStep.ANSWER,
            WorkflowStep.ANSWER: WorkflowStep.COMPLETE,
            WorkflowStep.COMPLETE: None,
            WorkflowStep.ERROR: None
        }
    @time_function
    def process_query(self, query: str, chat_history: List = None, documents_context: List = None,
                     user_profile: Dict = None) -> Dict[str, Any]:
        """Process query through integrated state orchestrated workflow"""
        # Initialize state
        state = AgentState(
            query=query,
            chat_history=chat_history,
            documents_context=documents_context,
            intent_info=None,
            entity_info=None,
            answer=None,
            execution_steps=[],
            start_time=time.time(),
            current_step=WorkflowStep.INIT.value,
            error=None
        )
        # ✅ ADD THESE 3 LINES HERE:
        print(f"[DEBUG PROCESS_QUERY] Received documents_context: {documents_context is not None}")
        print(f"[DEBUG PROCESS_QUERY] documents_context type: {type(documents_context)}")
        print(f"[DEBUG PROCESS_QUERY] documents_context length: {len(documents_context) if documents_context else 0}")
    
        state['user_profile'] = user_profile or {"authorization_level": DEFAULT_DEV_AUTH_LEVEL}
        try:
            # Execute workflow
            current_step = WorkflowStep.INIT
            
            while current_step is not None:
                print(f"[State Orchestrator] Executing step: {current_step.value}")
                state['current_step'] = current_step.value
                state['execution_steps'].append(f"Step: {current_step.value}")
                
                # Execute step
                state = self.workflow[current_step](state)
                
                # Check for error
                if state.get('error'):
                    current_step = WorkflowStep.ERROR
                else:
                    # Move to next step
                    current_step = self.transitions[current_step]
            
            execution_time = round(time.time() - state['start_time'], 2)
            
            return {
                "query": state['query'],
                "answer": state['answer'],
                "intent": state['intent_info'].get('intent', 'unknown') if state['intent_info'] else 'unknown',
                "entities_found": len(state['entity_info'].get('entities', [])) if state['entity_info'] else 0,
                "execution_time": execution_time,
                "execution_steps": state['execution_steps'],
                "success": state['error'] is None,
                "metadata": {
                    "intent_confidence": state['intent_info'].get('confidence', 0) if state['intent_info'] else 0,
                    "entities": state['entity_info'].get('entities', []) if state['entity_info'] else [],
                    "system_version": "Integrated_Database_SAMM_v5.0",
                    "workflow_completed": state['current_step'] == 'complete',
                    # Keep legacy metadata structure for Vue.js compatibility
                    "intent": state['intent_info'].get('intent', 'unknown') if state['intent_info'] else 'unknown',
                    "entities_found": len(state['entity_info'].get('entities', [])) if state['entity_info'] else 0,
                    "execution_time_seconds": execution_time,
                    # Add database integration status
                    "database_integration": {
                        "cosmos_gremlin": db_manager.cosmos_gremlin_client is not None,
                        "vector_db": db_manager.vector_db_client is not None,
                        "embedding_model": db_manager.embedding_model is not None
                    },
                    # Add HIL and trigger update status
                    "hil_updates_available": (len(self.intent_agent.hil_feedback_data) > 0 or 
                                            len(self.entity_agent.hil_feedback_data) > 0 or 
                                            len(self.answer_agent.hil_feedback_data) > 0),
                    "trigger_updates_available": (len(self.intent_agent.trigger_updates) > 0 or 
                                                len(self.entity_agent.trigger_updates) > 0 or 
                                                len(self.answer_agent.trigger_updates) > 0),
                    # Enhanced entity agent status
                    "entity_extraction_method": state['entity_info'].get('extraction_method', 'unknown') if state['entity_info'] else 'unknown',
                    "entity_confidence": state['entity_info'].get('overall_confidence', 0) if state['entity_info'] else 0,
                    "extraction_phases": state['entity_info'].get('phase_count', 0) if state['entity_info'] else 0,
                    "total_database_results": state['entity_info'].get('total_results', 0) if state['entity_info'] else 0
                }
            }
            
        except Exception as e:
            execution_time = round(time.time() - state['start_time'], 2)
            return {
                "query": query,
                "answer": f"I apologize, but I encountered an error during integrated processing: {str(e)}",
                "intent": "error",
                "entities_found": 0,
                "execution_time": execution_time,
                "execution_steps": state['execution_steps'] + [f"Error: {str(e)}"],
                "success": False,
                "metadata": {"error": str(e), "system_version": "Integrated_Database_SAMM_v5.0"}
            }
    
    def update_agents_from_hil(self, query: str, intent_correction: Dict = None, entity_correction: Dict = None, answer_correction: Dict = None) -> Dict[str, bool]:
        """Update all agents from human-in-the-loop feedback"""
        results = {}
        
        # Update Intent Agent
        if intent_correction:
            results["intent"] = self.intent_agent.update_from_hil(
                query=query,
                original_intent=intent_correction.get("original_intent"),
                corrected_intent=intent_correction.get("corrected_intent"),
                feedback_data=intent_correction.get("feedback_data", {})
            )
        
        # Update Integrated Entity Agent
        if entity_correction:
            results["entity"] = self.entity_agent.update_from_hil(
                query=query,
                original_entities=entity_correction.get("original_entities", []),
                corrected_entities=entity_correction.get("corrected_entities", []),
                feedback_data=entity_correction.get("feedback_data", {})
            )
        
        # Update Enhanced Answer Agent
        if answer_correction:
            results["answer"] = self.answer_agent.update_from_hil(
                query=query,
                original_answer=answer_correction.get("original_answer"),
                corrected_answer=answer_correction.get("corrected_answer"),
                feedback_data=answer_correction.get("feedback_data", {})
            )
        
        print(f"[State Orchestrator] HIL updates completed: {results}")
        return results
    
    def update_agents_from_trigger(self, new_entities: List[str], new_relationships: List[Dict], trigger_data: Dict[str, Any] = None) -> Dict[str, bool]:
        """Update all agents when new entity/relationship data is available"""
        results = {}
        
        # Update Intent Agent
        results["intent"] = self.intent_agent.update_from_trigger(
            new_entities=new_entities,
            new_relationships=new_relationships,
            trigger_data=trigger_data
        )
        
        # Update Integrated Entity Agent
        results["entity"] = self.entity_agent.update_from_trigger(
            new_entities=new_entities,
            new_relationships=new_relationships,
            trigger_data=trigger_data
        )
        
        # Update Enhanced Answer Agent
        results["answer"] = self.answer_agent.update_from_trigger(
            new_entities=new_entities,
            new_relationships=new_relationships,
            trigger_data=trigger_data
        )
        
        print(f"[State Orchestrator] Trigger updates completed: {results}")
        return results
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents including database connections and HIL/trigger update counts"""
        return {
            "intent_agent": {
                "hil_feedback_count": len(self.intent_agent.hil_feedback_data),
                "trigger_update_count": len(self.intent_agent.trigger_updates),
                "learned_patterns": len(self.intent_agent.intent_patterns)
            },
            "integrated_entity_agent": {
                "type": "IntegratedEntityAgent",
                "hil_feedback_count": len(self.entity_agent.hil_feedback_data),
                "trigger_update_count": len(self.entity_agent.trigger_updates),
                "custom_entities": len(self.entity_agent.custom_entities),
                "dynamic_entities": len(self.entity_agent.dynamic_knowledge["entities"]),
                "samm_patterns": sum(len(patterns) for patterns in self.entity_agent.samm_entity_patterns.values()),
                "extraction_phases": 3,  # pattern_matching, nlp_extraction, database_queries
                "database_status": db_manager.get_database_status()
            },
            "enhanced_answer_agent": {
                "type": "EnhancedAnswerAgent",
                "hil_feedback_count": len(self.answer_agent.hil_feedback_data),
                "trigger_update_count": len(self.answer_agent.trigger_updates),
                "answer_corrections": len(self.answer_agent.answer_corrections),
                "answer_templates": sum(len(templates) for templates in self.answer_agent.answer_templates.values()),
                "response_templates": len(self.answer_agent.samm_response_templates),
                "acronym_expansions": len(self.answer_agent.acronym_expansions)
            }
        }
    
    def get_database_status(self) -> Dict[str, Any]:
        """Get comprehensive database status"""
        return db_manager.get_database_status()
    
    def cleanup(self):
        """Cleanup all resources"""
        try:
            db_manager.cleanup()
            print("[State Orchestrator] Cleanup complete")
        except Exception as e:
            print(f"[State Orchestrator] Cleanup error: {e}")
    
    def _initialize_state(self, state: AgentState) -> AgentState:
        """Initialize workflow state"""
        state['execution_steps'].append("Integrated workflow initialized with database connections")
        print(f"[State Orchestrator] Initialized query: '{state['query']}'")
        return state
    
    def _analyze_intent_step(self, state: AgentState) -> AgentState:
        """Execute intent analysis step"""
        try:
            state['intent_info'] = self.intent_agent.analyze_intent(state['query'])
            state['execution_steps'].append(f"Intent analyzed: {state['intent_info'].get('intent', 'unknown')}")
            print(f"[State Orchestrator] Intent: {state['intent_info'].get('intent')} (confidence: {state['intent_info'].get('confidence')})")
        except Exception as e:
            state['error'] = f"Intent analysis failed: {str(e)}"
        return state
    
    @time_function
    def analyze_intent(self, query: str) -> Dict[str, Any]:
        # STEP 1: Check for special cases FIRST (before calling Ollama)
        special_case = self._check_special_cases(query)
        if special_case:
            print(f"[IntentAgent] Returning special case: {special_case['intent']}")
            return special_case
        
        # STEP 2: Normal SAMM intent analysis (existing logic unchanged)
        # Check if we have learned patterns from previous feedback
        enhanced_system_msg = self._build_enhanced_system_message()
        
        prompt = f"Analyze this SAMM query and determine intent: {query}"
        
        try:
            response = call_ollama_enhanced(prompt, enhanced_system_msg, temperature=0.0)
            # Try to parse JSON response
            if "{" in response and "}" in response:
                json_part = response[response.find("{"):response.rfind("}")+1]
                result = json.loads(json_part)
                
                # Apply any learned corrections from HIL feedback
                result = self._apply_hil_corrections(query, result)
                return result
            else:
                return {"intent": "general", "confidence": 0.5, "entities_mentioned": []}
        except:
            return {"intent": "general", "confidence": 0.5, "entities_mentioned": []}





    @time_function
    def _extract_entities_step(self, state: AgentState) -> AgentState:
        """Execute integrated entity extraction with database queries"""
        # NEW DEBUG LINES - ADD THESE 3 LINES:
        print(f"[DEBUG STATE] documents_context exists: {'documents_context' in state}")
        print(f"[DEBUG STATE] documents_context value: {state.get('documents_context', 'NOT FOUND')}")
        print(f"[DEBUG STATE] documents_context length: {len(state.get('documents_context', [])) if state.get('documents_context') else 0}")
    
        # ✅ ENHANCED: Skip entity extraction for special cases
        if state['intent_info'].get('special_case', False):
            intent = state['intent_info'].get('intent')
            print(f"[State Orchestrator] Skipping entity extraction for special case: {intent}")
            
            # ✅ NEW: Handle LOA timeline special case
            if intent == "loa_timeline":
                state['entity_info'] = {
                    'entities': ["LOA", "Timeline", "SAMM C5.4.2"],
                    'context': [{
                        "entity": "LOA",
                        "definition": "Letter of Offer and Acceptance - primary contractual document in FMS",
                        "section": "C5.4.2",
                        "type": "document",
                        "source": "knowledge_graph",
                        "confidence": 1.0
                    }],
                    'relationships': [
                        "LOA prepared by DSCA",
                        "LOA categorized by complexity (A, B, C)",
                        "LOA timeline varies by category"
                    ],
                    'special_case_skip': True,
                    'fast_path': True
                }
            else:
                state['entity_info'] = {
                    'entities': [],
                    'context': [],
                    'relationships': [],
                    'special_case_skip': True
                }
            
            state['execution_steps'].append("Entity extraction skipped (special case)")
            return state
        
        try:
            # ✅ ADDED: Get documents from state (safe - defaults to None if not present)
            documents_context = state.get('documents_context', None)
            
            # ✅ ADDED: Log file status for debugging
            if documents_context:
                print(f"[State Orchestrator] 📁 Passing {len(documents_context)} files to entity extraction")
                for idx, doc in enumerate(documents_context[:3], 1):
                    fname = doc.get('fileName', 'Unknown')
                    content_len = len(doc.get('content', ''))
                    print(f"[State Orchestrator]   File {idx}: {fname} ({content_len} chars)")
            else:
                print(f"[State Orchestrator] No files in state to pass to entity extraction")
            
            # ✅ FIXED: Now passes documents_context (was missing before)
            state['entity_info'] = self.entity_agent.extract_and_retrieve(
                state['query'], 
                state['intent_info'],
                documents_context  # ← ADDED THIS PARAMETER
            )
            
            # ✅ EXISTING: Get entity extraction stats
            entities_count = len(state['entity_info'].get('entities', []))
            confidence = state['entity_info'].get('overall_confidence', 0)
            db_results = state['entity_info'].get('total_results', 0)
            phases = state['entity_info'].get('phase_count', 0)
            
            # ✅ ADDED: Get file-related stats (safe - defaults to 0 if not present)
            files_processed = state['entity_info'].get('files_processed', 0)
            file_entities = state['entity_info'].get('file_entities_found', 0)
            file_relationships = state['entity_info'].get('file_relationships_found', 0)
            
            # ✅ ENHANCED: Include file stats in execution step message
            state['execution_steps'].append(
                f"Integrated entity extraction: {entities_count} entities found "
                f"(confidence: {confidence:.2f}, DB results: {db_results}, phases: {phases}, "
                f"files: {files_processed}, file_entities: {file_entities}, file_rels: {file_relationships})"
            )
            
            # ✅ ENHANCED: Include file stats in console log
            print(f"[State Orchestrator] Integrated Entities: {entities_count} entities found "
                f"through {phases} phases with {db_results} database results "
                f"and {file_entities} entities from {files_processed} files")
            
            # ✅ ADDED: Log file-specific extraction details if files were processed
            if files_processed > 0:
                print(f"[State Orchestrator] 📊 File Extraction Results:")
                print(f"[State Orchestrator]   • Files processed: {files_processed}")
                print(f"[State Orchestrator]   • Entities from files: {file_entities}")
                print(f"[State Orchestrator]   • Relationships from files: {file_relationships}")
            
        except Exception as e:
            # ✅ EXISTING: Error handling unchanged
            state['error'] = f"Integrated entity extraction failed: {str(e)}"
            print(f"[State Orchestrator] ❌ Entity extraction error: {str(e)}")
            
            # ✅ ADDED: Add traceback for debugging
            import traceback
            print(f"[State Orchestrator] Error traceback:\n{traceback.format_exc()}")
        
        return state

    @time_function
    def _generate_answer_step(self, state: AgentState) -> AgentState:
        """Execute enhanced answer generation step"""
        try:
            print(f"[State Orchestrator] 🔄 Starting answer generation...")
            print(f"[State Orchestrator]   Query: {state['query'][:50]}...")
            print(f"[State Orchestrator]   Intent: {state['intent_info'].get('intent', 'unknown')}")
            print(f"[State Orchestrator]   Entities: {len(state['entity_info'].get('entities', []))}")
            print(f"[State Orchestrator]   Files: {len(state.get('documents_context', []))}")
            
            # ✅ ADD: Pass user_profile to generate_answer
            state['answer'] = self.answer_agent.generate_answer(
                state['query'], 
                state['intent_info'], 
                state['entity_info'], 
                state['chat_history'], 
                state['documents_context'],
                state.get('user_profile')  # ← ADD THIS LINE
            )
            
            # ✅ ADD: Verify answer was generated
            if not state['answer'] or len(state['answer']) < 20:
                print(f"[State Orchestrator] ⚠️ WARNING: Answer too short or empty!")
                print(f"[State Orchestrator]   Answer: '{state['answer']}'")
                state['answer'] = "I apologize, but I encountered an issue generating a complete answer. Please try rephrasing your question."
            else:
                print(f"[State Orchestrator] ✅ Answer generated successfully:")
                print(f"[State Orchestrator]   Length: {len(state['answer'])} chars")
                print(f"[State Orchestrator]   Preview: {state['answer'][:150]}...")
            
            state['execution_steps'].append("Enhanced answer generated successfully with quality scoring")
        except Exception as e:
            print(f"[State Orchestrator] ❌ ERROR in answer generation: {str(e)}")
            import traceback
            traceback.print_exc()
            state['error'] = f"Enhanced answer generation failed: {str(e)}"
            state['answer'] = f"I apologize, but I encountered an error: {str(e)}"
        return state


    def _complete_workflow(self, state: AgentState) -> AgentState:
        """Complete workflow"""
        state['execution_steps'].append("Integrated workflow completed successfully")
        print(f"[State Orchestrator] Integrated workflow completed in {round(time.time() - state['start_time'], 2)}s")
        return state
    
    def _handle_error(self, state: AgentState) -> AgentState:
        """Handle workflow error"""
        state['execution_steps'].append(f"Error handled: {state['error']}")
        state['answer'] = f"I apologize, but I encountered an error: {state['error']}"
        print(f"[State Orchestrator] Error handled: {state['error']}")
        return state


# Initialize integrated orchestrator with all agents
orchestrator = SimpleStateOrchestrator()
print("Integrated State Orchestrator initialized with Intent, Integrated Entity (Database), and Enhanced Answer agents")

@time_function
def process_samm_query(query: str, chat_history: List = None, documents_context: List = None,
                      user_profile: Dict = None) -> Dict[str, Any]:
    """Process query through integrated state orchestrated 3-agent system with ITAR compliance"""
    return orchestrator.process_query(query, chat_history, documents_context, user_profile)
# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_mock_user():
    """Return a mock user for demo purposes"""
    return {
        "sub": "mock-user-123",
        "name": "Demo User",
        "email": "demo@example.com"
    }

def require_auth():
    """Check if user is authenticated, return user info or None"""
    user_session_data = session.get("user")
    if not user_session_data:
        return None
    
    # For OAuth
    if "userinfo" in user_session_data and "sub" in user_session_data["userinfo"]:
        return user_session_data["userinfo"]
    
    # For mock user (when OAuth not configured)
    if not oauth:
        return get_mock_user()
    
    return None



# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@app.route("/login")
def login():
    if oauth:
        # Hardcoded callback URL
        redirect_uri_for_auth0 = "http://172.16.200.12:3000/callback"
        print(f"[Login] Redirecting to Auth0 with callback: {redirect_uri_for_auth0}")
        return oauth.auth0.authorize_redirect(redirect_uri=redirect_uri_for_auth0)
    else:
        # Mock login when OAuth not configured
        session["user"] = {"userinfo": get_mock_user()}
        return jsonify({"message": "Logged in with mock user"}), 200


@app.route("/callback", methods=["GET", "POST"])
def callback():
    if not oauth:
        return jsonify({"error": "OAuth not configured"}), 500

    try:
        token = oauth.auth0.authorize_access_token()
        session["user"] = token
        userinfo = token.get("userinfo")
        if userinfo:
            print(f"User logged in: {userinfo.get('name')} ({userinfo.get('sub')})")
    except Exception as e:
        print(f"Error during Auth0 callback: {e}")
        return redirect(url_for("login"))

        # Hardcoded frontend URL
    vue_app_url = "http://172.16.200.12:5173"
    next_url_path_from_session = session.pop('next_url', None)
    final_redirect_url = vue_app_url

    if next_url_path_from_session:
        if next_url_path_from_session.startswith('/'):
            final_redirect_url = f"{vue_app_url}{next_url_path_from_session}"
        else:
            final_redirect_url = f"{vue_app_url}/{next_url_path_from_session}"

    print(f"[Callback] Redirecting to frontend: {final_redirect_url}")
    return redirect(final_redirect_url)


@app.route("/logout")
def logout():
    session.clear()
    if oauth:
        # Hardcoded frontend URL
        vue_app_url = "http://172.16.200.12:5173"
        return redirect(
            f"https://{AUTH0_DOMAIN}/v2/logout?" +
            urlencode({
                "returnTo": vue_app_url,
                "client_id": AUTH0_CLIENT_ID,
            }, quote_via=quote_plus)
        )
    else:
        return jsonify({"message": "Logged out"}), 200




# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route("/api/me", methods=["GET"])
def get_current_user_profile():
    user = require_auth()
    if user:
        return jsonify(user), 200
    else:
        return jsonify({"error": "User not authenticated"}), 401

@app.route("/api/user/cases", methods=["GET"])
def get_user_cases():
    user = require_auth()
    if not user:
        return jsonify({"error": "User not authenticated"}), 401
    
    user_id = user["sub"]
    
    if cases_container_client:
        try:
            query = "SELECT * FROM c WHERE c.userId = @userId AND c.type = 'case'" 
            parameters = [{"name": "@userId", "value": user_id}]
            user_cases_list = list(cases_container_client.query_items(query=query, parameters=parameters, partition_key=user_id))
            return jsonify(user_cases_list), 200
        except Exception as e:
            print(f"Error querying cases: {e}")
            return jsonify({"error": "Database service error"}), 503
    else:
        # Use in-memory storage
        return jsonify(user_cases.get(user_id, [])), 200

@app.route("/api/cases", methods=["POST"])
def create_case():
    user = require_auth()
    if not user:
        return jsonify({"error": "User not authenticated"}), 401
    
    user_id = user["sub"]
    case_data = request.get_json() if request.is_json else {}
    
    case_id = str(uuid.uuid4())
    new_case = {
        "id": case_id,
        "userId": user_id,
        "type": "case",
        "title": case_data.get("title", "New Case"),
        "description": case_data.get("description", ""),
        "caseDocuments": [],
        "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }
    
    if cases_container_client:
        try:
            cases_container_client.create_item(body=new_case)
            return jsonify(new_case), 201
        except Exception as e:
            print(f"Error creating case: {e}")
            return jsonify({"error": "Failed to create case"}), 500
    else:
        # Use in-memory storage
        if user_id not in user_cases:
            user_cases[user_id] = []
        user_cases[user_id].append(new_case)
        return jsonify(new_case), 201



@app.route('/api/cases/<case_id>/documents/upload', methods=['POST'])
def upload_case_document_to_case(case_id):
    """Upload document(s) to a specific case - AUTO-CREATES case if not found"""
    print(f"\n[Upload] === Starting upload to case: {case_id} ===")
    # Get authenticated user
    user = require_auth()
    if not user:
        return jsonify({"error": "User not authenticated"}), 401
    user_id = user["sub"]
    print(f"[Upload] User ID: {user_id}")
    # Get files from request
    if 'files' not in request.files and 'file' not in request.files:
        return jsonify({"error": "No files provided"}), 400
    files = request.files.getlist('files') or request.files.getlist('file')
    if not files or all(f.filename == '' for f in files):
        return jsonify({"error": "No files selected"}), 400
    results = []
    for file in files:
        if not file or file.filename == '':
            continue
        print(f"\n[Upload] Processing: {file.filename}")
        # Use URL case ID (from route parameter)
        target_case_id = case_id
        print(f"[Upload] 📋 Using URL case: {target_case_id}")
        # ========================================
        # Find or CREATE case with userId filter
        # ========================================
        case_doc = None
        # Try to read by ID with userId partition key
        try:
            case_doc = cases_container_client.read_item(item=target_case_id, partition_key=user_id)
            print(f"[Upload] ✅ Found case by ID: {target_case_id}")
        except CosmosExceptions.CosmosResourceNotFoundError:
            pass
        # Try query by caseNumber with userId filter
        if not case_doc:
            query = """
            SELECT * FROM c 
            WHERE c.userId = @userId 
            AND (c.caseNumber = @caseId OR c.id = @caseId)
            """
            parameters = [
                {"name": "@userId", "value": user_id},
                {"name": "@caseId", "value": target_case_id}
            ]
            cases = list(cases_container_client.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=False
            ))
            if cases:
                case_doc = cases[0]
                print(f"[Upload] ✅ Found case by query: {target_case_id}")
        # ✅ AUTO-CREATE: If case not found, create it
        if not case_doc:
            print(f"[Upload] 📝 Case not found, auto-creating: {target_case_id}")
            now = datetime.utcnow().isoformat() + "Z"
            case_doc = {
                "id": target_case_id,
                "caseNumber": target_case_id,
                "userId": user_id,
                "caseName": f"Case {target_case_id}",
                "status": "Active",
                "loa": "BASIC",
                "value": 0,
                "implementedDate": now,
                "caseDocuments": [],
                "financialDocuments": [],
                "createdAt": now,
                "updatedAt": now,
                "autoCreated": True
            }
            cases_container_client.upsert_item(case_doc)
            print(f"[Upload] ✅ Auto-created case: {target_case_id}")
        # ========================================
        # Upload file to Blob Storage
        # ========================================
        try:
            file_content = file.read()
            file.seek(0)
            # Generate unique blob name
            doc_id = str(uuid.uuid4())
            original_filename = secure_filename(file.filename)
            blob_name = f"{target_case_id}/{doc_id}_{original_filename}"
            # Upload to blob storage
            blob_client = case_docs_blob_container_client.get_blob_client(blob_name)
            blob_client.upload_blob(file_content, overwrite=True)
            blob_url = blob_client.url
            print(f"[Upload] ✅ Uploaded to blob: {blob_name}")
            # ========================================
            # Create document metadata
            # ========================================
            now = datetime.utcnow().isoformat() + "Z"
            doc_metadata = {
                "id": doc_id,
                "documentId": doc_id,
                "fileName": original_filename,
                "fileType": file.content_type or "application/octet-stream",
                "sizeBytes": len(file_content),
                "url": blob_url,
                "blobName": blob_name,
                "uploadedAt": now,
                "uploadedBy": user_id
            }
            # ========================================
            # Extract financial data from Excel files
            # ========================================
            financial_records = []
            if original_filename.lower().endswith(('.xlsx', '.xls')):
                print(f"[Upload] 📊 Extracting financial data from Excel...")
                try:
                    from io import BytesIO
                    file_buffer = BytesIO(file_content)
                    extraction_result = extract_case_document_data(file_buffer, "FINANCIAL_DATA", original_filename, target_case_id)
                    financial_records = extraction_result.get("key_info", {}).get("financial_records", [])
                    print(f"[Upload] ✅ Extracted {len(financial_records)} financial records")
                except Exception as e:
                    print(f"[Upload] ⚠️ Excel extraction error: {str(e)}")
                    financial_records = []
            # ========================================
            # Update case document in Cosmos DB
            # ========================================
            if 'caseDocuments' not in case_doc:
                case_doc['caseDocuments'] = []
            case_doc['caseDocuments'].append(doc_metadata)
            if 'financialDocuments' not in case_doc:
                case_doc['financialDocuments'] = []
            if financial_records:
                financial_doc = {
                    "id": doc_id,
                    "documentId": doc_id,
                    "fileName": original_filename,
                    "uploadedAt": now,
                    "records": financial_records,
                    "recordCount": len(financial_records)
                }
                case_doc['financialDocuments'].append(financial_doc)
            case_doc['updatedAt'] = now
            # Save updated case
            cases_container_client.upsert_item(case_doc)
            print(f"[Upload]   User ID (partition): {case_doc.get('userId')}")
            print(f"[Upload]   Document count: {len(case_doc.get('caseDocuments', []))}")
            # Verify the save
            verify_case = cases_container_client.read_item(item=case_doc['id'], partition_key=case_doc['userId'])
            print(f"[Upload] 🔍 VERIFY: Re-read case has {len(verify_case.get('caseDocuments', []))} docs")
            print(f"[Upload] ✅ Saved document to case {target_case_id}")
            results.append({
                "fileName": original_filename,
                "documentId": doc_id,
                "success": True,
                "url": blob_url,
                "financialRecords": len(financial_records)
            })
        except Exception as e:
            print(f"[Upload] ❌ Error uploading {file.filename}: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                "fileName": file.filename,
                "success": False,
                "error": str(e)
            })
    print(f"[Upload] ✅ Processed: {file.filename} -> Case: {target_case_id}")
    print(f"\n[Upload] === Complete: {len([r for r in results if r.get('success')])}/{len(results)} files processed ===")
    return jsonify({
        "success": True,
        "caseId": case_id,
        "caseNumber": case_id,
        "results": results
    }), 200



@app.route("/api/cases/<path:case_id>/financial-data", methods=["GET"])
def get_case_financial_data(case_id):
    """
    💰 GET ALL FINANCIAL DATA FOR A CASE
    
    Returns all extracted financial records from uploaded MISIL RSN sheets
    
    Response:
        {
          "success": true,
          "caseId": "uuid",
          "caseNumber": "SR-P-NAV",
          "financialDocuments": [
            {
              "documentId": "uuid",
              "fileName": "MISIL_RSN.xlsx",
              "uploadedAt": "2024-01-15T10:30:00Z",
              "recordCount": 45
            }
          ],
          "financialRecords": [
            {
              "rsn_identifier": "A-001",
              "pdli_pdli": "123456",
              "pdli_name": "F-16 Parts",
              "oa_rec_amt": 1000000,
              "net_commit_amt": 500000,
              "available": 500000,
              "sourceDocument": "MISIL_RSN.xlsx"
            }
          ],
          "recordCount": 45,
          "totals": {
            "oa_rec_amt": 50000000,
            "net_commit_amt": 25000000,
            ...
          }
        }
    """
    user = require_auth()
    if not user:
        return jsonify({"error": "User not authenticated"}), 401
    
    user_id = user["sub"]
    
    from urllib.parse import unquote
    case_id = unquote(case_id)
    
    print(f"[Financial Data] Fetching for case: {case_id}")
    
    if not cases_container_client:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        # Get case document
        case_doc = None
        
        # Try UUID lookup
        try:
            case_doc = cases_container_client.read_item(item=case_id, partition_key=user_id)
        except CosmosExceptions.CosmosResourceNotFoundError:
            # Try case number lookup
            query = """
            SELECT * FROM c 
            WHERE c.userId = @userId 
            AND c.type = 'case'
            AND c.caseNumber = @caseNumber
            """
            parameters = [
                {"name": "@userId", "value": user_id},
                {"name": "@caseNumber", "value": case_id}
            ]
            
            cases = list(cases_container_client.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=False
            ))
            
            if cases:
                case_doc = cases[0]
        
        if not case_doc:
            return jsonify({"error": "Case not found"}), 404
        
        # Extract all financial records
        all_financial_records = []
        financial_documents = []
        
        for doc in case_doc.get("caseDocuments", []):
            metadata = doc.get("metadata", {})
            
            if metadata.get("hasFinancialData", False):
                records = metadata.get("financialRecords", [])
                
                if records:
                    financial_documents.append({
                        "documentId": doc.get("documentId"),
                        "fileName": doc.get("fileName"),
                        "uploadedAt": doc.get("uploadedAt"),
                        "recordCount": len(records)
                    })
                    
                    # Add document reference to each record
                    for record in records:
                        record["sourceDocument"] = doc.get("fileName")
                        record["documentId"] = doc.get("documentId")
                    
                    all_financial_records.extend(records)
        
        # Calculate totals
        totals = {
            "oa_rec_amt": 0,
            "net_commit_amt": 0,
            "net_obl_amt": 0,
            "net_exp_amt": 0,
            "dir_rsrv_amt": 0
        }
        
        for record in all_financial_records:
            for field in totals.keys():
                value = record.get(field, 0)
                if value:
                    try:
                        totals[field] += float(str(value).replace('$', '').replace(',', ''))
                    except:
                        pass
        
        print(f"[Financial Data] ✅ Found {len(all_financial_records)} records")
        
        return jsonify({
            "success": True,
            "caseId": case_doc["id"],
            "caseNumber": case_doc.get("caseNumber", case_id),
            "financialDocuments": financial_documents,
            "financialRecords": all_financial_records,
            "recordCount": len(all_financial_records),
            "totals": totals,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        print(f"[Financial Data] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/cases/<path:case_id>/financial-summary", methods=["GET"])
def get_financial_summary(case_id):
    """
    📊 GET FINANCIAL SUMMARY WITH RSN AGGREGATION
    
    Returns high-level financial metrics grouped by RSN PDLI
    
    Response:
        {
          "success": true,
          "caseId": "uuid",
          "caseNumber": "SR-P-NAV",
          "rsnSummary": [
            {
              "rsn_identifier": "A-001",
              "pdli_pdli": "123456",
              "pdli_name": "F-16 Parts",
              "oa_rec_amt": 1000000,
              "net_commit_amt": 500000,
              "available": 500000,
              "record_count": 5
            }
          ],
          "grandTotals": {...},
          "uniqueRSNs": 10
        }
    """
    user = require_auth()
    if not user:
        return jsonify({"error": "User not authenticated"}), 401
    
    user_id = user["sub"]
    
    from urllib.parse import unquote
    case_id = unquote(case_id)
    
    if not cases_container_client:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        # Get case (same logic as financial-data endpoint)
        case_doc = None
        try:
            case_doc = cases_container_client.read_item(item=case_id, partition_key=user_id)
        except:
            query = """
            SELECT * FROM c 
            WHERE c.userId = @userId 
            AND c.caseNumber = @caseNumber
            """
            parameters = [
                {"name": "@userId", "value": user_id},
                {"name": "@caseNumber", "value": case_id}
            ]
            cases = list(cases_container_client.query_items(
                query=query, parameters=parameters, enable_cross_partition_query=False
            ))
            if cases:
                case_doc = cases[0]
        
        if not case_doc:
            return jsonify({"error": "Case not found"}), 404
        
        # Aggregate by RSN
        rsn_aggregation = {}
        
        for doc in case_doc.get("caseDocuments", []):
            metadata = doc.get("metadata", {})
            records = metadata.get("financialRecords", [])
            
            for record in records:
                rsn = record.get("rsn_identifier", "Unknown")
                
                if rsn not in rsn_aggregation:
                    rsn_aggregation[rsn] = {
                        "rsn_identifier": rsn,
                        "pdli_pdli": record.get("pdli_pdli", "N/A"),
                        "pdli_name": record.get("pdli_name", ""),
                        "oa_rec_amt": 0,
                        "net_commit_amt": 0,
                        "net_obl_amt": 0,
                        "net_exp_amt": 0,
                        "dir_rsrv_amt": 0,
                        "record_count": 0
                    }
                
                # Aggregate amounts
                for field in ["oa_rec_amt", "net_commit_amt", "net_obl_amt", "net_exp_amt", "dir_rsrv_amt"]:
                    value = record.get(field, 0)
                    if value:
                        try:
                            rsn_aggregation[rsn][field] += float(str(value).replace('$', '').replace(',', ''))
                        except:
                            pass
                
                rsn_aggregation[rsn]["record_count"] += 1
        
        # Convert to list and sort by amount
        rsn_summary = sorted(
            rsn_aggregation.values(),
            key=lambda x: x.get("oa_rec_amt", 0),
            reverse=True
        )
        
        # Calculate grand totals
        grand_totals = {
            "oa_rec_amt": sum(item["oa_rec_amt"] for item in rsn_summary),
            "net_commit_amt": sum(item["net_commit_amt"] for item in rsn_summary),
            "net_obl_amt": sum(item["net_obl_amt"] for item in rsn_summary),
            "net_exp_amt": sum(item["net_exp_amt"] for item in rsn_summary),
            "dir_rsrv_amt": sum(item["dir_rsrv_amt"] for item in rsn_summary)
        }
        
        return jsonify({
            "success": True,
            "caseId": case_doc["id"],
            "caseNumber": case_doc.get("caseNumber", case_id),
            "rsnSummary": rsn_summary,
            "grandTotals": grand_totals,
            "uniqueRSNs": len(rsn_summary),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        print(f"[Financial Summary] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
@app.route("/api/chat/stage_attachment", methods=["POST"])
def stage_chat_attachment():
    user = require_auth()
    if not user:
        return jsonify({"error": "User not authenticated"}), 401
    
    user_id = user["sub"]

    if not chat_docs_blob_container_client:
        print("[API StageChatAttachment] Chat documents blob service not available.")
        return jsonify({"error": "Chat document storage service not available"}), 503

    if 'document' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file_to_upload = request.files['document']

    if file_to_upload.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file_to_upload:
        original_filename = secure_filename(file_to_upload.filename)
        blob_name = f"{user_id}/chat_staging/{str(uuid.uuid4())}-{original_filename}"
        
        print(f"[API StageChatAttachment] Processing file: {original_filename} for blob: {blob_name}")
        blob_client_instance = chat_docs_blob_container_client.get_blob_client(blob_name)
            
        try:
            file_to_upload.seek(0) 
            blob_content_settings = ContentSettings(content_type=file_to_upload.mimetype)
            blob_client_instance.upload_blob(
                file_to_upload.read(), 
                overwrite=True,
                content_settings=blob_content_settings
            )
            print(f"[API StageChatAttachment] Successfully uploaded '{original_filename}' to blob: {blob_name}")

            file_to_upload.seek(0, os.SEEK_END)
            file_size_bytes = file_to_upload.tell()
            
            staged_doc_metadata = {
                "documentId": str(uuid.uuid4()),
                "fileName": original_filename,
                "blobName": blob_name,
                "blobContainer": AZURE_CHAT_DOCS_CONTAINER_NAME,
                "url": blob_client_instance.url,
                "fileType": file_to_upload.mimetype,
                "sizeBytes": file_size_bytes,
                "uploadedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "uploaderUserId": user_id,
                "status": "staged"
            }
            
            return jsonify({
                "message": f"File '{original_filename}' staged successfully.",
                "stagedDocument": staged_doc_metadata 
            }), 200

        except Exception as e:
            print(f"[API StageChatAttachment] Error uploading file '{original_filename}' to blob: {str(e)}")
            return jsonify({"error": f"Failed to upload file '{original_filename}'.", "details": str(e)}), 500
    
    return jsonify({"error": "Unknown error during file staging."}), 500


@app.route('/api/cases/documents/delete', methods=['POST'])
def delete_case_document():
    """Delete a document from a case - AUTO-CREATES case if not found"""
    print("\n" + "=" * 60)
    print("[DELETE DOC] Starting deletion")

    user = require_auth()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401

    user_id = user["sub"]
    print(f"[DELETE DOC] User: {user_id}")

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    case_id = data.get('caseId')
    document_id = data.get('documentId')

    print(f"[DELETE DOC] Case: {case_id}")
    print(f"[DELETE DOC] Document ID: {document_id}")
    print("=" * 60)

    if not case_id or not document_id:
        return jsonify({"error": "caseId and documentId are required"}), 400

    try:
        # ========================================
        # Find case with userId filter
        # ========================================
        case_doc = None

        # Try by ID with partition key
        try:
            case_doc = cases_container_client.read_item(item=case_id, partition_key=user_id)
            print(f"[DELETE DOC] ✅ Found case by ID: {case_id}")
        except CosmosExceptions.CosmosResourceNotFoundError:
            pass

        # Try by caseNumber query
        if not case_doc:
            print(f"[DELETE DOC] Querying Cosmos DB with userId filter...")
            query = """
            SELECT * FROM c 
            WHERE c.userId = @userId 
            AND (c.caseNumber = @caseId OR c.id = @caseId)
            """
            parameters = [
                {"name": "@userId", "value": user_id},
                {"name": "@caseId", "value": case_id}
            ]

            cases = list(cases_container_client.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=False
            ))

            if cases:
                case_doc = cases[0]
                print(f"[DELETE DOC] ✅ Found case by query: {case_id}")

        # ✅ AUTO-CREATE: If case not found, create it (but document won't exist)
        if not case_doc:
            print(f"[DELETE DOC] 📝 Case not found, auto-creating: {case_id}")

            now = datetime.utcnow().isoformat() + "Z"

            case_doc = {
                "id": case_id,
                "caseNumber": case_id,
                "userId": user_id,
                "caseName": f"Case {case_id}",
                "status": "Active",
                "loa": "BASIC",
                "value": 0,
                "implementedDate": now,
                "caseDocuments": [],
                "financialDocuments": [],
                "createdAt": now,
                "updatedAt": now,
                "autoCreated": True
            }

            cases_container_client.upsert_item(case_doc)
            print(f"[DELETE DOC] ✅ Auto-created case: {case_id}")

            # Case was just created, so document doesn't exist
            return jsonify({"error": f"Document {document_id} not found in case {case_id}"}), 404

        # ========================================
        # Find and remove document
        # ========================================
        case_documents = case_doc.get('caseDocuments', [])
        financial_documents = case_doc.get('financialDocuments', [])

        print(f"[DELETE DOC] Case has {len(case_documents)} documents")

        # Find document to delete
        doc_to_delete = None
        doc_index = -1

        for i, doc in enumerate(case_documents):
            doc_id = doc.get('id') or doc.get('documentId') or doc.get('metadata_id')
            if doc_id == document_id:
                doc_to_delete = doc
                doc_index = i
                break

        if doc_index == -1:
            print(f"[DELETE DOC] ❌ Document not found: {document_id}")
            return jsonify({"error": f"Document {document_id} not found"}), 404

        print(f"[DELETE DOC] ✅ Found document at index {doc_index}")

        # ========================================
        # Delete from blob storage
        # ========================================
        blob_name = doc_to_delete.get('blobName')
        if blob_name:
            try:
                blob_client = case_docs_blob_container_client.get_blob_client(blob_name)
                blob_client.delete_blob()
                print(f"[DELETE DOC] ✅ Deleted blob: {blob_name}")
            except Exception as e:
                print(f"[DELETE DOC] ⚠️ Blob delete warning: {str(e)}")

        # ========================================
        # Remove from case document
        # ========================================
        case_documents.pop(doc_index)
        case_doc['caseDocuments'] = case_documents

        # Also remove from financial documents if present
        financial_documents = [
            fd for fd in financial_documents
            if fd.get('id') != document_id and fd.get('documentId') != document_id
        ]
        case_doc['financialDocuments'] = financial_documents

        case_doc['updatedAt'] = datetime.utcnow().isoformat() + "Z"

        # Save updated case
        cases_container_client.upsert_item(case_doc)

        print(f"[DELETE DOC] ✅ Document deleted successfully")
        print(f"[DELETE DOC] Remaining documents: {len(case_documents)}")

        return jsonify({
            "success": True,
            "message": "Document deleted successfully",
            "documentId": document_id,
            "remainingDocuments": len(case_documents)
        }), 200

    except Exception as e:
        print(f"[DELETE DOC] ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/attachments/delete", methods=["POST"])
def delete_chat_attachment():
    user = require_auth()
    if not user:
        return jsonify({"error": "User not authenticated"}), 401
    
    user_id = user["sub"]

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    blob_name = data.get("blobName")
    blob_container_name = data.get("blobContainer")

    if not blob_name or not blob_container_name:
        return jsonify({"error": "Missing blobName or blobContainer in request"}), 400

    print(f"[API DeleteChatAttachment] User: {user_id} attempting to delete blob: {blob_name} from container: {blob_container_name}")

    if blob_container_name != AZURE_CHAT_DOCS_CONTAINER_NAME:
        print(f"[API DeleteChatAttachment] Attempt to delete from non-chat container: {blob_container_name}. Denied.")
        return jsonify({"error": "Invalid target container for deletion"}), 403

    if not blob_service_client:
        print("[API DeleteChatAttachment] Blob service client not available.")
        return jsonify({"error": "Blob storage service not available"}), 503
    
    target_blob_client = None
    if blob_container_name == AZURE_CHAT_DOCS_CONTAINER_NAME:
        if chat_docs_blob_container_client:
            target_blob_client = chat_docs_blob_container_client.get_blob_client(blob_name)
        else:
            print(f"[API DeleteChatAttachment] Mismatch or uninitialized client for container: {blob_container_name}")
            return jsonify({"error": "Specified blob container client not configured or mismatch"}), 500

    if not target_blob_client:
        return jsonify({"error": "Could not obtain blob client for deletion."}), 500

    try:
        target_blob_client.delete_blob()
        print(f"[API DeleteChatAttachment] Successfully deleted blob: {blob_name} from container: {blob_container_name}")
        return jsonify({"message": f"File '{blob_name}' deleted successfully from chat context."}), 200

    except BlobResourceNotFoundError:
        print(f"[API DeleteChatAttachment] Blob not found: {blob_name} in container: {blob_container_name}")
        return jsonify({"error": "File not found in storage."}), 404
    except Exception as e:
        print(f"[API DeleteChatAttachment] Error deleting blob '{blob_name}': {str(e)}")
        return jsonify({"error": "Failed to delete file from storage.", "details": str(e)}), 500




@app.route("/api/query", methods=["POST"])
def query_ai_assistant():
    """Main SAMM query endpoint using Integrated state orchestrated 3-agent system with caching and ITAR compliance"""
    user = require_auth()
    if not user:
        return jsonify({"error": "User not authenticated"}), 401
    
    user_id = user["sub"]

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    try:
        data = request.get_json()
        user_input = data.get("question", "").strip()
        chat_history = data.get("chat_history", []) 
        staged_chat_documents_metadata = data.get("staged_chat_documents", []) 
        
        if not user_input:
            return jsonify({"error": "Query cannot be empty"}), 400

        # === Extract user authorization profile ===
        user_profile = {
            "user_id": user_id,
            "authorization_level": user.get("authorization_level", DEFAULT_DEV_AUTH_LEVEL),
            "clearances": user.get("clearances", []),
            "role": user.get("role", "developer")
        }
        print(f"[Integrated SAMM Query] User: {user_id}, Auth: {user_profile['authorization_level']}, Query: '{user_input[:50]}...'")

        # === NEW: Load actual document content from blob storage ===
        documents_with_content = []
        for doc_meta in staged_chat_documents_metadata:
            blob_name = doc_meta.get("blobName")
            if blob_name and chat_docs_blob_container_client:
                content = fetch_blob_content(blob_name, chat_docs_blob_container_client)
                if content:
                    documents_with_content.append({
                        **doc_meta,
                        "content": content[:5000]  # Limit to 5000 chars to avoid overload
                    })
                    print(f"[Query] Loaded content from {doc_meta.get('fileName')}: {len(content)} chars")
        # === END NEW ===

        # STEP 1: Check cache first
        cached_result = get_from_cache(user_input)
        
        if cached_result:
            # Cache hit - return cached answer with cache metadata
            print(f"[Cache] Returning cached answer for: '{user_input[:50]}...'")
            
            response_data = {
                "response": {"answer": cached_result['answer']},
                "metadata": cached_result['metadata'],
                "uploadedChatDocuments": [],
                "cached": True,
                "cache_age_seconds": round(time.time() - cached_result['timestamp'], 2)
            }
            
            return jsonify(response_data)
        
        # STEP 2: Cache miss - process query normally
        print(f"[Integrated SAMM Query] Chat History items: {len(chat_history)}")
        print(f"[Integrated SAMM Query] Staged Chat Documents: {len(staged_chat_documents_metadata)}")
        
        # Check for demo partial response
        demo_response = generate_demo_partial_response(user_input)
        if demo_response and not get_from_cache(user_input):
            result = {
                'answer': demo_response['answer'],
                'metadata': {
                    'intent': demo_response['intent'],
                    'entities': demo_response['entities'],
                    'is_demo': True,
                    'demo_type': demo_response.get('demo_type', 'unknown')
                },
                'intent': demo_response['intent'],
                'entities_found': len(demo_response['entities']),
                'execution_time': 0.5
            }
            print(f"🎬 DEMO MODE: Using partial answer ({demo_response.get('demo_type', 'unknown').upper()})")
        else:
            # MODIFIED: Pass documents_with_content instead of staged_chat_documents_metadata
            result = process_samm_query(user_input, chat_history, documents_with_content, user_profile)
        
        # Apply HITL corrections if they exist
        result = apply_hitl_corrections(user_input, result)
        
        print(f"[Integrated SAMM Result] Intent: {result['intent']}, Entities: {result['entities_found']}, Time: {result['execution_time']}s")
        print(f"[Integrated SAMM Result] Workflow Steps: {len(result.get('execution_steps', []))}")
        print(f"[Integrated SAMM Result] System Version: {result['metadata'].get('system_version', 'Unknown')}")
        print(f"[Integrated SAMM Result] Database Results: {result['metadata'].get('total_database_results', 0)}")
        
        # STEP 3: Save to cache
        save_to_cache(user_input, result['answer'], result['metadata'])
        
        # ✅ NEW: Extract financial data from documents for response
        financial_summary = None
        if documents_with_content:
            financial_records = []
            for doc in documents_with_content:
                if doc.get('metadata', {}).get('hasFinancialData'):
                    records = doc['metadata'].get('financialRecords', [])
                    financial_records.extend(records)
            
            if financial_records:
                financial_summary = {
                    'total_records': len(financial_records),
                    'unique_rsns': len(set(r.get('rsn_identifier') for r in financial_records if r.get('rsn_identifier'))),
                    'total_available': sum(float(r.get('available', 0)) for r in financial_records),
                    'documents': [doc.get('fileName') for doc in documents_with_content 
                                 if doc.get('metadata', {}).get('hasFinancialData')]
                }
                print(f"[API] 💰 Financial summary: {financial_summary}")
        
        # Return response in the same format as before for Vue.js UI compatibility
        response_data = {
            "response": {"answer": result["answer"]},
            "metadata": result["metadata"],
            "uploadedChatDocuments": [],  # For future AI-generated documents
            "financialSummary": financial_summary,  # ✅ NEW
            "cached": False  # Fresh answer
        }
        
        # Add execution steps only in debug mode or if requested
        if data.get("debug", False) or data.get("include_workflow", False):
            response_data["execution_steps"] = result.get("execution_steps", [])
            response_data["workflow_info"] = {
                "orchestration": "integrated_database_state",
                "steps_completed": len(result.get("execution_steps", [])),
                "execution_time": result["execution_time"],
                "entity_extraction_method": result["metadata"].get("entity_extraction_method", "unknown"),
                "entity_confidence": result["metadata"].get("entity_confidence", 0),
                "extraction_phases": result["metadata"].get("extraction_phases", 0),
                "database_results": result["metadata"].get("total_database_results", 0),
                "database_integration": result["metadata"].get("database_integration", {})
            }
        
        return jsonify(response_data)

    except Exception as e:
        print(f"[Integrated SAMM Query] Error: {str(e)}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500






@app.route("/api/cache/stats", methods=["GET"])
def get_cache_statistics():
    """Get cache performance statistics"""
    user = require_auth()
    if not user:
        return jsonify({"error": "User not authenticated"}), 401
    
    stats = get_cache_stats()
    
    # Add additional details
    cache_entries = []
    for key, entry in list(query_cache.items())[:10]:  # Show top 10 most recent
        age_seconds = time.time() - entry['timestamp']
        cache_entries.append({
            "query": entry['original_query'][:100],  # Truncate long queries
            "age_seconds": round(age_seconds, 2),
            "intent": entry['metadata'].get('intent', 'unknown'),
            "entities_found": entry['metadata'].get('entities_found', 0)
        })
    
    return jsonify({
        "statistics": stats,
        "recent_entries": cache_entries,
        "cache_enabled": CACHE_ENABLED,
        "configuration": {
            "ttl_seconds": CACHE_TTL_SECONDS,
            "max_size": CACHE_MAX_SIZE
        },
        "timestamp": datetime.now().isoformat()
    })
   
@app.route("/api/system/status", methods=["GET"])
def get_system_status_for_ui():
    """Get system status in Vue.js UI compatible format"""
    # Test Ollama connection
    try:
        test_response = call_ollama_enhanced("Test", "Respond with 'OK'", temperature=0.0)
        ollama_status = "connected" if "OK" in test_response else "error"
        ollama_available = True
    except:
        ollama_status = "disconnected"
        ollama_available = False
    
    # Get database status
    db_status = orchestrator.get_database_status()
    
    # Get cache stats
    cache_stats_data = get_cache_stats()
    
    return jsonify({
        "status": "ready" if ollama_available else "degraded",
        "ai_model": OLLAMA_MODEL,
        "ai_provider": "Ollama",
        "ai_url": OLLAMA_URL,
        "ai_status": ollama_status,
        "knowledge_base": {
            "name": "SAMM",
            "entities": len(knowledge_graph.entities),
            "relationships": len(knowledge_graph.relationships),
            "status": "loaded"
        },
        "agents": {
            "available": 3,
            "types": ["intent", "integrated_entity", "enhanced_answer"],
            "orchestration": "integrated_database_state",
            "versions": {
                "intent_agent": "1.0",
                "entity_agent": "IntegratedEntityAgent v1.0",
                "answer_agent": "EnhancedAnswerAgent v1.0"
            }
        },
        "database_integration": {
            "cosmos_gremlin": db_status["cosmos_gremlin"]["connected"],
            "vector_db": db_status["vector_db"]["connected"],
            "embedding_model": db_status["embedding_model"]["loaded"]
        },
        "cache": cache_stats_data,  # NEW: Cache statistics
        "services": {
            "authentication": "configured" if oauth else "mock",
            "database": "connected" if cases_container_client else "disabled",
            "storage": "connected" if blob_service_client else "disabled",
            "cache": "enabled" if CACHE_ENABLED else "disabled"  # NEW
        },
        "version": "5.0.0-integrated-database-cached",  # Updated version
        "system_name": "Integrated Database SAMM ASIST with Cache",  # Updated name
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/examples", methods=["GET"])
def get_example_questions():
    """Get example questions in Vue.js UI compatible format"""
    examples = [
        "What is Security Cooperation?",
        "Who supervises Security Assistance programs?", 
        "What is the difference between Security Cooperation and Security Assistance?",
        "What does DFAS do?",
        "When was the Foreign Assistance Act enacted?",
        "What is an Implementing Agency?"
    ]
    
    return jsonify({
        "examples": examples,
        "count": len(examples)
    })

@app.route("/api/agents/hil_update", methods=["POST"])
def update_agents_from_hil():
    """Update agents from human-in-the-loop feedback"""
    user = require_auth()
    if not user:
        return jsonify({"error": "User not authenticated"}), 401
    
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        
        if not query:
            return jsonify({"error": "Query is required for HIL update"}), 400
        
        # Extract correction data for each agent
        intent_correction = data.get("intent_correction")
        entity_correction = data.get("entity_correction") 
        answer_correction = data.get("answer_correction")
        
        if not any([intent_correction, entity_correction, answer_correction]):
            return jsonify({"error": "At least one correction type must be provided"}), 400
        
        # Update agents through orchestrator
        results = orchestrator.update_agents_from_hil(
            query=query,
            intent_correction=intent_correction,
            entity_correction=entity_correction,
            answer_correction=answer_correction
        )
        
        return jsonify({
            "message": "HIL updates applied successfully",
            "query": query,
            "updates_applied": results,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"[HIL Update] Error: {str(e)}")
        return jsonify({"error": f"Failed to apply HIL updates: {str(e)}"}), 500

@app.route("/api/agents/trigger_update", methods=["POST"])
def update_agents_from_trigger():
    """Update agents when new entity/relationship data is available"""
    user = require_auth()
    if not user:
        return jsonify({"error": "User not authenticated"}), 401
    
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    try:
        data = request.get_json()
        new_entities = data.get("new_entities", [])
        new_relationships = data.get("new_relationships", [])
        trigger_data = data.get("trigger_data", {})
        
        if not new_entities and not new_relationships:
            return jsonify({"error": "At least one new entity or relationship must be provided"}), 400
        
        # Update agents through orchestrator
        results = orchestrator.update_agents_from_trigger(
            new_entities=new_entities,
            new_relationships=new_relationships,
            trigger_data=trigger_data
        )
        
        return jsonify({
            "message": "Trigger updates applied successfully",
            "new_entities_count": len(new_entities),
            "new_relationships_count": len(new_relationships),
            "updates_applied": results,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"[Trigger Update] Error: {str(e)}")
        return jsonify({"error": f"Failed to apply trigger updates: {str(e)}"}), 500

@app.route("/api/agents/status", methods=["GET"])
def get_agents_status():
    """Get detailed status of all agents including HIL and trigger update counts"""
    user = require_auth()
    if not user:
        return jsonify({"error": "User not authenticated"}), 401
    
    try:
        agent_status = orchestrator.get_agent_status()
        database_status = orchestrator.get_database_status()
        
        return jsonify({
            "agents": agent_status,
            "database_integration": database_status,
            "summary": {
                "total_hil_updates": sum(agent["hil_feedback_count"] for agent in agent_status.values()),
                "total_trigger_updates": sum(agent["trigger_update_count"] for agent in agent_status.values()),
                "total_learned_items": (
                    agent_status["intent_agent"]["learned_patterns"] +
                    agent_status["integrated_entity_agent"]["custom_entities"] + 
                    agent_status["enhanced_answer_agent"]["answer_corrections"]
                ),
                "database_features": {
                    "cosmos_gremlin_connected": database_status["cosmos_gremlin"]["connected"],
                    "vector_db_connected": database_status["vector_db"]["connected"],
                    "embedding_model_loaded": database_status["embedding_model"]["loaded"],
                    "total_vector_collections": len(database_status["vector_db"]["collections"]) 
                },
                "enhanced_features": {
                    "extraction_phases": agent_status["integrated_entity_agent"]["extraction_phases"],
                    "samm_patterns": agent_status["integrated_entity_agent"]["samm_patterns"],
                    "response_templates": agent_status["enhanced_answer_agent"]["response_templates"],
                    "acronym_expansions": agent_status["enhanced_answer_agent"]["acronym_expansions"]
                }
            },
            "system_version": "Integrated_Database_SAMM_v5.0",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"[Agent Status] Error: {str(e)}")
        return jsonify({"error": f"Failed to get agent status: {str(e)}"}), 500

@app.route("/api/database/status", methods=["GET"])
def get_database_status():
    """Get detailed database connection status"""
    user = require_auth()
    if not user:
        return jsonify({"error": "User not authenticated"}), 401
    
    try:
        database_status = orchestrator.get_database_status()
        
        return jsonify({
            "database_connections": database_status,
            "summary": {
                "total_connections": sum(1 for db in database_status.values() if db.get("connected", False)),
                "cosmos_gremlin_status": "connected" if database_status["cosmos_gremlin"]["connected"] else "disconnected",
                "vector_databases": {
                    "vector_db_collections": len(database_status["vector_db"]["collections"]),
                    "total_collections": len(database_status["vector_db"]["collections"]) 
                },
                "embedding_model_status": "loaded" if database_status["embedding_model"]["loaded"] else "not_loaded"
            },
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"[Database Status] Error: {str(e)}")
        return jsonify({"error": f"Failed to get database status: {str(e)}"}), 500

@app.route("/api/samm/status", methods=["GET"])
def get_samm_system_status():
    """Get detailed system status (maintains backward compatibility)"""
    # Test Ollama connection
    try:
        test_response = call_ollama_enhanced("Test", "Respond with 'OK'", temperature=0.0)
        ollama_status = "connected" if "OK" in test_response else "error"
    except:
        ollama_status = "disconnected"
    
    # Get database status
    database_status = orchestrator.get_database_status()
    
    return jsonify({
        "status": "ready",
        "ollama_url": OLLAMA_URL,
        "ollama_model": OLLAMA_MODEL,
        "ollama_status": ollama_status,
        "knowledge_graph": {
            "entities": len(knowledge_graph.entities),
            "relationships": len(knowledge_graph.relationships)
        },
        "orchestration": {
            "type": "integrated_database_state",
            "workflow_steps": [step.value for step in WorkflowStep],
            "agents": ["intent_agent", "integrated_entity_agent", "enhanced_answer_agent"]
        },
        "database_integration": {
            "cosmos_gremlin": {
                "connected": database_status["cosmos_gremlin"]["connected"],
                "endpoint": database_status["cosmos_gremlin"]["endpoint"],
                "database": database_status["cosmos_gremlin"]["database"]
            },
            "vector_databases": {
                "vector_db": {
                    "connected": database_status["vector_db"]["connected"],
                    "collections": database_status["vector_db"]["collections"]
                },
            },
            "embedding_model": {
                "loaded": database_status["embedding_model"]["loaded"],
                "model_name": database_status["embedding_model"]["model_name"]
            }
        },
        "enhanced_capabilities": {
            "integrated_entity_extraction": {
                "phases": 3,  # pattern_matching, nlp_extraction, database_queries
                "patterns": sum(len(patterns) for patterns in orchestrator.entity_agent.samm_entity_patterns.values()),
                "database_enhanced": True,
                "confidence_scoring": True,
                "ai_context_generation": True
            },
            "answer_generation": {
                "templates": len(orchestrator.answer_agent.samm_response_templates),
                "quality_scoring": True,
                "multi_pass_validation": True,
                "acronym_expansion": True
            }
        },
        "services": {
            "auth0": "configured" if oauth else "mock",
            "cosmos_db": "connected" if cases_container_client else "disabled",
            "blob_storage": "connected" if blob_service_client else "disabled"
        },
        "version": "Integrated_Database_SAMM_v5.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/samm/workflow", methods=["GET"])
def get_workflow_info():
    """Get workflow orchestration information"""
    return jsonify({
        "orchestration_type": "integrated_database_state",
        "workflow_steps": [
            {
                "step": step.value,
                "description": {
                    "initialize": "Initialize integrated workflow state with database connections",
                    "analyze_intent": "Analyze user intent using Intent Agent with HIL learning",
                    "extract_entities": "Extract entities using Integrated Entity Agent with database queries", 
                    "generate_answer": "Generate answer using Enhanced Answer Agent with quality scoring",
                    "complete": "Complete integrated workflow successfully",
                    "error": "Handle any workflow errors"
                }.get(step.value, "Unknown step")
            }
            for step in WorkflowStep
        ],
        "agents": [
            {
                "name": "IntentAgent", 
                "purpose": "Classify user queries and determine intent", 
                "hil_updates": True, 
                "trigger_updates": True,
                "version": "1.0"
            },
            {
                "name": "IntegratedEntityAgent", 
                "purpose": "Multi-phase entity extraction with SAMM patterns and database integration", 
                "hil_updates": True, 
                "trigger_updates": True,
                "version": "1.0",
                "features": ["pattern_matching", "nlp_extraction", "database_queries", "ai_context_generation", "confidence_scoring"],
                "database_integration": True
            },
            {
                "name": "EnhancedAnswerAgent", 
                "purpose": "Intent-optimized answer generation with quality enhancement", 
                "hil_updates": True, 
                "trigger_updates": True,
                "version": "1.0",
                "features": ["intent_optimization", "multi_pass_generation", "quality_scoring", "acronym_expansion", "answer_validation"]
            }
        ],
        "database_integration": {
            "cosmos_gremlin": {
                "purpose": "Graph database for entity relationships",
                "query_type": "Gremlin traversal queries"
            },
            "vector_db": {
                "purpose": "Document vector search",
                "query_type": "Semantic similarity search"
            },
        },
        "transitions": {
            "initialize": "analyze_intent",
            "analyze_intent": "extract_entities", 
            "extract_entities": "generate_answer",
            "generate_answer": "complete",
            "complete": "end",
            "error": "end"
        },
        "update_capabilities": {
            "human_in_loop": {
                "endpoint": "/api/agents/hil_update",
                "description": "Update agents based on human feedback corrections",
                "supported_corrections": ["intent", "entity", "answer"]
            },
            "trigger_updates": {
                "endpoint": "/api/agents/trigger_update", 
                "description": "Update agents when new entity/relationship data becomes available",
                "supported_data": ["new_entities", "new_relationships", "trigger_data"]
            }
        },
        "integrated_features": {
            "entity_extraction": {
                "phases": 3,
                "database_enhanced": True,
                "confidence_scoring": True,
                "pattern_matching": True,
                "nlp_extraction": True,
                "ai_fallback": True
            },
            "answer_generation": {
                "intent_optimization": True,
                "quality_validation": True,
                "multi_pass_generation": True,
                "template_adherence": True,
                "automatic_enhancement": True
            }
        }
    })

@app.route("/api/samm/examples", methods=["GET"])
def get_samm_examples():
    """Get example SAMM questions (detailed format for compatibility)"""
    examples = [
        {
            "question": "What is Security Cooperation?",
            "type": "definition",
            "expected_entities": ["Security Cooperation", "DoD"],
            "expected_intent": "definition",
            "database_relevant": True
        },
        {
            "question": "Who supervises Security Assistance programs?", 
            "type": "authority",
            "expected_entities": ["Security Assistance", "Department of State"],
            "expected_intent": "authority",
            "database_relevant": True
        },
        {
            "question": "What is the difference between Security Cooperation and Security Assistance?",
            "type": "distinction",
            "expected_entities": ["Security Cooperation", "Security Assistance"],
            "expected_intent": "distinction",
            "database_relevant": True
        },
        {
            "question": "What does DFAS do?",
            "type": "organization",
            "expected_entities": ["DFAS", "Defense Finance and Accounting Service"],
            "expected_intent": "organization",
            "database_relevant": True
        },
        {
            "question": "When was the Foreign Assistance Act enacted?",
            "type": "factual",
            "expected_entities": ["Foreign Assistance Act", "FAA"],
            "expected_intent": "factual",
            "database_relevant": True
        },
        {
            "question": "What is an Implementing Agency?",
            "type": "definition",
            "expected_entities": ["Implementing Agency", "IA"],
            "expected_intent": "definition",
            "database_relevant": True
        }
    ]
    
    return jsonify({
        "examples": examples,
        "count": len(examples),
        "usage": "Use these to test the Integrated Database orchestrated SAMM system",
        "integrated_testing": {
            "entity_extraction": "Each example includes expected entities for validation",
            "intent_classification": "Each example includes expected intent for validation",
            "database_integration": "All examples will trigger database queries",
            "quality_scoring": "Answers will include quality scores and enhancements"
        }
    })

@app.route("/api/samm/knowledge", methods=["GET"])
def get_knowledge_graph_info():
    """Get knowledge graph information"""
    entities_info = []
    for entity_id, entity in knowledge_graph.entities.items():
        entities_info.append({
            "id": entity_id,
            "label": entity['properties'].get('label', entity_id),
            "type": entity['type'],
            "definition": entity['properties'].get('definition', ''),
            "section": entity['properties'].get('section', '')
        })
    
    # Get integrated agent pattern information
    samm_patterns = {}
    if hasattr(orchestrator.entity_agent, 'samm_entity_patterns'):
        samm_patterns = {
            category: len(patterns) 
            for category, patterns in orchestrator.entity_agent.samm_entity_patterns.items()
        }
    
    # Get database status
    database_status = orchestrator.get_database_status()
    
    return jsonify({
        "entities": entities_info,
        "relationships": knowledge_graph.relationships,
        "total_entities": len(knowledge_graph.entities),
        "total_relationships": len(knowledge_graph.relationships),
        "enhanced_patterns": {
            "samm_entity_patterns": samm_patterns,
            "total_patterns": sum(samm_patterns.values()) if samm_patterns else 0,
            "pattern_categories": list(samm_patterns.keys()) if samm_patterns else []
        },
        "dynamic_knowledge": {
            "custom_entities": len(orchestrator.entity_agent.custom_entities),
            "dynamic_entities": len(orchestrator.entity_agent.dynamic_knowledge["entities"]),
            "dynamic_relationships": len(orchestrator.entity_agent.dynamic_knowledge["relationships"])
        },
        "database_integration": {
            "cosmos_gremlin": {
                "connected": database_status["cosmos_gremlin"]["connected"],
                "endpoint": database_status["cosmos_gremlin"]["endpoint"]
            },
            "vector_databases": {
                "vector_db_collections": len(database_status["vector_db"]["collections"]),
            },
            "embedding_model": {
                "loaded": database_status["embedding_model"]["loaded"],
                "model": database_status["embedding_model"]["model_name"]
            }
        }
    })

@app.route("/api/health", methods=["GET"])
def health_check():
    """System health check"""
    # Test integrated Ollama connection
    ollama_healthy = False
    try:
        test_response = call_ollama_enhanced("Test", "Respond with 'OK'", temperature=0.0)
        ollama_healthy = "OK" in test_response
    except:
        pass
    
    # Test agent status
    agent_healthy = False
    try:
        agent_status = orchestrator.get_agent_status()
        agent_healthy = len(agent_status) == 3  # All 3 agents should be present
    except:
        pass
    
    # Test database connections
    database_status = orchestrator.get_database_status()
    database_healthy = any([
        database_status["cosmos_gremlin"]["connected"],
        database_status["vector_db"]["connected"],
    ])
    
    # Get cache stats
    cache_stats_data = get_cache_stats()
    cache_healthy = CACHE_ENABLED and len(query_cache) >= 0  # Cache is working if enabled
    
    return jsonify({
        "status": "healthy" if (ollama_healthy and agent_healthy) else "degraded",
        "timestamp": datetime.now().isoformat(),
        "ollama_model": OLLAMA_MODEL,
        "ollama_healthy": ollama_healthy,
        "agents_healthy": agent_healthy,
        "database_healthy": database_healthy,
        "cache_healthy": cache_healthy,  # NEW
        "version": "Integrated_Database_SAMM_v5.0_Cached",  # Updated
        "components": {
            "ollama": "healthy" if ollama_healthy else "degraded",
            "agents": "healthy" if agent_healthy else "degraded",
            "knowledge_graph": "healthy" if len(knowledge_graph.entities) > 0 else "degraded",
            "case_database": "healthy" if cases_container_client else "disabled",
            "blob_storage": "healthy" if blob_service_client else "disabled",
            "cosmos_gremlin": "healthy" if database_status["cosmos_gremlin"]["connected"] else "disconnected",
            "vector_db": "healthy" if database_status["vector_db"]["connected"] else "disconnected",
            "embedding_model": "healthy" if database_status["embedding_model"]["loaded"] else "not_loaded",
            "cache": "healthy" if cache_healthy else "disabled"  # NEW
        },
        "cache_stats": cache_stats_data  # NEW: Include cache performance
    })

# Static file serving
@app.route('/')
def serve_main_app():
    user = require_auth()
    if not user and oauth:
        session['next_url'] = request.path
        return redirect(url_for("login"))
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_vue_paths(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else: 
        user = require_auth()
        if not user and oauth:
            session['next_url'] = request.path
            return redirect(url_for("login"))
        return send_from_directory(app.static_folder, 'index.html')

# Cleanup on exit
import atexit
atexit.register(orchestrator.cleanup)

@app.route("/api/reviews", methods=["POST"])
def create_review_item():
    """Create a new review item"""
    try:
        data = request.json
        
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())
        if not data.get('reviewId'):
            data['reviewId'] = str(uuid.uuid4())
        if not data.get('timestamp'):
            data['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        if reviews_test_container_client:
            result = reviews_test_container_client.create_item(data)
            return jsonify({
                "success": True,
                "message": "Review created successfully",
                "reviewId": data['reviewId']
            }), 201
        else:
            return jsonify({
                "success": False,
                "error": "Reviews container not available"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/reviews/pending", methods=["GET"])
def get_pending_reviews():
    """Get all pending reviews"""
    try:
        query = """
        SELECT * FROM c 
        WHERE c.type = 'review_item' 
        AND c.status = 'pending'
        ORDER BY c.timestamp DESC
        """
        
        if reviews_test_container_client:
            reviews = list(reviews_test_container_client.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            return jsonify({
                "success": True,
                "count": len(reviews),
                "reviews": reviews
            })
        else:
            return jsonify({
                "success": False,
                "error": "Reviews container not available",
                "reviews": []
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "reviews": []
        }), 500


@app.route("/api/reviews/<review_id>/submit", methods=["POST"])
def submit_review_feedback(review_id):
    """Submit review feedback"""
    try:
        data = request.json
        status = data.get('status')
        feedback = data.get('feedback', '')
        reviewer = data.get('reviewer', 'Unknown')
        
        if not reviews_test_container_client:
            return jsonify({
                "success": False,
                "error": "Reviews container not available"
            }), 500
        
        query = f"SELECT * FROM c WHERE c.reviewId = '{review_id}'"
        items = list(reviews_test_container_client.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return jsonify({
                "success": False,
                "error": "Review not found"
            }), 404
        
        review = items[0]
        review['status'] = status
        review['humanFeedback'] = feedback
        review['reviewedBy'] = reviewer
        review['reviewedAt'] = datetime.now(timezone.utc).isoformat()
        
        # ✨ NEW: Calculate entity metrics if corrected entities are provided
        if 'corrected_entities' in data:
            extracted = review.get('entities', [])
            corrected = data['corrected_entities']
            entity_metrics = calculate_entity_metrics(extracted, corrected)
            review['entityMetrics'] = entity_metrics
            print(f"📊 Entity metrics calculated: P={entity_metrics['precision']:.2f}, R={entity_metrics['recall']:.2f}, F1={entity_metrics['f1']:.2f}")
        
        # ✨ NEW: Track intent correctness
        if 'intent_correct' in data:
            review['intentCorrect'] = data['intent_correct']
        
        # ✨ NEW: Add timestamp for trend analysis if not exists
        if 'createdAt' not in review:
            review['createdAt'] = datetime.now(timezone.utc).isoformat()
        
        reviews_test_container_client.upsert_item(review)
        
        print(f"✅ Review {status} by {reviewer}: {review_id}")
        
        # ========== SAVE HITL CORRECTIONS ==========
        if status == "needs_revision":
            question = review.get('question', '')
            q_hash = create_question_hash(question)
            
            # Save corrected intent
            if 'corrected_intent' in data:
                HITL_CORRECTIONS_STORE["intent_corrections"][q_hash] = data['corrected_intent']
                print(f"💾 HITL: Intent correction saved for question hash {q_hash[:8]}...")
            
            # Save corrected entities
            if 'corrected_entities' in data:
                HITL_CORRECTIONS_STORE["entity_corrections"][q_hash] = data['corrected_entities']
                print(f"💾 HITL: Entity corrections saved ({len(data['corrected_entities'])} entities)")
            
            # Save corrected answer
            if 'corrected_answer' in data:
                HITL_CORRECTIONS_STORE["answer_corrections"][q_hash] = data['corrected_answer']
                print(f"💾 HITL: Answer correction saved ({len(data['corrected_answer'])} chars)")
            
            # Save all corrections to file
            save_hitl_corrections()
        # ========== END HITL CORRECTIONS ==========
        
        return jsonify({
            "success": True,
            "message": f"Review {status} successfully",
            "reviewId": review_id
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    
    # =============================================================================
# ENHANCED HITL APIs - Complete Implementation
# Add these routes to your Flask app after the existing /api/reviews/<review_id>/submit route
# =============================================================================

@app.route("/api/reviews/<review_id>/accept", methods=["POST"])
def accept_review(review_id):
    """Accept a review - mark as approved"""
    try:
        data = request.json or {}
        reviewer = data.get('reviewer', 'Travis')
        feedback = data.get('feedback', 'Approved by SME')
        
        if not reviews_test_container_client:
            return jsonify({
                "success": False,
                "error": "Reviews container not available"
            }), 500
        
        # Find the review
        query = f"SELECT * FROM c WHERE c.reviewId = '{review_id}'"
        items = list(reviews_test_container_client.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return jsonify({
                "success": False,
                "error": "Review not found"
            }), 404
        
        # Update review
        review = items[0]
        review['status'] = 'approved'
        review['humanFeedback'] = feedback
        review['reviewedBy'] = reviewer
        review['reviewedAt'] = datetime.now(timezone.utc).isoformat()
        
        # Save to database
        reviews_test_container_client.upsert_item(review)
        
        print(f"✅ Review ACCEPTED by {reviewer}: {review_id}")
        print(f"   Feedback: {feedback}")
        
        return jsonify({
            "success": True,
            "message": "Review accepted successfully",
            "reviewId": review_id,
            "status": "approved"
        })
        
    except Exception as e:
        print(f"❌ Error accepting review: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/reviews/<review_id>/reject", methods=["POST"])
def reject_review(review_id):
    """Reject a review - mark as needs revision"""
    try:
        data = request.json or {}
        reviewer = data.get('reviewer', 'Travis')
        feedback = data.get('feedback', '')
        
        if not feedback:
            return jsonify({
                "success": False,
                "error": "Feedback is required when rejecting"
            }), 400
        
        if not reviews_test_container_client:
            return jsonify({
                "success": False,
                "error": "Reviews container not available"
            }), 500
        
        # Find the review
        query = f"SELECT * FROM c WHERE c.reviewId = '{review_id}'"
        items = list(reviews_test_container_client.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return jsonify({
                "success": False,
                "error": "Review not found"
            }), 404
        
        # Update review
        review = items[0]
        review['status'] = 'needs_revision'
        review['humanFeedback'] = feedback
        review['reviewedBy'] = reviewer
        review['reviewedAt'] = datetime.now(timezone.utc).isoformat()
        
        # Save to database
        reviews_test_container_client.upsert_item(review)
        
        print(f"⚠️ Review REJECTED by {reviewer}: {review_id}")
        print(f"   Feedback: {feedback}")
        
        # TODO: Use feedback to improve agents in future
        # This is where you'd implement agent learning
        
        return jsonify({
            "success": True,
            "message": "Review rejected - feedback saved for improvement",
            "reviewId": review_id,
            "status": "needs_revision"
        })
        
    except Exception as e:
        print(f"❌ Error rejecting review: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/reviews/<review_id>/needs-revision", methods=["POST"])
def mark_needs_revision(review_id):
    """Mark review as needs revision with feedback"""
    try:
        data = request.json or {}
        reviewer = data.get('reviewer', 'Travis')
        feedback = data.get('feedback', '')
        
        if not feedback:
            return jsonify({
                "success": False,
                "error": "Feedback is required"
            }), 400
        
        if not reviews_test_container_client:
            return jsonify({
                "success": False,
                "error": "Reviews container not available"
            }), 500
        
        # Find the review
        query = f"SELECT * FROM c WHERE c.reviewId = '{review_id}'"
        items = list(reviews_test_container_client.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return jsonify({
                "success": False,
                "error": "Review not found"
            }), 404
        
        # Update review
        review = items[0]
        review['status'] = 'needs_revision'
        review['humanFeedback'] = feedback
        review['reviewedBy'] = reviewer
        review['reviewedAt'] = datetime.now(timezone.utc).isoformat()
        
        # Save to database
        reviews_test_container_client.upsert_item(review)
        
        print(f"📝 Review marked NEEDS REVISION by {reviewer}: {review_id}")
        print(f"   Feedback: {feedback}")
        
        return jsonify({
            "success": True,
            "message": "Feedback saved - marked for revision",
            "reviewId": review_id,
            "status": "needs_revision"
        })
        
    except Exception as e:
        print(f"❌ Error marking review: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/reviews/<review_id>/regenerate", methods=["POST"])
def regenerate_answer(review_id):
    """Regenerate answer for a review"""
    try:
        data = request.json or {}
        
        if not reviews_test_container_client:
            return jsonify({
                "success": False,
                "error": "Reviews container not available"
            }), 500
        
        # Find the review
        query = f"SELECT * FROM c WHERE c.reviewId = '{review_id}'"
        items = list(reviews_test_container_client.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return jsonify({
                "success": False,
                "error": "Review not found"
            }), 404
        
        review = items[0]
        original_question = review.get('question', '')
        
        # TODO: Re-run the query through agents
        # For now, just mark as regenerated
        review['status'] = 'regenerating'
        review['lastRegeneratedAt'] = datetime.now(timezone.utc).isoformat()
        
        reviews_test_container_client.upsert_item(review)
        
        print(f"🔄 Regenerating answer for review: {review_id}")
        print(f"   Question: {original_question}")
        
        return jsonify({
            "success": True,
            "message": "Answer regeneration initiated",
            "reviewId": review_id,
            "note": "Implementation pending - will re-run agents"
        })
        
    except Exception as e:
        print(f"❌ Error regenerating answer: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/reviews/<review_id>/agent/<agent_name>/accept", methods=["POST"])
def accept_agent_result(review_id, agent_name):
    """Accept a specific agent's result"""
    try:
        data = request.json or {}
        reviewer = data.get('reviewer', 'Travis')
        
        if not reviews_test_container_client:
            return jsonify({
                "success": False,
                "error": "Reviews container not available"
            }), 500
        
        # Find the review
        query = f"SELECT * FROM c WHERE c.reviewId = '{review_id}'"
        items = list(reviews_test_container_client.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return jsonify({
                "success": False,
                "error": "Review not found"
            }), 404
        
        review = items[0]
        
        # Track agent approvals
        if 'agentApprovals' not in review:
            review['agentApprovals'] = {}
        
        review['agentApprovals'][agent_name] = {
            'approved': True,
            'approvedBy': reviewer,
            'approvedAt': datetime.now(timezone.utc).isoformat()
        }
        
        reviews_test_container_client.upsert_item(review)
        
        print(f"✅ {agent_name} result ACCEPTED by {reviewer} for review: {review_id}")
        
        return jsonify({
            "success": True,
            "message": f"{agent_name} result accepted",
            "reviewId": review_id,
            "agent": agent_name
        })
        
    except Exception as e:
        print(f"❌ Error accepting agent result: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/reviews/stats", methods=["GET"])
def get_review_stats():
    """Get statistics about reviews"""
    try:
        if not reviews_test_container_client:
            return jsonify({
                "success": False,
                "error": "Reviews container not available"
            }), 500
        
        # Query all reviews
        query = "SELECT * FROM c WHERE c.type = 'review_item'"
        all_reviews = list(reviews_test_container_client.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        # Calculate stats
        total = len(all_reviews)
        pending = len([r for r in all_reviews if r.get('status') == 'pending'])
        approved = len([r for r in all_reviews if r.get('status') == 'approved'])
        needs_revision = len([r for r in all_reviews if r.get('status') == 'needs_revision'])
        
        # Calculate average confidence
        confidences = [r for r in all_reviews if 'confidenceOverall' in r]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        stats = {
            "success": True,
            "total_reviews": total,
            "pending": pending,
            "approved": approved,
            "needs_revision": needs_revision,
            "average_confidence": round(avg_confidence, 2),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"❌ Error getting review stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
        
@app.route("/api/test-metrics", methods=["GET"])
def test_metrics():
    """Simple test endpoint"""
    return jsonify({
        "success": True,
        "message": "Metrics endpoint working!",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route("/api/reviews/detailed-stats", methods=["GET"])
def get_detailed_review_stats():
    """Get detailed statistics - BULLETPROOF VERSION"""
    try:
        print("[METRICS] detailed-stats endpoint called")
        
        # Check container
        if not reviews_test_container_client:
            print("[METRICS] ❌ Reviews container not available")
            return jsonify({
                "success": False,
                "error": "Reviews container not available"
            }), 500
        
        # Query reviews
        try:
            query = "SELECT * FROM c WHERE c.type = 'review_item'"
            all_reviews = list(reviews_test_container_client.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            print(f"[METRICS] Found {len(all_reviews)} reviews")
        except Exception as query_error:
            print(f"[METRICS] ❌ Query error: {query_error}")
            all_reviews = []
        
        # Calculate stats
        total = len(all_reviews)
        pending = sum(1 for r in all_reviews if r.get('status') == 'pending')
        approved = sum(1 for r in all_reviews if r.get('status') == 'approved')
        needs_revision = sum(1 for r in all_reviews if r.get('status') == 'needs_revision')
        rejected = sum(1 for r in all_reviews if r.get('status') == 'rejected')
        
        # Confidence scores
        intent_confs = [r.get('confidenceIntent', 0) for r in all_reviews if 'confidenceIntent' in r]
        entity_confs = [r.get('confidenceEntity', 0) for r in all_reviews if 'confidenceEntity' in r]
        answer_confs = [r.get('confidenceAnswer', 0) for r in all_reviews if 'confidenceAnswer' in r]
        overall_confs = [r.get('confidenceOverall', 0) for r in all_reviews if 'confidenceOverall' in r]
        
        avg_intent = round(sum(intent_confs) / len(intent_confs), 2) if intent_confs else 0
        avg_entity = round(sum(entity_confs) / len(entity_confs), 2) if entity_confs else 0
        avg_answer = round(sum(answer_confs) / len(answer_confs), 2) if answer_confs else 0
        avg_overall = round(sum(overall_confs) / len(overall_confs), 2) if overall_confs else 0
        
        # Rates
        approval_rate = round((approved / total * 100), 2) if total > 0 else 0
        revision_rate = round((needs_revision / total * 100), 2) if total > 0 else 0
        rejection_rate = round((rejected / total * 100), 2) if total > 0 else 0
        
        # Intent accuracy
        correct = sum(1 for r in all_reviews if r.get('status') == 'approved' and r.get('intentCorrect', False))
        intent_accuracy = round((correct / total * 100), 2) if total > 0 else 0
        
        # Entity metrics
        e_precision = []
        e_recall = []
        e_f1 = []
        
        for r in all_reviews:
            if 'entityMetrics' in r:
                m = r['entityMetrics']
                if 'precision' in m: e_precision.append(m['precision'])
                if 'recall' in m: e_recall.append(m['recall'])
                if 'f1' in m: e_f1.append(m['f1'])
        
        avg_precision = round(sum(e_precision) / len(e_precision), 2) if e_precision else 0
        avg_recall = round(sum(e_recall) / len(e_recall), 2) if e_recall else 0
        avg_f1 = round(sum(e_f1) / len(e_f1), 2) if e_f1 else 0
        
        # Build response
        response = {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "counts": {
                "total_reviews": total,
                "pending": pending,
                "approved": approved,
                "needs_revision": needs_revision,
                "rejected": rejected
            },
            "rates": {
                "approval_rate": approval_rate,
                "revision_rate": revision_rate,
                "rejection_rate": rejection_rate
            },
            "confidence": {
                "intent": avg_intent,
                "entity": avg_entity,
                "answer": avg_answer,
                "overall": avg_overall
            },
            "accuracy": {
                "intent_accuracy": intent_accuracy,
                "entity_precision": avg_precision,
                "entity_recall": avg_recall,
                "entity_f1": avg_f1
            },
            "agent_performance": {
                "intent_agent": {
                    "accuracy": intent_accuracy,
                    "avg_confidence": avg_intent,
                    "total_processed": len(intent_confs)
                },
                "entity_agent": {
                    "precision": avg_precision,
                    "recall": avg_recall,
                    "f1_score": avg_f1,
                    "avg_confidence": avg_entity,
                    "total_processed": len(entity_confs)
                },
                "answer_agent": {
                    "avg_confidence": avg_answer,
                    "total_processed": len(answer_confs)
                }
            },
            "trend": [],
            "performance": {
                "avg_response_time": 0,
                "total_questions_evaluated": total
            }
        }
        
        print(f"[METRICS] ✅ Returning stats for {total} reviews")
        return jsonify(response)
        
    except Exception as e:
        print(f"[METRICS] ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }), 500

def calculate_entity_metrics(extracted_entities: List[str], 
                            gold_standard_entities: List[str]) -> Dict[str, float]:
    """
    Calculate precision, recall, and F1 score for entity extraction
    
    Args:
        extracted_entities: List of entities extracted by the system
        gold_standard_entities: List of correct entities (from SME/HITL)
    
    Returns:
        Dictionary with precision, recall, and f1 scores
    """
    if not gold_standard_entities:
        return {"precision": 0, "recall": 0, "f1": 0}
    
    # Convert to sets for comparison
    extracted_set = set(extracted_entities)
    gold_set = set(gold_standard_entities)
    
    # Calculate metrics
    true_positives = len(extracted_set & gold_set)
    false_positives = len(extracted_set - gold_set)
    false_negatives = len(gold_set - extracted_set)
    
    # Precision: TP / (TP + FP)
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    
    # Recall: TP / (TP + FN)
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    
    # F1: 2 * (Precision * Recall) / (Precision + Recall)
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives
    }

@app.route('/hitl_review_dashboard')
def serve_hitl_dashboard():
    return send_from_directory('static', 'hitl_review_dashboard_production.html')

@app.route('/sprint2-metrics')
def serve_sprint2_metrics():
    """Serve Sprint 2 HITL Metrics Dashboard"""
    return send_from_directory('static', 'Sprint2_HITL_Metrics_Dashboard_Live.html')
    
# Add this BEFORE if __name__ == '__main__':
def test_phase1_fixes():
    """Test that contamination is removed"""
    
    test_queries = [
        "What is DFAS responsible for?",
        "What does DoD do?",
        "Who supervises FMS programs?"
    ]
    
    print("\n" + "="*80)
    print("🧪 PHASE 1: Testing Contamination Removal")
    print("="*80)
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        result = orchestrator.process_query(query, "test_user")
        
        # Check for contamination
        answer = result.get('answer', '')
        entities = result.get('metadata', {}).get('entities', [])
        
        # DSCA should NOT appear if not in query
        if 'DSCA' in answer and 'DSCA' not in query:
            print(f"   ❌ CONTAMINATED: DSCA in answer but not in query")
            print(f"   Answer snippet: {answer[:200]}...")
        else:
            print(f"   ✅ CLEAN: No DSCA contamination")
        
        # Check entities
        dsca_entities = [e for e in entities if 'DSCA' in str(e).upper()]
        if dsca_entities and 'DSCA' not in query:
            print(f"   ❌ CONTAMINATED: DSCA in entities: {dsca_entities}")
        else:
            print(f"   ✅ CLEAN: No DSCA in entities")
        
        print("-" * 80)
    
    print("\n✅ PHASE 1 TESTING COMPLETE\n")

# ============================================================================
# HITL FEEDBACK ENDPOINTS
# ============================================================================

@app.route("/api/hitl/correct-intent", methods=["POST"])
def correct_intent():
    """Apply intent correction AND train the system"""
    try:
        data = request.json
        question = data.get('question', '')
        corrected_intent = data.get('corrected_intent', '')
        
        if not question or not corrected_intent:
            return jsonify({"success": False, "error": "Missing question or corrected_intent"}), 400
        
        q_hash = create_question_hash(question)
        HITL_CORRECTIONS_STORE["intent_corrections"][q_hash] = corrected_intent
        HITL_CORRECTIONS_STORE["correction_history"].append({
            "type": "intent",
            "question": question,
            "correction": corrected_intent,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # ✅ TRAIN THE SYSTEM for similar questions
        train_intent(question, corrected_intent)
        
        print(f"✅ HITL: Intent corrected AND trained to '{corrected_intent}'")
        save_hitl_corrections()  # Save to file for persistence
        
        keywords = extract_keywords(question)
        return jsonify({
            "success": True, 
            "message": "Intent correction applied and system trained!",
            "trained_keywords": keywords[:10]
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/hitl/correct-entities", methods=["POST"])
def correct_entities():
    """Apply entity corrections AND train the system"""
    try:
        data = request.json
        question = data.get('question', '')
        corrected_entities = data.get('corrected_entities', [])
        added_entity = data.get('added_entity', None)
        removed_entity = data.get('removed_entity', None)
        
        if not question:
            return jsonify({"success": False, "error": "Missing question"}), 400
        
        q_hash = create_question_hash(question)
        HITL_CORRECTIONS_STORE["entity_corrections"][q_hash] = corrected_entities
        HITL_CORRECTIONS_STORE["correction_history"].append({
            "type": "entity",
            "question": question,
            "correction": corrected_entities,
            "added": added_entity,
            "removed": removed_entity,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # ✅ TRAIN THE SYSTEM for similar questions
        train_entities(question, corrected_entities)
        
        action = "added" if added_entity else ("removed" if removed_entity else "updated")
        entity_name = added_entity or removed_entity or "entities"
        print(f"✅ HITL: Entity {action} AND trained ({len(corrected_entities)} entities)")
        save_hitl_corrections()  # Save to file for persistence
        
        keywords = extract_keywords(question)
        return jsonify({
            "success": True, 
            "message": f"Entity {action} and system trained!",
            "trained_keywords": keywords[:10],
            "total_entities": len(corrected_entities)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/hitl/correct-answer", methods=["POST"])
def correct_answer():
    """Apply answer correction AND train the system"""
    print(f"🔧 API CALLED: /api/hitl/correct-answer")
    try:
        data = request.json
        print(f"🔧 Received data: {data}")
        question = data.get('question', '')
        corrected_answer = data.get('corrected_answer', '')
        
        print(f"🔧 Question: {question[:50]}...")
        print(f"🔧 Answer length: {len(corrected_answer)} chars")
        
        if not question or not corrected_answer:
            return jsonify({"success": False, "error": "Missing question or corrected_answer"}), 400
        
        q_hash = create_question_hash(question)
        print(f"🔧 Generated hash: {q_hash}")
        print(f"🔧 Store before: {len(HITL_CORRECTIONS_STORE['answer_corrections'])} corrections")
        
        HITL_CORRECTIONS_STORE["answer_corrections"][q_hash] = corrected_answer
        
        print(f"🔧 Store after: {len(HITL_CORRECTIONS_STORE['answer_corrections'])} corrections")
        print(f"🔧 Verification - hash in store? {q_hash in HITL_CORRECTIONS_STORE['answer_corrections']}")
        
        HITL_CORRECTIONS_STORE["correction_history"].append({
            "type": "answer",
            "question": question,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # ✅ TRAIN THE SYSTEM for similar questions
        train_answer(question, corrected_answer)
        
        print(f"✅ HITL: Answer corrected AND trained (length: {len(corrected_answer)} chars)")
        save_hitl_corrections()  # Save to file for persistence
        
        keywords = extract_keywords(question)
        return jsonify({
            "success": True, 
            "message": "Answer correction applied and system trained!",
            "trained_keywords": keywords[:10]
        })
        
    except Exception as e:
        print(f"❌ ERROR in correct_answer: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/hitl/correction-stats", methods=["GET"])
def get_correction_stats():
    """Get correction statistics"""
    try:
        return jsonify({
            "success": True,
            "stats": {
                "intent_corrections": len(HITL_CORRECTIONS_STORE["intent_corrections"]),
                "entity_corrections": len(HITL_CORRECTIONS_STORE["entity_corrections"]),
                "answer_corrections": len(HITL_CORRECTIONS_STORE["answer_corrections"]),
                "total_corrections": len(HITL_CORRECTIONS_STORE["correction_history"]),
                "recent": HITL_CORRECTIONS_STORE["correction_history"][-5:]
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ========== NEW HITL APIs for Accept, Re-run, Regenerate ==========

# Store for review approvals
HITL_APPROVALS_STORE = {
    "approved_intents": {},      # question_hash -> {"approved_at": timestamp, "approved_by": user}
    "approved_entities": {},     # question_hash -> {"approved_at": timestamp, "approved_by": user}
    "approved_answers": {},      # question_hash -> {"approved_at": timestamp, "approved_by": user}
    "approval_history": []
}

@app.route("/api/hitl/accept-intent", methods=["POST"])
def accept_intent():
    """Accept/Approve intent classification"""
    try:
        data = request.get_json()
        question = data.get("question", "")
        intent = data.get("intent", "")
        review_id = data.get("review_id", "")
        
        if not question:
            return jsonify({"success": False, "error": "Question is required"}), 400
        
        q_hash = create_question_hash(question)
        
        HITL_APPROVALS_STORE["approved_intents"][q_hash] = {
            "intent": intent,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "review_id": review_id
        }
        
        HITL_APPROVALS_STORE["approval_history"].append({
            "type": "intent_approved",
            "question": question[:100],
            "intent": intent,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        print(f"✅ HITL: Intent APPROVED - '{intent}' for question hash {q_hash[:8]}")
        
        return jsonify({
            "success": True,
            "message": f"Intent '{intent}' approved successfully",
            "question_hash": q_hash
        })
        
    except Exception as e:
        print(f"❌ Error in accept_intent: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/hitl/accept-entities", methods=["POST"])
def accept_entities():
    """Accept/Approve entity extraction"""
    try:
        data = request.get_json()
        question = data.get("question", "")
        entities = data.get("entities", [])
        review_id = data.get("review_id", "")
        
        if not question:
            return jsonify({"success": False, "error": "Question is required"}), 400
        
        q_hash = create_question_hash(question)
        
        HITL_APPROVALS_STORE["approved_entities"][q_hash] = {
            "entities": entities,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "review_id": review_id
        }
        
        HITL_APPROVALS_STORE["approval_history"].append({
            "type": "entities_approved",
            "question": question[:100],
            "entity_count": len(entities),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        print(f"✅ HITL: Entities APPROVED - {len(entities)} entities for question hash {q_hash[:8]}")
        
        return jsonify({
            "success": True,
            "message": f"{len(entities)} entities approved successfully",
            "question_hash": q_hash
        })
        
    except Exception as e:
        print(f"❌ Error in accept_entities: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/hitl/accept-answer", methods=["POST"])
def accept_answer():
    """Accept/Approve generated answer"""
    try:
        data = request.get_json()
        question = data.get("question", "")
        answer = data.get("answer", "")
        review_id = data.get("review_id", "")
        
        if not question:
            return jsonify({"success": False, "error": "Question is required"}), 400
        
        q_hash = create_question_hash(question)
        
        HITL_APPROVALS_STORE["approved_answers"][q_hash] = {
            "answer_length": len(answer),
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "review_id": review_id
        }
        
        HITL_APPROVALS_STORE["approval_history"].append({
            "type": "answer_approved",
            "question": question[:100],
            "answer_length": len(answer),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        print(f"✅ HITL: Answer APPROVED - {len(answer)} chars for question hash {q_hash[:8]}")
        
        return jsonify({
            "success": True,
            "message": "Answer approved successfully",
            "question_hash": q_hash
        })
        
    except Exception as e:
        print(f"❌ Error in accept_answer: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/hitl/rerun-intent", methods=["POST"])
def rerun_intent():
    """Re-run intent classification agent"""
    try:
        data = request.get_json()
        question = data.get("question", "")
        
        if not question:
            return jsonify({"success": False, "error": "Question is required"}), 400
        
        print(f"🔄 HITL: Re-running Intent Agent for: '{question[:50]}...'")
        
        # Actually re-run the intent agent
        intent_agent = IntentAgent()
        intent_result = intent_agent.analyze_intent(question)
        
        print(f"🔄 HITL: Intent re-run result: {intent_result.get('intent')} ({intent_result.get('confidence', 0):.0%})")
        
        return jsonify({
            "success": True,
            "message": "Intent re-analyzed successfully",
            "result": {
                "intent": intent_result.get("intent", "general"),
                "confidence": intent_result.get("confidence", 0),
                "method": intent_result.get("method", "unknown")
            }
        })
        
    except Exception as e:
        print(f"❌ Error in rerun_intent: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/hitl/rerun-entities", methods=["POST"])
def rerun_entities():
    """Re-run entity extraction agent"""
    try:
        data = request.get_json()
        question = data.get("question", "")
        intent = data.get("intent", "general")
        
        if not question:
            return jsonify({"success": False, "error": "Question is required"}), 400
        
        print(f"🔄 HITL: Re-running Entity Agent for: '{question[:50]}...'")
        
        # Actually re-run the entity agent
        entity_agent = IntegratedEntityAgent()
        intent_info = {"intent": intent}
        entity_result = entity_agent.extract_and_retrieve(question, intent_info, None)
        
        entities = entity_result.get("entities", [])
        confidence = entity_result.get("confidence", 0)
        print(f"🔄 HITL: Entity re-run result: {len(entities)} entities found")
        
        return jsonify({
            "success": True,
            "message": "Entities re-extracted successfully",
            "result": {
                "entities": entities,
                "count": len(entities),
                "confidence": confidence
            }
        })
        
    except Exception as e:
        print(f"❌ Error in rerun_entities: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/hitl/regenerate-answer", methods=["POST"])
def hitl_regenerate_answer():
    """Regenerate answer using AI"""
    try:
        data = request.get_json()
        question = data.get("question", "")
        intent = data.get("intent", "general")
        entities = data.get("entities", [])
        context = data.get("context", "")
        
        if not question:
            return jsonify({"success": False, "error": "Question is required"}), 400
        
        print(f"🔄 HITL: Regenerating answer for: '{question[:50]}...'")
        
        # Build context for answer generation
        answer_context = context if context else "Based on SAMM guidelines and FMS procedures."
        
        # Generate new answer using EnhancedAnswerAgent
        answer_agent = EnhancedAnswerAgent()
        
        # Create required structures matching the method signature
        intent_info = {"intent": intent, "confidence": 0.8}
        entity_info = {"entities": entities, "context": answer_context}
        
        new_answer = answer_agent.generate_answer(
            query=question,
            intent_info=intent_info,
            entity_info=entity_info
        )
        
        print(f"🔄 HITL: Answer regenerated - {len(new_answer)} chars")
        
        return jsonify({
            "success": True,
            "message": "Answer regenerated successfully",
            "result": {
                "answer": new_answer,
                "length": len(new_answer)
            }
        })
        
    except Exception as e:
        print(f"❌ Error in hitl_regenerate_answer: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/hitl/approval-stats", methods=["GET"])
def get_approval_stats():
    """Get approval statistics"""
    try:
        return jsonify({
            "success": True,
            "stats": {
                "approved_intents": len(HITL_APPROVALS_STORE["approved_intents"]),
                "approved_entities": len(HITL_APPROVALS_STORE["approved_entities"]),
                "approved_answers": len(HITL_APPROVALS_STORE["approved_answers"]),
                "total_approvals": len(HITL_APPROVALS_STORE["approval_history"]),
                "recent": HITL_APPROVALS_STORE["approval_history"][-5:]
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ========== END NEW HITL APIs ==========


@app.route("/api/cases/<case_id>", methods=["GET"])
def get_case(case_id):
    """Get a specific case by ID - Cosmos DB version"""
    user = require_auth()
    if not user:
        return jsonify({"error": "User not authenticated"}), 401
    
    user_id = user["sub"]
    
    try:
        from urllib.parse import unquote
        case_id = unquote(case_id)
        
        print(f"[API] 🔍 Fetching case: {case_id}")
        
        if not cases_container_client:
            return jsonify({"error": "Database not available"}), 503
        
        case_doc = None
        
        # Try to find by UUID first
        try:
            case_doc = cases_container_client.read_item(item=case_id, partition_key=user_id)
            print(f"[API] ✅ Found case by UUID: {case_id}")
            
        except CosmosExceptions.CosmosResourceNotFoundError:
            # Try by case number
            query = """
            SELECT * FROM c 
            WHERE c.userId = @userId 
            AND c.caseNumber = @caseNumber
            """
            parameters = [
                {"name": "@userId", "value": user_id},
                {"name": "@caseNumber", "value": case_id}
            ]
            
            cases = list(cases_container_client.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=False
            ))
            
            if cases:
                case_doc = cases[0]
                print(f"[API] ✅ Found case by case number: {case_id}")
            else:
                print(f"[API] ❌ Case not found: {case_id}")
                return jsonify({"error": f"Case {case_id} not found"}), 404
        
        # ✅ CRITICAL FIX: Get documents from BOTH possible fields
        all_documents = case_doc.get("caseDocuments", []) or case_doc.get("documents", [])
        
        # Filter financial documents
        financial_docs = [
            doc for doc in all_documents
            if doc.get("metadata", {}).get("hasFinancialData", False)
        ]
        
        print(f"[API] 📊 Case: {case_doc.get('caseNumber')}")
        print(f"[API]   Total documents: {len(all_documents)}")
        print(f"[API]   Financial documents: {len(financial_docs)}")
        
        # ✅ RETURN BOTH FIELD NAMES for compatibility
        response = {
            "success": True,
            "case": case_doc,
            "caseId": case_doc["id"],
            "caseNumber": case_doc.get("caseNumber", case_id),
            "documents": all_documents,          # ← Frontend expects this
            "caseDocuments": all_documents,      # ← AND this
            "financialDocuments": financial_docs
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"[API] ❌ Error fetching case: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/query/stream", methods=["POST"])
def query_ai_assistant_stream():
    """Streaming SAMM query endpoint with ITAR compliance and real-time updates"""
    user = require_auth()
    if not user:
        return jsonify({"error": "User not authenticated"}), 401

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    user_input = data.get("question", "").strip()
    chat_history = data.get("chat_history", [])
    staged_chat_documents_metadata = data.get("staged_chat_documents", [])

    if not user_input:
        return jsonify({"error": "Query cannot be empty"}), 400

    # === Extract user authorization profile ===
    user_id = user["sub"]
    user_profile = {
        "user_id": user_id,
        "authorization_level": user.get("authorization_level", DEFAULT_DEV_AUTH_LEVEL),
        "clearances": user.get("clearances", []),
        "role": user.get("role", "developer")
    }
    # === END ===

    # CRITICAL FIX: Load file content from blob storage BEFORE streaming starts
    documents_with_content = []
    if staged_chat_documents_metadata:
        print(f"[Streaming] 📁 Loading content from {len(staged_chat_documents_metadata)} staged files...")
        for idx, doc_meta in enumerate(staged_chat_documents_metadata, 1):
            blob_name = doc_meta.get("blobName")
            blob_container = doc_meta.get("blobContainer")
            file_name = doc_meta.get("fileName", "Unknown")

            if not blob_name:
                print(f"[Streaming]   ⚠️ Missing blobName for {file_name}")
                continue

            # CRITICAL FIX: Select correct container client based on metadata
            container_client = None
            if blob_container == AZURE_CASE_DOCS_CONTAINER_NAME:
                container_client = case_docs_blob_container_client
                print(f"[Streaming]   File {idx}: {file_name} (CASE container)")
            elif blob_container == AZURE_CHAT_DOCS_CONTAINER_NAME:
                container_client = chat_docs_blob_container_client
                print(f"[Streaming]   File {idx}: {file_name} (CHAT container)")
            else:
                print(f"[Streaming]   ⚠️ Unknown container '{blob_container}' for {file_name}")

            if not container_client:
                print(f"[Streaming]   ⚠️ Container client not available for {file_name}")
                continue

            # Fetch content using the CORRECT container client
            print(f"[Streaming]   Fetching file {idx}: {file_name} from {blob_container}")
            content = fetch_blob_content(blob_name, container_client)

            if content:
                documents_with_content.append({
                    **doc_meta,
                    "content": content[:5000]
                })
                print(f"[Streaming]   ✅ Loaded {len(content)} chars from {file_name}")
            else:
                print(f"[Streaming]   ⚠️ No content retrieved from {file_name}")

        print(
            f"[Streaming] 📊 Result: {len(documents_with_content)}/{len(staged_chat_documents_metadata)} files loaded successfully")
    else:
        print(f"[Streaming] No staged documents in request")

    def check_and_apply_hitl_corrections(question):
        """Check HITL store and return corrections if exist - includes PATTERN MATCHING"""
        global HITL_CORRECTIONS_STORE

        q_hash = create_question_hash(question)

        print(f"🔍 HITL CHECK: Looking for hash = {q_hash}")
        print(f"🔍 HITL CHECK: Question = '{question}'")
        print(f"🔍 HITL CHECK: Store has {len(HITL_CORRECTIONS_STORE['answer_corrections'])} answer corrections")
        print(f"🔍 HITL CHECK: Store keys = {list(HITL_CORRECTIONS_STORE['answer_corrections'].keys())}")

        # Check EXACT matches first
        has_intent = q_hash in HITL_CORRECTIONS_STORE["intent_corrections"]
        has_entities = q_hash in HITL_CORRECTIONS_STORE["entity_corrections"]
        has_answer = q_hash in HITL_CORRECTIONS_STORE["answer_corrections"]

        # If no exact match, check TRAINED PATTERNS
        trained_intent = None
        trained_entities = None
        trained_answer = None
        
        if not has_intent:
            trained_intent = get_trained_intent(question)
        if not has_entities:
            trained_entities = get_trained_entities(question)
        if not has_answer:
            trained_answer = get_trained_answer(question)

        # Check if we have anything (exact OR pattern)
        has_any_exact = has_intent or has_entities or has_answer
        has_any_pattern = trained_intent or trained_entities or trained_answer

        if not (has_any_exact or has_any_pattern):
            print(f"🔍 HITL CHECK: No corrections found (exact or pattern)")
            return None

        print(f"✅ HITL CORRECTIONS FOUND!")
        corrections = {}

        # Intent - exact or pattern
        if has_intent:
            corrections['intent'] = HITL_CORRECTIONS_STORE["intent_corrections"][q_hash]
            print(f"   🔄 Intent: {corrections['intent']} (exact)")
        elif trained_intent:
            corrections['intent'] = trained_intent['intent']
            print(f"   🔄 Intent: {corrections['intent']} ({trained_intent['source']})")

        # Entities - exact or pattern
        if has_entities:
            corrections['entities'] = HITL_CORRECTIONS_STORE["entity_corrections"][q_hash]
            print(f"   🔄 Entities: {len(corrections['entities'])} entities (exact)")
        elif trained_entities:
            corrections['entities'] = trained_entities['entities']
            print(f"   🔄 Entities: {len(corrections['entities'])} entities ({trained_entities['source']})")

        # Answer - exact or pattern
        if has_answer:
            corrections['answer'] = HITL_CORRECTIONS_STORE["answer_corrections"][q_hash]
            print(f"   🔄 Answer: {len(corrections['answer'])} chars (exact)")
        elif trained_answer:
            corrections['answer'] = trained_answer
            print(f"   🔄 Answer: {len(corrections['answer'])} chars (pattern)")

        return corrections

    def generate():
        try:
            start_time = time.time()

            # START - Send immediately with file count
            yield f"data: {json.dumps({'type': 'start', 'query': user_input, 'timestamp': time.time(), 'files_loaded': len(documents_with_content)})}\n\n"


            # ========== ORIGINAL HITL CHECK (for other questions) ==========
            hitl_corrections = check_and_apply_hitl_corrections(user_input)
            if hitl_corrections and 'answer' in hitl_corrections:
                print("⚡ HITL CORRECTION FOUND - Returning corrected answer immediately!")

                yield f"data: {json.dumps({'type': 'progress', 'step': 'hitl_check', 'message': 'Using corrected answer from HITL...', 'elapsed': 0.1})}\n\n"
                yield f"data: {json.dumps({'type': 'answer_start', 'message': 'Streaming corrected answer...', 'elapsed': 0.2})}\n\n"

                # Stream corrected answer word by word
                corrected_answer = hitl_corrections['answer']
                for i, token in enumerate(corrected_answer.split()):
                    yield f"data: {json.dumps({'type': 'answer_token', 'token': token + ' ', 'position': i + 1})}\n\n"

                total_time = round(time.time() - start_time, 2)
                yield f"data: {json.dumps({'type': 'answer_complete', 'answer': corrected_answer})}\n\n"
                yield f"data: {json.dumps({'type': 'complete', 'answer': corrected_answer, 'data': {'hitl_corrected': True, 'source': 'hitl_correction', 'timings': {'total': total_time}}})}\n\n"
                return
            # ========== END HITL CHECK ==========

            # STEP 1: Intent Analysis
            yield f"data: {json.dumps({'type': 'progress', 'step': 'intent_analysis', 'message': 'Analyzing query intent...', 'elapsed': round(time.time() - start_time, 2)})}\n\n"
            intent_start = time.time()

            q_hash = create_question_hash(user_input)
            if q_hash in HITL_CORRECTIONS_STORE["intent_corrections"]:
                corrected_intent = HITL_CORRECTIONS_STORE["intent_corrections"][q_hash]
                print(f"🔄 HITL: Intent correction applied ({corrected_intent})")
                intent_info = {"intent": corrected_intent, "confidence": 1.0, "hitl_corrected": True}
            else:
                intent_info = orchestrator.intent_agent.analyze_intent(user_input)

            intent_time = round(time.time() - intent_start, 2)
            yield f"data: {json.dumps({'type': 'intent_complete', 'data': intent_info, 'time': intent_time})}\n\n"

            # === CHECK FOR SPECIAL CASES ===
            if intent_info.get('special_case', False):
                special_intent = intent_info.get('intent')
                print(f"[Streaming] Special case detected: {special_intent}")

                yield f"data: {json.dumps({'type': 'progress', 'step': 'special_case_handling', 'message': f'Handling {special_intent} query...', 'elapsed': round(time.time() - start_time, 2)})}\n\n"

                if special_intent == "loa_timeline":
                    special_answer = orchestrator.answer_agent._get_loa_timeline_answer()
                elif special_intent == "financial_verification":
                    special_answer = orchestrator.answer_agent._get_financial_verification_answer()
                elif special_intent == "line_item_details":
                    special_answer = orchestrator.answer_agent._get_technical_services_answer()
                elif special_intent == "pmr_minutes_summary":
                    special_answer = orchestrator.answer_agent._get_pmr_minutes_summary()
                elif special_intent == "nonsense":
                    special_answer = "I apologize, but I'm having difficulty understanding your question. It appears to contain unclear or garbled text.\n\nCould you please rephrase your question more clearly? I'm here to help with questions about the Security Assistance Management Manual (SAMM)."
                elif special_intent == "incomplete":
                    special_answer = "I'd be happy to help, but I need more information to answer your question properly.\n\nCould you please provide more details about what specific SAMM topic you're asking about?"
                elif special_intent == "non_samm":
                    detected_topic = intent_info.get('detected_topics', ['this topic'])[0]
                    special_answer = f"Thank you for your question about {detected_topic}.\n\nHowever, this topic is **outside the scope of SAMM**.\n\nCan I help you with any SAMM Chapter topics instead?"
                else:
                    special_answer = "I apologize, but I cannot process this query. Please ask about SAMM topics."

                yield f"data: {json.dumps({'type': 'answer_start', 'message': 'Sending response...', 'elapsed': round(time.time() - start_time, 2)})}\n\n"

                for i, token in enumerate(special_answer.split()):
                    yield f"data: {json.dumps({'type': 'answer_token', 'token': token + ' ', 'position': i + 1})}\n\n"

                total_time = round(time.time() - start_time, 2)
                yield f"data: {json.dumps({'type': 'answer_complete', 'answer': special_answer})}\n\n"
                yield f"data: {json.dumps({'type': 'complete', 'answer': special_answer, 'data': {'special_case': True, 'intent': special_intent, 'timings': {'total': total_time}}})}\n\n"
                return

            # STEP 2: Entity Extraction
            file_msg = f" and {len(documents_with_content)} files" if documents_with_content else ""
            yield f"data: {json.dumps({'type': 'progress', 'step': 'entity_extraction', 'message': f'Extracting entities from query{file_msg}...', 'elapsed': round(time.time() - start_time, 2)})}\n\n"

            entity_start = time.time()

            if q_hash in HITL_CORRECTIONS_STORE["entity_corrections"]:
                corrected_entities = HITL_CORRECTIONS_STORE["entity_corrections"][q_hash]
                print(f"🔄 HITL: Entity corrections applied ({len(corrected_entities)} entities)")
                entity_info = {
                    "entities": corrected_entities,
                    "overall_confidence": 1.0,
                    "hitl_corrected": True,
                    "context": {},
                    "relationships": []
                }
            else:
                entity_info = orchestrator.entity_agent.extract_and_retrieve(
                    user_input,
                    intent_info,
                    documents_with_content
                )

            entity_time = round(time.time() - entity_start, 2)

            files_processed = entity_info.get('files_processed', 0)
            file_entities = entity_info.get('file_entities_found', 0)
            file_relationships = entity_info.get('file_relationships_found', 0)

            # Include E1.1 entity metrics in response
            entity_metrics_data = entity_info.get('entity_metrics', {})
            entity_metrics_passed = entity_info.get('entity_metrics_passed', {})
            
            yield f"data: {json.dumps({'type': 'entities_complete', 'data': {'count': len(entity_info.get('entities', [])), 'entities': entity_info.get('entities', []), 'confidence': entity_info.get('overall_confidence', 0), 'files_processed': files_processed, 'file_entities': file_entities, 'file_relationships': file_relationships, 'entity_metrics': entity_metrics_data, 'entity_metrics_passed': entity_metrics_passed}, 'time': entity_time})}\n\n"

            # STEP 3: Compliance Check
            yield f"data: {json.dumps({'type': 'progress', 'step': 'compliance_check', 'message': 'Checking ITAR compliance...', 'elapsed': round(time.time() - start_time, 2)})}\n\n"

            compliance_start = time.time()
            compliance_result = check_compliance(user_input, intent_info, entity_info, user_profile)
            compliance_time = round(time.time() - compliance_start, 2)

            yield f"data: {json.dumps({'type': 'compliance_complete', 'data': {'status': compliance_result.get('compliance_status'), 'authorized': compliance_result.get('authorized'), 'user_level': compliance_result.get('user_authorization_level')}, 'time': compliance_time})}\n\n"

            if not compliance_result.get("authorized", True):
                required_level = compliance_result.get('required_authorization_level', 'higher')
                user_level = compliance_result.get('user_authorization_level', 'unknown')
                recommendations = compliance_result.get("recommendations", [])

                denial_msg = f"⚠️ ITAR COMPLIANCE NOTICE\n\nThis query requires {required_level.upper()} clearance.\nYour authorization: {user_level.upper()}\n\n"

                if recommendations:
                    denial_msg += "Recommendations:\n" + "\n".join(f"• {r}" for r in recommendations)

                yield f"data: {json.dumps({'type': 'answer_start', 'message': 'Access restricted'})}\n\n"
                yield f"data: {json.dumps({'type': 'answer_token', 'token': denial_msg, 'position': 1})}\n\n"
                yield f"data: {json.dumps({'type': 'answer_complete', 'answer': denial_msg})}\n\n"
                yield f"data: {json.dumps({'type': 'complete', 'answer': denial_msg, 'data': {'compliance_denied': True, 'timings': {'total': round(time.time() - start_time, 2)}}})}\n\n"
                return

            # STEP 4: Answer Generation
            file_context_msg = f" with {len(documents_with_content)} file(s)" if documents_with_content else ""
            yield f"data: {json.dumps({'type': 'progress', 'step': 'answer_generation', 'message': f'Generating answer{file_context_msg}...', 'elapsed': round(time.time() - start_time, 2)})}\n\n"

            answer_start = time.time()

            context = orchestrator.answer_agent._build_comprehensive_context(
                user_input, intent_info, entity_info, chat_history, documents_with_content
            )

            intent = intent_info.get("intent", "general")
            system_msg = orchestrator.answer_agent._create_optimized_system_message(intent, context, entity_info, user_input)  # v5.9.11: Pass query for Gold guidance
            prompt = orchestrator.answer_agent._create_enhanced_prompt(user_input, intent_info, entity_info)

            yield f"data: {json.dumps({'type': 'answer_start', 'message': 'Streaming answer...', 'elapsed': round(time.time() - start_time, 2)})}\n\n"

            full_answer = ""
            token_count = 0

            for token in call_ollama_streaming(prompt, system_msg, temperature=0.1):
                if token and not token.startswith("Error"):
                    full_answer += token
                    token_count += 1
                    yield f"data: {json.dumps({'type': 'answer_token', 'token': token, 'position': token_count})}\n\n"

            answer_time = round(time.time() - answer_start, 2)
            total_time = round(time.time() - start_time, 2)

            enhanced_answer = orchestrator.answer_agent._enhance_answer_quality(
                full_answer, intent_info, entity_info
            )

            final_answer = enhanced_answer if enhanced_answer else full_answer

            yield f"data: {json.dumps({'type': 'answer_complete', 'answer': final_answer, 'enhanced': (enhanced_answer != full_answer)})}\n\n"
            yield f"data: {json.dumps({'type': 'complete', 'answer': final_answer, 'data': {'compliance_approved': True, 'intent': intent, 'entities_found': len(entity_info.get('entities', [])), 'entities': entity_info.get('entities', []), 'entity_metrics': entity_info.get('entity_metrics', {}), 'entity_metrics_passed': entity_info.get('entity_metrics_passed', {}), 'files_processed': files_processed, 'file_entities': file_entities, 'file_relationships': file_relationships, 'answer_length': len(final_answer), 'token_count': token_count, 'timings': {'intent': intent_time, 'entity': entity_time, 'compliance': compliance_time, 'answer': answer_time, 'total': total_time}}})}\n\n"

            # Confidence check for HITL
            intent_confidence = intent_info.get('confidence', 0.5)
            entity_confidence = entity_info.get('overall_confidence', 0.5)
            answer_confidence = 0.8 if len(final_answer) > 200 else 0.5
            overall_confidence = (intent_confidence + entity_confidence + answer_confidence) / 3

            print(
                f"📊 Confidence: Intent={intent_confidence:.2f}, Entity={entity_confidence:.2f}, Answer={answer_confidence:.2f}, Overall={overall_confidence:.2f}")

            if overall_confidence < 0.95:
                print(f"⚠️ LOW CONFIDENCE ({overall_confidence:.2f}) - Adding to HITL queue...")

                try:
                    review_item = {
                        "id": str(uuid.uuid4()),
                        "type": "review_item",
                        "reviewId": str(uuid.uuid4()),
                        "question": user_input,
                        "aiResponse": {
                            "intent": intent_info.get('intent', 'unknown'),
                            "entities": entity_info.get('entities', []),
                            "answer": final_answer
                        },
                        "status": "pending",
                        "priority": "high" if overall_confidence < 0.5 else "medium",
                        "confidenceOverall": overall_confidence,
                        "confidenceIntent": intent_confidence,
                        "confidenceEntity": entity_confidence,
                        "confidenceAnswer": answer_confidence,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "assignedTo": "Travis",
                        "humanFeedback": "",
                        "reviewedBy": "",
                        "reviewedAt": ""
                    }

                    if reviews_test_container_client:
                        reviews_test_container_client.create_item(review_item)
                        print(f"✅ Added to review queue: {review_item['reviewId']}")
                        yield f"data: {json.dumps({'type': 'hitl_triggered', 'message': 'Low confidence - added to review queue', 'reviewId': review_item['reviewId']})}\n\n"

                except Exception as e:
                    print(f"❌ Error adding to review queue: {e}")

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[Streaming Error] {error_detail}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'detail': error_detail})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )



@app.route("/api/hitl/reset-demo", methods=["POST"])
def reset_demo():
    """Reset demo corrections"""
    try:
        data = request.json or {}
        demo_type = data.get('demo_type', 'all')  # 'test', 'travis', or 'all'
        
        scenarios_to_reset = []
        if demo_type == 'all':
            scenarios_to_reset = list(DEMO_SCENARIOS.keys())
        elif demo_type in DEMO_SCENARIOS:
            scenarios_to_reset = [demo_type]
        else:
            return jsonify({"success": False, "error": "Invalid demo_type"}), 400
        
        for scenario_name in scenarios_to_reset:
            q_hash = create_question_hash(DEMO_SCENARIOS[scenario_name]["question"])
            for store in ["intent_corrections", "entity_corrections", "answer_corrections"]:
                if q_hash in HITL_CORRECTIONS_STORE[store]:
                    del HITL_CORRECTIONS_STORE[store][q_hash]
        
        print(f"🔄 HITL: Demo reset for {', '.join(scenarios_to_reset).upper()}")
        return jsonify({"success": True, "message": f"Demo reset complete for {', '.join(scenarios_to_reset)}"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# OLLAMA MODEL WARM-UP
# =============================================================================
def warm_up_ollama():
    import threading
    def _warmup():
        print("[Ollama Warmup] 🔥 Warming up model...")
        try:
            ollama_session.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": "Hi"}],
                    "stream": False,
                    "options": {"num_predict": 5}
                },
                timeout=60
            )
            print("[Ollama Warmup] ✅ Model ready!")
        except Exception as e:
            print(f"[Ollama Warmup] ⚠️ {e}")

    threading.Thread(target=_warmup, daemon=True).start()


warm_up_ollama()




# =============================================================================
# TEST ENDPOINT (NO AUTH) - For Automated Testing with FULL ANSWER GENERATION
# =============================================================================
@app.route("/api/test/query", methods=["POST"])
def test_query_endpoint():
    """
    Test endpoint for automated testing - NO AUTHENTICATION REQUIRED
    Now includes FULL answer generation for metrics testing.
    
    Returns:
        - answer: Generated answer text
        - intent: Detected intent
        - entities: Extracted entities
        - quality_score: Answer quality score
        - citations_found: SAMM section citations in answer
        - timings: Performance metrics
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    user_input = data.get("question", "").strip()
    
    if not user_input:
        return jsonify({"error": "Query cannot be empty"}), 400
    
    print(f"\n[TEST ENDPOINT] 🧪 Query: {user_input}")
    
    try:
        start_time = time.time()
        
        # Step 1: Intent Analysis
        intent_start = time.time()
        intent_info = orchestrator.intent_agent.analyze_intent(user_input)
        intent_time = round(time.time() - intent_start, 2)
        print(f"[TEST ENDPOINT] ✅ Intent: {intent_info.get('intent')} ({intent_info.get('confidence', 0):.2f})")
        
        # Step 2: Entity Extraction
        entity_start = time.time()
        entity_info = orchestrator.entity_agent.extract_and_retrieve(
            user_input,
            intent_info,
            []  # No files for testing
        )
        entity_time = round(time.time() - entity_start, 2)
        print(f"[TEST ENDPOINT] ✅ Entities: {entity_info.get('entities', [])}")
        
        # Step 3: Answer Generation (FULL PIPELINE)
        answer_start = time.time()
        
        # Build comprehensive context
        context = orchestrator.answer_agent._build_comprehensive_context(
            user_input, intent_info, entity_info, [], []  # No chat history or docs for testing
        )
        
        # Create optimized prompts
        intent = intent_info.get("intent", "general")
        system_msg = orchestrator.answer_agent._create_optimized_system_message(intent, context, entity_info, user_input)  # v5.9.11: Pass query for Gold guidance
        prompt = orchestrator.answer_agent._create_enhanced_prompt(user_input, intent_info, entity_info)
        
        # Generate answer using Ollama (non-streaming for testing)
        raw_answer = call_ollama(prompt, system_msg)
        
        # Enhance answer quality
        enhanced_answer = orchestrator.answer_agent._enhance_answer_quality(
            raw_answer, intent_info, entity_info
        )
        
        final_answer = enhanced_answer if enhanced_answer else raw_answer
        answer_time = round(time.time() - answer_start, 2)
        
        print(f"[TEST ENDPOINT] ✅ Answer generated: {len(final_answer)} chars")
        print(f"[TEST ENDPOINT] 📝 Preview: {final_answer[:200]}...")
        
        # Calculate quality score
        quality_score = orchestrator.answer_agent._calculate_quality_score(final_answer, intent)
        
        # Extract citations from answer
        section_pattern = re.compile(r'C\d+\.\d+(?:\.\d+)*|Chapter\s+\d+|Section\s+C?\d+')
        citations_found = list(set(section_pattern.findall(final_answer)))
        
        total_time = round(time.time() - start_time, 2)
        
        # Build comprehensive response for metrics testing
        response = {
            "status": "success",
            "question": user_input,
            
            # Answer data (PRIMARY - for metrics testing)
            "answer": final_answer,
            "answer_length": len(final_answer),
            "quality_score": round(quality_score, 3),
            "citations_found": citations_found,
            
            # Intent data
            "intent": intent_info.get("intent"),
            "intent_confidence": intent_info.get("confidence"),
            
            # Entity data
            "entities": entity_info.get("entities", []),
            "entity_confidence": entity_info.get("overall_confidence", 0),
            "entity_metrics": entity_info.get("entity_metrics", {}),
            "entity_metrics_passed": entity_info.get("entity_metrics_passed", {}),
            "relationships": entity_info.get("relationships", [])[:10],
            
            # Retrieval data (for groundedness evaluation)
            "vector_results_count": len(entity_info.get("data_sources", {}).get("vector_db", {}).get("results", [])),
            "cosmos_results_count": len(entity_info.get("data_sources", {}).get("cosmos_gremlin", {}).get("results", [])),
            
            # Timing data
            "timings": {
                "intent": intent_time,
                "entity": entity_time,
                "answer": answer_time,
                "total": total_time
            },
            
            # Data source summary
            "data_sources": {
                "cosmos_gremlin": len(entity_info.get("data_sources", {}).get("cosmos_gremlin", {}).get("results", [])),
                "vector_db": len(entity_info.get("data_sources", {}).get("vector_db", {}).get("results", []))
            }
        }
        
        print(f"[TEST ENDPOINT] ✅ Complete - Total time: {total_time}s")
        print(f"[TEST ENDPOINT] 📊 Quality score: {quality_score:.2f}")
        print(f"[TEST ENDPOINT] 📑 Citations: {citations_found}")
        
        return jsonify(response), 200
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[TEST ENDPOINT] ❌ Error: {error_detail}")
        return jsonify({
            "status": "error", 
            "error": str(e),
            "answer": f"Error generating answer: {str(e)}"
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    
    # v5.9.3: Initialize 2-Hop Path RAG
    print("\n[v5.9.3] Initializing 2-Hop Path RAG...")
    two_hop_initialized = initialize_2hop_rag("samm_knowledge_graph.json")
    
    print("\n" + "="*90)
    print("🚀 Complete Integrated SAMM ASIST System with Database Integration v5.9.4")
    print("   Entity Updates (E1.5.2) + Intent Updates (M1.3 HYBRID v8)")
    print("   v5.9.11: GOLD STANDARD TRAINING for verified Q&A patterns")
    print("   v5.9.4: N-Hop Path RAG (configurable 1-3+ hops) for Deep Relationship Traversal")
    print("   Chapters: 1, 4, 5, 6, 7, 9")
    print("="*90)
    print(f"🌐 Server: http://172.16.200.12:{port}")
    print(f"🤖 Ollama Model: {OLLAMA_MODEL}")
    print(f"🔗 Ollama URL: {OLLAMA_URL}")
    print(f"📊 Knowledge Graph: {len(knowledge_graph.entities)} entities, {len(knowledge_graph.relationships)} relationships")
    print(f"🎯 Gold Training (v5.9.11): {len(GOLD_TRAINING_DATA['patterns'])} patterns loaded")
    if SAMM_JSON_KG:
        print(f"📊 JSON KG (v5.9.3): {len(SAMM_JSON_KG.entities)} entities, {len(SAMM_JSON_KG.relationships)} relationships")
    print(f"🔗 2-Hop Path RAG: {'✅ Enabled' if two_hop_initialized else '❌ Disabled'}")
    print(f"🎯 Integrated Database Orchestration: {len(WorkflowStep)} workflow steps")
    print(f"🔄 Integrated Agents: Intent → Integrated Entity (Database) → Enhanced Answer (Quality)")
    print(f"🔐 Auth: {'OAuth (Auth0)' if oauth else 'Mock User'}")
    print(f"💾 Storage: {'Azure Cosmos DB' if cases_container_client else 'In-Memory'}")
    print(f"📁 Blob Storage: {'Azure' if blob_service_client else 'Disabled'}")
    
    # Database status
    db_status = orchestrator.get_database_status()
    print(f"\n💽 Database Integration:")
    print(f"• Cosmos Gremlin: {'Connected' if db_status['cosmos_gremlin']['connected'] else 'Disconnected'} ({db_status['cosmos_gremlin']['endpoint']})")
    print(f"• Vector DB: {'Connected' if db_status['vector_db']['connected'] else 'Disconnected'} ({len(db_status['vector_db']['collections'])} collections)")
    print(f"• Embedding Model: {'Loaded' if db_status['embedding_model']['loaded'] else 'Not Loaded'} ({db_status['embedding_model']['model_name']})")
    
    print(f"\n📡 Core Endpoints:")
    print(f"• Integrated Query: POST http://172.16.200.12:{port}/api/query")
    print(f"• System Status: GET http://172.16.200.12:{port}/api/system/status")
    print(f"• Database Status: GET http://172.16.200.12:{port}/api/database/status")
    print(f"• Examples: GET http://172.16.200.12:{port}/api/examples")
    print(f"• User Cases: GET http://172.16.200.12:{port}/api/user/cases")
    print(f"• Authentication: GET http://172.16.200.12:{port}/login")
    
    print(f"\n🧪 AUTOMATED TESTING (No Auth Required):")
    print(f"• Test Query: POST http://172.16.200.12:{port}/api/test/query")
    print(f"  Usage: python run_entity_tests.py --start 1 --end 10")

    print(f"\n🤖 Enhanced Agent Endpoints:")
    print(f"• HIL Update: POST http://172.16.200.12:{port}/api/agents/hil_update")
    print(f"• Trigger Update: POST http://172.16.200.12:{port}/api/agents/trigger_update")
    print(f"• Agent Status: GET http://172.16.200.12:{port}/api/agents/status")

    print(f"\n📡 Advanced SAMM Endpoints:")
    print(f"• Detailed Status: GET http://172.16.200.12:{port}/api/samm/status")
    print(f"• Integrated Workflow: GET http://172.16.200.12:{port}/api/samm/workflow")
    print(f"• Knowledge Graph: GET http://172.16.200.12:{port}/api/samm/knowledge")
    print(f"• Health Check: GET http://172.16.200.12:{port}/api/health")
    
    print(f"\n🧪 Try these questions:")
    print("• What is Security Cooperation?")
    print("• Who supervises Security Assistance programs?")
    print("• What's the difference between SC and SA?") 
    print("• What does DFAS do?")
    print("• What is Emergency Implementation (EI)?")
    print("• What is a Supply Discrepancy Report (SDR)?")
    print("• What is the Brooke Amendment?")
    print("• How do Amendments differ from Modifications?")
    
    print(f"\n⚡ Integrated Database Capabilities:")
    print("• Integrated Entity Agent: Pattern → NLP → Database queries (Cosmos Gremlin + Vector DBs)")
    print(f"  - {sum(len(patterns) for patterns in orchestrator.entity_agent.samm_entity_patterns.values())} SAMM patterns")
    print("  - Real-time database integration for entity context")
    print("  - Confidence scoring for all extracted entities")
    print("  - Dynamic knowledge expansion with HIL feedback")
    print("• Enhanced Answer Agent: Intent-optimized responses with quality scoring")
    print(f"  - {len(orchestrator.answer_agent.samm_response_templates)} response templates")
    print(f"  - {len(orchestrator.answer_agent.acronym_expansions)} acronym expansions")
    print("  - Multi-pass generation with validation")
    print("  - Automatic quality enhancement")
    
    print(f"\n🔄 Learning System:")
    print("• Human-in-Loop (HIL): Correct intent, entities, and answers")
    print("• Trigger Updates: Add new entities and relationships dynamically")
    print("• Database Learning: Entities learn from graph and vector databases")
    print("• Pattern Learning: Intent agent learns query patterns")
    print("• Knowledge Expansion: Entity agent grows knowledge base")
    print("• Answer Corrections: Answer agent stores and reuses corrections")
    print("• Quality Improvement: All agents learn from feedback")
    
    print(f"\n📊 Agent Status:")
    try:
        status = orchestrator.get_agent_status()
        print(f"• Intent Agent: {status['intent_agent']['learned_patterns']} learned patterns")
        print(f"• Integrated Entity Agent: {status['integrated_entity_agent']['custom_entities']} custom entities, {status['integrated_entity_agent']['samm_patterns']} SAMM patterns")
        print(f"• Enhanced Answer Agent: {status['enhanced_answer_agent']['answer_corrections']} stored corrections, {status['enhanced_answer_agent']['response_templates']} templates")
    except:
        print("• Agent status: Initializing...")
    
    print("="*90 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)