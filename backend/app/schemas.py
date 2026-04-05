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
    order: int
    title: str
    hint: Optional[str] = None
    lat: float
    lng: float
    radius_meters: int = 30
    qr_code: Optional[str] = None
    enigma: Optional[EnigmaCreate] = None


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
