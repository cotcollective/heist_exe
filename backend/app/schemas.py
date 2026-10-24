from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


# ── Enigma ──────────────────────────────────────────────────────────────────

class EnigmaCreate(BaseModel):
    question: str
    answer: str          # plain text → hashé dans le service
    hint: Optional[str] = None


class EnigmaOut(BaseModel):
    id: int
    waypoint_id: int
    question: str
    hint: Optional[str]
    model_config = {"from_attributes": True}


# ── Waypoint ─────────────────────────────────────────────────────────────────

class WaypointCreate(BaseModel):
    order: int = 0
    title: str
    hint: Optional[str] = None
    lat: float
    lng: float
    radius_meters: int = 30
    qr_code: Optional[str] = None
    enigma: Optional[EnigmaCreate] = None
    # ── Monde ──
    is_public: bool = False
    claim_mode: str = "progress"        # "progress" | "find"
    owner_label: Optional[str] = None


class WaypointOut(BaseModel):
    id: int
    order: int
    title: str
    hint: Optional[str]
    lat: float
    lng: float
    radius_meters: int
    qr_code: Optional[str]
    enigma: Optional[EnigmaOut]
    is_public: bool = False
    claim_mode: str = "progress"
    owner_label: Optional[str] = None
    model_config = {"from_attributes": True}


# ── Mission ───────────────────────────────────────────────────────────────────

class MissionCreate(BaseModel):
    title: str
    lore: Optional[str] = None
    pin: str
    duration_minutes: int = 45
    reward_text: Optional[str] = None
    waypoints: list[WaypointCreate] = []

    @field_validator("pin")
    @classmethod
    def pin_not_empty(cls, v: str) -> str:
        if len(v.strip()) < 4:
            raise ValueError("PIN doit avoir au moins 4 caractères")
        return v


class MissionOut(BaseModel):
    id: int
    title: str
    lore: Optional[str]
    duration_minutes: int
    is_active: bool
    created_at: datetime
    audio_file: Optional[str]
    reward_text: Optional[str]
    waypoints: list[WaypointOut] = []
    model_config = {"from_attributes": True}


# ── Auth ──────────────────────────────────────────────────────────────────────

class PlayerAuth(BaseModel):
    mission_id: int
    pin: str
    player_name: str = "Agent"


class TokenOut(BaseModel):
    access_token: str
    mission: MissionOut


# ── Game progress ─────────────────────────────────────────────────────────────

class EnigmaAnswer(BaseModel):
    waypoint_id: int
    answer: str


class ProgressOut(BaseModel):
    waypoint_id: int
    correct: bool
    next_waypoint: Optional[WaypointOut] = None
    mission_complete: bool = False


# ── Monde (caches hors mission) ───────────────────────────────────────────────

class CachePlant(BaseModel):
    title: str
    lat: float
    lng: float
    # Défaut plus large qu'un waypoint de mission : le rayon marque
    # la ZONE DE RECHERCHE, pas la tolérance d'arrivée.
    radius_meters: int = 120
    hint: Optional[str] = None
    qr_code: Optional[str] = None
    owner_label: Optional[str] = None


class CacheOut(BaseModel):
    """Vue publique d'une cache. Ne contient jamais qr_code."""
    id: int
    title: str
    hint: Optional[str] = None
    lat: float
    lng: float
    radius_meters: int
    claim_mode: str
    owner_label: Optional[str] = None
    requires_proof: bool = False
    claim_count: int = 0


class ClaimIn(BaseModel):
    player_name: str
    proof: Optional[str] = None
    # Signature ECDSA P-256 de « waypoint_id|player_name|ts », base64url.
    signature: Optional[str] = None
    ts: Optional[int] = None


class AgentRegisterIn(BaseModel):
    player_name: str
    public_jwk: dict


class AgentOut(BaseModel):
    player_name: str
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class ClaimOut(BaseModel):
    waypoint_id: int
    claimed: bool
    already_claimed: bool = False
    proven: bool = False
    claim_count: int = 0
    reason: Optional[str] = None


class PublishOut(BaseModel):
    waypoint_id: int
    mission_id: Optional[int] = None
    is_public: bool
    claim_mode: str


# ── Versement idempotent au monde ────────────────────────────────────────────

class PublishItem(BaseModel):
    """Une cache à verser au monde.

    `waypoint_id` est optionnel : s'il est fourni, le waypoint existant est
    détaché de sa mission. Sinon la cache est créée à partir du payload —
    c'est le chemin des missions jouées hors ligne puis synchronisées.
    """
    mission_id: Optional[int] = None
    waypoint_id: Optional[int] = None
    title: str
    lat: float
    lng: float
    radius_meters: int = 120
    hint: Optional[str] = None
    qr_code: Optional[str] = None
    owner_label: Optional[str] = None


class PublishBatchIn(BaseModel):
    items: list[PublishItem]


class PublishResult(BaseModel):
    cache_id: int
    origin_mission_id: Optional[int] = None
    origin_waypoint_id: Optional[int] = None
    created: bool          # False = déjà versée, renvoyée telle quelle
    title: str


class PublishBatchOut(BaseModel):
    published: list[PublishResult]
    created_count: int
    existing_count: int

# ── Comptes et parties ──────────────────────────────────────────────────────
# Une partie peut vivre sans compte. Le compte n'apparaît qu'au point de
# contrôle et contient autant de parties qu'on veut : l'email est une
# étiquette, pas une identité, et il n'est jamais vérifié.

class PartyCreateIn(BaseModel):
    kind: str = "mission"            # "mission" | "cache"
    ref_id: Optional[int] = None     # missions.id quand kind == "mission"
    title: Optional[str] = None
    state: Optional[dict] = None


class PartyCheckpointIn(BaseModel):
    state: Optional[dict] = None     # remplace l'état
    merge: Optional[dict] = None     # fusionne (deux onglets en parallèle)
    title: Optional[str] = None


class PartyOut(BaseModel):
    id: int
    kind: str
    ref_id: Optional[int]
    title: Optional[str]
    state: dict
    account_id: Optional[int]
    created_at: datetime
    updated_at: datetime


class AccountCreateIn(BaseModel):
    email: str
    label: Optional[str] = None


class AccountOut(BaseModel):
    id: int
    email: str
    label: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class PartyAttachIn(BaseModel):
    party_id: int
    party_token: str
