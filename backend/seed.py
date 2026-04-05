#!/usr/bin/env python3
"""
seed.py — Injecte la mission de démo Tétreaultville dans la DB.

Usage:
    python seed.py                          # API sur localhost
    python seed.py http://monserveur.com    # API custom

La mission utilise de vraies coordonnées GPS de Tétreaultville, Montréal.
PIN de la mission: 2077
"""
import sys
import json
import urllib.request
import urllib.error
import os

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"
ADMIN_KEY = os.getenv("ADMIN_KEY", "admin-secret-key-change-me")

MISSION = {
    "title": "Opération Tétreaultville",
    "lore": (
        "L'agent X a été compromis. Sa dernière transmission pointait vers le secteur Taillon. "
        "Une clé d'accès contenant les preuves a été cachée quelque part dans le quartier "
        "avant son arrestation. Tu as 45 minutes avant que le signal soit tracé. "
        "Commence au parc. Suis les indices. Récupère la planque."
    ),
    "pin": "2077",
    "duration_minutes": 45,
    "reward_text": (
        "ACCÈS ACCORDÉ. L'agent X a laissé une enveloppe au comptoir du dépanneur Taillon. "
        "Identifie-toi avec le code OMEGA-7. Budget alloué: 15$. "
        "Tu as 8 minutes avant que la trace soit active. Bonne chance."
    ),
    "waypoints": [
        {
            "order": 0,
            "title": "Parc L.-O.-Taillon",
            "hint": (
                "Repère le banc qui fait exactement face au sud-est, en direction du pont. "
                "C'est là que l'échange devait avoir lieu."
            ),
            "lat": 45.567890,
            "lng": -73.549120,
            "radius_meters": 35,
            "enigma": {
                "question": (
                    "Compte le nombre de lattes de bois sur le dossier du banc. "
                    "Multiplie ce nombre par le numéro civique de la bâtisse rouge "
                    "visible en face, de l'autre côté de la rue."
                ),
                "answer": "84",
                "hint": "Le numéro civique est clairement visible sur la façade principale.",
            },
        },
        {
            "order": 1,
            "title": "Mural de la rue Sainte-Catherine",
            "hint": (
                "L'agent X avait une affection particulière pour l'art urbain. "
                "Cherche le mural avec l'œil géant qui te regarde. "
                "Il cache quelque chose dans ses couleurs."
            ),
            "lat": 45.568450,
            "lng": -73.547800,
            "radius_meters": 30,
            "enigma": {
                "question": (
                    "Compte le nombre de couleurs distinctes utilisées dans le mural. "
                    "Ne compte pas le noir ni le blanc comme des couleurs."
                ),
                "answer": "7",
                "hint": "Regarde bien les dégradés — chaque teinte compte comme une couleur séparée.",
            },
        },
        {
            "order": 2,
            "title": "Coin Ontario / Joliette",
            "hint": (
                "L'intersection où les deux lignes se croisent. "
                "Regarde en bas. Le code est gravé quelque part dans le béton."
            ),
            "lat": 45.569100,
            "lng": -73.546200,
            "radius_meters": 25,
            "enigma": {
                "question": (
                    "Sur la plaque de rue du coin, quelle est la limite de vitesse "
                    "affichée sur le panneau juste en dessous du nom de rue?"
                ),
                "answer": "30",
                "hint": "C'est une zone résidentielle — la limite standard du quartier.",
            },
        },
        {
            "order": 3,
            "title": "Dépanneur Taillon — La Planque",
            "hint": (
                "Tu y es presque. Le dépanneur vert au coin. "
                "Identifie-toi au comptoir avec le code OMEGA-7. "
                "Mérite tes chips."
            ),
            "lat": 45.569800,
            "lng": -73.544900,
            "radius_meters": 20,
            "enigma": None,
        },
    ],
}


def request(method, path, body=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ADMIN_KEY}",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return json.loads(body) if body else {}, e.code


def main():
    print("=" * 60)
    print("  HEIST.EXE — Seed Tétreaultville")
    print("=" * 60)
    print(f"  API: {BASE_URL}")
    print(f"  Admin key: {'*' * (len(ADMIN_KEY) - 4) + ADMIN_KEY[-4:]}")
    print()

    # Health check
    print("  [1/3] Health check...")
    data, status = request("GET", "/health")
    if status != 200:
        print(f"  ✗ API non disponible (status {status})")
        print("    Lance d'abord: docker-compose up --build")
        sys.exit(1)
    print(f"  ✓ API online — {data.get('service')}")

    # Vérifier si une mission existe déjà
    print()
    print("  [2/3] Vérification missions existantes...")
    existing, _ = request("GET", "/admin/missions")
    if isinstance(existing, list) and len(existing) > 0:
        titles = [m["title"] for m in existing]
        print(f"  ⚠ {len(existing)} mission(s) déjà présente(s): {titles}")
        ans = input("  Continuer quand même? (o/N): ").strip().lower()
        if ans != "o":
            print("  Annulé.")
            sys.exit(0)
    else:
        print("  ✓ Aucune mission existante")

    # Créer la mission
    print()
    print("  [3/3] Création de la mission Tétreaultville...")
    data, status = request("POST", "/admin/missions", MISSION)

    if status != 201:
        print(f"  ✗ Erreur création (status {status}): {data}")
        sys.exit(1)

    mission_id = data["id"]
    print(f"  ✓ Mission créée — ID: {mission_id}")
    print(f"  ✓ Titre: {data['title']}")
    print(f"  ✓ Durée: {data['duration_minutes']} minutes")
    print(f"  ✓ Waypoints: {len(data['waypoints'])}")
    for wp in data["waypoints"]:
        enigma_status = "avec énigme" if wp["enigma"] else "final (pas d'énigme)"
        print(f"     WP{wp['order']}: {wp['title']} [{enigma_status}]")

    print()
    print("=" * 60)
    print("  MISSION PRÊTE")
    print("=" * 60)
    print(f"  URL joueur : http://localhost")
    print(f"  Mission ID : {mission_id}")
    print(f"  PIN accès  : 2077")
    print(f"  Swagger    : http://localhost/api/docs")
    print()
    print("  Pour uploader un message audio:")
    print(f"  curl -X POST http://localhost/api/upload/audio/{mission_id} \\")
    print(f"    -H 'Authorization: Bearer {ADMIN_KEY}' \\")
    print(f"    -F 'file=@ton_message.mp3'")
    print()


if __name__ == "__main__":
    main()
