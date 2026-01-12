# backend/autonomous_learning.py

import json
import os
from datetime import datetime
from beliefs import beliefs_system
from verification import verification_engine
from metacognition import metacognition
from user_model import user_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
LEARNING_LOG_PATH = os.path.join(DATA_DIR, "autonomous_learning.json")

class AutonomousLearning:
    """
    למידה אוטונומית - Nog משפר את עצמו בלי עזרה.
    
    Learning Modes:
    1. Pattern Discovery - מגלה דפוסים חדשים
    2. Hypothesis Testing - בודק תיאוריות
    3. Self-Calibration - מכייל ביטחון
    4. Strategy Optimization - משפר אסטרטגיות
    """
    
    def __init__(self):
        self.learning_log = self.load_log()
        self.learning_cycles = 0
        self.min_data_points = 5
        self.confidence_threshold = 0.7
    
    def load_log(self):
        if os.path.exists(LEARNING_LOG_PATH):
            try:
                with open(LEARNING_LOG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._create_initial_log()
        return self._create_initial_log()
    
    def _create_initial_log(self):
        return {
            "learning_cycles": 0,
            "discoveries": [],
            "hypotheses_tested": [],
            "improvements_made": [],
            "meta": {
                "last_learning": None,
                "total_discoveries": 0,
                "successful_hypotheses": 0,
                "failed_hypotheses": 0
            }
        }
    
    def save_log(self):
        try:
            self.learning_log["meta"]["last_learning"] = datetime.now().isoformat()
            with open(LEARNING_LOG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.learning_log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving learning log: {e}")
    
    def run_learning_cycle(self):
        """מריץ מחזור למידה מלא"""
        print("🧠 === AUTONOMOUS LEARNING CYCLE ===")
        
        self.learning_cycles += 1
        cycle_results = {
            "cycle_number": self.learning_cycles,
            "timestamp": datetime.now().isoformat(),
            "discoveries": [],
            "improvements": []
        }
        
        # שלב 1: Pattern Discovery
        print("🔍 Discovering patterns...")
        discoveries = self._discover_patterns()
        cycle_results["discoveries"] = discoveries
        
        # שלב 2: Hypothesis Testing
        print("🧪 Testing hypotheses...")
        self._test_hypotheses()
        
        # שלב 3: Self-Calibration
        print("📊 Calibrating...")
        self._calibrate_confidence()
        
        # שלב 4: Strategy Optimization
        print("⚡ Optimizing strategies...")
        improvements = self._optimize_strategies()
        cycle_results["improvements"] = improvements
        
        # שמירה
        self.learning_log["learning_cycles"] += 1
        self.learning_log["discoveries"].extend(discoveries)
        self.save_log()
        
        print(f"✅ Cycle complete: {len(discoveries)} discoveries, {len(improvements)} improvements")
        
        return cycle_results
    
    def _discover_patterns(self):
        """מגלה דפוסים חדשים"""
        discoveries = []
        user_data = user_model.data
        
        # גילוי שעות פיק
        productive_hours = user_data["patterns"]["productive_hours"]
        for period, data in productive_hours.items():
            conf = data.get("confidence", 0)
            count = data.get("count", 0)
            
            if count >= self.min_data_points and conf > self.confidence_threshold:
                existing = beliefs_system.get_belief("about_user", f"productive_{period}")
                
                if not existing:
                    discovery = {
                        "type": "productive_pattern",
                        "statement": f"User productive during {period}",
                        "confidence": conf,
                        "evidence_count": count,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    discoveries.append(discovery)
                    
                    beliefs_system.add_belief(
                        "about_user",
                        f"productive_{period}",
                        f"Maor is productive during {period}",
                        confidence=conf,
                        source="autonomous_discovery"
                    )
                    
                    print(f"💡 Discovery: {discovery['statement']}")
        
        # גילוי הסחות
        distractions = user_data["patterns"]["distraction_triggers"]
        for trigger, data in distractions.items():
            count = data.get("count", 0)
            severity = data.get("severity", "low")
            
            if count >= self.min_data_points and severity in ["medium", "high"]:
                existing = beliefs_system.get_belief("about_user", f"distracted_by_{trigger}")
                
                if not existing:
                    discovery = {
                        "type": "distraction_pattern",
                        "statement": f"User distracted by {trigger}",
                        "confidence": min(0.9, count / 20),
                        "evidence_count": count,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    discoveries.append(discovery)
                    
                    beliefs_system.add_belief(
                        "about_user",
                        f"distracted_by_{trigger}",
                        f"Maor distracted by {trigger}",
                        confidence=discovery["confidence"],
                        source="autonomous_discovery"
                    )
                    
                    print(f"💡 Discovery: {discovery['statement']}")
        
        return discoveries
    
    def _test_hypotheses(self):
        """בודק תיאוריות"""
        uncertain_beliefs = beliefs_system.get_uncertain_beliefs(max_confidence=0.6)
        
        if not uncertain_beliefs:
            return []
        
        tested = []
        for item in uncertain_beliefs[:3]:
            category = item["category"]
            key = item["key"]
            
            result = verification_engine.verify_belief(category, key)
            tested.append(result)
            
            if result["verified"]:
                self.learning_log["meta"]["successful_hypotheses"] += 1
            else:
                self.learning_log["meta"]["failed_hypotheses"] += 1
        
        return tested
    
    def _calibrate_confidence(self):
        """מכייל ביטחון"""
        verification_log = verification_engine.verification_log
        recent = verification_log.get("verifications", [])[-10:]
        
        if not recent:
            return
        
        correct = sum(1 for v in recent if v.get("verified"))
        total = len(recent)
        accuracy = correct / total
        
        metacognition.calibrate(accuracy > 0.7)
        
        print(f"   Calibration: {accuracy:.0%} accuracy")
    
    def _optimize_strategies(self):
        """משפר אסטרטגיות"""
        improvements = []
        
        # שיפור ask-back frequency
        ask_back_stats = metacognition.state["meta"]
        total_ask_backs = ask_back_stats.get("total_ask_backs", 0)
        
        if total_ask_backs > 20:
            current_threshold = metacognition.state["uncertainty_threshold"]
            new_threshold = max(0.3, current_threshold - 0.05)
            metacognition.state["uncertainty_threshold"] = new_threshold
            
            improvement = {
                "type": "ask_back_frequency",
                "action": "Reduced ask-back threshold",
                "old_value": current_threshold,
                "new_value": new_threshold,
                "reasoning": "Too many ask-backs"
            }
            
            improvements.append(improvement)
            metacognition.save()
            
            print(f"   Improvement: {improvement['reasoning']}")
        
        return improvements

# יצירת מופע גלובלי
autonomous_learning = AutonomousLearning()
