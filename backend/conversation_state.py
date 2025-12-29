import time
from enum import Enum

class State(Enum):
    IDLE = "idle"                   # ממתין, פנוי
    LISTENING = "listening"         # מקשיב למשתמש כרגע
    THINKING = "thinking"           # מעבד תשובה (במוח או ב-GPT)
    SPEAKING = "speaking"           # מדבר כרגע (TTS מנגן)
    DEEP_CONVERSATION = "deep_chat" # מצב שיחה מתמשכת (מונע הפרעות)

class ConversationState:
    """
    מנהל את המצבים של Nog כדי למנוע התנגשויות (כמו לדבר ולהקשיב בו זמנית).
    """
    def __init__(self):
        self.current_state = State.IDLE
        self.last_state_change = time.time()
        self.conversation_start_time = 0
        self.interaction_count = 0 # כמה תגובות היו בשיחה הנוכחית

    def set_state(self, new_state):
        """שינוי מצב בטוח"""
        if self.current_state == new_state:
            return

        print(f"🔄 Status Change: {self.current_state.value} -> {new_state.value}")
        self.current_state = new_state
        self.last_state_change = time.time()

        # לוגיקה למצבים מיוחדים
        if new_state == State.DEEP_CONVERSATION:
            if self.conversation_start_time == 0:
                self.conversation_start_time = time.time()
        
        elif new_state == State.IDLE:
            # אם חזרנו ל-IDLE אחרי זמן רב, אפס את מונה השיחה
            if time.time() - self.conversation_start_time > 300: # 5 דקות הפסקה
                self.interaction_count = 0
                self.conversation_start_time = 0

    def get_state(self):
        return self.current_state

    def is_busy(self):
        """האם המערכת עסוקה (לא יכולה לקבל פקודות חדשות כרגע)"""
        return self.current_state in [State.THINKING, State.SPEAKING]

    def should_listen(self):
        """האם המיקרופון צריך להיות פתוח?"""
        return self.current_state in [State.IDLE, State.DEEP_CONVERSATION, State.LISTENING]

    def increment_interaction(self):
        self.interaction_count += 1
        # אם יש כבר 3 אינטראקציות רצופות, אנחנו ב"שיחה עמוקה"
        if self.interaction_count >= 3 and self.current_state != State.DEEP_CONVERSATION:
            self.set_state(State.DEEP_CONVERSATION)

state_machine = ConversationState()