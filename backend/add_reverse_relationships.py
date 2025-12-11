"""
Add Reverse Relationships to KG
================================
For every A --[rel]--> B, add B --[rel_reverse]--> A
"""

import json
from datetime import datetime

# Reverse relationship mappings
REVERSE_MAP = {
    # Active → Passive
    'submitted_to': 'receives_from',
    'reports_to': 'receives_reports_from',
    'managed_by': 'manages',
    'managedby': 'manages',
    'supervised_by': 'supervises',
    'authorized_by': 'authorizes',
    'authorizedby': 'authorizes',
    'administered_by': 'administers',
    'funded_by': 'funds',
    'fundedby': 'funds',
    'provided_by': 'provides',
    'providedby': 'provides',
    'executed_by': 'executes',
    'implemented_by': 'implements',
    'directed_by': 'directs',
    'overseen_by': 'oversees',
    'controlled_by': 'controls',
    'owned_by': 'owns',
    'issued_by': 'issues',
    'prepared_by': 'prepares',
    'reviewed_by': 'reviews',
    'approved_by': 'approves',
    'coordinated_by': 'coordinates',
    'supported_by': 'supports',
    'handled_by': 'handles',
    'processed_by': 'processes',
    'tracked_by': 'tracks',
    'governed_by': 'governs',
    'governedby': 'governs',
    
    # Passive → Active
    'manages': 'managed_by',
    'supervises': 'supervised_by',
    'authorizes': 'authorized_by',
    'administers': 'administered_by',
    'funds': 'funded_by',
    'provides': 'provided_by',
    'executes': 'executed_by',
    'implements': 'implemented_by',
    'directs': 'directed_by',
    'oversees': 'overseen_by',
    'controls': 'controlled_by',
    'owns': 'owned_by',
    'issues': 'issued_by',
    'prepares': 'prepared_by',
    'reviews': 'reviewed_by',
    'approves': 'approved_by',
    'coordinates': 'coordinated_by',
    'coordinates_with': 'coordinated_with',
    'coordinateswith': 'coordinated_with',
    'supports': 'supported_by',
    'handles': 'handled_by',
    'processes': 'processed_by',
    'tracks': 'tracked_by',
    'governs': 'governed_by',
    'receives': 'submitted_to',
    'receives_from': 'submitted_to',
    
    # Bidirectional (same both ways)
    'part_of': 'contains',
    'contains': 'part_of',
    'subset_of': 'includes',
    'includes': 'subset_of',
    'same_as': 'same_as',
    'related_to': 'related_to',
    'relatedto': 'relatedto',
    'works_with': 'works_with',
    'workswith': 'workswith',
    'coordinates_with': 'coordinates_with',
    
    # Special cases
    'is_ia_for': 'has_ia',
    'is_IA_for': 'has_ia',
    'responsible_for': 'responsibility_of',
    'responsiblefor': 'responsibility_of',
    'provides_logistics_for': 'receives_logistics_from',
    'provides_services_for': 'receives_services_from',
    'performs_auditing': 'audited_by',
    'performs_accounting': 'accounting_by',
    'performs_billing': 'billed_by',
    'performs_disbursing': 'disbursed_by',
    'performs_collecting': 'collected_by',
    'develops_campaign_plans_for': 'campaign_plans_developed_by',
    'provides_military_advice': 'receives_military_advice_from',
    'provides_general_direction': 'receives_general_direction_from',
    'provides_guidance_to': 'receives_guidance_from',
    'providesguidanceto': 'receives_guidance_from',
}

def get_reverse_type(rel_type: str) -> str:
    """Get reverse relationship type."""
    rel_lower = rel_type.lower()
    
    # Check direct mapping
    if rel_lower in REVERSE_MAP:
        return REVERSE_MAP[rel_lower]
    
    # Auto-generate reverse for _by suffix
    if rel_lower.endswith('_by'):
        return rel_lower[:-3] + 's'  # managed_by → manages
    if rel_lower.endswith('by'):
        return rel_lower[:-2] + 's'  # managedby → manages
    
    # Auto-generate reverse for active verbs (add _by)
    if rel_lower.endswith('s') and not rel_lower.endswith('_to'):
        return rel_lower[:-1] + '_by'  # manages → manage_by
    
    # Default: add _reverse suffix
    return rel_lower + '_reverse'


def add_reverse_relationships(kg_path: str, output_path: str = None):
    """Add reverse relationships to KG."""
    
    # Load KG
    with open(kg_path, 'r', encoding='utf-8') as f:
        kg = json.load(f)
    
    relationships = kg.get('relationships', [])
    
    print(f"📥 Loaded KG: {len(relationships)} relationships")
    
    # Track existing relationships to avoid duplicates
    existing_keys = set()
    for rel in relationships:
        key = (rel['source'].upper(), rel['target'].upper(), rel['type'].lower())
        existing_keys.add(key)
    
    # Get max relationship ID
    max_id = 0
    for rel in relationships:
        rel_id = rel.get('id', 'rel_0')
        if rel_id.startswith('rel_'):
            try:
                num = int(rel_id.split('_')[1])
                max_id = max(max_id, num)
            except:
                pass
    
    # Add reverse relationships
    added = 0
    skipped = 0
    
    new_relationships = []
    
    for rel in relationships:
        source = rel['source']
        target = rel['target']
        rel_type = rel['type']
        
        # Get reverse type
        reverse_type = get_reverse_type(rel_type)
        
        # Check if reverse already exists
        reverse_key = (target.upper(), source.upper(), reverse_type.lower())
        
        if reverse_key in existing_keys:
            skipped += 1
            continue
        
        # Create reverse relationship
        max_id += 1
        reverse_rel = {
            'id': f'rel_{max_id:04d}',
            'source': target,
            'target': source,
            'type': reverse_type,
            'description': f'{target} {reverse_type} {source}',
            'section': rel.get('section', ''),
            'weight': rel.get('weight', 7),
            'source_db': 'reverse_generated',
            'original_rel': rel.get('id', '')
        }
        
        new_relationships.append(reverse_rel)
        existing_keys.add(reverse_key)
        added += 1
    
    # Add to KG
    kg['relationships'].extend(new_relationships)
    
    # Update metadata
    kg['metadata'] = kg.get('metadata', {})
    kg['metadata']['reverse_relationships_added'] = datetime.now().isoformat()
    kg['metadata']['reverse_count'] = added
    
    # Save
    out_path = output_path or kg_path
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(kg, f, indent=2, ensure_ascii=False)
    
    # Print results
    print(f"\n{'='*60}")
    print(f"📊 REVERSE RELATIONSHIPS ADDED")
    print(f"{'='*60}")
    print(f"   Original relationships: {len(relationships)}")
    print(f"   Reverse added:          {added}")
    print(f"   Skipped (duplicates):   {skipped}")
    print(f"   Total now:              {len(kg['relationships'])}")
    print(f"\n   Saved to: {out_path}")
    
    return {
        'original': len(relationships),
        'added': added,
        'skipped': skipped,
        'total': len(kg['relationships'])
    }


if __name__ == '__main__':
    import sys
    
    kg_path = sys.argv[1] if len(sys.argv) > 1 else 'samm_knowledge_graph.json'
    
    result = add_reverse_relationships(kg_path)
    
    print(f"\n✅ Done! Run your tests again.")

