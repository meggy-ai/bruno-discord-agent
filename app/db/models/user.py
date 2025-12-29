from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(120), unique=True, index=True)
    
    # Relationships
    notes = relationship("Note", back_populates="user")
    timers = relationship("Timer", back_populates="user")
