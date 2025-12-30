
from app.crud import user as user_crud

class UserManager:
    def __init__(self, db):
        self.db = db
    def get_user_by_username(self, username: str):
        user = user_crud.get_user_by_username(self.db, username)
        if not user:
            user = user_crud.create_user(self.db, "", username)
        return user