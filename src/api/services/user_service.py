from src.api.core.security import hash_password, verify_password
from src.api.schemas.auth import UserInDB

# ⚠️ Simulation - à remplacer par une vraie DB
fake_users_db = {
    "alice": UserInDB(
        username="alice",
        hashed_password=hash_password("wonderland"),
    )
}

def get_user(username: str) -> UserInDB | None:
    return fake_users_db.get(username)

def authenticate_user(username: str, password: str) -> UserInDB | None:
    user = get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user