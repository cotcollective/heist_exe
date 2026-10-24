"""Migrations SQL versionnées, sans dépendance.

Principe :
  - `backend/migrations/*.sql`, appliqués dans l'ordre lexicographique.
  - Table `schema_version` : une ligne par migration appliquée.
  - Une DB neuve (aucune table avant `create_all`) est *baselinée* : le
    schéma est déjà complet, on marque les migrations comme appliquées
    sans les rejouer.

Pourquoi pas Alembic : deux fichiers SQL et 80 lignes suffisent ici, et
le projet n'a aucune autre dépendance de migration. Si le schéma devient
complexe, ce module se remplace sans toucher au reste.

Limite connue du découpage : on sépare sur `;` après avoir retiré les
commentaires `--`. Aucune migration ne doit contenir de `;` dans une
chaîne littérale. C'est documenté ici parce que c'est le piège classique.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _strip_comments(sql: str) -> str:
    return "\n".join(
        line for line in sql.splitlines() if not line.strip().startswith("--")
    )


def split_statements(sql: str) -> list[str]:
    """Découpe un fichier SQL en instructions exécutables."""
    body = _strip_comments(sql)
    return [s.strip() for s in body.split(";") if s.strip()]


def migration_files() -> list[Path]:
    if not MIGRATIONS_DIR.is_dir():
        return []
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


async def _applied_versions(conn) -> set[str]:
    await conn.exec_driver_sql(
        "CREATE TABLE IF NOT EXISTS schema_version ("
        "  version    TEXT NOT NULL PRIMARY KEY,"
        "  applied_at TEXT NOT NULL"
        ")"
    )
    result = await conn.exec_driver_sql("SELECT version FROM schema_version")
    return {row[0] for row in result.fetchall()}


async def _mark(conn, version: str) -> None:
    await conn.exec_driver_sql(
        "INSERT OR REPLACE INTO schema_version (version, applied_at) VALUES (?, ?)",
        (version, datetime.now(timezone.utc).isoformat()),
    )


async def apply_migrations(conn, baseline_fresh: bool = False) -> list[str]:
    """Applique les migrations en attente.

    Args:
        conn: connexion SQLAlchemy async (ou objet exposant exec_driver_sql).
        baseline_fresh: True si la base vient d'être créée par `create_all` —
            le schéma est alors déjà à jour et on marque tout comme appliqué.

    Returns:
        La liste des versions effectivement exécutées (vide si baseline).
    """
    files = migration_files()
    if not files:
        return []

    applied = await _applied_versions(conn)

    if baseline_fresh:
        for path in files:
            if path.stem not in applied:
                await _mark(conn, path.stem)
        return []

    executed: list[str] = []
    for path in files:
        version = path.stem
        if version in applied:
            continue

        statements = split_statements(path.read_text(encoding="utf-8"))
        for stmt in statements:
            await conn.exec_driver_sql(stmt)

        await _mark(conn, version)
        executed.append(version)

    return executed
