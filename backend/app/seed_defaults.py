"""Missions par défaut — pour que l'app ait de quoi jouer au premier lancement.

Cinq chasses complètes, dans Tétreaultville (Montréal, coin Taillon /
Notre-Dame / Sherbrooke). Elles sont semées **une seule fois**, à la création
de la base, et jamais réinjectées ensuite : si tu les effaces, elles restent
effacées.

Deux choses à garder en tête :

1. Les coordonnées pointent le secteur, pas un objet précis au centimètre.
   Un papa qui veut une vraie chasse ajuste les points avec le constructeur —
   c'est fait pour être édité, pas pour être joué les yeux fermés.
2. Les énigmes se répondent à l'œil ou par déduction simple, jamais par
   culture générale. Un enfant de huit ans doit pouvoir finir seul.

Les PIN sont volontairement simples et documentés : c'est un jeu de famille,
pas un coffre-fort.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_answer, hash_secret
from app.models import AppSetting, Enigma, Mission, Waypoint

SEED_KEY = "default_missions_v1"

# ── Les cinq missions ────────────────────────────────────────────────────────
# Chaque waypoint : (titre, indice, lat, lng, rayon_m, (question, réponse))

DEFAULT_MISSIONS = [
    {
        "title": "Le Trésor du Parc",
        "pin": "1111",
        "duration_minutes": 20,
        "lore": (
            "Quelqu'un a oublié un colis au parc avant la fermeture. Trois arrêts, "
            "trois devinettes, pis la cache est à toi. Prends ton temps, c'est facile."
        ),
        "reward_text": "T'as trouvé le colis du parc. Chips au dépanneur, tu l'as mérité.",
        "waypoints": [
            ("Le banc du parc", "Face au pont, à l'ombre. Assieds-toi deux secondes.",
             45.5680, -73.5500, 30,
             ("Je suis en bois, je te porte quand t'es fatigué, et je ne dis jamais un mot. Qui suis-je ?", "banc")),
            ("La clôture", "Le long du terrain de jeux, côté rue.",
             45.5688, -73.5492, 25,
             ("J'ai des dents mais je ne mords personne, et je garde les enfants dedans. Qui suis-je ?", "cloture")),
            ("La boîte aux lettres", "Près de l'entrée, sur le poteau gris.",
             45.5672, -73.5506, 20,
             ("J'avale des lettres toute la journée et je ne réponds jamais. Qui suis-je ?", "boite aux lettres")),
        ],
    },
    {
        "title": "Le Vieux Tétreault",
        "pin": "2222",
        "duration_minutes": 30,
        "lore": (
            "Le quartier est plus vieux que toi, plus vieux que ton père, plus vieux "
            "que le dépanneur du coin. Quatre arrêts pour retrouver des affaires que "
            "le monde a oubliées en marchant dessus."
        ),
        "reward_text": "T'as marché dans les traces du vieux Tétreault. Le quartier te connaît maintenant.",
        "waypoints": [
            ("Le coin de Notre-Dame", "Au coin, regarde le trottoir : y'a une date gravée.",
             45.5662, -73.5487, 30,
             ("Une date gravée dans le béton, ça commence toujours par quoi ? Deux chiffres.", "19")),
            ("La vieille bâtisse", "La brique rouge, celle avec les fenêtres hautes.",
             45.5655, -73.5472, 25,
             ("Sur une bâtisse en brique, qu'est-ce qui monte jusqu'au ciel et sert à sortir la fumée ?", "cheminee")),
            ("La croix du parc", "Au fond, tu vas la voir de loin.",
             45.5648, -73.5459, 25,
             ("Je suis plantée debout, j'ai deux bras, pis tout le monde me regarde en l'air. Qui suis-je ?", "croix")),
            ("La pierre commémorative", "Près de l'entrée, la grosse roche avec une plaque.",
             45.5660, -73.5466, 20,
             ("Qu'est-ce qui raconte une histoire mais ne parle jamais ?", "plaque")),
        ],
    },
    {
        "title": "Le Dépanneur Mystère",
        "pin": "3333",
        "duration_minutes": 25,
        "lore": (
            "Le dépanneur du coin cache un message dans sa vitrine depuis des années. "
            "Personne l'a jamais lu. Toi, tu vas le lire."
        ),
        "reward_text": "Le message du dépanneur, c'est toi qui l'as trouvé. Le propriétaire va être impressionné.",
        "waypoints": [
            ("Le coin Honoré-Beaugrand", "Arrête-toi au coin, regarde l'enseigne du commerce.",
             45.5702, -73.5450, 30,
             ("Combien de couleurs différentes sur l'enseigne ? Regarde bien, c'est un petit chiffre.", "3")),
            ("La vitrine", "Collée sur la vitre, y'a des affichettes partout.",
             45.5695, -73.5442, 25,
             ("Sur la vitre, qu'est-ce qui annonce un prix mais ne vend rien ?", "affiche")),
            ("La boîte postale", "Sur le mur de côté, la boîte rouge.",
             45.5710, -73.5458, 20,
             ("Je suis rouge, j'ai une fente, et j'attends le facteur. Qui suis-je ?", "boite postale")),
        ],
    },
    {
        "title": "La Grande Promenade",
        "pin": "4444",
        "duration_minutes": 35,
        "lore": (
            "La plus longue des cinq. Quatre arrêts, une trotte, pis un view-point "
            "que le monde du quartier connaît même pas. Amène de l'eau."
        ),
        "reward_text": "Quatre arrêts, une trotte, pis la vue. T'as fait la grande promenade au complet.",
        "waypoints": [
            ("Sur Sherbrooke", "Le long du boulevard, côté nord. Ça roule vite, reste sur le trottoir.",
             45.5725, -73.5420, 30,
             ("Qu'est-ce qui a des feux, des lignes blanches, pis que tout le monde suit sans discuter ?", "route")),
            ("Le parc linéaire", "Le long corridor vert entre les rues.",
             45.5712, -73.5435, 30,
             ("Je suis vert, je longe la rue, pis les chiens m'adorent. Qui suis-je ?", "gazon")),
            ("La passerelle", "Tu passes par-dessus. Regarde en dessous.",
             45.5698, -73.5428, 25,
             ("Je passe par-dessus l'eau mais je ne nage pas. Qui suis-je ?", "pont")),
            ("Le belvédère", "La butte au bout. Monte, pis regarde en arrière.",
             45.5685, -73.5415, 25,
             ("Plus tu montes, plus tu vois. Qu'est-ce que c'est ?", "vue")),
        ],
    },
    {
        "title": "Le Fantôme du Boulevard",
        "pin": "5555",
        "duration_minutes": 15,
        "lore": (
            "La plus courte. Faite pour les petits, ou pour les soirées où on est "
            "pressé. Trois arrêts, quinze minutes, pas de trotte."
        ),
        "reward_text": "Quinze minutes, trois arrêts, un fantôme. Record battu.",
        "waypoints": [
            ("Le lampadaire", "Le premier en sortant, celui qui clignote des fois.",
             45.5675, -73.5475, 25,
             ("Je m'allume la nuit, je m'éteins le jour, pis je clignote quand je suis tanné. Qui suis-je ?", "lampadaire")),
            ("Le gros arbre", "Le plus gros du bout de la rue. Tu peux pas le manquer.",
             45.5682, -73.5468, 20,
             ("J'ai des bras toute l'année, des cheveux juste l'été, pis je reste planté là. Qui suis-je ?", "arbre")),
            ("Le banc du coin", "Le dernier arrêt. Assieds-toi, le fantôme est en dessous.",
             45.5690, -73.5460, 20,
             ("Je suis sous le banc, je fais peur à personne, pis je mesure rien du tout. Qui suis-je ?", "ombre")),
        ],
    },
]


async def seed_default_missions(db: AsyncSession) -> int:
    """Sème les cinq missions une seule fois. Retourne le nombre créé.

    La garde est un drapeau en base, pas un compteur de missions : sans lui,
    un papa qui efface les cinq pour repartir à zéro les verrait revenir au
    prochain redémarrage, et croirait que la suppression ne marche pas.
    """
    already = await db.get(AppSetting, SEED_KEY)
    if already is not None:
        return 0

    for spec in DEFAULT_MISSIONS:
        mission = Mission(
            title=spec["title"],
            lore=spec["lore"],
            pin_hash=hash_secret(spec["pin"]),
            duration_minutes=spec["duration_minutes"],
            reward_text=spec["reward_text"],
        )
        db.add(mission)
        await db.flush()          # pour obtenir mission.id

        for order, (title, hint, lat, lng, radius, enigma) in enumerate(spec["waypoints"]):
            wp = Waypoint(
                mission_id=mission.id,
                order=order,
                title=title,
                hint=hint,
                lat=lat,
                lng=lng,
                radius_meters=radius,
            )
            db.add(wp)
            await db.flush()

            if enigma:
                question, answer = enigma
                db.add(Enigma(
                    waypoint_id=wp.id,
                    question=question,
                    answer_hash=hash_answer(answer),
                    hint=None,
                ))

    db.add(AppSetting(key=SEED_KEY, value="done"))
    await db.commit()
    return len(DEFAULT_MISSIONS)


async def reset_default_missions(db: AsyncSession) -> None:
    """Retire le drapeau pour permettre un nouveau semis (utile en test)."""
    flag = await db.get(AppSetting, SEED_KEY)
    if flag is not None:
        await db.delete(flag)
        await db.commit()
