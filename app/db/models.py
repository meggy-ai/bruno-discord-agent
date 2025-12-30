from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    username = Column(String(100), unique=True, index=True)
    
    # Relationships
    notes = relationship("Note", back_populates="user")
    timers = relationship("Timer", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)  # Changed from Integer to DateTime
    sequence_number = Column(Integer, nullable=False)
    intent = Column(String(100), nullable=True)
    entities = Column(String, nullable=True)  # JSON string of entities

    conversation = relationship("Conversation", back_populates="messages")


class Timer(Base):
    __tablename__ = "timers"
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(String(100), nullable=True, comment='External conversation identifier') 
    
    # Timer details
    name = Column(String(200), nullable=False, comment='Description of what the timer is for')
    duration_seconds = Column(Integer, nullable=False, comment='Total duration in seconds')
    end_time = Column(DateTime, nullable=False, comment='When the timer will end')
    
    # State management
    status = Column(String(20), nullable=False, default='active', comment='Current status of the timer')
    paused_at = Column(DateTime, nullable=True, comment='Timestamp when the timer was paused')
    remaining_seconds = Column(Integer, nullable=True, comment='Seconds remaining when paused')
    
    # Notifications 
    three_minute_warning_sent = Column(Boolean, default=False)
    completion_notification_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="timers")

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), default='Untitled')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships 
    user = relationship("User", back_populates="notes")
    entries = relationship("NoteEntry", back_populates="note", cascade="all, delete-orphan")

class NoteEntry(Base):
    __tablename__ = "note_entries"
    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship
    note = relationship("Note", back_populates="entries")



