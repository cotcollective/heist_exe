"""Comptes et parties — séparés des mécaniques de mission.

Le principe tient en trois phrases :

  1. Une partie peut exister sans compte. On ouvre le jeu, on choisit, ça
     démarre ; un jeton est généré à la volée et vit dans le navigateur.
  2. Le compte est un CONTENEUR de parties, pas une condition d'entrée. Il
     naît au premier point de contrôle, et il en porte autant qu'on veut.
  3. Les missions ignorent les comptes. Ce fichier ne touche jamais aux
     tables missions/waypoints — c'est ce qui garde les deux mécaniques
     étanches.

Les jetons sont hachés en base. Ils ne sont affichés qu'une fois, à la
création, et jamais redonnés : ce n'est pas une récupération de mot de passe,
c'est une capacité.
"""

import hashlib
import json
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Account, Party
from app.schemas import (
    AccountCreateIn,
    AccountOut,
    PartyAttachIn,
    PartyCheckpointIn,
    PartyCreateIn,
    PartyOut,
)

router = APIRouter()


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _new_token() -> str:
    return secrets.token_urlsafe(32)


def _party_out(p: Party) -> PartyOut:
    try:
        state = json.loads(p.state_json or "{}")
    except json.JSONDecodeError:
        state = {}
    return PartyOut(
        id=p.id,
        kind=p.kind,
        ref_id=p.ref_id,
        title=p.title,
        state=state,
        account_id=p.account_id,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


# ── Authentification par capacité ────────────────────────────────────────────
# Le jeton voyage dans un en-tête, pas dans l'URL : une URL finit dans les
# journaux et dans l'historique du navigateur.


async def require_party(
    party_id: int,
    db: AsyncSession = Depends(get_db),
    x_party_token: str | None = Header(default=None, alias="X-Party-Token"),
) -> Party:
    if not x_party_token:
        raise HTTPException(401, "Jeton de partie manquant")
    party = await db.get(Party, party_id)
    # Message identique pour « inexistante » et « mauvais jeton » : ne pas
    # confirmer l'existence d'une partie à qui n'a pas le jeton.
    if party is None or not secrets.compare_digest(party.token_hash, _hash(x_party_token)):
        raise HTTPException(403, "Partie introuvable ou jeton invalide")
    return party


async def require_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    x_account_token: str | None = Header(default=None, alias="X-Account-Token"),
) -> Account:
    if not x_account_token:
        raise HTTPException(401, "Jeton de compte manquant")
    acc = await db.get(Account, account_id)
    if acc is None or not secrets.compare_digest(acc.token_hash, _hash(x_account_token)):
        raise HTTPException(403, "Compte introuvable ou jeton invalide")
    return acc


# ── Parties ──────────────────────────────────────────────────────────────────


@router.post("/parties", response_model=dict, status_code=201)
async def create_party(payload: PartyCreateIn, db: AsyncSession = Depends(get_db)):
    """Crée une partie anonyme. Aucun compte, aucun email, aucun formulaire.

    Le jeton brut n'est renvoyé qu'ici. Le serveur n'en garde que le hash.
    """
    if payload.kind not in ("mission", "cache"):
        raise HTTPException(422, "kind doit valoir 'mission' ou 'cache'")

    token = _new_token()
    party = Party(
        kind=payload.kind,
        ref_id=payload.ref_id,
        title=payload.title,
        token_hash=_hash(token),
        state_json=json.dumps(payload.state or {}),
    )
    db.add(party)
    await db.commit()
    await db.refresh(party)
    return {"party": _party_out(party).model_dump(mode="json"), "token": token}


@router.get("/parties/{party_id}", response_model=PartyOut)
async def get_party(party: Party = Depends(require_party)):
    """Reprise : le navigateur revient avec son jeton et retrouve l'état."""
    return _party_out(party)


@router.patch("/parties/{party_id}", response_model=PartyOut)
async def checkpoint(
    payload: PartyCheckpointIn,
    party: Party = Depends(require_party),
    db: AsyncSession = Depends(get_db),
):
    """Point de contrôle.

    `state` remplace l'état ; `merge` le fusionne. Le merge existe parce que
    deux onglets peuvent sauvegarder en parallèle — écraser serait perdre
    l'avancement de l'autre.
    """
    # Un titre seul est un point de contrôle valide : on ne connaît souvent
    # le nom de la partie qu'une fois dedans.
    if payload.state is None and payload.merge is None and payload.title is None:
        raise HTTPException(422, "Fournir 'state', 'merge' ou 'title'")

    current = json.loads(party.state_json or "{}")

    if payload.merge:
        current.update(payload.merge)
    elif payload.state is not None:
        current = payload.state

    party.state_json = json.dumps(current)
    party.updated_at = datetime.now(timezone.utc)
    if payload.title is not None:
        party.title = payload.title
    await db.commit()
    await db.refresh(party)
    return _party_out(party)


@router.delete("/parties/{party_id}", status_code=204)
async def delete_party(party: Party = Depends(require_party), db: AsyncSession = Depends(get_db)):
    await db.delete(party)
    await db.commit()


# ── Comptes ──────────────────────────────────────────────────────────────────


@router.post("/accounts", response_model=dict, status_code=201)
async def create_account(payload: AccountCreateIn, db: AsyncSession = Depends(get_db)):
    """Crée un conteneur. L'email est une étiquette, pas une preuve.

    On n'envoie aucun courrier et on ne prétend donc rien vérifier. L'email
    ne sert jamais à retrouver une partie à lui seul : le jeton authentifie.
    """
    email = payload.email.strip()
    if "@" not in email or len(email) > 200:
        raise HTTPException(422, "Adresse invalide")

    token = _new_token()
    acc = Account(email=email, label=payload.label, token_hash=_hash(token))
    db.add(acc)
    await db.commit()
    await db.refresh(acc)
    return {"account": AccountOut.model_validate(acc).model_dump(mode="json"), "token": token}


@router.get("/accounts/{account_id}/parties", response_model=list[PartyOut])
async def list_parties(acc: Account = Depends(require_account)):
    """Les parties du conteneur. Plusieurs par compte, sans hiérarchie."""
    return [_party_out(p) for p in sorted(acc.parties, key=lambda x: x.updated_at, reverse=True)]


@router.post("/accounts/{account_id}/parties", response_model=PartyOut)
async def attach_party(
    account_id: int,
    payload: PartyAttachIn,
    acc: Account = Depends(require_account),
    db: AsyncSession = Depends(get_db),
):
    """Rattache une partie existante au compte.

    Il faut les DEUX jetons : celui du compte (en-tête) et celui de la partie
    (corps). Sinon posséder un compte suffirait à voler la partie de
    quelqu'un d'autre en devinant son identifiant.
    """
    party = await db.get(Party, payload.party_id)
    if party is None or not secrets.compare_digest(party.token_hash, _hash(payload.party_token)):
        raise HTTPException(403, "Partie introuvable ou jeton invalide")

    party.account_id = acc.id
    party.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(party)
    return _party_out(party)


@router.delete("/accounts/{account_id}/parties/{party_id}", response_model=PartyOut)
async def detach_party(
    party_id: int,
    acc: Account = Depends(require_account),
    db: AsyncSession = Depends(get_db),
):
    """Détache sans supprimer : la partie redevient locale, elle survit."""
    party = await db.get(Party, party_id)
    if party is None or party.account_id != acc.id:
        raise HTTPException(404, "Cette partie n'est pas dans ce compte")
    party.account_id = None
    party.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(party)
    return _party_out(party)
