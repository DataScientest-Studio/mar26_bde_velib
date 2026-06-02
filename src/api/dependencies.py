from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.api.core.security import (
    decode_access_token,
    TokenExpiredError,
    TokenInvalidError,
)
from src.api.services.user_service import get_user
from src.api.schemas.auth import User
from fastapi import Request

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = decode_access_token(token)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée, veuillez vous reconnecter",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload.get("sub")
    user = get_user(username) if username else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable",
        )
    return user


def get_predictor(request: Request):
    """Retourne le prédicteur (vrai ou fake) chargé au démarrage."""
    return request.app.state.predictor
