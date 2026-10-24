from sqlalchemy import String, Integer, Float, Boolean, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from app.db import Base


class Mission(Base):
    __tablename__ = "missions"

    id:               Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    title:            Mapped[str]           = mapped_column(String(200))
    lore:             Mapped[str | None]    = mapped_column(Text)
    pin_hash:         Mapped[str]           = mapped_column(String(200))
    duration_minutes: Mapped[int]           = mapped_column(Integer, default=45)
    is_active:        Mapped[bool]          = mapped_column(Boolean, default=True)
    created_at:       Mapped[datetime]      = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    audio_file:       Mapped[str | None]    = mapped_column(String(300))
    reward_text:      Mapped[str | None]    = mapped_column(Text)

    waypoints: Mapped[list["Waypoint"]] = relationship(
        back_populates="mission",
        cascade="all, delete-orphan",
        order_by="Waypoint.order",
        lazy="selectin",
    )
    sessions: Mapped[list["PlayerSession"]] = relationship(
        back_populates="mission",
        cascade="all, delete-orphan",
    )


class Waypoint(Base):
    __tablename__ = "waypoints"
    __table_args__ = (
        # Idempotence du versement au monde : une même cache d'origine
        # ne peut être publiée qu'une fois, même si le client retente
        # après une coupure réseau ou un rejeu depuis un avion.
        UniqueConstraint("origin_mission_id", "origin_waypoint_id", name="uq_origin_pair"),
    )

    id:             Mapped[int]         = mapped_column(Integer, primary_key=True, index=True)
    # NULLABLE : un waypoint peut vivre hors mission (cache du monde).
    mission_id:     Mapped[int | None]  = mapped_column(ForeignKey("missions.id"), index=True, nullable=True)
    order:          Mapped[int]         = mapped_column(Integer, default=0)
    title:          Mapped[str]         = mapped_column(String(200))
    hint:           Mapped[str | None]  = mapped_column(Text)
    lat:            Mapped[float]       = mapped_column(Float)
    lng:            Mapped[float]       = mapped_column(Float)
    radius_meters:  Mapped[int]         = mapped_column(Integer, default=30)
    qr_code:        Mapped[str | None]  = mapped_column(String(100))

    # ── Monde ────────────────────────────────────────────────────────────────
    # is_public  : apparaît dans le catalogue du monde (trouvable par tous)
    # claim_mode : "progress" (avance une mission, exclusif par joueur, par mission)
    #              "find"     (trouvaille permanente, N joueurs peuvent réclamer)
    # owner_label: qui a planté la cache (libre, pas un compte)
    is_public:      Mapped[bool]        = mapped_column(Boolean, default=False, index=True)
    claim_mode:     Mapped[str]         = mapped_column(String(16), default="progress")
    owner_label:    Mapped[str | None]  = mapped_column(String(100))

    # Provenance pour l'idempotence du versement au monde.
    origin_mission_id:  Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    origin_waypoint_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    mission: Mapped["Mission | None"]   = relationship(back_populates="waypoints")
    claims:  Mapped[list["WaypointClaim"]] = relationship(
        back_populates="waypoint",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    enigma:  Mapped["Enigma | None"]    = relationship(
        back_populates="waypoint",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Enigma(Base):
    __tablename__ = "enigmas"

    id:           Mapped[int]         = mapped_column(Integer, primary_key=True, index=True)
    waypoint_id:  Mapped[int]         = mapped_column(ForeignKey("waypoints.id"), unique=True)
    question:     Mapped[str]         = mapped_column(Text)
    answer_hash:  Mapped[str]         = mapped_column(String(200))  # bcrypt
    hint:         Mapped[str | None]  = mapped_column(Text)

    waypoint: Mapped["Waypoint"] = relationship(back_populates="enigma")


class Agent(Base):
    """Identité d'appareil : un nom + une clé publique ECDSA.

    Pas de compte, pas de mot de passe. L'appareil génère une paire de clés
    et enregistre la publique. Ensuite chaque réclamation est signée, donc
    personne ne peut réclamer au nom d'un autre.
    """
    __tablename__ = "agents"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    player_name: Mapped[str]      = mapped_column(String(100), unique=True, index=True)
    public_x:    Mapped[str]      = mapped_column(String(120))
    public_y:    Mapped[str]      = mapped_column(String(120))
    created_at:  Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class WaypointClaim(Base):
    """Réclamation d'un waypoint.

    Deux régimes, une seule table (cf. claim_mode sur Waypoint) :
      - mode="progress" : avance une mission. Un joueur ne peut réclamer
        chaque waypoint qu'une fois — l'unicité (waypoint, joueur) suffit.
      - mode="find"     : trouvaille du monde. Plusieurs joueurs réclament
        chacun une fois, de façon permanente et indépendante.
    """
    __tablename__ = "waypoint_claims"
    __table_args__ = (
        UniqueConstraint("waypoint_id", "player_name", name="uq_claim_waypoint_player"),
    )

    id:          Mapped[int]            = mapped_column(Integer, primary_key=True, index=True)
    waypoint_id: Mapped[int]            = mapped_column(ForeignKey("waypoints.id"), index=True)
    player_name: Mapped[str]            = mapped_column(String(100))
    mode:        Mapped[str]            = mapped_column(String(16), default="find")
    proof:       Mapped[str | None]     = mapped_column(String(100))  # ce qui a été scanné
    proven:      Mapped[bool]           = mapped_column(Boolean, default=False)
    claimed_at:  Mapped[datetime]       = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    waypoint: Mapped["Waypoint"] = relationship(back_populates="claims")


class PlayerSession(Base):
    __tablename__ = "player_sessions"

    id:               Mapped[int]            = mapped_column(Integer, primary_key=True, index=True)
    mission_id:       Mapped[int]            = mapped_column(ForeignKey("missions.id"), index=True)
    player_name:      Mapped[str]            = mapped_column(String(100))
    started_at:       Mapped[datetime]       = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at:     Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_waypoint: Mapped[int]            = mapped_column(Integer, default=0)
    token_jti:        Mapped[str]            = mapped_column(String(100), unique=True)

    mission: Mapped["Mission"] = relationship(back_populates="sessions")


# ── Comptes et parties ───────────────────────────────────────────────────────
# Séparation volontaire : le compte est un CONTENEUR de parties, la partie est
# l'unité de jeu, et les missions ignorent totalement l'existence des comptes.
#
# Une partie peut vivre sans compte (jeu local, aucun formulaire). Le compte
# n'apparaît qu'au moment d'un point de contrôle, et il en contient autant
# qu'on veut — un email n'est pas une personne, c'est une étiquette.
#
# Les jetons sont stockés HACHÉS. Personne ne les tape jamais, donc ça ne
# coûte aucune friction, mais une fuite de base ne donne pas de sessions.


class Account(Base):
    """Conteneur de parties. Email = étiquette, jamais preuve.

    L'email n'est pas vérifié : on n'envoie aucun courrier. Il ne sert donc
    jamais à retrouver quoi que ce soit à lui seul — c'est le jeton qui
    authentifie. Chercher par email sans jeton ne rend rien.
    """
    __tablename__ = "accounts"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    email:      Mapped[str]           = mapped_column(String(200), index=True)  # PAS unique : étiquette
    label:      Mapped[str | None]    = mapped_column(String(100))
    token_hash: Mapped[str]           = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime]      = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    parties: Mapped[list["Party"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Party(Base):
    """Une partie : le jeton EST la partie.

    kind = "mission" (ref_id -> missions.id) ou "cache" (chasse libre).
    state_json porte l'avancement ; c'est un blob volontairement souple,
    parce que ce qu'une mission considère comme « avancé » lui appartient —
    pas à la table.
    """
    __tablename__ = "parties"

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    account_id:  Mapped[int | None]    = mapped_column(ForeignKey("accounts.id"), nullable=True, index=True)
    kind:        Mapped[str]           = mapped_column(String(16), default="mission")
    ref_id:      Mapped[int | None]    = mapped_column(Integer, nullable=True)
    title:       Mapped[str | None]    = mapped_column(String(200))
    token_hash:  Mapped[str]           = mapped_column(String(64), unique=True, index=True)
    state_json:  Mapped[str]           = mapped_column(Text, default="{}")
    created_at:  Mapped[datetime]      = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at:  Mapped[datetime]      = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    account: Mapped["Account | None"] = relationship(back_populates="parties")

class AppSetting(Base):
    """Petit magasin clé/valeur pour l'état de l'application.

    Sert d'abord à ne semer les missions par défaut qu'une seule fois : si le
    papa les efface, elles ne doivent pas revenir au redémarrage suivant.
    """
    __tablename__ = "app_settings"

    key:   Mapped[str]           = mapped_column(String(64), primary_key=True)
    value: Mapped[str]           = mapped_column(Text, default="")
    set_at: Mapped[datetime]     = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
