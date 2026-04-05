from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models import Enigma
from app.schemas import EnigmaOut
from app.auth import get_current_player

router = APIRouter()


@router.get("/{enigma_id}", response_model=EnigmaOut)
async def get_enigma(
    enigma_id: int,
    player: dict = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    enigma = await db.get(Enigma, enigma_id)
    if not enigma:
        raise HTTPException(status_code=404, detail="Énigme introuvable")
    # Ne jamais retourner le hash de la réponse
    return enigma
