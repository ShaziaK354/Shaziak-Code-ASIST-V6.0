# ASIST V5.9.4 - AI Security Assistance Management System

**Complete Integrated SAMM System with Multi-Agent Architecture, N-Hop Path RAG, and Intelligent Learning**

[![Version](https://img.shields.io/badge/version-5.9.4-blue.svg)](https://github.com/ShaziaK354/Shaziak-Code-ASIST-V6.0)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/vue.js-3.x-brightgreen.svg)](https://vuejs.org/)
[![LLM](https://img.shields.io/badge/LLM-Llama%203.1%3A8B-orange.svg)](https://ollama.ai/)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Multi-Agent Architecture](#multi-agent-architecture)
- [N-Hop Path RAG](#n-hop-path-rag)
- [Training System](#training-system)
- [HITL System](#human-in-the-loop-hitl-system)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Performance Metrics](#performance-metrics)
- [Version History](#version-history)

---

## Overview

ASIST (AI Security Assistance Information System & Toolkit) is an advanced AI-powered RAG (Retrieval-Augmented Generation) platform designed for answering complex queries about the **Security Assistance Management Manual (SAMM)**. The system leverages a multi-agent architecture, N-Hop Path RAG for deep relationship traversal, and multi-database integration to provide accurate, context-aware responses with full citation support.

### Supported SAMM Chapters
- Chapter 1: Security Cooperation Overview
- Chapter 4: Foreign Military Sales (FMS)
- Chapter 5: FMS Case Implementation
- Chapter 6: Financial Management
- Chapter 7: Transportation and Logistics
- Chapter 9: Program Management

---

## Key Features

| Feature | Description |
|---------|-------------|
| Multi-Agent AI System | Intent, Entity, and Answer agents with specialized roles |
| N-Hop Path RAG | Configurable 1-3+ hop relationship traversal for deep knowledge extraction |
| Intelligent Training | SME corrections improve future responses for similar questions (60% keyword match) |
| Human-in-the-Loop (HITL) | Real-time correction interface with learning capabilities |
| Multi-Database Integration | Cosmos Gremlin Graph DB, ChromaDB Vector Store, Azure Cosmos DB |
| Quality Assurance | Citation accuracy, groundedness, and completeness scoring |
| ITAR Compliance | Classification-aware response filtering (Top Secret default) |
| Intelligent Caching | Query normalization with configurable TTL |

---

## System Architecture

```
+-------------------------------------------------------------------------+
|                         ASIST V5.9.4 System                             |
|                    Vue.js Frontend + Flask Backend                       |
+-------------------------------------------------------------------------+
                                    |
                     +--------------+---------------+
                     |                              |
             +-------v--------+          +---------v---------+
             |  Auth0 OAuth   |          |  ITAR Compliance  |
             | Authentication |          |   Microservice    |
             +-------+--------+          +-------------------+
                     |
+--------------------v----------------------------------------------------+
|                     Workflow Orchestration Engine                        |
|  +-------------------------------------------------------------------+  |
|  |                    Workflow State Machine                          |  |
|  |  +---------+   +---------+   +---------+   +---------+            |  |
|  |  | INTENT  |-->| ENTITY  |-->| ANSWER  |-->| QUALITY |            |  |
|  |  |CLASSIFY |   | EXTRACT |   |GENERATE |   | ENHANCE |            |  |
|  |  +---------+   +---------+   +---------+   +---------+            |  |
|  +-------------------------------------------------------------------+  |
+-------------------------------------------------------------------------+
         |                    |                    |
+--------v-------+    +-------v--------+   +-------v---------+
|  Intent Agent  |    |  Entity Agent  |   |  Answer Agent   |
|                |    |  (Integrated)  |   |  (Enhanced)     |
| - Pattern      |    | - NLP Extract  |   | - Templates     |
|   Matching     |    | - N-Hop RAG    |   | - Quality Score |
| - Training     |    | - Confidence   |   | - Training      |
|   System       |    |   Scoring      |   |   System        |
+----------------+    +-------+--------+   +-----------------+
                              |
          +-------------------+-------------------+
          |                   |                   |
  +-------v--------+  +-------v-------+  +-------v-------+
  | Cosmos Gremlin |  |   ChromaDB    |  |  Ollama LLM   |
  |   Graph DB     |  | Vector Store  |  | Llama 3.1:8B  |
  |                |  |               |  |               |
  | - 1663 Entities|  | - 1330 Chunks |  | - Generation  |
  | - 7225 Relations| | - 384-dim     |  | - Reasoning   |
  | - N-Hop Query  |  | - Semantic    |  | - QA Scoring  |
  +----------------+  +---------------+  +---------------+
```

---

## Multi-Agent Architecture

### 1. Intent Agent

**Purpose**: Classify user query intent and determine optimal workflow path

| Component | Details |
|-----------|---------|
| Pattern Matching | 100+ pre-defined SAMM query patterns |
| Training System | Learns from HITL corrections (60% keyword threshold) |
| Confidence Scoring | Intent predictions with confidence metrics |
| Supported Intents | definitional, procedural, entity-focused, comparative, acronym |
| Current Performance | 85% accuracy |

### 2. Integrated Entity Agent

**Purpose**: Extract and contextualize entities using multi-source integration

| Component | Details |
|-----------|---------|
| SAMM Patterns | 1,028 entity patterns across all chapters |
| N-Hop Path RAG | 1-3+ hop relationship traversal |
| Database Integration | Cosmos Gremlin + ChromaDB queries |
| Confidence Scoring | Multi-source confidence aggregation |
| Current Performance | 82% F1 Score |

### 3. Enhanced Answer Agent

**Purpose**: Generate high-quality, intent-optimized responses

| Component | Details |
|-----------|---------|
| Response Templates | 14 intent-specific templates |
| Acronym Expansions | 595 SAMM acronyms |
| Quality Scoring | Automatic quality assessment |
| Training System | Learns from SME corrections |
| Citation Extraction | Automatic SAMM section references |
| Current Performance | 78% quality score |

---

## N-Hop Path RAG

The N-Hop Path RAG system (introduced in v5.9.3) enables deep relationship traversal for complex queries requiring multi-step reasoning.

### How It Works

```
Query: "Who supervises Security Assistance?"

Step 1 - Entity Extraction:
   Identified entities: [Security Assistance, SA]

Step 2 - N-Hop Traversal (2 hops):
   SA --supervised_by--> SECSTATE
   SA --part_of--> Security Cooperation
   Security Cooperation --overseen_by--> SECDEF

Step 3 - Path Assembly:
   Primary chain: SA --> SECSTATE (direct supervision)
   Extended chain: SA --> Security Cooperation --> SECDEF

Step 4 - Answer Generation:
   Response includes full authority chain with citations
```

### Configuration

```python
# Knowledge Graph Statistics
Entities: 1,663
Relationships: 7,225
Graph Nodes: 1,276

# Traversal Settings
MAX_HOPS = 2  # Default, configurable up to 3+
```

### Supported Relationship Types

| Relationship | Inverse |
|--------------|---------|
| supervised_by | supervises |
| reports_to | manages |
| part_of | contains |
| related_to | implements |
| authorized_by | authorizes |

---

## Training System

ASIST V5.9.4 introduces an intelligent training system that learns from SME corrections.

### Answer Training

When an SME corrects an answer:
1. System extracts keywords from the question
2. Pattern is saved: `{keywords: [...], correct_answer: "..."}`
3. Future similar questions (60%+ keyword match) receive the trained answer

**Storage**: `answer_training.json`

### Intent Training

When an SME corrects intent classification:
1. System extracts keywords from the question
2. Pattern is saved: `{keywords: [...], correct_intent: "..."}`
3. Future similar questions use the trained intent

**Storage**: `intent_training.json`

### Similarity Algorithm

```python
def calculate_similarity(query_keywords, trained_keywords):
    overlap = len(set(query_keywords) & set(trained_keywords))
    return overlap / len(trained_keywords)

SIMILARITY_THRESHOLD = 0.6  # 60% keyword match required
```

---

## Human-in-the-Loop (HITL) System

### HITL Review Dashboard

The system includes two production-ready dashboards:

**1. HITL Review Interface** (`hitl_review_dashboard_production_UPDATED.html`)
- Review queue with pending items sorted by confidence
- Confidence display for Intent, Entity, and Relevance
- Inline answer editing
- Intent correction dropdown
- Entity tagging (correct/hallucinated/missing)
- Automatic training integration

**2. HITL Metrics Dashboard** (`Sprint2_HITL_Dashboard_Horizontal_Bars_Final.html`)
- Real-time metrics visualization
- Agent performance comparison
- Approval rate tracking
- Confidence score trends
- Auto-refresh capability (30-second intervals)

### Current Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Intent Accuracy | 85% | 90% |
| Entity F1 Score | 82% | 85% |
| Answer Quality | 78% | 85% |
| Entity Hallucinations | 12% | <10% |
| Overall System | 85% | 90% |

---

## Technology Stack

| Layer | Technology | Version/Details |
|-------|------------|-----------------|
| Frontend | Vue.js | 3.x with Vite |
| State Management | Pinia | Latest |
| Backend | Flask | Python 3.9+ |
| LLM | Ollama | Llama 3.1:8B |
| Vector Database | ChromaDB | 1,330 chunks |
| Graph Database | Azure Cosmos DB | Gremlin API |
| Document Database | Azure Cosmos DB | SQL API |
| Blob Storage | Azure Blob Storage | Case documents |
| Authentication | Auth0 | OAuth 2.0 |
| Embeddings | SentenceTransformers | all-MiniLM-L6-v2 (384-dim) |

---

## Installation

### Prerequisites

- Python 3.9 or higher
- Node.js 16 or higher
- Ollama with Llama 3.1:8B model
- Azure account (Cosmos DB, Blob Storage)
- Auth0 account (optional, for production auth)

### Step 1: Clone Repository

```bash
git clone https://github.com/ShaziaK354/Shaziak-Code-ASIST-V6.0.git
cd Shaziak-Code-ASIST-V6.0
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Frontend Setup

```bash
cd asist-vue-frontend

# Install dependencies
npm install

# Build for production
npm run build
```

### Step 4: Ollama Setup

```bash
# Install Ollama from https://ollama.ai/

# Pull the model
ollama pull llama3.1:8b

# Start Ollama server
ollama serve
```

### Step 5: Run Application

```bash
cd backend
python app_5_9_4_WITH_TRAINING.py
```

Application will be available at: `http://localhost:3000`

---

## Configuration

Create a `.env` file in the `backend` directory:

```env
# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Azure Cosmos DB (Document Storage)
COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-key
DATABASE_NAME=ASIST_DATA
CASES_CONTAINER_NAME=Cases

# Azure Cosmos DB (Gremlin - Graph Database)
COSMOS_GREMLIN_ENDPOINT=your-endpoint.gremlin.cosmos.azure.com
COSMOS_GREMLIN_DATABASE=ASIST-DB
COSMOS_GREMLIN_COLLECTION=Agent1
COSMOS_GREMLIN_KEY=your-gremlin-key

# Azure Blob Storage
AZURE_CONNECTION_STRING=your-connection-string
AZURE_CASE_DOCS_CONTAINER_NAME=casedocuments
AZURE_CHAT_DOCS_CONTAINER_NAME=chatattachments

# Auth0
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
APP_SECRET_KEY=your-secret-key

# ITAR Compliance
COMPLIANCE_SERVICE_URL=http://localhost:3002
COMPLIANCE_ENABLED=true
DEFAULT_DEV_AUTH_LEVEL=top_secret

# Cache Configuration
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=1000
```

---

## API Reference

### Core Query Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/query` | Main integrated query | Yes |
| POST | `/api/test/query` | Test endpoint | No |
| GET | `/api/examples` | Sample queries | No |

### Query Request Example

```bash
POST /api/query
Content-Type: application/json

{
  "question": "What is Security Cooperation?",
  "case_id": "optional-case-id"
}
```

### Query Response Example

```json
{
  "answer": "Security Cooperation (SC) encompasses all DoD interactions...",
  "confidence": 0.92,
  "intent": "definition",
  "entities": [
    {"name": "Security Cooperation", "type": "concept", "confidence": 0.95}
  ],
  "citations_found": ["C1.2.3", "Chapter 1"],
  "quality_score": 0.88,
  "timings": {
    "intent": 0.2,
    "entity": 0.5,
    "answer": 2.3,
    "total": 3.0
  }
}
```

### HITL Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hitl/pending-reviews` | Get pending reviews |
| POST | `/api/hitl/correct-answer` | Submit answer correction (triggers training) |
| POST | `/api/hitl/correct-intent` | Submit intent correction (triggers training) |
| POST | `/api/hitl/accept/{id}` | Accept review |
| POST | `/api/hitl/reject/{id}` | Reject review |
| POST | `/api/hitl/reset-demo` | Reset demo corrections |

### System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | System health check |
| GET | `/api/system/status` | Detailed system status |
| GET | `/api/database/status` | Database connection status |
| GET | `/api/agents/status` | Agent statistics |
| GET | `/api/cache/stats` | Cache performance metrics |
| GET | `/api/samm/status` | SAMM-specific status |
| GET | `/api/samm/knowledge` | Knowledge graph statistics |

---

## Performance Metrics

### Response Times

| Operation | Time |
|-----------|------|
| Intent Classification | ~0.2s |
| Entity Extraction | ~0.5s |
| Answer Generation | ~2-3s |
| Total Query Processing | ~3-5s |
| Cached Query | ~0.1s |
| N-Hop Traversal | ~50-100ms |

### Database Statistics

| Database | Metric | Value |
|----------|--------|-------|
| Cosmos Gremlin | Entities | 1,663 |
| Cosmos Gremlin | Relationships | 7,225 |
| ChromaDB | Chunks | 1,330 |
| ChromaDB | Embedding Dimensions | 384 |
| Knowledge Graph | Graph Nodes | 1,276 |

### System Statistics

| Component | Count |
|-----------|-------|
| SAMM Entity Patterns | 1,028 |
| Response Templates | 14 |
| Acronym Expansions | 595 |
| Workflow Steps | 6 |

---

## Project Structure

```
ASIST_V2.1/
├── asist-vue-frontend/              # Vue.js Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/                # Chat interface components
│   │   │   ├── dashboard/           # Dashboard panels
│   │   │   └── layout/              # Layout components
│   │   ├── stores/                  # Pinia state management
│   │   ├── services/                # API services
│   │   └── router/                  # Vue Router configuration
│   ├── public/                      # Static assets
│   └── package.json
│
├── backend/
│   ├── app_5_9_4_WITH_TRAINING.py   # Main application (current version)
│   ├── samm_knowledge_graph.json    # Knowledge graph data
│   ├── Chromadb/                    # Vector databases
│   │   └── samm_all_chapters_db/    # All SAMM chapters (1,330 chunks)
│   ├── data_loader/                 # Data ingestion agents
│   ├── entity_answer_agents/        # Agent implementations
│   ├── static/                      # HITL dashboards
│   │   ├── hitl_review_dashboard_production_UPDATED.html
│   │   └── Sprint2_HITL_Dashboard_Horizontal_Bars_Final.html
│   ├── hitl_learning_data/          # Learning data storage
│   │   ├── answer_training.json
│   │   └── intent_training.json
│   ├── hitl_corrections.json        # HITL corrections storage
│   ├── requirements.txt
│   └── .env.example
│
├── .gitignore
└── README.md
```

---

## Version History

### v5.9.4 (December 2025) - Current

- Added Answer Training System for similar questions (60% keyword match)
- Added Intent Training System for similar questions
- Persistent storage: `answer_training.json` and `intent_training.json`
- HITL corrections now train the system automatically
- SME corrections improve future responses for similar questions

### v5.9.3

- Introduced N-Hop Path RAG for multi-hop relationship traversal
- Added JSON Knowledge Graph loader (SAMMKnowledgeGraph class)
- Added TwoHopPathFinder class with BFS-based path finding
- Authority/supervision chain detection
- Enhanced entity extraction for better acronym matching

### v5.9.1

- Increased Ollama timeout: 180s to 200s
- Increased Cosmos timeout: 120s to 200s
- Added quality instructions to system prompts
- Improved citation accuracy: 45% to 80%+
- Improved groundedness: 52% to 80%+
- Improved completeness: 55% to 85%+

### v5.0

- Multi-agent architecture implementation
- Database integration (Cosmos Gremlin + ChromaDB)
- Basic HITL system

---

## Sample Queries

### Definitional
- What is Security Cooperation?
- Define Foreign Military Sales
- What does DFAS stand for?

### Procedural
- How do I create a new FMS case?
- What are the steps to process a case amendment?

### Entity-Focused
- Who supervises Security Assistance programs?
- What is DSCA's role?

### Comparative
- What's the difference between SC and SA?
- How do Amendments differ from Modifications?

### Multi-Hop (v5.9.3+)
- Who is the ultimate authority over FMS?
- What oversight chain applies to DSCA?
- What is the Brooke Amendment?
- What is Emergency Implementation (EI)?

---

## Development Team

**AI Tech Lead**: Shazia Kashif ([@ShaziaK354](https://github.com/ShaziaK354))

---

## License

Private and Confidential - ITAR Controlled

---

## Acknowledgments

- Defense Security Cooperation Agency (DSCA) for SAMM documentation
- Ollama team for local LLM capabilities
- ChromaDB for vector storage solution
- Microsoft Azure for cloud infrastructure
