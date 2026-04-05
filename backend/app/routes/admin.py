from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db import get_db
from app.models import Mission, Waypoint, Enigma
from app.schemas import MissionCreate, MissionOut
from app.auth import require_admin, hash_secret, hash_answer

router = APIRouter(dependencies=[Depends(require_admin)])


@router.post("/missions", response_model=MissionOut, status_code=status.HTTP_201_CREATED)
async def create_mission(payload: MissionCreate, db: AsyncSession = Depends(get_db)):
    mission = Mission(
        title=payload.title,
        lore=payload.lore,
        pin_hash=hash_secret(payload.pin),
        duration_minutes=payload.duration_minutes,
        reward_text=payload.reward_text,
    )
    db.add(mission)
    await db.flush()  # get mission.id

    for wp_data in payload.waypoints:
        wp = Waypoint(
            mission_id=mission.id,
            order=wp_data.order,
            title=wp_data.title,
            hint=wp_data.hint,
            lat=wp_data.lat,
            lng=wp_data.lng,
            radius_meters=wp_data.radius_meters,
            qr_code=wp_data.qr_code,
        )
        db.add(wp)
        await db.flush()

        if wp_data.enigma:
            enigma = Enigma(
                waypoint_id=wp.id,
                question=wp_data.enigma.question,
                answer_hash=hash_answer(wp_data.enigma.answer),
                hint=wp_data.enigma.hint,
            )
            db.add(enigma)

    await db.commit()
    # Reload avec eager loading pour éviter MissingGreenlet en async
    result = await db.execute(
        select(Mission)
        .where(Mission.id == mission.id)
        .options(selectinload(Mission.waypoints).selectinload(Waypoint.enigma))
    )
    return result.scalar_one()


@router.get("/missions", response_model=list[MissionOut])
async def list_missions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Mission)
        .options(selectinload(Mission.waypoints).selectinload(Waypoint.enigma))
        .order_by(Mission.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/missions/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mission(mission_id: int, db: AsyncSession = Depends(get_db)):
    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission introuvable")
    await db.delete(mission)
