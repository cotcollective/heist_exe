-- ══════════════════════════════════════════════════════════════════════════
--  001_world.sql — 1.0.0 → 1.1.0
--
--  Le monde : caches publiques hors mission.
--
--  Deux difficultés SQLite, traitées ici :
--
--  1. `waypoints.mission_id` était NOT NULL en 1.0.0. SQLite ne sait pas
--     relâcher une contrainte NOT NULL par ALTER : il faut reconstruire la
--     table (créer / copier / déposer / renommer). La copie préserve les id,
--     donc `enigmas.waypoint_id` reste valide.
--
--  2. Une contrainte UNIQUE ne peut pas être ajoutée par ALTER TABLE.
--     On crée un index unique à la place — même garantie, même coût.
--
--  Les clés étrangères sont désactivées par défaut dans SQLite (SQLAlchemy
--  ne pose pas le PRAGMA), donc le DROP/RENAME ne casse rien.
-- ══════════════════════════════════════════════════════════════════════════

CREATE TABLE waypoints_new (
    id                 INTEGER      NOT NULL PRIMARY KEY,
    mission_id         INTEGER,
    "order"            INTEGER      NOT NULL DEFAULT 0,
    title              VARCHAR(200) NOT NULL,
    hint               TEXT,
    lat                FLOAT        NOT NULL,
    lng                FLOAT        NOT NULL,
    radius_meters      INTEGER      NOT NULL DEFAULT 30,
    qr_code            VARCHAR(100),
    is_public          BOOLEAN      NOT NULL DEFAULT 0,
    claim_mode         VARCHAR(16)  NOT NULL DEFAULT 'progress',
    owner_label        VARCHAR(100),
    origin_mission_id  INTEGER,
    origin_waypoint_id INTEGER,
    FOREIGN KEY(mission_id) REFERENCES missions (id)
);

INSERT INTO waypoints_new
    (id, mission_id, "order", title, hint, lat, lng, radius_meters, qr_code)
SELECT
    id, mission_id, "order", title, hint, lat, lng, radius_meters, qr_code
FROM waypoints;

DROP TABLE waypoints;

ALTER TABLE waypoints_new RENAME TO waypoints;

CREATE INDEX ix_waypoints_id                  ON waypoints (id);
CREATE INDEX ix_waypoints_mission_id          ON waypoints (mission_id);
CREATE INDEX ix_waypoints_is_public           ON waypoints (is_public);
CREATE INDEX ix_waypoints_origin_mission_id   ON waypoints (origin_mission_id);
CREATE INDEX ix_waypoints_origin_waypoint_id  ON waypoints (origin_waypoint_id);
CREATE UNIQUE INDEX uq_origin_pair            ON waypoints (origin_mission_id, origin_waypoint_id);

CREATE TABLE IF NOT EXISTS waypoint_claims (
    id          INTEGER      NOT NULL PRIMARY KEY,
    waypoint_id INTEGER      NOT NULL,
    player_name VARCHAR(100) NOT NULL,
    mode        VARCHAR(16)  NOT NULL DEFAULT 'find',
    proof       VARCHAR(100),
    proven      BOOLEAN      NOT NULL DEFAULT 0,
    claimed_at  DATETIME     NOT NULL,
    FOREIGN KEY(waypoint_id) REFERENCES waypoints (id)
);

CREATE INDEX IF NOT EXISTS ix_waypoint_claims_waypoint_id ON waypoint_claims (waypoint_id);
