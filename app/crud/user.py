from sqlalchemy.orm import Session
from app.db.models import User
from typing import Optional

def create_user(db: Session, name: str, username: str):
    user = User(name=name, username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_or_get_user(db: Session, username: str, name: Optional[str] = None):
    user = get_user_by_username(db, username)
    if user:
        return user
    else:
        return create_user(db, name or username, username)
        