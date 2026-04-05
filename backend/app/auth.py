from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os, uuid

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-prod-minimum-32-chars")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "12"))
ADMIN_KEY = os.getenv("ADMIN_KEY", "admin-secret-key")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


# ── Hashing ───────────────────────────────────────────────────────────────────

def hash_secret(value: str) -> str:
    return pwd_context.hash(value)

def verify_secret(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_answer(answer: str) -> str:
    """Normalise + hash la réponse d'énigme."""
    return pwd_context.hash(answer.strip().lower())

def verify_answer(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain.strip().lower(), hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_player_token(mission_id: int, player_name: str, session_id: int) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    payload = {
        "sub": player_name,
        "mission_id": mission_id,
        "session_id": session_id,
        "jti": jti,
        "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expiré")


# ── Dependencies ──────────────────────────────────────────────────────────────

async def get_current_player(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    return decode_token(credentials.credentials)


async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> None:
    if credentials.credentials != ADMIN_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")
