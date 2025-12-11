# quick_integration.py
# Quick patch to add HITL to your existing app_3.2.1.py
# Run this to automatically integrate HITL system

import os
import re

def integrate_hitl_system():
    """
    Automatically integrate HITL system into existing app_3.2.1.py
    """
    
    app_file = "app_3.2.1.py"
    
    if not os.path.exists(app_file):
        print("❌ app_3.2.1.py not found!")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔧 Integrating HITL system...")
    
    # 1. Add imports after line 55 (after Azure imports)
    import_section = """
# HITL Review System Imports
REVIEWS_CONTAINER_NAME = os.getenv("REVIEWS_CONTAINER_NAME", "hitl_reviews")
FEEDBACK_CONTAINER_NAME = os.getenv("FEEDBACK_CONTAINER_NAME", "sme_feedback")

reviews_container_client = None
feedback_container_client = None

class ReviewStatus:
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
"""
    
    # Find where to insert (after Azure imports)
    insert_pos = content.find("from azure.core.exceptions import")
    if insert_pos != -1:
        next_newline = content.find("\n\n", insert_pos)
        content = content[:next_newline] + "\n\n" + import_section + content[next_newline:]
        print("✅ Added HITL imports")
    
    # 2. Add initialization function
    init_function = """
def initialize_hitl_containers():
    \"\"\"Initialize Cosmos DB containers for HITL reviews\"\"\"
    global reviews_container_client, feedback_container_client
    
    if not cosmos_client:
        print("⚠️  HITL: Cosmos DB not available - using in-memory storage")
        return
    
    try:
        database_client = cosmos_client.get_database_client(DATABASE_NAME)
        
        # Reviews Container
        try:
            reviews_container_client = database_client.create_container(
                id=REVIEWS_CONTAINER_NAME,
                partition_key=PartitionKey(path="/userId"),
                offer_throughput=400
            )
            print(f"✅ HITL: Created reviews container")
        except CosmosExceptions.CosmosResourceExistsError:
            reviews_container_client = database_client.get_container_client(REVIEWS_CONTAINER_NAME)
            print(f"✅ HITL: Connected to reviews container")
        
        # Feedback Container
        try:
            feedback_container_client = database_client.create_container(
                id=FEEDBACK_CONTAINER_NAME,
                partition_key=PartitionKey(path="/reviewId"),
                offer_throughput=400
            )
            print(f"✅ HITL: Created feedback container")
        except CosmosExceptions.CosmosResourceExistsError:
            feedback_container_client = database_client.get_container_client(FEEDBACK_CONTAINER_NAME)
            print(f"✅ HITL: Connected to feedback container")
            
    except Exception as e:
        print(f"❌ HITL Error: {e}")

def create_review_item(user_id, case_id, question, answer, agent_metadata, priority="medium"):
    \"\"\"Add item to review queue\"\"\"
    review_id = str(uuid.uuid4())
    
    review_item = {
        'id': review_id,
        'userId': user_id,
        'caseId': case_id,
        'question': question,
        'originalAnswer': answer,
        'agentMetadata': agent_metadata,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'status': ReviewStatus.PENDING,
        'assignedTo': None,
        'priority': priority,
        'type': 'review_item'
    }
    
    if reviews_container_client:
        try:
            reviews_container_client.create_item(body=review_item)
            print(f"📝 HITL: Review queued (Priority: {priority})")
        except Exception as e:
            print(f"❌ HITL: Error queuing review: {e}")
    
    return review_item

def get_hitl_reviews(limit=50):
    \"\"\"Get pending reviews\"\"\"
    if not reviews_container_client:
        return []
    
    try:
        query = "SELECT * FROM c WHERE c.type = 'review_item' AND c.status IN (@pending, @in_review) ORDER BY c.timestamp DESC"
        items = list(reviews_container_client.query_items(
            query=query,
            parameters=[
                {"name": "@pending", "value": ReviewStatus.PENDING},
                {"name": "@in_review", "value": ReviewStatus.IN_REVIEW}
            ],
            enable_cross_partition_query=True,
            max_item_count=limit
        ))
        return items
    except Exception as e:
        print(f"❌ HITL: Error fetching reviews: {e}")
        return []

def submit_hitl_feedback(review_id, sme_id, sme_name, feedback_type, corrected_answer=None, comments=""):
    \"\"\"Submit SME feedback\"\"\"
    feedback_id = str(uuid.uuid4())
    
    feedback_item = {
        'id': feedback_id,
        'reviewId': review_id,
        'smeId': sme_id,
        'smeName': sme_name,
        'feedbackType': feedback_type,
        'correctedAnswer': corrected_answer,
        'comments': comments,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'type': 'feedback_item'
    }
    
    if feedback_container_client:
        try:
            feedback_container_client.create_item(body=feedback_item)
            
            # Update review status
            if reviews_container_client:
                items = list(reviews_container_client.query_items(
                    query="SELECT * FROM c WHERE c.id = @id",
                    parameters=[{"name": "@id", "value": review_id}],
                    enable_cross_partition_query=True
                ))
                
                if items:
                    item = items[0]
                    if feedback_type == 'approve':
                        item['status'] = ReviewStatus.APPROVED
                    elif feedback_type == 'reject':
                        item['status'] = ReviewStatus.REJECTED
                    elif feedback_type == 'revise':
                        item['status'] = ReviewStatus.NEEDS_REVISION
                    
                    reviews_container_client.replace_item(item=item['id'], body=item)
            
            # Apply to agents if corrected
            if corrected_answer and feedback_type in ['revise', 'reject']:
                # Get original review
                if reviews_container_client:
                    items = list(reviews_container_client.query_items(
                        query="SELECT * FROM c WHERE c.id = @id",
                        parameters=[{"name": "@id", "value": review_id}],
                        enable_cross_partition_query=True
                    ))
                    if items:
                        review = items[0]
                        # Store correction in answer agent
                        orchestrator.answer_agent.answer_corrections[review['question']] = {
                            'corrected_answer': corrected_answer,
                            'source': 'sme_feedback',
                            'timestamp': feedback_item['timestamp']
                        }
                        print(f"✅ HITL: Applied correction to agent")
            
            return feedback_item
        except Exception as e:
            print(f"❌ HITL: Error submitting feedback: {e}")
            return None
"""
    
    # Insert before Flask routes (before @app.route)
    route_pos = content.find("@app.route('/api/query'")
    if route_pos != -1:
        content = content[:route_pos] + init_function + "\n\n" + content[route_pos:]
        print("✅ Added HITL functions")
    
    # 3. Add API endpoints
    api_endpoints = """
# HITL API Endpoints
@app.route("/api/hitl/reviews", methods=["GET"])
def get_reviews():
    \"\"\"Get pending reviews\"\"\"
    user = require_auth()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    limit = request.args.get('limit', 50, type=int)
    reviews = get_hitl_reviews(limit=limit)
    
    return jsonify({
        'success': True,
        'count': len(reviews),
        'reviews': reviews
    })

@app.route("/api/hitl/feedback", methods=["POST"])
def submit_feedback_endpoint():
    \"\"\"Submit SME feedback\"\"\"
    user = require_auth()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    
    feedback = submit_hitl_feedback(
        review_id=data['reviewId'],
        sme_id=user['email'],
        sme_name=user.get('name', user['email']),
        feedback_type=data['feedbackType'],
        corrected_answer=data.get('correctedAnswer'),
        comments=data.get('comments', '')
    )
    
    return jsonify({
        'success': True,
        'feedbackId': feedback['id'] if feedback else None
    })

@app.route("/api/hitl/statistics", methods=["GET"])
def get_review_statistics_endpoint():
    \"\"\"Get review statistics\"\"\"
    user = require_auth()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    if not reviews_container_client:
        return jsonify({'success': False, 'error': 'HITL not available'})
    
    try:
        all_reviews = list(reviews_container_client.query_items(
            query="SELECT * FROM c WHERE c.type = 'review_item'",
            enable_cross_partition_query=True
        ))
        
        stats = {
            'total_reviews': len(all_reviews),
            'pending': sum(1 for r in all_reviews if r['status'] == ReviewStatus.PENDING),
            'in_review': sum(1 for r in all_reviews if r['status'] == ReviewStatus.IN_REVIEW),
            'approved': sum(1 for r in all_reviews if r['status'] == ReviewStatus.APPROVED),
            'rejected': sum(1 for r in all_reviews if r['status'] == ReviewStatus.REJECTED),
            'needs_revision': sum(1 for r in all_reviews if r['status'] == ReviewStatus.NEEDS_REVISION),
            'by_priority': {
                'high': sum(1 for r in all_reviews if r['priority'] == 'high'),
                'medium': sum(1 for r in all_reviews if r['priority'] == 'medium'),
                'low': sum(1 for r in all_reviews if r['priority'] == 'low')
            },
            'feedback_count': 0
        }
        
        if feedback_container_client:
            feedback_count = list(feedback_container_client.query_items(
                query="SELECT VALUE COUNT(1) FROM c WHERE c.type = 'feedback_item'",
                enable_cross_partition_query=True
            ))
            stats['feedback_count'] = feedback_count[0] if feedback_count else 0
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

"""
    
    # Insert before health check endpoint
    health_pos = content.find('@app.route("/api/health"')
    if health_pos != -1:
        content = content[:health_pos] + api_endpoints + "\n" + content[health_pos:]
        print("✅ Added HITL API endpoints")
    
    # 4. Modify /api/query to add items to review queue
    query_modification = """
    # HITL: Add to review queue if low confidence
    if 'confidence' in result and 'overall' in result['confidence']:
        avg_confidence = result['confidence']['overall']
        
        if avg_confidence < 0.7:  # Low confidence threshold
            agent_metadata = {
                'intent': result.get('intent'),
                'entities': result.get('entities'),
                'confidence': result.get('confidence'),
                'workflow': result.get('workflow')
            }
            
            priority = "high" if avg_confidence < 0.5 else "medium"
            
            create_review_item(
                user_id=user['email'],
                case_id=case_id,
                question=query,
                answer=result['answer'],
                agent_metadata=agent_metadata,
                priority=priority
            )
"""
    
    # Find return statement in /api/query endpoint
    query_return = content.find('return jsonify({')
    if query_return != -1:
        # Find the previous line
        prev_newline = content.rfind('\n', 0, query_return)
        content = content[:prev_newline] + "\n" + query_modification + content[prev_newline:]
        print("✅ Modified /api/query to auto-queue low-confidence responses")
    
    # 5. Add initialization call
    init_call = "\ninitialize_hitl_containers()\n"
    
    # Find where orchestrator is initialized
    orchestrator_init = content.find("orchestrator = DatabaseAgentOrchestrator(")
    if orchestrator_init != -1:
        next_newline = content.find("\n", orchestrator_init)
        # Find the end of this statement (might be multiline)
        statement_end = next_newline
        while content[statement_end:statement_end+1] != '\n' or content[statement_end+1:statement_end+2] in [' ', '\t', ')']:
            statement_end = content.find("\n", statement_end + 1)
            if statement_end == -1:
                break
        
        if statement_end != -1:
            content = content[:statement_end] + init_call + content[statement_end:]
            print("✅ Added HITL initialization call")
    
    # Write back to file
    output_file = "/home/claude/app_3_2_with_hitl.py"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Integration complete!")
    print(f"📄 Modified file saved to: {output_file}")
    print(f"\n📋 Next steps:")
    print("1. Review the changes in app_3_2_with_hitl.py")
    print("2. Copy it to your backend directory")
    print("3. Add to .env:")
    print("   REVIEWS_CONTAINER_NAME=hitl_reviews")
    print("   FEEDBACK_CONTAINER_NAME=sme_feedback")
    print("4. Restart your Flask app")
    print("5. Test: http://localhost:3000/api/hitl/reviews")
    
    return True

if __name__ == "__main__":
    print("🚀 HITL Quick Integration Tool")
    print("=" * 50)
    integrate_hitl_system()