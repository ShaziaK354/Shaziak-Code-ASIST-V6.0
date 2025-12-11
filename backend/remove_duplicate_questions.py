"""
HITL Reviews - Duplicate Questions Remover (FIXED - Partition Key: /type)
==========================================================================
Yeh script Cosmos DB se duplicate questions remove karti hai.
Partition key: /type (value: "review_item")

Requirements:
    pip install azure-cosmos python-dotenv

Usage:
    python remove_duplicates_FIXED.py
"""

import json
from datetime import datetime
from collections import OrderedDict
from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("DATABASE_NAME")
REVIEWS_CONTAINER_NAME = "reviews"

# PARTITION KEY (from screenshot: /type)
PARTITION_KEY_VALUE = "review_item"

# ============================================================================
# FUNCTIONS
# ============================================================================

def connect_to_cosmos():
    """Cosmos DB se connection banao"""
    print("🔌 Connecting to Cosmos DB...")
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.get_database_client(DATABASE_NAME)
    container = database.get_container_client(REVIEWS_CONTAINER_NAME)
    print("✅ Connected successfully!")
    
    # Verify partition key
    properties = container.read()
    partition_key_path = properties.get('partitionKey', {}).get('paths', ['Unknown'])[0]
    print(f"📌 Partition Key Path: {partition_key_path}")
    
    return container

def fetch_all_reviews(container):
    """Saari reviews fetch karo"""
    print("\n📥 Fetching all reviews from Cosmos DB...")
    
    query = """
    SELECT c.id, c.reviewId, c.question, c.type, c.timestamp
    FROM c 
    WHERE c.type = 'review_item'
    ORDER BY c.timestamp ASC
    """
    
    reviews = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    
    print(f"✅ Fetched {len(reviews)} total reviews")
    return reviews

def identify_duplicates(reviews):
    """
    Duplicate questions identify karo
    Keep FIRST occurrence, mark REST as duplicates
    """
    print("\n🔍 Identifying duplicate questions...")
    
    seen_questions = {}
    unique_items = []
    duplicate_items = []
    
    for item in reviews:
        question = item.get('question', '').strip()
        
        if not question:
            print(f"   ⚠️  Skipping item with empty question: {item.get('id', 'unknown')}")
            continue
        
        # Normalize question for comparison
        normalized = ' '.join(question.lower().split())
        
        if normalized not in seen_questions:
            # First occurrence - KEEP
            seen_questions[normalized] = item
            unique_items.append(item)
        else:
            # Duplicate - MARK for deletion
            duplicate_items.append(item)
            
            if len(duplicate_items) <= 5:  # Show first 5 duplicates as preview
                print(f"   📍 Duplicate: {question[:60]}...")
    
    if len(duplicate_items) > 5:
        print(f"   ... and {len(duplicate_items) - 5} more duplicates")
    
    print(f"\n✅ Found {len(unique_items)} unique questions")
    print(f"⚠️  Found {len(duplicate_items)} duplicate questions")
    
    return unique_items, duplicate_items

def save_backup(reviews, duplicates):
    """Backup save karo"""
    print("\n💾 Saving backup files...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # All reviews backup
    backup_file = f'backup_all_reviews_{timestamp}.json'
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)
    print(f"✅ All reviews backed up: {backup_file}")
    
    # Duplicates list
    duplicates_file = f'backup_duplicates_{timestamp}.json'
    with open(duplicates_file, 'w', encoding='utf-8') as f:
        json.dump(duplicates, f, indent=2, ensure_ascii=False)
    print(f"✅ Duplicates list saved: {duplicates_file}")
    
    return backup_file, duplicates_file

def delete_duplicates(container, duplicates):
    """
    Cosmos DB se duplicate reviews delete karo
    Using partition key: /type with value "review_item"
    """
    print("\n🗑️  Deleting duplicates from Cosmos DB...")
    print(f"   Total to delete: {len(duplicates)}")
    print(f"   Using partition key: /type = '{PARTITION_KEY_VALUE}'")
    
    deleted_count = 0
    failed_items = []
    
    for i, dup in enumerate(duplicates, 1):
        item_id = dup.get('id')
        
        if not item_id:
            print(f"   ⚠️  [{i}/{len(duplicates)}] No ID found, skipping...")
            failed_items.append({"item": dup, "reason": "No ID"})
            continue
        
        try:
            # CRITICAL: Use correct partition key value
            container.delete_item(
                item=item_id, 
                partition_key=PARTITION_KEY_VALUE  # "review_item"
            )
            
            deleted_count += 1
            
            # Progress updates
            if i % 10 == 0:
                print(f"   ✓ Deleted {deleted_count}/{len(duplicates)}...")
            
            # Small delay to avoid rate limiting
            if i % 50 == 0:
                time.sleep(0.5)
                
        except exceptions.CosmosResourceNotFoundError:
            print(f"   ⚠️  [{i}/{len(duplicates)}] Not found: {item_id[:20]}... (may be already deleted)")
            failed_items.append({"item_id": item_id, "reason": "Not found"})
            
        except exceptions.CosmosHttpResponseError as e:
            print(f"   ❌ [{i}/{len(duplicates)}] Error deleting {item_id[:20]}...: {e.status_code}")
            failed_items.append({"item_id": item_id, "reason": str(e)})
            
        except Exception as e:
            print(f"   ❌ [{i}/{len(duplicates)}] Unexpected error: {e}")
            failed_items.append({"item_id": item_id, "reason": str(e)})
    
    print(f"\n✅ Successfully deleted: {deleted_count}")
    
    if failed_items:
        print(f"⚠️  Failed to delete: {len(failed_items)}")
        
        # Save failed items for review
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        failed_file = f'failed_deletions_{timestamp}.json'
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump(failed_items, f, indent=2, ensure_ascii=False)
        print(f"   Failed items saved to: {failed_file}")
    
    return deleted_count, failed_items

def verify_deletion(container):
    """Verify final count after deletion"""
    print("\n🔍 Verifying deletion...")
    
    query = "SELECT VALUE COUNT(1) FROM c WHERE c.type = 'review_item'"
    count = list(container.query_items(
        query=query, 
        enable_cross_partition_query=True
    ))[0]
    
    print(f"✅ Current count in database: {count}")
    return count

def generate_report(original_count, unique_count, deleted_count, final_count):
    """Final report"""
    print("\n" + "="*60)
    print("📊 DUPLICATE REMOVAL REPORT")
    print("="*60)
    print(f"Original Reviews:     {original_count}")
    print(f"Unique Reviews:       {unique_count}")
    print(f"Duplicates Found:     {original_count - unique_count}")
    print(f"Duplicates Deleted:   {deleted_count}")
    print(f"Final Count:          {final_count}")
    print("="*60)
    
    if deleted_count == (original_count - unique_count):
        print("✅ SUCCESS: All duplicates removed!")
    else:
        print(f"⚠️  WARNING: Some deletions may have failed")
        print(f"   Expected to delete: {original_count - unique_count}")
        print(f"   Actually deleted: {deleted_count}")

# ============================================================================
# MAIN SCRIPT
# ============================================================================

def main():
    """Main execution"""
    print("="*60)
    print("🚀 HITL Reviews - Duplicate Removal (FIXED)")
    print("="*60)
    print(f"Partition Key: /type = '{PARTITION_KEY_VALUE}'")
    print("="*60)
    
    # Step 1: Connect
    try:
        container = connect_to_cosmos()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Step 2: Fetch reviews
    try:
        reviews = fetch_all_reviews(container)
        if not reviews:
            print("⚠️  No reviews found!")
            return
        original_count = len(reviews)
    except Exception as e:
        print(f"❌ Failed to fetch reviews: {e}")
        return
    
    # Step 3: Identify duplicates
    unique_reviews, duplicates = identify_duplicates(reviews)
    
    if not duplicates:
        print("\n🎉 No duplicates found! Database is clean.")
        return
    
    # Step 4: Save backup
    backup_file, duplicates_file = save_backup(reviews, duplicates)
    
    # Step 5: Confirm deletion
    print(f"\n⚠️  WARNING: About to delete {len(duplicates)} duplicate reviews!")
    print("   Backup files have been created for safety.")
    print(f"   Backups: {backup_file}, {duplicates_file}")
    
    confirm = input("\n🔴 Type 'DELETE' to confirm deletion (or anything else to cancel): ")
    
    if confirm.strip().upper() != 'DELETE':
        print("❌ Operation cancelled by user")
        print("   No changes made to database")
        return
    
    # Step 6: Delete duplicates
    deleted_count, failed_items = delete_duplicates(container, duplicates)
    
    # Step 7: Verify
    final_count = verify_deletion(container)
    
    # Step 8: Report
    generate_report(original_count, len(unique_reviews), deleted_count, final_count)
    
    print("\n✅ Process completed successfully!")
    print("   - Backup files saved")
    print("   - Duplicates removed from Cosmos DB")
    print("   - Dashboard refresh karo to see updated count")

if __name__ == "__main__":
    main()