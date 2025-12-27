from app.db.session import engine
from app.db.base import Base
from app.db.models.user import User
from app.db.session import SessionLocal
from app.crud.user import create_user

db = SessionLocal()


Base.metadata.create_all(bind=engine)

def main():
    user = create_user(db, "Sameer", "sameer@example.com")
    print(user.id)
    print("Hello, Bruno Discord Agent!")

if __name__ == "__main__":
    main()