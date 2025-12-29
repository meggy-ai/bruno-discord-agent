from sqlalchemy.orm import Session
from app.db.models.user import User

def create_user(db: Session, name: str, email: str, username: str):
    user = User(name=name, email=email, username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_or_get_user(db: Session, name: str, username: str, email: str = None):
    user = get_user_by_username(db, username)
    if user:
        return user
    return create_user(db, name, username, email)