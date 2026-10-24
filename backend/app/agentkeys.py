"""Signature ECDSA P-256 des réclamations.

Pourquoi des clés par appareil plutôt que des comptes : une cache du monde
se trouve hors mission, donc hors du jeton joueur. On veut une identité qui
survit, qui ne demande ni mot de passe ni courriel, et qui empêche surtout
de réclamer au nom de quelqu'un d'autre.

Le navigateur signe avec WebCrypto. Attention au format : WebCrypto produit
une signature ECDSA brute de 64 octets (r ‖ s, 32 + 32), alors que la
bibliothèque `cryptography` attend du DER. La conversion est faite ici.
"""
from __future__ import annotations

import base64
import binascii

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

# Fenêtre de validité d'une signature. Large : un téléphone peut être hors
# réseau un moment avant de synchroniser sa réclamation.
SIGNATURE_WINDOW_SECONDS = 600


def _b64url_to_bytes(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def canonical_claim_message(waypoint_id: int, player_name: str, ts: int) -> bytes:
    """Forme canonique signée — doit être identique des deux côtés.

    Pipe-délimité plutôt que JSON : pas de question d'ordre des clés, pas
    d'échappement, pas de normalisation Unicode à faire correspondre.
    """
    return f"{waypoint_id}|{player_name}|{ts}".encode("utf-8")


def verify_claim_signature(
    public_jwk: dict,
    waypoint_id: int,
    player_name: str,
    ts: int,
    signature_b64: str,
) -> bool:
    """Vérifie une signature de réclamation. False sur toute anomalie."""
    try:
        if public_jwk.get("kty") != "EC" or public_jwk.get("crv") != "P-256":
            return False

        raw = _b64url_to_bytes(signature_b64)
        if len(raw) != 64:
            return False

        r = int.from_bytes(raw[:32], "big")
        s = int.from_bytes(raw[32:], "big")
        der = encode_dss_signature(r, s)

        x = int.from_bytes(_b64url_to_bytes(public_jwk["x"]), "big")
        y = int.from_bytes(_b64url_to_bytes(public_jwk["y"]), "big")
        pub = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1()).public_key()

        pub.verify(der, canonical_claim_message(waypoint_id, player_name, ts),
                   ec.ECDSA(hashes.SHA256()))
        return True
    except (InvalidSignature, KeyError, ValueError, TypeError, binascii.Error):
        return False


def valid_public_jwk(jwk: dict) -> bool:
    """Contrôle de forme minimal avant stockage."""
    return (
        isinstance(jwk, dict)
        and jwk.get("kty") == "EC"
        and jwk.get("crv") == "P-256"
        and isinstance(jwk.get("x"), str)
        and isinstance(jwk.get("y"), str)
        and len(jwk["x"]) >= 40
        and len(jwk["y"]) >= 40
    )


def jwk_fingerprint(jwk: dict) -> str:
    """Empreinte stable d'une clé — sert à détecter un changement de clé."""
    return f"{jwk.get('x', '')}:{jwk.get('y', '')}"
