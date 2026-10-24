"""Monde — caches hors mission (le pendant « chasse au trésor » de HEIST.EXE).

Une mission est une SÉQUENCE ordonnée de waypoints (progression exclusive).
Une cache du monde est un waypoint ORPHELIN (mission_id = NULL) et public,
réclamable indépendamment par plusieurs joueurs.

Même table, même géométrie (lat/lng/radius), même preuve (qr_code).
Seul le régime de réclamation change — cf. Waypoint.claim_mode.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db import get_db
from app.models import Waypoint, WaypointClaim, Agent
from app.schemas import (
    CachePlant, CacheOut, ClaimIn, ClaimOut, PublishOut,
    PublishBatchIn, PublishBatchOut, PublishResult,
    AgentRegisterIn, AgentOut,
)
from app.auth import require_admin
from app.agentkeys import (
    verify_claim_signature, valid_public_jwk, jwk_fingerprint,
    SIGNATURE_WINDOW_SECONDS,
)
import time

router = APIRouter()


async def _claim_count(db: AsyncSession, waypoint_id: int) -> int:
    r = await db.execute(
        select(func.count())
        .select_from(WaypointClaim)
        .where(WaypointClaim.waypoint_id == waypoint_id)
    )
    return int(r.scalar_one())


def _to_out(wp: Waypoint, claim_count: int) -> CacheOut:
    return CacheOut(
        id=wp.id,
        title=wp.title,
        hint=wp.hint,
        lat=wp.lat,
        lng=wp.lng,
        radius_meters=wp.radius_meters,
        claim_mode=wp.claim_mode,
        owner_label=wp.owner_label,
        requires_proof=bool(wp.qr_code),
        claim_count=claim_count,
    )


async def _find_by_origin(db: AsyncSession, mission_id, waypoint_id):
    """Retrouve une cache déjà versée, via sa clé d'idempotence."""
    if mission_id is None or waypoint_id is None:
        return None
    r = await db.execute(
        select(Waypoint)
        .where(Waypoint.origin_mission_id == mission_id)
        .where(Waypoint.origin_waypoint_id == waypoint_id)
    )
    return r.scalar_one_or_none()


@router.get("/caches", response_model=list[CacheOut])
async def list_caches(
    lat_min: Optional[float] = Query(None),
    lat_max: Optional[float] = Query(None),
    lng_min: Optional[float] = Query(None),
    lng_max: Optional[float] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Catalogue des caches publiques, filtrable par bbox.

    Ne renvoie jamais qr_code : on expose `requires_proof`, pas la preuve.
    """
    stmt = select(Waypoint).where(Waypoint.is_public.is_(True))
    if lat_min is not None:
        stmt = stmt.where(Waypoint.lat >= lat_min)
    if lat_max is not None:
        stmt = stmt.where(Waypoint.lat <= lat_max)
    if lng_min is not None:
        stmt = stmt.where(Waypoint.lng >= lng_min)
    if lng_max is not None:
        stmt = stmt.where(Waypoint.lng <= lng_max)
    stmt = stmt.order_by(Waypoint.id).limit(limit)

    result = await db.execute(stmt)
    out = []
    for wp in result.scalars().all():
        out.append(_to_out(wp, await _claim_count(db, wp.id)))
    return out


@router.get("/caches/{waypoint_id}", response_model=CacheOut)
async def get_cache(waypoint_id: int, db: AsyncSession = Depends(get_db)):
    wp = await db.get(Waypoint, waypoint_id)
    if not wp or not wp.is_public:
        raise HTTPException(status_code=404, detail="Cache introuvable")
    return _to_out(wp, await _claim_count(db, wp.id))


@router.post("/caches", response_model=CacheOut, status_code=201,
             dependencies=[Depends(require_admin)])
async def plant_cache(payload: CachePlant, db: AsyncSession = Depends(get_db)):
    """Plante une cache orpheline et publique (admin)."""
    wp = Waypoint(
        mission_id=None,
        order=0,
        title=payload.title,
        hint=payload.hint,
        lat=payload.lat,
        lng=payload.lng,
        radius_meters=payload.radius_meters,
        qr_code=payload.qr_code,
        is_public=True,
        claim_mode="find",
        owner_label=payload.owner_label,
    )
    db.add(wp)
    await db.flush()
    await db.commit()
    await db.refresh(wp)
    return _to_out(wp, 0)


@router.post("/publish", response_model=PublishBatchOut,
             dependencies=[Depends(require_admin)])
async def publish_batch(payload: PublishBatchIn, db: AsyncSession = Depends(get_db)):
    """Verse des caches au monde, de façon IDEMPOTENTE.

    Le versement COPIE, il ne déplace pas. Le waypoint d'origine reste dans
    sa mission, intact : une mission en cours ne doit pas se retrouver
    amputée parce qu'on a versé ses caches au monde. La copie publique et le
    waypoint de mission sont deux objets distincts, avec deux régimes de
    réclamation différents — c'est exactement ce qu'on veut.

    Deux chemins, un seul endpoint :
      - `waypoint_id` connu du serveur → copie depuis le waypoint.
      - `waypoint_id` inconnu ou absent → cache créée depuis le payload
        (mission jouée hors ligne, synchronisée plus tard).

    La clé d'idempotence est (origin_mission_id, origin_waypoint_id).
    Rejouer le même lot renvoie les caches existantes avec created=False
    au lieu d'en créer des doublons — indispensable pour une file de
    retry côté client.
    """
    results: list[PublishResult] = []

    for item in payload.items:
        existing = await _find_by_origin(db, item.mission_id, item.waypoint_id)
        if existing:
            results.append(PublishResult(
                cache_id=existing.id,
                origin_mission_id=existing.origin_mission_id,
                origin_waypoint_id=existing.origin_waypoint_id,
                created=False,
                title=existing.title,
            ))
            continue

        server_wp = await db.get(Waypoint, item.waypoint_id) if item.waypoint_id else None

        wp = Waypoint(
            mission_id=None,
            order=0,
            title=item.title or (server_wp.title if server_wp else ""),
            hint=item.hint if item.hint is not None else (server_wp.hint if server_wp else None),
            lat=item.lat,
            lng=item.lng,
            radius_meters=item.radius_meters,
            qr_code=item.qr_code if item.qr_code is not None else (
                server_wp.qr_code if server_wp else None),
            is_public=True,
            claim_mode="find",
            owner_label=item.owner_label,
            origin_mission_id=item.mission_id,
            origin_waypoint_id=item.waypoint_id,
        )
        db.add(wp)
        try:
            await db.commit()
        except IntegrityError:
            # Course perdue : un autre appel a versé la même cache.
            await db.rollback()
            existing = await _find_by_origin(db, item.mission_id, item.waypoint_id)
            if existing is None:
                raise HTTPException(409, "Conflit de versement")
            results.append(PublishResult(
                cache_id=existing.id,
                origin_mission_id=existing.origin_mission_id,
                origin_waypoint_id=existing.origin_waypoint_id,
                created=False, title=existing.title,
            ))
            continue

        await db.refresh(wp)
        results.append(PublishResult(
            cache_id=wp.id,
            origin_mission_id=wp.origin_mission_id,
            origin_waypoint_id=wp.origin_waypoint_id,
            created=True,
            title=wp.title,
        ))

    created = sum(1 for r in results if r.created)
    return PublishBatchOut(
        published=results,
        created_count=created,
        existing_count=len(results) - created,
    )


@router.post("/agents", response_model=AgentOut)
async def register_agent(payload: AgentRegisterIn, db: AsyncSession = Depends(get_db)):
    """Enregistre la clé publique d'un appareil sous un nom d'agent.

    Premier arrivé, premier servi : un nom déjà pris avec une autre clé
    renvoie 409. C'est ce qui empêche quelqu'un de réclamer une identité
    existante — et c'est suffisant pour un jeu de quartier, où le nom n'a
    pas de valeur monétaire.
    """
    name = payload.player_name.strip()
    if not name:
        raise HTTPException(400, "Nom d'agent requis")
    if not valid_public_jwk(payload.public_jwk):
        raise HTTPException(400, "Clé publique invalide (ECDSA P-256 attendue)")

    existing = await db.execute(select(Agent).where(Agent.player_name == name))
    agent = existing.scalar_one_or_none()

    if agent:
        same = jwk_fingerprint({
            "x": agent.public_x, "y": agent.public_y,
        }) == jwk_fingerprint(payload.public_jwk)
        if not same:
            raise HTTPException(409, "Ce nom d'agent est déjà associé à une autre clé")
        return AgentOut(player_name=agent.player_name, created_at=agent.created_at)

    agent = Agent(
        player_name=name,
        public_x=payload.public_jwk["x"],
        public_y=payload.public_jwk["y"],
    )
    db.add(agent)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Ce nom d'agent vient d'être pris")
    await db.refresh(agent)
    return AgentOut(player_name=agent.player_name, created_at=agent.created_at)


@router.get("/agents/{player_name}", response_model=AgentOut)
async def get_agent(player_name: str, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Agent).where(Agent.player_name == player_name.strip()))
    agent = r.scalar_one_or_none()
    if not agent:
        raise HTTPException(404, "Agent inconnu")
    return AgentOut(player_name=agent.player_name, created_at=agent.created_at)


@router.post("/caches/{waypoint_id}/claim", response_model=ClaimOut)
async def claim_cache(waypoint_id: int, payload: ClaimIn,
                      db: AsyncSession = Depends(get_db)):
    """Réclame une cache. Le régime est porté par la cache, pas par l'appelant.

    La réclamation est signée par la clé d'appareil de l'agent : sans elle,
    n'importe qui pourrait réclamer au nom de n'importe qui dès que le
    service est exposé publiquement.
    """
    wp = await db.get(Waypoint, waypoint_id)
    if not wp or not wp.is_public:
        raise HTTPException(status_code=404, detail="Cache introuvable")

    name = payload.player_name.strip()
    r = await db.execute(select(Agent).where(Agent.player_name == name))
    agent = r.scalar_one_or_none()
    if agent is None:
        raise HTTPException(
            status_code=403,
            detail="Agent non enregistré — enregistre ta clé d'appareil d'abord",
        )

    if not payload.signature or payload.ts is None:
        raise HTTPException(status_code=401, detail="Signature de réclamation manquante")
    if abs(time.time() - payload.ts) > SIGNATURE_WINDOW_SECONDS:
        raise HTTPException(status_code=401, detail="Signature expirée")

    if not verify_claim_signature(
        {"kty": "EC", "crv": "P-256", "x": agent.public_x, "y": agent.public_y},
        waypoint_id, name, payload.ts, payload.signature,
    ):
        raise HTTPException(status_code=403, detail="Signature invalide")

    existing = await db.execute(
        select(WaypointClaim)
        .where(WaypointClaim.waypoint_id == waypoint_id)
        .where(WaypointClaim.player_name == name)
    )
    if existing.scalar_one_or_none():
        return ClaimOut(
            waypoint_id=waypoint_id,
            claimed=False,
            already_claimed=True,
            claim_count=await _claim_count(db, waypoint_id),
            reason="déjà réclamée par ce joueur",
        )

    proven = False
    if wp.qr_code:
        if not payload.proof:
            raise HTTPException(status_code=400,
                                detail="Cette cache exige une preuve (scan du QR)")
        if payload.proof.strip() != wp.qr_code.strip():
            raise HTTPException(status_code=403, detail="Preuve invalide")
        proven = True

    db.add(WaypointClaim(
        waypoint_id=waypoint_id,
        player_name=name,
        mode=wp.claim_mode,
        proof=payload.proof,
        proven=proven,
    ))
    await db.commit()

    return ClaimOut(
        waypoint_id=waypoint_id,
        claimed=True,
        already_claimed=False,
        proven=proven,
        claim_count=await _claim_count(db, waypoint_id),
    )
