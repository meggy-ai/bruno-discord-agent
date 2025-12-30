from app.db.session import get_db_session
from app.db.models import Conversation
from app.db.models import Message  
from typing import Optional
from datetime import datetime

class MemoryStore:
    def __init__(self, db):
        self.db = db


    def create_conversation(self, user_id: int, title: str):
        conversation = Conversation(user_id=user_id, title=title)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def get_conversation(self, conversation_id: int):
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    def get_conversations_for_user(self, user_id: int):
        return self.db.query(Conversation).filter(Conversation.user_id == user_id).first()
    
     # ==================== Message Operations ====================
    
    def add_message(self, conversation_id: int, role: str, content: str, sequence_number: Optional[int] = None, intent: str = None, entities: str = None):
        if sequence_number is None:
            last_message = self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.sequence_number.desc()).first()
            sequence_number = last_message.sequence_number + 1 if last_message else 1
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            timestamp=datetime.now(),
            sequence_number=sequence_number,
            intent=intent,
            entities=entities
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message