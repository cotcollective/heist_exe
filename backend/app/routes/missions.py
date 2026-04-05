from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db import get_db
from app.models import Mission, PlayerSession, Waypoint
from app.schemas import PlayerAuth, TokenOut, MissionOut
from app.auth import verify_secret, create_player_token, get_current_player

router = APIRouter()


@router.post("/auth", response_model=TokenOut)
async def player_auth(payload: PlayerAuth, db: AsyncSession = Depends(get_db)):
    """Le joueur entre le PIN pour accéder à une mission active."""
    mission = await db.get(Mission, payload.mission_id)
    if not mission or not mission.is_active:
        raise HTTPException(status_code=404, detail="Mission introuvable ou inactive")

    if not verify_secret(payload.pin, mission.pin_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="PIN incorrect")

    # Créer une session joueur
    session = PlayerSession(
        mission_id=mission.id,
        player_name=payload.player_name,
        token_jti="pending",
    )
    db.add(session)
    await db.flush()

    token, jti = create_player_token(mission.id, payload.player_name, session.id)
    session.token_jti = jti
    await db.commit()

    # Reload avec eager loading
    result = await db.execute(
        select(Mission)
        .where(Mission.id == mission.id)
        .options(selectinload(Mission.waypoints).selectinload(Waypoint.enigma))
    )
    loaded_mission = result.scalar_one()
    return TokenOut(access_token=token, mission=loaded_mission)


@router.get("/active", response_model=list[MissionOut])
async def list_active_missions(db: AsyncSession = Depends(get_db)):
    """Liste les missions actives (pour l'écran de Boot)."""
    result = await db.execute(
        select(Mission)
        .where(Mission.is_active == True)
        .options(selectinload(Mission.waypoints).selectinload(Waypoint.enigma))
        .order_by(Mission.created_at.desc())
    )
    return result.scalars().all()


@router.get("/me", response_model=MissionOut)
async def get_my_mission(
    player: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Mission)
        .where(Mission.id == player["mission_id"])
        .options(selectinload(Mission.waypoints).selectinload(Waypoint.enigma))
    )
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission introuvable")
    return mission
