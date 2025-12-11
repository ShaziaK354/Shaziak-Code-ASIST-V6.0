"""
Intent Agent Learning System
Yeh file Intent Agent ke corrections ko training data mein convert karti hay
WITH PATTERN TRACKING (Week 2 Enhancement)
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

class IntentLearning:
    """
    Intent Agent ke liye learning system
    WITH PATTERN TRACKING!
    """
    
    def __init__(self, storage_dir="hitl_learning_data"):
        """Initialize storage"""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Training data storage
        self.training_file = self.storage_dir / "training_data" / "intent_training.jsonl"
        self.training_file.parent.mkdir(exist_ok=True)
        
        # NEW: Pattern storage
        self.patterns_file = self.storage_dir / "patterns" / "intent_patterns.json"
        self.patterns_file.parent.mkdir(exist_ok=True)
        
        # Load existing data
        self.training_samples = self._load_training_samples()
        self.patterns = self._load_patterns()
        
        print(f"✅ IntentLearning initialized")
        print(f"   📂 Storage: {self.storage_dir}")
        print(f"   📝 Existing samples: {len(self.training_samples)}")
        print(f"   📊 Existing patterns: {len(self.patterns)}")
    
    def _load_training_samples(self) -> List[Dict]:
        """Load existing training samples from file"""
        samples = []
        if self.training_file.exists():
            try:
                with open(self.training_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            samples.append(json.loads(line))
            except Exception as e:
                print(f"⚠️  Error loading samples: {e}")
        return samples
    
    def _load_patterns(self) -> Dict:
        """Load existing patterns"""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading patterns: {e}")
        return {}
    
    def _save_patterns(self):
        """Save patterns to file"""
        try:
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving patterns: {e}")
    
    def _hash_question(self, question: str) -> str:
        """Create consistent hash for question"""
        normalized = question.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def _track_pattern(self, original: str, corrected: str, question: str):
        """Track misclassification pattern"""
        pattern_key = f"{original}→{corrected}"
        
        if pattern_key not in self.patterns:
            self.patterns[pattern_key] = {
                "count": 0,
                "examples": []
            }
        
        self.patterns[pattern_key]["count"] += 1
        self.patterns[pattern_key]["examples"].append({
            "question": question[:100],  # First 100 chars
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Keep only last 10 examples
        if len(self.patterns[pattern_key]["examples"]) > 10:
            self.patterns[pattern_key]["examples"] = self.patterns[pattern_key]["examples"][-10:]
        
        self._save_patterns()
        
        print(f"📊 Pattern tracked: {pattern_key} (count: {self.patterns[pattern_key]['count']})")
    
    def save_correction(self, correction_data: Dict) -> Dict:
        """
        Main function: Save intent correction as training data
        WITH PATTERN TRACKING!
        
        Args:
            correction_data = {
                "question": "What is CN threshold?",
                "original_intent": "procedural",
                "corrected_intent": "factual_lookup",
                "confidence": 0.65
            }
        
        Returns:
            Result dictionary with success status
        """
        try:
            # Step 1: Extract data
            question = correction_data.get('question', '')
            original = correction_data.get('original_intent', '')
            corrected = correction_data.get('corrected_intent', '')
            confidence = correction_data.get('confidence', 0.0)
            
            # Validation
            if not question or not corrected:
                return {
                    "success": False,
                    "error": "Missing question or corrected_intent"
                }
            
            # Step 2: Create training sample
            training_sample = {
                "text": question,
                "label": corrected,  # Correct intent
                "metadata": {
                    "original_prediction": original,
                    "confidence": confidence,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "hash": self._hash_question(question)
                }
            }
            
            # Step 3: Save to file (append)
            with open(self.training_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(training_sample) + '\n')
            
            # Step 4: Add to memory
            self.training_samples.append(training_sample)
            
            # Step 5: NEW - Track pattern
            pattern_tracked = None
            if original:  # Only if we have original intent
                self._track_pattern(original, corrected, question)
                pattern_tracked = f"{original}→{corrected}"
            
            # Step 6: Print success
            print(f"✅ Training sample saved!")
            print(f"   Question: {question[:50]}...")
            print(f"   Label: {corrected}")
            print(f"   Total samples: {len(self.training_samples)}")
            if pattern_tracked:
                print(f"   Pattern: {pattern_tracked}")
            
            return {
                "success": True,
                "training_sample_created": True,
                "total_samples": len(self.training_samples),
                "pattern_tracked": pattern_tracked,  # NEW
                "file_path": str(self.training_file)
            }
            
        except Exception as e:
            print(f"❌ Error saving correction: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stats(self) -> Dict:
        """Get training statistics"""
        return {
            "total_samples": len(self.training_samples),
            "file_location": str(self.training_file),
            "retraining_progress": f"{len(self.training_samples)}/100",
            "ready_for_retraining": len(self.training_samples) >= 100,
            "patterns_tracked": len(self.patterns)  # NEW
        }
    
    def get_patterns(self) -> Dict:
        """Get top patterns"""
        # Sort by count
        sorted_patterns = sorted(
            self.patterns.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        return {
            "total_patterns": len(self.patterns),
            "top_patterns": [
                {
                    "pattern": pattern,
                    "count": data["count"],
                    "examples": data["examples"][:3]  # Top 3 examples
                }
                for pattern, data in sorted_patterns[:5]  # Top 5 patterns
            ]
        }
    
    def get_detailed_stats(self) -> Dict:
        """Get comprehensive statistics (Week 3 addition)"""
        # Count intents
        intent_distribution = {}
        for sample in self.training_samples:
            intent = sample['label']
            intent_distribution[intent] = intent_distribution.get(intent, 0) + 1
        
        # Get pattern stats
        patterns = self.get_patterns()
        
        return {
            "overview": {
                "total_samples": len(self.training_samples),
                "retraining_threshold": 100,
                "progress_percent": (len(self.training_samples) / 100) * 100,
                "ready_for_retraining": len(self.training_samples) >= 100
            },
            "intent_distribution": intent_distribution,
            "patterns": patterns,
            "recent_samples": [
                {
                    "question": s["text"][:50],
                    "intent": s["label"],
                    "timestamp": s["metadata"]["timestamp"]
                }
                for s in self.training_samples[-5:]  # Last 5
            ]
        }


# Test function
if __name__ == "__main__":
    print("="*60)
    print("Testing IntentLearning Class WITH PATTERN TRACKING")
    print("="*60)
    
    # Initialize
    intent_learning = IntentLearning()
    
    # Test multiple corrections with same pattern
    print("\n" + "="*60)
    print("Testing Pattern Tracking (same pattern multiple times)")
    print("="*60)
    
    corrections = [
        {
            "question": "What is CN?",
            "original_intent": "procedural",
            "corrected_intent": "factual_lookup",
            "confidence": 0.6
        },
        {
            "question": "Define LOA",
            "original_intent": "procedural",
            "corrected_intent": "factual_lookup",
            "confidence": 0.55
        },
        {
            "question": "What is FMS?",
            "original_intent": "procedural",
            "corrected_intent": "factual_lookup",
            "confidence": 0.7
        },
        {
            "question": "How do I process CN?",
            "original_intent": "factual_lookup",
            "corrected_intent": "procedural",
            "confidence": 0.65
        }
    ]
    
    for i, corr in enumerate(corrections, 1):
        print(f"\n--- Test {i} ---")
        result = intent_learning.save_correction(corr)
        print(f"Result: {result.get('pattern_tracked', 'No pattern')}")
    
    # Get patterns
    print("\n" + "="*60)
    print("Pattern Analysis")
    print("="*60)
    patterns = intent_learning.get_patterns()
    print(json.dumps(patterns, indent=2))
    
    # Get stats
    print("\n" + "="*60)
    print("Statistics")
    print("="*60)
    stats = intent_learning.get_stats()
    print(json.dumps(stats, indent=2))
    
    # Get detailed stats
    print("\n" + "="*60)
    print("Detailed Statistics")
    print("="*60)
    detailed = intent_learning.get_detailed_stats()
    print(json.dumps(detailed, indent=2))
