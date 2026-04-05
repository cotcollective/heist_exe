from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models import Mission
from app.auth import require_admin
import aiofiles, os, uuid

router = APIRouter(dependencies=[Depends(require_admin)])

ALLOWED_TYPES = {"audio/mpeg", "audio/ogg", "audio/wav", "audio/mp4"}
MAX_SIZE_MB = 20
MEDIA_PATH = os.getenv("MEDIA_PATH", "/app/media")


@router.post("/audio/{mission_id}")
async def upload_audio(
    mission_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Type non supporté: {file.content_type}")

    content = await file.read()
    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Fichier trop gros (max {MAX_SIZE_MB}MB)")

    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission introuvable")

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "mp3"
    filename = f"mission_{mission_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(MEDIA_PATH, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    mission.audio_file = filename
    await db.commit()

    return {"filename": filename, "url": f"/media/{filename}"}
