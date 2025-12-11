"""
SAMM Answering Agent - Automated Metrics Testing Framework v2
With better debugging and support for different response formats

FIXES:
- Better answer extraction from different API response formats
- Debug mode to see raw API responses
- Support for streaming endpoints
"""

import requests
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
import pandas as pd

# ============================================================================
# CONFIGURATION
# ============================================================================

# CHANGE THIS TO YOUR ACTUAL API URL
API_BASE_URL = "http://127.0.0.1:3000"

# Available endpoints - try in order until one works
ENDPOINTS = {
    "test": "/api/test/query",           # Test endpoint (no auth)
    "test_simple": "/api/test/query/simple",  # Simpler test endpoint
    "main": "/api/query",                # Main endpoint (may need auth)
}

# Use this endpoint
ACTIVE_ENDPOINT = "test"

# Metric Thresholds from Dashboard
THRESHOLDS = {
    "completeness": 0.95,
    "groundedness": 0.98,
    "citation_accuracy": 0.95,
    "quality_score": 0.80,
    "confidence_score": 0.85
}

# Quality Score Weights (from dashboard)
QUALITY_WEIGHTS = {
    "section_citations": 0.25,
    "acronym_expansion": 0.15,
    "length": 0.25,
    "samm_terms": 0.20,
    "structure": 0.15
}

# ============================================================================
# CHAPTER 1 GROUND TRUTH DATA
# ============================================================================

CHAPTER_1_GROUND_TRUTH = {
    "C1.1.1": {
        "section": "C1.1.1",
        "title": "Definition and Purpose",
        "key_content": [
            "Security cooperation (SC) comprises all activities undertaken by the DoD to encourage and enable international partners",
            "includes all DoD interactions with foreign defense and security establishments",
            "all DoD-administered security assistance (SA) programs",
            "build defense and security relationships",
            "promote specific U.S. security interests",
            "develop allied and friendly military capabilities",
            "provide U.S. forces with peacetime and contingency access"
        ],
        "required_terms": ["Security Cooperation", "DoD", "international partners", "Security Assistance"]
    },
    "C1.1.2": {
        "section": "C1.1.2",
        "title": "Distinguishing Between Security Cooperation and Security Assistance Programs",
        "key_content": [
            "SC programs and SA programs are distinguished by the statutes by which they are authorized and funded",
            "Programs of both types provide defense articles, military training, and other defense services"
        ],
        "required_terms": ["SC programs", "SA programs", "statutes", "defense articles"]
    },
    "C1.1.2.1": {
        "section": "C1.1.2.1",
        "title": "Security Cooperation Programs",
        "key_content": [
            "SC program authorizations and appropriations are provided to the Secretary of Defense",
            "primarily under the annual National Defense Authorization Act (NDAA)",
            "By statute or Executive Order (EO), sometimes required to be exercised in coordination with the Secretary of State"
        ],
        "required_terms": ["NDAA", "Secretary of Defense", "Executive Order"]
    },
    "C1.1.2.2": {
        "section": "C1.1.2.2",
        "title": "Security Assistance Programs",
        "key_content": [
            "SA is a group of programs, authorized under Title 22 authorities",
            "grant, loan, credit, cash sales, or lease",
            "subject to the continuous supervision and general direction of the Secretary of State",
            "Those SA programs that are administered by DoD are a subset of SC"
        ],
        "required_terms": ["Title 22", "Secretary of State", "grant", "loan", "subset"]
    },
    "C1.2.1": {
        "section": "C1.2.1",
        "title": "Legislative Authorities for Security Assistance",
        "key_content": [
            "The Foreign Assistance Act (FAA) of 1961",
            "The Arms Export Control Act (AECA) of 1976",
            "Annual appropriations acts for Foreign Operations"
        ],
        "required_terms": ["FAA", "AECA", "Foreign Assistance Act", "Arms Export Control Act"]
    },
    "C1.2.3": {
        "section": "C1.2.3",
        "title": "Executive Orders for Security Assistance",
        "key_content": [
            "Executive Order (E.O.) 13637",
            "allocates authority and responsibility for SA principally to the Secretary of Defense and the Secretary of State",
            "further delegated to the Deputy Secretary of Defense, to the Under Secretary of Defense for Policy (USD(P)), and finally to the Director, DSCA"
        ],
        "required_terms": ["E.O. 13637", "USD(P)", "DSCA"]
    },
    "C1.3.1": {
        "section": "C1.3.1",
        "title": "Department of State",
        "key_content": [
            "Secretary of State (SECSTATE) is responsible for continuous supervision and general direction of SA programs",
            "determining whether (and when) there will be a program or sale for a particular country",
            "reviews and approves export license requests",
            "United States Munitions List (USML)",
            "International Traffic in Arms Regulations (ITAR)"
        ],
        "required_terms": ["SECSTATE", "USML", "ITAR", "export license"]
    },
    "C1.3.2": {
        "section": "C1.3.2",
        "title": "Department of Defense Organizations",
        "key_content": [
            "Secretary of Defense (SECDEF) establishes military requirements",
            "implements programs to transfer defense articles and services",
            "principal responsible agencies for security cooperation (SC) are DSCA, the Combatant Commands (CCMDs), the Joint Staff (JS), the Security Cooperation Organizations (SCOs), and the Military Departments (MILDEPs)"
        ],
        "required_terms": ["SECDEF", "DSCA", "CCMDs", "MILDEPs"]
    },
    "C1.3.2.1": {
        "section": "C1.3.2.1",
        "title": "Under Secretary of Defense for Policy",
        "key_content": [
            "USD(P) serves as the principal staff assistant and advisor to the SECDEF on SC matters",
            "develops and coordinates DoD guidance",
            "Guidance for the Employment of the Force (GEF)"
        ],
        "required_terms": ["USD(P)", "principal staff assistant", "GEF"]
    },
    "C1.3.2.2": {
        "section": "C1.3.2.2",
        "title": "Defense Security Cooperation Agency",
        "key_content": [
            "DSCA directs, administers, and provides guidance to the DoD Components",
            "Executive Agent (EA) for DoD Regional Centers for Security Studies",
            "DoDD 5105.65"
        ],
        "required_terms": ["DSCA", "DoD Components", "Executive Agent"]
    },
    "C1.3.2.8": {
        "section": "C1.3.2.8",
        "title": "Defense Finance and Accounting Service",
        "key_content": [
            "DFAS performs accounting, billing, disbursing, and collecting functions for SC programs",
            "primary site for SA is DFAS Indianapolis (DFAS-IN)",
            "DoDD 5118.05"
        ],
        "required_terms": ["DFAS", "accounting", "billing", "DFAS-IN"]
    }
}

# ============================================================================
# TEST QUESTIONS FOR CHAPTER 1
# ============================================================================

CHAPTER_1_TEST_QUESTIONS = [
    {
        "id": "Q1",
        "question": "What is Security Cooperation?",
        "expected_section": "C1.1.1",
        "question_type": "definition",
        "required_elements": ["definition", "purpose", "scope"],
        "expected_citations": ["C1.1.1", "Chapter 1"],
        "complexity": "simple"
    },
    {
        "id": "Q2", 
        "question": "What is the difference between Security Cooperation and Security Assistance?",
        "expected_section": "C1.1.2",
        "question_type": "distinction",
        "required_elements": ["SC definition", "SA definition", "key difference", "relationship"],
        "expected_citations": ["C1.1.2", "C1.1.2.1", "C1.1.2.2"],
        "complexity": "medium"
    },
    {
        "id": "Q3",
        "question": "What are the legislative authorities for Security Assistance?",
        "expected_section": "C1.2.1",
        "question_type": "authority",
        "required_elements": ["FAA", "AECA", "appropriations acts"],
        "expected_citations": ["C1.2.1"],
        "complexity": "simple"
    },
    {
        "id": "Q4",
        "question": "Who supervises Security Assistance programs?",
        "expected_section": "C1.3.1",
        "question_type": "authority",
        "required_elements": ["Secretary of State", "supervision", "direction"],
        "expected_citations": ["C1.3.1", "C1.1.2.2"],
        "complexity": "simple"
    },
    {
        "id": "Q5",
        "question": "What is DSCA's role in Security Cooperation?",
        "expected_section": "C1.3.2.2",
        "question_type": "role",
        "required_elements": ["directs", "administers", "guidance", "Executive Agent"],
        "expected_citations": ["C1.3.2.2"],
        "complexity": "simple"
    },
    {
        "id": "Q6",
        "question": "What does DFAS do for Security Cooperation programs?",
        "expected_section": "C1.3.2.8",
        "question_type": "role",
        "required_elements": ["accounting", "billing", "disbursing", "collecting"],
        "expected_citations": ["C1.3.2.8"],
        "complexity": "simple"
    },
    {
        "id": "Q7",
        "question": "What is the role of the Under Secretary of Defense for Policy in SC?",
        "expected_section": "C1.3.2.1",
        "question_type": "role",
        "required_elements": ["principal staff assistant", "advisor", "guidance"],
        "expected_citations": ["C1.3.2.1"],
        "complexity": "simple"
    },
    {
        "id": "Q8",
        "question": "What is Executive Order 13637?",
        "expected_section": "C1.2.3",
        "question_type": "definition",
        "required_elements": ["SA delegations", "Secretary of Defense", "Secretary of State"],
        "expected_citations": ["C1.2.3"],
        "complexity": "simple"
    },
    {
        "id": "Q9",
        "question": "What organizations are the principal responsible agencies for SC within DoD?",
        "expected_section": "C1.3.2",
        "question_type": "list",
        "required_elements": ["DSCA", "CCMDs", "Joint Staff", "SCOs", "MILDEPs"],
        "expected_citations": ["C1.3.2"],
        "complexity": "medium"
    },
    {
        "id": "Q10",
        "question": "What is the relationship between SC and SA programs?",
        "expected_section": "C1.1.2.2",
        "question_type": "relationship",
        "required_elements": ["subset", "Title 22", "DoD administered"],
        "expected_citations": ["C1.1.2.2", "C1.1.2"],
        "complexity": "medium"
    },
    {
        "id": "Q11",
        "question": "What is ITAR and who manages it?",
        "expected_section": "C1.3.1",
        "question_type": "definition",
        "required_elements": ["International Traffic in Arms Regulations", "State", "export"],
        "expected_citations": ["C1.3.1"],
        "complexity": "simple"
    },
    {
        "id": "Q12",
        "question": "What is USML?",
        "expected_section": "C1.3.1",
        "question_type": "definition",
        "required_elements": ["United States Munitions List", "ITAR", "export license"],
        "expected_citations": ["C1.3.1"],
        "complexity": "simple"
    },
    {
        "id": "Q13",
        "question": "What are the three main laws for Security Assistance authorization?",
        "expected_section": "C1.2.1",
        "question_type": "list",
        "required_elements": ["Foreign Assistance Act", "Arms Export Control Act", "appropriations acts"],
        "expected_citations": ["C1.2.1"],
        "complexity": "medium"
    },
    {
        "id": "Q14",
        "question": "How are SC programs funded differently from SA programs?",
        "expected_section": "C1.1.2",
        "question_type": "distinction",
        "required_elements": ["NDAA", "Title 22", "Secretary of Defense", "statutes"],
        "expected_citations": ["C1.1.2.1", "C1.1.2.2"],
        "complexity": "complex"
    },
    {
        "id": "Q15",
        "question": "What does the Secretary of State approve regarding SA?",
        "expected_section": "C1.3.1",
        "question_type": "authority",
        "required_elements": ["export license", "program decisions", "budget", "third party transfers"],
        "expected_citations": ["C1.3.1"],
        "complexity": "medium"
    }
]

# ============================================================================
# METRICS CALCULATION CLASSES
# ============================================================================

@dataclass
class MetricResult:
    """Single metric result"""
    name: str
    score: float
    passed: bool
    threshold: float
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TestResult:
    """Complete test result for one question"""
    question_id: str
    question: str
    answer: str
    response_time_ms: float
    completeness: MetricResult = None
    groundedness: MetricResult = None
    citation_accuracy: MetricResult = None
    quality_score: MetricResult = None
    confidence_score: MetricResult = None
    overall_passed: bool = False
    raw_response: Dict = field(default_factory=dict)

class SAMMMetricsEvaluator:
    """Evaluates answers against SAMM Chapter 1 ground truth"""
    
    def __init__(self, ground_truth: Dict = None):
        self.ground_truth = ground_truth or CHAPTER_1_GROUND_TRUTH
        self.samm_terms = [
            "Security Cooperation", "Security Assistance", "SAMM", 
            "Title 10", "Title 22", "FMS", "DSCA", "DoD", "FAA", "AECA",
            "SECSTATE", "SECDEF", "USD(P)", "CCMDs", "MILDEPs",
            "SCO", "LOA", "IMET", "EDA"
        ]
        self.section_pattern = re.compile(r'C\d+\.\d+(?:\.\d+)*|Chapter\s+\d+|Section\s+C?\d+')
        
    def evaluate_completeness(self, answer: str, test_question: Dict) -> MetricResult:
        """Evaluates if answer addresses all parts of the question."""
        required_elements = test_question.get("required_elements", [])
        if not required_elements:
            return MetricResult("completeness", 1.0, True, THRESHOLDS["completeness"], 
                              {"note": "No required elements specified"})
        
        found_elements = []
        missing_elements = []
        
        answer_lower = answer.lower()
        for element in required_elements:
            element_variations = self._get_element_variations(element)
            if any(var.lower() in answer_lower for var in element_variations):
                found_elements.append(element)
            else:
                missing_elements.append(element)
        
        score = len(found_elements) / len(required_elements)
        
        return MetricResult(
            name="completeness",
            score=score,
            passed=score >= THRESHOLDS["completeness"],
            threshold=THRESHOLDS["completeness"],
            details={
                "found_elements": found_elements,
                "missing_elements": missing_elements,
                "total_required": len(required_elements)
            }
        )
    
    def _get_element_variations(self, element: str) -> List[str]:
        """Get synonyms/variations of an element"""
        variations = {
            "definition": ["definition", "defined as", "refers to", "means", "is", "comprises"],
            "purpose": ["purpose", "objective", "goal", "aim", "intended to", "designed to"],
            "scope": ["scope", "includes", "encompasses", "comprises", "covers", "activities"],
            "subset": ["subset", "part of", "component of", "within", "under"],
            "FAA": ["FAA", "Foreign Assistance Act", "foreign assistance"],
            "AECA": ["AECA", "Arms Export Control Act", "arms export"],
            "appropriations acts": ["appropriations", "funding", "budget"],
            "supervision": ["supervision", "supervise", "oversight", "oversee", "direction"],
            "direction": ["direction", "direct", "guide", "guidance"],
            "Secretary of State": ["Secretary of State", "SECSTATE", "State Department"],
            "DSCA": ["DSCA", "Defense Security Cooperation Agency"],
            "CCMDs": ["CCMDs", "Combatant Commands", "combatant command"],
            "MILDEPs": ["MILDEPs", "Military Departments", "military department"],
            "Joint Staff": ["Joint Staff", "JS", "joint chiefs"],
            "SCOs": ["SCOs", "Security Cooperation Organizations"],
            "accounting": ["accounting", "financial", "fiscal"],
            "billing": ["billing", "bill", "invoice"],
            "disbursing": ["disbursing", "disbursement", "payment"],
            "collecting": ["collecting", "collection", "receive"],
            "directs": ["directs", "direct", "directing", "direction"],
            "administers": ["administers", "administer", "administering", "administration"],
            "guidance": ["guidance", "guide", "policy"],
            "Executive Agent": ["Executive Agent", "EA", "executive agent"],
            "principal staff assistant": ["principal staff assistant", "staff assistant", "advisor"],
            "advisor": ["advisor", "advise", "advisory"],
            "SA delegations": ["delegation", "delegated", "authority"],
            "Secretary of Defense": ["Secretary of Defense", "SECDEF", "defense secretary"],
            "International Traffic in Arms Regulations": ["ITAR", "International Traffic in Arms", "traffic in arms"],
            "export license": ["export license", "license", "export control"],
            "United States Munitions List": ["USML", "Munitions List", "munitions"],
            "program decisions": ["program", "decision", "determine"],
            "third party transfers": ["third party", "transfer", "retransfer"],
            "NDAA": ["NDAA", "National Defense Authorization Act", "defense authorization"],
            "Title 22": ["Title 22", "title 22", "T22"],
            "statutes": ["statute", "law", "legislation", "authorized"],
            "SC definition": ["security cooperation", "SC"],
            "SA definition": ["security assistance", "SA"],
            "key difference": ["difference", "differ", "distinction", "versus", "vs", "unlike"],
            "relationship": ["relationship", "related", "subset", "part of"],
            "DoD administered": ["DoD", "Defense", "administered"],
        }
        return variations.get(element.lower(), [element])
    
    def evaluate_groundedness(self, answer: str, test_question: Dict) -> MetricResult:
        """Evaluates if answer is supported by retrieved documents."""
        expected_section = test_question.get("expected_section", "")
        if not expected_section or expected_section not in self.ground_truth:
            return MetricResult("groundedness", 0.5, False, THRESHOLDS["groundedness"],
                              {"note": "No ground truth available for verification"})
        
        ground_truth_data = self.ground_truth[expected_section]
        key_content = ground_truth_data.get("key_content", [])
        required_terms = ground_truth_data.get("required_terms", [])
        
        answer_lower = answer.lower()
        
        grounded_claims = 0
        total_checkable = len(key_content) + len(required_terms)
        
        for content in key_content:
            content_words = set(content.lower().split())
            answer_words = set(answer_lower.split())
            overlap = len(content_words.intersection(answer_words)) / len(content_words)
            if overlap > 0.3:  # 30% word overlap threshold
                grounded_claims += 1
        
        for term in required_terms:
            if term.lower() in answer_lower:
                grounded_claims += 1
        
        hallucination_indicators = [
            "I believe", "I think", "probably", "might be", "could be",
            "in my opinion", "generally", "usually", "typically"
        ]
        hallucination_count = sum(1 for indicator in hallucination_indicators 
                                  if indicator in answer_lower)
        
        score = (grounded_claims / max(1, total_checkable)) * (1 - 0.1 * hallucination_count)
        score = max(0, min(1, score))
        
        return MetricResult(
            name="groundedness",
            score=score,
            passed=score >= THRESHOLDS["groundedness"],
            threshold=THRESHOLDS["groundedness"],
            details={
                "grounded_claims": grounded_claims,
                "total_checkable": total_checkable,
                "hallucination_indicators_found": hallucination_count,
                "expected_section": expected_section
            }
        )
    
    def evaluate_citation_accuracy(self, answer: str, test_question: Dict) -> MetricResult:
        """Evaluates if citations are correct and verifiable."""
        expected_citations = test_question.get("expected_citations", [])
        found_citations = self.section_pattern.findall(answer)
        found_citations = list(set(found_citations))
        
        if not expected_citations:
            has_citation = len(found_citations) > 0
            return MetricResult("citation_accuracy", 1.0 if has_citation else 0.5, 
                              has_citation, THRESHOLDS["citation_accuracy"],
                              {"note": "No expected citations specified", 
                               "found_citations": found_citations})
        
        correct_citations = []
        incorrect_citations = []
        
        for citation in found_citations:
            is_correct = any(exp.lower() in citation.lower() or 
                           citation.lower() in exp.lower() 
                           for exp in expected_citations)
            if is_correct:
                correct_citations.append(citation)
            else:
                if re.match(r'C\d+\.\d+', citation):
                    correct_citations.append(citation)
                else:
                    incorrect_citations.append(citation)
        
        if not found_citations:
            score = 0.0
        else:
            score = len(correct_citations) / len(found_citations)
        
        expected_found = sum(1 for exp in expected_citations 
                            if any(exp.lower() in fc.lower() for fc in found_citations))
        coverage = expected_found / len(expected_citations) if expected_citations else 1.0
        
        final_score = (score * 0.6) + (coverage * 0.4)
        
        return MetricResult(
            name="citation_accuracy",
            score=final_score,
            passed=final_score >= THRESHOLDS["citation_accuracy"],
            threshold=THRESHOLDS["citation_accuracy"],
            details={
                "found_citations": found_citations,
                "expected_citations": expected_citations,
                "correct_citations": correct_citations,
                "incorrect_citations": incorrect_citations,
                "coverage": coverage
            }
        )
    
    def evaluate_quality_score(self, answer: str, test_question: Dict) -> MetricResult:
        """Evaluates SAMM standards and formatting compliance."""
        scores = {}
        
        citations = self.section_pattern.findall(answer)
        scores["section_citations"] = min(1.0, len(citations) / 2) * QUALITY_WEIGHTS["section_citations"]
        
        acronym_pattern = re.compile(r'\b([A-Z]{2,6})\b')
        acronyms = acronym_pattern.findall(answer)
        expanded_count = sum(1 for acr in acronyms if f"({acr})" in answer or f"{acr} (" in answer)
        if acronyms:
            scores["acronym_expansion"] = (expanded_count / len(set(acronyms))) * QUALITY_WEIGHTS["acronym_expansion"]
        else:
            scores["acronym_expansion"] = QUALITY_WEIGHTS["acronym_expansion"]
        
        question_type = test_question.get("question_type", "general")
        length_guidelines = {
            "definition": {"min": 100, "target": 300, "max": 600},
            "distinction": {"min": 200, "target": 500, "max": 1000},
            "authority": {"min": 100, "target": 250, "max": 500},
            "role": {"min": 100, "target": 300, "max": 600},
            "list": {"min": 150, "target": 400, "max": 800},
            "relationship": {"min": 150, "target": 400, "max": 800},
            "general": {"min": 100, "target": 300, "max": 600}
        }
        guidelines = length_guidelines.get(question_type, length_guidelines["general"])
        answer_len = len(answer)
        
        if guidelines["min"] <= answer_len <= guidelines["max"]:
            if answer_len >= guidelines["target"]:
                scores["length"] = QUALITY_WEIGHTS["length"]
            else:
                scores["length"] = QUALITY_WEIGHTS["length"] * 0.8
        elif answer_len < guidelines["min"]:
            scores["length"] = QUALITY_WEIGHTS["length"] * (answer_len / guidelines["min"])
        else:
            scores["length"] = QUALITY_WEIGHTS["length"] * 0.7
        
        terms_used = sum(1 for term in self.samm_terms if term in answer)
        scores["samm_terms"] = min(1.0, terms_used / 3) * QUALITY_WEIGHTS["samm_terms"]
        
        structure_score = 0
        if "." in answer and len(answer.split(".")) > 1:
            structure_score += 0.4
        if any(term in answer for term in ["Security Cooperation", "Security Assistance"]):
            structure_score += 0.3
        if citations:
            structure_score += 0.3
        scores["structure"] = min(1.0, structure_score) * QUALITY_WEIGHTS["structure"]
        
        total_score = sum(scores.values())
        
        return MetricResult(
            name="quality_score",
            score=total_score,
            passed=total_score >= THRESHOLDS["quality_score"],
            threshold=THRESHOLDS["quality_score"],
            details={
                "component_scores": scores,
                "answer_length": len(answer),
                "citations_found": len(citations),
                "acronyms_found": len(set(acronyms)),
                "samm_terms_used": terms_used
            }
        )
    
    def calculate_confidence_score(self, completeness: MetricResult, 
                                   groundedness: MetricResult,
                                   citation_accuracy: MetricResult,
                                   quality: MetricResult) -> MetricResult:
        """Calculate composite confidence score."""
        weights = {
            "completeness": 0.30,
            "groundedness": 0.30,
            "citation_accuracy": 0.20,
            "quality": 0.20
        }
        
        composite = (
            completeness.score * weights["completeness"] +
            groundedness.score * weights["groundedness"] +
            citation_accuracy.score * weights["citation_accuracy"] +
            quality.score * weights["quality"]
        )
        
        return MetricResult(
            name="confidence_score",
            score=composite,
            passed=composite >= THRESHOLDS["confidence_score"],
            threshold=THRESHOLDS["confidence_score"],
            details={
                "weights": weights,
                "component_contributions": {
                    "completeness": completeness.score * weights["completeness"],
                    "groundedness": groundedness.score * weights["groundedness"],
                    "citation_accuracy": citation_accuracy.score * weights["citation_accuracy"],
                    "quality": quality.score * weights["quality"]
                }
            }
        )

# ============================================================================
# TEST RUNNER WITH BETTER DEBUGGING
# ============================================================================

class SAMMTestRunner:
    """Runs automated tests against the SAMM answering agent"""
    
    def __init__(self, api_url: str = API_BASE_URL, endpoint: str = None, debug: bool = False):
        self.api_url = api_url
        self.endpoint = endpoint or ENDPOINTS[ACTIVE_ENDPOINT]
        self.evaluator = SAMMMetricsEvaluator()
        self.results: List[TestResult] = []
        self.debug = debug
        
    def extract_answer(self, response_data: Dict) -> str:
        """
        Extract answer from API response - tries multiple possible field names.
        """
        # Try different possible answer field names
        answer_fields = [
            "answer",
            "response", 
            "text",
            "content",
            "message",
            "result",
            "output"
        ]
        
        for field in answer_fields:
            if field in response_data and response_data[field]:
                return str(response_data[field])
        
        # Try nested fields
        if "data" in response_data:
            data = response_data["data"]
            if isinstance(data, dict):
                for field in answer_fields:
                    if field in data and data[field]:
                        return str(data[field])
        
        if "aiResponse" in response_data:
            ai_resp = response_data["aiResponse"]
            if isinstance(ai_resp, dict) and "answer" in ai_resp:
                return str(ai_resp["answer"])
        
        return ""
        
    def call_agent(self, question: str) -> Tuple[str, Dict, float]:
        """Call the answering agent API"""
        url = f"{self.api_url}{self.endpoint}"
        payload = {"question": question}
        
        start_time = time.time()
        try:
            response = requests.post(url, json=payload, timeout=120)
            response_time = (time.time() - start_time) * 1000
            
            if self.debug:
                print(f"\n[DEBUG] URL: {url}")
                print(f"[DEBUG] Status: {response.status_code}")
                print(f"[DEBUG] Raw response: {response.text[:500]}...")
            
            if response.status_code == 200:
                data = response.json()
                answer = self.extract_answer(data)
                
                if self.debug:
                    print(f"[DEBUG] Extracted answer ({len(answer)} chars): {answer[:200]}...")
                
                if not answer:
                    print(f"⚠️ WARNING: No answer found in response!")
                    print(f"   Response keys: {list(data.keys())}")
                
                return answer, data, response_time
            else:
                return f"Error: HTTP {response.status_code}", {"error": response.text}, response_time
                
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to API", {"error": "Connection failed"}, 0
        except Exception as e:
            return f"Error: {str(e)}", {"error": str(e)}, 0
    
    def run_single_test(self, test_question: Dict, verbose: bool = True) -> TestResult:
        """Run a single test and evaluate metrics"""
        question_id = test_question["id"]
        question = test_question["question"]
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"Testing: {question_id}")
            print(f"Question: {question}")
            print(f"{'='*60}")
        
        answer, raw_response, response_time = self.call_agent(question)
        
        if verbose:
            print(f"Response time: {response_time:.2f}ms")
            if answer and not answer.startswith("Error"):
                print(f"Answer ({len(answer)} chars): {answer[:200]}...")
            else:
                print(f"⚠️ Answer: {answer}")
        
        # If no answer, return failed result
        if not answer or answer.startswith("Error"):
            print(f"❌ No valid answer received!")
            return TestResult(
                question_id=question_id,
                question=question,
                answer=answer or "No answer",
                response_time_ms=response_time,
                completeness=MetricResult("completeness", 0, False, THRESHOLDS["completeness"]),
                groundedness=MetricResult("groundedness", 0, False, THRESHOLDS["groundedness"]),
                citation_accuracy=MetricResult("citation_accuracy", 0, False, THRESHOLDS["citation_accuracy"]),
                quality_score=MetricResult("quality_score", 0, False, THRESHOLDS["quality_score"]),
                confidence_score=MetricResult("confidence_score", 0, False, THRESHOLDS["confidence_score"]),
                overall_passed=False,
                raw_response=raw_response
            )
        
        # Evaluate all metrics
        completeness = self.evaluator.evaluate_completeness(answer, test_question)
        groundedness = self.evaluator.evaluate_groundedness(answer, test_question)
        citation_accuracy = self.evaluator.evaluate_citation_accuracy(answer, test_question)
        quality = self.evaluator.evaluate_quality_score(answer, test_question)
        confidence = self.evaluator.calculate_confidence_score(
            completeness, groundedness, citation_accuracy, quality
        )
        
        overall_passed = all([
            completeness.passed,
            groundedness.passed,
            citation_accuracy.passed,
            quality.passed,
            confidence.passed
        ])
        
        result = TestResult(
            question_id=question_id,
            question=question,
            answer=answer,
            response_time_ms=response_time,
            completeness=completeness,
            groundedness=groundedness,
            citation_accuracy=citation_accuracy,
            quality_score=quality,
            confidence_score=confidence,
            overall_passed=overall_passed,
            raw_response=raw_response
        )
        
        if verbose:
            self._print_metrics(result)
        
        return result
    
    def _print_metrics(self, result: TestResult):
        """Print metrics for a test result"""
        print(f"\n📊 METRICS RESULTS:")
        print(f"{'Metric':<20} {'Score':<10} {'Threshold':<10} {'Status':<10}")
        print("-" * 50)
        
        for metric in [result.completeness, result.groundedness, 
                       result.citation_accuracy, result.quality_score, 
                       result.confidence_score]:
            if metric:
                status = "✅ PASS" if metric.passed else "❌ FAIL"
                print(f"{metric.name:<20} {metric.score:.2%}     {metric.threshold:.0%}        {status}")
        
        print("-" * 50)
        print(f"OVERALL: {'✅ PASSED' if result.overall_passed else '❌ FAILED'}")
    
    def run_all_tests(self, test_questions: List[Dict] = None, verbose: bool = True) -> List[TestResult]:
        """Run all tests and collect results"""
        if test_questions is None:
            test_questions = CHAPTER_1_TEST_QUESTIONS
        
        print(f"\n{'#'*70}")
        print(f"# SAMM ANSWERING AGENT - AUTOMATED METRICS TEST v2")
        print(f"# Testing {len(test_questions)} questions from Chapter 1")
        print(f"# API Endpoint: {self.api_url}{self.endpoint}")
        print(f"# Started: {datetime.now().isoformat()}")
        print(f"{'#'*70}")
        
        self.results = []
        
        for test_q in test_questions:
            result = self.run_single_test(test_q, verbose)
            self.results.append(result)
            time.sleep(1)
        
        self._print_summary()
        return self.results
    
    def _print_summary(self):
        """Print test summary"""
        if not self.results:
            print("No results to summarize")
            return
        
        print(f"\n{'#'*70}")
        print("# TEST SUMMARY")
        print(f"{'#'*70}")
        
        passed = sum(1 for r in self.results if r.overall_passed)
        total = len(self.results)
        
        print(f"\nOverall: {passed}/{total} tests passed ({passed/total:.1%})")
        
        print(f"\nMetric Averages:")
        metrics = ["completeness", "groundedness", "citation_accuracy", 
                   "quality_score", "confidence_score"]
        
        for metric_name in metrics:
            scores = [getattr(r, metric_name).score for r in self.results 
                     if getattr(r, metric_name) is not None]
            if scores:
                avg = sum(scores) / len(scores)
                threshold = THRESHOLDS.get(metric_name.replace("_score", ""), 0)
                status = "✅" if avg >= threshold else "❌"
                print(f"  {metric_name:<20}: {avg:.2%} (threshold: {threshold:.0%}) {status}")
        
        times = [r.response_time_ms for r in self.results if r.response_time_ms > 0]
        if times:
            print(f"\nResponse Time: avg={sum(times)/len(times):.0f}ms, "
                  f"min={min(times):.0f}ms, max={max(times):.0f}ms")
    
    def export_results_to_excel(self, filepath: str = "samm_metrics_test_results.xlsx"):
        """Export results to Excel file"""
        if not self.results:
            print("No results to export")
            return
        
        data = []
        for r in self.results:
            row = {
                "Question ID": r.question_id,
                "Question": r.question,
                "Answer Preview": r.answer[:300] if r.answer else "",
                "Answer Length": len(r.answer) if r.answer else 0,
                "Response Time (ms)": r.response_time_ms,
                "Completeness": r.completeness.score if r.completeness else 0,
                "Completeness Passed": r.completeness.passed if r.completeness else False,
                "Groundedness": r.groundedness.score if r.groundedness else 0,
                "Groundedness Passed": r.groundedness.passed if r.groundedness else False,
                "Citation Accuracy": r.citation_accuracy.score if r.citation_accuracy else 0,
                "Citation Passed": r.citation_accuracy.passed if r.citation_accuracy else False,
                "Quality Score": r.quality_score.score if r.quality_score else 0,
                "Quality Passed": r.quality_score.passed if r.quality_score else False,
                "Confidence Score": r.confidence_score.score if r.confidence_score else 0,
                "Confidence Passed": r.confidence_score.passed if r.confidence_score else False,
                "Overall Passed": r.overall_passed
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False, sheet_name="Test Results")
        print(f"\nResults exported to: {filepath}")
        return filepath

# ============================================================================
# API DIAGNOSTIC TOOL
# ============================================================================

def diagnose_api(api_url: str = API_BASE_URL):
    """Diagnose API connection and response format"""
    print("\n" + "="*60)
    print("API DIAGNOSTIC")
    print("="*60)
    
    # Test different endpoints
    for name, endpoint in ENDPOINTS.items():
        url = f"{api_url}{endpoint}"
        print(f"\n--- Testing {name}: {url} ---")
        
        try:
            response = requests.post(
                url, 
                json={"question": "What is Security Cooperation?"},
                timeout=30
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response keys: {list(data.keys())}")
                
                # Check for answer
                for key in ["answer", "response", "text", "content"]:
                    if key in data:
                        val = data[key]
                        print(f"✅ Found '{key}': {str(val)[:100]}...")
                        break
                else:
                    print(f"⚠️ No answer field found!")
                    print(f"Full response: {json.dumps(data, indent=2)[:500]}")
            else:
                print(f"Error: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed - Is the server running?")
        except Exception as e:
            print(f"❌ Error: {e}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def run_tests(debug: bool = False):
    """Main test execution function"""
    runner = SAMMTestRunner(debug=debug)
    results = runner.run_all_tests(verbose=True)
    runner.export_results_to_excel("samm_metrics_test_results.xlsx")
    return results

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--diagnose":
            diagnose_api()
        elif sys.argv[1] == "--debug":
            run_tests(debug=True)
        elif sys.argv[1] == "--quick":
            runner = SAMMTestRunner(debug=True)
            runner.run_all_tests(CHAPTER_1_TEST_QUESTIONS[:3])
        else:
            print("Usage:")
            print("  python samm_metrics_tester_v2.py           # Run all tests")
            print("  python samm_metrics_tester_v2.py --diagnose  # Diagnose API")
            print("  python samm_metrics_tester_v2.py --debug     # Run with debug output")
            print("  python samm_metrics_tester_v2.py --quick     # Run first 3 tests only")
    else:
        run_tests()
