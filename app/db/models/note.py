from sqlalchemy import Column, ForeignKey, Integer, String
from app.db.base import Base
from sqlalchemy import DateTime
from datetime import datetime
from sqlalchemy.orm import relationship

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    user = relationship("User", back_populates="notes")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), default='Untitled')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to note entries
    entries = relationship("NoteEntry", back_populates="note")

class NoteEntry(Base):
    __tablename__ = "note_entries"
    id = Column(Integer, primary_key=True, index=True)
    note = relationship("Note", back_populates="entries")
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False)
    content = Column(String, nullable=False)
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)