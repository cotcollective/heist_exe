from sqlalchemy import String, Integer, Float, Boolean, Text, ForeignKey, DateTime
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

    id:             Mapped[int]         = mapped_column(Integer, primary_key=True, index=True)
    mission_id:     Mapped[int]         = mapped_column(ForeignKey("missions.id"), index=True)
    order:          Mapped[int]         = mapped_column(Integer)
    title:          Mapped[str]         = mapped_column(String(200))
    hint:           Mapped[str | None]  = mapped_column(Text)
    lat:            Mapped[float]       = mapped_column(Float)
    lng:            Mapped[float]       = mapped_column(Float)
    radius_meters:  Mapped[int]         = mapped_column(Integer, default=30)
    qr_code:        Mapped[str | None]  = mapped_column(String(100))

    mission: Mapped["Mission"]          = relationship(back_populates="waypoints")
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
