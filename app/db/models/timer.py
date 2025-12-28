from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Timer(Base):
    __tablename__ = "timers"
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
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
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="timers")