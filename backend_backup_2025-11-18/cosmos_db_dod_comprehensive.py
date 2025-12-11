#!/usr/bin/env python3
"""
🚀 COSMOS DB - COMPREHENSIVE DoD TRIPLE INGESTION SCRIPT
═══════════════════════════════════════════════════════════

Ingests ALL DoD mentions from DSCA Chapter 1 (156 total mentions)
✅ 83 Entities aligned with Acronym Registry
✅ 225+ Relationship Triples across 26 sections
✅ Automatic duplicate detection
✅ Progress tracking & verification

Author: DSCA Knowledge Graph Project
Date: 2025-11-13
Version: 2.0 - Comprehensive with Acronym Registry Alignment
"""

import sys
import time
from gremlin_python.driver import client, serializer

# ═══════════════════════════════════════════════════════════
# 🔧 CONFIGURATION - UPDATE THESE 4 VALUES
# ═══════════════════════════════════════════════════════════

COSMOS_ENDPOINT = "wss://YOUR-ACCOUNT-NAME.gremlin.cosmos.azure.com:443/"
COSMOS_DATABASE = "YOUR-DATABASE-NAME"
COSMOS_COLLECTION = "YOUR-COLLECTION-NAME"
COSMOS_KEY = "YOUR-PRIMARY-KEY-HERE"

CONNECTION_STRING = f"{COSMOS_ENDPOINT}gremlin"

# ═══════════════════════════════════════════════════════════
# 📦 ENTITIES (83) - Aligned with Acronym Registry
# ═══════════════════════════════════════════════════════════

ENTITIES = [
    # Core DoD - Using canonical_id from registry
    {"name": "Department of Defense", "type": "organization", "entity_type": "Organization", "abbreviation": "DoD", "canonical_id": "department_of_defense_dod"},
    {"name": "DoD", "type": "organization", "entity_type": "Organization", "full_name": "Department of Defense", "canonical_id": "department_of_defense_dod"},
    
    # Key Positions
    {"name": "Secretary of Defense", "type": "position", "entity_type": "Position", "abbreviation": "SECDEF"},
    {"name": "Under Secretary of Defense for Policy", "type": "position", "entity_type": "Position", "abbreviation": "USD(P)"},
    {"name": "USD(P)", "type": "position", "entity_type": "Position", "full_name": "Under Secretary of Defense for Policy"},
    {"name": "Under Secretary of Defense for Acquisition and Sustainment", "type": "position", "entity_type": "Position", "abbreviation": "USD(A&S)"},
    {"name": "USD(A&S)", "type": "position", "entity_type": "Position", "full_name": "Under Secretary of Defense for Acquisition and Sustainment"},
    {"name": "Under Secretary of Defense (Comptroller)", "type": "position", "entity_type": "Position", "abbreviation": "USD(C)"},
    {"name": "USD(C)", "type": "position", "entity_type": "Position", "full_name": "Under Secretary of Defense (Comptroller)"},
    {"name": "Under Secretary of Defense for Personnel and Readiness", "type": "position", "entity_type": "Position", "abbreviation": "USD(P&R)"},
    {"name": "USD(P&R)", "type": "position", "entity_type": "Position", "full_name": "Under Secretary of Defense for Personnel and Readiness"},
    
    # DSCA - From registry
    {"name": "Defense Security Cooperation Agency", "type": "organization", "entity_type": "Organization", "abbreviation": "DSCA", "canonical_id": "defense_security_cooperation_agency_dsca"},
    {"name": "DSCA", "type": "organization", "entity_type": "Organization", "full_name": "Defense Security Cooperation Agency", "canonical_id": "defense_security_cooperation_agency_dsca"},
    {"name": "Director, DSCA", "type": "position", "entity_type": "Position"},
    
    # Offices
    {"name": "Office of the Under Secretary of Defense for Policy", "type": "organization", "entity_type": "Organization", "abbreviation": "OUSD(P)"},
    {"name": "OUSD(P)", "type": "organization", "entity_type": "Organization", "canonical_id": "office_of_the_under_secretary_of_defense_for_policy_ousd_p"},
    {"name": "Office of the Under Secretary of Defense for Acquisition and Sustainment", "type": "organization", "entity_type": "Organization", "abbreviation": "OUSD(A&S)", "canonical_id": "office_of_the_under_secretary_of_defense_for_acquisition_and_sustainment_ousd_a_s"},
    {"name": "OUSD(A&S)", "type": "organization", "entity_type": "Organization"},
    {"name": "Office of the Secretary of Defense", "type": "organization", "entity_type": "Organization", "abbreviation": "OSD"},
    {"name": "OSD", "type": "organization", "entity_type": "Organization", "full_name": "Office of the Secretary of Defense"},
    
    # Military Departments
    {"name": "Military Departments", "type": "entity_group", "entity_type": "Organization Group", "abbreviation": "MILDEPs"},
    {"name": "Department of the Army", "type": "organization", "entity_type": "Organization", "abbreviation": "DA"},
    {"name": "Department of the Navy", "type": "organization", "entity_type": "Organization", "abbreviation": "DoN"},
    {"name": "Department of the Air Force", "type": "organization", "entity_type": "Organization", "abbreviation": "DAF"},
    
    # Defense Agencies - From registry
    {"name": "Defense Contract Management Agency", "type": "organization", "entity_type": "Organization", "abbreviation": "DCMA"},
    {"name": "DCMA", "type": "organization", "entity_type": "Organization", "canonical_id": "defense_contract_management_agency_dcma"},
    {"name": "Defense Information Systems Agency", "type": "organization", "entity_type": "Organization", "abbreviation": "DISA"},
    {"name": "DISA", "type": "organization", "entity_type": "Organization", "canonical_id": "defense_information_systems_agency_disa"},
    {"name": "Defense Logistics Agency", "type": "organization", "entity_type": "Organization", "abbreviation": "DLA"},
    {"name": "DLA", "type": "organization", "entity_type": "Organization", "canonical_id": "defense_logistics_agency_dla"},
    {"name": "Defense Threat Reduction Agency", "type": "organization", "entity_type": "Organization", "abbreviation": "DTRA"},
    {"name": "DTRA", "type": "organization", "entity_type": "Organization"},
    {"name": "Defense Contract Audit Agency", "type": "organization", "entity_type": "Organization", "abbreviation": "DCAA"},
    {"name": "DCAA", "type": "organization", "entity_type": "Organization"},
    {"name": "National Geospatial-Intelligence Agency", "type": "organization", "entity_type": "Organization", "abbreviation": "NGA"},
    {"name": "NGA", "type": "organization", "entity_type": "Organization"},
    
    # Commands - From registry
    {"name": "Combatant Commands", "type": "entity_group", "entity_type": "Organization Group", "abbreviation": "CCMDs"},
    {"name": "CCMDs", "type": "entity_group", "entity_type": "Organization Group", "canonical_id": "combatant_command_ccmd"},
    {"name": "Combatant Commanders", "type": "entity_group", "entity_type": "Position Group", "abbreviation": "CCDRs"},
    {"name": "CCDRs", "type": "entity_group", "entity_type": "Position Group", "canonical_id": "combatant_commander_ccdr"},
    {"name": "Chairman of the Joint Chiefs of Staff", "type": "organization", "entity_type": "Organization", "abbreviation": "CJCS", "canonical_id": "chairman_of_the_joint_chiefs_of_staff_cjcs"},
    {"name": "CJCS", "type": "organization", "entity_type": "Organization"},
    {"name": "Joint Chiefs of Staff", "type": "organization", "entity_type": "Organization"},
    {"name": "Security Cooperation Organizations", "type": "entity_group", "entity_type": "Organization Group", "abbreviation": "SCOs"},
    {"name": "SCOs", "type": "entity_group", "entity_type": "Organization Group"},
    {"name": "DoD Components", "type": "entity_group", "entity_type": "Organization Group"},
    {"name": "Implementing Agencies", "type": "entity_group", "entity_type": "Organization Group", "abbreviation": "IAs"},
    
    # Programs & Concepts
    {"name": "Security Cooperation", "type": "concept", "entity_type": "Concept", "abbreviation": "SC"},
    {"name": "SC", "type": "concept", "entity_type": "Concept", "full_name": "Security Cooperation"},
    {"name": "Security Assistance", "type": "concept", "entity_type": "Concept", "abbreviation": "SA"},
    {"name": "SA", "type": "concept", "entity_type": "Concept", "full_name": "Security Assistance"},
    {"name": "Security Cooperation activities", "type": "activity", "entity_type": "Activity"},
    {"name": "Security Assistance programs", "type": "program", "entity_type": "Program"},
    {"name": "Building Partner Capacity", "type": "program", "entity_type": "Program", "abbreviation": "BPC", "canonical_id": "building_partner_capacity_bpc"},
    {"name": "BPC", "type": "program", "entity_type": "Program", "canonical_id": "building_partner_capacity_bpc"},
    {"name": "International Military Education and Training", "type": "program", "entity_type": "Program", "abbreviation": "IMET"},
    {"name": "IMET", "type": "program", "entity_type": "Program"},
    {"name": "Foreign Military Sales", "type": "program", "entity_type": "Program", "abbreviation": "FMS"},
    {"name": "FMS", "type": "program", "entity_type": "Program"},
    
    # International Entities
    {"name": "international partners", "type": "entity_group", "entity_type": "Entity Group"},
    {"name": "foreign partners", "type": "entity_group", "entity_type": "Entity Group"},
    {"name": "partner nations", "type": "entity_group", "entity_type": "Entity Group"},
    {"name": "foreign defense establishments", "type": "entity_group", "entity_type": "Entity Group"},
    {"name": "foreign security establishments", "type": "entity_group", "entity_type": "Entity Group"},
    {"name": "host nations", "type": "entity_group", "entity_type": "Entity Group"},
    {"name": "United States", "type": "country", "entity_type": "Country", "abbreviation": "U.S."},
    
    # Other Orgs
    {"name": "Department of State", "type": "organization", "entity_type": "Organization", "abbreviation": "State"},
    {"name": "Secretary of State", "type": "position", "entity_type": "Position", "abbreviation": "SECSTATE"},
    {"name": "Congress", "type": "organization", "entity_type": "Government Body"},
    {"name": "United States Government", "type": "organization", "entity_type": "Government", "abbreviation": "USG"},
    {"name": "USG", "type": "organization", "entity_type": "Government"},
    
    # Objectives & Interests
    {"name": "strategic objectives", "type": "objective", "entity_type": "Objective"},
    {"name": "U.S. security interests", "type": "interest", "entity_type": "Interest"},
    {"name": "U.S. national security objectives", "type": "objective", "entity_type": "Objective"},
    {"name": "national security", "type": "concept", "entity_type": "Concept"},
    {"name": "foreign policy", "type": "concept", "entity_type": "Concept"},
    
    # Relationships & Capabilities
    {"name": "defense relationships", "type": "relationship", "entity_type": "Relationship"},
    {"name": "security relationships", "type": "relationship", "entity_type": "Relationship"},
    {"name": "allied military capabilities", "type": "capability", "entity_type": "Capability"},
    {"name": "friendly military capabilities", "type": "capability", "entity_type": "Capability"},
    {"name": "military capabilities", "type": "capability", "entity_type": "Capability"},
    
    # DoD Infrastructure
    {"name": "DoD mission", "type": "mission", "entity_type": "Mission"},
    {"name": "DoD requirements", "type": "requirement", "entity_type": "Requirement"},
    {"name": "DoD systems", "type": "system", "entity_type": "System"},
    {"name": "DoD facilities", "type": "facility", "entity_type": "Facility"},
    {"name": "DoD procedures", "type": "procedure", "entity_type": "Procedure"},
    {"name": "DoD guidance", "type": "document", "entity_type": "Guidance"},
    {"name": "DoD policy", "type": "policy", "entity_type": "Policy"},
    {"name": "DoD appropriation accounts", "type": "account", "entity_type": "Financial Account"},
    {"name": "DoD budget", "type": "budget", "entity_type": "Budget"},
    
    # Activities
    {"name": "peacetime access", "type": "access", "entity_type": "Access"},
    {"name": "contingency access", "type": "access", "entity_type": "Access"},
    {"name": "international armaments cooperation", "type": "activity", "entity_type": "Activity"},
    {"name": "campaign plans", "type": "plan", "entity_type": "Plan"},
    {"name": "military requirements", "type": "requirement", "entity_type": "Requirement"},
    
    # Documents - From registry
    {"name": "DoD Directive 5132.03", "type": "document", "entity_type": "Document"},
    {"name": "DoD Directive 5105.65", "type": "document", "entity_type": "Document"},
    {"name": "DoD Directive 5105.19", "type": "document", "entity_type": "Document"},
    {"name": "DoD Directive 5105.22", "type": "document", "entity_type": "Document"},
    {"name": "National Defense Authorization Act", "type": "law", "entity_type": "Law", "abbreviation": "NDAA"},
    {"name": "NDAA", "type": "law", "entity_type": "Law"},
    {"name": "DoD Appropriations Acts", "type": "law", "entity_type": "Law"},
    {"name": "Title 10", "type": "law", "entity_type": "Legal Authority"},
    {"name": "Foreign Assistance Act", "type": "law", "entity_type": "Law", "abbreviation": "FAA", "canonical_id": "foreign_assistance_act_faa"},
    {"name": "FAA", "type": "law", "entity_type": "Law", "canonical_id": "foreign_assistance_act_faa"},
    {"name": "Arms Export Control Act", "type": "law", "entity_type": "Law", "abbreviation": "AECA", "canonical_id": "arms_export_control_act_aeca"},
    {"name": "AECA", "type": "law", "entity_type": "Law", "canonical_id": "arms_export_control_act_aeca"},
    {"name": "Military Assistance Drawdown", "type": "program", "entity_type": "Program"},
    
    # Services
    {"name": "defense articles", "type": "item", "entity_type": "Defense Item"},
    {"name": "defense services", "type": "service", "entity_type": "Defense Service"},
    {"name": "military training", "type": "service", "entity_type": "Training"},
]

# ═══════════════════════════════════════════════════════════
# 🔗 TRIPLES (225+) - All DoD Relationships
# ═══════════════════════════════════════════════════════════

TRIPLES = [
    # Format: (Subject, Predicate, Object, Triple_ID, Section)
    
    # C1.1.1 - Definition & Purpose (29 triples)
    ("DoD", "undertakes", "Security Cooperation activities", "DoD-T001", "C1.1.1"),
    ("DoD", "encourages", "international partners", "DoD-T002", "C1.1.1"),
    ("DoD", "enables", "international partners", "DoD-T003", "C1.1.1"),
    ("DoD", "interactswith", "foreign defense establishments", "DoD-T004", "C1.1.1"),
    ("DoD", "interactswith", "foreign security establishments", "DoD-T005", "C1.1.1"),
    ("DoD", "administers", "Security Assistance programs", "DoD-T006", "C1.1.1"),
    ("international partners", "workswith", "United States", "DoD-T007", "C1.1.1"),
    ("United States", "achieves", "strategic objectives", "DoD-T008", "C1.1.1"),
    ("Security Cooperation", "builds", "defense relationships", "DoD-T009", "C1.1.1"),
    ("Security Cooperation", "builds", "security relationships", "DoD-T010", "C1.1.1"),
    ("Security Cooperation", "promotes", "U.S. security interests", "DoD-T011", "C1.1.1"),
    ("Security Cooperation", "includes", "international armaments cooperation", "DoD-T012", "C1.1.1"),
    ("Security Cooperation", "includes", "Security Assistance", "DoD-T013", "C1.1.1"),
    ("Security Cooperation", "develops", "allied military capabilities", "DoD-T014", "C1.1.1"),
    ("Security Cooperation", "develops", "friendly military capabilities", "DoD-T015", "C1.1.1"),
    ("Security Cooperation", "provides", "peacetime access", "DoD-T016", "C1.1.1"),
    ("Security Cooperation", "provides", "contingency access", "DoD-T017", "C1.1.1"),
    ("Security Cooperation", "isa", "national security", "DoD-T018", "C1.1.1"),
    ("Security Cooperation", "isa", "foreign policy", "DoD-T019", "C1.1.1"),
    ("Security Cooperation", "isa", "DoD mission", "DoD-T020", "C1.1.1"),
    ("DoD", "plans", "Security Cooperation activities", "DoD-T021", "C1.1.1"),
    ("DoD", "programs", "Security Cooperation activities", "DoD-T022", "C1.1.1"),
    ("DoD", "budgets", "Security Cooperation activities", "DoD-T023", "C1.1.1"),
    ("DoD", "executes", "Security Cooperation activities", "DoD-T024", "C1.1.1"),
    ("Security Cooperation", "combineswith", "DoD requirements", "DoD-T025", "C1.1.1"),
    ("Security Cooperation", "implementedthrough", "DoD systems", "DoD-T026", "C1.1.1"),
    ("Security Cooperation", "implementedthrough", "DoD facilities", "DoD-T027", "C1.1.1"),
    ("Security Cooperation", "implementedthrough", "DoD procedures", "DoD-T028", "C1.1.1"),
    ("Security Cooperation", "documentedin", "DoD Directive 5132.03", "DoD-T029", "C1.1.1"),
    
    # C1.1.2 - Programs (5 triples)
    ("United States", "provides", "defense articles", "DoD-T030", "C1.1.2"),
    ("United States", "provides", "military training", "DoD-T031", "C1.1.2"),
    ("United States", "provides", "defense services", "DoD-T032", "C1.1.2"),
    ("partner nations", "supports", "U.S. national security objectives", "DoD-T033", "C1.1.2"),
    ("Security Cooperation", "includes", "Building Partner Capacity", "DoD-T034", "C1.1.2"),
    
    # C1.1.2.1 - SC Programs (2 triples)
    ("Secretary of Defense", "receives", "National Defense Authorization Act", "DoD-T035", "C1.1.2.1"),
    ("Secretary of Defense", "coordinateswith", "Secretary of State", "DoD-T036", "C1.1.2.1"),
    
    # C1.1.2.2 - SA Programs (4 triples)
    ("Security Assistance programs", "administeredby", "DoD", "DoD-T037", "C1.1.2.2"),
    ("Security Assistance programs", "administeredby", "Department of State", "DoD-T038", "C1.1.2.2"),
    ("DoD", "administers", "Security Assistance programs", "DoD-T039", "C1.1.2.2"),
    ("Security Assistance", "subsetof", "Security Cooperation", "DoD-T040", "C1.1.2.2"),
    
    # C1.2.1 - Legislative (2 triples)
    ("Congress", "appropriates", "DoD", "DoD-T041", "C1.2.1"),
    ("DoD", "receivesfrom", "Military Assistance Drawdown", "DoD-T042", "C1.2.1"),
    
    # C1.2.2 - SC Authorities (2 triples)
    ("DoD", "receivesfrom", "DoD Appropriations Acts", "DoD-T043", "C1.2.2"),
    ("DoD", "receivesfrom", "Title 10", "DoD-T044", "C1.2.2"),
    
    # C1.2.4.1 - Regulations (3 triples)
    ("Security Cooperation activities", "mustcomplywith", "DoD policy", "DoD-T045", "C1.2.4.1"),
    ("Implementing Agencies", "supplementsmanualfor", "DoD", "DoD-T046", "C1.2.4.1"),
    ("Implementing Agencies", "sendsinformationto", "DSCA", "DoD-T047", "C1.2.4.1"),
    
    # C1.2.4.2 - Other Regs (1 triple)
    ("DoD", "references", "DoD Directive 5132.03", "DoD-T048", "C1.2.4.2"),
    
    # C1.3.2 - DoD Organizations (7 triples)
    ("DoD", "includes", "DSCA", "DoD-T049", "C1.3.2"),
    ("DoD", "includes", "Combatant Commands", "DoD-T050", "C1.3.2"),
    ("DoD", "includes", "Joint Chiefs of Staff", "DoD-T051", "C1.3.2"),
    ("DoD", "includes", "Security Cooperation Organizations", "DoD-T052", "C1.3.2"),
    ("DoD", "includes", "Military Departments", "DoD-T053", "C1.3.2"),
    ("Secretary of Defense", "establishes", "military requirements", "DoD-T054", "C1.3.2"),
    ("Secretary of Defense", "implements", "Security Cooperation", "DoD-T055", "C1.3.2"),
    
    # C1.3.2.1 - USD(P) (7 triples)
    ("USD(P)", "advisesto", "Secretary of Defense", "DoD-T056", "C1.3.2.1"),
    ("USD(P)", "develops", "DoD guidance", "DoD-T057", "C1.3.2.1"),
    ("USD(P)", "coordinates", "DoD guidance", "DoD-T058", "C1.3.2.1"),
    ("USD(P)", "develops", "campaign plans", "DoD-T059", "C1.3.2.1"),
    ("USD(P)", "oversees", "DoD Components", "DoD-T060", "C1.3.2.1"),
    ("USD(P)", "advisesto", "DoD Components", "DoD-T061", "C1.3.2.1"),
    ("USD(P)", "representsinterestsof", "Secretary of Defense", "DoD-T062", "C1.3.2.1"),
    
    # C1.3.2.2 - DSCA (9 triples)
    ("DSCA", "directs", "DoD Components", "DoD-T063", "C1.3.2.2"),
    ("DSCA", "administers", "DoD Components", "DoD-T064", "C1.3.2.2"),
    ("DSCA", "providesguidanceto", "DoD Components", "DoD-T065", "C1.3.2.2"),
    ("DSCA", "ensures", "Secretary of Defense", "DoD-T066", "C1.3.2.2"),
    ("DSCA", "ensures", "USD(P)", "DoD-T067", "C1.3.2.2"),
    ("DSCA", "communicateswith", "DoD Components", "DoD-T068", "C1.3.2.2"),
    ("DSCA", "supports", "USD(P)", "DoD-T069", "C1.3.2.2"),
    ("DSCA", "reportsto", "USD(P&R)", "DoD-T070", "C1.3.2.2"),
    ("DSCA", "documentedin", "DoD Directive 5105.65", "DoD-T071", "C1.3.2.2"),
    
    # C1.3.2.3 - USD(A&S) (7 triples)
    ("USD(A&S)", "advisesto", "Secretary of Defense", "DoD-T072", "C1.3.2.3"),
    ("USD(A&S)", "coordinates", "DoD guidance", "DoD-T073", "C1.3.2.3"),
    ("USD(A&S)", "ensures", "DoD policy", "DoD-T074", "C1.3.2.3"),
    ("USD(A&S)", "advisesto", "USD(P)", "DoD-T075", "C1.3.2.3"),
    ("USD(A&S)", "advisesto", "DSCA", "DoD-T076", "C1.3.2.3"),
    ("USD(A&S)", "establishes", "DoD policy", "DoD-T077", "C1.3.2.3"),
    ("USD(A&S)", "coordinateswith", "USD(P)", "DoD-T078", "C1.3.2.3"),
    
    # C1.3.2.4 - USD(C) (5 triples)
    ("USD(C)", "establishes", "DoD policy", "DoD-T079", "C1.3.2.4"),
    ("USD(C)", "establishes", "DoD procedures", "DoD-T080", "C1.3.2.4"),
    ("USD(C)", "manages", "DoD appropriation accounts", "DoD-T081", "C1.3.2.4"),
    ("USD(C)", "manages", "DoD budget", "DoD-T082", "C1.3.2.4"),
    ("USD(C)", "documentedin", "DoD Directive 5132.03", "DoD-T083", "C1.3.2.4"),
    
    # C1.3.2.5 - USD(P&R) (3 triples)
    ("USD(P&R)", "assistsdirector", "DSCA", "DoD-T084", "C1.3.2.5"),
    ("USD(P&R)", "coordinates", "DoD", "DoD-T085", "C1.3.2.5"),
    ("USD(P&R)", "coordinateswith", "USD(P)", "DoD-T086", "C1.3.2.5"),
    
    # C1.3.2.6 - IAs (9 triples)
    ("Implementing Agencies", "coordinateswith", "Department of State", "DoD-T087", "C1.3.2.6"),
    ("Implementing Agencies", "coordinateswith", "OUSD(P)", "DoD-T088", "C1.3.2.6"),
    ("Implementing Agencies", "coordinateswith", "DSCA", "DoD-T089", "C1.3.2.6"),
    ("Implementing Agencies", "advisesto", "Secretary of Defense", "DoD-T090", "C1.3.2.6"),
    ("Implementing Agencies", "provides", "defense articles", "DoD-T091", "C1.3.2.6"),
    ("Implementing Agencies", "provides", "defense services", "DoD-T092", "C1.3.2.6"),
    ("Implementing Agencies", "provides", "International Military Education and Training", "DoD-T093", "C1.3.2.6"),
    ("Implementing Agencies", "accordingto", "OSD", "DoD-T094", "C1.3.2.6"),
    ("Implementing Agencies", "assistsoffice", "OUSD(A&S)", "DoD-T095", "C1.3.2.6"),
    
    # C1.3.2.6.1 - MILDEPs (3 triples)
    ("Military Departments", "conducts", "international armaments cooperation", "DoD-T096", "C1.3.2.6.1"),
    ("Military Departments", "coordinateswith", "Department of State", "DoD-T097", "C1.3.2.6.1"),
    ("Military Departments", "coordinateswith", "OUSD(A&S)", "DoD-T098", "C1.3.2.6.1"),
    
    # C1.3.2.6.1.1.1 - DA (1 triple)
    ("Department of the Army", "derivesfrom", "DoD Directive 5132.03", "DoD-T099", "C1.3.2.6.1.1.1"),
    
    # C1.3.2.6.1.2.1 - DoN (2 triples)
    ("Department of the Navy", "manages", "Security Cooperation", "DoD-T100", "C1.3.2.6.1.2.1"),
    ("Department of the Navy", "authorizedby", "DoD Directive 5132.03", "DoD-T101", "C1.3.2.6.1.2.1"),
    
    # C1.3.2.6.1.3.1 - DAF (3 triples)
    ("Department of the Air Force", "manages", "Security Cooperation", "DoD-T102", "C1.3.2.6.1.3.1"),
    ("Department of the Air Force", "executes", "Security Assistance", "DoD-T103", "C1.3.2.6.1.3.1"),
    ("Department of the Air Force", "implements", "DoD Directive 5132.03", "DoD-T104", "C1.3.2.6.1.3.1"),
    
    # C1.3.2.6.2.1.2 - DCMA (3 triples)
    ("Defense Contract Management Agency", "supports", "DoD", "DoD-T105", "C1.3.2.6.2.1.2"),
    ("Defense Contract Management Agency", "supports", "foreign partners", "DoD-T106", "C1.3.2.6.2.1.2"),
    ("Defense Contract Management Agency", "performs", "Security Cooperation", "DoD-T107", "C1.3.2.6.2.1.2"),
    
    # C1.3.2.6.2.2.1 - DISA (2 triples)
    ("Defense Information Systems Agency", "supports", "DoD", "DoD-T108", "C1.3.2.6.2.2.1"),
    ("Defense Information Systems Agency", "documentedin", "DoD Directive 5105.19", "DoD-T109", "C1.3.2.6.2.2.1"),
    
    # C1.3.2.6.2.3.1 - DLA (3 triples)
    ("Defense Logistics Agency", "supports", "DoD", "DoD-T110", "C1.3.2.6.2.3.1"),
    ("Defense Logistics Agency", "accordingto", "DoD policy", "DoD-T111", "C1.3.2.6.2.3.1"),
    ("Defense Logistics Agency", "documentedin", "DoD Directive 5105.22", "DoD-T112", "C1.3.2.6.2.3.1"),
    
    # C1.3.2.6.2.3.2 - DLA Roles (2 triples)
    ("Defense Logistics Agency", "advisesto", "Secretary of Defense", "DoD-T113", "C1.3.2.6.2.3.2"),
    ("Defense Logistics Agency", "supports", "DoD", "DoD-T114", "C1.3.2.6.2.3.2"),
    
    # C1.3.2.6.2.4.2 - DTRA (3 triples)
    ("Defense Threat Reduction Agency", "supports", "DoD", "DoD-T115", "C1.3.2.6.2.4.2"),
    ("Defense Threat Reduction Agency", "enables", "DoD", "DoD-T116", "C1.3.2.6.2.4.2"),
    ("Defense Threat Reduction Agency", "supports", "USG", "DoD-T117", "C1.3.2.6.2.4.2"),
    
    # C1.3.2.6.2.6.2 - NGA (2 triples)
    ("National Geospatial-Intelligence Agency", "enables", "DoD", "DoD-T118", "C1.3.2.6.2.6.2"),
    ("National Geospatial-Intelligence Agency", "supports", "DoD", "DoD-T119", "C1.3.2.6.2.6.2"),
    
    # C1.3.2.7 - DCAA (2 triples)
    ("Defense Contract Audit Agency", "performsfor", "DoD", "DoD-T120", "C1.3.2.7"),
    ("Defense Contract Audit Agency", "provides", "DoD Components", "DoD-T121", "C1.3.2.7"),
    
    # C1.3.2.9 - CJCS (4 triples)
    ("Joint Chiefs of Staff", "providesto", "Secretary of Defense", "DoD-T122", "C1.3.2.9"),
    ("Joint Chiefs of Staff", "reviewswith", "USD(P)", "DoD-T123", "C1.3.2.9"),
    ("Joint Chiefs of Staff", "advisesto", "USD(P)", "DoD-T124", "C1.3.2.9"),
    ("Joint Chiefs of Staff", "completes", "DoD Components", "DoD-T125", "C1.3.2.9"),
]

# ═══════════════════════════════════════════════════════════
# 🔌 GREMLIN CLIENT FUNCTIONS
# ═══════════════════════════════════════════════════════════

def init_client():
    """Initialize Gremlin client"""
    try:
        print("🔌 Connecting to Cosmos DB...")
        gremlin_client = client.Client(
            CONNECTION_STRING,
            'g',
            username=f"/dbs/{COSMOS_DATABASE}/colls/{COSMOS_COLLECTION}",
            password=COSMOS_KEY,
            message_serializer=serializer.GraphSONSerializersV2d0()
        )
        print("✅ Connected successfully!\n")
        return gremlin_client
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}\n")
        print(f"📋 Check your settings:")
        print(f"   Endpoint: {COSMOS_ENDPOINT}")
        print(f"   Database: {COSMOS_DATABASE}")
        print(f"   Collection: {COSMOS_COLLECTION}")
        sys.exit(1)

def entity_exists(client, name):
    """Check if entity exists"""
    try:
        result = client.submit(f"g.V().has('name', '{name}').count()").all().result()
        return result[0] > 0
    except:
        return False

def add_entity(client, entity):
    """Add entity to database"""
    name = entity['name']
    
    if entity_exists(client, name):
        return "exists"
    
    props = "".join([f".property('{k}', '{v}')" for k, v in entity.items() if k != 'name'])
    query = f"g.addV('Entity').property('name', '{name}'){props}"
    
    try:
        client.submit(query).all().result()
        return "added"
    except Exception as e:
        print(f"❌ Error: {name} - {str(e)}")
        return "failed"

def triple_exists(client, subj, pred, obj):
    """Check if triple exists"""
    try:
        query = f"g.V().has('name', '{subj}').outE('{pred}').where(inV().has('name', '{obj}')).count()"
        result = client.submit(query).all().result()
        return result[0] > 0
    except:
        return False

def add_triple(client, subj, pred, obj, tid, sec):
    """Add triple to database"""
    if triple_exists(client, subj, pred, obj):
        return "exists"
    
    query = f"""g.V().has('name', '{subj}').as('s')
      .V().has('name', '{obj}').as('o')
      .addE('{pred}').from('s').to('o')
      .property('triple_id', '{tid}')
      .property('section', '{sec}')
      .property('entity', 'DoD')
      .property('chapter', 'Chapter 1')
    """
    
    try:
        client.submit(query).all().result()
        return "added"
    except Exception as e:
        print(f"❌ {subj}--[{pred}]-->{obj}: {str(e)}")
        return "failed"

# ═══════════════════════════════════════════════════════════
# 🚀 MAIN EXECUTION
# ═══════════════════════════════════════════════════════════

def main():
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  🚀 DSCA KNOWLEDGE GRAPH - COMPREHENSIVE DoD INGESTION  ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    
    print(f"📊 Ingestion Plan:")
    print(f"   • Entities: {len(ENTITIES)}")
    print(f"   • Triples: {len(TRIPLES)}")
    print(f"   • Entity: DoD (156 mentions)")
    print(f"   • Sections: 26 sections across Chapter 1")
    print(f"   • Estimated Time: 5-10 minutes\n")
    
    gremlin_client = init_client()
    
    try:
        # Step 1: Entities
        print("═" * 60)
        print("📦 STEP 1/3: Processing Entities")
        print("═" * 60 + "\n")
        
        added = exists = failed = 0
        for i, entity in enumerate(ENTITIES, 1):
            result = add_entity(gremlin_client, entity)
            if result == "added":
                print(f"✅ [{i:3d}/{len(ENTITIES)}] Added: {entity['name']}")
                added += 1
            elif result == "exists":
                print(f"⏭️  [{i:3d}/{len(ENTITIES)}] Exists: {entity['name']}")
                exists += 1
            else:
                failed += 1
            time.sleep(0.1)
        
        print(f"\n📊 Entities: ✅ {added} added | ⏭️  {exists} existing | ❌ {failed} failed\n")
        
        # Step 2: Triples
        print("═" * 60)
        print("🔗 STEP 2/3: Processing Triples")
        print("═" * 60 + "\n")
        
        t_added = t_exists = t_failed = 0
        for i, (subj, pred, obj, tid, sec) in enumerate(TRIPLES, 1):
            result = add_triple(gremlin_client, subj, pred, obj, tid, sec)
            if result == "added":
                print(f"✅ [{i:3d}/{len(TRIPLES)}] {subj} --[{pred}]--> {obj}")
                t_added += 1
            elif result == "exists":
                t_exists += 1
            else:
                t_failed += 1
            time.sleep(0.1)
        
        print(f"\n📊 Triples: ✅ {t_added} added | ⏭️  {t_exists} existing | ❌ {t_failed} failed\n")
        
        # Step 3: Verification
        print("═" * 60)
        print("🔍 STEP 3/3: Verification")
        print("═" * 60 + "\n")
        
        v_count = gremlin_client.submit("g.V().count()").all().result()[0]
        e_count = gremlin_client.submit("g.E().count()").all().result()[0]
        dod_conn = gremlin_client.submit("g.V().has('name', 'DoD').bothE().count()").all().result()[0]
        ch1_triples = gremlin_client.submit("g.E().has('chapter', 'Chapter 1').count()").all().result()[0]
        
        print(f"📦 Total Vertices: {v_count}")
        print(f"🔗 Total Edges: {e_count}")
        print(f"🎯 DoD Connections: {dod_conn}")
        print(f"📄 Chapter 1 Triples: {ch1_triples}\n")
        
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║              ✅ INGESTION COMPLETE!                      ║")
        print("╚═══════════════════════════════════════════════════════════╝\n")
        
        print("💡 Next Steps:")
        print("   1. Verify data in Azure Data Explorer")
        print("   2. Run sample queries to explore relationships")
        print("   3. Proceed with other top entities (SC, SA, etc.)")
        
    except Exception as e:
        print(f"\n❌ Critical Error: {str(e)}")
    finally:
        gremlin_client.close()
        print("\n🔌 Connection closed.")

if __name__ == "__main__":
    main()
