# backend/prediction_engine.py

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from user_model import user_model
from beliefs import beliefs_system

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
PREDICTIONS_PATH = os.path.join(DATA_DIR, "predictions.json")

class PredictionEngine:
    """
    מנוע תחזיות - צופה מה המשתמש ירצה לפני שהוא מבקש.
    
    זה מה שהופך את Nog מ"מגיב לבקשות" ל"מצפה לצרכים".
    
    Features:
    - Pattern Recognition: מזהה דפוסים חוזרים
    - Context Prediction: צופה צעד הבא מההקשר
    - Temporal Prediction: יודע מה קורה באיזו שעה
    - Need Inference: מסיק צרכים לא מפורשים
    
    Examples:
    - "אני רואה שאתה עובד על X - בטח תרצה את Y בעוד רגע"
    - "בדרך כלל בשעה הזו אתה בודק ביטקוין - הנה המחיר"
    - "כשאתה מתחיל פגישה אתה תמיד צריך את המסמך - הנה הוא"
    """
    
    def __init__(self):
        self.prediction_history = self.load_history()
        self.patterns = defaultdict(list)  # דפוסים שזוהו
    
    def load_history(self):
        if os.path.exists(PREDICTIONS_PATH):
            try:
                with open(PREDICTIONS_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"predictions": [], "accuracy": 0.0}
        return {"predictions": [], "accuracy": 0.0}
    
    def save_history(self):
        try:
            with open(PREDICTIONS_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.prediction_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving predictions: {e}")
    
    def predict_next_action(self, current_context):
        """
        צופה מה המשתמש ירצה הבא.
        
        Args:
            current_context (dict): הקשר נוכחי
        
        Returns:
            dict: {
                "prediction": str,
                "confidence": float,
                "reasoning": str,
                "should_offer": bool
            }
        """
        
        predictions = []
        
        # === תחזית 1: לפי שעה ===
        temporal_pred = self._predict_by_time()
        if temporal_pred:
            predictions.append(temporal_pred)
        
        # === תחזית 2: לפי דפוס רצף ===
        sequence_pred = self._predict_by_sequence(current_context)
        if sequence_pred:
            predictions.append(sequence_pred)
        
        # === תחזית 3: לפי אמונות ===
        belief_pred = self._predict_by_beliefs()
        if belief_pred:
            predictions.append(belief_pred)
        
        # === תחזית 4: לפי הקשר מיידי ===
        immediate_pred = self._predict_by_immediate_context(current_context)
        if immediate_pred:
            predictions.append(immediate_pred)
        
        # בחירת התחזית הטובה ביותר
        if predictions:
            predictions.sort(key=lambda x: x["confidence"], reverse=True)
            best = predictions[0]
            
            # החלט אם להציע
            best["should_offer"] = best["confidence"] > 0.6
            
            return best
        
        return {
            "prediction": None,
            "confidence": 0.0,
            "reasoning": "No patterns identified",
            "should_offer": False
        }
    
    def _predict_by_time(self):
        """
        תחזית לפי שעה - מה בדרך כלל קורה בשעה הזו?
        
        Example:
            - 09:00: "בדרך כלל אתה קורא חדשות עכשיו"
            - 22:00: "בדרך כלל אתה מתחיל לקודד עכשיו"
        """
        
        current_hour = datetime.now().hour
        user_data = user_model.data
        
        # בדוק אם זו שעת peak productivity
        for period, data in user_data["patterns"]["productive_hours"].items():
            start_h = int(data["start"].split(":")[0])
            end_h = int(data["end"].split(":")[0])
            conf = data["confidence"]
            
            # טיפול במעבר חצות
            if start_h > end_h:
                if current_hour >= start_h or current_hour < end_h:
                    if conf > 0.7:
                        return {
                            "prediction": f"בדרך כלל אתה פרודוקטיבי עכשיו ({period}) - משהו ספציפי שתרצה לעשות?",
                            "confidence": conf,
                            "reasoning": f"User is in {period} productive period",
                            "type": "temporal_productivity"
                        }
            else:
                if start_h <= current_hour < end_h:
                    if conf > 0.7:
                        return {
                            "prediction": f"זו השעה שאתה הכי פרודוקטיבי - בוא נעשה משהו",
                            "confidence": conf,
                            "reasoning": f"User is in {period} productive period",
                            "type": "temporal_productivity"
                        }
        
        # בדוק אם זו שעת הסחה ידועה
        for trigger, data in user_data["patterns"]["distraction_triggers"].items():
            if data.get("count", 0) > 10:
                # אם זו השעה שהמשתמש בדרך כלל נסחג
                if trigger == "bitcoin_price" and current_hour in [9, 14, 22]:
                    return {
                        "prediction": "בדרך כלל אתה בודק ביטקוין עכשיו - רוצה שאביא לך את המחיר?",
                        "confidence": 0.7,
                        "reasoning": "User tends to check Bitcoin at this hour",
                        "type": "temporal_distraction"
                    }
        
        return None
    
    def _predict_by_sequence(self, context):
        """
        תחזית לפי רצף - מה בא אחרי X?
        
        Example:
            - אחרי "open VS Code" בדרך כלל בא "run script"
            - אחרי "פגישה" בדרך כלל בא "notes summary"
        """
        
        last_action = context.get("last_action")
        if not last_action:
            return None
        
        # דפוסי רצף ידועים (צריך למידה)
        known_sequences = {
            "coding": "test",
            "meeting": "notes",
            "research": "summary"
        }
        
        for trigger, next_action in known_sequences.items():
            if trigger in last_action.lower():
                return {
                    "prediction": f"אחרי {trigger} אתה בדרך כלל עושה {next_action} - להכין?",
                    "confidence": 0.6,
                    "reasoning": f"Common sequence: {trigger} → {next_action}",
                    "type": "sequence_prediction"
                }
        
        return None
    
    def _predict_by_beliefs(self):
        """
        תחזית לפי אמונות - מה המשתמש בדרך כלל אוהב/צריך?
        """
        
        high_conf_beliefs = beliefs_system.get_high_confidence_beliefs("about_user", min_confidence=0.75)
        
        for belief in high_conf_beliefs:
            statement = belief["statement"].lower()
            
            # אם יש אמונה על דפוס התנהגות
            if "distracted" in statement and "bitcoin" in statement:
                return {
                    "prediction": "אני רואה שאתה מסתכל בכיוון של מחירי קריפטו - רוצה שאעדכן אותך?",
                    "confidence": belief["confidence"],
                    "reasoning": f"Based on belief: {belief['statement']}",
                    "type": "belief_based"
                }
        
        return None
    
    def _predict_by_immediate_context(self, context):
        """
        תחזית לפי הקשר מיידי - מה עושים עכשיו?
        """
        
        recent_activity = context.get("recent_activity", "")
        
        # אם יש פעילות של כתיבת קוד
        if any(word in recent_activity.lower() for word in ["code", "script", "function"]):
            return {
                "prediction": "רואה שאתה מקודד - צריך עזרה בדיבאג או לרוץ משהו?",
                "confidence": 0.5,
                "reasoning": "Detected coding activity",
                "type": "immediate_context"
            }
        
        return None
    
    def log_prediction(self, prediction, actual_need, was_correct):
        """
        רושם תחזית ומעדכן דיוק.
        
        Args:
            prediction (str): מה חזינו
            actual_need (str): מה היה בפועל
            was_correct (bool): האם צדקנו
        """
        
        self.prediction_history["predictions"].append({
            "timestamp": datetime.now().isoformat(),
            "prediction": prediction,
            "actual": actual_need,
            "was_correct": was_correct
        })
        
        # עדכון דיוק
        total = len(self.prediction_history["predictions"])
        correct = sum(1 for p in self.prediction_history["predictions"] if p.get("was_correct"))
        self.prediction_history["accuracy"] = correct / total if total > 0 else 0.0
        
        self.save_history()
        
        print(f"🔮 Prediction Accuracy: {self.prediction_history['accuracy']:.0%} ({correct}/{total})")
    
    def get_summary(self):
        """
        מחזיר סיכום היכולות החיזוי.
        
        Returns:
            str: טקסט מעוצב
        """
        
        accuracy = self.prediction_history.get("accuracy", 0.0)
        total = len(self.prediction_history.get("predictions", []))
        
        summary = f"PREDICTION ENGINE:\n"
        summary += f"  • Total Predictions: {total}\n"
        summary += f"  • Accuracy: {accuracy:.0%}\n"
        
        if accuracy > 0.7:
            summary += "  • Status: High accuracy - predictions are reliable\n"
        elif accuracy > 0.5:
            summary += "  • Status: Moderate accuracy - improving\n"
        else:
            summary += "  • Status: Low accuracy - learning patterns\n"
        
        return summary

# יצירת מופע גלובלי
prediction_engine = PredictionEngine()
