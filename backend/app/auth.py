from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os, secrets, uuid

ALGORITHM = "HS256"

# Clé JWT éphémère : si SECRET_KEY n'est pas fournie, on en génère une au
# démarrage. Les jetons ne survivent alors pas à un redémarrage, mais
# personne ne peut en forger — infiniment préférable à une clé de signature
# par défaut, connue de quiconque lit le dépôt.
_EPHEMERAL_SECRET = secrets.token_urlsafe(48)

# Valeurs de démonstration à refuser : les accepter revient à publier le
# panneau d'administration.
_WEAK_ADMIN_KEYS = {
    "admin-secret-key", "changeme", "change-me", "secret",
    "admin", "password", "heist", "test",
}


def get_secret_key() -> str:
    """Lue à l'appel, pas à l'import — rotation possible sans redémarrage."""
    value = os.getenv("SECRET_KEY")
    if not value or len(value) < 32:
        return _EPHEMERAL_SECRET
    return value


def get_admin_key() -> str | None:
    """Lue à l'appel. None si non configurée : on refuse alors l'accès."""
    return os.getenv("ADMIN_KEY") or None


def admin_key_problem() -> str | None:
    """Raison de refuser l'admin, ou None si la configuration est utilisable."""
    key = get_admin_key()
    if not key:
        return "ADMIN_KEY non configurée — définis-la dans .env"
    if key.lower() in _WEAK_ADMIN_KEYS:
        return "ADMIN_KEY utilise une valeur de démonstration publique"
    if len(key) < 8:
        return "ADMIN_KEY trop courte (8 caractères minimum)"
    return None


ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "12"))

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
    token = jwt.encode(payload, get_secret_key(), algorithm=ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
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
    """Vérifie la clé admin, relue à chaque requête.

    503 si la configuration est inutilisable (absente, valeur de démo, trop
    courte) : on préfère un refus explicite à un panneau ouvert avec une clé
    devinable. 403 si la clé fournie est fausse. Comparaison à temps constant.
    """
    key = get_admin_key()
    problem = admin_key_problem()
    if problem or key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Administration indisponible : {problem or 'ADMIN_KEY absente'}",
        )
    if not secrets.compare_digest(credentials.credentials, key):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")
