from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from app.db import get_db
from app.models import Waypoint, PlayerSession, Mission, Enigma
from app.schemas import WaypointOut, ProgressOut, EnigmaAnswer
from app.auth import get_current_player, verify_answer

router = APIRouter()


@router.get("/current", response_model=WaypointOut)
async def get_current_waypoint(
    player: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """Retourne le waypoint actif du joueur."""
    session = await db.get(PlayerSession, player["session_id"])
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")

    result = await db.execute(
        select(Waypoint)
        .where(Waypoint.mission_id == player["mission_id"])
        .where(Waypoint.order == session.current_waypoint)
        .options(selectinload(Waypoint.enigma))
    )
    waypoint = result.scalar_one_or_none()
    if not waypoint:
        raise HTTPException(status_code=404, detail="Waypoint introuvable")
    return waypoint


@router.post("/answer", response_model=ProgressOut)
async def submit_answer(
    payload: EnigmaAnswer,
    player: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """Valide la réponse d'une énigme et avance la progression."""
    waypoint = await db.get(Waypoint, payload.waypoint_id)
    if not waypoint or not waypoint.enigma:
        raise HTTPException(status_code=404, detail="Énigme introuvable")

    correct = verify_answer(payload.answer, waypoint.enigma.answer_hash)

    if not correct:
        return ProgressOut(waypoint_id=payload.waypoint_id, correct=False)

    session = await db.get(PlayerSession, player["session_id"])
    mission = await db.get(Mission, player["mission_id"])

    next_order = session.current_waypoint + 1
    result = await db.execute(
        select(Waypoint)
        .where(Waypoint.mission_id == player["mission_id"])
        .where(Waypoint.order == next_order)
    )
    next_wp = result.scalar_one_or_none()
    mission_complete = next_wp is None

    session.current_waypoint = next_order
    if mission_complete:
        session.completed_at = datetime.now(timezone.utc)

    await db.commit()

    return ProgressOut(
        waypoint_id=payload.waypoint_id,
        correct=True,
        next_waypoint=next_wp,
        mission_complete=mission_complete,
    )
